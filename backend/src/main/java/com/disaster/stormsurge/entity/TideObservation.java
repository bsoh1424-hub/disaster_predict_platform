package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "tide_observation", indexes = {
    @Index(name = "idx_obs_station_time", columnList = "station_code, obs_time")
})
public class TideObservation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "station_code", nullable = false, length = 20)
    private String stationCode;

    @Column(name = "obs_time", nullable = false)
    private LocalDateTime obsTime;

    @Column(name = "tide_obs_cm")
    private Double tideObsCm; // 실측 조위

    @Column(name = "tide_pred_cm")
    private Double tidePredCm; // 천문조 예측 조위

    @Column(name = "residual_cm")
    private Double residualCm; // 실측 - 천문조 조위 편차

    @Column(name = "air_pressure_hpa")
    private Double airPressureHpa; // 현지 기압

    @Column(name = "wind_speed_ms")
    private Double windSpeedMs; // 풍속

    @Column(name = "wind_dir_deg")
    private Double windDirDeg; // 풍향

    public TideObservation() {}

    public Long getId() { return id; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public LocalDateTime getObsTime() { return obsTime; }
    public void setObsTime(LocalDateTime obsTime) { this.obsTime = obsTime; }
    public Double getTideObsCm() { return tideObsCm; }
    public void setTideObsCm(Double tideObsCm) { this.tideObsCm = tideObsCm; }
    public Double getTidePredCm() { return tidePredCm; }
    public void setTidePredCm(Double tidePredCm) { this.tidePredCm = tidePredCm; }
    public Double getResidualCm() { return residualCm; }
    public void setResidualCm(Double residualCm) { this.residualCm = residualCm; }
    public Double getAirPressureHpa() { return airPressureHpa; }
    public void setAirPressureHpa(Double airPressureHpa) { this.airPressureHpa = airPressureHpa; }
    public Double getWindSpeedMs() { return windSpeedMs; }
    public void setWindSpeedMs(Double windSpeedMs) { this.windSpeedMs = windSpeedMs; }
    public Double getWindDirDeg() { return windDirDeg; }
    public void setWindDirDeg(Double windDirDeg) { this.windDirDeg = windDirDeg; }
}
