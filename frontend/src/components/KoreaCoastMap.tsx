'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { StationSummary } from '../types/api';

interface KoreaCoastMapProps {
  stations: StationSummary[];
  selectedStation: StationSummary | null;
  onSelectStation: (station: StationSummary) => void;
}

export default function KoreaCoastMap({
  stations,
  selectedStation,
  onSelectStation
}: KoreaCoastMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<{ [code: string]: L.Marker }>({});

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // 대한민국 전역 중심 좌표 (위도 35.8, 경도 127.8)
    const map = L.map(mapContainerRef.current, {
      center: [35.9, 127.7],
      zoom: 7,
      minZoom: 6,
      maxZoom: 12,
      zoomControl: true,
      attributionControl: false
    });

    // OpenStreetMap 공식 무료 공개 타일 (API 키 불필요)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 관측소 마커 렌더링 및 갱신
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // 기존 마커 제거
    Object.values(markersRef.current).forEach((m) => m.remove());
    markersRef.current = {};

    stations.forEach((st) => {
      // 위도 경도 검증
      if (!st.latitude || !st.longitude) return;

      const isWarning = st.alertLevel === 'WARNING';
      const isAdvisory = st.alertLevel === 'ADVISORY';
      const isSelected = selectedStation?.stationCode === st.stationCode;

      const badgeBg = isWarning ? '#dc3545' : isAdvisory ? '#fd7e14' : '#198754';
      const pulseColor = isWarning ? 'rgba(220, 53, 69, 0.5)' : isAdvisory ? 'rgba(253, 126, 20, 0.4)' : 'transparent';
      const pulseAnim = (isWarning || isAdvisory) ? 'pulse-wave 1.8s infinite ease-out' : 'none';

      const customIcon = L.divIcon({
        className: 'custom-coast-marker',
        html: `
          <div style="position: relative; transform: translate(-50%, -50%); cursor: pointer;">
            <div style="
              position: absolute;
              top: -8px; left: -8px; right: -8px; bottom: -8px;
              border-radius: 9999px;
              background-color: ${pulseColor};
              animation: ${pulseAnim};
              pointer-events: none;
            "></div>
            <div style="
              display: flex;
              align-items: center;
              gap: 4px;
              background: #ffffff;
              padding: 3px 8px;
              border-radius: 20px;
              box-shadow: 0 2px 8px rgba(0,0,0,0.25);
              border: ${isSelected ? '2.5px solid #0d6efd' : `1.5px solid ${badgeBg}`};
              white-space: nowrap;
              font-family: system-ui, -apple-system, sans-serif;
              transition: transform 0.15s ease;
            ">
              <span style="
                width: 9px;
                height: 9px;
                border-radius: 50%;
                background-color: ${badgeBg};
                display: inline-block;
              "></span>
              <strong style="font-size: 11px; color: #212529;">${st.name}</strong>
              <span style="
                font-size: 11px;
                font-weight: 700;
                color: ${badgeBg};
                font-family: monospace;
              ">${Math.round(st.latestTotalTideCm)}<span style="font-size: 9px; font-weight: normal; color: #6c757d;">cm</span></span>
            </div>
          </div>
        `,
        iconSize: [0, 0]
      });

      const marker = L.marker([st.latitude, st.longitude], { icon: customIcon }).addTo(map);

      // 팝업 내용
      const popupHtml = `
        <div style="min-width: 190px; padding: 4px; font-family: system-ui, -apple-system, sans-serif;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;">
            <strong style="font-size: 14px; color: #212529;">${st.name} 관측소</strong>
            <span style="font-size: 11px; background: #e9ecef; color: #495057; padding: 2px 6px; border-radius: 4px;">${st.seaRegion}해</span>
          </div>
          <div style="margin-bottom: 6px; font-size: 12px; color: #495057;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span>예상 총수위:</span>
              <strong style="color: ${badgeBg}; font-size: 13px;">${st.latestTotalTideCm} cm</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px; font-size: 11px;">
              <span>주의보 기준:</span>
              <span>${st.advisoryThresholdCm} cm</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px;">
              <span>경보 기준:</span>
              <span>${st.warningThresholdCm} cm</span>
            </div>
          </div>
          <a href="/forecast?station=${st.stationCode}" style="
            display: block;
            text-align: center;
            background: #0d6efd;
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            padding: 5px 8px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 8px;
          ">
            예측 모델 분석 차트 보기 &rarr;
          </a>
        </div>
      `;

      marker.bindPopup(popupHtml);

      marker.on('click', () => {
        onSelectStation(st);
      });

      markersRef.current[st.stationCode] = marker;
    });
  }, [stations, selectedStation, onSelectStation]);

  // 외부에서 관측소 선택 시 지도 중심 이동
  useEffect(() => {
    if (!selectedStation || !mapInstanceRef.current) return;
    const map = mapInstanceRef.current;
    map.flyTo([selectedStation.latitude, selectedStation.longitude], 8.5, {
      duration: 1.0
    });
    const marker = markersRef.current[selectedStation.stationCode];
    if (marker) {
      marker.openPopup();
    }
  }, [selectedStation]);

  return (
    <div className="position-relative w-100 rounded-3 overflow-hidden border shadow-sm" style={{ height: '620px', background: '#f8f9fa' }}>
      <style jsx global>{`
        @keyframes pulse-wave {
          0% {
            transform: scale(0.9);
            opacity: 0.9;
          }
          70% {
            transform: scale(2.2);
            opacity: 0;
          }
          100% {
            transform: scale(2.4);
            opacity: 0;
          }
        }
        .custom-coast-marker {
          background: transparent !important;
          border: none !important;
        }
      `}</style>
      <div ref={mapContainerRef} className="w-100 h-100" />

      {/* 지도 위 범례 오버레이 */}
      <div
        className="position-absolute bg-white p-2 rounded shadow-sm border"
        style={{ bottom: '16px', left: '16px', zIndex: 1000, fontSize: '0.75rem' }}
      >
        <div className="fw-bold mb-1.5 text-dark" style={{ fontSize: '0.8rem' }}>
          <i className="bi bi-shield-shaded text-primary me-1"></i> 해안 침수 위험도 범례
        </div>
        <div className="d-flex flex-column gap-1">
          <div className="d-flex align-items-center gap-1.5">
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#dc3545', display: 'inline-block' }}></span>
            <span className="fw-semibold text-danger">🚨 경보 초과</span>
          </div>
          <div className="d-flex align-items-center gap-1.5">
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#fd7e14', display: 'inline-block' }}></span>
            <span className="fw-semibold text-warning-emphasis">⚠️ 주의보 초과</span>
          </div>
          <div className="d-flex align-items-center gap-1.5">
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#198754', display: 'inline-block' }}></span>
            <span className="text-secondary">✅ 정상 수위</span>
          </div>
        </div>
      </div>
    </div>
  );
}
