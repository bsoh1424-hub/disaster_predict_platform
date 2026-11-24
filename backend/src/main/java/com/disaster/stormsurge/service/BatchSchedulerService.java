package com.disaster.stormsurge.service;

import com.disaster.stormsurge.client.FastApiClient;
import com.disaster.stormsurge.entity.Station;
import com.disaster.stormsurge.repository.StationRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@EnableScheduling
public class BatchSchedulerService {

    private static final Logger log = LoggerFactory.getLogger(BatchSchedulerService.class);

    private final StationRepository stationRepository;
    private final ForecastService forecastService;
    private final FastApiClient fastApiClient;

    public BatchSchedulerService(StationRepository stationRepository, ForecastService forecastService, FastApiClient fastApiClient) {
        this.stationRepository = stationRepository;
        this.forecastService = forecastService;
        this.fastApiClient = fastApiClient;
    }

    /**
     * 아키텍처 A1 & 7장 서빙 설계:
     * 매시간 정시(0분 0초)에 자동 배치 예측 실행
     */
    @Scheduled(cron = "0 0 * * * *")
    public void runHourlyBatch() {
        log.info("Starting hourly storm surge batch prediction...");
        runBatchInternal("BATCH");
    }

    public void runBatchNow() {
        log.info("Triggering manual batch prediction run...");
        runBatchInternal("BATCH");
    }

    private void runBatchInternal(String runType) {
        List<Station> stations = stationRepository.findByActiveTrue();
        log.info("Found {} active stations for batch execution", stations.size());

        for (Station s : stations) {
            try {
                // 1. 수집 모듈 트리거 (FastAPI 수집 모듈에 비동기 수집 요청)
                fastApiClient.triggerCollection(s.getStationCode());

                // 2. 예측 및 환산/저장
                forecastService.executeAndSavePrediction(s.getStationCode(), runType, "batch-scheduler");
            } catch (Exception e) {
                log.error("Batch prediction failed for station {}: {}", s.getStationCode(), e.getMessage());
            }
        }
        log.info("Completed storm surge batch execution.");
    }
}
