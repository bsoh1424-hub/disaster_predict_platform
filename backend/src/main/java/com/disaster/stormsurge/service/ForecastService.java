package com.disaster.stormsurge.service;

import com.disaster.stormsurge.client.FastApiClient;
import com.disaster.stormsurge.dto.FastApiDto.*;
import com.disaster.stormsurge.dto.ForecastDto.*;
import com.disaster.stormsurge.entity.*;
import com.disaster.stormsurge.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class ForecastService {

    private static final Logger log = LoggerFactory.getLogger(ForecastService.class);

    private final StationRepository stationRepository;
    private final StationThresholdRepository thresholdRepository;
    private final PredictionRunRepository runRepository;
    private final PredictionResultRepository resultRepository;
    private final TideObservationRepository observationRepository;
    private final ForecastFeatureRepository featureRepository;
    private final FastApiClient fastApiClient;

    public ForecastService(
            StationRepository stationRepository,
            StationThresholdRepository thresholdRepository,
            PredictionRunRepository runRepository,
            PredictionResultRepository resultRepository,
            TideObservationRepository observationRepository,
            ForecastFeatureRepository featureRepository,
            FastApiClient fastApiClient) {
        this.stationRepository = stationRepository;
        this.thresholdRepository = thresholdRepository;
        this.runRepository = runRepository;
        this.resultRepository = resultRepository;
        this.observationRepository = observationRepository;
        this.featureRepository = featureRepository;
        this.fastApiClient = fastApiClient;
    }

    public ForecastResponse getLatestForecast(String stationCode) {
        Station station = stationRepository.findById(stationCode)
                .orElseThrow(() -> new IllegalArgumentException("관측소를 찾을 수 없습니다: " + stationCode));

        StationThreshold threshold = thresholdRepository.findByStationCode(stationCode).orElse(null);
        Double advisory = threshold != null ? threshold.getAdvisoryCm() : 200.0;
        Double warning = threshold != null ? threshold.getWarningCm() : 250.0;
        Double flood = threshold != null ? threshold.getLocalFloodCm() : advisory - 10.0;

        // 최신 배치 또는 실시간 실행 조회
        Optional<PredictionRun> latestRunOpt = runRepository.findTopByOrderByExecutedAtDesc();
        if (latestRunOpt.isEmpty()) {
            // 실행 이력이 없으면 임시 계산 실행
            return executeAndSavePrediction(stationCode, "BATCH", "system");
        }

        PredictionRun run = latestRunOpt.get();
        List<PredictionResult> results = resultRepository.findByRunIdAndStationCodeOrderByLeadHourAsc(run.getRunId(), stationCode);

        if (results.isEmpty()) {
            return executeAndSavePrediction(stationCode, "BATCH", "system");
        }

        List<ForecastPoint> points = new ArrayList<>();
        double maxTotalTide = 0.0;
        String maxTideTime = "";
        double maxResidual = 0.0;
        String maxResidualTime = "";
        boolean overlapFound = false;

        for (PredictionResult r : results) {
            String targetTimeStr = r.getTargetTime().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
            points.add(new ForecastPoint(
                    r.getLeadHour(),
                    targetTimeStr,
                    r.getAstronomicalTideCm(),
                    r.getResidualCm(),
                    r.getTotalTideCm(),
                    r.getExceedProbability(),
                    r.getIsExceeded(),
                    r.getAlertLevel(),
                    r.getIsTideOverlap()
            ));

            if (r.getTotalTideCm() > maxTotalTide) {
                maxTotalTide = r.getTotalTideCm();
                maxTideTime = targetTimeStr;
            }
            if (r.getResidualCm() > maxResidual) {
                maxResidual = r.getResidualCm();
                maxResidualTime = targetTimeStr;
            }
            if (Boolean.TRUE.equals(r.getIsTideOverlap())) {
                overlapFound = true;
            }
        }

        boolean isFallback = "FALLBACK".equals(run.getStatus());
        String reasonSummary = results.getFirst().getReasonText();

        TideSummary tideSummary = new TideSummary(
                maxTotalTide,
                maxTideTime,
                maxResidual,
                maxResidualTime,
                overlapFound,
                overlapFound ? "만조 전후 2시간 집중 위험" : "만조 분리 안전"
        );

        String officialStatus = maxTotalTide >= warning ? "폭풍해일경보" : (maxTotalTide >= advisory ? "폭풍해일주의보" : "발령 없음");
        OfficialWarning officialWarning = new OfficialWarning(
                officialStatus,
                "국립해양조사원 및 기상청 현업 수치예보(RTSM/CTSM)와 연계된 참고 경보입니다. 공식 특보 발표 시 우선 적용하십시오.",
                true
        );

        return new ForecastResponse(
                station.getStationCode(),
                station.getName(),
                run.getExecutedAt().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                run.getRunId(),
                run.getRunType(),
                run.getModelVersion(),
                isFallback,
                advisory,
                warning,
                flood,
                points,
                reasonSummary,
                tideSummary,
                officialWarning
        );
    }

    @Transactional
    public ForecastResponse recalculate(String stationCode, String username) {
        log.info("Executing real-time recalculation for station {} by user {}", stationCode, username);
        return executeAndSavePrediction(stationCode, "REALTIME", username);
    }

    @Transactional
    public ForecastResponse executeAndSavePrediction(String stationCode, String runType, String username) {
        Station station = stationRepository.findById(stationCode)
                .orElseThrow(() -> new IllegalArgumentException("관측소를 찾을 수 없습니다: " + stationCode));

        StationThreshold threshold = thresholdRepository.findByStationCode(stationCode).orElse(null);
        Double advisory = threshold != null ? threshold.getAdvisoryCm() : 200.0;
        Double warning = threshold != null ? threshold.getWarningCm() : 250.0;
        Double flood = threshold != null ? threshold.getLocalFloodCm() : advisory - 10.0;

        LocalDateTime now = LocalDateTime.now();
        String baseTimeStr = now.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME) + "+09:00";

        // 최근 관측값 및 예보 피처 추출
        Optional<TideObservation> latestObs = observationRepository.findTopByStationCodeOrderByObsTimeDesc(stationCode);
        Optional<ForecastFeature> latestFcst = featureRepository.findTopByStationCodeOrderByForecastTimeDesc(stationCode);

        Map<String, Object> features = new HashMap<>();
        features.put("current_pressure", latestObs.map(TideObservation::getAirPressureHpa).orElse(1008.5));
        features.put("pressure_drop_3h", 2.1);
        features.put("wind_speed", latestObs.map(TideObservation::getWindSpeedMs).orElse(14.5));
        features.put("wind_dir", latestObs.map(TideObservation::getWindDirDeg).orElse(185.0));
        features.put("past_residual", latestObs.map(TideObservation::getResidualCm).orElse(15.0));
        features.put("forecast_pressure_12h", latestFcst.map(ForecastFeature::getForecastPressure12h).orElse(992.0));
        features.put("forecast_pressure_24h", latestFcst.map(ForecastFeature::getForecastPressure24h).orElse(998.0));
        features.put("forecast_wind_12h", latestFcst.map(ForecastFeature::getForecastWind12h).orElse(21.0));
        features.put("forecast_wind_24h", latestFcst.map(ForecastFeature::getForecastWind24h).orElse(16.0));

        // 천문조 기준값 (관측소 위치 특성에 따른 12h, 24h 조위 모사)
        double baseAstro12h = getEstimatedAstroTide(stationCode, 12);
        double baseAstro24h = getEstimatedAstroTide(stationCode, 24);

        // FastAPI 추론 호출
        Optional<PredictResponse> predictOpt = fastApiClient.predict(stationCode, baseTimeStr, features);

        boolean isFallback = predictOpt.isEmpty();
        String modelVersion = predictOpt.map(PredictResponse::model_version).orElse("baseline_astronomical_only");
        String runStatus = isFallback ? "FALLBACK" : "SUCCESS";

        PredictionRun run = new PredictionRun(runType, now, modelVersion, runStatus, username);
        runRepository.save(run);

        List<PredictionResult> resultsToSave = new ArrayList<>();
        List<ForecastPoint> points = new ArrayList<>();

        if (isFallback) {
            // 천문조 베이스라인 폴백 (잔차 = 0.0)
            log.warn("FastAPI failure: Falling back to astronomical tide baseline for {}", stationCode);
            PredictionResult res12 = createResult(run.getRunId(), stationCode, 12, now.plusHours(12),
                    baseAstro12h, 0.0, 0.05, advisory, warning, "FastAPI 연결 장애로 인해 천문조 기준 베이스라인(잔차 0)으로 산출된 임시 예보입니다.");
            PredictionResult res24 = createResult(run.getRunId(), stationCode, 24, now.plusHours(24),
                    baseAstro24h, 0.0, 0.05, advisory, warning, "FastAPI 연결 장애로 인해 천문조 기준 베이스라인(잔차 0)으로 산출된 임시 예보입니다.");
            resultsToSave.add(res12);
            resultsToSave.add(res24);
        } else {
            PredictResponse pred = predictOpt.get();
            for (PredictionItem item : pred.predictions()) {
                LocalDateTime targetTime = now.plusHours(item.lead_hour()).truncatedTo(ChronoUnit.HOURS);
                // 목표 시각의 실제 KHOA 천문조를 DB에서 조회 (행이 없으면 기존 추정값으로 폴백)
                double astro = observationRepository.findByStationCodeAndObsTime(stationCode, targetTime)
                        .map(TideObservation::getTidePredCm)
                        .filter(v -> v != null)
                        .orElseGet(() -> getEstimatedAstroTide(stationCode, item.lead_hour()));
                double residual = item.residual_cm();
                double prob = item.exceed_probability();

                String reason = String.format("기압 역효과(+%.1fcm) 및 풍속 밀어올림(+%.1fcm) 작용. 예측 시각 만조 구간 근접.",
                        Math.max(0.0, (1013.25 - (double)features.get("forecast_pressure_12h")) * 1.0),
                        Math.pow((double)features.get("forecast_wind_12h"), 1.8) * 0.07);

                PredictionResult res = createResult(run.getRunId(), stationCode, item.lead_hour(), targetTime,
                        astro, residual, prob, advisory, warning, reason);
                resultsToSave.add(res);
            }
        }

        resultRepository.saveAll(resultsToSave);

        for (PredictionResult r : resultsToSave) {
            points.add(new ForecastPoint(
                    r.getLeadHour(),
                    r.getTargetTime().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                    r.getAstronomicalTideCm(),
                    r.getResidualCm(),
                    r.getTotalTideCm(),
                    r.getExceedProbability(),
                    r.getIsExceeded(),
                    r.getAlertLevel(),
                    r.getIsTideOverlap()
            ));
        }

        double maxTotalTide = resultsToSave.stream().mapToDouble(PredictionResult::getTotalTideCm).max().orElse(0.0);
        double maxResidual = resultsToSave.stream().mapToDouble(PredictionResult::getResidualCm).max().orElse(0.0);

        TideSummary tideSummary = new TideSummary(
                maxTotalTide,
                points.getFirst().targetTime(),
                maxResidual,
                points.getFirst().targetTime(),
                true,
                "만조 전후 2시간 주의"
        );

        String officialStatus = maxTotalTide >= warning ? "폭풍해일경보" : (maxTotalTide >= advisory ? "폭풍해일주의보" : "발령 없음");
        OfficialWarning officialWarning = new OfficialWarning(
                officialStatus,
                "국립해양조사원 및 기상청 현업 수치예보(RTSM/CTSM)와 연계된 참고 경보입니다.",
                true
        );

        return new ForecastResponse(
                station.getStationCode(),
                station.getName(),
                now.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                run.getRunId(),
                run.getRunType(),
                modelVersion,
                isFallback,
                advisory,
                warning,
                flood,
                points,
                resultsToSave.getFirst().getReasonText(),
                tideSummary,
                officialWarning
        );
    }

    private PredictionResult createResult(Long runId, String stationCode, int leadHour, LocalDateTime targetTime,
                                         double astroTide, double residual, double prob, double advisory, double warning, String reason) {
        PredictionResult r = new PredictionResult();
        r.setRunId(runId);
        r.setStationCode(stationCode);
        r.setLeadHour(leadHour);
        r.setTargetTime(targetTime);
        r.setAstronomicalTideCm(astroTide);
        r.setResidualCm(residual);
        
        // PRD 핵심 환산 규칙: 총 수위 = 천문조 예측조위 + 예측 잔차
        double totalTide = Math.round((astroTide + residual) * 10.0) / 10.0;
        r.setTotalTideCm(totalTide);
        r.setExceedProbability(prob);

        String alertLevel = "NORMAL";
        boolean isExceeded = false;
        if (totalTide >= warning) {
            alertLevel = "WARNING";
            isExceeded = true;
        } else if (totalTide >= advisory) {
            alertLevel = "ADVISORY";
            isExceeded = true;
        }
        r.setAlertLevel(alertLevel);
        r.setIsExceeded(isExceeded);
        r.setIsTideOverlap(leadHour == 12); // 12시간 후 만조 시점과 일치 가정
        r.setReasonText(reason);
        return r;
    }

    private double getEstimatedAstroTide(String stationCode, int leadHour) {
        // 지역별 조차 특성 반영
        // 서해안(인천, 평택, 보령, 군산): 대조차 600~950cm
        // 남서해/남해(목포, 여수, 통영): 350~500cm
        // 남해/동해남부(부산, 울산, 포항): 90~180cm
        return switch (stationCode) {
            case "INCHEON" -> leadHour == 12 ? 940.0 : 420.0;
            case "PYEONGTAEK" -> leadHour == 12 ? 980.0 : 450.0;
            case "BORYEONG" -> leadHour == 12 ? 720.0 : 310.0;
            case "GUNSAN" -> leadHour == 12 ? 680.0 : 280.0;
            case "MOKPO" -> leadHour == 12 ? 505.0 : 230.0;
            case "YEOSU" -> leadHour == 12 ? 395.0 : 180.0;
            case "TONGYEONG" -> leadHour == 12 ? 260.0 : 110.0;
            case "BUSAN" -> leadHour == 12 ? 165.0 : 60.0;
            case "ULSAN" -> leadHour == 12 ? 105.0 : 40.0;
            case "POHANG" -> leadHour == 12 ? 92.0 : 35.0;
            case "JEJU" -> leadHour == 12 ? 245.0 : 90.0;
            default -> leadHour == 12 ? 150.0 : 50.0;
        };
    }

    public ObservationResponse getObservations(String stationCode) {
        Station station = stationRepository.findById(stationCode)
                .orElseThrow(() -> new IllegalArgumentException("관측소를 찾을 수 없습니다: " + stationCode));

        LocalDateTime now = LocalDateTime.now();
        List<TideObservation> list = observationRepository.findByStationCodeAndObsTimeBetweenOrderByObsTimeAsc(
                stationCode, now.minusHours(24), now
        );

        List<ObservationPoint> points = new ArrayList<>();
        for (TideObservation o : list) {
            points.add(new ObservationPoint(
                    o.getObsTime().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                    o.getTideObsCm(),
                    o.getTidePredCm(),
                    o.getResidualCm(),
                    o.getAirPressureHpa(),
                    o.getWindSpeedMs(),
                    o.getWindDirDeg()
            ));
        }

        return new ObservationResponse(station.getStationCode(), station.getName(), points);
    }
}
