'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '../../lib/api';
import { StationSummary } from '../../types/api';

export default function RagPage() {
  const router = useRouter();
  const [stations, setStations] = useState<StationSummary[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>('BUSAN');
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string; sources?: string[]; engine?: string }>>([
    {
      sender: 'bot',
      text: '안녕하세요! 폭풍해일 방재 RAG AI 어시스턴트 전용 페이지입니다.\n\n국립해양조사원 및 기상청 특보 기준, 지자체 행동 지침과 현재 선택된 관측소의 실시간 수위 데이터를 연계하여 전문적인 방재 가이드를 제공합니다. 궁금한 점을 질문해 보세요!',
      sources: ['국립해양조사원 조석 기준', '행정안전부 국민행동요령'],
      engine: 'Custom-RAG-Ready',
    },
  ]);

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      router.push('/login?next=/rag');
      return;
    }
    async function load() {
      try {
        const data = await api.getStations();
        setStations(data);
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, [router]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    if (!localStorage.getItem('token')) {
      router.push('/login?next=/rag');
      return;
    }

    const userText = query.trim();
    setQuery('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      const res = await api.queryRag(userText, selectedStation);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: res.answer,
          sources: res.sources,
          engine: res.llm_used,
        },
      ]);
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        router.push('/login?next=/rag');
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: '응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (q: string) => {
    setQuery(q);
  };

  return (
    <div className="py-2">
      {/* 상단 헤더 */}
      <div className="card shadow-sm mb-4">
        <div className="card-body p-3 d-flex flex-wrap align-items-center justify-content-between gap-3">
          <div className="d-flex align-items-center gap-3">
            <div className="bg-info text-dark rounded p-2 text-center d-flex align-items-center justify-center" style={{ width: 44, height: 44 }}>
              <i className="bi bi-robot fs-4"></i>
            </div>
            <div>
              <div className="d-flex align-items-center gap-2">
                <h4 className="mb-0 fw-bold fs-5 text-dark">방재 RAG AI 어시스턴트</h4>
                <span className="badge bg-info-subtle text-info-emphasis border border-info-subtle">
                  Custom RAG Integration
                </span>
              </div>
              <small className="text-muted">
                FastAPI <code>app/rag/rag_engine.py</code> 와 실시간 연동되는 전문 방재 지식 질의응답 전용 페이지
              </small>
            </div>
          </div>

          <div className="d-flex align-items-center gap-2">
            <label className="small text-muted fw-semibold">상황 연계 관측소:</label>
            <select
              className="form-select form-select-sm fw-bold border-info shadow-sm"
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              style={{ minWidth: '140px' }}
            >
              {stations.map((s) => (
                <option key={s.stationCode} value={s.stationCode}>
                  {s.name} ({s.stationCode})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 메인 2분할 레이아웃: 대형 채팅창(8 cols) vs 지식 베이스 가이드(4 cols) */}
      <div className="row g-3">
        {/* 채팅창 영역 */}
        <div className="col-lg-8">
          <div className="card shadow-sm d-flex flex-column" style={{ height: '620px' }}>
            <div className="card-header bg-white py-2 px-3 d-flex align-items-center justify-content-between">
              <span className="fw-bold d-flex align-items-center gap-2">
                <i className="bi bi-chat-dots-fill text-primary"></i> 방재 질의응답 채널
              </span>
              <span className="badge bg-light text-secondary border font-monospace">
                Spring Boot &rarr; FastAPI
              </span>
            </div>

            {/* 메시지 리스트 */}
            <div className="card-body p-3 overflow-auto flex-grow-1 bg-light">
              <div className="vstack gap-3">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`d-flex flex-column ${m.sender === 'user' ? 'align-items-end' : 'align-items-start'}`}
                  >
                    <div
                      className={`p-3 rounded shadow-sm ${
                        m.sender === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-white text-dark border'
                      }`}
                      style={{ maxWidth: '85%', fontSize: '0.9rem' }}
                    >
                      <div className="text-break" style={{ whiteSpace: 'pre-line', lineHeight: '1.6' }}>
                        {m.text}
                      </div>

                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-2 pt-2 border-top d-flex flex-wrap align-items-center gap-1.5" style={{ fontSize: '0.75rem' }}>
                          <span className={m.sender === 'user' ? 'text-white-50' : 'text-muted'}>
                            <i className="bi bi-journal-text me-1"></i>참고 근거:
                          </span>
                          {m.sources.map((s, i) => (
                            <span key={i} className="badge bg-secondary-subtle text-secondary border">
                              {s}
                            </span>
                          ))}
                          {m.engine && (
                            <span className="ms-auto font-monospace text-primary fw-bold" style={{ fontSize: '0.7rem' }}>
                              [{m.engine}]
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="d-flex align-items-center gap-2 text-muted small p-2">
                    <div className="spinner-border spinner-border-sm text-primary" role="status"></div>
                    <span>FastAPI RAG 엔진에서 방재 지식 및 실시간 상황을 분석 중입니다...</span>
                  </div>
                )}
              </div>
            </div>

            {/* 추천 질문 바 */}
            <div className="p-2 bg-white border-top border-bottom d-flex gap-2 overflow-auto">
              <button
                type="button"
                onClick={() => handleQuickQuestion('현재 수위가 주의보 기준을 넘으면 어떤 조치를 해야 하나요?')}
                className="btn btn-outline-secondary btn-sm text-nowrap rounded-pill flex-shrink-0"
                style={{ fontSize: '0.75rem' }}
              >
                🚨 주의보 기준 조치요령
              </button>
              <button
                type="button"
                onClick={() => handleQuickQuestion('총 수위와 조위 편차(잔차)의 차이가 무엇인가요?')}
                className="btn btn-outline-secondary btn-sm text-nowrap rounded-pill flex-shrink-0"
                style={{ fontSize: '0.75rem' }}
              >
                📖 총수위 vs 잔차 개념
              </button>
              <button
                type="button"
                onClick={() => handleQuickQuestion('만조 시간대와 폭풍해일이 겹치면 위험도가 왜 커지나요?')}
                className="btn btn-outline-secondary btn-sm text-nowrap rounded-pill flex-shrink-0"
                style={{ fontSize: '0.75rem' }}
              >
                🌊 만조 겹침 위험 메커니즘
              </button>
            </div>

            {/* 입력 폼 */}
            <div className="p-3 bg-white">
              <form onSubmit={handleSend} className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="방재 지침이나 폭풍해일 대응에 대해 질문하세요..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={loading}
                />
                <button
                  type="submit"
                  className="btn btn-primary px-4 fw-semibold"
                  disabled={loading || !query.trim()}
                >
                  <i className="bi bi-send-fill me-1"></i> 전송
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* 지식베이스 및 커스텀 가이드 사이드바 */}
        <div className="col-lg-4">
          <div className="vstack gap-3">
            {/* RAG 커스텀 안내 카드 */}
            <div className="card shadow-sm border-info">
              <div className="card-header bg-info-subtle text-info-emphasis fw-bold py-2 px-3">
                <i className="bi bi-code-slash me-1"></i> RAG 직접 구현 가이드
              </div>
              <div className="card-body p-3 small">
                <p className="mb-2 leading-relaxed">
                  이 화면은 사용자가 직접 구축할 RAG 엔진을 즉시 테스트할 수 있도록 연동되어 있습니다.
                </p>
                <div className="p-2 bg-light rounded border font-monospace text-dark mb-2" style={{ fontSize: '0.75rem' }}>
                  fastapi-model/app/rag/rag_engine.py
                </div>
                <p className="mb-0 text-muted" style={{ fontSize: '0.8rem' }}>
                  위 파일의 <code>answer_query</code> 함수에 원하시는 벡터DB(Chroma, Milvus)나 LangChain/LLM 검색 코드를 작성하시면 여기에 실시간으로 반영됩니다.
                </p>
              </div>
            </div>

            {/* 표준 특보 기준 요약 카드 */}
            <div className="card shadow-sm">
              <div className="card-header bg-white fw-bold py-2 px-3">
                <i className="bi bi-book me-1 text-primary"></i> 폭풍해일 특보 기준 참고표
              </div>
              <div className="card-body p-2">
                <table className="table table-sm table-bordered text-center mb-0 small">
                  <thead className="table-light">
                    <tr>
                      <th>관측소</th>
                      <th>주의보</th>
                      <th>경보</th>
                    </tr>
                  </thead>
                  <tbody className="font-monospace">
                    <tr><td>인천</td><td>966cm</td><td>1,004cm</td></tr>
                    <tr><td>평택</td><td>1,010cm</td><td>1,030cm</td></tr>
                    <tr><td>목포</td><td>522cm</td><td>544cm</td></tr>
                    <tr><td>여수</td><td>420cm</td><td>440cm</td></tr>
                    <tr><td>부산</td><td>183cm</td><td>214cm</td></tr>
                    <tr><td>울산</td><td>120cm</td><td>170cm</td></tr>
                    <tr><td>포항</td><td>109cm</td><td>150cm</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
