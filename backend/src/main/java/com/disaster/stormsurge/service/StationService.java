package com.disaster.stormsurge.service;

import com.disaster.stormsurge.dto.StationDto.*;
import com.disaster.stormsurge.entity.*;
import com.disaster.stormsurge.repository.*;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class StationService {

    private final StationRepository stationRepository;
    private final StationThresholdRepository thresholdRepository;
    private final PredictionRunRepository runRepository;
    private final PredictionResultRepository resultRepository;
    private final TideObservationRepository observationRepository;

    public StationService(
            StationRepository stationRepository,
            StationThresholdRepository thresholdRepository,
            PredictionRunRepository runRepository,
            PredictionResultRepository resultRepository,
            TideObservationRepository observationRepository) {
        this.stationRepository = stationRepository;
        this.thresholdRepository = thresholdRepository;
        this.runRepository = runRepository;
        this.resultRepository = resultRepository;
        this.observationRepository = observationRepository;
    }

    public List<StationSummary> getAllStationSummaries() {
        List<Station> stations = stationRepository.findAll();
        Optional<PredictionRun> latestRun = runRepository.findTopByOrderByExecutedAtDesc();

        List<StationSummary> list = new ArrayList<>();
        for (Station s : stations) {
            StationThreshold th = thresholdRepository.findByStationCode(s.getStationCode()).orElse(null);
            Double advisory = th != null ? th.getAdvisoryCm() : 200.0;
            Double warning = th != null ? th.getWarningCm() : 250.0;

            // 최신 관측값 (실시간 현황) — 실측이 있는 행만 (오늘·미래 시간 행은 실측이 비어 있어 제외). 없으면 null (기본값을 넣지 않음)
            Optional<TideObservation> latestObs = observationRepository.findTopByStationCodeAndTideObsCmIsNotNullOrderByObsTimeDesc(s.getStationCode());
            Double obsTide = latestObs.map(TideObservation::getTideObsCm).orElse(null);
            LocalDateTime obsTime = latestObs.map(TideObservation::getObsTime).orElse(null);

            // 12시간 뒤 예측 총수위 — 없으면 null (가짜 120.0 기본값 제거)
            PredictionResult pred = resultRepository
                    .findTopByStationCodeAndLeadHourOrderByRunIdDesc(s.getStationCode(), 12)
                    .orElse(null);
            Double totalTide = pred != null ? pred.getTotalTideCm() : null;

            // 경보 판정은 현재 관측 수위 기준 (실시간 상황판). 관측 없으면 NORMAL.
            String alertLevel = "NORMAL";
            boolean isExceeded = false;
            if (obsTide != null) {
                if (obsTide >= warning) {
                    alertLevel = "WARNING";
                    isExceeded = true;
                } else if (obsTide >= advisory) {
                    alertLevel = "ADVISORY";
                    isExceeded = true;
                }
            }

            LocalDateTime updated = obsTime != null ? obsTime
                    : latestRun.map(PredictionRun::getExecutedAt).orElse(LocalDateTime.now());

            list.add(new StationSummary(
                    s.getStationCode(),
                    s.getName(),
                    s.getLatitude(),
                    s.getLongitude(),
                    s.getSeaRegion(),
                    totalTide,
                    obsTide,
                    obsTime,
                    advisory,
                    warning,
                    alertLevel,
                    isExceeded,
                    updated
            ));
        }

        return list;
    }

    public StationDetail getStationDetail(String stationCode) {
        Station s = stationRepository.findById(stationCode)
                .orElseThrow(() -> new IllegalArgumentException("관측소를 찾을 수 없습니다: " + stationCode));
        StationThreshold th = thresholdRepository.findByStationCode(stationCode).orElse(null);

        return new StationDetail(
                s.getStationCode(),
                s.getName(),
                s.getLatitude(),
                s.getLongitude(),
                s.getSeaRegion(),
                th != null ? th.getAdvisoryCm() : 0.0,
                th != null ? th.getWarningCm() : 0.0,
                th != null ? th.getLocalFloodCm() : 0.0,
                s.getDescription()
        );
    }
}
