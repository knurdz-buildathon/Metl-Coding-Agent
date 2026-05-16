"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { IDELayout } from "@/components/IDELayout";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export default function TaskDetailPage() {
  const params = useParams();
  const taskId = params.id as string;

  const [wsMessages, setWsMessages] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef<any[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/tasks/${taskId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        messagesRef.current = [...messagesRef.current, msg];
        setWsMessages([...messagesRef.current]);
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      console.error("WebSocket error");
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  return <IDELayout taskId={taskId} wsMessages={wsMessages} />;
}