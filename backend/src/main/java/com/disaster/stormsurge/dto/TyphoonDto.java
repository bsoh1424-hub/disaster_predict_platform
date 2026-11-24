package com.disaster.stormsurge.dto;

import java.util.List;

public class TyphoonDto {

    public record CaseSummary(
        String caseId,
        String name,
        Integer year,
        String period,
        Double maxSurgeCm,
        String affectedStations,
        String description
    ) {}

    public record EvaluationItem(
        String stationCode,
        Integer leadHour,
        Double peakErrorCm,
        Double peakTimeErrorHours,
        Double exceedF1,
        Double baselineAstroErrorCm,
        Double baselineRtsmErrorCm
    ) {}

    public record CaseDetail(
        CaseSummary caseInfo,
        List<EvaluationItem> evaluations
    ) {}
}
