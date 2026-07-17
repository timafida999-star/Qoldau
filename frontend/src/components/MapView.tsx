import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { Link } from "react-router-dom";

import "@/lib/leafletIcons";
import type { ListingSummary } from "@/types";

interface MapViewProps {
  listings: ListingSummary[];
  center?: [number, number];
}

export function MapView({ listings, center }: MapViewProps) {
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
        {listings.map((listing) => (
          <Marker key={listing.id} position={[listing.latitude, listing.longitude]}>
            <Popup>
              <Link to={`/listings/${listing.id}`} className="font-medium text-primary hover:underline">
                {listing.title}
              </Link>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
