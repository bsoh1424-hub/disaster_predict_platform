"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { FloodPrediction } from "../../types/forecast";
import { mockRegion } from "../../lib/mock/forecast";
import { mockTimeSeries } from "../../lib/mock/timeseries";

export default function ForecastPage() {
  const [predictions, setPredictions] = useState<FloodPrediction[]>([]);

  useEffect(() => {
    fetch("/api/forecast")
      .then((res) => res.json())
      .then((data) => setPredictions(data));
  }, []);

  return (
    <main className="p-8">
      <Link href="/" className="text-blue-600 underline">
        ← 메인으로 돌아가기
      </Link>

      <h1 className="mt-4 text-2xl font-bold">
        {mockRegion.city} {mockRegion.name} 48시간 예측
      </h1>

      <div className="mt-6 space-y-4">
        {predictions.map((p) => (
          <div key={p.id} className="rounded-lg border p-4">
            <p className="font-bold">
              {p.targetAt} — {p.riskLevel} {p.riskScore}점
            </p>
            <p>예측 조위: {p.tideCm}cm</p>
            <p>예측 파고: {p.waveHeight}m</p>
            <p>모델: {p.modelVersion}</p>
          </div>
        ))}
      </div>

      <h2 className="mt-8 text-xl font-bold">시간별 시계열</h2>
      <table className="mt-4 w-full border">
        <thead>
          <tr>
            <th className="border p-2">시간</th>
            <th className="border p-2">조위(cm)</th>
            <th className="border p-2">파고(m)</th>
            <th className="border p-2">풍속(m/s)</th>
            <th className="border p-2">위험 점수</th>
          </tr>
        </thead>
        <tbody>
          {mockTimeSeries.map((point) => (
            <tr key={point.time}>
              <td className="border p-2">{point.time}</td>
              <td className="border p-2">{point.tideCm}</td>
              <td className="border p-2">{point.waveHeight}</td>
              <td className="border p-2">{point.windSpeed}</td>
              <td className="border p-2">{point.riskScore}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}