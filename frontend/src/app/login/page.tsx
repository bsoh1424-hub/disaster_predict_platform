'use client';

import React, { Suspense, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '../../lib/api';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get('next') || '/rag';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(username.trim(), password);
      localStorage.setItem('token', res.token);
      router.push(next);
    } catch {
      setError('로그인에 실패했습니다. 아이디 또는 비밀번호를 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-2 d-flex justify-content-center">
      <div className="card shadow-sm" style={{ width: '100%', maxWidth: '420px' }}>
        <div className="card-body p-4">
          <h4 className="fw-bold mb-1">로그인</h4>
          <p className="text-muted small mb-4">
            방재 RAG AI를 이용하려면 로그인이 필요합니다.
          </p>
          {error && (
            <div className="alert alert-danger py-2 px-3 small">{error}</div>
          )}
          <form onSubmit={handleSubmit} className="vstack gap-3">
            <div>
              <label className="form-label small fw-semibold">아이디</label>
              <input
                type="text"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                disabled={loading}
              />
            </div>
            <div>
              <label className="form-label small fw-semibold">비밀번호</label>
              <input
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                disabled={loading}
              />
            </div>
            <button type="submit" className="btn btn-primary fw-semibold" disabled={loading}>
              {loading ? '로그인 중...' : '로그인'}
            </button>
          </form>
          <p className="text-muted small mt-3 mb-0">
            테스트 계정: user / user123 (관리자: admin / admin123)
          </p>
          <Link href="/" className="small text-decoration-none d-inline-block mt-2">
            &larr; 대시보드로 돌아가기
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="py-5 text-center text-muted">
          <div className="spinner-border text-primary" role="status"></div>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
