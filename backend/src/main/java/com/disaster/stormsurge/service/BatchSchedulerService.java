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

    /**
     * 수동 데이터 새로고침 (대시보드 "최신 데이터" 버튼용).
     * FastAPI 수집 모듈에 전 관측소 수집을 요청한다. FastAPI는 백그라운드에서
     * KHOA 조위 + KMA 부이 데이터를 받아 DB에 적재하므로, 이 메서드는
     * 트리거만 하고 바로 돌아온다. 실제 적재 완료는 FastAPI 로그로 확인한다.
     */
    public void refreshDataNow() {
        List<Station> stations = stationRepository.findByActiveTrue();
        log.info("Manual data refresh requested for {} stations", stations.size());
        int triggered = 0;
        for (Station s : stations) {
            try {
                if (fastApiClient.triggerCollection(s.getStationCode())) {
                    triggered++;
                }
            } catch (Exception e) {
                log.error("Data refresh trigger failed for station {}: {}", s.getStationCode(), e.getMessage());
            }
        }
        log.info("Data refresh triggered for {}/{} stations.", triggered, stations.size());
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
