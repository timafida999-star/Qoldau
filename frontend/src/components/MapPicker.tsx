import { useState } from "react";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";
import { useTranslation } from "react-i18next";

import "@/lib/leafletIcons";

interface MapPickerProps {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lng: number) => void;
}

function ClickHandler({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export function MapPicker({ latitude, longitude, onChange }: MapPickerProps) {
  const { t } = useTranslation();
  const [position, setPosition] = useState<[number, number]>([latitude, longitude]);

  function handleChange(lat: number, lng: number) {
    setPosition([lat, lng]);
    onChange(lat, lng);
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <MapContainer center={position} zoom={13} style={{ height: "320px", width: "100%" }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={position} />
        <ClickHandler onChange={handleChange} />
      </MapContainer>
      <p className="border-t border-border bg-secondary px-3 py-2 text-xs text-muted-foreground">
        {t("form.clickMap")}
      </p>
    </div>
  );
}
