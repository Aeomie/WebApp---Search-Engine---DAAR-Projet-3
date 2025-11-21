package com.example.webapp;

import org.springframework.data.jpa.repository.JpaRepository;

public interface BookResponseRepository extends JpaRepository<BookResponseDTO,Long> {

}
