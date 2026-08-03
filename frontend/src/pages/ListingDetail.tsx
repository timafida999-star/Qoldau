import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ImageOff, Info, MapPin, Pencil, Send, Star, Trash2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { API_BASE_URL } from "@/api/client";
import { deleteListing, fetchListing } from "@/api/listings";
import { createReservation } from "@/api/reservations";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ReportModal } from "@/components/ReportModal";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/lib/apiError";
import type { Listing } from "@/types";
import { STATUS_BADGE_VARIANT } from "@/utils/listingOptions";

import "@/lib/leafletIcons";
import { Circle, MapContainer, Marker, TileLayer } from "react-leaflet";

// Matches UNCERTAINTY_RADIUS_M in backend/app/utils/geo.py: the blurred point
// is always within this circle of the true meeting spot.
const APPROX_RADIUS_M = 500;
const REQUEST_MESSAGE_MAX = 500;

export default function ListingDetailPage() {
  const { listingId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [listing, setListing] = useState<Listing | null>(null);
  const [activeImage, setActiveImage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reserveError, setReserveError] = useState<string | null>(null);
  const [reserveSent, setReserveSent] = useState(false);
  const [reserving, setReserving] = useState(false);
  const [requestFormOpen, setRequestFormOpen] = useState(false);
  const [requestMessage, setRequestMessage] = useState("");

  useEffect(() => {
    if (!listingId) return;
    fetchListing(listingId)
      .then(setListing)
      .finally(() => setLoading(false));
  }, [listingId]);

  async function handleDelete() {
    if (!listing) return;
    if (!confirm(t("listing.confirmDelete"))) return;
    await deleteListing(listing.id);
    navigate("/");
  }

  async function handleReserve() {
    if (!listing) return;
    setReserveError(null);
    setReserving(true);
    try {
      await createReservation(listing.id, requestMessage.trim() || undefined);
      setReserveSent(true);
      setRequestFormOpen(false);
    } catch (err: any) {
      setReserveError(apiErrorMessage(err, t("listing.reserveError")));
    } finally {
      setReserving(false);
    }
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">{t("common.loading")}</div>;
  }

  if (!listing) {
    return <div className="container py-16 text-center text-muted-foreground">{t("listing.notFound")}</div>;
  }

  const isOwner = user?.id === listing.owner_id;
  const cover = listing.images[activeImage];

  return (
    <div className="container max-w-4xl py-10">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <div className="aspect-[4/3] w-full overflow-hidden rounded-xl border border-border bg-secondary shadow-soft">
            {cover ? (
              <img src={`${API_BASE_URL}${cover.image_url}`} alt={listing.title} className="h-full w-full object-contain" />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-muted-foreground">
                <ImageOff className="h-10 w-10" />
              </div>
            )}
          </div>
          {listing.images.length > 1 && (
            <div className="mt-3 flex gap-2">
              {listing.images.map((img, index) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(index)}
                  className={`h-16 w-16 overflow-hidden rounded-lg border-2 ${
                    index === activeImage ? "border-primary" : "border-transparent"
                  }`}
                >
                  <img src={`${API_BASE_URL}${img.thumb_url || img.image_url}`} alt="" className="h-full w-full object-contain" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-start justify-between gap-3">
            <h1 className="min-w-0 break-words text-2xl font-semibold">{listing.title}</h1>
            <Badge variant={STATUS_BADGE_VARIANT[listing.status]}>{t(`status.${listing.status}`)}</Badge>
          </div>

          <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
            <span>{t(`category.${listing.category}`)}</span>
            <span>&middot;</span>
            <span>{t(`condition.${listing.condition}`)}</span>
          </div>

          <p className="mt-4 whitespace-pre-line break-words text-foreground/90">{listing.description}</p>

          <Card className="mt-6">
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-secondary text-sm font-semibold text-muted-foreground">
                {listing.owner.avatar_url ? (
                  <img
                    src={`${API_BASE_URL}${listing.owner.avatar_url}`}
                    alt={listing.owner.full_name}
                    className="h-full w-full object-contain"
                  />
                ) : (
                  listing.owner.full_name.charAt(0).toUpperCase()
                )}
              </div>
              <div className="flex-1">
                <Link to={`/profile/${listing.owner.id}`} className="font-medium hover:underline">
                  {listing.owner.full_name}
                </Link>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  {listing.owner.rating_avg.toFixed(1)} ({listing.owner.rating_count})
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 flex gap-3">
            {isOwner ? (
              <>
                <Button variant="outline" onClick={() => navigate(`/listings/${listing.id}/edit`)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  {t("common.edit")}
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  {t("common.delete")}
                </Button>
              </>
            ) : listing.status === "available" ? (
              user ? (
                !requestFormOpen && (
                  <Button
                    size="lg"
                    disabled={reserving || reserveSent}
                    onClick={() => setRequestFormOpen(true)}
                  >
                    {reserveSent ? t("listing.requestSent") : t("listing.reserve")}
                  </Button>
                )
              ) : (
                <Button size="lg" onClick={() => navigate("/login")}>
                  {t("listing.loginToReserve")}
                </Button>
              )
            ) : (
              <Button size="lg" disabled>
                {t("listing.noLongerAvailable")}
              </Button>
            )}
          </div>
          {requestFormOpen && !reserveSent && (
            <Card className="mt-4">
              <CardContent className="space-y-3 p-4">
                <div className="space-y-1">
                  <Label htmlFor="request-message">{t("listing.requestMessageLabel")}</Label>
                  <p className="text-xs text-muted-foreground">{t("listing.requestMessageHint")}</p>
                </div>
                <Textarea
                  id="request-message"
                  value={requestMessage}
                  onChange={(e) => setRequestMessage(e.target.value)}
                  placeholder={t("listing.requestMessagePlaceholder")}
                  maxLength={REQUEST_MESSAGE_MAX}
                  rows={3}
                  autoFocus
                />
                {requestMessage.length > REQUEST_MESSAGE_MAX * 0.9 && (
                  <p className="text-right text-xs text-muted-foreground">
                    {requestMessage.length} / {REQUEST_MESSAGE_MAX}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button disabled={reserving} onClick={handleReserve}>
                    <Send className="mr-2 h-4 w-4" />
                    {reserving ? t("listing.sending") : t("listing.sendRequest")}
                  </Button>
                  <Button variant="ghost" disabled={reserving} onClick={() => setRequestFormOpen(false)}>
                    {t("common.cancel")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          {reserveError && <p className="mt-2 text-sm text-destructive">{reserveError}</p>}
          {reserveSent && (
            <p className="mt-2 text-sm text-muted-foreground">
              {t("listing.trackPrefix")}{" "}
              <Link to="/reservations" className="font-medium text-primary hover:underline">
                {t("listing.reservationsPage")}
              </Link>
              .
            </p>
          )}

          {!isOwner && user && (
            <div className="mt-4">
              <ReportModal targetType="listing" targetId={listing.id} triggerLabel={t("listing.reportListing")} />
            </div>
          )}
        </div>
      </div>

      <div className="mt-10">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
          <MapPin className="h-5 w-5 text-primary" />
          {t("listing.meetingLocation")}
        </h2>
        {listing.address_text && <p className="mb-3 text-sm text-muted-foreground">{listing.address_text}</p>}
        {listing.location_is_approximate && (
          <div className="mb-3 flex items-start gap-2 rounded-lg border border-border bg-accent/50 px-3 py-2 text-sm text-muted-foreground">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <span>
              {t("listing.approximateArea")} {t("listing.exactAfterAccept")}
            </span>
          </div>
        )}
        <div className="overflow-hidden rounded-xl border border-border shadow-soft">
          <MapContainer
            center={[listing.latitude, listing.longitude]}
            zoom={14}
            style={{ height: "320px", width: "100%" }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {listing.location_is_approximate ? (
              <Circle
                center={[listing.latitude, listing.longitude]}
                radius={APPROX_RADIUS_M}
                pathOptions={{ color: "hsl(152 55% 40%)", fillOpacity: 0.15, weight: 2 }}
              />
            ) : (
              <Marker position={[listing.latitude, listing.longitude]} />
            )}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
