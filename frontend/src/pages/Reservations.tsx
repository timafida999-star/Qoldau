import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Check, MessageCircle, QrCode, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { actOnReservation, listMyReservations } from "@/api/reservations";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Reservation } from "@/types";

const STATUS_VARIANT: Record<Reservation["status"], "default" | "secondary" | "outline" | "destructive"> = {
  pending: "secondary",
  accepted: "default",
  declined: "destructive",
  cancelled: "outline",
};

export default function ReservationsPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
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

  const filtered = reservations.filter((r) => r.role === tab.replace("received", "owner").replace("sent", "requester"));

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
      ) : filtered.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border p-10 text-center text-muted-foreground">
          {t("reservations.empty")}
        </p>
      ) : (
        <div className="space-y-4">
          {filtered.map((reservation) => (
            <Card key={reservation.id}>
              <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
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
                </div>

                <div className="flex gap-2">
                  {tab === "received" && reservation.status === "pending" && (
                    <>
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
                    </>
                  )}
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
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
