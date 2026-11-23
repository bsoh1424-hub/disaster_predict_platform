import type { ChatResponse } from "../../types/chat";

export const mockChatResponse: ChatResponse = {
  answer:
    "폭풍해일 특보가 발령되면 해안 저지대에서는 즉시 고지대나 지정 대피소로 이동하세요. 차량은 해안도로를 피하고, 침수된 도로는 절대 건너지 마세요.",
  sources: [
    {
      docName: "국민행동요령 - 폭풍해일",
      page: 12,
      snippet: "폭풍해일 특보 발령 시 해안 저지대 주민은 고지대로 대피한다.",
    },
    {
      docName: "재난 및 안전관리 기본법",
      page: 3,
      snippet: "재난 발생 시 주민은 대피 명령에 따라야 한다.",
    },
  ],
};
