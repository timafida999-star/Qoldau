import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Send } from "lucide-react";
import { useTranslation } from "react-i18next";

import { fetchChat, fetchMessages } from "@/api/chat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { useChatSocket } from "@/hooks/useChatSocket";
import type { ChatInfo, ChatMessage } from "@/types";

function formatTime(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChatPage() {
  const { chatId } = useParams();
  const { user } = useAuth();
  const { t } = useTranslation();

  const [chatInfo, setChatInfo] = useState<ChatInfo | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { sendMessage, isConnected } = useChatSocket(chatId, (message) => {
    setMessages((prev) => [...prev, message]);
  });

  useEffect(() => {
    if (!chatId) return;
    Promise.all([fetchChat(chatId), fetchMessages(chatId)])
      .then(([info, history]) => {
        setChatInfo(info);
        setMessages(history);
      })
      .finally(() => setLoading(false));
  }, [chatId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const content = draft.trim();
    if (!content) return;
    sendMessage(content);
    setDraft("");
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">{t("chat.loading")}</div>;
  }

  if (!chatInfo) {
    return <div className="container py-16 text-center text-muted-foreground">{t("chat.notFound")}</div>;
  }

  return (
    <div className="container flex max-w-2xl flex-col py-8" style={{ height: "calc(100vh - 4rem)" }}>
      <div className="mb-4 flex items-center justify-between border-b border-border pb-4">
        <div>
          <h1 className="font-semibold">{chatInfo.other_participant.full_name}</h1>
          <p className="text-sm text-muted-foreground">{t("chat.about", { title: chatInfo.listing_title })}</p>
        </div>
        <span className={`text-xs ${isConnected ? "text-primary" : "text-muted-foreground"}`}>
          {isConnected ? t("chat.connected") : t("chat.connecting")}
        </span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((message) => {
          const isMine = message.sender_id === user?.id;
          return (
            <div key={message.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm shadow-soft ${
                  isMine ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                }`}
              >
                <p>{message.content}</p>
                <p className={`mt-1 text-[10px] ${isMine ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
                  {formatTime(message.created_at)}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-4 flex gap-2 border-t border-border pt-4">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={t("chat.placeholder")}
          autoFocus
        />
        <Button type="submit" size="icon" disabled={!draft.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
