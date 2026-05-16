"use client";

import { useState, useRef, useEffect } from "react";
import { Monitor, Camera, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface BrowserPreviewProps {
  previewUrl: string;
  screenshots: string[];
  browserActions: any[];
  ready: boolean;
}

export function BrowserPreview({
  previewUrl,
  screenshots,
  browserActions,
  ready,
}: BrowserPreviewProps) {
  const [activeTab, setActiveTab] = useState<"preview" | "screenshots">("preview");
  const [screenshotIndex, setScreenshotIndex] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (screenshots.length > 0) {
      setScreenshotIndex(screenshots.length - 1);
    }
  }, [screenshots]);

  return (
    <div className="h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-[var(--border-primary)]">
        <button
          onClick={() => setActiveTab("preview")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors",
            activeTab === "preview"
              ? "text-[var(--accent-blue)] border-b-2 border-[var(--accent-blue)]"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          )}
        >
          <Monitor className="w-3.5 h-3.5" />
          Preview
        </button>
        <button
          onClick={() => setActiveTab("screenshots")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors",
            activeTab === "screenshots"
              ? "text-[var(--accent-blue)] border-b-2 border-[var(--accent-blue)]"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          )}
        >
          <Camera className="w-3.5 h-3.5" />
          Inspection
          {screenshots.length > 0 && (
            <span className="ml-1 px-1 rounded text-[10px] bg-[var(--accent-blue)]/20 text-[var(--accent-blue)]">
              {screenshots.length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "preview" && (
          <div className="h-full flex flex-col">
            {ready && previewUrl ? (
              <iframe
                ref={iframeRef}
                src={previewUrl}
                className="flex-1 border-0 bg-white"
                title="Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              <div className="flex-1 flex items-center justify-center text-sm text-[var(--text-secondary)]">
                <div className="text-center space-y-2">
                  <Monitor className="w-8 h-8 mx-auto opacity-30" />
                  <p>Preview will appear here</p>
                  <p className="text-xs opacity-70">when the dev server starts</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "screenshots" && (
          <div className="h-full flex flex-col">
            {screenshots.length > 0 ? (
              <>
                <div className="flex-1 overflow-auto flex items-center justify-center p-2 bg-black">
                  <img
                    src={`data:image/png;base64,${screenshots[screenshotIndex]}`}
                    alt={`Screenshot ${screenshotIndex + 1}`}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
                <div className="flex items-center justify-between px-2 py-1.5 bg-[var(--bg-tertiary)] border-t border-[var(--border-primary)]">
                  <button
                    onClick={() => setScreenshotIndex((prev) => Math.max(0, prev - 1))}
                    disabled={screenshotIndex === 0}
                    className="p-1 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-xs text-[var(--text-secondary)]">
                    {screenshotIndex + 1} / {screenshots.length}
                  </span>
                  <button
                    onClick={() =>
                      setScreenshotIndex((prev) => Math.min(screenshots.length - 1, prev + 1))
                    }
                    disabled={screenshotIndex === screenshots.length - 1}
                    className="p-1 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-sm text-[var(--text-secondary)]">
                <div className="text-center space-y-2">
                  <Camera className="w-8 h-8 mx-auto opacity-30" />
                  <p>No screenshots yet</p>
                  <p className="text-xs opacity-70">browser inspection snapshots</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Browser actions log */}
      {browserActions.length > 0 && (
        <div className="border-t border-[var(--border-primary)] max-h-32 overflow-y-auto">
          <div className="px-3 py-1.5 text-[10px] text-[var(--text-secondary)] uppercase font-medium">
            Browser Actions
          </div>
          {browserActions.slice(-10).map((action, i) => (
            <div
              key={i}
              className="px-3 py-1 text-[11px] text-[var(--text-secondary)] border-t border-[var(--border-primary)]/50"
            >
              {typeof action === "string" ? action : JSON.stringify(action)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}