package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "forecast_feature", indexes = {
    @Index(name = "idx_fcst_station_time", columnList = "station_code, forecast_time")
})
public class ForecastFeature {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "station_code", nullable = false, length = 20)
    private String stationCode;

    @Column(name = "forecast_time", nullable = false)
    private LocalDateTime forecastTime;

    @Column(name = "forecast_pressure_12h")
    private Double forecastPressure12h;

    @Column(name = "forecast_pressure_24h")
    private Double forecastPressure24h;

    @Column(name = "forecast_wind_12h")
    private Double forecastWind12h;

    @Column(name = "forecast_wind_24h")
    private Double forecastWind24h;

    public ForecastFeature() {}

    public Long getId() { return id; }
    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public LocalDateTime getForecastTime() { return forecastTime; }
    public void setForecastTime(LocalDateTime forecastTime) { this.forecastTime = forecastTime; }
    public Double getForecastPressure12h() { return forecastPressure12h; }
    public void setForecastPressure12h(Double forecastPressure12h) { this.forecastPressure12h = forecastPressure12h; }
    public Double getForecastPressure24h() { return forecastPressure24h; }
    public void setForecastPressure24h(Double forecastPressure24h) { this.forecastPressure24h = forecastPressure24h; }
    public Double getForecastWind12h() { return forecastWind12h; }
    public void setForecastWind12h(Double forecastWind12h) { this.forecastWind12h = forecastWind12h; }
    public Double getForecastWind24h() { return forecastWind24h; }
    public void setForecastWind24h(Double forecastWind24h) { this.forecastWind24h = forecastWind24h; }
}
