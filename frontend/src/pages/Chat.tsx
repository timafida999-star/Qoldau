import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Loader2, Send, WifiOff } from "lucide-react";
import { useTranslation } from "react-i18next";

import { fetchChat, fetchMessages } from "@/api/chat";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { useChatSocket } from "@/hooks/useChatSocket";
import { apiErrorStatus } from "@/lib/apiError";
import type { ChatInfo, ChatMessage } from "@/types";

// Keep in sync with MAX_MESSAGE_CHARS in backend/app/websocket/limits.py
const MAX_MESSAGE_CHARS = 2000;

type LoadError = "unauthorized" | "notFound" | "forbidden" | "failed";

function formatTime(iso: string, locale: string) {
  return new Date(iso).toLocaleString(locale, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function mergeMessages(current: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  const byId = new Map(current.map((message) => [message.id, message]));
  for (const message of incoming) byId.set(message.id, message);
  return [...byId.values()].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at));
}

export default function ChatPage() {
  const { chatId } = useParams();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const [chatInfo, setChatInfo] = useState<ChatInfo | null>(null);
  const [loadedChatId, setLoadedChatId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<LoadError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const expireSession = useCallback(() => {
    navigate("/login", { replace: true, state: { sessionExpired: true } });
    logout();
  }, [navigate, logout]);

  // The socket opens only after the REST calls confirmed the chat and the
  // participant, so access errors surface once, with the right message.
  const socketChatId = chatId && loadedChatId === chatId ? chatId : undefined;
  const { status: socketStatus, sendMessage, reconnectNow } = useChatSocket(socketChatId, (message) => {
    setMessages((prev) => mergeMessages(prev, [message]));
  });

  useEffect(() => {
    if (!chatId) return;
    let cancelled = false;
    setChatInfo(null);
    setLoadedChatId(null);
    setLoadError(null);
    setMessages([]);

    Promise.all([fetchChat(chatId), fetchMessages(chatId)])
      .then(([info, history]) => {
        if (cancelled) return;
        setChatInfo(info);
        setMessages((prev) => mergeMessages(prev, history));
        setLoadedChatId(chatId);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = apiErrorStatus(err);
        if (status === 401) setLoadError("unauthorized");
        else if (status === 403) setLoadError("forbidden");
        else if (status === 404 || status === 422) setLoadError("notFound");
        else setLoadError("failed");
      });

    return () => {
      cancelled = true;
    };
  }, [chatId, reloadKey]);

  // Every (re)connect refetches the history: anything sent while this socket
  // was not open exists only in the database.
  useEffect(() => {
    if (socketStatus !== "open" || !socketChatId) return;
    let cancelled = false;
    fetchMessages(socketChatId)
      .then((history) => {
        if (!cancelled) setMessages((prev) => mergeMessages(prev, history));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [socketStatus, socketChatId]);

  const sessionExpired = loadError === "unauthorized" || socketStatus === "unauthorized";
  useEffect(() => {
    if (sessionExpired) expireSession();
  }, [sessionExpired, expireSession]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const content = draft.trim();
    if (!content) return;
    // Keep the draft if the socket wasn't open: clearing it unconditionally is
    // how a message disappears with no trace and no error.
    if (sendMessage(content)) setDraft("");
  }

  const accessError =
    loadError && loadError !== "unauthorized"
      ? loadError
      : socketStatus === "forbidden" || socketStatus === "notFound"
        ? socketStatus
        : null;

  if (accessError) {
    const message =
      accessError === "forbidden"
        ? t("chat.forbidden")
        : accessError === "notFound"
          ? t("chat.notFound")
          : t("chat.loadError");
    return (
      <div className="container flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-muted-foreground" role="alert">
          {message}
        </p>
        {accessError === "failed" ? (
          <Button variant="outline" onClick={() => setReloadKey((key) => key + 1)}>
            {t("common.retry")}
          </Button>
        ) : (
          <Link to="/reservations" className={buttonVariants({ variant: "outline" })}>
            {t("chat.backToReservations")}
          </Link>
        )}
      </div>
    );
  }

  if (sessionExpired || !chatInfo || !socketChatId) {
    return <div className="container py-16 text-center text-muted-foreground">{t("chat.loading")}</div>;
  }

  const isOpen = socketStatus === "open";

  return (
    <div className="chat-screen container flex max-w-2xl flex-col py-8">
      <div className="mb-4 flex items-center justify-between gap-3 border-b border-border pb-4">
        <div className="min-w-0">
          <h1 className="truncate font-semibold">{chatInfo.other_participant.full_name}</h1>
          <p className="line-clamp-2 break-words text-sm text-muted-foreground">{t("chat.about", { title: chatInfo.listing_title })}</p>
        </div>
        <span
          role="status"
          aria-live="polite"
          className={`flex shrink-0 items-center gap-1.5 text-xs ${
            isOpen ? "text-primary" : socketStatus === "reconnecting" ? "text-destructive" : "text-muted-foreground"
          }`}
        >
          {isOpen ? (
            <span className="h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
          ) : socketStatus === "reconnecting" ? (
            <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          )}
          {isOpen ? t("chat.connected") : socketStatus === "reconnecting" ? t("chat.reconnecting") : t("chat.connecting")}
        </span>
      </div>

      {socketStatus === "reconnecting" && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-secondary px-3 py-2 text-sm text-secondary-foreground">
          <span className="min-w-0 flex-[1_1_14rem]">{t("chat.connectionLost")}</span>
          <Button type="button" variant="outline" size="sm" onClick={reconnectNow}>
            {t("chat.reconnectNow")}
          </Button>
        </div>
      )}

      <div className="flex-1 space-y-3 overflow-y-auto pr-1">
        {messages.map((message) => {
          const isMine = message.sender_id === user?.id;
          return (
            <div key={message.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
              <div
                className={`min-w-0 max-w-[75%] break-words rounded-2xl px-4 py-2 text-sm shadow-soft ${
                  isMine ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                }`}
              >
                <p>{message.content}</p>
                <p className={`mt-1 text-[10px] ${isMine ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
                  {formatTime(message.created_at, i18n.language)}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-4 border-t border-border pt-4">
        <div className="flex gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={t("chat.placeholder")}
            maxLength={MAX_MESSAGE_CHARS}
            autoFocus
          />
          <Button type="submit" size="icon" disabled={!draft.trim() || !isOpen} aria-label={t("chat.send")}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
        {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
          <p className="mt-1 text-right text-xs text-muted-foreground">
            {draft.length} / {MAX_MESSAGE_CHARS}
          </p>
        )}
      </form>
    </div>
  );
}
