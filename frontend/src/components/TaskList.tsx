"use client";

interface Task {
  id: string;
  status: string;
  github_url: string;
  prompt: string;
  current_step: number;
  total_steps: number;
  created_at: string;
}

export default function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-[var(--border-primary)] rounded-lg">
        <p className="text-[var(--text-secondary)] text-sm">No tasks yet</p>
        <p className="text-[var(--text-secondary)] text-xs mt-2 opacity-60">
          Create a coding task above to get started
        </p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    pending: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    analyzing: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    planning: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    cloning: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    coding: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    building: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    inspecting: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    waiting_for_resource: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    completed: "bg-green-500/10 text-green-400 border-green-500/20",
    failed: "bg-red-500/10 text-red-400 border-red-500/20",
    cancelled: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  };

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <a
          key={task.id}
          href={`/task/${task.id}`}
          className="block p-4 bg-[var(--bg-tertiary)] border border-[var(--border-primary)] rounded-lg hover:border-[var(--accent-blue)] hover:bg-[var(--bg-hover)] transition-all"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                {task.prompt}
              </p>
              <p className="text-xs text-[var(--text-secondary)] mt-1 truncate font-mono">
                {task.github_url}
              </p>
              <div className="flex items-center gap-4 mt-2 text-[10px] text-[var(--text-secondary)]">
                <span>
                  Step {task.current_step}/{task.total_steps || "?"}
                </span>
                <span>{new Date(task.created_at).toLocaleString()}</span>
              </div>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-[10px] font-medium border whitespace-nowrap ${
                statusColors[task.status] || statusColors.pending
              }`}
            >
              {task.status.replace(/_/g, " ")}
            </span>
          </div>

          {task.current_step > 0 && task.total_steps > 0 && (
            <div className="mt-3 w-full bg-[var(--bg-primary)] rounded-full h-1">
              <div
                className="bg-[var(--accent-blue)] h-1 rounded-full transition-all"
                style={{
                  width: `${Math.round((task.current_step / task.total_steps) * 100)}%`,
                }}
              />
            </div>
          )}
        </a>
      ))}
    </div>
  );
}