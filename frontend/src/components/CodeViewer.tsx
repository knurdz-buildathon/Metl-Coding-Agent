"use client";

import { useState, useEffect } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface CodeViewerProps {
  taskId: string;
  filePath: string;
  isModified: boolean;
}

export function CodeViewer({ taskId, filePath, isModified }: CodeViewerProps) {
  const [original, setOriginal] = useState("");
  const [modified, setModified] = useState("");
  const [language, setLanguage] = useState("plaintext");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadFile() {
      try {
        setLoading(true);
        setError("");

        const extension = filePath.split(".").pop()?.toLowerCase() || "";
        const langMap: Record<string, string> = {
          ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
          py: "python", rs: "rust", go: "go", java: "java", rb: "ruby",
          html: "html", css: "css", scss: "scss", json: "json", yaml: "yaml",
          yml: "yaml", md: "markdown", sql: "sql", sh: "shell", bash: "shell",
          xml: "xml", toml: "ini", env: "plaintext", gitignore: "plaintext",
        };
        setLanguage(langMap[extension] || "plaintext");

        // Fetch current file content
        const fileRes = await fetch(
          `${API_BASE}/tasks/${taskId}/workspace/file?path=${encodeURIComponent(filePath)}`
        );
        if (!fileRes.ok) throw new Error("File not found");
        const fileData = await fileRes.json();

        if (cancelled) return;

        if (isModified) {
          // Show diff: original from git, modified from current workspace
          const diffRes = await fetch(
            `${API_BASE}/tasks/${taskId}/workspace/diff?path=${encodeURIComponent(filePath)}`
          );
          if (diffRes.ok) {
            const diffData = await diffRes.json();
            // Parse git diff to extract original content
            // For simplicity, show an empty original for new files
            const diffText = diffData.diff || "";
            if (diffText.startsWith("diff --git") && diffText.includes("new file mode")) {
              setOriginal("");
            } else {
              // Extract original from diff
              const originalLines: string[] = [];
              const lines = diffText.split("\n");
              for (const line of lines) {
                if (line.startsWith("-") && !line.startsWith("---")) {
                  originalLines.push(line.substring(1));
                }
              }
              setOriginal(originalLines.join("\n"));
            }
          }
          setModified(fileData.content || "");
        } else {
          // Just show the file content (read-only)
          setOriginal(fileData.content || "");
          setModified(fileData.content || "");
        }
      } catch (err: any) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadFile();
    return () => {
      cancelled = true;
    };
  }, [taskId, filePath, isModified]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-[var(--text-secondary)]">
        <span>Loading {filePath}...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center text-[var(--accent-red)]">
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-1.5 text-xs bg-[var(--bg-tertiary)] border-b border-[var(--border-primary)] flex items-center gap-2">
        <span className="text-[var(--text-secondary)]">
          {isModified ? "Diff View" : "File"}
        </span>
        <span className="text-[var(--text-primary)] font-medium truncate">
          {filePath}
        </span>
        {isModified && (
          <span className="px-1.5 py-0.5 text-[10px] bg-[var(--accent-yellow)]/20 text-[var(--accent-yellow)] rounded">
            MODIFIED
          </span>
        )}
      </div>
      <div className="flex-1 overflow-hidden">
        <DiffEditor
          height="100%"
          language={language}
          original={original}
          modified={modified}
          theme="vs-dark"
          options={{
            readOnly: true,
            renderSideBySide: true,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily:
              'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            padding: { top: 8 },
          }}
        />
      </div>
    </div>
  );
}