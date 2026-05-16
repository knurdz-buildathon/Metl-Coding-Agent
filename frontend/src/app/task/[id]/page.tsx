"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import LiveLogViewer from "@/components/LiveLogViewer";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export default function TaskDetailPage() {
  const params = useParams();
  const taskId = params.id as string;

  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const res = await fetch(`${API_BASE}/tasks/${taskId}`);
        const data = await res.json();
        setTask(data);
        if (data.logs) setLogs(data.logs);
      } catch (err) {
        console.error("Failed to fetch task:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTask();

    // Connect WebSocket for real-time updates
    const ws = new WebSocket(`${WS_BASE}/tasks/${taskId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "status" || msg.type === "log") {
          setLogs((prev) => [...prev, msg]);
        }
        if (msg.type === "completed" || msg.type === "status") {
          fetchTask(); // Refresh task data
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      console.error("WebSocket error");
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  if (loading) {
    return <div className="min-h-screen p-8"><div className="text-center py-12">Loading...</div></div>;
  }

  if (!task) {
    return <div className="min-h-screen p-8"><div className="text-center py-12">Task not found</div></div>;
  }

  const statusColors: Record<string, string> = {
    completed: "bg-green-100 text-green-600 border-green-200",
    failed: "bg-red-100 text-red-600 border-red-200",
    cancelled: "bg-gray-100 text-gray-500 border-gray-200",
    pending: "bg-blue-100 text-blue-600 border-blue-200",
  };

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto">
      <a href="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to tasks</a>

      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">Task Details</h1>
            <p className="text-gray-500 text-sm">ID: {taskId}</p>
          </div>
          <span
            className={`px-4 py-1.5 rounded-full text-sm font-medium border ${
              statusColors[task.status] || "bg-gray-100"
            }`}
          >
            {task.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Repository:</span>
            <a href={task.github_url} className="ml-2 text-blue-600 hover:underline" target="_blank">
              {task.github_url}
            </a>
          </div>
          <div>
            <span className="text-gray-400">Branch:</span>
            <span className="ml-2">{task.branch}</span>
          </div>
          <div>
            <span className="text-gray-400">Progress:</span>
            <span className="ml-2">{task.current_step}/{task.total_steps || "?"}</span>
          </div>
          <div>
            <span className="text-gray-400">Created:</span>
            <span className="ml-2">{new Date(task.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">Prompt:</p>
          <p className="mt-1">{task.prompt}</p>
        </div>
      </div>

      <div className="mb-6">
        <LiveLogViewer logs={logs} />
      </div>

      {task.report && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Completion Report</h2>
          <pre className="text-sm text-gray-600 whitespace-pre-wrap">
            {JSON.stringify(task.report, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}