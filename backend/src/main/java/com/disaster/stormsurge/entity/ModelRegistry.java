package com.disaster.stormsurge.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "model_registry")
public class ModelRegistry {

    @Id
    @Column(name = "version", length = 50)
    private String version;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "train_period", length = 100)
    private String trainPeriod;

    @Column(name = "stations", length = 255)
    private String stations;

    @Column(name = "data_snapshot", length = 255)
    private String dataSnapshot;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = false;

    @Column(name = "meta_json", columnDefinition = "TEXT")
    private String metaJson;

    public ModelRegistry() {}

    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public String getTrainPeriod() { return trainPeriod; }
    public void setTrainPeriod(String trainPeriod) { this.trainPeriod = trainPeriod; }
    public String getStations() { return stations; }
    public void setStations(String stations) { this.stations = stations; }
    public String getDataSnapshot() { return dataSnapshot; }
    public void setDataSnapshot(String dataSnapshot) { this.dataSnapshot = dataSnapshot; }
    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }
    public String getMetaJson() { return metaJson; }
    public void setMetaJson(String metaJson) { this.metaJson = metaJson; }
}
