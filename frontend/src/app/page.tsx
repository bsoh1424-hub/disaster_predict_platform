import Link from "next/link";
import { mockPredictions, mockRegion } from "../lib/mock/forecast";

function riskColor(level: string) {
  if (level === "HIGH") return "bg-red-100 text-red-800 border-red-300";
  if (level === "MEDIUM") return "bg-yellow-100 text-yellow-800 border-yellow-300";
  return "bg-green-100 text-green-800 border-green-300";
}

export default function Home() {
  const latest = mockPredictions[mockPredictions.length - 1];

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 px-8 py-6 text-white">
        <h1 className="text-2xl font-bold">
          {mockRegion.city} {mockRegion.name} 연안 위험 현황
        </h1>
        <p className="mt-1 text-blue-100">예측 시각: {latest.predictedAt}</p>
        <nav className="mt-4 space-x-4">
          <Link href="/forecast" className="underline">예측</Link>
          <Link href="/chatbot" className="underline">챗봇</Link>
          <Link href="/about" className="underline">소개</Link>
        </nav>
      </header>

      <div className="mx-auto max-w-4xl p-8">
        <div className="rounded-xl border bg-white p-6 shadow">
          <span className={`rounded-full border px-3 py-1 text-sm font-bold ${riskColor(latest.riskLevel)}`}>
            {latest.riskLevel}
          </span>
          <p className="mt-4 text-5xl font-bold">{latest.riskScore}점</p>
          <p className="mt-4 text-gray-600">예측 조위: {latest.tideCm}cm</p>
          <p className="text-gray-600">예측 파고: {latest.waveHeight}m</p>
          <p className="text-gray-600">예측 대상: {latest.targetAt}</p>
        </div>

        <h2 className="mt-8 text-xl font-bold">48시간 예측 목록</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {mockPredictions.map((p) => (
            <div key={p.id} className="rounded-xl border bg-white p-4 shadow">
              <span className={`rounded-full border px-3 py-1 text-sm font-bold ${riskColor(p.riskLevel)}`}>
                {p.riskLevel}
              </span>
              <p className="mt-3 text-2xl font-bold">{p.riskScore}점</p>
              <p className="mt-1 text-sm text-gray-600">{p.targetAt}</p>
              <p className="text-sm text-gray-600">조위 {p.tideCm}cm, 파고 {p.waveHeight}m</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}