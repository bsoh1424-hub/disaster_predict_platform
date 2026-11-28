package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.PredictionRun;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface PredictionRunRepository extends JpaRepository<PredictionRun, Long> {
    Optional<PredictionRun> findTopByRunTypeOrderByExecutedAtDesc(String runType);
    Optional<PredictionRun> findTopByOrderByExecutedAtDesc();
    List<PredictionRun> findTop100ByOrderByExecutedAtDesc();
}
