'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

export default function AuthNav() {
  const [loggedIn, setLoggedIn] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setLoggedIn(!!localStorage.getItem('token'));
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setLoggedIn(false);
    router.push('/login');
  };

  if (loggedIn) {
    return (
      <button
        type="button"
        onClick={handleLogout}
        className="btn btn-outline-light btn-sm fw-semibold"
      >
        로그아웃
      </button>
    );
  }

  return (
    <Link href="/login" className="btn btn-outline-light btn-sm fw-semibold">
      로그인
    </Link>
  );
}
