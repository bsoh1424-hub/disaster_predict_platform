'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../lib/api';
import { StationSummary } from '../types/api';

export default function HomePage() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState<string>('전체');

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getStations();
        setStations(data);
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

  return (
    <div className="py-2">
      {/* 상단 헤더 & 알림 안내 */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4 pb-3 border-bottom">
        <div>
          <h2 className="fw-bold text-dark mb-1 d-flex align-items-center gap-2">
            <i className="bi bi-grid-1x2 text-primary"></i> 전국 연안 조위관측소 실시간 종합 현황판
          </h2>
          <p className="text-muted small mb-0">
            국립해양조사원(KHOA) 전국 10개 주요 조위관측소의 실시간 조위 및 폭풍해일 특보 임계 상태를 통합 모니터링합니다.
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
      <div className="alert alert-warning py-2 px-3 mb-4 d-flex align-items-center justify-content-between shadow-sm border-0">
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

      {/* 해역 필터 탭 */}
      <div className="d-flex align-items-center justify-content-between mb-3">
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

      {/* 10개 관측소 카드 그리드 */}
      {loading ? (
        <div className="card shadow-sm p-5 text-center text-muted">
          <div className="spinner-border text-primary mx-auto mb-3" role="status"></div>
          <div>전국 관측망 실시간 수위 데이터를 수집 중입니다...</div>
        </div>
      ) : error ? (
        <div className="alert alert-danger p-4 text-center">
          <div>{error}</div>
        </div>
      ) : (
        <div className="row g-3">
          {filtered.map((st) => (
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

                {/* 카드 바디: 총 수위 & 임계치 비교 */}
                <div className="card-body p-3">
                  <div className="d-flex justify-content-between align-items-baseline mb-2">
                    <span className="text-muted small">예상 최고 총수위</span>
                    <div className="text-end">
                      <span className="fs-3 fw-bold font-monospace text-primary">{st.latestTotalTideCm}</span>
                      <span className="text-muted small ms-1">cm</span>
                    </div>
                  </div>

                  {/* 상태 배지 */}
                  <div className="d-flex align-items-center justify-content-between p-2 rounded mb-3" style={{
                    backgroundColor: st.alertLevel === 'WARNING' ? '#f8d7da' : st.alertLevel === 'ADVISORY' ? '#fff3cd' : '#d1e7dd'
                  }}>
                    <span className="small fw-semibold text-muted">특보 판정:</span>
                    <span className={`badge ${
                      st.alertLevel === 'WARNING'
                        ? 'bg-danger'
                        : st.alertLevel === 'ADVISORY'
                        ? 'bg-warning text-dark'
                        : 'bg-success'
                    }`}>
                      {st.alertLevel === 'WARNING' ? '🚨 경보 초과' : st.alertLevel === 'ADVISORY' ? '⚠️ 주의보 초과' : '✅ 정상 수위'}
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
          ))}
        </div>
      )}
    </div>
  );
}
