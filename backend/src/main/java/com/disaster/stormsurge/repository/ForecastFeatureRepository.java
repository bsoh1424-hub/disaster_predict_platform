package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.ForecastFeature;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ForecastFeatureRepository extends JpaRepository<ForecastFeature, Long> {
    Optional<ForecastFeature> findTopByStationCodeOrderByForecastTimeDesc(String stationCode);
}
