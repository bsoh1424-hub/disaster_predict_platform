package com.disaster.stormsurge.service;

import com.disaster.stormsurge.entity.*;
import com.disaster.stormsurge.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class DataInitService implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitService.class);

    private final UserRepository userRepository;
    private final StationRepository stationRepository;
    private final StationThresholdRepository thresholdRepository;
    private final TideObservationRepository observationRepository;
    private final ForecastFeatureRepository featureRepository;
    private final TyphoonCaseRepository caseRepository;
    private final EvaluationResultRepository evaluationRepository;
    private final ModelRegistryRepository modelRepository;
    private final PasswordEncoder passwordEncoder;
    private final ForecastService forecastService;

    public DataInitService(
            UserRepository userRepository,
            StationRepository stationRepository,
            StationThresholdRepository thresholdRepository,
            TideObservationRepository observationRepository,
            ForecastFeatureRepository featureRepository,
            TyphoonCaseRepository caseRepository,
            EvaluationResultRepository evaluationRepository,
            ModelRegistryRepository modelRepository,
            PasswordEncoder passwordEncoder,
            ForecastService forecastService) {
        this.userRepository = userRepository;
        this.stationRepository = stationRepository;
        this.thresholdRepository = thresholdRepository;
        this.observationRepository = observationRepository;
        this.featureRepository = featureRepository;
        this.caseRepository = caseRepository;
        this.evaluationRepository = evaluationRepository;
        this.modelRepository = modelRepository;
        this.passwordEncoder = passwordEncoder;
        this.forecastService = forecastService;
    }

    @Override
    @Transactional
    public void run(String... args) {
        log.info("Initializing Storm Surge Platform default dataset...");

        // 1. 기본 관리자 및 사용자 생성
        if (!userRepository.existsByUsername("admin")) {
            userRepository.save(new User("admin", passwordEncoder.encode("admin123"), "재난상황실 관리자", "해양방재과", "ROLE_ADMIN"));
            userRepository.save(new User("user", passwordEncoder.encode("user123"), "어항관리 담당자", "수산항만과", "ROLE_USER"));
            log.info("Default users initialized: admin / user");
        }

        // 2. 전국 10개소 이상 조위관측소 마스터 (PRD Q2 및 아키텍처 6장)
        if (stationRepository.count() == 0) {
            List<Station> stations = List.of(
                    new Station("BUSAN", "부산", 35.0931, 129.0345, "남해", true, "부산항 남외항 및 북항 조위 관측"),
                    new Station("INCHEON", "인천", 37.4520, 126.5920, "서해", true, "인천항 및 연안부두 조위 관측 (서해 대조차)"),
                    new Station("PYEONGTAEK", "평택", 36.9530, 126.8320, "서해", true, "평택·당진항 외항 조위 관측"),
                    new Station("MOKPO", "목포", 34.7830, 126.3750, "서해", true, "목포항 및 영산강 하구언 조위 관측"),
                    new Station("YEOSU", "여수", 34.7470, 127.7660, "남해", true, "여수 신항 및 광양만 입구 조위 관측"),
                    new Station("ULSAN", "울산", 35.5010, 129.3850, "동해", true, "울산항 및 장생포 연안 조위 관측"),
                    new Station("POHANG", "포항", 36.0500, 129.3800, "동해", true, "포항 구항 및 영일만 연안 조위 관측"),
                    new Station("BORYEONG", "보령", 36.3260, 126.5050, "서해", true, "대천항 및 천수만 입구 조위 관측"),
                    new Station("GUNSAN", "군산", 35.9750, 126.5650, "서해", true, "군산 내항 및 금강 하구 조위 관측"),
                    new Station("JEJU", "제주", 33.5280, 126.5430, "제주", true, "제주항 탑동 연안 조위 관측")
            );
            stationRepository.saveAll(stations);

            // 관측소별 임계값 (PRD 4장 별표 13 수치 반영)
            List<StationThreshold> thresholds = List.of(
                    new StationThreshold("BUSAN", 183.0, 214.0, 175.0, "남해안 대표 (주의보 183, 경보 214)"),
                    new StationThreshold("INCHEON", 966.0, 1004.0, 950.0, "서해 대조차 (주의보 966, 경보 1004)"),
                    new StationThreshold("PYEONGTAEK", 1010.0, 1030.0, 990.0, "서해 대조차 (주의보 1010, 경보 1030)"),
                    new StationThreshold("MOKPO", 522.0, 544.0, 510.0, "남서해 (주의보 522, 경보 544)"),
                    new StationThreshold("YEOSU", 420.0, 440.0, 410.0, "남해 (주의보 420, 경보 440)"),
                    new StationThreshold("ULSAN", 120.0, 170.0, 110.0, "동해 (주의보 120, 경보 170)"),
                    new StationThreshold("POHANG", 109.0, 150.0, 100.0, "동해 (주의보 109, 경보 150)"),
                    new StationThreshold("BORYEONG", 780.0, 830.0, 760.0, "서해 중부"),
                    new StationThreshold("GUNSAN", 740.0, 790.0, 720.0, "서해 중부"),
                    new StationThreshold("JEJU", 280.0, 310.0, 270.0, "제주 해역")
            );
            thresholdRepository.saveAll(thresholds);
            log.info("10 stations and thresholds initialized");
        }

        // 3. 태풍 사례 및 평가 결과 (PRD Q6, Q5)
        if (caseRepository.count() == 0) {
            List<TyphoonCase> cases = List.of(
                    new TyphoonCase("MAEMI_2003", "태풍 매미 (MAEMI 0314)", 2003, "2003-09-11 ~ 2003-09-13",
                            212.0, "BUSAN, YEOSU, TONGYEONG", "2003년 9월 남해안을 강타한 역대 최강 폭풍해일. 마산·부산 해일 침수 피해 극심."),
                    new TyphoonCase("CHABA_2016", "태풍 차바 (CHABA 1618)", 2016, "2016-10-04 ~ 2016-10-06",
                            138.0, "BUSAN, ULSAN, JEJU", "부산 마린시티 월파 침수 및 울산 태화강 범람을 유발한 가을 태풍."),
                    new TyphoonCase("HINNAMNOR_2022", "태풍 힌남노 (HINNAMNOR 2211)", 2022, "2022-09-05 ~ 2022-09-07",
                            145.0, "POHANG, BUSAN, ULSAN", "포항 및 동해남부 해역에 기록적 파고와 조위 상승을 초래한 초대형 태풍.")
            );
            caseRepository.saveAll(cases);

            List<EvaluationResult> evals = List.of(
                    // 매미 평가
                    createEval("MAEMI_2003", "BUSAN", 12, 6.2, 0.4, 0.94, 38.5, 14.8),
                    createEval("MAEMI_2003", "BUSAN", 24, 11.8, 0.8, 0.89, 44.2, 21.3),
                    createEval("MAEMI_2003", "YEOSU", 12, 7.8, 0.5, 0.91, 35.0, 16.5),
                    // 차바 평가
                    createEval("CHABA_2016", "BUSAN", 12, 5.4, 0.2, 0.96, 29.8, 12.1),
                    createEval("CHABA_2016", "ULSAN", 12, 8.1, 0.6, 0.88, 32.4, 15.6),
                    // 힌남노 평가
                    createEval("HINNAMNOR_2022", "POHANG", 12, 7.1, 0.3, 0.93, 31.0, 13.9),
                    createEval("HINNAMNOR_2022", "BUSAN", 12, 6.0, 0.4, 0.95, 28.5, 11.4)
            );
            evaluationRepository.saveAll(evals);
            log.info("Typhoon cases and evaluation benchmark data initialized");
        }

        // 4. 모델 레지스트리 메타 등록 (아키텍처 10장)
        if (modelRepository.count() == 0) {
            ModelRegistry model = new ModelRegistry();
            model.setVersion("surge_v1.0.0_2026-11-20");
            model.setCreatedAt(LocalDateTime.now().minusDays(3));
            model.setTrainPeriod("2015-01-01 ~ 2025-12-31");
            model.setStations("BUSAN, INCHEON, PYEONGTAEK, MOKPO, YEOSU, ULSAN, POHANG, BORYEONG, GUNSAN, JEJU");
            model.setDataSnapshot("KHOA Tide & KMA Numerical Forecast 10yr archive");
            model.setIsActive(true);
            model.setMetaJson("{\"framework\": \"hybrid_physics_ml\", \"lead_hours\": [12, 24]}");
            modelRepository.save(model);
        }

        // 5. 초기 관측값 및 예보 피처 Seeding (시뮬레이션용)
        LocalDateTime now = LocalDateTime.now();
        if (observationRepository.count() == 0) {
            for (int h = 24; h >= 0; h--) {
                LocalDateTime t = now.minusHours(h);
                TideObservation obs = new TideObservation();
                obs.setStationCode("BUSAN");
                obs.setObsTime(t);
                obs.setTideObsCm(145.0 + Math.sin(h * 0.5) * 40.0);
                obs.setTidePredCm(115.0 + Math.sin(h * 0.5) * 40.0);
                obs.setResidualCm(30.0);
                obs.setAirPressureHpa(1002.0 - (24 - h) * 0.4);
                obs.setWindSpeedMs(12.0 + (24 - h) * 0.3);
                obs.setWindDirDeg(180.0);
                observationRepository.save(obs);
            }

            ForecastFeature feat = new ForecastFeature();
            feat.setStationCode("BUSAN");
            feat.setForecastTime(now);
            feat.setForecastPressure12h(985.0);
            feat.setForecastPressure24h(995.0);
            feat.setForecastWind12h(22.0);
            feat.setForecastWind24h(15.0);
            featureRepository.save(feat);
        }

        // 6. 초기 예측 실행 1회 수행
        try {
            forecastService.executeAndSavePrediction("BUSAN", "BATCH", "system-init");
            log.info("Initial prediction run generated successfully");
        } catch (Exception e) {
            log.warn("Initial prediction generation deferred: {}", e.getMessage());
        }
    }

    private EvaluationResult createEval(String caseId, String stationCode, int lead, double peakErr, double timeErr, double f1, double astroErr, double rtsmErr) {
        EvaluationResult e = new EvaluationResult();
        e.setCaseId(caseId);
        e.setStationCode(stationCode);
        e.setLeadHour(lead);
        e.setPeakErrorCm(peakErr);
        e.setPeakTimeErrorHours(timeErr);
        e.setExceedF1(f1);
        e.setBaselineAstroErrorCm(astroErr);
        e.setBaselineRtsmErrorCm(rtsmErr);
        return e;
    }
}
