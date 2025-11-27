package com.example.webapp;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookIndexContentRepository extends JpaRepository<BookIndexContentEntity,Long> {
    List<BookIndexContentEntity> findAllByWordIn(List<String> word);
    List<BookIndexContentEntity> findAllByWordContains(String word);
}
