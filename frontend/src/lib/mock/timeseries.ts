import type { TimeSeriesPoint } from "../../types/timeseries";

export const mockTimeSeries: TimeSeriesPoint[] = [
  { time: "2026-11-22T09:00:00", tideCm: 130, waveHeight: 0.6, windSpeed: 4.2, riskScore: 12 },
  { time: "2026-11-22T15:00:00", tideCm: 142, waveHeight: 0.8, windSpeed: 5.1, riskScore: 18 },
  { time: "2026-11-22T21:00:00", tideCm: 158, waveHeight: 1.1, windSpeed: 6.8, riskScore: 34 },
  { time: "2026-11-23T03:00:00", tideCm: 172, waveHeight: 1.5, windSpeed: 8.4, riskScore: 48 },
  { time: "2026-11-23T09:00:00", tideCm: 185, waveHeight: 1.8, windSpeed: 10.2, riskScore: 62 },
  { time: "2026-11-24T09:00:00", tideCm: 210, waveHeight: 2.9, windSpeed: 13.5, riskScore: 84 },
];
