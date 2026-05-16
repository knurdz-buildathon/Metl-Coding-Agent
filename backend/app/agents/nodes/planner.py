import json
from app.agents.state import AgentState, get_task, task_update
from app.models import Plan, TaskStatus
from app.services.llm_service import get_llm_service
from app.agents.prompts import PLANNER_SYSTEM_PROMPT


async def analyze_plan_node(state: AgentState) -> dict:
    """Analyze the prompt + plan_file and create an enhanced implementation plan."""
    import json, time  # #region agent log
    with open("/Users/rk_vishva/Documents/Projects/Metl/.cursor/debug-a493e7.log","a") as _dl_f:_dl_f.write(json.dumps({"sessionId":"a493e7","id":"log_"+str(int(time.time()*1000)),"timestamp":int(time.time()*1000),"location":"planner.py:12","message":"H1/H2: planner entry","data":{"task_id":get_task(state).id,"github_url":get_task(state).github_url,"has_plan_file":bool(get_task(state).plan.original_plan_file)},"runId":"debug","hypothesisId":"H1"})+"\n")  # #endregion
    llm = get_llm_service()
    task = get_task(state)

    # Build context for LLM
    repo_context = ""
    if task.github_url:
        repo_context = f"GitHub Repository: {task.github_url} (branch: {task.branch})"

    existing_plan = ""
    if task.plan.original_plan_file:
        existing_plan = f"\nExisting Plan Provided:\n{task.plan.original_plan_file}"

    prompt = f"""{PLANNER_SYSTEM_PROMPT}

{repo_context}
{existing_plan}

User's Prompt:
{task.prompt}

Available Resources:
{json.dumps([r.model_dump() for r in task.available_resources], indent=2)}

Analyze the request and create a detailed implementation plan. 
Output your analysis and plan as a JSON object with fields:
- analysis: str (brief analysis of what needs to be done)
- steps: list[str] (ordered list of implementation steps)
- resources_needed: list[dict] (resources the project needs, each with type, name, reason)
"""

    response = await llm.generate(prompt)
    
    try:
        parsed = json.loads(response)
        steps = parsed.get("steps", [])
        resources_needed = parsed.get("resources_needed", [])
    except json.JSONDecodeError:
        steps = [response]
        resources_needed = []

    enhanced_plan = Plan(
        original_prompt=task.prompt,
        original_plan_file=task.plan.original_plan_file,
        enhanced_plan=response,
        steps=steps,
    )

    return {
        "current_step": 0,
        "step_results": [],
        "errors": [],
        "resources_requested": resources_needed,
        "task": task_update(
            state,
            plan=enhanced_plan,
            status=TaskStatus.PLANNING,
            total_steps=len(steps),
        ),
    }