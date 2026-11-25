"""준비 단계 — 한 번만 실행한다. (팀 fastapi-model용)

문서(app/rag/documents/*.md) → 청킹 → 임베딩 → ChromaDB 저장.
서버를 켤 때마다 하는 것이 아니다. 문서가 바뀔 때만 다시 실행한다.

실행 (둘 중 하나):
  fastapi-model 폴더에서: python -m app.rag.build_index
  app/rag 폴더에서:      python build_index.py

이 파일이 있는 폴더 기준으로 찾는다. 어디서 실행해도 같은 documents를 본다.
"""

from pathlib import Path

# 패키지로 부를 때(python -m app.rag.build_index)는 상대 import,
# app/rag 폴더에서 직접 실행할 때는 일반 import를 쓴다.
# try/except ImportError로 나누지 않는다. rag_service 안에서 chromadb가
# 없어서 나는 에러까지 잡아서 다시 시도하면 진짜 원인이 안 보이기 때문.
if __package__:
    from .rag_service import build_index
else:
    from rag_service import build_index

if __name__ == "__main__":
    documents_dir = Path(__file__).resolve().parent / "documents"
    doc_count, chunk_count = build_index(str(documents_dir))
    print(f"문서 {doc_count}개, 청크 {chunk_count}개를 ChromaDB에 저장했습니다.")

