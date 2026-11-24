package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.EvaluationResult;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EvaluationResultRepository extends JpaRepository<EvaluationResult, Long> {
    List<EvaluationResult> findByCaseId(String caseId);
}
