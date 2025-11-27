package com.example.webapp;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookIndexRepository extends JpaRepository<BookIndexEntity,Long> {
    // Find all entries for a given word
    List<BookIndexEntity> findAllByWord(String word);

    List<BookIndexEntity> findAllByWordContains(String word);
    List<BookIndexEntity> findAllByBookId(Long bookId);
}
