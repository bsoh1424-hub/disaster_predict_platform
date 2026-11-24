export interface TimeSeriesPoint {
  time: string; // 예: "2026-11-22T15:00:00"
  tideCm: number; // 조위 (cm)
  waveHeight: number; // 파고 (m)
  windSpeed: number; // 풍속 (m/s)
  riskScore: number; // 0-100
}