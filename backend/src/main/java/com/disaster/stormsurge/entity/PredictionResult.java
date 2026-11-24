package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "prediction_result", indexes = {
    @Index(name = "idx_pred_run_station_lead", columnList = "run_id, station_code, lead_hour, target_time")
})
public class PredictionResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "run_id", nullable = false)
    private Long runId;

    @Column(name = "station_code", nullable = false, length = 20)
    private String stationCode;

    @Column(name = "lead_hour", nullable = false)
    private Integer leadHour; // 12, 24

    @Column(name = "target_time", nullable = false)
    private LocalDateTime targetTime;

    @Column(name = "residual_cm", nullable = false)
    private Double residualCm; // 예측 조위 편차 (잔차)

    @Column(name = "exceed_probability", nullable = false)
    private Double exceedProbability; // 초과 확률 (0.0 ~ 1.0)

    @Column(name = "astronomical_tide_cm", nullable = false)
    private Double astronomicalTideCm; // 천문조 예측 조위

    @Column(name = "total_tide_cm", nullable = false)
    private Double totalTideCm; // 총 수위 = 천문조 + 잔차

    @Column(name = "is_exceeded", nullable = false)
    private Boolean isExceeded = false; // 주의보/경보 문턱 초과 여부

    @Column(name = "alert_level", length = 20)
    private String alertLevel; // NORMAL, ADVISORY, WARNING

    @Column(name = "is_tide_overlap")
    private Boolean isTideOverlap = false; // 만조 겹침 여부

    @Column(name = "reason_text", length = 500)
    private String reasonText; // 근거 패널 텍스트

    public PredictionResult() {}

    public Long getId() { return id; }
    public Long getRunId() { return runId; }
    public void setRunId(Long runId) { this.runId = runId; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public Integer getLeadHour() { return leadHour; }
    public void setLeadHour(Integer leadHour) { this.leadHour = leadHour; }
    public LocalDateTime getTargetTime() { return targetTime; }
    public void setTargetTime(LocalDateTime targetTime) { this.targetTime = targetTime; }
    public Double getResidualCm() { return residualCm; }
    public void setResidualCm(Double residualCm) { this.residualCm = residualCm; }
    public Double getExceedProbability() { return exceedProbability; }
    public void setExceedProbability(Double exceedProbability) { this.exceedProbability = exceedProbability; }
    public Double getAstronomicalTideCm() { return astronomicalTideCm; }
    public void setAstronomicalTideCm(Double astronomicalTideCm) { this.astronomicalTideCm = astronomicalTideCm; }
    public Double getTotalTideCm() { return totalTideCm; }
    public void setTotalTideCm(Double totalTideCm) { this.totalTideCm = totalTideCm; }
    public Boolean getIsExceeded() { return isExceeded; }
    public void setIsExceeded(Boolean isExceeded) { this.isExceeded = isExceeded; }
    public String getAlertLevel() { return alertLevel; }
    public void setAlertLevel(String alertLevel) { this.alertLevel = alertLevel; }
    public Boolean getIsTideOverlap() { return isTideOverlap; }
    public void setIsTideOverlap(Boolean isTideOverlap) { this.isTideOverlap = isTideOverlap; }
    public String getReasonText() { return reasonText; }
    public void setReasonText(String reasonText) { this.reasonText = reasonText; }
}
