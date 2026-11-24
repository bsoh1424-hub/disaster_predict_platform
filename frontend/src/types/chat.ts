export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatSource {
  docName: string;
  page: number;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}
