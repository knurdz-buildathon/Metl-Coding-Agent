"use client";

import { useState, useCallback, useEffect } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { FileExplorer } from "./FileExplorer";
import { CodeViewer } from "./CodeViewer";
import { BrowserPreview } from "./BrowserPreview";
import { AgentConsole } from "./AgentConsole";
import { TaskControlBar } from "./TaskControlBar";

interface IDELayoutProps {
  taskId: string;
  wsMessages: any[];
}

export function IDELayout({ taskId, wsMessages }: IDELayoutProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [modifiedFiles, setModifiedFiles] = useState<Set<string>>(new Set());
  const [previewReady, setPreviewReady] = useState(false);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [browserActions, setBrowserActions] = useState<any[]>([]);
  const [taskStatus, setTaskStatus] = useState<string>("pending");
  const [previewUrl, setPreviewUrl] = useState<string>("");

  useEffect(() => {
    for (const msg of wsMessages) {
      switch (msg.type) {
        case "file_changed": {
          setModifiedFiles((prev) => {
            const next = new Set(prev);
            next.add(msg.path);
            return next;
          });
          break;
        }
        case "browser_screenshot": {
          setScreenshots((prev) => [...prev, msg.screenshot]);
          setPreviewReady(true);
          break;
        }
        case "browser_action": {
          setBrowserActions((prev) => [...prev, msg.action]);
          break;
        }
        case "task_status": {
          setTaskStatus(msg.status);
          break;
        }
        case "preview_url": {
          setPreviewUrl(msg.url);
          break;
        }
        case "step_progress": {
          if (msg.files_changed) {
            setModifiedFiles((prev) => {
              const next = new Set(prev);
              (msg.files_changed as string[]).forEach((f: string) => next.add(f));
              return next;
            });
          }
          break;
        }
      }
    }
  }, [wsMessages]);

  const handleFileSelect = useCallback((path: string) => {
    setSelectedFile(path);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      <TaskControlBar
        taskId={taskId}
        status={taskStatus}
        previewReady={previewReady}
        previewUrl={previewUrl}
      />

      <div className="flex-1 overflow-hidden">
        <Group orientation="horizontal">
          <Panel defaultSize={20} minSize={15} maxSize={30}>
            <div className="h-full border-r border-[var(--border-primary)] overflow-hidden">
              <FileExplorer
                taskId={taskId}
                selectedFile={selectedFile}
                modifiedFiles={modifiedFiles}
                onFileSelect={handleFileSelect}
              />
            </div>
          </Panel>
          <Separator className="w-1 bg-[var(--border-primary)] hover:bg-[var(--accent-blue)] transition-colors" />

          <Panel defaultSize={55} minSize={35}>
            <Group orientation="vertical">
              <Panel defaultSize={60} minSize={30}>
                <div className="h-full overflow-hidden">
                  {selectedFile ? (
                    <CodeViewer
                      taskId={taskId}
                      filePath={selectedFile}
                      isModified={modifiedFiles.has(selectedFile)}
                    />
                  ) : (
                    <div className="h-full flex items-center justify-center text-[var(--text-secondary)]">
                      <div className="text-center space-y-2">
                        <div className="text-4xl opacity-30">{"<>"}</div>
                        <p>Select a file to view</p>
                      </div>
                    </div>
                  )}
                </div>
              </Panel>
              <Separator className="h-1 bg-[var(--border-primary)] hover:bg-[var(--accent-blue)] transition-colors" />
              <Panel defaultSize={40} minSize={20}>
                <div className="h-full border-t border-[var(--border-primary)] overflow-hidden">
                  <AgentConsole messages={wsMessages} />
                </div>
              </Panel>
            </Group>
          </Panel>
          <Separator className="w-1 bg-[var(--border-primary)] hover:bg-[var(--accent-blue)] transition-colors" />

          <Panel defaultSize={25} minSize={15} maxSize={40}>
            <div className="h-full border-l border-[var(--border-primary)] overflow-hidden">
              <BrowserPreview
                previewUrl={previewUrl}
                screenshots={screenshots}
                browserActions={browserActions}
                ready={previewReady}
              />
            </div>
          </Panel>
        </Group>
      </div>
    </div>
  );
}