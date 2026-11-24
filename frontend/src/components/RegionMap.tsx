"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Region } from "../types/forecast";

export default function RegionMap({ region }: { region: Region }) {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    L.Icon.Default.mergeOptions({
      iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });

    const map = L.map(mapRef.current).setView([region.lat, region.lng], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    L.marker([region.lat, region.lng])
      .addTo(map)
      .bindPopup(`${region.city} ${region.name}`);

    return () => {
      map.remove();
    };
  }, [region]);

  return (
    <div
      ref={mapRef}
      style={{ height: "400px", width: "100%" }}
      className="rounded-xl"
    />
  );
}
