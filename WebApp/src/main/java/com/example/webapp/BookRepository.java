package com.example.webapp;

import org.springframework.data.jpa.repository.JpaRepository;

public interface BookRepository extends JpaRepository<Book,Long> {
    boolean existsByTitle(String title);
}
