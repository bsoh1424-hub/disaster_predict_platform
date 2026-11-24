"use client";

import { useState } from "react";
import Link from "next/link";
import { mockChatResponse } from "../../lib/mock/chat";

export default function ChatbotPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex min-h-screen bg-gray-50">
      {sidebarOpen && (
        <aside className="w-64 shrink-0 border-r bg-white p-6">
          <h2 className="text-lg font-bold">RAG 정보</h2>
          <ul className="mt-4 space-y-2 text-sm text-gray-700">
            <li>문서 수: 7개 (MVP)</li>
            <li>청크 수: 164개 (예시)</li>
            <li>임베딩 모델: bge-m3 (예시)</li>
            <li>생성 모델: exaone3.5:2.4b (예시)</li>
          </ul>
          <button
            onClick={() => setSidebarOpen(false)}
            className="mt-6 rounded border px-3 py-1"
          >
            닫기
          </button>
        </aside>
      )}

      <main className="flex-1">
        <header className="bg-blue-700 px-8 py-6 text-white">
          <h1 className="text-2xl font-bold">법령·매뉴얼 챗봇</h1>
          <nav className="mt-4 space-x-4">
            <Link href="/" className="underline">메인</Link>
            <Link href="/forecast" className="underline">예측</Link>
            <Link href="/about" className="underline">소개</Link>
          </nav>
        </header>

        <div className="mx-auto max-w-4xl p-8">
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="mb-4 rounded border bg-white px-3 py-1"
            >
              RAG 정보 열기
            </button>
          )}

          <div className="rounded-xl border bg-white p-6 shadow">
            <p className="font-bold">질문: 폭풍해일 때 어떻게 대피하나요?</p>
            <p className="mt-3 leading-relaxed text-gray-700">
              {mockChatResponse.answer}
            </p>
          </div>

          <h2 className="mt-8 text-xl font-bold">출처</h2>
          <div className="mt-4 space-y-4">
            {mockChatResponse.sources.map((source) => (
              <div key={source.docName} className="rounded-xl border bg-white p-4 shadow">
                <p className="font-bold">
                  {source.docName} <span className="text-sm font-normal text-gray-500">(p. {source.page})</span>
                </p>
                <p className="mt-1 text-gray-700">{source.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
