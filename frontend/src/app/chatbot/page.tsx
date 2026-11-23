import Link from "next/link";
import { mockChatResponse } from "../../lib/mock/chat";

export default function ChatbotPage() {
  return (
    <main className="p-8">
      <Link href="/" className="text-blue-600 underline">
        ← 메인으로 돌아가기
      </Link>

      <h1 className="mt-4 text-2xl font-bold">법령·매뉴얼 챗봇</h1>

      <div className="mt-6 rounded-lg border p-4">
        <p className="font-bold">질문: 폭풍해일 때 어떻게 대피하나요?</p>
        <p className="mt-2">{mockChatResponse.answer}</p>
      </div>

      <h2 className="mt-8 text-xl font-bold">출처</h2>
      <div className="mt-4 space-y-4">
        {mockChatResponse.sources.map((source) => (
          <div key={source.docName} className="rounded-lg border p-4">
            <p className="font-bold">
              {source.docName} (p. {source.page})
            </p>
            <p>{source.snippet}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
