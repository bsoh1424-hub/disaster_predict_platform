package com.disaster.stormsurge.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "evaluation_result")
public class EvaluationResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "case_id", nullable = false, length = 30)
    private String caseId;

    @Column(name = "station_code", nullable = false, length = 20)
    private String stationCode;

    @Column(name = "lead_hour", nullable = false)
    private Integer leadHour; // 12, 24

    @Column(name = "peak_error_cm")
    private Double peakErrorCm; // 딥러닝 모델 피크 오차 (cm)

    @Column(name = "peak_time_error_hours")
    private Double peakTimeErrorHours; // 피크 시각 오차 (시간)

    @Column(name = "exceed_f1")
    private Double exceedF1; // 총조위 임계 초과 분류 F1 점수

    @Column(name = "baseline_astro_error_cm")
    private Double baselineAstroErrorCm; // 천문조 베이스라인 피크 오차 (cm)

    @Column(name = "baseline_rtsm_error_cm")
    private Double baselineRtsmErrorCm; // 기상청 RTSM 수치모델 피크 오차 (cm)

    public EvaluationResult() {}

    public Long getId() { return id; }
    public String getCaseId() { return caseId; }
    public void setCaseId(String caseId) { this.caseId = caseId; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public Integer getLeadHour() { return leadHour; }
    public void setLeadHour(Integer leadHour) { this.leadHour = leadHour; }
    public Double getPeakErrorCm() { return peakErrorCm; }
    public void setPeakErrorCm(Double peakErrorCm) { this.peakErrorCm = peakErrorCm; }
    public Double getPeakTimeErrorHours() { return peakTimeErrorHours; }
    public void setPeakTimeErrorHours(Double peakTimeErrorHours) { this.peakTimeErrorHours = peakTimeErrorHours; }
    public Double getExceedF1() { return exceedF1; }
    public void setExceedF1(Double exceedF1) { this.exceedF1 = exceedF1; }
    public Double getBaselineAstroErrorCm() { return baselineAstroErrorCm; }
    public void setBaselineAstroErrorCm(Double baselineAstroErrorCm) { this.baselineAstroErrorCm = baselineAstroErrorCm; }
    public Double getBaselineRtsmErrorCm() { return baselineRtsmErrorCm; }
    public void setBaselineRtsmErrorCm(Double baselineRtsmErrorCm) { this.baselineRtsmErrorCm = baselineRtsmErrorCm; }
}
