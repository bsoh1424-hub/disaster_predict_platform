import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="p-8">
      <Link href="/" className="text-blue-600 underline">
        ← 메인으로 돌아가기
      </Link>

      <h1 className="mt-4 text-2xl font-bold">
        기후위기 연안 침식·폭풍해일 재난 예측 플랫폼
      </h1>

      <p className="mt-4">
        해수면 상승, 태풍, 백중사리로 인한 해안도로·상가 침수와 연안
        붕괴로부터 해안 거주민과 관광객의 안전을 지키기 위한
        프로젝트입니다.
      </p>

      <h2 className="mt-8 text-xl font-bold">AI 기능</h2>
      <ul className="mt-2 list-disc pl-6">
        <li>RNN/LSTM — 조위·기압·풍속·파고로 24~48시간 침수·월파 위험도 예측</li>
        <li>RAG — 연안재해 대피 요령, 풍수해보험 기준, 연안침식 실태보고서 Q&amp;A</li>
      </ul>

      <p className="mt-8 text-sm text-gray-500">
        현재 화면에 보이는 데이터는 개발용 Mock 데이터입니다.
      </p>
    </main>
  );
}