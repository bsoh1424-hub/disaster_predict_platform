package com.disaster.stormsurge.controller;

import com.disaster.stormsurge.dto.TyphoonDto.*;
import com.disaster.stormsurge.service.TyphoonCaseService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/cases")
public class TyphoonCaseController {

    private final TyphoonCaseService caseService;

    public TyphoonCaseController(TyphoonCaseService caseService) {
        this.caseService = caseService;
    }

    /**
     * 아키텍처 11장: GET /api/cases
     * 태풍 사례 목록 (Q6)
     */
    @GetMapping
    public ResponseEntity<List<CaseSummary>> getCases() {
        return ResponseEntity.ok(caseService.getAllCases());
    }

    /**
     * 아키텍처 11장: GET /api/cases/{id}
     * 특정 태풍 사례와 평가 결과 (피크 오차, 초과 분류 등)
     */
    @GetMapping("/{id}")
    public ResponseEntity<CaseDetail> getCaseDetail(@PathVariable("id") String caseId) {
        return ResponseEntity.ok(caseService.getCaseDetail(caseId));
    }
}
