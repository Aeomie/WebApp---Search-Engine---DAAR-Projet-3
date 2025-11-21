package com.example.webapp;

import jakarta.persistence.Column;
import jakarta.persistence.Id;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BookResponseDTO {

    private Long id;

    private String title;

    private String author;
}
