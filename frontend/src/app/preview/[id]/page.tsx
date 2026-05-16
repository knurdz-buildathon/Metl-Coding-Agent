"use client";

import { useParams } from "next/navigation";

export default function PreviewPage() {
  const params = useParams();
  const previewId = params.id as string;

  const previewUrl = process.env.NEXT_PUBLIC_PREVIEW_URL
    ? `${process.env.NEXT_PUBLIC_PREVIEW_URL}/${previewId}`
    : null;

  return (
    <div className="min-h-screen bg-white">
      <div className="bg-gray-100 p-2 flex items-center gap-2 text-sm">
        <a href={`/task/${previewId}`} className="text-blue-600 hover:underline">
          &larr; Back to task
        </a>
        <span className="text-gray-400">|</span>
        <span className="text-gray-500">Preview URL: {previewUrl || `${previewId}`}</span>
        <span className="ml-auto px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">
          Preview Mode - No Real Backend
        </span>
      </div>

      {previewUrl ? (
        <iframe
          src={previewUrl}
          className="w-full h-[calc(100vh-40px)] border-none"
          title="Preview"
        />
      ) : (
        <div className="flex items-center justify-center h-[calc(100vh-40px)] text-gray-400">
          No preview available. The preview URL will appear here once the preview server is ready.
        </div>
      )}
    </div>
  );
}