import Link from "next/link";
import { mockPredictions, mockRegion } from "../lib/mock/forecast";

export default function Home() {
  const latest = mockPredictions[mockPredictions.length - 1];

  return (
    <main className="p-8">
      <nav className="mb-6 space-x-4">
        <Link href="/forecast" className="text-blue-600 underline">
          예측
        </Link>
        <Link href="/chatbot" className="text-blue-600 underline">
          챗봇
        </Link>
        <Link href="/about" className="text-blue-600 underline">
          소개
        </Link>
      </nav>

      <h1 className="text-2xl font-bold">
        {mockRegion.city} {mockRegion.name} 연안 위험 현황
      </h1>
      <p className="mt-2">예측 시각: {latest.predictedAt}</p>

      <div className="mt-6 rounded-lg border p-6">
        <p className="text-xl font-bold">위험 단계: {latest.riskLevel}</p>
        <p className="mt-2 text-4xl font-bold">{latest.riskScore}점</p>
        <p className="mt-2">예측 조위: {latest.tideCm}cm</p>
        <p>예측 파고: {latest.waveHeight}m</p>
        <p>예측 대상: {latest.targetAt}</p>
      </div>

      <h2 className="mt-8 text-xl font-bold">48시간 예측 목록</h2>
      <div className="mt-4 space-y-4">
        {mockPredictions.map((p) => (
          <div key={p.id} className="rounded-lg border p-4">
            <p>
              {p.targetAt} — {p.riskLevel} {p.riskScore}점
            </p>
            <p>
              조위 {p.tideCm}cm, 파고 {p.waveHeight}m
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
