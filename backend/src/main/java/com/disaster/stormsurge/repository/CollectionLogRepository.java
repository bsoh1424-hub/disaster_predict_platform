package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.CollectionLog;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CollectionLogRepository extends JpaRepository<CollectionLog, Long> {
    List<CollectionLog> findTop20ByOrderByCollectedAtDesc();
}
