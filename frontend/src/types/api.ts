// Spring Boot DTO와 1:1 매칭되는 TypeScript 인터페이스 (아키텍처 4.1 지침)

export interface UserInfo {
  id: number;
  username: string;
  name: string;
  role: string;
  department: string;
  createdAt: string;
}

export interface AuthResponse {
  token: string;
  username: string;
  name: string;
  role: string;
  department: string;
}

export interface StationSummary {
  stationCode: string;
  name: string;
  latitude: number;
  longitude: number;
  seaRegion: string;
  latestTotalTideCm: number | null;
  latestObsTideCm: number | null;
  latestObsTime: string | null;
  advisoryThresholdCm: number;
  warningThresholdCm: number;
  alertLevel: 'NORMAL' | 'ADVISORY' | 'WARNING';
  isExceeded: boolean;
  lastUpdated: string;
}

export interface ForecastPoint {
  leadHour: number;
  targetTime: string;
  astronomicalTideCm: number;
  residualCm: number;
  totalTideCm: number;
  exceedProbability: number;
  isExceeded: boolean;
  alertLevel: 'NORMAL' | 'ADVISORY' | 'WARNING';
  isTideOverlap: boolean;
}

export interface TideSummary {
  maxTotalTideCm: number;
  maxTideTime: string;
  maxResidualCm: number;
  maxResidualTime: string;
  highTideOverlap: boolean;
  overlapWindow: string;
}

export interface OfficialWarning {
  officialStatus: string;
  noticeText: string;
  matchWithModel: boolean;
}

export interface ForecastResponse {
  stationCode: string;
  stationName: string;
  baseTime: string;
  runId: number;
  runType: 'BATCH' | 'REALTIME';
  modelVersion: string;
  isFallback: boolean;
  advisoryThresholdCm: number;
  warningThresholdCm: number;
  localFloodThresholdCm: number;
  points: ForecastPoint[];
  reasonSummary: string;
  tideSummary: TideSummary;
  officialWarning: OfficialWarning;
}

export interface ObservationPoint {
  obsTime: string;
  tideObsCm: number;
  tidePredCm: number;
  residualCm: number;
  airPressureHpa: number;
  windSpeedMs: number;
  windDirDeg: number;
}

export interface ObservationResponse {
  stationCode: string;
  stationName: string;
  observations: ObservationPoint[];
}

export interface TyphoonCaseSummary {
  caseId: string;
  name: string;
  year: number;
  period: string;
  maxSurgeCm: number;
  affectedStations: string;
  description: string;
}

export interface EvaluationItem {
  stationCode: string;
  leadHour: number;
  peakErrorCm: number;
  peakTimeErrorHours: number;
  exceedF1: number;
  baselineAstroErrorCm: number;
  baselineRtsmErrorCm: number;
}

export interface TyphoonCaseDetail {
  caseInfo: TyphoonCaseSummary;
  evaluations: EvaluationItem[];
}

export interface RagResponse {
  query: string;
  answer: string;
  sources: string[];
  llm_used: string;
}
