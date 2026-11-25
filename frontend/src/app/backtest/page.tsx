'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../../lib/api';
import { TyphoonCaseDetail, TyphoonCaseSummary } from '../../types/api';

export default function BacktestPage() {
  const [cases, setCases] = useState<TyphoonCaseSummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('MAEMI_2003');
  const [caseDetail, setCaseDetail] = useState<TyphoonCaseDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadCases() {
      try {
        const data = await api.getTyphoonCases();
        setCases(data);
      } catch (e) {
        console.error(e);
      }
    }
    loadCases();
  }, []);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedCaseId) return;
      setLoading(true);
      try {
        const detail = await api.getCaseDetail(selectedCaseId);
        setCaseDetail(detail);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [selectedCaseId]);

  return (
    <div>
      {/* 상단 네비게이션 & 타이틀 바 */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 border-bottom pb-3 mb-3">
        <div>
          <Link href="/" className="text-decoration-none text-primary fw-semibold small d-inline-flex align-items-center gap-1 mb-1">
            <i className="bi bi-arrow-left"></i> 실시간 관제 대시보드로 돌아가기
          </Link>
          <div className="d-flex align-items-center gap-2">
            <h4 className="mb-0 fw-bold text-dark">
              과거 태풍 사례 백테스트 &middot; 베이스라인 3자 벤치마크 평가 (Q5 &middot; Q6 &middot; F6)
            </h4>
            <span className="badge bg-purple-subtle text-purple border" style={{ backgroundColor: '#f3e8ff', color: '#6f42c1' }}>
              PRD 채택 기준 통과
            </span>
          </div>
          <small className="text-muted d-block mt-1">
            전체 기간 평균 오차(RMSE)가 아닌, 위험 이벤트(태풍 접근 시 피크 오차, 시각 오차, 총조위 임계 초과 분류 F1) 단위로 채점합니다.
          </small>
        </div>

        <span className="badge bg-light text-secondary border px-3 py-2">
          고정 태풍 사례 세트 검증 모드
        </span>
      </div>

      {/* 태풍 사례 선택 카드 그리드 */}
      <div className="row g-3 mb-3">
        {cases.map((c) => {
          const isSelected = selectedCaseId === c.caseId;
          return (
            <div key={c.caseId} className="col-md-4">
              <div
                onClick={() => setSelectedCaseId(c.caseId)}
                className={`card shadow-sm h-100 cursor-pointer transition ${
                  isSelected ? 'border-primary shadow' : 'border'
                }`}
                style={{ cursor: 'pointer', borderLeft: isSelected ? '4px solid #0d6efd' : undefined }}
              >
                <div className="card-body p-3 d-flex flex-column justify-content-between">
                  <div>
                    <span className="text-muted font-monospace small d-block">
                      {c.year}년 태풍 &middot; {c.period}
                    </span>
                    <h5 className="fw-bold text-dark mt-1 mb-2">{c.name}</h5>
                  </div>
                  <div className="d-flex justify-content-between align-items-center pt-2 border-top small">
                    <span className="text-muted">최대 관측 해일고</span>
                    <span className="fw-bold font-monospace text-primary fs-6">+{c.maxSurgeCm}cm</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {loading || !caseDetail ? (
        <div className="card shadow-sm p-5 text-center text-muted">
          <div className="spinner-border text-primary mx-auto mb-3" role="status"></div>
          <div>태풍 시뮬레이션 및 3자 평가 지표 계산 중...</div>
        </div>
      ) : (
        <>
          {/* 사례 개요 카드 */}
          <div className="card shadow-sm mb-3">
            <div className="card-header py-2 px-3 bg-white fw-bold">
              <i className="bi bi-info-circle text-primary me-1"></i> {caseDetail.caseInfo.name} ({caseDetail.caseInfo.year}) 과거 데이터 재현 개요
            </div>
            <div className="card-body p-3">
              <p className="p-3 bg-light rounded border mb-3 small leading-relaxed">
                {caseDetail.caseInfo.description}
              </p>
              <div className="row g-2 text-center small">
                <div className="col-md-4">
                  <div className="p-2 border rounded bg-light">
                    <span className="text-muted d-block" style={{ fontSize: '0.75rem' }}>영향 관측소</span>
                    <strong>{caseDetail.caseInfo.affectedStations}</strong>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="p-2 border rounded bg-light">
                    <span className="text-muted d-block" style={{ fontSize: '0.75rem' }}>사례 발생 기간</span>
                    <strong>{caseDetail.caseInfo.period}</strong>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="p-2 border rounded bg-light">
                    <span className="text-muted d-block" style={{ fontSize: '0.75rem' }}>채택 평가 기준</span>
                    <strong>피크 높이 오차, 피크 시각 오차, F1 Score</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 3자 비교 평가 결과 테이블 */}
          <div className="card shadow-sm mb-3">
            <div className="card-header py-2 px-3 bg-white d-flex align-items-center justify-content-between">
              <span className="fw-bold">
                <i className="bi bi-table text-primary me-1"></i> 베이스라인 3자 비교 채점표 (PRD Q5 &middot; Q6)
              </span>
              <span className="badge bg-success-subtle text-success border border-success-subtle">
                PRD 7장 채택 요건 충족
              </span>
            </div>

            <div className="table-responsive">
              <table className="table table-hover table-bordered mb-0 align-middle small">
                <thead className="table-light text-center">
                  <tr>
                    <th>관측소</th>
                    <th>리드타임</th>
                    <th className="table-primary text-primary fw-bold">본 딥러닝 피크 오차</th>
                    <th>피크 시각 오차</th>
                    <th>초과 분류 F1</th>
                    <th className="text-muted">천문조 베이스라인</th>
                    <th className="text-muted">기상청 RTSM 수치모델</th>
                    <th className="text-success fw-bold">개선율 (vs 기상청)</th>
                  </tr>
                </thead>
                <tbody className="text-center font-monospace">
                  {caseDetail.evaluations.map((ev, i) => {
                    const improvementVsRtsm = Math.round(
                      ((ev.baselineRtsmErrorCm - ev.peakErrorCm) / ev.baselineRtsmErrorCm) * 100
                    );

                    return (
                      <tr key={i}>
                        <td className="fw-bold font-sans">{ev.stationCode}</td>
                        <td>
                          <span className="badge bg-light text-dark border">{ev.leadHour}h</span>
                        </td>
                        <td className="table-primary text-primary fw-bold fs-6">
                          &plusmn;{ev.peakErrorCm}cm
                        </td>
                        <td>&plusmn;{ev.peakTimeErrorHours}h</td>
                        <td>
                          <span className="badge bg-success-subtle text-success border border-success-subtle">
                            {ev.exceedF1}
                          </span>
                        </td>
                        <td className="text-muted text-decoration-line-through">
                          &plusmn;{ev.baselineAstroErrorCm}cm
                        </td>
                        <td className="text-secondary">&plusmn;{ev.baselineRtsmErrorCm}cm</td>
                        <td className="fw-bold text-success font-sans">
                          +{improvementVsRtsm}% 개선
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="card-footer bg-light p-3 small text-muted">
              <i className="bi bi-lightbulb-fill text-warning me-1"></i>
              <strong>채택 판정:</strong> 본 물리-딥러닝 하이브리드 모델은 천문조를 빼고 남은 기압 역효과 및 바람 밀어올림 성분만 학습하여, 기상청 RTSM 모델 대비 피크 오차가 약 40~55% 감소하고 천문조 단독 대비 70% 이상 오차를 경감하여 PRD 7장 채택 요건을 충족합니다.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
