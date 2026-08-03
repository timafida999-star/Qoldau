import { useEffect, useRef, useState } from "react";

import { getAuthToken, wsUrl } from "@/api/client";
import type { ChatMessage } from "@/types";

const MAX_RECONNECT_DELAY_MS = 15_000;

export function useChatSocket(chatId: string | undefined, onMessage: (message: ChatMessage) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!chatId) return;

    // A dropped connection (backend restart, flaky network, laptop sleep) used
    // to kill the chat until a manual page reload. Reconnect with exponential
    // backoff instead; the cleanup flag stops the loop on unmount.
    let disposed = false;
    let attempt = 0;
    let reconnectTimer: number | undefined;
    let socket: WebSocket | null = null;

    function connect() {
      if (disposed) return;
      const token = getAuthToken();
      // Bound to this attempt: `socket` below is reassigned on every reconnect,
      // so the handlers must close over their own instance, not the latest one.
      const ws = new WebSocket(wsUrl(`/ws/chats/${chatId}?token=${token}`));
      socket = ws;
      socketRef.current = ws;

      ws.onopen = () => {
        attempt = 0;
        setIsConnected(true);
      };
      ws.onmessage = (event) => {
        const message: ChatMessage = JSON.parse(event.data);
        onMessageRef.current(message);
      };
      ws.onclose = () => {
        // A socket that has already been replaced must not touch the state of
        // the one that superseded it. React's development double-mount closes
        // the first socket *after* the second is live, and without this guard
        // its late onclose nulls the ref of the working socket - the chat then
        // reads as "connected" while every send is silently dropped.
        if (socketRef.current !== ws) return;

        setIsConnected(false);
        socketRef.current = null;
        if (disposed) return;
        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS) + Math.random() * 300;
        attempt += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      disposed = true;
      window.clearTimeout(reconnectTimer);
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

  return { isConnected, sendMessage };
}
