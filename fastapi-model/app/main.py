import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

# fastapi-model 디렉터리를 sys.path 최우선 등록 (No module named 'app' 원천 방지)
CURRENT_DIR = Path(__file__).resolve().parent
FASTAPI_ROOT = CURRENT_DIR.parent
if str(FASTAPI_ROOT) not in sys.path:
    sys.path.insert(0, str(FASTAPI_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 루트 .env 로드
try:
    from dotenv import load_dotenv
    root_env = Path(__file__).resolve().parent.parent.parent / ".env"
    if root_env.exists():
        load_dotenv(dotenv_path=root_env)
except Exception:
    pass

from app.inference.predictor import SurgePredictor
from app.collector.collector import DataCollector
from app.rag.rag_engine import DisasterRagEngine

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Storm Surge ML & RAG Engine",
    description="국립해양조사원/기상청 데이터 기반 폭풍해일 조위 편차 딥러닝 추론 및 방재 RAG 계산 서버",
    version="1.0.0"
)

# CORS 설정 (Spring Boot 및 내부 네트워크 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 및 컴포넌트 초기화
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models", os.getenv("ACTIVE_MODEL_DIR", "surge_v1.0.0_2026-11-20"))

start_time = datetime.now(timezone(timedelta(hours=9)))
predictor = SurgePredictor(MODEL_DIR)
collector = DataCollector()
rag_engine = DisasterRagEngine()

# Pydantic Schemas
class PredictRequest(BaseModel):
    station_id: str = Field(..., example="BUSAN")
    base_time: str = Field(..., example="2026-11-23T09:00:00+09:00")
    features: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PredictionItem(BaseModel):
    lead_hour: int
    target_time: str
    residual_cm: float
    exceed_probability: float

class PredictResponse(BaseModel):
    station_id: str
    base_time: str
    model_version: str
    predictions: List[PredictionItem]

class RagRequest(BaseModel):
    query: str
    context_info: Optional[Dict[str, Any]] = None

@app.get("/health")
def health_check():
    """
    아키텍처 10, 11페이지 스펙:
    상태, 로드된 모델 버전, 로드 시각 반환
    """
    return {
        "status": "UP",
        "model_version": predictor.model_version,
        "loaded_at": start_time.isoformat(),
        "model_dir": MODEL_DIR
    }

@app.post("/predict", response_model=PredictResponse)
def predict_surge(req: PredictRequest):
    """
    Spring Boot 전용 내부 추론 API (아키텍처 11페이지)
    - 관측소, 기준시각, 피처를 받아 12h, 24h 잔차 및 초과확률 반환
    """
    try:
        result = predictor.predict(
            station_id=req.station_id,
            base_time_str=req.base_time,
            features=req.features or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/collector/trigger")
async def trigger_collection(station_id: str):
    """
    수집 모듈 트리거 (KHOA / KMA 데이터 수집)
    """
    try:
        result = await collector.collect_station_data(station_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data collection failed: {str(e)}")

@app.post("/rag/query")
async def rag_query(req: RagRequest):
    """
    폭풍해일/재난 대응 전문 RAG 질의응답 (Spring Boot 중계)
    1순위: app.rag.rag_service.ask() - ChromaDB + Ollama 실전 RAG
    실패 시: 기존 템플릿 엔진(rag_engine)으로 폴백
    """
    try:
        # 지연 임포트: chromadb가 없는 환경에서도 predict 등 다른 API가
        # 죽지 않게 한다. 임포트나 Ollama 호출이 실패하면 아래 폴백으로 간다.
        from app.rag.rag_service import ask as rag_ask
        result = await asyncio.to_thread(rag_ask, req.query)
        sources = [f"{s.get('title', '')} > {s.get('section', '')}"
                   for s in result.get("sources", [])]
        return {
            "query": req.query,
            "answer": result["answer"],
            "sources": sources,
            "llm_used": "ollama-rag",
        }
    except Exception as e:
        logger.warning("Real RAG failed, falling back to template: %s", e)
    try:
        response = await rag_engine.answer_query(req.query, req.context_info)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
