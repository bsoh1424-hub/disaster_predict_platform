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
        Double latestTotalTideCm, // 12시간 뒤 예측 총수위 (예측 없으면 null)
        Double latestObsTideCm, // 최신 관측 수위 (실시간, 관측 없으면 null)
        LocalDateTime latestObsTime, // 최신 관측 시각 (관측 없으면 null)
        Double advisoryThresholdCm,
        Double warningThresholdCm,
        String alertLevel, // NORMAL, ADVISORY, WARNING (현재 관측 수위 기준)
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
