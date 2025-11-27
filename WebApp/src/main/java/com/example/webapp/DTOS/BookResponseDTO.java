package com.example.webapp.DTOS;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BookResponseDTO {

    private Long id;

    private String title;

    private String author;
}
