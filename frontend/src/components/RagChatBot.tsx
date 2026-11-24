'use client';

import React, { useState } from 'react';
import { api } from '../lib/api';

interface RagChatBotProps {
  currentStationCode: string;
  currentStationName: string;
}

export default function RagChatBot({ currentStationCode, currentStationName }: RagChatBotProps) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string; sources?: string[]; engine?: string }>>([
    {
      sender: 'bot',
      text: `안녕하세요! 방재 RAG AI 어시스턴트입니다. 현재 ${currentStationName} 관측소의 총 수위 및 조위 편차 상황을 기반으로 침수 위험 대응 절차와 특보 기준을 전문적으로 안내해 드립니다. 무엇이 궁금하신가요?`,
      sources: ['행정안전부 폭풍해일 행동요령', '국립해양조사원'],
      engine: 'Disaster-RAG-Engine',
    },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userText = query.trim();
    setQuery('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setLoading(true);

    try {
      // Spring Boot /api/rag/query 호출 -> FastAPI RAG 엔진으로 연계
      const res = await api.queryRag(userText, currentStationCode);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: res.answer,
          sources: res.sources,
          engine: res.llm_used,
        },
      ]);
    } catch {
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
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[520px]">
      <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-bold text-sm tracking-wide">폭풍해일 방재 RAG AI 어시스턴트</span>
        </div>
        <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
          {currentStationName} 상황 연계
        </span>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-sm">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                m.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none shadow-sm'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
              }`}
            >
              <p className="whitespace-pre-line leading-relaxed">{m.text}</p>
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap gap-1 text-[11px] text-slate-500">
                  <span className="font-semibold text-slate-600">참고 근거:</span>
                  {m.sources.map((s, i) => (
                    <span key={i} className="bg-slate-100 px-1.5 py-0.5 rounded">
                      {s}
                    </span>
                  ))}
                  {m.engine && (
                    <span className="ml-auto text-[10px] text-blue-600 font-mono">
                      via {m.engine}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce"></div>
            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]"></div>
            <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]"></div>
            <span>FastAPI 딥러닝/RAG 엔진에서 방재 지식 및 실시간 상황 분석 중...</span>
          </div>
        )}
      </div>

      {/* 추천 빠른 질문 */}
      <div className="px-3 py-2 bg-slate-100 border-t border-slate-200 flex gap-2 overflow-x-auto text-[11px]">
        <button
          onClick={() => handleQuickQuestion('현재 수위가 주의보 기준을 넘으면 어떤 조치를 해야 하나요?')}
          className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-slate-200 rounded-full border border-slate-300 text-slate-700 transition"
        >
          🚨 주의보 기준 조치요령
        </button>
        <button
          onClick={() => handleQuickQuestion('총 수위와 조위 편차(잔차)의 차이가 무엇인가요?')}
          className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-slate-200 rounded-full border border-slate-300 text-slate-700 transition"
        >
          📖 총수위 vs 잔차 개념
        </button>
        <button
          onClick={() => handleQuickQuestion('만조 시간대와 폭풍해일이 겹치면 위험도가 왜 커지나요?')}
          className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-slate-200 rounded-full border border-slate-300 text-slate-700 transition"
        >
          🌊 만조 겹침 위험 메커니즘
        </button>
      </div>

      {/* 입력 폼 */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-200 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="방재 절차나 폭풍해일 관련 질문을 입력하세요..."
          className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm transition disabled:opacity-50"
        >
          전송
        </button>
      </form>
    </div>
  );
}
