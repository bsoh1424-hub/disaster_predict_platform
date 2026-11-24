import {
  AuthResponse,
  ForecastResponse,
  ObservationResponse,
  RagResponse,
  StationSummary,
  TyphoonCaseDetail,
  TyphoonCaseSummary,
  UserInfo
} from '../types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';

function getAuthHeader(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  // 인증
  async login(username: string, password: string):Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error('로그인에 실패했습니다. 아이디 또는 비밀번호를 확인하세요.');
    return res.json();
  },

  async register(username: string, password: string, name: string, department: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, name, department }),
    });
    if (!res.ok) throw new Error('회원가입에 실패했습니다.');
    return res.json();
  },

  async getMe(): Promise<UserInfo | null> {
    try {
      const res = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { ...getAuthHeader() },
      });
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  },

  // 관측소 목록 및 상태 요약
  async getStations(): Promise<StationSummary[]> {
    const res = await fetch(`${API_BASE}/api/stations`, { cache: 'no-store' });
    if (!res.ok) throw new Error('관측소 목록 조회 실패');
    return res.json();
  },

  // 특정 관측소 최신 예측 조회
  async getForecast(stationCode: string): Promise<ForecastResponse> {
    const res = await fetch(`${API_BASE}/api/stations/${stationCode}/forecast`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`예측 데이터 조회 실패: ${stationCode}`);
    return res.json();
  },

  // 실측 및 천문조 과거 시계열 조회
  async getObservations(stationCode: string): Promise<ObservationResponse> {
    const res = await fetch(`${API_BASE}/api/stations/${stationCode}/observations`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`관측 데이터 조회 실패: ${stationCode}`);
    return res.json();
  },

  // 실시간 재계산 요청 (A1)
  async recalculate(stationCode: string): Promise<ForecastResponse> {
    const res = await fetch(`${API_BASE}/api/stations/${stationCode}/recalculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
    });
    if (!res.ok) throw new Error('실시간 재계산 요청 실패');
    return res.json();
  },

  // 태풍 사례 목록 (Q6)
  async getTyphoonCases(): Promise<TyphoonCaseSummary[]> {
    const res = await fetch(`${API_BASE}/api/cases`, { cache: 'no-store' });
    if (!res.ok) throw new Error('태풍 사례 목록 조회 실패');
    return res.json();
  },

  // 태풍 사례 상세 및 평가 결과
  async getCaseDetail(caseId: string): Promise<TyphoonCaseDetail> {
    const res = await fetch(`${API_BASE}/api/cases/${caseId}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`태풍 상세 조회 실패: ${caseId}`);
    return res.json();
  },

  // 방재 전문 RAG 어시스턴트 질의 (Spring Boot를 통해 FastAPI로 위임)
  async queryRag(query: string, stationCode?: string): Promise<RagResponse> {
    const res = await fetch(`${API_BASE}/api/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, stationCode }),
    });
    if (!res.ok) throw new Error('방재 AI 답변 생성 실패');
    return res.json();
  },
};
