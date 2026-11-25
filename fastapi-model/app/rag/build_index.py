from rag_service import build_index

if __name__ == "__main__":
    doc_count, chunk_count = build_index("documents")
    print(f"문서 {doc_count}개, 청크 {chunk_count}개를 ChromaDB에 저장했습니다.")
