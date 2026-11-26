'use client';

import React from 'react';
import { ForecastPoint, ObservationPoint } from '../types/api';

interface DoubleCurveChartProps {
  points: ForecastPoint[];
  advisoryThreshold: number;
  warningThreshold: number;
  stationName: string;
  history?: ObservationPoint[];
  baseTime?: string;
}

export default function DoubleCurveChart({
  points,
  advisoryThreshold,
  warningThreshold,
  stationName,
  history,
  baseTime,
}: DoubleCurveChartProps) {
  if (!points || points.length === 0) {
    return (
      <div className="card shadow-sm p-4 text-center text-muted">
        예측 데이터가 수신되지 않았습니다.
      </div>
    );
  }

  // ---- 과거 관측값 정리 (실측이 없는 행은 제외) ----
  const hist = (history ?? []).filter(
    (h) =>
      (typeof h.tideObsCm === 'number' && !isNaN(h.tideObsCm)) ||
      (typeof h.tidePredCm === 'number' && !isNaN(h.tidePredCm))
  );
  const histObs = hist.filter((h) => typeof h.tideObsCm === 'number' && !isNaN(h.tideObsCm));
  const histAstro = hist.filter((h) => typeof h.tidePredCm === 'number' && !isNaN(h.tidePredCm));

  // ---- 시간 축 (과거 24h + 예측 12h/24h) ----
  const toMs = (s: string) => Date.parse(s);
  const histTimes = hist.map((h) => toMs(h.obsTime)).filter((t) => !isNaN(t));
  const predTimes = points.map((p) => toMs(p.targetTime)).filter((t) => !isNaN(t));
  const allTimes = [...histTimes, ...predTimes];
  const tMin = allTimes.length > 0 ? Math.min(...allTimes) : 0;
  const tMax = allTimes.length > 0 ? Math.max(...allTimes) : 1;
  const tSpan = tMax - tMin || 1;

  // ---- 스케일 계산 (과거 관측값도 포함) ----
  const allTotalTides = [
    ...points.map((p) => p.totalTideCm),
    ...histObs.map((h) => h.tideObsCm as number),
  ];
  const allAstro = [
    ...points.map((p) => p.astronomicalTideCm),
    ...histAstro.map((h) => h.tidePredCm as number),
  ];
  const allResiduals = points.map((p) => p.residualCm);
  const maxTide = Math.max(...allTotalTides, ...allAstro, warningThreshold + 20, 100);
  const minTide = Math.min(...allAstro.map((v) => v - 20), 0);

  const maxResidual = Math.max(...allResiduals, 45);
  const minResidual = Math.min(...allResiduals, -10, 0);

  const width = 840;
  const height = 300;
  const paddingLeft = 60;
  const paddingRight = 60;
  const paddingTop = 35;
  const paddingBottom = 40;
  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  // Y 좌표 환산
  const getYTotal = (val: number) => {
    return paddingTop + chartH - ((val - minTide) / (maxTide - minTide || 1)) * chartH;
  };

  const getYResidual = (val: number) => {
    return paddingTop + chartH - ((val - minResidual) / (maxResidual - minResidual || 1)) * (chartH * 0.42);
  };

  // X 좌표 환산 (시간 기준)
  const getX = (timeMs: number) => paddingLeft + ((timeMs - tMin) / tSpan) * chartW;

  // "현재" 경계 (예측 기준 시각, 없으면 가장 최근 관측 시각)
  const baseMs = baseTime ? Date.parse(baseTime) : NaN;
  const nowMs = !isNaN(baseMs) ? baseMs : histTimes.length > 0 ? Math.max(...histTimes) : NaN;
  const showNow = histTimes.length > 0 && !isNaN(nowMs) && nowMs >= tMin && nowMs <= tMax;
  const nowX = showNow ? getX(nowMs) : 0;

  // 과거 관측 선 (폴리라인 — 실제 측정값이라 선으로 연결)
  const histObsPath = histObs
    .map((h, i) => `${i === 0 ? 'M' : 'L'} ${getX(toMs(h.obsTime))} ${getYTotal(h.tideObsCm as number)}`)
    .join(' ');
  const histAstroPath = histAstro
    .map((h, i) => `${i === 0 ? 'M' : 'L'} ${getX(toMs(h.obsTime))} ${getYTotal(h.tidePredCm as number)}`)
    .join(' ');

  const advisoryY = getYTotal(advisoryThreshold);
  const warningY = getYTotal(warningThreshold);

  // 시간 라벨 포맷 (MM/DD HH:mm)
  const fmtTime = (ms: number) => {
    const d = new Date(ms);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mi = String(d.getMinutes()).padStart(2, '0');
    return `${mm}/${dd} ${hh}:${mi}`;
  };

  // X축 시간 눈금 (3시간 간격 — 어느 시점의 점인지 알 수 있게)
  const fmtTick = (ms: number) => {
    const d = new Date(ms);
    const hh = String(d.getHours()).padStart(2, '0');
    const mi = String(d.getMinutes()).padStart(2, '0');
    return `${hh}:${mi}`;
  };
  const tickIntervalMs = 3 * 60 * 60 * 1000;
  const tickTimes: number[] = [];
  for (let t = tMin; t <= tMax; t += tickIntervalMs) {
    tickTimes.push(t);
  }
  const predXs = points.map((p) => getX(toMs(p.targetTime)));
  const startX = getX(tMin);
  const tickTooClose = (x: number) => {
    if (Math.abs(x - startX) < 70) return true;
    return predXs.some((px) => Math.abs(x - px) < 70);
  };

  return (
    <div className="card shadow-sm mb-3">
      {/* 카드 헤더 (Bootstrap Card Header) */}
      <div className="card-header d-flex flex-wrap align-items-center justify-content-between py-2 px-3 bg-white">
        <div className="d-flex align-items-center gap-2">
          <i className="bi bi-graph-up text-primary fs-6"></i>
          <span className="fw-bold text-dark fs-6">{stationName} 연안 이중 출력 예측 시점</span>
          <span className="badge bg-light text-secondary border">PRD Q7 &middot; F1</span>
        </div>

        {/* 범례 (Bootstrap Badges) */}
        <div className="d-flex flex-wrap align-items-center gap-2" style={{ fontSize: '0.78rem' }}>
          <span className="badge bg-light text-secondary border d-flex align-items-center gap-1">
            <span style={{ width: 14, height: 3, backgroundColor: '#0d6efd', display: 'inline-block' }}></span>
            과거 실측 (24h)
          </span>
          <span className="badge bg-primary-subtle text-primary border border-primary-subtle d-flex align-items-center gap-1">
            <span style={{ width: 9, height: 9, borderRadius: '50%', backgroundColor: '#0d6efd', display: 'inline-block' }}></span>
            총 수위(cm)
          </span>
          <span className="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1">
            <span style={{ width: 9, height: 9, borderRadius: '50%', backgroundColor: '#adb5bd', display: 'inline-block' }}></span>
            천문조(cm)
          </span>
          <span className="badge bg-purple-subtle text-purple border d-flex align-items-center gap-1" style={{ backgroundColor: '#f3e8ff', color: '#6f42c1' }}>
            <span style={{ width: 9, height: 9, borderRadius: '50%', backgroundColor: '#6f42c1', display: 'inline-block' }}></span>
            잔차(cm)
          </span>
          <span className="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle">
            주의보선 ({advisoryThreshold}cm)
          </span>
          <span className="badge bg-danger-subtle text-danger border border-danger-subtle">
            경보선 ({warningThreshold}cm)
          </span>
        </div>
      </div>

      {/* 카드 바디 (SVG Chart) */}
      <div className="card-body p-3">
        <div className="w-100 overflow-auto">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-100 select-none" style={{ minWidth: 680 }}>
            {/* 그리드 가이드라인 */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y = paddingTop + chartH * ratio;
              const val = Math.round(maxTide - ratio * (maxTide - minTide));
              return (
                <g key={ratio}>
                  <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#e9ecef" strokeWidth="1" strokeDasharray={ratio === 1 ? 'none' : '3 3'} />
                  <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="font-monospace" fill="#6c757d" fontSize="10">
                    {val}cm
                  </text>
                </g>
              );
            })}

            {/* 주의보 기준선 (Warning line) */}
            {advisoryY >= paddingTop && advisoryY <= paddingTop + chartH && (
              <g>
                <line x1={paddingLeft} y1={advisoryY} x2={width - paddingRight} y2={advisoryY} stroke="#ffc107" strokeWidth="1.5" strokeDasharray="4 3" />
                <rect x={width - paddingRight + 2} y={advisoryY - 8} width="56" height="16" rx="3" fill="#fff3cd" stroke="#ffe69c" />
                <text x={width - paddingRight + 30} y={advisoryY + 4} textAnchor="middle" fill="#664d03" fontSize="9" fontWeight="bold">
                  주의보 {advisoryThreshold}
                </text>
              </g>
            )}

            {/* 경보 기준선 (Danger line) */}
            {warningY >= paddingTop && warningY <= paddingTop + chartH && (
              <g>
                <line x1={paddingLeft} y1={warningY} x2={width - paddingRight} y2={warningY} stroke="#dc3545" strokeWidth="2" strokeDasharray="3 2" />
                <rect x={width - paddingRight + 2} y={warningY - 8} width="56" height="16" rx="3" fill="#f8d7da" stroke="#f5c2c7" />
                <text x={width - paddingRight + 30} y={warningY + 4} textAnchor="middle" fill="#842029" fontSize="9" fontWeight="bold">
                  경보 {warningThreshold}
                </text>
              </g>
            )}

            {/* 과거 관측 실측 선 (실제 측정값이라 선으로 연결) */}
            {histObsPath && (
              <path d={histObsPath} fill="none" stroke="#0d6efd" strokeWidth="2.5" strokeLinecap="round" />
            )}
            {histAstroPath && (
              <path d={histAstroPath} fill="none" stroke="#adb5bd" strokeWidth="2" strokeDasharray="4 3" />
            )}

            {/* 과거 관측 점 마커 (작은 점) */}
            {histObs.map((h) => (
              <circle key={`obs-${h.obsTime}`} cx={getX(toMs(h.obsTime))} cy={getYTotal(h.tideObsCm as number)} r="2.5" fill="#0d6efd" />
            ))}

            {/* "현재" 경계선 (과거/예측 구분) */}
            {showNow && (
              <g>
                <line x1={nowX} y1={paddingTop} x2={nowX} y2={paddingTop + chartH} stroke="#495057" strokeWidth="1.5" />
                <text x={nowX} y={paddingTop - 8} textAnchor="middle" fill="#495057" fontSize="10" fontWeight="bold">
                  현재
                </text>
              </g>
            )}

            {/* 과거 시작 시간 라벨 */}
            {histTimes.length > 0 && (
              <text x={getX(tMin)} y={paddingTop + chartH + 18} textAnchor="middle" fill="#6c757d" fontSize="10">
                {fmtTime(tMin)}
              </text>
            )}

            {/* X축 시간 눈금 (3시간 간격 — 예측 라벨과 겹치는 위치는 생략) */}
            {tickTimes.map((t) => {
              const tx = getX(t);
              if (tickTooClose(tx)) return null;
              return (
                <g key={`tick-${t}`}>
                  <line x1={tx} y1={paddingTop + chartH} x2={tx} y2={paddingTop + chartH + 4} stroke="#adb5bd" strokeWidth="1" />
                  <text x={tx} y={paddingTop + chartH + 18} textAnchor="middle" fill="#6c757d" fontSize="10">
                    {fmtTick(t)}
                  </text>
                </g>
              );
            })}

            {/* 예측 시점 마커 및 수치 라벨 (B1: 선 없이 점만 — 두 시점 사이를 직선으로 잇지 않음) */}
            {points.map((p) => {
              const cx = getX(toMs(p.targetTime));
              const cyTotal = getYTotal(p.totalTideCm);
              const cyAstro = getYTotal(p.astronomicalTideCm);
              const cyRes = getYResidual(p.residualCm);
              const timeLabel = `${p.leadHour}h 리드타임 (${p.targetTime.substring(11, 16)})`;

              return (
                <g key={p.leadHour}>
                  {/* 세로 타임라인 */}
                  <line x1={cx} y1={paddingTop} x2={cx} y2={paddingTop + chartH} stroke="#dee2e6" strokeWidth="1" strokeDasharray="3 3" />

                  {/* X축 시간 라벨 */}
                  <text x={cx} y={paddingTop + chartH + 18} textAnchor="middle" fill="#495057" fontSize="10" fontWeight="bold">
                    {timeLabel}
                  </text>

                  {/* 천문조 마커 */}
                  <circle cx={cx} cy={cyAstro} r="4" fill="#adb5bd" stroke="#fff" strokeWidth="2" />

                  {/* 총 수위 마커 & 레이블 */}
                  <circle cx={cx} cy={cyTotal} r="6" fill={p.isExceeded ? '#dc3545' : '#0d6efd'} stroke="#fff" strokeWidth="2.5" />
                  <rect x={cx - 28} y={cyTotal - 24} width="56" height="18" rx="4" fill={p.isExceeded ? '#dc3545' : '#0d6efd'} />
                  <text x={cx} y={cyTotal - 12} textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold" className="font-monospace">
                    {p.totalTideCm}cm
                  </text>

                  {/* 잔차 마커 & 레이블 (라벨을 마커 위로 — 아래 초과율 배지와 겹치지 않게) */}
                  <circle cx={cx} cy={cyRes} r="4" fill="#6f42c1" stroke="#fff" strokeWidth="2" />
                  <rect x={cx - 22} y={cyRes - 24} width="44" height="16" rx="3" fill="#f3e8ff" stroke="#d8b4fe" />
                  <text x={cx} y={cyRes - 12} textAnchor="middle" fill="#6f42c1" fontSize="9" fontWeight="bold" className="font-monospace">
                    +{p.residualCm}
                  </text>

                  {/* 초과 확률 배지 */}
                  <g transform={`translate(${cx - 32}, ${paddingTop + chartH - 22})`}>
                    <rect
                      width="64"
                      height="17"
                      rx="8"
                      fill={p.exceedProbability >= 0.5 ? '#f8d7da' : '#cfe2ff'}
                      stroke={p.exceedProbability >= 0.5 ? '#f5c2c7' : '#b6d4fe'}
                    />
                    <text
                      x="32"
                      y="12"
                      textAnchor="middle"
                      fill={p.exceedProbability >= 0.5 ? '#842029' : '#084298'}
                      fontSize="9"
                      fontWeight="bold"
                    >
                      초과율 {Math.round(p.exceedProbability * 100)}%
                    </text>
                  </g>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
}
