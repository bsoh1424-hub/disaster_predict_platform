package com.disaster.stormsurge.client;

import com.disaster.stormsurge.dto.FastApiDto.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.Optional;

@Component
public class FastApiClient {

    private static final Logger log = LoggerFactory.getLogger(FastApiClient.class);
    private final RestClient restClient;

    public FastApiClient(RestClient fastApiRestClient) {
        this.restClient = fastApiRestClient;
    }

    public Optional<HealthResponse> checkHealth() {
        try {
            HealthResponse response = restClient.get()
                    .uri("/health")
                    .retrieve()
                    .body(HealthResponse.class);
            return Optional.ofNullable(response);
        } catch (Exception e) {
            log.warn("FastAPI health check failed: {}", e.getMessage());
            return Optional.empty();
        }
    }

    public Optional<PredictResponse> predict(String stationId, String baseTime, Map<String, Object> features) {
        try {
            PredictRequest request = new PredictRequest(stationId, baseTime, features);
            PredictResponse response = restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(PredictResponse.class);
            return Optional.ofNullable(response);
        } catch (Exception e) {
            log.error("FastAPI /predict failed for station {}: {}", stationId, e.getMessage());
            return Optional.empty();
        }
    }

    public Optional<RagResponse> queryRag(String query, Map<String, Object> contextInfo) {
        try {
            RagRequest request = new RagRequest(query, contextInfo);
            RagResponse response = restClient.post()
                    .uri("/rag/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(RagResponse.class);
            return Optional.ofNullable(response);
        } catch (Exception e) {
            log.error("FastAPI /rag/query failed: {}", e.getMessage());
            return Optional.empty();
        }
    }

    public boolean triggerCollection(String stationId) {
        try {
            restClient.post()
                    .uri(uriBuilder -> uriBuilder.path("/collector/trigger").queryParam("station_id", stationId).build())
                    .retrieve()
                    .toBodilessEntity();
            return true;
        } catch (Exception e) {
            log.warn("FastAPI /collector/trigger failed for station {}: {}", stationId, e.getMessage());
            return false;
        }
    }
}
