package com.disaster.stormsurge.service;

import com.disaster.stormsurge.client.FastApiClient;
import com.disaster.stormsurge.dto.FastApiDto.*;
import com.disaster.stormsurge.dto.ForecastDto.ForecastResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class RagService {

    private static final Logger log = LoggerFactory.getLogger(RagService.class);

    private final FastApiClient fastApiClient;
    private final ForecastService forecastService;

    public RagService(FastApiClient fastApiClient, ForecastService forecastService) {
        this.fastApiClient = fastApiClient;
        this.forecastService = forecastService;
    }

    public RagResponse askDisasterAssistant(String query, String stationCode) {
        Map<String, Object> contextInfo = new HashMap<>();
        if (stationCode != null && !stationCode.isBlank()) {
            try {
                ForecastResponse fcst = forecastService.getLatestForecast(stationCode);
                contextInfo.put("station_name", fcst.stationName());
                contextInfo.put("total_tide", fcst.tideSummary().maxTotalTideCm());
                contextInfo.put("is_exceeded", fcst.points().stream().anyMatch(p -> Boolean.TRUE.equals(p.isExceeded())));
                contextInfo.put("tide_overlap", fcst.tideSummary().highTideOverlap() ? "만조 겹침 위험" : "만조 미겹침");
            } catch (Exception e) {
                log.warn("Failed to inject forecast context into RAG query: {}", e.getMessage());
            }
        }

        Optional<RagResponse> responseOpt = fastApiClient.queryRag(query, contextInfo);

        if (responseOpt.isPresent()) {
            return responseOpt.get();
        }

        // FastAPI RAG 서비스 연결 불가 시 Spring Boot 자체 룰베이스 Fallback 응답
        return new RagResponse(
                query,
                "현재 FastAPI 방재 RAG 엔진 연결이 지연되고 있어 기본 가이드로 응답합니다:\n" +
                "1. 폭풍해일 특보 및 침수 판단은 잔차가 아닌 [천문조 + 잔차 = 총 수위]를 기준으로 발령됩니다.\n" +
                "2. 만조 시간대와 강풍/기압급강하가 겹칠 경우 저지대 배수문 가동 및 방파제 출입 통제가 최우선입니다.\n" +
                "3. 관측소별 공식 주의보/경보 수위 초과 여부를 대시보드에서 반드시 교차 확인하십시오.",
                List.of("행정안전부 폭풍해일 국민행동요령", "국립해양조사원 조석 기준표"),
                "SpringBoot-Rulebase-Fallback"
        );
    }
}
