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
    return <div className="p-8 text-center text-slate-400">예측 데이터가 없습니다.</div>;
  }

  // 차트 스케일 계산
  const allTotalTides = points.map((p) => p.totalTideCm);
  const allResiduals = points.map((p) => p.residualCm);
  const maxTide = Math.max(...allTotalTides, warningThreshold + 10, 100);
  const minTide = Math.min(...points.map((p) => p.astronomicalTideCm - 10), 0);

  const maxResidual = Math.max(...allResiduals, 40);
  const minResidual = Math.min(...allResiduals, -10, 0);

  const width = 800;
  const height = 300;
  const paddingLeft = 60;
  const paddingRight = 60;
  const paddingTop = 30;
  const paddingBottom = 40;
  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  // Y 좌표 환산 함수 (총 수위: 좌측 Y축)
  const getYTotal = (val: number) => {
    return paddingTop + chartH - ((val - minTide) / (maxTide - minTide || 1)) * chartH;
  };

  // Y 좌표 환산 함수 (잔차: 우측 Y축)
  const getYResidual = (val: number) => {
    return paddingTop + chartH - ((val - minResidual) / (maxResidual - minResidual || 1)) * (chartH * 0.45);
  };

  // X 좌표 환산 함수
  const getX = (index: number) => {
    if (points.length === 1) return paddingLeft + chartW / 2;
    return paddingLeft + (index / (points.length - 1)) * chartW;
  };

  // 라인 패스 생성
  const totalPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYTotal(p.totalTideCm)}`)
    .join(' ');

  const astroPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYTotal(p.astronomicalTideCm)}`)
    .join(' ');

  const residualPath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYResidual(p.residualCm)}`)
    .join(' ');

  const advisoryY = getYTotal(advisoryThreshold);
  const warningY = getYTotal(warningThreshold);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span>📈</span> {stationName} 이중 출력 곡선 (총 수위 & 조위 편차)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            1차 표시: <span className="font-semibold text-blue-600">총 수위(예상 조위)</span> · 근거 표시: <span className="font-semibold text-purple-600">조위 편차(잔차)</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 bg-blue-600 rounded"></span>
            <span className="text-slate-700 font-medium">총 수위(cm)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 bg-slate-300 rounded stroke-dasharray"></span>
            <span className="text-slate-500 font-medium">천문조(cm)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 bg-purple-600 rounded"></span>
            <span className="text-purple-700 font-medium">잔차(cm)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-amber-500"></span>
            <span className="text-amber-700">주의보선</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-rose-600"></span>
            <span className="text-rose-700">경보선</span>
          </div>
        </div>
      </div>

      <div className="relative w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-w-[650px] select-none">
          {/* 배경 그리드선 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = paddingTop + chartH * ratio;
            const val = Math.round(maxTide - ratio * (maxTide - minTide));
            return (
              <g key={ratio}>
                <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="#f1f5f9" strokeWidth="1" />
                <text x={paddingLeft - 8} y={y + 4} textAnchor="end" className="text-[11px] fill-slate-400 font-mono">
                  {val}
                </text>
              </g>
            );
          })}

          {/* 주의보 기준선 (황색 점선) */}
          {advisoryY >= paddingTop && advisoryY <= paddingTop + chartH && (
            <g>
              <line
                x1={paddingLeft}
                y1={advisoryY}
                x2={width - paddingRight}
                y2={advisoryY}
                stroke="#f59e0b"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
              <text x={width - paddingRight + 5} y={advisoryY + 3} className="text-[10px] fill-amber-600 font-bold">
                주의보 {advisoryThreshold}cm
              </text>
            </g>
          )}

          {/* 경보 기준선 (적색 실선) */}
          {warningY >= paddingTop && warningY <= paddingTop + chartH && (
            <g>
              <line
                x1={paddingLeft}
                y1={warningY}
                x2={width - paddingRight}
                y2={warningY}
                stroke="#e11d48"
                strokeWidth="1.8"
                strokeDasharray="2 2"
              />
              <text x={width - paddingRight + 5} y={warningY + 3} className="text-[10px] fill-rose-600 font-bold">
                경보 {warningThreshold}cm
              </text>
            </g>
          )}

          {/* 천문조 곡선 (회색 점선) */}
          <path d={astroPath} fill="none" stroke="#94a3b8" strokeWidth="2" strokeDasharray="5 3" />

          {/* 총 수위 곡선 (1차 표시, 굵은 파란색) */}
          <path d={totalPath} fill="none" stroke="#2563eb" strokeWidth="3.5" strokeLinecap="round" />

          {/* 잔차 곡선 (보조 표시, 보라색) */}
          <path d={residualPath} fill="none" stroke="#9333ea" strokeWidth="2.5" strokeLinecap="round" />

          {/* 포인트 마커 및 툴팁 레이블 */}
          {points.map((p, i) => {
            const cx = getX(i);
            const cyTotal = getYTotal(p.totalTideCm);
            const cyRes = getYResidual(p.residualCm);
            const timeLabel = `${p.leadHour}h (${p.targetTime.substring(11, 16)})`;

            return (
              <g key={p.leadHour}>
                {/* 수직 타임 가이드라인 */}
                <line x1={cx} y1={paddingTop} x2={cx} y2={paddingTop + chartH} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="3 3" />

                {/* X축 시간 라벨 */}
                <text x={cx} y={paddingTop + chartH + 20} textAnchor="middle" className="text-[11px] fill-slate-600 font-semibold">
                  {timeLabel}
                </text>

                {/* 총 수위 포인트 */}
                <circle
                  cx={cx}
                  cy={cyTotal}
                  r="6"
                  className={p.isExceeded ? 'fill-rose-500 stroke-white' : 'fill-blue-600 stroke-white'}
                  strokeWidth="2.5"
                />
                <text
                  x={cx}
                  y={cyTotal - 10}
                  textAnchor="middle"
                  className={`text-[12px] font-bold ${p.isExceeded ? 'fill-rose-600' : 'fill-blue-700'}`}
                >
                  {p.totalTideCm}cm
                </text>

                {/* 잔차 포인트 */}
                <circle cx={cx} cy={cyRes} r="4.5" fill="#9333ea" stroke="#fff" strokeWidth="2" />
                <text x={cx} y={cyRes + 16} textAnchor="middle" className="text-[11px] font-medium fill-purple-700">
                  +{p.residualCm}cm
                </text>

                {/* 초과 확률 뱃지 */}
                <g transform={`translate(${cx - 30}, ${paddingTop + chartH - 24})`}>
                  <rect
                    width="60"
                    height="18"
                    rx="9"
                    fill={p.exceedProbability >= 0.5 ? '#ffe4e6' : '#eff6ff'}
                    stroke={p.exceedProbability >= 0.5 ? '#f43f5e' : '#93c5fd'}
                  />
                  <text
                    x="30"
                    y="13"
                    textAnchor="middle"
                    className={`text-[10px] font-bold ${p.exceedProbability >= 0.5 ? 'fill-rose-700' : 'fill-blue-700'}`}
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
  );
}
