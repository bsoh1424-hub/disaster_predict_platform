import Link from "next/link";
import { mockPredictions, mockRegion } from "../../lib/mock/forecast";

export default function ForecastPage() {
    return(
        <main className="p-8">
        <Link href="/" className="text-blue-600 underline">
            ← 메인으로 돌아가기
        </Link>

        <h1 className="mt-4 text-2xl font-bold">
            {mockRegion.city} {mockRegion.name} 48시간 예측
        </h1>

        <div className="mt-6 space-y-4">
            {mockPredictions.map((p) => (
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
        </main>
    );
}