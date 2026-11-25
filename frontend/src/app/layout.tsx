import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import AuthNav from '../components/AuthNav';

export const metadata: Metadata = {
  title: '해수면 이상 상승 폭풍해일 예측 관제 시스템',
  description: '국립해양조사원 및 기상청 데이터 기반 폭풍해일 딥러닝 예측 플랫폼',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        {/* Bootstrap 5.3.3 CSS & Icons CDN */}
        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
          crossOrigin="anonymous"
        />
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
        />
      </head>
      <body className="d-flex flex-column min-vh-100 bg-light">
        {/* Bootstrap 표준 상단 내비바 (4개 전용 페이지 메뉴 분리) */}
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark py-2 shadow-sm sticky-top">
          <div className="container-fluid px-4">
            <Link href="/" className="navbar-brand d-flex align-items-center gap-2 fw-bold text-white">
              <span className="fs-5">🌊</span>
              <span>폭풍해일 예측 관제 플랫폼</span>
              <span className="badge bg-primary text-uppercase" style={{ fontSize: '0.65rem' }}>
                v1.0
              </span>
            </Link>

            <div className="d-flex align-items-center gap-3">
              <ul className="navbar-nav me-auto mb-2 mb-lg-0 flex-row gap-3">
                <li className="nav-item">
                  <Link href="/" className="nav-link text-white fw-semibold px-2">
                    <i className="bi bi-grid-fill me-1"></i> 연안 종합 현황
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/forecast" className="nav-link text-white-50 hover-text-white fw-semibold px-2">
                    <i className="bi bi-graph-up-arrow me-1 text-primary"></i> 예측 모델 분석
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/rag" className="nav-link text-white-50 hover-text-white fw-semibold px-2">
                    <i className="bi bi-robot me-1 text-info"></i> 방재 RAG AI
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/backtest" className="nav-link text-white-50 hover-text-white fw-semibold px-2">
                    <i className="bi bi-clipboard-data me-1 text-warning"></i> 태풍 백테스트 평가
                  </Link>
                </li>
              </ul>

              <div className="d-none d-md-flex align-items-center gap-2">
                <span className="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
                  <span className="spinner-grow spinner-grow-sm me-1 text-success" style={{ width: '8px', height: '8px' }}></span>
                  실시간 관측망 가동 중
                </span>
                <AuthNav />
              </div>
            </div>
          </div>
        </nav>

        {/* 메인 콘텐츠 영역 */}
        <main className="container-fluid px-4 py-3 flex-grow-1">
          {children}
        </main>

        {/* 하단 푸터 */}
        <footer className="bg-white border-top py-3 text-muted" style={{ fontSize: '0.8rem' }}>
          <div className="container-fluid px-4 d-flex flex-column flex-sm-row justify-content-between align-items-center gap-2">
            <div>
              <strong>폭풍해일 예측 시스템</strong> &middot; Next.js + Spring Boot 4.1 + MariaDB + FastAPI
            </div>
            <div>
              데이터 출처: 국립해양조사원(KHOA) 조위관측소 &middot; 기상청(KMA) 수치모델 &middot; 공식 특보 발표 시 공식 정보가 최우선입니다.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
