'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '../../lib/api';
import { UserInfo } from '../../types/api';

export default function MyPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);

  useEffect(() => {
    if (!sessionStorage.getItem('token')) {
      router.push('/login?next=/mypage');
      return;
    }
    async function load() {
      const me = await api.getMe();
      if (!me) {
        router.push('/login?next=/mypage');
        return;
      }
      setUser(me);
      setName(me.name);
      setDepartment(me.department || '');
      setLoading(false);
    }
    load();
  }, [router]);

  const goLogin = () => router.push('/login?next=/mypage');

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || saving) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const updated = await api.updateProfile(name.trim(), department.trim());
      setUser(updated);
      setMessage('내 정보를 저장했습니다.');
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') return goLogin();
      setError('내 정보 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || changingPw) return;
    if (newPassword.length < 4) {
      setError('새 비밀번호는 4자 이상이어야 합니다.');
      return;
    }
    if (newPassword !== newPasswordConfirm) {
      setError('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    setChangingPw(true);
    setMessage(null);
    setError(null);
    try {
      await api.changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordConfirm('');
      setMessage('비밀번호를 변경했습니다.');
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') return goLogin();
      setError('비밀번호 변경에 실패했습니다. 현재 비밀번호를 확인하세요.');
    } finally {
      setChangingPw(false);
    }
  };

  const handleWithdraw = async () => {
    if (!window.confirm('정말 탈퇴하시겠습니까? 계정 정보가 삭제되고 되돌릴 수 없습니다.')) return;
    try {
      await api.deleteAccount();
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') return goLogin();
      setError('회원 탈퇴에 실패했습니다.');
      return;
    }
    sessionStorage.removeItem('token');
    router.push('/');
  };

  if (loading) {
    return (
      <div className="py-5 text-center text-muted">
        <div className="spinner-border text-primary" role="status"></div>
        <div className="mt-2 small">내 정보를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="py-2 d-flex justify-content-center">
      <div className="vstack gap-3" style={{ width: '100%', maxWidth: '560px' }}>
        <div>
          <h4 className="fw-bold mb-1">마이페이지</h4>
          <p className="text-muted small mb-0">내 계정 정보를 조회하고 수정합니다.</p>
        </div>

        {message && <div className="alert alert-success py-2 px-3 small mb-0">{message}</div>}
        {error && <div className="alert alert-danger py-2 px-3 small mb-0">{error}</div>}

        <div className="card shadow-sm">
          <div className="card-header bg-white fw-bold py-2 px-3">내 정보</div>
          <div className="card-body p-3">
            <dl className="row small mb-3">
              <dt className="col-3 text-muted">아이디</dt>
              <dd className="col-9 font-monospace mb-1">{user?.username}</dd>
              <dt className="col-3 text-muted">권한</dt>
              <dd className="col-9 mb-1">{user?.role}</dd>
              <dt className="col-3 text-muted">가입일</dt>
              <dd className="col-9 mb-0">{user?.createdAt?.replace('T', ' ').substring(0, 19)}</dd>
            </dl>
            <form onSubmit={handleSaveProfile} className="vstack gap-3">
              <div>
                <label className="form-label small fw-semibold">이름</label>
                <input
                  type="text"
                  className="form-control"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={saving}
                />
              </div>
              <div>
                <label className="form-label small fw-semibold">부서</label>
                <input
                  type="text"
                  className="form-control"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  disabled={saving}
                />
              </div>
              <div>
                <button type="submit" className="btn btn-primary fw-semibold" disabled={saving}>
                  {saving ? '저장 중...' : '저장'}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="card shadow-sm">
          <div className="card-header bg-white fw-bold py-2 px-3">비밀번호 변경</div>
          <div className="card-body p-3">
            <form onSubmit={handleChangePassword} className="vstack gap-3">
              <div>
                <label className="form-label small fw-semibold">현재 비밀번호</label>
                <input
                  type="password"
                  className="form-control"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  autoComplete="current-password"
                  disabled={changingPw}
                />
              </div>
              <div>
                <label className="form-label small fw-semibold">새 비밀번호 (4자 이상)</label>
                <input
                  type="password"
                  className="form-control"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={changingPw}
                />
              </div>
              <div>
                <label className="form-label small fw-semibold">새 비밀번호 확인</label>
                <input
                  type="password"
                  className="form-control"
                  value={newPasswordConfirm}
                  onChange={(e) => setNewPasswordConfirm(e.target.value)}
                  autoComplete="new-password"
                  disabled={changingPw}
                />
              </div>
              <div>
                <button type="submit" className="btn btn-primary fw-semibold" disabled={changingPw}>
                  {changingPw ? '변경 중...' : '비밀번호 변경'}
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="card shadow-sm border-danger">
          <div className="card-header bg-danger-subtle text-danger-emphasis fw-bold py-2 px-3">회원 탈퇴</div>
          <div className="card-body p-3 d-flex flex-wrap align-items-center justify-content-between gap-2">
            <span className="small text-muted">계정을 삭제합니다. 되돌릴 수 없습니다.</span>
            <button type="button" className="btn btn-outline-danger btn-sm fw-semibold" onClick={handleWithdraw}>
              탈퇴하기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
