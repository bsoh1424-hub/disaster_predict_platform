package com.disaster.stormsurge.dto;

import java.time.LocalDateTime;
import java.util.List;

public class ForecastDto {

    public record ForecastPoint(
        Integer leadHour,
        String targetTime,
        Double astronomicalTideCm,
        Double residualCm,
        Double totalTideCm,
        Double exceedProbability,
        Boolean isExceeded,
        String alertLevel,
        Boolean isTideOverlap
    ) {}

    public record ForecastResponse(
        String stationCode,
        String stationName,
        String baseTime,
        Long runId,
        String runType,
        String modelVersion,
        Boolean isFallback,
        Double advisoryThresholdCm,
        Double warningThresholdCm,
        Double localFloodThresholdCm,
        List<ForecastPoint> points,
        String reasonSummary,
        TideSummary tideSummary,
        OfficialWarning officialWarning
    ) {}

    public record TideSummary(
        Double maxTotalTideCm,
        String maxTideTime,
        Double maxResidualCm,
        String maxResidualTime,
        Boolean highTideOverlap,
        String overlapWindow
    ) {}

    public record OfficialWarning(
        String officialStatus, // "발령 없음", "폭풍해일주의보", "폭풍해일경보"
        String noticeText,
        Boolean matchWithModel
    ) {}

    public record ObservationPoint(
        String obsTime,
        Double tideObsCm,
        Double tidePredCm,
        Double residualCm,
        Double airPressureHpa,
        Double windSpeedMs,
        Double windDirDeg
    ) {}

    public record ObservationResponse(
        String stationCode,
        String stationName,
        List<ObservationPoint> observations
    ) {}
}
