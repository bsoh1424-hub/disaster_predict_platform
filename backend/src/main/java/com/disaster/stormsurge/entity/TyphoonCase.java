package com.disaster.stormsurge.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "typhoon_case")
public class TyphoonCase {

    @Id
    @Column(name = "case_id", length = 30)
    private String caseId; // e.g. "MAEMI_2003", "CHABA_2016", "HINNAMNOR_2022"

    @Column(nullable = false, length = 50)
    private String name; // e.g. "태풍 매미 (MAEMI)"

    @Column(name = "case_year", nullable = false)
    private Integer year;

    @Column(nullable = false, length = 50)
    private String period; // e.g. "2003-09-11 ~ 2003-09-13"

    @Column(name = "max_surge_cm")
    private Double maxSurgeCm;

    @Column(name = "affected_stations", length = 255)
    private String affectedStations;

    @Column(columnDefinition = "TEXT")
    private String description;

    public TyphoonCase() {}

    public TyphoonCase(String caseId, String name, Integer year, String period, Double maxSurgeCm, String affectedStations, String description) {
        this.caseId = caseId;
        this.name = name;
        this.year = year;
        this.period = period;
        this.maxSurgeCm = maxSurgeCm;
        this.affectedStations = affectedStations;
        this.description = description;
    }

    public String getCaseId() { return caseId; }
    public void setCaseId(String caseId) { this.caseId = caseId; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Integer getYear() { return year; }
    public void setYear(Integer year) { this.year = year; }
    public String getPeriod() { return period; }
    public void setPeriod(String period) { this.period = period; }
    public Double getMaxSurgeCm() { return maxSurgeCm; }
    public void setMaxSurgeCm(Double maxSurgeCm) { this.maxSurgeCm = maxSurgeCm; }
    public String getAffectedStations() { return affectedStations; }
    public void setAffectedStations(String affectedStations) { this.affectedStations = affectedStations; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
}
