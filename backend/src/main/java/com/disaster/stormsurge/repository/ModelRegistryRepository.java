package com.disaster.stormsurge.repository;

import com.disaster.stormsurge.entity.ModelRegistry;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface ModelRegistryRepository extends JpaRepository<ModelRegistry, String> {
    Optional<ModelRegistry> findByIsActiveTrue();
}
