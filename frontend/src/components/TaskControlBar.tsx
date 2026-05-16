"use client";

import { useState } from "react";
import { Play, ExternalLink, FileCode, X } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface TaskControlBarProps {
  taskId: string;
  status: string;
  previewReady: boolean;
  previewUrl: string;
}

export function TaskControlBar({ taskId, status, previewReady, previewUrl }: TaskControlBarProps) {
  const [showContinue, setShowContinue] = useState(false);
  const [continuePrompt, setContinuePrompt] = useState("");
  const [sending, setSending] = useState(false);

  const statusColors: Record<string, string> = {
    pending: "bg-gray-500/20 text-gray-400",
    analyzing: "bg-blue-500/20 text-blue-400",
    planning: "bg-purple-500/20 text-purple-400",
    cloning: "bg-yellow-500/20 text-yellow-400",
    coding: "bg-indigo-500/20 text-indigo-400",
    building: "bg-orange-500/20 text-orange-400",
    inspecting: "bg-cyan-500/20 text-cyan-400",
    waiting_for_resource: "bg-amber-500/20 text-amber-400",
    completed: "bg-green-500/20 text-green-400",
    failed: "bg-red-500/20 text-red-400",
    cancelled: "bg-gray-500/20 text-gray-500",
  };

  const isRunning = !["completed", "failed", "cancelled"].includes(status);

  const handleContinue = async () => {
    if (!continuePrompt.trim()) return;
    setSending(true);
    try {
      await fetch(`${API_BASE}/tasks/${taskId}/continue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: continuePrompt }),
      });
      setContinuePrompt("");
      setShowContinue(false);
    } catch (err) {
      console.error("Failed to continue task:", err);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-[var(--bg-secondary)] border-b border-[var(--border-primary)]">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <a href="/" className="text-[var(--accent-blue)] font-bold text-sm">
          Metl
        </a>
        <span className="text-[var(--text-secondary)] text-xs">/</span>
        <span className="text-[var(--text-primary)] text-xs font-mono">{taskId}</span>
      </div>

      {/* Status badge */}
      <span
        className={cn(
          "px-2 py-0.5 rounded-full text-[10px] font-medium",
          statusColors[status] || "bg-gray-500/20 text-gray-400"
        )}
      >
        {status === "in_progress" ? <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse mr-1" /> : null}
        {status.replace(/_/g, " ")}
      </span>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-2">
        {previewReady && previewUrl && (
          <a
            href={previewUrl}
            target="_blank"
            className="flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/20 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            Open Preview
          </a>
        )}

        {!isRunning && (
          <button
            onClick={() => setShowContinue(true)}
            className="flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--accent-green)]/10 text-[var(--accent-green)] hover:bg-[var(--accent-green)]/20 transition-colors"
          >
            <FileCode className="w-3 h-3" />
            Continue
          </button>
        )}
      </div>

      {/* Continue Prompt Modal */}
      {showContinue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[var(--bg-tertiary)] border border-[var(--border-primary)] rounded-lg p-4 w-full max-w-lg mx-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-[var(--text-primary)]">
                Continue Task
              </h3>
              <button
                onClick={() => setShowContinue(false)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <textarea
              value={continuePrompt}
              onChange={(e) => setContinuePrompt(e.target.value)}
              placeholder="Enter a follow-up prompt to continue working..."
              rows={4}
              className="w-full px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)] resize-none"
            />
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={() => setShowContinue(false)}
                className="px-3 py-1.5 text-[11px] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleContinue}
                disabled={sending || !continuePrompt.trim()}
                className="flex items-center gap-1 px-3 py-1.5 text-[11px] rounded bg-[var(--accent-green)] text-white hover:opacity-90 disabled:opacity-50 transition-colors"
              >
                <Play className="w-3 h-3" />
                {sending ? "Sending..." : "Send"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}