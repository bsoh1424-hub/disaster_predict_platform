import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# ==============================================================================
# [사용자 전용 RAG 커스텀 영역]
# 사용자가 직접 RAG(LangChain, LlamaIndex, ChromaDB, Milvus, OpenAI, Gemini 등)를
# 구현할 수 있는 진입점입니다.
# ==============================================================================

class DisasterRagEngine:
    """
    폭풍해일/재난 대응 전문 RAG 엔진
    - 사용자가 직접 구축하거나 커스텀 LLM/벡터DB를 연결할 수 있습니다.
    """
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        logger.info("DisasterRagEngine initialized. Ready for custom RAG integration.")

    async def answer_query(self, query: str, context_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Spring Boot로부터 중계받은 사용자 질의와 현재 관측소 상황 컨텍스트를 받아
        RAG 처리 후 답변을 반환합니다.
        
        :param query: 사용자 질문 텍스트
        :param context_info: {'station_name', 'total_tide', 'is_exceeded', 'tide_overlap'}
        :return: {'query', 'answer', 'sources', 'llm_used'}
        """
        # ----------------------------------------------------------------------
        # TODO: 여기에 사용자의 커스텀 RAG 검색 및 생성 코드를 넣으시면 됩니다.
        # 예: retriever.get_relevant_documents(query) -> llm.invoke(...)
        # ----------------------------------------------------------------------

        ctx_summary = ""
        if context_info:
            ctx_summary = (
                f"\n[실시간 관측/예측 컨텍스트]\n"
                f"- 대상 관측소: {context_info.get('station_name', '')}\n"
                f"- 예상 최고 총수위: {context_info.get('total_tide', '')}cm\n"
                f"- 특보 임계 초과여부: {context_info.get('is_exceeded', '')}\n"
                f"- 만조 겹침 여부: {context_info.get('tide_overlap', '')}\n"
            )

        # 기본 표준 방재 지침 가이드 응답
        guide_answer = (
            f"질문하신 내용: '{query}'\n\n"
            f"[기본 방재 원칙]\n"
            f"1. 폭풍해일 침수 위험은 순수 해일 잔차가 아닌 [천문조 + 조위 편차(잔차) = 총 수위] 절대값을 기준으로 평가됩니다.\n"
            f"2. 만조 시간대와 강풍·기압 급강하가 겹칠 경우 저지대 배수문 가동 및 해안도로 사전 통제가 필수적입니다.\n"
            f"{ctx_summary}\n"
            f"(안내: RAG 모듈은 사용자가 직접 커스텀하여 교체할 수 있도록 분리되어 있습니다.)"
        )

        return {
            "query": query,
            "answer": guide_answer,
            "sources": ["국립해양조사원 조석표", "기상청 폭풍해일 특보기준"],
            "llm_used": "Custom-RAG-Ready"
        }
