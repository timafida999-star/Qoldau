import { useCallback, useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/api/notifications";
import type { AppNotification } from "@/types";
import { timeAgo } from "@/utils/time";

const POLL_INTERVAL_MS = 20000;

export function NotificationBell() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const refreshCount = useCallback(async () => {
    try {
      setUnread(await fetchUnreadCount());
    } catch {
      // Ignore polling failures; the next tick will retry.
    }
  }, []);

  useEffect(() => {
    refreshCount();
    const timer = setInterval(refreshCount, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refreshCount]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next) return;

    setLoading(true);
    try {
      setItems(await fetchNotifications());
    } finally {
      setLoading(false);
    }
  }

  async function handleItemClick(notification: AppNotification) {
    setOpen(false);
    if (!notification.is_read) {
      await markNotificationRead(notification.id);
      setItems((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n))
      );
      refreshCount();
    }
    if (notification.link) navigate(notification.link);
  }

  async function handleMarkAll() {
    await markAllNotificationsRead();
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnread(0);
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={toggle}
        aria-label={t("notifications.title")}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-background shadow-lg">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <span className="text-sm font-semibold">{t("notifications.title")}</span>
            {unread > 0 && (
              <button
                onClick={handleMarkAll}
                className="text-xs font-medium text-primary hover:underline"
              >
                {t("notifications.markAllRead")}
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                {t("common.loading")}
              </p>
            ) : items.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                {t("notifications.empty")}
              </p>
            ) : (
              items.map((notification) => (
                <button
                  key={notification.id}
                  onClick={() => handleItemClick(notification)}
                  className={`flex w-full flex-col items-start gap-1 border-b border-border px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-secondary ${
                    notification.is_read ? "" : "bg-accent/40"
                  }`}
                >
                  <span className="flex w-full items-start gap-2">
                    {!notification.is_read && (
                      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                    )}
                    <span className="text-sm text-foreground">
                      {t(`notifications.types.${notification.type}`, {
                        actor: notification.actor_name ?? "",
                        title: notification.entity_title ?? "",
                      })}
                    </span>
                  </span>
                  <span className="pl-4 text-xs text-muted-foreground">
                    {timeAgo(notification.created_at, i18n.language)}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
