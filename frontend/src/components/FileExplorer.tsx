"use client";

import { useState, useEffect, useCallback } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface TreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: TreeNode[];
}

interface FileExplorerProps {
  taskId: string;
  selectedFile: string | null;
  modifiedFiles: Set<string>;
  onFileSelect: (path: string) => void;
}

function TreeNodeItem({
  node,
  depth,
  selectedFile,
  modifiedFiles,
  onFileSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedFile: string | null;
  modifiedFiles: Set<string>;
  onFileSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 1);

  const isSelected = selectedFile === node.path;
  const isModified = modifiedFiles.has(node.path);

  if (node.type === "directory") {
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className={cn(
            "flex items-center w-full px-1 py-0.5 text-sm hover:bg-[var(--bg-hover)] transition-colors",
            "text-[var(--text-secondary)]"
          )}
          style={{ paddingLeft: `${depth * 12 + 4}px` }}
        >
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 mr-1 shrink-0" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 mr-1 shrink-0" />
          )}
          {expanded ? (
            <FolderOpen className="w-3.5 h-3.5 mr-1.5 shrink-0 text-[var(--accent-yellow)]" />
          ) : (
            <Folder className="w-3.5 h-3.5 mr-1.5 shrink-0 text-[var(--accent-yellow)]" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {expanded && hasChildren && (
          <div>
            {node.children!.map((child) => (
              <TreeNodeItem
                key={child.path}
                node={child}
                depth={depth + 1}
                selectedFile={selectedFile}
                modifiedFiles={modifiedFiles}
                onFileSelect={onFileSelect}
              />
            ))}
          </div>
        )}
        {expanded && !hasChildren && (
          <div
            className="text-xs text-[var(--text-secondary)] italic py-0.5"
            style={{ paddingLeft: `${(depth + 1) * 12 + 4}px` }}
          >
            (empty)
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onFileSelect(node.path)}
      className={cn(
        "flex items-center w-full px-1 py-0.5 text-sm text-left transition-colors",
        isSelected
          ? "bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]"
          : "text-[var(--text-primary)] hover:bg-[var(--bg-hover)]",
        isModified && "font-medium"
      )}
      style={{ paddingLeft: `${depth * 12 + 4}px` }}
    >
      <File className="w-3.5 h-3.5 mr-1.5 shrink-0 text-[var(--text-secondary)]" />
      <span className="truncate">{node.name}</span>
      {isModified && (
        <span className="ml-1.5 w-2 h-2 rounded-full bg-[var(--accent-yellow)] shrink-0" title="Modified" />
      )}
    </button>
  );
}

export function FileExplorer({ taskId, selectedFile, modifiedFiles, onFileSelect }: FileExplorerProps) {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchTree() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/tasks/${taskId}/workspace/tree`);
        if (!res.ok) throw new Error("Failed to fetch file tree");
        const data = await res.json();
        if (!cancelled) setTree(data.tree || []);
      } catch (err: any) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchTree();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  if (loading) {
    return (
      <div className="p-3 text-sm text-[var(--text-secondary)]">
        <div className="flex flex-col gap-2">
          <div className="h-3 bg-[var(--bg-hover)] rounded animate-pulse w-3/4" />
          <div className="h-3 bg-[var(--bg-hover)] rounded animate-pulse w-1/2" />
          <div className="h-3 bg-[var(--bg-hover)] rounded animate-pulse w-2/3" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 text-sm text-[var(--accent-red)]">
        <p>Error loading files</p>
        <p className="text-xs opacity-70">{error}</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider border-b border-[var(--border-primary)]">
        Files
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        {tree.length === 0 ? (
          <div className="p-3 text-sm text-[var(--text-secondary)] italic">No files cloned yet</div>
        ) : (
          tree.map((node) => (
            <TreeNodeItem
              key={node.path}
              node={node}
              depth={0}
              selectedFile={selectedFile}
              modifiedFiles={modifiedFiles}
              onFileSelect={onFileSelect}
            />
          ))
        )}
      </div>
    </div>
  );
}