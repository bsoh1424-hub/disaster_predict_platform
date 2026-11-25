package com.disaster.stormsurge.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "station_threshold")
public class StationThreshold {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "station_code", nullable = false, length = 20)
    private String stationCode;

    @Column(name = "advisory_cm", nullable = false)
    private Double advisoryCm; // 주의보 총 수위 기준 (cm)

    @Column(name = "warning_cm", nullable = false)
    private Double warningCm; // 경보 총 수위 기준 (cm)

    @Column(name = "local_flood_cm")
    private Double localFloodCm; // 어항/저지대 침수 시작 기준 (cm)

    @Column(length = 100)
    private String note;

    public StationThreshold() {}

    public StationThreshold(String stationCode, Double advisoryCm, Double warningCm, Double localFloodCm, String note) {
        this.stationCode = stationCode;
        this.advisoryCm = advisoryCm;
        this.warningCm = warningCm;
        this.localFloodCm = localFloodCm;
        this.note = note;
    }

    public Long getId() { return id; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public Double getAdvisoryCm() { return advisoryCm; }
    public void setAdvisoryCm(Double advisoryCm) { this.advisoryCm = advisoryCm; }
    public Double getWarningCm() { return warningCm; }
    public void setWarningCm(Double warningCm) { this.warningCm = warningCm; }
    public Double getLocalFloodCm() { return localFloodCm; }
    public void setLocalFloodCm(Double localFloodCm) { this.localFloodCm = localFloodCm; }
    public String getNote() { return note; }
    public void setNote(String note) { this.note = note; }
}
