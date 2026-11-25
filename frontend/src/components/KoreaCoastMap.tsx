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

    // 대한민국 전역 중심 좌표 (위도 35.9, 경도 127.7)
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

    L.control.attribution({ position: 'bottomright' })
      .addAttribution('&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>')
      .addTo(map);

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
      if (!st.latitude || !st.longitude) return;

      const isWarning = st.alertLevel === 'WARNING';
      const isAdvisory = st.alertLevel === 'ADVISORY';
      const isSelected = selectedStation?.stationCode === st.stationCode;

      // 색상 정의 (경보: 빨강, 주의보: 주황, 정상: 짙은 네이비)
      const primaryColor = isWarning ? '#dc2626' : isAdvisory ? '#ea580c' : '#1e3a8a';
      const valColor = isWarning ? '#b91c1c' : isAdvisory ? '#c2410c' : '#0f172a';
      const pulseClass = isWarning ? 'warning-pulse' : isAdvisory ? 'advisory-pulse' : '';
      const scaleTransform = isSelected ? 'scale(1.18)' : 'scale(1)';
      const zIndexBoost = isSelected ? 1000 : isWarning ? 800 : isAdvisory ? 500 : 100;

      const customIcon = L.divIcon({
        className: 'custom-coast-marker',
        html: `
          <div style="
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            transform: ${scaleTransform};
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.45));
            user-select: none;
          ">
            <!-- 캡슐형 라벨 뱃지 -->
            <div class="${pulseClass}" style="
              display: flex;
              align-items: center;
              border-radius: 6px;
              overflow: hidden;
              background: #ffffff;
              border: 2px solid ${isSelected ? '#2563eb' : primaryColor};
              box-shadow: 0 0 0 2px #ffffff;
            ">
              <!-- 좌측: 관측소명 (고대비 유색 배경 + 흰색 굵은 텍스트) -->
              <div style="
                background-color: ${primaryColor};
                color: #ffffff;
                padding: 4px 9px;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: -0.2px;
                white-space: nowrap;
                display: flex;
                align-items: center;
                gap: 4px;
              ">
                ${isWarning ? '🚨' : isAdvisory ? '⚠️' : '⚓'}
                <span>${st.name}</span>
              </div>

              <!-- 우측: 수위 수치 (선명한 흰색 바탕 + 굵은 글씨) -->
              <div style="
                background-color: #ffffff;
                color: ${valColor};
                padding: 4px 8px;
                font-size: 13px;
                font-weight: 900;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                white-space: nowrap;
                letter-spacing: -0.5px;
              ">
                ${st.latestObsTideCm != null ? Math.round(st.latestObsTideCm) : '–'}
              </div>
            </div>

            <!-- 하단 핀 화살표 (정확한 관측소 위치 지목) -->
            <div style="
              width: 0;
              height: 0;
              border-left: 6px solid transparent;
              border-right: 6px solid transparent;
              border-top: 7px solid ${isSelected ? '#2563eb' : primaryColor};
              margin-top: -1px;
            "></div>

            <!-- 관측소 위치 정밀 점 -->
            <div style="
              width: 7px;
              height: 7px;
              border-radius: 50%;
              background-color: ${primaryColor};
              border: 1.5px solid #ffffff;
              box-shadow: 0 1px 3px rgba(0,0,0,0.5);
              margin-top: -1px;
            "></div>
          </div>
        `,
        iconSize: [120, 42],
        iconAnchor: [60, 42] // 마커의 핀 끝점이 관측소 위경도에 정확히 오도록 고정
      });

      const marker = L.marker([st.latitude, st.longitude], {
        icon: customIcon,
        zIndexOffset: zIndexBoost
      }).addTo(map);

      // 팝업 내용
      const popupHtml = `
        <div style="min-width: 200px; padding: 4px; font-family: system-ui, -apple-system, sans-serif;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 2px solid ${primaryColor}; padding-bottom: 4px;">
            <strong style="font-size: 15px; color: #1e293b;">${st.name} 관측소</strong>
            <span style="font-size: 11px; background: #e2e8f0; color: #334155; padding: 2px 6px; border-radius: 4px; font-weight: 600;">${st.seaRegion}해</span>
          </div>
          <div style="margin-bottom: 8px; font-size: 12px; color: #334155;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; align-items: center;">
              <span>예상 최고 총수위:</span>
              <strong style="color: ${primaryColor}; font-size: 15px; font-family: monospace;">${st.latestTotalTideCm} cm</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px; font-size: 11px; color: #64748b;">
              <span>주의보 기준:</span>
              <span style="font-weight: 600;">${st.advisoryThresholdCm} cm</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b;">
              <span>경보 기준:</span>
              <span style="font-weight: 600;">${st.warningThresholdCm} cm</span>
            </div>
          </div>
          <a href="/forecast?station=${st.stationCode}" style="
            display: block;
            text-align: center;
            background: #2563eb;
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            padding: 6px 10px;
            border-radius: 6px;
            text-decoration: none;
            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
          ">
            예측 모델 상세 분석 차트 보기 &rarr;
          </a>
        </div>
      `;

      marker.bindPopup(popupHtml, { offset: [0, -42] });

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
      duration: 0.8
    });
    const marker = markersRef.current[selectedStation.stationCode];
    if (marker) {
      marker.openPopup();
    }
  }, [selectedStation]);

  return (
    <div className="position-relative w-100 rounded-3 overflow-hidden border shadow-sm" style={{ height: '620px', background: '#f8f9fa' }}>
      <div ref={mapContainerRef} className="w-100 h-100" />

      {/* 지도 위 범례 오버레이 */}
      <div
        className="position-absolute bg-white p-2.5 rounded shadow-sm border"
        style={{ bottom: '16px', left: '16px', zIndex: 1000, fontSize: '0.75rem' }}
      >
        <div className="fw-bold mb-1.5 text-dark" style={{ fontSize: '0.8rem' }}>
          <i className="bi bi-shield-shaded text-primary me-1"></i> 연안 특보 위험도 범례
        </div>
        <div className="d-flex flex-column gap-1.5">
          <div className="d-flex align-items-center gap-2">
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#dc2626', display: 'inline-block' }}></span>
            <span className="fw-bold text-danger">🚨 경보 초과</span>
          </div>
          <div className="d-flex align-items-center gap-2">
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#ea580c', display: 'inline-block' }}></span>
            <span className="fw-bold text-warning-emphasis">⚠️ 주의보 초과</span>
          </div>
          <div className="d-flex align-items-center gap-2">
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#1e3a8a', display: 'inline-block' }}></span>
            <span className="fw-semibold text-secondary">⚓ 정상 수위</span>
          </div>
        </div>
      </div>
    </div>
  );
}
