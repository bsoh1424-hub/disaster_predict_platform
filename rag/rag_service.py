"""RAG 서비스 — 재난 프로젝트,

흐름:
문서 불러오기 → 청킹 → 임베딩 → ChromaDB 저장 → 검색 → 프롬프트 조립 → LLM 답변
준비(색인)는 build_index.py로 한 번만 하고, 평소에는 ask()만 쓴다.
모델 이름은 easy_rag.py.
"""
import re
from pathlib import Path

import chromadb  # 벡터 저장소 (문서·청크·임베딩은 여기만 저장, MySQL에는 안 넣음)
import numpy as np
import requests

OLLAMA_URL = "http://127.0.0.1:11434"  # Ollama 서버 주소
LLM_MODEL = "exaone3.5:2.4b"  # 답변 모델 (한국어 소형)
EMBED_MODEL = "bge-m3"  # 임베딩 모델 (1024차원)
CHROMA_DIR = str(Path(__file__).resolve().parent / "chroma_db")  # ChromaDB 저장 폴더
COLLECTION_NAME = "disaster_docs"  # ChromaDB 안 컬렉션 이름 (테이블 이름 같은 것)

SYSTEM_PROMPT = """당신은 연안 재난 안내 도우미입니다.
<규칙>
- <문서> 안의 내용만 근거로 답합니다.
- 문서에 없는 내용은 추측하지 말고 "제공된 자료에서 확인할 수 없습니다"라고 답합니다.
- 숫자(일수, 금액, 시간)는 문서에 적힌 그대로 씁니다.
- 3문장 이내의 존댓말로 답하고, 마지막 줄에 <자료>에 적힌 출처를 그대로 붙입니다.
</규칙>"""


# ---------------------------------------------------------------- 1. 문서 불러오기
def load_docs(folder):
    """폴더의 .md 파일만 읽어 [{'file', 'title', 'text'}] 목록으로 돌려준다."""
    docs = []
    for path in sorted(Path(folder).rglob("*.md")):  # .md만 읽음 (PDF는 먼저 .md로 바꿔야 함)
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()  # 첫 줄 '# 제목'에서 '# '를 뗀 것
        docs.append({"file": path.name, "title": title, "text": text})
    return docs


# ---------------------------------------------------------------- 2. 청킹
def split_sections(doc):
    """'## 소제목' 단위로 자른다. 소제목은 section 칸에 남긴다."""
    chunks = []
    for part in re.split(r"\n(?=## )", doc["text"]):
        if not part.startswith("## "):
            continue  # 문서 제목·머리말은 건너뜀
        section, _, body = part.partition("\n")
        chunks.append({
            "chunk_id": f'{Path(doc["file"]).stem}-{len(chunks) + 1:02d}',
            "file": doc["file"],
            "title": doc["title"],
            "section": section.lstrip("# ").strip(),
            "text": body.strip(),
        })
    return chunks


def make_chunks(docs):
    """모든 문서를 잘라 청크 하나의 목록으로 합친다."""
    return [c for d in docs for c in split_sections(d)]


def chunk_text(chunk):
    """검색할 때 쓰는 글: 문서 제목 + 소제목 + 본문."""
    return f'{chunk["title"]} {chunk["section"]} {chunk["text"]}'


# ---------------------------------------------------------------- 3. 임베딩
def embed(texts, model=EMBED_MODEL, batch=32):
    """문장 목록 → (문장 수, 1024) 행렬. 길이를 1로 맞춰 '내적 = 코사인 유사도'가 되게 한다."""
    vecs = []
    for i in range(0, len(texts), batch):  # 32개씩 나눠서 보냄 (노트북과 같음)
        resp = requests.post(f"{OLLAMA_URL}/api/embed", timeout=300,
                             json={"model": model, "input": texts[i:i + batch]})
        resp.raise_for_status()
        vecs.extend(resp.json()["embeddings"])
    vecs = np.array(vecs)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


# ---------------------------------------------------------------- 4. ChromaDB 저장·검색
def get_collection():
    """ChromaDB를 열고 컬렉션을 돌려준다. cosine 공간으로 만든다."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # 코사인 유사도로 검색하겠다는 뜻
    )


def build_index(documents_dir="documents"):
    """준비 단계 (한 번만 실행). 문서 → 청킹 → 임베딩 → ChromaDB 저장."""
    docs = load_docs(documents_dir)
    if not docs:
        raise RuntimeError("documents 폴더에 .md 파일이 없습니다. 문서를 먼저 넣으세요.")
    chunks = make_chunks(docs)
    vectors = embed([chunk_text(c) for c in chunks])  # 청크를 숫자로 바꿈 (미리 한 번만)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(name=COLLECTION_NAME)  # 다시 만들 때 예전 것이 겹치지 않게 지움
    except Exception:
        pass  # 처음 만들 때는 지울 것이 없어서 그냥 넘어감
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=vectors.tolist(),
        documents=[c["text"] for c in chunks],
        metadatas=[{"title": c["title"], "section": c["section"], "file": c["file"]} for c in chunks],
    )
    return len(docs), len(chunks)


def search(question, k=3):
    """질문과 가장 비슷한 청크 k개를 ChromaDB에서 찾는다."""
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("ChromaDB가 비어 있습니다. python build_index.py를 먼저 실행하세요.")
    question_vec = embed([question])[0]  # 질문 1개를 숫자로 바꿈
    result = collection.query(query_embeddings=[question_vec.tolist()], n_results=k)
    hits = []
    for i in range(len(result["ids"][0])):
        meta = result["metadatas"][0][i]
        distance = float(result["distances"][0][i])  # cosine 공간에서는 거리 = 1 - 유사도
        hits.append({
            "title": meta["title"],
            "section": meta["section"],
            "file": meta["file"],
            "text": result["documents"][0][i],
            "score": round(1 - distance, 3),  # 1에 가까울수록 질문과 비슷함
        })
    return hits


# ---------------------------------------------------------------- 5. 프롬프트 + LLM 답변
def build_prompt(question, hits):
    """찾은 청크를 <문서> 태그로 감싸고, 그 아래에 질문을 붙인다."""
    docs = "\n".join(f'<자료 번호="{i}" 출처="{h["title"]} > {h["section"]}">\n{h["text"]}\n</자료>'
                     for i, h in enumerate(hits, 1))
    return f"<문서>\n{docs}\n</문서>\n\n질문: {question}"


def ask_llm(prompt, system=SYSTEM_PROMPT, temperature=0):
    """Ollama에 질문 하나를 보내고 답변 텍스트를 받는다. temperature 0이면 같은 질문에 같은 답."""
    resp = requests.post(f"{OLLAMA_URL}/api/chat", timeout=300, json={
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    })
    resp.raise_for_status()
    text = resp.json()["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()  # 생각 과정이 나오면 지움


def ask(question, k=3):
    """사용 단계. ① 검색 → ② 프롬프트 조립 → ③ LLM 답변. 답변과 근거를 함께 돌려준다."""
    hits = search(question, k=k)
    answer = ask_llm(build_prompt(question, hits))
    return {
        "question": question,
        "answer": answer,
        "sources": [{"title": h["title"], "section": h["section"], "score": h["score"]} for h in hits],
    }
