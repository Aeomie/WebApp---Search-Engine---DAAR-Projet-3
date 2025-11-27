package com.example.webapp.BookIndex;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookIndexRepository extends JpaRepository<BookIndexEntity,Long> {

    List<BookIndexEntity> findAllByWordContains(String word);
}
