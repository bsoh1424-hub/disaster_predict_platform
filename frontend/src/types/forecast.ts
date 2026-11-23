export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface Region {
    id: number;
    name: string;
    city: string;
    lat: number;
    lng: number;
}

export interface FloodPrediction {
    id: number;
    regionId: number;
    predictedAt: string;
    targetAt: string;
    riskLevel: RiskLevel;
    riskScore: number;
    tideCm: number;
    waveHeight: number;
    modelVersion: string;
}