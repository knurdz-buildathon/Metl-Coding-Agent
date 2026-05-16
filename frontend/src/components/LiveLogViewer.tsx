"use client";

import { useEffect, useRef } from "react";

interface LogEntry {
  type: string;
  message?: string;
  step?: string;
  progress?: number;
}

export default function LiveLogViewer({ logs }: { logs: LogEntry[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const getLogStyle = (type: string) => {
    switch (type) {
      case "status":
        return "text-blue-600";
      case "log":
        return "text-gray-700";
      case "error":
        return "text-red-600";
      case "completed":
        return "text-green-600 font-medium";
      default:
        return "text-gray-500";
    }
  };

  return (
    <div className="bg-gray-900 text-gray-100 rounded-xl p-4 font-mono text-sm max-h-96 overflow-y-auto">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-700">
        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        <span className="text-gray-400">Live Agent Log</span>
      </div>

      {logs.length === 0 ? (
        <div className="text-gray-500 italic">Waiting for agent activity...</div>
      ) : (
        logs.map((entry, i) => (
          <div key={i} className={`py-0.5 ${getLogStyle(entry.type)}`}>
            <span className="text-gray-500 mr-2">[{entry.type}]</span>
            {entry.message && <span>{entry.message}</span>}
            {entry.step && <span>Step: {entry.step}</span>}
            {entry.progress !== undefined && (
              <span className="ml-2">Progress: {entry.progress}%</span>
            )}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}