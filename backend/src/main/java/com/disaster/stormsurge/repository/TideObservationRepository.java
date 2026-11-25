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
}
