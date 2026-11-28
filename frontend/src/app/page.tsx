'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { api } from '../lib/api';
import { StationSummary } from '../types/api';

const KoreaCoastMap = dynamic(() => import('../components/KoreaCoastMap'), {
  ssr: false,
  loading: () => (
    <div className="card shadow-sm p-5 text-center text-muted d-flex align-items-center justify-content-center" style={{ height: '620px' }}>
      <div>
        <div className="spinner-border text-primary mb-3" role="status"></div>
        <div className="fw-semibold">대한민국 연안 관측망 지도를 불러오는 중...</div>
      </div>
    </div>
  )
});

export default function HomePage() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState<string>('전체');
  const [viewMode, setViewMode] = useState<'map' | 'grid'>('map');
  const [selectedStation, setSelectedStation] = useState<StationSummary | null>(null);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const handleRecalculateAll = async () => {
    if (recalculating) return;
    setRecalculating(true);
    try {
      await api.runBatch();
      const data = await api.getStations();
      setStations(data);
      if (data.length > 0) {
        const sorted = [...data].sort((a, b) => {
          const score = (lvl: string) => lvl === 'WARNING' ? 3 : lvl === 'ADVISORY' ? 2 : 1;
          return score(b.alertLevel) - score(a.alertLevel);
        });
        setSelectedStation(sorted[0]);
      }
    } catch (e) {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        sessionStorage.removeItem('token');
        window.location.href = '/login';
        return;
      }
      console.error(e);
      alert('전체 재계산 중 오류가 발생했습니다.');
    } finally {
      setRecalculating(false);
    }
  };

  const handleRefreshData = async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      await api.refreshData();
      alert('최신 데이터 가져오기를 시작했습니다. 1~2분 뒤 새로고침하면 반영됩니다.');
    } catch (e) {
      if (e instanceof Error && e.message === 'UNAUTHORIZED') {
        sessionStorage.removeItem('token');
        window.location.href = '/login';
        return;
      }
      console.error(e);
      alert('최신 데이터 가져오기 중 오류가 발생했습니다.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getStations();
        setStations(data);
        if (data.length > 0) {
          // 위험도(경보 > 주의보 > 정상)가 가장 높은 관측소를 기본 선택
          const sorted = [...data].sort((a, b) => {
            const score = (lvl: string) => lvl === 'WARNING' ? 3 : lvl === 'ADVISORY' ? 2 : 1;
            return score(b.alertLevel) - score(a.alertLevel);
          });
          setSelectedStation(sorted[0]);
        }
      } catch (e) {
        console.error(e);
        setError('Spring Boot 백엔드 서버에서 관측소 데이터를 불러오지 못했습니다.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const regions = ['전체', '서해', '남해', '동해', '제주'];
  const filtered = regionFilter === '전체'
    ? stations
    : stations.filter((s) => s.seaRegion.includes(regionFilter));

  const warningCount = stations.filter((s) => s.alertLevel === 'WARNING').length;
  const advisoryCount = stations.filter((s) => s.alertLevel === 'ADVISORY').length;

  // 선택된 관측소 표시용 값: 관측값이 메인, 12h 예측이 보조 (PR #32)
  const selObs = selectedStation?.latestObsTideCm ?? null;
  const selTotal = selectedStation?.latestTotalTideCm ?? null;
  // 진행 바는 관측 수위 기준 (alertLevel도 관측 수위 기준)
  const selPct =
    selectedStation != null && selObs != null
      ? Math.min(100, Math.round((selObs / selectedStation.warningThresholdCm) * 100))
      : 0;

  let selBarColor = 'bg-success';
  if (selectedStation?.alertLevel === 'WARNING') selBarColor = 'bg-danger';
  else if (selectedStation?.alertLevel === 'ADVISORY') selBarColor = 'bg-warning';

  let selBadgeBg = '#d1e7dd';
  let selBadgeClass = 'bg-success';
  let selBadgeText = '✅ 정상 수위';
  if (selectedStation?.alertLevel === 'WARNING') {
    selBadgeBg = '#f8d7da';
    selBadgeClass = 'bg-danger';
    selBadgeText = '🚨 경보 초과';
  } else if (selectedStation?.alertLevel === 'ADVISORY') {
    selBadgeBg = '#fff3cd';
    selBadgeClass = 'bg-warning text-dark';
    selBadgeText = '⚠️ 주의보 초과';
  }

  return (
    <div className="py-2">
      {/* 상단 헤더 & 알림 안내 */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4 pb-3 border-bottom">
        <div>
          <h2 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
            <i className="bi bi-geo-alt-fill text-danger"></i> 전국 연안 조위관측소 실시간 종합 상황판
          </h2>
          <p className="text-muted small mb-0">
            대한민국 10개 주요 조위관측소의 실시간 조위 및 12h/24h 폭풍해일 특보 임계 상태를 통합 모니터링합니다.
          </p>
        </div>

        {/* 종합 위험 요약 뱃지 */}
        <div className="d-flex gap-2">
          <div className="p-2 px-3 rounded bg-white border text-center shadow-sm">
            <small className="text-muted d-block" style={{ fontSize: '0.7rem' }}>모니터링 관측소</small>
            <span className="fw-bold font-monospace fs-6">{stations.length}개소</span>
          </div>
          <div className={`p-2 px-3 rounded border text-center shadow-sm ${warningCount > 0 ? 'bg-danger text-white' : 'bg-white'}`}>
            <small className={warningCount > 0 ? 'text-white-50' : 'text-muted'} style={{ fontSize: '0.7rem' }}>경보 초과</small>
            <span className="fw-bold font-monospace fs-6">{warningCount}개소</span>
          </div>
          <div className={`p-2 px-3 rounded border text-center shadow-sm ${advisoryCount > 0 ? 'bg-warning-subtle text-warning-emphasis' : 'bg-white'}`}>
            <small className="text-muted d-block" style={{ fontSize: '0.7rem' }}>주의보 초과</small>
            <span className="fw-bold font-monospace fs-6">{advisoryCount}개소</span>
          </div>
        </div>
      </div>

      {/* 안내 알림 (PRD F5) */}
      <div className="alert alert-warning py-2 px-3 mb-4 d-flex flex-wrap align-items-center justify-content-between gap-2 shadow-sm border-0">
        <div className="d-flex align-items-center gap-2 small">
          <i className="bi bi-exclamation-triangle-fill text-warning fs-5"></i>
          <span>
            <strong>공식 특보 우선 원칙 (F5):</strong> 본 대시보드는 KHOA 조위와 KMA 수치예보를 연계한 침수 참고 경보입니다. 기상청 공식 특보 발표 시 공식 정보가 최우선입니다.
          </span>
        </div>
        <Link href="/forecast" className="btn btn-primary btn-sm px-3 fw-semibold">
          <i className="bi bi-graph-up-arrow me-1"></i> 예측 모델 분석으로 이동 &rarr;
        </Link>
      </div>

      {/* 해역 필터 탭 & 뷰 모드 전환 */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <div className="d-flex flex-wrap align-items-center gap-2">
          <div className="btn-group shadow-sm" role="group">
            {regions.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRegionFilter(r)}
                className={`btn btn-sm ${regionFilter === r ? 'btn-primary' : 'btn-outline-secondary bg-white'}`}
              >
                {r === '전체' ? '전체 해역 (10)' : `${r}해`}
              </button>
            ))}
          </div>
          <span className="text-muted small">
            {filtered.length}개 관측소 표시 중
          </span>
        </div>

        <div className="d-flex align-items-center gap-2">
          <button
            type="button"
            onClick={handleRefreshData}
            disabled={refreshing}
            className="btn btn-sm btn-outline-primary"
          >
            {refreshing ? '가져오는 중...' : '최신 데이터'}
          </button>
          <button
            type="button"
            onClick={handleRecalculateAll}
            disabled={recalculating}
            className="btn btn-sm btn-primary"
          >
            전체 재계산
          </button>

          {/* 뷰 모드 전환 버튼 (지도 뷰 vs 카드 그리드 뷰) */}
          <div className="btn-group shadow-sm" role="group">
            <button
              type="button"
              onClick={() => setViewMode('map')}
              className={`btn btn-sm d-flex align-items-center gap-1 ${viewMode === 'map' ? 'btn-dark' : 'btn-outline-secondary bg-white'}`}
            >
              <i className="bi bi-map"></i>
              <span>대한민국 지도 뷰</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`btn btn-sm d-flex align-items-center gap-1 ${viewMode === 'grid' ? 'btn-dark' : 'btn-outline-secondary bg-white'}`}
            >
              <i className="bi bi-grid-3x3-gap"></i>
              <span>격자 카드 뷰</span>
            </button>
          </div>
        </div>
      </div>

      {/* 로딩 및 에러 처리 */}
      {loading ? (
        <div className="card shadow-sm p-5 text-center text-muted">
          <div className="spinner-border text-primary mx-auto mb-3" role="status"></div>
          <div>전국 관측망 실시간 수위 데이터를 수집 중입니다...</div>
        </div>
      ) : error ? (
        <div className="alert alert-danger p-4 text-center">
          <div>{error}</div>
        </div>
      ) : viewMode === 'map' ? (
        /* ================= 1. 대한민국 해안 지도 뷰 ================= */
        <div className="row g-3">
          {/* 좌측: 대한민국 연안 지도 (Leaflet 인터랙티브 맵) */}
          <div className="col-lg-8">
            <KoreaCoastMap
              stations={filtered}
              selectedStation={selectedStation}
              onSelectStation={(st) => setSelectedStation(st)}
            />
          </div>

          {/* 우측: 선택된 관측소 상세 정보 및 위험 순위 리스트 */}
          <div className="col-lg-4 d-flex flex-column gap-3">
            {/* 선택된 관측소 상세 카드 */}
            {selectedStation ? (
              <div className="card shadow-sm border-top border-4 border-primary">
                <div className="card-header bg-white py-2 px-3 d-flex align-items-center justify-content-between">
                  <div>
                    <h5 className="fw-bold mb-0 text-dark d-flex align-items-center gap-2">
                      <span>{selectedStation.name} 관측소</span>
                      <span className="badge bg-secondary-subtle text-secondary small font-monospace" style={{ fontSize: '0.7rem' }}>
                        {selectedStation.stationCode}
                      </span>
                    </h5>
                  </div>
                  <span className="badge bg-light text-dark border">
                    {selectedStation.seaRegion}해안
                  </span>
                </div>

                <div className="card-body p-3">
                  <div className="d-flex justify-content-between align-items-baseline mb-2">
                    <span className="text-muted small">현재 관측 수위</span>
                    <div className="text-end">
                      <span className="fs-2 fw-bold font-monospace text-primary">
                        {selObs != null ? Math.round(selObs) : '–'}
                      </span>
                      <span className="text-muted small ms-1">cm</span>
                    </div>
                  </div>

                  <div className="d-flex justify-content-between align-items-baseline mb-2">
                    <span className="text-muted small">12시간 뒤 예상 총수위</span>
                    <div className="text-end">
                      <span className="fs-5 fw-bold font-monospace text-secondary">
                        {selTotal != null ? Math.round(selTotal) : '예측 없음'}
                      </span>
                      {selTotal != null && <span className="text-muted small ms-1">cm</span>}
                    </div>
                  </div>

                  {/* 특보 상태 뱃지 */}
                  <div
                    className="d-flex align-items-center justify-content-between p-2 rounded mb-3"
                    style={{ backgroundColor: selBadgeBg }}
                  >
                    <span className="small fw-semibold text-muted">특보 상태:</span>
                    <span className={`badge ${selBadgeClass}`}>
                      {selBadgeText}
                    </span>
                  </div>

                  {/* 임계치 진행 바 */}
                  <div className="mb-3">
                    <div className="d-flex justify-content-between small text-muted mb-1" style={{ fontSize: '0.75rem' }}>
                      <span>기준 임계치 비교</span>
                      <span>
                        주의보: <strong>{selectedStation.advisoryThresholdCm}cm</strong> / 경보: <strong>{selectedStation.warningThresholdCm}cm</strong>
                      </span>
                    </div>
                    <div className="progress" style={{ height: '8px' }}>
                      <div
                        className={`progress-bar ${selBarColor}`}
                        role="progressbar"
                        style={{ width: `${selPct}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* 상세 분석 페이지 이동 링크 버튼 */}
                  <Link
                    href={`/forecast?station=${selectedStation.stationCode}`}
                    className="btn btn-primary w-100 fw-semibold d-flex align-items-center justify-content-center gap-2"
                  >
                    <span>{selectedStation.name} 예측 모델 &middot; XAI 분석 차트</span>
                    <i className="bi bi-arrow-right"></i>
                  </Link>
                </div>
              </div>
            ) : null}

            {/* 전국 10개 관측소 수위 현황 리스트 (클릭 시 지도 이동) */}
            <div className="card shadow-sm flex-grow-1" style={{ maxHeight: '315px', overflowY: 'auto' }}>
              <div className="card-header bg-white py-2 px-3 fw-bold small text-dark d-flex justify-content-between align-items-center">
                <span><i className="bi bi-list-ol text-primary me-1"></i> 관측소별 위험 현황</span>
                <small className="text-muted">클릭 시 해당 위치로 이동</small>
              </div>
              <div className="list-group list-group-flush small">
                {filtered.map((st) => {
                  const isCurrent = selectedStation?.stationCode === st.stationCode;
                  const isWarn = st.alertLevel === 'WARNING';
                  const isAdv = st.alertLevel === 'ADVISORY';

                  return (
                    <button
                      key={st.stationCode}
                      type="button"
                      onClick={() => setSelectedStation(st)}
                      className={`list-group-item list-group-item-action d-flex align-items-center justify-content-between py-2 px-3 ${
                        isCurrent ? 'bg-primary-subtle text-primary-emphasis fw-bold' : ''
                      }`}
                    >
                      <div className="d-flex align-items-center gap-2">
                        <span
                          style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: isWarn ? '#dc3545' : isAdv ? '#fd7e14' : '#198754'
                          }}
                        ></span>
                        <span>{st.name}</span>
                        <span className="text-muted" style={{ fontSize: '0.7rem' }}>({st.seaRegion})</span>
                      </div>
                      <div className="d-flex align-items-center gap-2 font-monospace">
                        <span className={isWarn ? 'text-danger fw-bold' : isAdv ? 'text-warning-emphasis fw-bold' : 'text-dark'}>
                          {st.latestObsTideCm != null ? `${Math.round(st.latestObsTideCm)} cm` : '–'}
                        </span>
                        <span
                          className={`badge ${
                            isWarn ? 'bg-danger' : isAdv ? 'bg-warning text-dark' : 'bg-light text-secondary border'
                          }`}
                          style={{ fontSize: '0.65rem' }}
                        >
                          {isWarn ? '경보' : isAdv ? '주의보' : '정상'}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* ================= 2. 격자 카드 뷰 ================= */
        <div className="row g-3">
          {filtered.map((st) => {
            const gridObs = st.latestObsTideCm;
            const gridTotal = st.latestTotalTideCm;

            let gridBadgeBg = '#d1e7dd';
            let gridBadgeClass = 'bg-success';
            let gridBadgeText = '✅ 정상 수위';
            if (st.alertLevel === 'WARNING') {
              gridBadgeBg = '#f8d7da';
              gridBadgeClass = 'bg-danger';
              gridBadgeText = '🚨 경보 초과';
            } else if (st.alertLevel === 'ADVISORY') {
              gridBadgeBg = '#fff3cd';
              gridBadgeClass = 'bg-warning text-dark';
              gridBadgeText = '⚠️ 주의보 초과';
            }

            return (
              <div key={st.stationCode} className="col-sm-6 col-lg-4 col-xl-3">
                <div className="card shadow-sm h-100 hover-shadow transition">
                  {/* 카드 헤더 */}
                  <div className="card-header bg-white py-2 px-3 d-flex align-items-center justify-content-between">
                    <div className="d-flex align-items-center gap-1.5">
                      <span className="fw-bold text-dark fs-6">{st.name}</span>
                      <span className="badge bg-light text-secondary border font-monospace" style={{ fontSize: '0.65rem' }}>
                        {st.stationCode}
                      </span>
                    </div>
                    <span className="badge bg-secondary-subtle text-secondary small" style={{ fontSize: '0.7rem' }}>
                      {st.seaRegion}해
                    </span>
                  </div>

                  {/* 카드 바디: 관측 수위 & 12h 예측 */}
                  <div className="card-body p-3">
                    <div className="d-flex justify-content-between align-items-baseline mb-2">
                      <span className="text-muted small">현재 관측 수위</span>
                      <div className="text-end">
                        <span className="fs-3 fw-bold font-monospace text-primary">{gridObs != null ? Math.round(gridObs) : '–'}</span>
                        <span className="text-muted small ms-1">cm</span>
                      </div>
                    </div>

                    <div className="d-flex justify-content-between align-items-baseline mb-2">
                      <span className="text-muted small">12시간 뒤 예상 총수위</span>
                      <div className="text-end">
                        <span className="fs-6 fw-bold font-monospace text-secondary">{gridTotal != null ? Math.round(gridTotal) : '예측 없음'}</span>
                        {gridTotal != null && <span className="text-muted small ms-1">cm</span>}
                      </div>
                    </div>

                    {/* 상태 배지 */}
                    <div
                      className="d-flex align-items-center justify-content-between p-2 rounded mb-3"
                      style={{ backgroundColor: gridBadgeBg }}
                    >
                      <span className="small fw-semibold text-muted">특보 판정:</span>
                      <span className={`badge ${gridBadgeClass}`}>
                        {gridBadgeText}
                      </span>
                    </div>

                    {/* 임계치 안내 */}
                    <div className="d-flex justify-content-between text-muted border-top pt-2" style={{ fontSize: '0.75rem' }}>
                      <span>주의보: <strong>{st.advisoryThresholdCm}cm</strong></span>
                      <span>경보: <strong>{st.warningThresholdCm}cm</strong></span>
                    </div>
                  </div>

                  {/* 카드 푸터: 상세 예측 페이지 이동 버튼 */}
                  <div className="card-footer bg-light p-2 text-center">
                    <Link
                      href={`/forecast?station=${st.stationCode}`}
                      className="btn btn-outline-primary btn-sm w-100 fw-semibold d-flex align-items-center justify-content-center gap-1"
                    >
                      <span>예측 모델 분석 &middot; 차트 보기</span>
                      <i className="bi bi-chevron-right"></i>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
