package com.disaster.stormsurge.dto;

import java.util.List;
import java.util.Map;

public class FastApiDto {

    public record PredictRequest(
        String station_id,
        String base_time,
        Map<String, Object> features
    ) {}

    public record PredictionItem(
        int lead_hour,
        String target_time,
        double residual_cm,
        double exceed_probability
    ) {}

    public record PredictResponse(
        String station_id,
        String base_time,
        String model_version,
        List<PredictionItem> predictions
    ) {}

    public record HealthResponse(
        String status,
        String model_version,
        String loaded_at,
        String model_dir
    ) {}

    public record RagRequest(
        String query,
        Map<String, Object> context_info
    ) {}

    public record RagResponse(
        String query,
        String answer,
        List<String> sources,
        String llm_used
    ) {}
}
