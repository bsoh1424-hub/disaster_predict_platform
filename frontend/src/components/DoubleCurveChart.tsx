'use client';

import React from 'react';
import { ForecastPoint } from '../types/api';

interface DoubleCurveChartProps {
  points: ForecastPoint[];
  advisoryThreshold: number;
  warningThreshold: number;
  stationName: string;
}

export default function DoubleCurveChart({
  points,
  advisoryThreshold,
  warningThreshold,
  stationName,
}: DoubleCurveChartProps) {
  if (!points || points.length === 0) {
    return (
      <div className="card shadow-sm p-4 text-center text-muted">
        예측 데이터가 수신되지 않았습니다.
      </div>
    );
  }

  // 스케일 계산
  const allTotalTides = points.map((p) => p.totalTideCm);
  const allResiduals = points.map((p) => p.residualCm);
  const maxTide = Math.max(...allTotalTides, warningThreshold + 20, 100);
  const minTide = Math.min(...points.map((p) => p.astronomicalTideCm - 20), 0);

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

  const getX = (index: number) => {
    if (points.length === 1) return paddingLeft + chartW / 2;
    return paddingLeft + (index / (points.length - 1)) * chartW;
  };

  // SVG 패스
  const totalPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYTotal(p.totalTideCm)}`)
    .join(' ');

  const totalAreaPath = `${totalPath} L ${getX(points.length - 1)} ${paddingTop + chartH} L ${getX(0)} ${paddingTop + chartH} Z`;

  const astroPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYTotal(p.astronomicalTideCm)}`)
    .join(' ');

  const residualPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYResidual(p.residualCm)}`)
    .join(' ');

  const residualAreaPath = `${residualPath} L ${getX(points.length - 1)} ${paddingTop + chartH} L ${getX(0)} ${paddingTop + chartH} Z`;

  const advisoryY = getYTotal(advisoryThreshold);
  const warningY = getYTotal(warningThreshold);

  return (
    <div className="card shadow-sm mb-3">
      {/* 카드 헤더 (Bootstrap Card Header) */}
      <div className="card-header d-flex flex-wrap align-items-center justify-content-between py-2 px-3 bg-white">
        <div className="d-flex align-items-center gap-2">
          <i className="bi bi-graph-up text-primary fs-6"></i>
          <span className="fw-bold text-dark fs-6">{stationName} 연안 이중 출력 예측 곡선</span>
          <span className="badge bg-light text-secondary border">PRD Q7 &middot; F1</span>
        </div>

        {/* 범례 (Bootstrap Badges) */}
        <div className="d-flex flex-wrap align-items-center gap-2" style={{ fontSize: '0.78rem' }}>
          <span className="badge bg-primary-subtle text-primary border border-primary-subtle d-flex align-items-center gap-1">
            <span style={{ width: 12, height: 3, backgroundColor: '#0d6efd', display: 'inline-block' }}></span>
            총 수위(cm)
          </span>
          <span className="badge bg-secondary-subtle text-secondary border border-secondary-subtle d-flex align-items-center gap-1">
            <span style={{ width: 12, height: 3, backgroundColor: '#6c757d', borderTop: '1px dashed #000', display: 'inline-block' }}></span>
            천문조(cm)
          </span>
          <span className="badge bg-purple-subtle text-purple border d-flex align-items-center gap-1" style={{ backgroundColor: '#f3e8ff', color: '#6f42c1' }}>
            <span style={{ width: 12, height: 3, backgroundColor: '#6f42c1', display: 'inline-block' }}></span>
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
            <defs>
              <linearGradient id="bsTotalTideGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0d6efd" stopOpacity="0.22" />
                <stop offset="100%" stopColor="#0d6efd" stopOpacity="0.0" />
              </linearGradient>

              <linearGradient id="bsResidualGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6f42c1" stopOpacity="0.18" />
                <stop offset="100%" stopColor="#6f42c1" stopOpacity="0.0" />
              </linearGradient>
            </defs>

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
                <rect x={width - paddingRight + 5} y={advisoryY - 8} width="75" height="16" rx="3" fill="#fff3cd" stroke="#ffe69c" />
                <text x={width - paddingRight + 42} y={advisoryY + 4} textAnchor="middle" fill="#664d03" fontSize="9" fontWeight="bold">
                  주의보 {advisoryThreshold}
                </text>
              </g>
            )}

            {/* 경보 기준선 (Danger line) */}
            {warningY >= paddingTop && warningY <= paddingTop + chartH && (
              <g>
                <line x1={paddingLeft} y1={warningY} x2={width - paddingRight} y2={warningY} stroke="#dc3545" strokeWidth="2" strokeDasharray="3 2" />
                <rect x={width - paddingRight + 5} y={warningY - 8} width="75" height="16" rx="3" fill="#f8d7da" stroke="#f5c2c7" />
                <text x={width - paddingRight + 42} y={warningY + 4} textAnchor="middle" fill="#842029" fontSize="9" fontWeight="bold">
                  경보 {warningThreshold}
                </text>
              </g>
            )}

            {/* 면적 채우기 */}
            <path d={totalAreaPath} fill="url(#bsTotalTideGrad)" />
            <path d={residualAreaPath} fill="url(#bsResidualGrad)" />

            {/* 천문조 곡선 */}
            <path d={astroPath} fill="none" stroke="#adb5bd" strokeWidth="2" strokeDasharray="4 3" />

            {/* 잔차 곡선 (보라색) */}
            <path d={residualPath} fill="none" stroke="#6f42c1" strokeWidth="2.5" strokeLinecap="round" />

            {/* 총 수위 곡선 (파란색) */}
            <path d={totalPath} fill="none" stroke="#0d6efd" strokeWidth="3.5" strokeLinecap="round" />

            {/* 포인트 마커 및 수치 라벨 */}
            {points.map((p, i) => {
              const cx = getX(i);
              const cyTotal = getYTotal(p.totalTideCm);
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

                  {/* 총 수위 마커 & 레이블 */}
                  <circle cx={cx} cy={cyTotal} r="6" fill={p.isExceeded ? '#dc3545' : '#0d6efd'} stroke="#fff" strokeWidth="2.5" />
                  <rect x={cx - 28} y={cyTotal - 24} width="56" height="18" rx="4" fill={p.isExceeded ? '#dc3545' : '#0d6efd'} />
                  <text x={cx} y={cyTotal - 12} textAnchor="middle" fill="#fff" fontSize="10" fontWeight="bold" className="font-monospace">
                    {p.totalTideCm}cm
                  </text>

                  {/* 잔차 마커 & 레이블 */}
                  <circle cx={cx} cy={cyRes} r="4" fill="#6f42c1" stroke="#fff" strokeWidth="2" />
                  <rect x={cx - 22} y={cyRes + 8} width="44" height="16" rx="3" fill="#f3e8ff" stroke="#d8b4fe" />
                  <text x={cx} y={cyRes + 20} textAnchor="middle" fill="#6f42c1" fontSize="9" fontWeight="bold" className="font-monospace">
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
