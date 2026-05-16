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

    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <header className="border-b border-[var(--border-primary)] bg-[var(--bg-secondary)]">
        <div className="max-w-5xl mx-auto flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <span className="text-[var(--accent-blue)] font-bold text-lg">Metl</span>
            <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-tertiary)] px-2 py-0.5 rounded border border-[var(--border-primary)]">
              IDE
            </span>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-1.5 text-sm rounded bg-[var(--accent-blue)] text-white hover:opacity-90 transition-opacity"
          >
            {showCreate ? "Cancel" : "New Task"}
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-6">
        {showCreate && (
          <div className="mb-8">
            <CreateTaskForm
              onCreated={() => {
                setShowCreate(false);
                fetchTasks();
              }}
            />
          </div>
        )}

        <main>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
              Tasks
            </h2>
            <span className="text-xs text-[var(--text-secondary)]">
              {loading ? "Loading..." : `${tasks.length} tasks`}
            </span>
          </div>
          {loading ? (
            <div className="text-center py-12 text-[var(--text-secondary)]">
              <div className="inline-block w-5 h-5 border-2 border-[var(--border-primary)] border-t-[var(--accent-blue)] rounded-full animate-spin" />
            </div>
          ) : (
            <TaskList tasks={tasks} />
          )}
        </main>
      </div>
    </div>
  );
}