import re
from pathlib import Path

import chromadb
import numpy as np
import requests

OLLAMA_URL = "http://127.0.0.1:11434"
LLM_MODEL = "exaone3.5:2.4b"
EMBED_MODEL = "bge-m3"
CHROMA_DIR = str(Path(__file__).resolve().parent / "chroma_db")
COLLECTION_NAME = "disaster_docs"

SYSTEM_PROMPT = """당신은 연안 재난 안내 도우미입니다.
<규칙>
- <문서> 안의 내용만 근거로 답합니다.
- 문서에 없는 내용은 추측하지 말고 "제공된 자료에서 확인할 수 없습니다"라고 답합니다.
- 숫자(일수, 금액, 시간)는 문서에 적힌 그대로 씁니다.
- 3문장 이내의 존댓말로 답하고, 마지막 줄에 출처를 '문서 제목 > 항목' 형태로 적습니다.
- 답에 <자료>, <문서> 같은 태그 이름은 절대 쓰지 않습니다.
</규칙>"""

# ---------------------------------------------------------------- 1. 문서 불러오기
def load_docs(folder):
    docs = []
    for path in sorted(Path(folder).rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = ""
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("<!--"):
                continue
            title = line.lstrip("# ").strip()
            break
        docs.append({"file": path.name, "title": title, "text": text})
    return docs

# ---------------------------------------------------------------- 2. 청킹
def split_sections(doc):
    chunks = []
    for part in re.split(r"\n(?=## )", doc["text"]):
        if not part.startswith("## "):
            continue
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
    return [c for d in docs for c in split_sections(d)]


def chunk_text(chunk):
    return f'{chunk["title"]} {chunk["section"]} {chunk["text"]}'

# ---------------------------------------------------------------- 3. 임베딩
def embed(texts, model=EMBED_MODEL, batch=32):
    vecs = []
    for i in range(0, len(texts), batch):
        resp = requests.post(f"{OLLAMA_URL}/api/embed", timeout=300,
                             json={"model": model, "input": texts[i:i + batch]})
        resp.raise_for_status()
        vecs.extend(resp.json()["embeddings"])
    vecs = np.array(vecs)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)

# ---------------------------------------------------------------- 4. ChromaDB 저장·검색
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(documents_dir="documents"):
    docs = load_docs(documents_dir)
    if not docs:
        raise RuntimeError("documents 폴더에 .md 파일이 없습니다. 문서를 먼저 넣으세요.")
    chunks = make_chunks(docs)
    vectors = embed([chunk_text(c) for c in chunks])
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
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
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("ChromaDB가 비어 있습니다. python build_index.py를 먼저 실행하세요.")
    question_vec = embed([question])[0]
    result = collection.query(query_embeddings=[question_vec.tolist()], n_results=k)
    hits = []
    for i in range(len(result["ids"][0])):
        meta = result["metadatas"][0][i]
        distance = float(result["distances"][0][i])
        hits.append({
            "title": meta["title"],
            "section": meta["section"],
            "file": meta["file"],
            "text": result["documents"][0][i],
            "score": round(1 - distance, 3),
        })
    return hits

# ---------------------------------------------------------------- 5. 프롬프트 + LLM 답변
def build_prompt(question, hits):
    docs = "\n".join(f'[출처 {i}] {h["title"]} > {h["section"]}\n{h["text"]}'
                     for i, h in enumerate(hits, 1))
    return f"<문서>\n{docs}\n</문서>\n\n질문: {question}"


def ask_llm(prompt, system=SYSTEM_PROMPT, temperature=0):
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
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def ask(question, k=3):
    hits = search(question, k=k)
    if not hits or hits[0]["score"] < 0.5:  # 점수가 0.5보다 낮으면 관련 자료가 없다는 뜻이다
        return {
            "question": question,
            "answer": "제공된 자료에서 확인할 수 없습니다.",
            "sources": [{"title": h["title"], "section": h["section"], "score": h["score"], "file": h["file"]} for h in hits],
        }
    answer = ask_llm(build_prompt(question, hits))
    return {
        "question": question,
        "answer": answer,
        "sources": [{"title": h["title"], "section": h["section"], "score": h["score"], "file": h["file"]} for h in hits],
    }
