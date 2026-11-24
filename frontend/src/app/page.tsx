'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { ForecastResponse, StationSummary } from '../types/api';
import DoubleCurveChart from '../components/DoubleCurveChart';
import RagChatBot from '../components/RagChatBot';

export default function DashboardPage() {
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>('BUSAN');
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recalculating, setRecalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isRagOpen, setIsRagOpen] = useState<boolean>(false);

  // 초기 관측소 목록 로드
  useEffect(() => {
    async function loadStations() {
      try {
        const data = await api.getStations();
        setStations(data);
        if (data.length > 0 && !data.find((s) => s.stationCode === selectedStation)) {
          setSelectedStation(data[0].stationCode);
        }
      } catch (err: unknown) {
        console.error(err);
        setError('Spring Boot 백엔드 서버에서 관측소 데이터를 불러오지 못했습니다.');
      }
    }
    loadStations();
  }, [selectedStation]);

  // 선택된 관측소 예측 로드
  useEffect(() => {
    async function loadForecast() {
      if (!selectedStation) return;
      setLoading(true);
      setError(null);
      try {
        const data = await api.getForecast(selectedStation);
        setForecast(data);
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
      const updatedStations = await api.getStations();
      setStations(updatedStations);
    } catch (err: unknown) {
      alert('실시간 재계산 요청 중 오류가 발생했습니다: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setRecalculating(false);
    }
  };

  const currentStationInfo = stations.find((s) => s.stationCode === selectedStation);

  return (
    <div className="space-y-6 relative pb-16">
      {/* 최상단 공지 및 공식 특보 안내 배지 (PRD F5) */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <span className="text-xl">⚠️</span>
          <div>
            <h4 className="text-sm font-bold text-amber-900">
              폭풍해일 공식 정보 대조 안내 (PRD F5)
            </h4>
            <p className="text-xs text-amber-800">
              본 시스템은 국립해양조사원 및 기상청 현업 수치예보(RTSM·CTSM)와 연계된 참고 경보입니다. 기상청 공식 특보 발표 시 공식 정보가 최우선입니다.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-amber-200 text-amber-900 font-semibold px-2.5 py-1 rounded">
            공식 특보 우선 원칙 준수
          </span>
        </div>
      </div>

      {/* 전국 주요 10개소 이상 조위관측소 탭/선택기 (PRD Q2) */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <span>📍</span> 전국 주요 조위관측소 선택 (10개소)
          </h2>
          <span className="text-xs text-slate-500">
            총 {stations.length}개 관측소 실시간 모니터링
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
          {stations.map((st) => {
            const isSelected = st.stationCode === selectedStation;
            return (
              <button
                key={st.stationCode}
                onClick={() => setSelectedStation(st.stationCode)}
                className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-600 border-blue-600 text-white shadow-md'
                    : 'bg-white border-slate-200 text-slate-800 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="font-bold text-sm">{st.name}</span>
                  <span
                    className={`text-[9px] px-1 py-0.5 rounded font-bold ${
                      isSelected
                        ? 'bg-blue-700 text-blue-100'
                        : st.alertLevel === 'WARNING'
                        ? 'bg-rose-100 text-rose-700'
                        : st.alertLevel === 'ADVISORY'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}
                  >
                    {st.alertLevel === 'WARNING'
                      ? '경보'
                      : st.alertLevel === 'ADVISORY'
                      ? '주의보'
                      : '정상'}
                  </span>
                </div>
                <div className="mt-2 text-xs">
                  <span className={`font-mono font-bold ${isSelected ? 'text-white' : 'text-slate-900'}`}>
                    {st.latestTotalTideCm}
                  </span>
                  <span className={`text-[10px] ml-0.5 ${isSelected ? 'text-blue-200' : 'text-slate-400'}`}>
                    cm
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {loading && !forecast ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
          <p>예측 및 관측 데이터를 분석 중입니다...</p>
        </div>
      ) : error ? (
        <div className="p-8 text-center text-rose-600 bg-rose-50 rounded-xl border border-rose-200">
          <p className="font-bold">{error}</p>
          <button
            onClick={() => setSelectedStation(selectedStation)}
            className="mt-4 px-4 py-1.5 bg-rose-600 text-white text-xs rounded-lg"
          >
            다시 시도
          </button>
        </div>
      ) : forecast ? (
        <>
          {/* 핵심 지표 요약 카드 (Q7, F2, F3, A1) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* 1차 핵심 표시: 총 수위 절대값 (Q7) */}
            <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm relative overflow-hidden">
              <span className="text-xs font-semibold text-slate-500 block mb-1">
                최고 예상 총 수위 (1차 판정 기준)
              </span>
              <div className="flex items-baseline space-x-2">
                <span className="text-3xl font-extrabold text-blue-600 font-mono">
                  {forecast.tideSummary.maxTotalTideCm}
                </span>
                <span className="text-sm font-semibold text-slate-500">cm</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-xs text-slate-500 border-t pt-2">
                <span>주의보: {forecast.advisoryThresholdCm}cm</span>
                <span>경보: {forecast.warningThresholdCm}cm</span>
              </div>
            </div>

            {/* 임계 초과 여부 & 경보 등급 (F2) */}
            <div
              className={`rounded-xl p-5 border shadow-sm ${
                forecast.points.some((p) => p.alertLevel === 'WARNING')
                  ? 'bg-rose-50 border-rose-300'
                  : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                  ? 'bg-amber-50 border-amber-300'
                  : 'bg-emerald-50 border-emerald-300'
              }`}
            >
              <span className="text-xs font-semibold text-slate-600 block mb-1">
                침수 임계 초과 판정 (F2)
              </span>
              <div className="flex items-center space-x-2">
                <span
                  className={`text-2xl font-black ${
                    forecast.points.some((p) => p.alertLevel === 'WARNING')
                      ? 'text-rose-600'
                      : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                      ? 'text-amber-600'
                      : 'text-emerald-700'
                  }`}
                >
                  {forecast.points.some((p) => p.alertLevel === 'WARNING')
                    ? '폭풍해일 경보 초과'
                    : forecast.points.some((p) => p.alertLevel === 'ADVISORY')
                    ? '폭풍해일 주의보 초과'
                    : '안전 (임계치 미만)'}
                </span>
              </div>
              <div className="mt-3 text-xs text-slate-600 border-t border-slate-200/50 pt-2">
                {forecast.points.some((p) => p.isExceeded)
                  ? '⚠️ 방파제 통제 및 저지대 배수문 가동 준비 요망'
                  : '✅ 현재 예측 총수위가 특보 기준 이하입니다'}
              </div>
            </div>

            {/* 만조 겹침 판정 배지 (F3) */}
            <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 block mb-1">
                만조 겹침 판정 (F3)
              </span>
              <div className="flex items-center space-x-2">
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-bold ${
                    forecast.tideSummary.highTideOverlap
                      ? 'bg-rose-100 text-rose-700 border border-rose-300'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {forecast.tideSummary.highTideOverlap ? '🔴 만조 겹침 집중 위험' : '⚪ 만조 분리 안전'}
                </span>
              </div>
              <p className="mt-3 text-xs text-slate-500 border-t pt-2">
                위험 구간: <span className="font-semibold text-slate-700">{forecast.tideSummary.overlapWindow}</span>
              </p>
            </div>

            {/* 예측 실행 상태 및 실시간 재계산 버튼 (A1) */}
            <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-slate-500">실행 모드 (A1)</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                      forecast.runType === 'REALTIME'
                        ? 'bg-purple-100 text-purple-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}
                  >
                    {forecast.runType}
                  </span>
                </div>
                <p className="text-xs text-slate-600 truncate">
                  모델: {forecast.modelVersion}
                </p>
                {forecast.isFallback && (
                  <span className="text-[10px] text-amber-600 font-bold block mt-0.5">
                    * FastAPI 통신 장애로 천문조 베이스라인 폴백 중
                  </span>
                )}
              </div>

              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                className="mt-3 w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-2 px-3 rounded-lg text-xs transition flex items-center justify-center space-x-1.5 disabled:opacity-50"
              >
                <span>{recalculating ? '🔄 재계산 중...' : '⚡ 실시간 재계산 요청 (A1)'}</span>
              </button>
            </div>
          </div>

          {/* 메인 이중 출력 곡선 차트 (F1, F2) */}
          <DoubleCurveChart
            points={forecast.points}
            advisoryThreshold={forecast.advisoryThresholdCm}
            warningThreshold={forecast.warningThresholdCm}
            stationName={forecast.stationName}
          />

          {/* 하단 2분할: 근거 패널 (F4) & 연안 방재 행동 지침 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 근거 패널 (PRD F4) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <span>📑</span> 침수 위험 요인 분석 근거 패널 (PRD F4)
                  </h3>
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">
                    설명 가능 AI (XAI)
                  </span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-slate-800 leading-relaxed font-medium">
                    {forecast.reasonSummary}
                  </p>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-600 font-medium">기압 역효과 (Inverse Barometer)</span>
                    <span className="font-semibold text-slate-900">1hPa 하강당 약 +1.0cm 상승 기여</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-600 font-medium">바람 밀어올림 (Wind Setup)</span>
                    <span className="font-semibold text-slate-900">풍속의 제곱 비례 및 연안 방향 집중</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
                    <span className="text-slate-600 font-medium">조석 상호작용 (Tide Interaction)</span>
                    <span className="font-semibold text-slate-900">만조 극값과 잔차 피크 중첩 위험도 분석</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 text-xs text-slate-500">
                관측소: <span className="font-semibold text-slate-700">{forecast.stationName} ({forecast.stationCode})</span> · 기준 시각: <span className="font-mono">{forecast.baseTime}</span>
              </div>
            </div>

            {/* 관측소 방재 제원 및 표준 행동 지침 (PRD 부록 A 대응) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <span>🛡️</span> 지자체 및 어항 단계별 방재 행동 지침
                  </h3>
                  <span className="text-xs bg-blue-50 text-blue-700 font-bold px-2 py-0.5 rounded">
                    특보 연계
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="border border-emerald-200 bg-emerald-50/60 p-3 rounded-lg">
                    <span className="font-bold text-emerald-800 block mb-1">1단계: 평시 및 잔차 단독 상승 시</span>
                    <p className="text-slate-700 leading-relaxed">
                      만조와 겹치지 않는 경우 총 수위 절대값이 임계치를 넘지 않으므로 과잉 대응을 지양하고 관측 조위 추이를 상시 모니터링합니다.
                    </p>
                  </div>
                  <div className="border border-amber-200 bg-amber-50/60 p-3 rounded-lg">
                    <span className="font-bold text-amber-800 block mb-1">2단계: 폭풍해일 주의보 ({forecast.advisoryThresholdCm}cm) 예상 시</span>
                    <p className="text-slate-700 leading-relaxed">
                      해안가 저지대 배수문 및 빗물펌프장 사전 가동 점검, 지하주차장·해안도로 사전 통제 준비, 어선 결박 및 피항 조치 완료.
                    </p>
                  </div>
                  <div className="border border-rose-200 bg-rose-50/60 p-3 rounded-lg">
                    <span className="font-bold text-rose-800 block mb-1">3단계: 폭풍해일 경보 ({forecast.warningThresholdCm}cm) 초과 예상 시</span>
                    <p className="text-slate-700 leading-relaxed">
                      해안 침수 우려 지역 주민 대피 권고 및 방파제·갯바위 전면 출입 통제, 상가 차수판 설치 완료 및 비상상황실 가동.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                <span>지역 문턱: <strong className="text-slate-700">{forecast.localFloodThresholdCm}cm</strong> (침수 시작 기준)</span>
                <span className="font-medium text-blue-600">행정안전부 국민행동요령 기준</span>
              </div>
            </div>
          </div>
        </>
      ) : null}

      {/* 우측 하단 RAG AI 테스트용 플로팅 토글 버튼 & 패널 */}
      <div className="fixed bottom-6 right-6 z-50">
        {!isRagOpen ? (
          <button
            onClick={() => setIsRagOpen(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold p-3.5 rounded-full shadow-xl flex items-center gap-2 transition hover:scale-105"
            title="방재 RAG 어시스턴트 열기"
          >
            <span className="text-xl">🤖</span>
            <span className="text-xs font-semibold pr-1">방재 RAG 챗봇</span>
          </button>
        ) : (
          <div className="w-[380px] sm:w-[420px] shadow-2xl rounded-2xl overflow-hidden border border-slate-300">
            <div className="bg-slate-800 text-white px-3 py-1.5 flex justify-end">
              <button
                onClick={() => setIsRagOpen(false)}
                className="text-slate-300 hover:text-white text-xs font-bold px-2 py-0.5"
              >
                ✕ 닫기
              </button>
            </div>
            <RagChatBot
              currentStationCode={selectedStation}
              currentStationName={currentStationInfo ? currentStationInfo.name : selectedStation}
            />
          </div>
        )}
      </div>
    </div>
  );
}
