package com.example.webapp.BookIndex;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookIndexContentRepository extends JpaRepository<BookIndexContentEntity,Long> {
    List<BookIndexContentEntity> findAllByWordContains(String word);
}
