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
      <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-xl">
        <p className="text-gray-400 text-lg">No tasks yet</p>
        <p className="text-gray-300 text-sm mt-2">Create a new task to get started</p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-600",
    analyzing: "bg-blue-100 text-blue-600",
    planning: "bg-purple-100 text-purple-600",
    cloning: "bg-yellow-100 text-yellow-600",
    coding: "bg-indigo-100 text-indigo-600",
    building: "bg-orange-100 text-orange-600",
    inspecting: "bg-cyan-100 text-cyan-600",
    waiting_for_resource: "bg-amber-100 text-amber-600",
    completed: "bg-green-100 text-green-600",
    failed: "bg-red-100 text-red-600",
    cancelled: "bg-gray-100 text-gray-500",
  };

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <a
          key={task.id}
          href={`/task/${task.id}`}
          className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{task.prompt}</p>
              <p className="text-sm text-gray-400 mt-1 truncate">{task.github_url}</p>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                <span>
                  Step {task.current_step}/{task.total_steps || "?"}
                </span>
                <span>{new Date(task.created_at).toLocaleString()}</span>
              </div>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                statusColors[task.status] || "bg-gray-100 text-gray-600"
              }`}
            >
              {task.status.replace(/_/g, " ")}
            </span>
          </div>
        </a>
      ))}
    </div>
  );
}