package com.disaster.stormsurge.service;

import com.disaster.stormsurge.dto.TyphoonDto.*;
import com.disaster.stormsurge.entity.EvaluationResult;
import com.disaster.stormsurge.entity.TyphoonCase;
import com.disaster.stormsurge.repository.EvaluationResultRepository;
import com.disaster.stormsurge.repository.TyphoonCaseRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class TyphoonCaseService {

    private final TyphoonCaseRepository caseRepository;
    private final EvaluationResultRepository evaluationRepository;

    public TyphoonCaseService(TyphoonCaseRepository caseRepository, EvaluationResultRepository evaluationRepository) {
        this.caseRepository = caseRepository;
        this.evaluationRepository = evaluationRepository;
    }

    public List<CaseSummary> getAllCases() {
        List<TyphoonCase> cases = caseRepository.findAllByOrderByYearDesc();
        List<CaseSummary> list = new ArrayList<>();
        for (TyphoonCase c : cases) {
            list.add(new CaseSummary(
                    c.getCaseId(),
                    c.getName(),
                    c.getYear(),
                    c.getPeriod(),
                    c.getMaxSurgeCm(),
                    c.getAffectedStations(),
                    c.getDescription()
            ));
        }
        return list;
    }

    public CaseDetail getCaseDetail(String caseId) {
        TyphoonCase c = caseRepository.findById(caseId)
                .orElseThrow(() -> new IllegalArgumentException("태풍 사례를 찾을 수 없습니다: " + caseId));

        List<EvaluationResult> evals = evaluationRepository.findByCaseId(caseId);
        List<EvaluationItem> evalItems = new ArrayList<>();
        for (EvaluationResult e : evals) {
            evalItems.add(new EvaluationItem(
                    e.getStationCode(),
                    e.getLeadHour(),
                    e.getPeakErrorCm(),
                    e.getPeakTimeErrorHours(),
                    e.getExceedF1(),
                    e.getBaselineAstroErrorCm(),
                    e.getBaselineRtsmErrorCm()
            ));
        }

        CaseSummary summary = new CaseSummary(
                c.getCaseId(),
                c.getName(),
                c.getYear(),
                c.getPeriod(),
                c.getMaxSurgeCm(),
                c.getAffectedStations(),
                c.getDescription()
        );

        return new CaseDetail(summary, evalItems);
    }
}
