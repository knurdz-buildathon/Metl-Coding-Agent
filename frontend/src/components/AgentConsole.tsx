"use client";

import { useRef, useEffect, useState, useMemo } from "react";
import { Search, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentConsoleProps {
  messages: any[];
}

const LOG_TYPE_STYLES: Record<string, string> = {
  log: "text-[var(--text-secondary)]",
  aider_output: "text-[var(--text-primary)]",
  task_status: "text-[var(--accent-blue)]",
  task_completed: "text-[var(--accent-green)] font-medium",
  task_failed: "text-[var(--accent-red)] font-medium",
  step_progress: "text-[var(--accent-purple)]",
  file_changed: "text-[var(--accent-yellow)]",
  error: "text-[var(--accent-red)]",
};

export function AgentConsole({ messages }: AgentConsoleProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const uniqueTypes = useMemo(() => {
    const types = new Set<string>();
    for (const msg of messages) {
      types.add(msg.type || "log");
    }
    return Array.from(types);
  }, [messages]);

  const filteredMessages = useMemo(() => {
    let msgs = messages;
    if (typeFilter !== "all") {
      msgs = msgs.filter((m) => m.type === typeFilter);
    }
    if (filter) {
      const lower = filter.toLowerCase();
      msgs = msgs.filter((m) => {
        const text =
          m.message || m.description || m.line || m.status || "";
        return text.toLowerCase().includes(lower);
      });
    }
    return msgs;
  }, [messages, filter, typeFilter]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [filteredMessages]);

  const formatMessage = (msg: any): string => {
    if (msg.line) return msg.line;
    if (msg.message) return msg.message;
    if (msg.description) return msg.description;
    if (msg.status) return `Status: ${msg.status}`;
    if (msg.path) return `File: ${msg.path}`;
    return JSON.stringify(msg);
  };

  const formatTimestamp = (msg: any): string => {
    if (msg.timestamp) {
      return new Date(msg.timestamp).toLocaleTimeString();
    }
    return "";
  };

  return (
    <div className="h-full flex flex-col bg-[var(--bg-secondary)]">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-[var(--border-primary)]">
        <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
          Console
        </span>
        <div className="flex items-center gap-1 ml-auto">
          <div className="relative">
            <Search className="w-3 h-3 absolute left-1.5 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter..."
              className="w-32 pl-6 pr-2 py-0.5 text-[11px] bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] outline-none focus:border-[var(--accent-blue)]"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-[11px] bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded px-1.5 py-0.5 text-[var(--text-secondary)] outline-none"
          >
            <option value="all">All</option>
            {uniqueTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto font-mono text-[12px] leading-relaxed">
        {filteredMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[var(--text-secondary)] text-xs">
            {messages.length === 0
              ? "Waiting for agent..."
              : "No messages match filter"}
          </div>
        ) : (
          filteredMessages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "px-3 py-0.5 border-b border-[var(--border-primary)]/30",
                LOG_TYPE_STYLES[msg.type] || "text-[var(--text-secondary)]"
              )}
            >
              <span className="text-[10px] text-[var(--text-secondary)] mr-2 opacity-50">
                {formatTimestamp(msg)}
              </span>
              <span className="text-[10px] text-[var(--text-secondary)] mr-1 opacity-40">
                [{msg.type || "log"}]
              </span>
              <span>{formatMessage(msg)}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}