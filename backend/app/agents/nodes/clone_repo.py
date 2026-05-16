import os
from pathlib import Path

from app.agents.state import AgentState, get_task, task_update, task_update
from app.models import TaskStatus
from app.sandbox.workspace import Workspace


async def clone_repo_node(state: AgentState) -> dict:
    """Clone the repository and set up the feature branch."""
    import json, time, traceback  # #region agent log
    _dl_path = "/tmp/metl-debug-a493e7.log"
    def _dl(msg, data, hid="H2"):
        _dl_obj = json.dumps({"sessionId":"a493e7","id":"log_"+str(int(time.time()*1000)),"timestamp":int(time.time()*1000),"location":"clone_repo.py:12","message":msg,"data":data,"runId":"debug","hypothesisId":hid})
        print("[METL_DEBUG] " + _dl_obj)
        try:
            with open(_dl_path,"a") as f: f.write(_dl_obj+"\n")
        except Exception: pass
    task = get_task(state)
    _dl("H2: clone_repo entry", {"task_id":task.id,"github_url":task.github_url,"branch":task.branch}, "H2")
    workspace = Workspace(
        task_id=task.id,
        github_url=task.github_url,
        branch=task.branch,
    )
    _dl("H2: workspace created", {"work_dir":str(workspace.work_dir),"sandbox_base_dir":workspace.work_dir.parent.name}, "H2")
    try:
        work_dir = await workspace.clone()
    except Exception as e:
        _dl("H2: clone raised exception", {"error":str(e),"tb":traceback.format_exc()[-500:]}, "H2")
        raise
    _dl("H2: clone returned", {"work_dir":str(work_dir)}, "H2")  # #endregion
    return {
        "workspace_path": str(work_dir),
        "task": task_update(state, status=TaskStatus.CLONING),
    }