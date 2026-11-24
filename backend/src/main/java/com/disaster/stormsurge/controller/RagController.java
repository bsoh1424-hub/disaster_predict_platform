package com.disaster.stormsurge.controller;

import com.disaster.stormsurge.dto.FastApiDto.RagResponse;
import com.disaster.stormsurge.service.RagService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/rag")
public class RagController {

    private final RagService ragService;

    public RagController(RagService ragService) {
        this.ragService = ragService;
    }

    /**
     * 서비스 요청은 전부 Spring Boot로 들어오고,
     * FastAPI로 딥러닝과 RAG 계산만 위임하여 응답 반환
     */
    @PostMapping("/query")
    public ResponseEntity<RagResponse> askAssistant(@RequestBody Map<String, String> body) {
        String query = body.getOrDefault("query", "");
        String stationCode = body.get("stationCode");
        return ResponseEntity.ok(ragService.askDisasterAssistant(query, stationCode));
    }
}
