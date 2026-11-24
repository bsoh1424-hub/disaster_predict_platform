package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.StationThreshold;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface StationThresholdRepository extends JpaRepository<StationThreshold, Long> {
    Optional<StationThreshold> findByStationCode(String stationCode);
}
