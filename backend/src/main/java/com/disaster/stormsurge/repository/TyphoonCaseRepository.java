package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.TyphoonCase;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TyphoonCaseRepository extends JpaRepository<TyphoonCase, String> {
    List<TyphoonCase> findAllByOrderByYearDesc();
}
