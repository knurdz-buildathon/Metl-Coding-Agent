"use client";

import { useState, useEffect } from "react";
import TaskList from "@/components/TaskList";
import CreateTaskForm from "@/components/CreateTaskForm";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function Home() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/tasks`);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Metl</h1>
            <p className="text-gray-500 mt-1">Autonomous Coding Agent</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            {showCreate ? "Cancel" : "New Task"}
          </button>
        </div>
      </header>

      {showCreate && (
        <div className="mb-8">
          <CreateTaskForm onCreated={() => { setShowCreate(false); fetchTasks(); }} />
        </div>
      )}

      <main>
        <h2 className="text-xl font-semibold mb-4">Tasks</h2>
        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading tasks...</div>
        ) : (
          <TaskList tasks={tasks} />
        )}
      </main>
    </div>
  );
}