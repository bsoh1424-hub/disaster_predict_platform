package com.disaster.stormsurge.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "station")
public class Station {

    @Id
    @Column(name = "station_code", length = 20)
    private String stationCode; // e.g. "BUSAN", "INCHEON"

    @Column(nullable = false, length = 50)
    private String name; // e.g. "부산", "인천"

    @Column(nullable = false)
    private Double latitude;

    @Column(nullable = false)
    private Double longitude;

    @Column(length = 50)
    private String seaRegion; // 서해, 남해, 동해

    @Column(nullable = false)
    private Boolean active = true;

    @Column(length = 255)
    private String description;

    public Station() {}

    public Station(String stationCode, String name, Double latitude, Double longitude, String seaRegion, Boolean active, String description) {
        this.stationCode = stationCode;
        this.name = name;
        this.latitude = latitude;
        this.longitude = longitude;
        this.seaRegion = seaRegion;
        this.active = active;
        this.description = description;
    }

    public String getStationCode() { return stationCode; }
    public void setStationCode(String stationCode) { this.stationCode = stationCode; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Double getLatitude() { return latitude; }
    public void setLatitude(Double latitude) { this.latitude = latitude; }
    public Double getLongitude() { return longitude; }
    public void setLongitude(Double longitude) { this.longitude = longitude; }
    public String getSeaRegion() { return seaRegion; }
    public void setSeaRegion(String seaRegion) { this.seaRegion = seaRegion; }
    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
