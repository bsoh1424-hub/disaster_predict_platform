"""준비 단계 (S3) — 한 번만 실행한다.

문서(documents/*.md) → 청킹 → 임베딩 → ChromaDB 저장.
서버를 켤 때마다 하는 것이 아니다. 문서가 바뀔 때만 다시 실행한다.
실행: python build_index.py
"""
from rag_service import build_index

if __name__ == "__main__":
    doc_count, chunk_count = build_index("documents")
    print(f"문서 {doc_count}개, 청크 {chunk_count}개를 ChromaDB에 저장했습니다.")
