'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '../../lib/api';
import { ForecastResponse, ObservationResponse, StationSummary } from '../../types/api';
import DoubleCurveChart from '../../components/DoubleCurveChart';

function ForecastContent() {
  const searchParams = useSearchParams();
  const initialStation = searchParams.get('station') || 'BUSAN';

  const [stations, setStations] = useState<StationSummary[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>(initialStation);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [observations, setObservations] = useState<ObservationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // URL 파라미터 변경 시 반영
  useEffect(() => {
    const st = searchParams.get('station');
    if (st) setSelectedStation(st);
  }, [searchParams]);

  // 관측소 목록 로드
  useEffect(() => {
    async function loadStations() {
      try {
        const data = await api.getStations();
        setStations(data);
      } catch (e) {
        console.error(e);
      }
    }
    loadStations();
  }, []);

  // 선택된 관측소 예측 로드
  useEffect(() => {
    async function loadForecast() {
      if (!selectedStation) return;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getForecast(selectedStation);
        setForecast(data);
        // 과거 24h 관측값 (차트에 이전 데이터 표시용 — 실패해도 예측은 보여줌)
        try {
          const obs = await api.getObservations(selectedStation);
          setObservations(obs);
        } catch (e) {
          console.error(e);
          setObservations(null);
        }
      } catch (err: unknown) {
        console.error(err);
        setError(`예측 데이터를 불러오지 못했습니다: ${selectedStation}`);
      } finally {
        setLoading(false);
      }
    }
    loadForecast();
  }, [selectedStation]);

  // 실시간 재계산 요청 (A1)
  const handleRecalculate = async () => {
    if (!selectedStation || recalculating) return;
    setRecalculating(true);
    try {
      const data = await api.recalculate(selectedStation);
      setForecast(data);
    } catch (err: unknown) {
      alert('실시간 재계산 중 오류가 발생했습니다: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setRecalculating(false);
    }
  };

  // 전체 관측소 재계산
  const handleRecalculateAll = async () => {
    if (recalculating) return;
    setRecalculating(true);
    try {
      await api.runBatch();
      const updatedStations = await api.getStations();
      setStations(updatedStations);
      const data = await api.getForecast(selectedStation);
      setForecast(data);
    } catch (err: unknown) {
      alert('전체 재계산 중 오류가 발생했습니다: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setRecalculating(false);
    }
  };

  return (
    <div>
      {/* 상단 타이틀 & 관측소 선택기 */}
      <div className="card shadow-sm mb-4">
        <div className="card-body p-3 d-flex flex-wrap align-items-center justify-content-between gap-3">
          <div className="d-flex align-items-center gap-3">
            <div className="bg-primary text-white rounded p-2 text-center d-flex align-items-center justify-content-center" style={{ width: 44, height: 44 }}>
              <i className="bi bi-graph-up-arrow fs-5"></i>
            </div>
            <div>
              <div className="d-flex align-items-center gap-2">
                <h4 className="mb-0 fw-bold fs-5 text-dark">
                  {forecast ? forecast.stationName : selectedStation} 폭풍해일 딥러닝 예측 모델
                </h4>
                <span className="badge bg-primary font-monospace" style={{ fontSize: '0.7rem' }}>
                  {forecast?.runType || 'BATCH'} (A1)
                </span>
              </div>
              <small className="text-muted font-monospace">
                모델: {forecast?.modelVersion || 'surge_v1.0.0'} &middot; 기준: {forecast?.baseTime.substring(11, 16) || '정시'} KST
              </small>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            {/* 관측소 선택 셀렉트박스 */}
            <select
              className="form-select form-select-sm fw-bold border-primary shadow-sm"
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              style={{ minWidth: '150px' }}
            >
              {stations.map((s) => (
                <option key={s.stationCode} value={s.stationCode}>
                  {s.name} ({s.stationCode} - {s.seaRegion})
                </option>
              ))}
            </select>

            {/* 실시간 재계산 버튼 (A1) */}
            <button
              onClick={handleRecalculate}
              disabled={recalculating}
              className="btn btn-primary btn-sm d-flex align-items-center gap-1.5 px-3 py-1.5 shadow-sm"
            >
              <i className="bi bi-arrow-repeat"></i>
              <span>{recalculating ? '재계산 중...' : '실시간 재계산 (A1)'}</span>
            </button>
            <button 
              onClick={handleRecalculateAll} 
              disabled={recalculating}
            >
              전체 재계산
            </button>
          </div>
        </div>
      </div>

      {loading && !forecast ? (
        <div className="card shadow-sm p-5 text-center text-muted">
          <div className="spinner-border text-primary mx-auto mb-3" role="status"></div>
          <div>물리-기상 결합 딥러닝 잔차 계산 및 총 수위 환산 중...</div>
        </div>
      ) : error ? (
        <div className="alert alert-danger p-4 text-center">
          <div>{error}</div>
        </div>
      ) : forecast ? (
        <div className="row g-3">
          {/* 3대 핵심 KPI 카드 (1줄 3칸) */}
          <div className="col-md-4">
            <div className="card shadow-sm h-100">
              <div className="card-body p-3">
                <span className="text-muted fw-semibold d-block mb-1" style={{ fontSize: '0.78rem' }}>
                  최고 예상 총 수위 (1차 판정 기준 - Q7)
                </span>
                <div className="d-flex align-items-baseline gap-1">
                  <span className="fs-3 fw-bold text-primary font-monospace">{forecast.tideSummary.maxTotalTideCm}</span>
                  <span className="text-muted fw-bold" style={{ fontSize: '0.85rem' }}>cm</span>
                </div>
                <small className="text-muted mt-1 d-block" style={{ fontSize: '0.72rem' }}>
                  주의보: {forecast.advisoryThresholdCm}cm / 경보: {forecast.warningThresholdCm}cm
                </small>
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className={`card shadow-sm h-100 ${
              forecast.points.some((p) => p.alertLevel === 'WARNING')
                ? 'border-danger bg-danger-subtle'
                : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                ? 'border-warning bg-warning-subtle'
                : 'border-success-subtle bg-success-subtle'
            }`}>
              <div className="card-body p-3">
                <span className="text-muted fw-semibold d-block mb-1" style={{ fontSize: '0.78rem' }}>
                  침수 임계 초과 판정 (PRD F2)
                </span>
                <div className={`fs-5 fw-bold ${
                  forecast.points.some((p) => p.alertLevel === 'WARNING')
                    ? 'text-danger'
                    : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                    ? 'text-warning-emphasis'
                    : 'text-success'
                }`}>
                  {forecast.points.some((p) => p.alertLevel === 'WARNING')
                    ? '🚨 폭풍해일 경보 초과'
                    : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                    ? '⚠️ 폭풍해일 주의보 초과'
                    : '✅ 안전 수위 유지 중'}
                </div>
                <small className="text-muted mt-1 d-block" style={{ fontSize: '0.72rem' }}>
                  {forecast.points.some((p) => p.isExceeded) ? '방파제 통제 및 저지대 배수문 가동 준비 요망' : '기준치 이하로 정상입니다'}
                </small>
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className="card shadow-sm h-100">
              <div className="card-body p-3">
                <span className="text-muted fw-semibold d-block mb-1" style={{ fontSize: '0.78rem' }}>
                  만조 겹침 판정 (PRD F3)
                </span>
                <div>
                  <span className={`badge ${
                    forecast.tideSummary.highTideOverlap
                      ? 'bg-danger'
                      : 'bg-secondary'
                  } px-2.5 py-1.5 fs-6`}>
                    {forecast.tideSummary.highTideOverlap ? '만조 겹침 집중 위험' : '만조 분리 안전'}
                  </span>
                </div>
                <small className="text-muted mt-1 d-block" style={{ fontSize: '0.72rem' }}>
                  위험 구간: {forecast.tideSummary.overlapWindow}
                </small>
              </div>
            </div>
          </div>

          {/* 메인 이중 출력 곡선 차트 (F1) */}
          <div className="col-12">
            <DoubleCurveChart
              points={forecast.points}
              advisoryThreshold={forecast.advisoryThresholdCm}
              warningThreshold={forecast.warningThresholdCm}
              stationName={forecast.stationName}
              history={observations?.observations ?? []}
              baseTime={forecast.baseTime}
            />
          </div>

          {/* 하단 2분할: XAI 근거 패널 (F4) & 지자체/어항 표준 방재 지침 */}
          <div className="col-lg-6">
            <div className="card shadow-sm h-100">
              <div className="card-header py-2 px-3 bg-white d-flex align-items-center justify-content-between">
                <span className="fw-bold">
                  <i className="bi bi-file-earmark-text text-primary me-1"></i> 침수 위험 요인 분석 근거 (PRD F4 &middot; XAI)
                </span>
                <span className="badge bg-light text-secondary border font-monospace">
                  Explainable AI
                </span>
              </div>
              <div className="card-body p-3">
                <div className="p-2.5 rounded bg-light border mb-3 small">
                  <strong>모델 근거 설명:</strong> {forecast.reasonSummary}
                </div>

                <div className="vstack gap-2">
                  <div className="p-2 border rounded">
                    <div className="d-flex justify-content-between mb-1 small">
                      <span className="text-muted">기압 역효과 (Inverse Barometer)</span>
                      <span className="fw-bold text-primary">1hPa 하강당 약 +1.0cm 상승</span>
                    </div>
                    <div className="progress" style={{ height: '6px' }}>
                      <div className="progress-bar bg-primary" style={{ width: '70%' }}></div>
                    </div>
                  </div>

                  <div className="p-2 border rounded">
                    <div className="d-flex justify-content-between mb-1 small">
                      <span className="text-muted">바람 밀어올림 (Wind Setup)</span>
                      <span className="fw-bold text-purple" style={{ color: '#6f42c1' }}>풍속² 비례 &middot; 연안 집중</span>
                    </div>
                    <div className="progress" style={{ height: '6px' }}>
                      <div className="progress-bar" style={{ width: '60%', backgroundColor: '#6f42c1' }}></div>
                    </div>
                  </div>

                  <div className="p-2 border rounded">
                    <div className="d-flex justify-content-between mb-1 small">
                      <span className="text-muted">조석 상호작용 (Tide Interaction)</span>
                      <span className="fw-bold text-warning-emphasis">만조 극값과 잔차 피크 중첩 분석</span>
                    </div>
                    <div className="progress" style={{ height: '6px' }}>
                      <div className="progress-bar bg-warning" style={{ width: '85%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-6">
            <div className="card shadow-sm h-100">
              <div className="card-header py-2 px-3 bg-white d-flex align-items-center justify-content-between">
                <span className="fw-bold">
                  <i className="bi bi-shield-check text-success me-1"></i> 지자체 및 어항 단계별 방재 행동 지침
                </span>
                <span className="badge bg-light text-secondary border font-monospace">
                  임계고: {forecast.localFloodThresholdCm}cm
                </span>
              </div>
              <div className="card-body p-3 vstack gap-2 small">
                <div className="p-2.5 rounded bg-light border">
                  <strong className="text-success d-block mb-1">1단계: 평시 및 잔차 단독 상승 시</strong>
                  <div>만조와 겹치지 않으면 총 수위가 임계치를 넘지 않으므로 과잉 대응을 지양하고 상시 모니터링합니다.</div>
                </div>
                <div className="p-2.5 rounded bg-warning-subtle text-warning-emphasis border border-warning-subtle">
                  <strong className="d-block mb-1">2단계: 폭풍해일 주의보 ({forecast.advisoryThresholdCm}cm) 도달 시</strong>
                  <div>저지대 배수문&middot;빗물펌프장 사전 가동, 해안도로&middot;지하주차장 사전 통제 준비, 선박 피항 조치.</div>
                </div>
                <div className="p-2.5 rounded bg-danger-subtle text-danger border border-danger-subtle">
                  <strong className="d-block mb-1">3단계: 폭풍해일 경보 ({forecast.warningThresholdCm}cm) 초과 시</strong>
                  <div>해안 주민 대피 권고, 방파제&middot;갯바위 전면 출입 통제, 상가 차수판 설치 완료 및 비상상황실 격상.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function ForecastPage() {
  return (
    <Suspense fallback={<div className="p-5 text-center text-muted">화면을 불러오는 중...</div>}>
      <ForecastContent />
    </Suspense>
  );
}
