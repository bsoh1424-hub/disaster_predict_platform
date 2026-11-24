import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 px-8 py-6 text-white">
        <h1 className="text-2xl font-bold">
          기후위기 연안 침식·폭풍해일 재난 예측 플랫폼
        </h1>
        <nav className="mt-4 space-x-4">
          <Link href="/" className="underline">메인</Link>
          <Link href="/forecast" className="underline">예측</Link>
          <Link href="/chatbot" className="underline">챗봇</Link>
        </nav>
      </header>

      <div className="mx-auto max-w-4xl p-8">
        <div className="rounded-xl border bg-white p-6 shadow">
          <p className="leading-relaxed text-gray-700">
            해수면 상승, 태풍, 백중사리로 인한 해안도로·상가 침수와 연안
            붕괴로부터 해안 거주민과 관광객의 안전을 지키기 위한
            프로젝트입니다.
          </p>
        </div>

        <h2 className="mt-8 text-xl font-bold">AI 기능</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border bg-white p-4 shadow">
            <p className="font-bold">RNN/LSTM 예측</p>
            <p className="mt-1 text-gray-700">
              조위·기압·풍속·파고로 24~48시간 침수·월파 위험도를 예측합니다.
            </p>
          </div>
          <div className="rounded-xl border bg-white p-4 shadow">
            <p className="font-bold">RAG 챗봇</p>
            <p className="mt-1 text-gray-700">
              연안재해 대피 요령, 풍수해보험 기준, 연안침식 실태보고서를
              바탕으로 답합니다.
            </p>
          </div>
        </div>

        <p className="mt-8 text-sm text-gray-500">
          현재 화면에 보이는 데이터는 개발용 Mock 데이터입니다.
        </p>
      </div>
    </main>
  );
}
