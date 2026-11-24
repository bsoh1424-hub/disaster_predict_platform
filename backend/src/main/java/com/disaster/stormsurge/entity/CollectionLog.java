package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "collection_log")
public class CollectionLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "source", nullable = false, length = 20)
    private String source; // KHOA, KMA

    @Column(name = "station_code", length = 20)
    private String stationCode;

    @Column(name = "collected_at", nullable = false)
    private LocalDateTime collectedAt;

    @Column(name = "status", nullable = false, length = 20)
    private String status; // SUCCESS, FAILED

    @Column(name = "row_count")
    private Integer rowCount;

    @Column(name = "error_message", length = 500)
    private String errorMessage;

    public CollectionLog() {}

    public Long getId() { return id; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public LocalDateTime getCollectedAt() { return collectedAt; }
    public void setCollectedAt(LocalDateTime collectedAt) { this.collectedAt = collectedAt; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getRowCount() { return rowCount; }
    public void setRowCount(Integer rowCount) { this.rowCount = rowCount; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
}
