import { useEffect, useMemo } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import "@/lib/leafletIcons";
import type { ListingSummary } from "@/types";

interface MapViewProps {
  listings: ListingSummary[];
  center?: [number, number];
}

/** Cluster bubbles drawn with our own divIcon, so no plugin CSS is needed. */
function createClusterIcon(cluster: { getChildCount: () => number }) {
  const count = cluster.getChildCount();
  const size = count < 10 ? 34 : count < 50 ? 40 : 46;
  return L.divIcon({
    html: `<div style="
      width:${size}px;height:${size}px;
      display:flex;align-items:center;justify-content:center;
      background:hsl(var(--primary) / 0.92);color:hsl(var(--primary-foreground));
      border:3px solid rgba(255,255,255,0.85);border-radius:9999px;
      font:600 13px/1 system-ui,sans-serif;
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
    ">${count}</div>`,
    className: "",
    iconSize: L.point(size, size),
  });
}

/** Zoom the map to whatever set of pins is currently shown. */
function FitToListings({ listings }: { listings: ListingSummary[] }) {
  const map = useMap();
  const boundsKey = useMemo(
    () => listings.map((l) => `${l.id}:${l.latitude}:${l.longitude}`).join("|"),
    [listings]
  );

  useEffect(() => {
    if (listings.length === 0) return;
    const bounds = L.latLngBounds(listings.map((l) => [l.latitude, l.longitude] as [number, number]));
    map.fitBounds(bounds.pad(0.2), { maxZoom: 15 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boundsKey, map]);

  return null;
}

export function MapView({ listings, center }: MapViewProps) {
  const { t } = useTranslation();
  const defaultCenter: [number, number] = center ?? [
    listings[0]?.latitude ?? 51.169,
    listings[0]?.longitude ?? 71.449,
  ];

  return (
    <div className="overflow-hidden rounded-xl border border-border shadow-soft">
      <MapContainer center={defaultCenter} zoom={12} style={{ height: "480px", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MarkerClusterGroup chunkedLoading maxClusterRadius={60} iconCreateFunction={createClusterIcon}>
          {listings.map((listing) => (
            <Marker key={listing.id} position={[listing.latitude, listing.longitude]}>
              <Popup>
                <div className="space-y-1">
                  <Link to={`/listings/${listing.id}`} className="font-medium text-primary hover:underline">
                    {listing.title}
                  </Link>
                  {typeof listing.distance_km === "number" && (
                    <p className="text-xs text-muted-foreground">
                      {t("home.distanceAway", { km: listing.distance_km })}
                    </p>
                  )}
                  {listing.location_is_approximate && (
                    <p className="text-xs text-muted-foreground">{t("listing.approximateArea")}</p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
        <FitToListings listings={listings} />
      </MapContainer>
    </div>
  );
}
