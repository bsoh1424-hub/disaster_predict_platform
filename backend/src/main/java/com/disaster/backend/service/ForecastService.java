package com.disaster.backend.service;

import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Map;

@Service
public class ForecastService {

    private final RestClient restClient = RestClient.builder()
            .baseUrl("http://127.0.0.1:8000")
            .build();

    public Map<String, Object> getForecast(String beach) {
        // 1. FastAPI에 물어보기
        // 2. 위험도 계산하기
        // 3. DB에 저장하기 (나중에)
        // 4. 결과 돌려주기
        return restClient.post()
                .uri("/predict/flood")
                .body(Map.of("beach", beach, "hours_ahead", 48,
                        "tide_cm", 120.0, "wave_m", 2.0, "wind_ms", 8.0))
                .retrieve()
                .body(Map.class);
    }
}
