package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "prediction_run")
public class PredictionRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "run_id")
    private Long runId;

    @Column(name = "run_type", nullable = false, length = 20)
    private String runType; // BATCH, REALTIME

    @Column(name = "executed_at", nullable = false)
    private LocalDateTime executedAt;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(name = "status", length = 20)
    private String status; // SUCCESS, FALLBACK, FAILED

    @Column(name = "trigger_user", length = 50)
    private String triggerUser;

    public PredictionRun() {}

    public PredictionRun(String runType, LocalDateTime executedAt, String modelVersion, String status, String triggerUser) {
        this.runType = runType;
        this.executedAt = executedAt;
        this.modelVersion = modelVersion;
        this.status = status;
        this.triggerUser = triggerUser;
    }

    public Long getRunId() { return runId; }
    public String getRunType() { return runType; }
    public void setRunType(String runType) { this.runType = runType; }
    public LocalDateTime getExecutedAt() { return executedAt; }
    public void setExecutedAt(LocalDateTime executedAt) { this.executedAt = executedAt; }
    public String getModelVersion() { return modelVersion; }
    public void setModelVersion(String modelVersion) { this.modelVersion = modelVersion; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getTriggerUser() { return triggerUser; }
    public void setTriggerUser(String triggerUser) { this.triggerUser = triggerUser; }
}
