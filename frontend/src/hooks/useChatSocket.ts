import { useEffect, useRef, useState } from "react";

import { getAuthToken, wsUrl } from "@/api/client";
import type { ChatMessage } from "@/types";

const MAX_RECONNECT_DELAY_MS = 15_000;

// Keep in sync with WS_CLOSE_* in backend/app/routers/chat.py
const CLOSE_UNAUTHORIZED = 4401;
const CLOSE_FORBIDDEN = 4403;
const CLOSE_NOT_FOUND = 4404;

export type ChatSocketStatus =
  | "idle"
  | "connecting"
  | "open"
  | "reconnecting"
  | "unauthorized"
  | "forbidden"
  | "notFound";

const FINAL_STATUS_BY_CLOSE_CODE: Partial<Record<number, ChatSocketStatus>> = {
  [CLOSE_UNAUTHORIZED]: "unauthorized",
  [CLOSE_FORBIDDEN]: "forbidden",
  [CLOSE_NOT_FOUND]: "notFound",
};

export function useChatSocket(chatId: string | undefined, onMessage: (message: ChatMessage) => void) {
  const [status, setStatus] = useState<ChatSocketStatus>("idle");
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectNowRef = useRef<() => void>(() => undefined);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!chatId) {
      setStatus("idle");
      return;
    }

    let disposed = false;
    let attempt = 0;
    let reconnectTimer: number | undefined;
    let socket: WebSocket | null = null;

    function connect() {
      if (disposed) return;
      window.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;

      const token = getAuthToken();
      if (!token) {
        setStatus("unauthorized");
        return;
      }

      setStatus(attempt === 0 ? "connecting" : "reconnecting");
      const ws = new WebSocket(wsUrl(`/ws/chats/${chatId}?token=${encodeURIComponent(token)}`));
      socket = ws;
      socketRef.current = ws;

      ws.onopen = () => {
        if (socketRef.current !== ws) return;
        attempt = 0;
        setStatus("open");
      };
      ws.onmessage = (event) => {
        let message: ChatMessage;
        try {
          message = JSON.parse(event.data);
        } catch {
          return;
        }
        onMessageRef.current(message);
      };
      ws.onclose = (event) => {
        // React's development double mount closes the first socket after the
        // second one is live; a superseded socket must not touch the state.
        if (socketRef.current !== ws) return;
        socketRef.current = null;
        if (disposed) return;

        const finalStatus = FINAL_STATUS_BY_CLOSE_CODE[event.code];
        if (finalStatus) {
          setStatus(finalStatus);
          return;
        }

        setStatus("reconnecting");
        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS) + Math.random() * 300;
        attempt += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      };
    }

    function reconnectNow() {
      if (disposed || reconnectTimer === undefined) return;
      connect();
    }

    reconnectNowRef.current = reconnectNow;
    window.addEventListener("online", reconnectNow);
    connect();

    return () => {
      disposed = true;
      window.clearTimeout(reconnectTimer);
      window.removeEventListener("online", reconnectNow);
      reconnectNowRef.current = () => undefined;
      socket?.close();
      if (socketRef.current === socket) socketRef.current = null;
    };
  }, [chatId]);

  /** Returns false when the socket isn't open, so the caller can keep the draft. */
  function sendMessage(content: string): boolean {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify({ content }));
    return true;
  }

  function reconnectNow() {
    reconnectNowRef.current();
  }

  return { status, sendMessage, reconnectNow };
}
