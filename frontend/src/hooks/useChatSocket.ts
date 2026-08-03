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
      socket = new WebSocket(wsUrl(`/ws/chats/${chatId}?token=${token}`));
      socketRef.current = socket;

      socket.onopen = () => {
        attempt = 0;
        setIsConnected(true);
      };
      socket.onmessage = (event) => {
        const message: ChatMessage = JSON.parse(event.data);
        onMessageRef.current(message);
      };
      socket.onclose = () => {
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
      socketRef.current = null;
    };
  }, [chatId]);

  function sendMessage(content: string) {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ content }));
    }
  }

  return { isConnected, sendMessage };
}
