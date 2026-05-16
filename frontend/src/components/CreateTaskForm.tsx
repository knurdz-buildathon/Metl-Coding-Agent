"use client";

import { useState } from "react";
import { GitBranch, Sparkles } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function CreateTaskForm({ onCreated }: { onCreated: () => void }) {
  const [githubUrl, setGithubUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [prompt, setPrompt] = useState("");
  const [planFile, setPlanFile] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          github_url: githubUrl,
          branch,
          prompt,
          plan_file: planFile || undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create task");
      }

      onCreated();
      setGithubUrl("");
      setBranch("main");
      setPrompt("");
      setPlanFile("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-5 bg-[var(--bg-tertiary)] border border-[var(--border-primary)] rounded-lg space-y-4"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[var(--accent-blue)]" />
          New Coding Task
        </h3>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
        >
          {showAdvanced ? "Hide advanced" : "Show advanced"}
        </button>
      </div>

      <div className="grid grid-cols-[1fr_auto] gap-2">
        <input
          type="url"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          placeholder="https://github.com/org/repo"
          required
          className="px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)] placeholder:text-[var(--text-secondary)]"
        />
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 text-sm bg-[var(--accent-blue)] text-white rounded hover:opacity-90 disabled:opacity-50 transition-opacity whitespace-nowrap"
        >
          {submitting ? "Creating..." : "Start Task"}
        </button>
      </div>

      {showAdvanced && (
        <div>
          <label className="flex items-center gap-1.5 text-[11px] text-[var(--text-secondary)] mb-1">
            <GitBranch className="w-3 h-3" />
            Branch
          </label>
          <input
            type="text"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            className="w-full px-3 py-1.5 text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)]"
          />
        </div>
      )}

      <div>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what you want the agent to build... e.g., 'Add a dark mode toggle to the settings page'"
          rows={3}
          required
          className="w-full px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)] placeholder:text-[var(--text-secondary)] resize-none"
        />
      </div>

      {showAdvanced && (
        <div>
          <label className="text-[11px] text-[var(--text-secondary)] block mb-1">
            Plan File (optional, markdown)
          </label>
          <textarea
            value={planFile}
            onChange={(e) => setPlanFile(e.target.value)}
            placeholder="Paste a markdown plan file..."
            rows={3}
            className="w-full px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)] placeholder:text-[var(--text-secondary)] resize-none"
          />
        </div>
      )}

      {error && (
        <div className="p-3 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded text-sm text-[var(--accent-red)]">
          {error}
        </div>
      )}
    </form>
  );
}