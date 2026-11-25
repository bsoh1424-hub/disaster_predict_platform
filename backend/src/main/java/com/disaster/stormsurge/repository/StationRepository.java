package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.Station;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface StationRepository extends JpaRepository<Station, String> {
    List<Station> findByActiveTrue();
}
