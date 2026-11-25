"""FastAPI 껍데기 — RAG를 밖에서 부를 수 있게 열어주는 창구.

흐름: 챗봇 화면 → 이 FastAPI(8001) → rag_service.ask()
이 파일은 RAG 로직이 없다. 질문을 받아 rag_service에 넘기고, 답만 돌려준다.
로그인 검사는 여기서 안 한다. 스프링이 하고, user_id를 여기로 넘긴다.
실행: uvicorn main:app --port 8001 --reload
확인: http://127.0.0.1:8001/docs
챗봇 화면: http://127.0.0.1:8001/  (disaster-chatbot.html이 같은 폴더에 있을 때)
"""
from pathlib import Path  # 파일이 있는지 확인할 때 씀

from fastapi import FastAPI, HTTPException  # FastAPI: 웹 API를 만드는 도구
from fastapi.middleware.cors import CORSMiddleware  # CORS: 다른 주소의 화면이 이 서버를 부를 수 있게 해주는 설정
from fastapi.responses import FileResponse  # HTML 파일을 그대로 보내줄 때 씀
from pydantic import BaseModel  # BaseModel: 들어오는 JSON 모양을 정하는 틀

from rag_service import ask  # RAG 본체 (검색 + LLM 답변)

app = FastAPI(title="Disaster RAG API")  # 앱 이름 (Swagger /docs에 보임)

# CORS 설정 — 챗봇 HTML이 file://로 열리거나 다른 포트에서 열려도 이 서버를 부를 수 있게 한다.
# allow_origins=["*"]는 개발용이다. 팀 발표·배포 때는 Next.js 주소만 적는 것으로 바꿔야 한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 어느 주소에서 와도 받는다 (개발용)
    allow_credentials=False,  # 쿠키는 안 보낸다
    allow_methods=["*"],  # GET, POST 등 모든 방식을 받는다
    allow_headers=["*"],  # 모든 헤더를 받는다
)


class ChatRequest(BaseModel):
    user_id: int  # 스프링이 넘겨주는 로그인한 사용자 번호 (없으면 안 받음) — 숫자다. "test1"이 아니라 1처럼 보낸다.
    question: str  # 사용자 질문


class Source(BaseModel):
    title: str  # 근거 문서 이름
    section: str  # 근거 항목 (## 소제목)
    score: float  # 질문과 얼마나 비슷한지 (1에 가까울수록 비슷함)


class ChatResponse(BaseModel):
    answer: str  # LLM 답변
    sources: list[Source]  # 답의 근거 목록


@app.get("/")
def root():
    """챗봇 화면을 바로 보여주는 용도. http://127.0.0.1:8001/ 로 열면 된다."""
    html_path = Path(__file__).parent / "disaster-chatbot.html"  # 같은 폴더의 챗봇 HTML 파일
    if html_path.exists():  # HTML 파일이 있으면
        return FileResponse(html_path)  # 그 파일을 그대로 보내준다
    return {"ok": True, "message": "disaster-chatbot.html 파일이 rag 폴더에 없습니다."}  # 없으면 이 메시지를 보여준다


@app.get("/health")
def health():
    """서버가 켜져 있는지 확인하는 용도. {"ok": true}가 나오면 켜진 것이다."""
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """POST /chat — 질문을 받아 RAG 답변을 돌려준다."""
    if not req.question.strip():  # 빈 질문은 안 받음
        raise HTTPException(status_code=400, detail="question이 비어 있습니다.")
    result = ask(req.question, k=3)  # RAG 본체에 질문을 넘김
    return ChatResponse(answer=result["answer"], sources=result["sources"])
