import { useEffect, useRef, useState } from "react";

import { getAuthToken, wsUrl } from "@/api/client";
import type { ChatMessage } from "@/types";

export function useChatSocket(chatId: string | undefined, onMessage: (message: ChatMessage) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    if (!chatId) return;

    const token = getAuthToken();
    const socket = new WebSocket(wsUrl(`/ws/chats/${chatId}?token=${token}`));
    socketRef.current = socket;

    socket.onopen = () => setIsConnected(true);
    socket.onclose = () => setIsConnected(false);
    socket.onmessage = (event) => {
      const message: ChatMessage = JSON.parse(event.data);
      onMessageRef.current(message);
    };

    return () => {
      socket.close();
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
