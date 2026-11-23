import type {FloodPrediction, Region} from "@/src/types/forecast";

export const mockRegion: Region = {
  id: 1,
  name: "해운대",
  city: "부산",
  lat: 35.1587,
  lng: 129.1604,
};

export const mockPredictions: FloodPrediction[] = [
  {
    id: 1,
    regionId: 1,
    predictedAt: "2026-11-22T09:00:00",
    targetAt: "2026-11-22T15:00:00",
    riskLevel: "LOW",
    riskScore: 18,
    tideCm: 142,
    waveHeight: 0.8,
    modelVersion: "lstm-v1",
  },
  {
    id: 2,
    regionId: 1,
    predictedAt: "2026-11-22T09:00:00",
    targetAt: "2026-11-23T09:00:00",
    riskLevel: "MEDIUM",
    riskScore: 62,
    tideCm: 185,
    waveHeight: 1.8,
    modelVersion: "lstm-v1",
  },
  {
    id: 3,
    regionId: 1,
    predictedAt: "2026-11-22T09:00:00",
    targetAt: "2026-11-24T09:00:00",
    riskLevel: "HIGH",
    riskScore: 84,
    tideCm: 210,
    waveHeight: 2.9,
    modelVersion: "lstm-v1",
  },
];