package com.disaster.stormsurge.controller;

import com.disaster.stormsurge.client.FastApiClient;
import com.disaster.stormsurge.dto.FastApiDto.HealthResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
public class HealthController {

    private final FastApiClient fastApiClient;

    public HealthController(FastApiClient fastApiClient) {
        this.fastApiClient = fastApiClient;
    }

    @GetMapping("/api/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> map = new HashMap<>();
        map.put("status", "UP");
        map.put("service", "Storm Surge Spring Boot Backend");
        map.put("version", "1.0.0");

        fastApiClient.checkHealth().ifPresentOrElse(
                h -> map.put("fastapi_model_server", h),
                () -> map.put("fastapi_model_server", Map.of("status", "DOWN", "fallback_active", true))
        );

        return ResponseEntity.ok(map);
    }
}
