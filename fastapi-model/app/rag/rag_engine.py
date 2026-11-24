import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# 재난 대응 및 폭풍해일 지식 베이스
DISASTER_KNOWLEDGE_BASE = [
    {
        "id": "kb_01",
        "category": "개념",
        "title": "총 수위와 잔차(조위 편차)의 정의",
        "content": "총 수위는 천문조(달과 태양의 인력에 의한 규칙적 예측 조위)와 기상 요인(기압 하강, 강풍 등)에 의해 발생하는 잔차(조위 편차)의 합입니다. 폭풍해일 특보 및 침수 판단은 잔차가 아닌 총 수위 절대값을 기준으로 발령됩니다."
    },
    {
        "id": "kb_02",
        "category": "특보 기준",
        "title": "주요 항만별 폭풍해일 특보 기준",
        "content": "인천: 주의보 966cm / 경보 1,004cm\n평택: 주의보 1,010cm / 경보 1,030cm\n목포: 주의보 522cm / 경보 544cm\n여수: 주의보 420cm / 경보 440cm\n부산: 주의보 183cm / 경보 214cm\n울산: 주의보 120cm / 경보 170cm\n포항: 주의보 109cm / 경보 150cm\n보령: 주의보 780cm / 경보 830cm\n군산: 주의보 740cm / 경보 790cm\n제주: 주의보 280cm / 경보 310cm\n서해안은 조차가 크고 동해안은 조차가 작아 기준 수위 차이가 큽니다."
    },
    {
        "id": "kb_03",
        "category": "대응 절차",
        "title": "만조 겹침 및 해일 주의보/경보 시 지자체 및 어항 행동요령",
        "content": "1. 폭풍해일 주의보 발령 예상 시: 저지대 배수문 및 빗물펌프장 사전 가동 점검, 해안가 도로 및 지하차도 통제 준비, 어선 결박 및 피항 조치 완료.\n2. 경보 발령 시: 해안 침수 위험지역 주민 대피령 발령, 방파제/갯바위 출입 전면 통제, 상가 차수판 설치 완료 확인.\n3. 만조 시간대(만조 전후 2시간)가 최대 위험 구간이므로 기압 급강하와 남풍 계열 강풍 지속 시 즉각 비상대응 단계를 격상합니다."
    },
    {
        "id": "kb_04",
        "category": "물리 요인",
        "title": "해일고를 결정짓는 핵심 기상 인자",
        "content": "1. 기압 역효과(Inverse Barometer): 중심 기압이 1hPa 낮아질 때마다 해수면은 약 1cm 상승합니다.\n2. 바람 밀어올림(Wind Setup): 연안을 향해 지속적으로 부는 강풍(풍속의 제곱에 비례)이 해수를 해안선에 축적시킵니다.\n3. 만조 겹침: 기상 잔차가 극대화되는 시점에 천문조의 만조가 겹치면 치명적인 침수 피해가 발생합니다."
    }
]

class DisasterRagEngine:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.docs = DISASTER_KNOWLEDGE_BASE

    def search_docs(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        tokens = query.lower().split()
        scores = []
        for doc in self.docs:
            score = 0
            text = (doc["title"] + " " + doc["content"] + " " + doc["category"]).lower()
            for t in tokens:
                if t in text:
                    score += 2
            scores.append((score, doc))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        results = [d for s, d in scores[:top_k] if s > 0]
        if not results:
            results = self.docs[:top_k]
        return results

    async def answer_query(self, query: str, context_info: Dict[str, Any] = None) -> Dict[str, Any]:
        matched_docs = self.search_docs(query)
        doc_texts = "\n\n".join([f"[{d['title']}]\n{d['content']}" for d in matched_docs])
        
        ctx_str = ""
        if context_info:
            ctx_str = f"\n[현재 관측/예측 상황]\n관측소: {context_info.get('station_name', '')}\n예측 총수위: {context_info.get('total_tide', '')}cm\n임계 초과여부: {context_info.get('is_exceeded', '')}\n만조 겹침 여부: {context_info.get('tide_overlap', '')}"

        # Gemini API 호출 시도 (API 키가 제공된 경우)
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
                prompt = f"""당신은 국립해양조사원 및 기상청 데이터를 바탕으로 폭풍해일 침수 위험을 분석하고 대응을 안내하는 AI 방재 전문가입니다.
아래 전문 지식과 현재 상황을 바탕으로 사용자의 질문에 전문적이고 명확하게 한국어로 답변하십시오.
[지식 베이스]
{doc_texts}
{ctx_str}

[질문]
{query}"""
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=8.0) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "query": query,
                        "answer": text,
                        "sources": [d["title"] for d in matched_docs],
                        "llm_used": "Gemini-1.5-Flash"
                    }
            except Exception as e:
                logger.warning(f"Gemini API 호출 예외, Fallback 로컬 지식 엔진으로 응답: {e}")

        # 로컬 지식 베이스 Fallback 응답 생성기
        answer_parts = []
        answer_parts.append(f"전문 방재 지식 베이스 검색 결과에 기반한 안내입니다:")
        for d in matched_docs:
            answer_parts.append(f"■ {d['title']}\n{d['content']}")

        if context_info and context_info.get("station_name"):
            st_name = context_info.get("station_name")
            total = context_info.get("total_tide")
            exceeded = context_info.get("is_exceeded")
            answer_parts.append(f"\n[현재 {st_name} 관측소 상태 권고]\n예상 총 수위: {total}cm (특보 기준 초과: {exceeded})\n만조 시간대 저지대 침수 우려 구역에 대한 예찰 활동을 강화하시기 바랍니다.")

        return {
            "query": query,
            "answer": "\n\n".join(answer_parts),
            "sources": [d["title"] for d in matched_docs],
            "llm_used": "Local-Disaster-Knowledge-Engine"
        }
