import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Check, MessageCircle, QrCode, Users, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { actOnReservation, listMyReservations } from "@/api/reservations";
import { API_BASE_URL } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StarRating } from "@/components/StarRating";
import { timeAgo } from "@/utils/time";
import type { Reservation } from "@/types";

const STATUS_VARIANT: Record<Reservation["status"], "default" | "secondary" | "outline" | "destructive"> = {
  pending: "secondary",
  accepted: "default",
  declined: "destructive",
  cancelled: "outline",
};

function RequesterAvatar({ requester }: { requester: Reservation["requester"] }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full bg-secondary text-sm font-semibold text-muted-foreground">
      {requester.avatar_url ? (
        <img src={`${API_BASE_URL}${requester.avatar_url}`} alt={requester.full_name} className="h-full w-full object-cover" />
      ) : (
        requester.full_name.charAt(0).toUpperCase()
      )}
    </div>
  );
}

export default function ReservationsPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [tab, setTab] = useState<"received" | "sent">("received");
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listMyReservations();
      setReservations(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAction(reservation: Reservation, action: "accept" | "decline" | "cancel") {
    setActingId(reservation.id);
    try {
      await actOnReservation(reservation.id, action);
      await load();
    } finally {
      setActingId(null);
    }
  }

  async function handleCancelAccepted(reservation: Reservation) {
    if (!confirm(t("reservations.confirmCancelExchange"))) return;
    await handleAction(reservation, "cancel");
  }

  const received = reservations.filter((r) => r.role === "owner");
  const sent = reservations.filter((r) => r.role === "requester");

  // The owner picks a recipient per listing, so pending requests are grouped
  // by the item they compete for.
  const pendingGroups = useMemo(() => {
    const groups = new Map<string, { listing: Reservation["listing"]; requests: Reservation[] }>();
    for (const reservation of reservations) {
      if (reservation.role !== "owner" || reservation.status !== "pending") continue;
      const group = groups.get(reservation.listing.id) ?? { listing: reservation.listing, requests: [] };
      group.requests.push(reservation);
      groups.set(reservation.listing.id, group);
    }
    return [...groups.values()];
  }, [reservations]);

  const restReceived = received.filter((r) => r.status !== "pending");
  const currentList = tab === "received" ? received : sent;

  function renderFlatCard(reservation: Reservation) {
    return (
      <Card key={reservation.id}>
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <Link to={`/listings/${reservation.listing.id}`} className="font-medium hover:underline">
              {reservation.listing.title}
            </Link>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              {tab === "received" ? (
                <span>{t("reservations.from", { name: reservation.requester.full_name })}</span>
              ) : (
                <span>{t("reservations.requestedByYou")}</span>
              )}
              <Badge variant={STATUS_VARIANT[reservation.status]}>
                {t(`reservationStatus.${reservation.status}`)}
              </Badge>
            </div>
            {reservation.message && (
              <p className="mt-2 break-words rounded-lg bg-secondary/60 px-3 py-2 text-sm text-foreground/90">
                {reservation.message}
              </p>
            )}
          </div>

          <div className="flex shrink-0 flex-wrap gap-2">
            {tab === "sent" && reservation.status === "pending" && (
              <Button
                size="sm"
                variant="outline"
                disabled={actingId === reservation.id}
                onClick={() => handleAction(reservation, "cancel")}
              >
                {t("reservations.cancel")}
              </Button>
            )}
            {reservation.status === "accepted" && reservation.chat_id && (
              <Button size="sm" variant="secondary" onClick={() => navigate(`/chats/${reservation.chat_id}`)}>
                <MessageCircle className="mr-1 h-4 w-4" />
                {t("reservations.openChat")}
              </Button>
            )}
            {reservation.status === "accepted" && reservation.exchange_id && (
              <Button size="sm" variant="outline" onClick={() => navigate(`/exchanges/${reservation.exchange_id}`)}>
                <QrCode className="mr-1 h-4 w-4" />
                {tab === "received" ? t("reservations.showQr") : t("reservations.confirmExchange")}
              </Button>
            )}
            {/* Either side can back out until the handover actually happens.
                Once the listing reads "completed" the exchange is done and
                the backend refuses to cancel, so drop the button. */}
            {reservation.status === "accepted" && reservation.listing.status !== "completed" && (
              <Button
                size="sm"
                variant="outline"
                disabled={actingId === reservation.id}
                onClick={() => handleCancelAccepted(reservation)}
              >
                <X className="mr-1 h-4 w-4" />
                {t("reservations.cancelExchange")}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="container max-w-3xl py-10">
      <h1 className="mb-6 text-2xl font-semibold">{t("reservations.title")}</h1>

      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setTab("received")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "received" ? "bg-accent text-primary" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          {t("reservations.received")}
        </button>
        <button
          onClick={() => setTab("sent")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            tab === "sent" ? "bg-accent text-primary" : "text-muted-foreground hover:bg-secondary"
          }`}
        >
          {t("reservations.sent")}
        </button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">{t("common.loading")}</p>
      ) : currentList.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
          {t("reservations.empty")}
        </p>
      ) : tab === "sent" ? (
        <div className="space-y-4">{sent.map(renderFlatCard)}</div>
      ) : (
        <div className="space-y-8">
          {pendingGroups.length > 0 && (
            <section>
              <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
                <Users className="h-5 w-5 text-primary" />
                {t("reservations.pendingHeader")}
              </h2>
              <div className="space-y-4">
                {pendingGroups.map((group) => (
                  <Card key={group.listing.id}>
                    <CardContent className="p-4">
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <Link to={`/listings/${group.listing.id}`} className="font-medium hover:underline">
                          {group.listing.title}
                        </Link>
                        <Badge variant="secondary">
                          {t("reservations.requestCount", { count: group.requests.length })}
                        </Badge>
                      </div>
                      <p className="mb-2 text-xs text-muted-foreground">{t("reservations.chooseHint")}</p>
                      <div className="divide-y divide-border">
                        {group.requests.map((reservation) => (
                          <div
                            key={reservation.id}
                            className="flex flex-col gap-3 py-4 sm:flex-row sm:items-start sm:justify-between"
                          >
                            <div className="flex min-w-0 flex-1 gap-3">
                              <RequesterAvatar requester={reservation.requester} />
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                  <Link
                                    to={`/profile/${reservation.requester.id}`}
                                    className="font-medium hover:underline"
                                  >
                                    {reservation.requester.full_name}
                                  </Link>
                                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                    <StarRating value={Math.round(reservation.requester.rating_avg)} readOnly size={13} />
                                    {reservation.requester.rating_avg.toFixed(1)} ({reservation.requester.rating_count})
                                  </span>
                                </div>
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                  {timeAgo(reservation.created_at, i18n.language)}
                                </p>
                                {reservation.message ? (
                                  <p className="mt-2 break-words rounded-lg bg-secondary/60 px-3 py-2 text-sm text-foreground/90">
                                    {reservation.message}
                                  </p>
                                ) : (
                                  <p className="mt-2 text-sm italic text-muted-foreground">
                                    {t("reservations.noMessage")}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex shrink-0 gap-2 sm:pt-1">
                              <Button
                                size="sm"
                                disabled={actingId === reservation.id}
                                onClick={() => handleAction(reservation, "accept")}
                              >
                                <Check className="mr-1 h-4 w-4" />
                                {t("reservations.accept")}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={actingId === reservation.id}
                                onClick={() => handleAction(reservation, "decline")}
                              >
                                <X className="mr-1 h-4 w-4" />
                                {t("reservations.decline")}
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {restReceived.length > 0 && (
            <section>
              {pendingGroups.length > 0 && (
                <h2 className="mb-3 text-lg font-medium text-muted-foreground">
                  {t("reservations.restHeader")}
                </h2>
              )}
              <div className="space-y-4">{restReceived.map(renderFlatCard)}</div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
