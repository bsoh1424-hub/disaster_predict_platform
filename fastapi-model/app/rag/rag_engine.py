"""팀 fastapi-model 연동용 껍데기 — 화면(/rag)은 그대로, RAG 본체만 기존 것으로 바꾼다.

팀 main.py가 쓰는 모양 (원본 기준):
- 클래스: app.rag.rag_engine.DisasterRagEngine
- main.py가 서버를 켤 때 DisasterRagEngine()을 한 번 만들고,
  /rag/query가 들어오면 await rag_engine.answer_query(query, context_info)를 부른다.
- 돌려주는 모양은 기존 틀과 같다: {"query", "answer", "sources", "llm_used"}.
  sources는 문자열 목록 ("제목 > 항목")이다. llm_used에는 실제 모델명을 넣는다.

이 파일은 RAG 로직이 없다. 질문을 받아 rag_service.ask()에 넘기고,
팀이 쓰기 좋은 모양(answer + sources)으로 돌려준다.
원래 파일(rag/main.py, 8001번)은 그대로 두면 된다. 둘은 따로 뜬다.

흐름:
브라우저(/rag) → Next.js → Spring Boot → 팀 FastAPI(8000) → DisasterRagEngine.answer_query() → rag_service.ask()
"""

import asyncio

if __package__:
    from .rag_service import ask, get_collection, OLLAMA_URL, LLM_MODEL
else:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from rag_service import ask, get_collection, OLLAMA_URL, LLM_MODEL

import requests


def answer_query(question, k=3, station=None):
    """질문 하나를 받아 답변과 근거를 돌려준다. 단독 테스트용 함수다.

    question: 사용자 질문 (예: "부산 폭풍해일 주의보 기준이 뭐야?")
    k: 근거로 쓸 청크 개수 (기본 3개 — 원래 설정과 같음)
    station: 화면의 관측소 선택값 (예: "BUSAN"). 결과에만 적고, 검색어는 바꾸지 않는다.
        팀 코드가 station을 안 넘겨도 된다. 안 넘기면 None으로 둔다.

    돌려주는 모양:
    {
        "question": "부산 폭풍해일 주의보 기준이 뭐야?",
        "answer": "3문장 이내의 존댓말 답변... (마지막 줄에 출처가 붙음)",
        "sources": [
            {"title": "문서 제목", "section": "## 소제목", "score": 0.812,
             "source": "문서 제목 > 소제목", "file": "01-침수.md"},
        ],
        "station": "BUSAN",
    }
    """
    if not question or not str(question).strip():
        raise ValueError("question이 비어 있습니다.")
    result = ask(str(question).strip(), k=k)  # RAG 본체에 질문을 넘김
    sources = [
        {
            "title": s["title"],
            "section": s["section"],
            "score": s["score"],
            "source": f'{s["title"]} > {s["section"]}',  # 화면의 "[출처: 문서명 > 항목]" 모양
            "file": s.get("file", ""),
        }
        for s in result["sources"]
    ]
    return {
        "question": result["question"],
        "answer": result["answer"],
        "sources": sources,
        "station": station,
    }


def rag_health():
    """RAG가 답할 준비가 됐는지 확인하는 용도. 팀의 /health에서 쓰면 된다.

    {"ok": true, "chunks": 110}처럼 나오면 준비된 것이다.
    Ollama가 꺼져 있거나 인덱스가 비어 있으면 ok가 false가 되고, 이유는 detail에 적힌다.
    """
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        return {"ok": False, "chunks": 0, "detail": f"Ollama에 닿지 않습니다: {e}"}
    try:
        count = get_collection().count()
    except Exception as e:
        return {"ok": False, "chunks": 0, "detail": f"ChromaDB를 열 수 없습니다: {e}"}
    if count == 0:
        return {"ok": False, "chunks": 0, "detail": "ChromaDB가 비어 있습니다. python -m app.rag.build_index를 먼저 실행하세요."}
    return {"ok": True, "chunks": count, "detail": "준비됐습니다."}


class DisasterRagEngine:
    """팀 main.py가 만드는 RAG 엔진. 서버를 켤 때 한 번 만들어진다.

    무거운 초기화는 없다. ask()가 불릴 때 ChromaDB와 Ollama에 닿는다.
    main.py는 이렇게 쓴다:
        from app.rag.rag_engine import DisasterRagEngine
        rag_engine = DisasterRagEngine()
        response = await rag_engine.answer_query(req.query, req.context_info)
    """

    def __init__(self):
        pass

    async def answer_query(self, query, context_info=None):
        """main.py의 /rag/query가 부르는 함수.

        query: 사용자 질문 (예: "부산 폭풍해일 주의보 기준이 뭐야?")
        context_info: 화면이 같이 보내는 정보 (예: {"station": "BUSAN"}). 없어도 된다.
            station이 있으면 결과의 station에 적는다. 검색어는 바꾸지 않는다.

        돌려주는 모양 (기존 틀과 같다):
        {
            "query": "부산 폭풍해일 주의보 기준이 뭐야?",
            "answer": "답변...",
            "sources": ["문서 제목 > 소제목", ...],
            "llm_used": "exaone3.5:2.4b",
            "station": "BUSAN",
        }
        """
        if not query or not str(query).strip():
            raise ValueError("query가 비어 있습니다.")
        station = None
        if isinstance(context_info, dict):
            # 스프링이 보내는 키는 station_name이다. (RagService.java 원본 기준)
            station = (
                context_info.get("station")
                or context_info.get("station_id")
                or context_info.get("stationId")
                or context_info.get("station_name")
            )
        # ask()는 동기 함수라서, await로 기다리는 동안 서버가 멈추지 않게 별도 스레드로 돌린다.
        result = await asyncio.to_thread(ask, str(query).strip(), 3)
        sources = [f'{s["title"]} > {s["section"]}' for s in result["sources"]]
        return {
            "query": result["question"],
            "answer": result["answer"],
            "sources": sources,
            "llm_used": LLM_MODEL,
            "station": station,
        }
