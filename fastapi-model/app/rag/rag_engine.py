import asyncio
import re 

try:
    from .rag_service import ask, LLM_MODEL
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rag_service import ask, LLM_MODEL

GUARD_ANSWER = "이것만으로는 어떤 내용인지 알 수 없어요. 질문을 문장으로 적어주세요."


def _is_number_only_query(query): 
    text = str(query).strip() 
    if not text:
        return True
    if text.isdigit():
        return True
    if not re.search(r"[가-힣a-zA-Z]", text):
        return True
    return False 

class DisasterRagEngine:
    def __init__(self):
        pass

    async def answer_query(self, query, context_info=None):
        if not query or not str(query).strip():
            raise ValueError("query가 비어 있습니다.")
        station = None

        if isinstance(context_info, dict):
            station = (
                context_info.get("station")
                or context_info.get("station_id")
                or context_info.get("stationId")
                or context_info.get("station_name")
            )
        if _is_number_only_query(query):
            return {
                "query": str(query).strip(),
                "answer": GUARD_ANSWER,
                "sources": [], 
                "llm_used": "없음", 
                "station": station,
            }
        result = await asyncio.to_thread(ask, str(query).strip(), 3)
        sources = [f'{s["title"]} > {s["section"]}' for s in result["sources"]]
        return {
            "query": result["question"],
            "answer": result["answer"],
            "sources": sources,
            "llm_used": LLM_MODEL,
            "station": station,
        }
