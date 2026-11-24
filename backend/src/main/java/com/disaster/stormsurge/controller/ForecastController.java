package com.disaster.stormsurge.controller;

import com.disaster.stormsurge.dto.ForecastDto.*;
import com.disaster.stormsurge.service.BatchSchedulerService;
import com.disaster.stormsurge.service.ForecastService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class ForecastController {

    private final ForecastService forecastService;
    private final BatchSchedulerService batchSchedulerService;

    public ForecastController(ForecastService forecastService, BatchSchedulerService batchSchedulerService) {
        this.forecastService = forecastService;
        this.batchSchedulerService = batchSchedulerService;
    }

    /**
     * 아키텍처 11장: GET /api/stations/{id}/forecast
     * 최신 배치 기준 총 수위 곡선, 12h/24h, 임계 초과 여부와 시각 (Q7)
     */
    @GetMapping("/stations/{id}/forecast")
    public ResponseEntity<ForecastResponse> getForecast(@PathVariable("id") String stationCode) {
        return ResponseEntity.ok(forecastService.getLatestForecast(stationCode));
    }

    /**
     * 아키텍처 11장: GET /api/stations/{id}/observations
     * 실측, 천문조, 잔차 곡선 - 근거 설명용
     */
    @GetMapping("/stations/{id}/observations")
    public ResponseEntity<ObservationResponse> getObservations(@PathVariable("id") String stationCode) {
        return ResponseEntity.ok(forecastService.getObservations(stationCode));
    }

    /**
     * 아키텍처 11장: POST /api/stations/{id}/recalculate
     * 실시간 재계산 요청 (A1). REALTIME 실행을 만들고 결과를 반환
     */
    @PostMapping("/stations/{id}/recalculate")
    public ResponseEntity<ForecastResponse> recalculate(
            @PathVariable("id") String stationCode,
            Authentication authentication) {
        String username = authentication != null ? authentication.getName() : "anonymous";
        return ResponseEntity.ok(forecastService.recalculate(stationCode, username));
    }

    /**
     * 관리자 수동 전체 배치 트리거
     */
    @PostMapping("/batch/run")
    public ResponseEntity<String> triggerBatch() {
        batchSchedulerService.runBatchNow();
        return ResponseEntity.ok("Hourly batch prediction triggered successfully.");
    }
}
