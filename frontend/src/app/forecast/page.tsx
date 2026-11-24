"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { FloodPrediction } from "../../types/forecast";
import { mockRegion } from "../../lib/mock/forecast";
import { mockTimeSeries } from "../../lib/mock/timeseries";

function riskColor(level: string) {
  if (level === "HIGH") return "bg-red-100 text-red-800 border-red-300";
  if (level === "MEDIUM") return "bg-yellow-100 text-yellow-800 border-yellow-300";
  return "bg-green-100 text-green-800 border-green-300";
}

export default function ForecastPage() {
  const [predictions, setPredictions] = useState<FloodPrediction[]>([]);

  useEffect(() => {
    fetch("/api/forecast")
      .then((res) => res.json())
      .then((data) => setPredictions(data));
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 px-8 py-6 text-white">
        <h1 className="text-2xl font-bold">
          {mockRegion.city} {mockRegion.name} 48시간 예측
        </h1>
        <nav className="mt-4 space-x-4">
          <Link href="/" className="underline">메인</Link>
          <Link href="/chatbot" className="underline">챗봇</Link>
          <Link href="/about" className="underline">소개</Link>
        </nav>
      </header>

      <div className="mx-auto max-w-4xl p-8">
        <div className="grid gap-4 md:grid-cols-3">
          {predictions.map((p) => (
            <div key={p.id} className="rounded-xl border bg-white p-4 shadow">
              <span className={`rounded-full border px-3 py-1 text-sm font-bold ${riskColor(p.riskLevel)}`}>
                {p.riskLevel}
              </span>
              <p className="mt-3 text-2xl font-bold">{p.riskScore}점</p>
              <p className="mt-1 text-sm text-gray-600">{p.targetAt}</p>
              <p className="text-sm text-gray-600">조위 {p.tideCm}cm, 파고 {p.waveHeight}m</p>
              <p className="text-sm text-gray-500">모델: {p.modelVersion}</p>
            </div>
          ))}
        </div>

        <h2 className="mt-8 text-xl font-bold">시간별 시계열</h2>
        <div className="mt-4 overflow-hidden rounded-xl border bg-white shadow">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-3 text-left">시간</th>
                <th className="p-3 text-left">조위(cm)</th>
                <th className="p-3 text-left">파고(m)</th>
                <th className="p-3 text-left">풍속(m/s)</th>
                <th className="p-3 text-left">위험 점수</th>
              </tr>
            </thead>
            <tbody>
              {mockTimeSeries.map((point) => (
                <tr key={point.time} className="border-t">
                  <td className="p-3">{point.time}</td>
                  <td className="p-3">{point.tideCm}</td>
                  <td className="p-3">{point.waveHeight}</td>
                  <td className="p-3">{point.windSpeed}</td>
                  <td className="p-3 font-bold">{point.riskScore}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
