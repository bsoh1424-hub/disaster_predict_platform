from rag_service import search

questions = [
    "현재 수위가 주의보 기준을 넘으면 어떤 조치를 해야 하나요?",
    "만조 시간대와 폭풍해일이 겹치면 위험도가 왜 커지나요?",
    "만조와 폭풍해일이 겹치면 왜 위험한가요?",
    "gk0",
    "0",
    "하0",
]

for q in questions:
    hits = search(q, k=3)
    print("질문:", q)
    for h in hits:
        print("  ", h["score"], h["title"], ">", h["section"])
    print()