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

    /**
     * 최신 데이터 새로고침 (대시보드 "최신 데이터" 버튼용).
     * KHOA 조위 + KMA 부이 데이터를 전 관측소에 대해 다시 받아온다.
     * 수집은 FastAPI 백그라운드에서 진행되므로 즉시 돌아온다.
     * 1~2분 뒤 화면을 새로고침하면 반영된 데이터를 볼 수 있다.
     */
    @PostMapping("/data/refresh")
    public ResponseEntity<String> refreshData() {
        batchSchedulerService.refreshDataNow();
        return ResponseEntity.ok("Data refresh started for all stations.");
    }
}
