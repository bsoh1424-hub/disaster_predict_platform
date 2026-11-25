"""fastapi-model/app/rag 패키지 — 기존 RAG를 팀 FastAPI에 붙이는 묶음.

팀 코드에서는 이렇게 쓴다:
    from app.rag.rag_engine import DisasterRagEngine
    rag_engine = DisasterRagEngine()
    result = await rag_engine.answer_query("부산 폭풍해일 주의보 기준이 뭐야?", {"station": "BUSAN"})
"""

from .rag_engine import DisasterRagEngine, answer_query, query, rag_health
from .rag_service import ask, build_index, search

__all__ = ["DisasterRagEngine", "answer_query", "query", "rag_health", "ask", "build_index", "search"]
