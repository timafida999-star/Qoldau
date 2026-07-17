import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ImageOff, MapPin, Pencil, Star, Trash2 } from "lucide-react";

import { API_BASE_URL } from "@/api/client";
import { deleteListing, fetchListing } from "@/api/listings";
import { createReservation } from "@/api/reservations";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ReportModal } from "@/components/ReportModal";
import { useAuth } from "@/hooks/useAuth";
import type { Listing } from "@/types";
import { CATEGORY_LABELS, CONDITION_LABELS, STATUS_BADGE_VARIANT, STATUS_LABELS } from "@/utils/listingOptions";

import "@/lib/leafletIcons";
import { MapContainer, Marker, TileLayer } from "react-leaflet";

export default function ListingDetailPage() {
  const { listingId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [listing, setListing] = useState<Listing | null>(null);
  const [activeImage, setActiveImage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [reserveError, setReserveError] = useState<string | null>(null);
  const [reserveSent, setReserveSent] = useState(false);
  const [reserving, setReserving] = useState(false);

  useEffect(() => {
    if (!listingId) return;
    fetchListing(listingId)
      .then(setListing)
      .finally(() => setLoading(false));
  }, [listingId]);

  async function handleDelete() {
    if (!listing) return;
    if (!confirm("Delete this listing? This cannot be undone.")) return;
    await deleteListing(listing.id);
    navigate("/");
  }

  async function handleReserve() {
    if (!listing) return;
    setReserveError(null);
    setReserving(true);
    try {
      await createReservation(listing.id);
      setReserveSent(true);
    } catch (err: any) {
      setReserveError(err?.response?.data?.detail || "Could not send the request. Please try again.");
    } finally {
      setReserving(false);
    }
  }

  if (loading) {
    return <div className="container py-16 text-center text-muted-foreground">Loading...</div>;
  }

  if (!listing) {
    return <div className="container py-16 text-center text-muted-foreground">Listing not found.</div>;
  }

  const isOwner = user?.id === listing.owner_id;
  const cover = listing.images[activeImage];

  return (
    <div className="container max-w-4xl py-10">
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <div className="aspect-[4/3] w-full overflow-hidden rounded-xl border border-border bg-secondary shadow-soft">
            {cover ? (
              <img src={`${API_BASE_URL}${cover.image_url}`} alt={listing.title} className="h-full w-full object-cover" />
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
                  <img src={`${API_BASE_URL}${img.image_url}`} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-start justify-between gap-3">
            <h1 className="text-2xl font-semibold">{listing.title}</h1>
            <Badge variant={STATUS_BADGE_VARIANT[listing.status]}>{STATUS_LABELS[listing.status]}</Badge>
          </div>

          <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
            <span>{CATEGORY_LABELS[listing.category]}</span>
            <span>&middot;</span>
            <span>{CONDITION_LABELS[listing.condition]}</span>
          </div>

          <p className="mt-4 whitespace-pre-line text-foreground/90">{listing.description}</p>

          <Card className="mt-6">
            <CardContent className="flex items-center gap-3 p-4">
              <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-secondary text-sm font-semibold text-muted-foreground">
                {listing.owner.avatar_url ? (
                  <img
                    src={`${API_BASE_URL}${listing.owner.avatar_url}`}
                    alt={listing.owner.full_name}
                    className="h-full w-full object-cover"
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
                  Edit
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </>
            ) : listing.status === "available" ? (
              user ? (
                <Button size="lg" disabled={reserving || reserveSent} onClick={handleReserve}>
                  {reserveSent ? "Request sent" : reserving ? "Sending..." : "Reserve this item"}
                </Button>
              ) : (
                <Button size="lg" onClick={() => navigate("/login")}>
                  Log in to reserve
                </Button>
              )
            ) : (
              <Button size="lg" disabled>
                No longer available
              </Button>
            )}
          </div>
          {reserveError && <p className="mt-2 text-sm text-destructive">{reserveError}</p>}
          {reserveSent && (
            <p className="mt-2 text-sm text-muted-foreground">
              Track it on your{" "}
              <Link to="/reservations" className="font-medium text-primary hover:underline">
                reservations page
              </Link>
              .
            </p>
          )}

          {!isOwner && user && (
            <div className="mt-4">
              <ReportModal targetType="listing" targetId={listing.id} triggerLabel="Report this listing" />
            </div>
          )}
        </div>
      </div>

      <div className="mt-10">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-medium">
          <MapPin className="h-5 w-5 text-primary" />
          Meeting location
        </h2>
        {listing.address_text && <p className="mb-3 text-sm text-muted-foreground">{listing.address_text}</p>}
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
            <Marker position={[listing.latitude, listing.longitude]} />
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
