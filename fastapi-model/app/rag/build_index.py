from pathlib import Path

if __package__:
    from .rag_service import build_index
else:
    from rag_service import build_index

if __name__ == "__main__":
    documents_dir = Path(__file__).resolve().parent / "documents"
    doc_count, chunk_count = build_index(str(documents_dir))
    print(f"문서 {doc_count}개, 청크 {chunk_count}개를 ChromaDB에 저장했습니다.")