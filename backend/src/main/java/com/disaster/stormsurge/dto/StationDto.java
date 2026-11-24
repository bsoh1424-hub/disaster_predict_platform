package com.disaster.stormsurge.dto;

import java.time.LocalDateTime;
import java.util.List;

public class StationDto {

    public record StationSummary(
        String stationCode,
        String name,
        Double latitude,
        Double longitude,
        String seaRegion,
        Double latestTotalTideCm,
        Double advisoryThresholdCm,
        Double warningThresholdCm,
        String alertLevel, // NORMAL, ADVISORY, WARNING
        Boolean isExceeded,
        LocalDateTime lastUpdated
    ) {}

    public record StationDetail(
        String stationCode,
        String name,
        Double latitude,
        Double longitude,
        String seaRegion,
        Double advisoryThresholdCm,
        Double warningThresholdCm,
        Double localFloodThresholdCm,
        String description
    ) {}
}
