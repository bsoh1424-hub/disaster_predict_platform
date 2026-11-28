package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.TideObservation;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface TideObservationRepository extends JpaRepository<TideObservation, Long> {
    List<TideObservation> findByStationCodeAndObsTimeBetweenOrderByObsTimeAsc(
        String stationCode, LocalDateTime start, LocalDateTime end
    );

    Optional<TideObservation> findTopByStationCodeOrderByObsTimeDesc(String stationCode);

    // 실측값이 있는 최신 관측 (오늘·미래 시간 행은 실측이 비어 있어 제외)
    Optional<TideObservation> findTopByStationCodeAndTideObsCmIsNotNullOrderByObsTimeDesc(String stationCode);

    // 목표 시각의 천문조 예측값 조회 (미래 시간 행도 예측값이 있음)
    Optional<TideObservation> findByStationCodeAndObsTime(String stationCode, LocalDateTime obsTime);
}
