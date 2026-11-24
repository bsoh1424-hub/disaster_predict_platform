import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

export const metadata: Metadata = {
  title: '해수면 이상 상승 폭풍해일 예측 플랫폼',
  description: '국립해양조사원 및 기상청 데이터 기반 12/24시간 조위 편차 딥러닝 추론 및 총 수위 침수 경보 시스템',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="bg-slate-50 text-slate-900 min-h-screen flex flex-col font-sans antialiased">
        <header className="bg-slate-900 text-white shadow-md border-b border-slate-800 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center space-x-2">
                <span className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-lg shadow">
                  🌊
                </span>
                <span className="font-bold text-lg tracking-tight text-white hover:text-blue-200 transition">
                  폭풍해일 예측 플랫폼 <span className="text-xs px-2 py-0.5 rounded bg-blue-800 text-blue-200 font-normal">v1.0</span>
                </span>
              </Link>

              <nav className="hidden md:flex space-x-1 pl-6">
                <Link
                  href="/"
                  className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition text-slate-200 hover:text-white"
                >
                  실시간 연안 대시보드
                </Link>
                <Link
                  href="/backtest"
                  className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition text-slate-200 hover:text-white"
                >
                  태풍 사례 백테스트 & 평가
                </Link>
              </nav>
            </div>

            <div className="flex items-center space-x-3 text-xs sm:text-sm">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                <span className="w-2 h-2 mr-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                실시간 연안 감시 가동중
              </span>
            </div>
          </div>
        </header>

        <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {children}
        </div>

        <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
          <p className="font-medium text-slate-700">
            폭풍해일 예측 시스템 (Next.js + Spring Boot 4.1 + MariaDB + FastAPI 딥러닝 & RAG)
          </p>
          <p className="mt-1">
            출처 데이터: 국립해양조사원(KHOA) 조위관측소 및 기상청(KMA) 수치예보(RTSM·CTSM) · 공식 특보 발표 시 공식 정보가 최우선입니다.
          </p>
        </footer>
      </body>
    </html>
  );
}
