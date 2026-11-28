'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '../../lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password || !name.trim() || loading) return;
    if (password.length < 4) {
      setError('비밀번호는 4자 이상이어야 합니다.');
      return;
    }
    if (password !== passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.register(username.trim(), password, name.trim(), department.trim());
      sessionStorage.setItem('token', res.token);
      router.push('/rag');
    } catch {
      setError('회원가입에 실패했습니다. 이미 존재하는 아이디일 수 있습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-2 d-flex justify-content-center">
      <div className="card shadow-sm" style={{ width: '100%', maxWidth: '420px' }}>
        <div className="card-body p-4">
          <h4 className="fw-bold mb-1">회원가입</h4>
          <p className="text-muted small mb-4">
            계정을 만들면 방재 RAG AI를 이용할 수 있습니다.
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
              <label className="form-label small fw-semibold">비밀번호 (4자 이상)</label>
              <input
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                disabled={loading}
              />
            </div>
            <div>
              <label className="form-label small fw-semibold">비밀번호 확인</label>
              <input
                type="password"
                className="form-control"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                autoComplete="new-password"
                disabled={loading}
              />
            </div>
            <div>
              <label className="form-label small fw-semibold">이름</label>
              <input
                type="text"
                className="form-control"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                disabled={loading}
              />
            </div>
            <div>
              <label className="form-label small fw-semibold">부서 (선택)</label>
              <input
                type="text"
                className="form-control"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                disabled={loading}
              />
            </div>
            <button type="submit" className="btn btn-primary fw-semibold" disabled={loading}>
              {loading ? '가입 중...' : '회원가입'}
            </button>
          </form>
          <p className="small mt-3 mb-0">
            이미 계정이 있으신가요?{' '}
            <Link href="/login" className="text-decoration-none fw-semibold">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
