package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.PredictionResult;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface PredictionResultRepository extends JpaRepository<PredictionResult, Long> {
    List<PredictionResult> findByRunIdAndStationCodeOrderByLeadHourAsc(Long runId, String stationCode);
    List<PredictionResult> findByRunIdOrderByStationCodeAscLeadHourAsc(Long runId);
}
