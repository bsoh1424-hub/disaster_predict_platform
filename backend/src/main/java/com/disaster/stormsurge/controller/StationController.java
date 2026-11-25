package com.disaster.stormsurge.controller;

import com.disaster.stormsurge.dto.StationDto.*;
import com.disaster.stormsurge.service.StationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/stations")
public class StationController {

    private final StationService stationService;

    public StationController(StationService stationService) {
        this.stationService = stationService;
    }

    /**
     * 아키텍처 11장: GET /api/stations
     * 관측소 목록과 최신 상태 요약
     */
    @GetMapping
    public ResponseEntity<List<StationSummary>> getStations() {
        return ResponseEntity.ok(stationService.getAllStationSummaries());
    }

    @GetMapping("/{id}")
    public ResponseEntity<StationDetail> getStation(@PathVariable("id") String stationCode) {
        return ResponseEntity.ok(stationService.getStationDetail(stationCode));
    }
}
