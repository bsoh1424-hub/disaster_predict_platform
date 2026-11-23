from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="disaster-predict-ai-server")

# LSTM 모델이 아직 없어서 False로 둬
# 모델 오면 True로 바꾸고, predict 함수로 연결해
MODEL_READY = False


class FloodRequest(BaseModel):
    beach: str = "haeundae"
    hours_ahead: int = 48
    tide_cm: float = 0.0
    wave_m: float = 0.0
    wind_ms: float = 0.0


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": MODEL_READY}


@app.post("/predict/flood")
def predict_flood(req: FloodRequest):
    # 룰버전: 부산 기준값으로 판정해
    # 조위 183cm 주의보 / 214cm 경보
    # 파고 3m 주의보 / 5m 경보
    # 풍속 14m/s 주의보 / 21m/s 경보
    risk = "low"
    reasons = []

    if req.tide_cm >= 214 or req.wave_m >= 5 or req.wind_ms >= 21:
        risk = "high"
    elif req.tide_cm >= 183 or req.wave_m >= 3 or req.wind_ms >= 14:
        risk = "medium"

    if req.tide_cm >= 183:
        reasons.append(f"조위 {req.tide_cm}cm")
    if req.wave_m >= 3:
        reasons.append(f"파고 {req.wave_m}m")
    if req.wind_ms >= 14:
        reasons.append(f"풍속 {req.wind_ms}m/s")

    return {
        "beach": req.beach,
        "hours_ahead": req.hours_ahead,
        "risk": risk,
        "reason": ", ".join(reasons) if reasons else "기준값 이하",
        "model": "rule" if not MODEL_READY else "lstm",
    }


@app.post("/chat")
def chat(req: ChatRequest):
    # RAG 담당이 오기 전까지는 준비 중으로 둬
    return {
        "answer": "RAG 연결 준비 중이야.",
        "sources": [],
    }
