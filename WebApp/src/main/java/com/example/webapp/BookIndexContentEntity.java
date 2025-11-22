package com.example.webapp;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@IdClass(BookIndexCompositeID.class)
@Table(name = "books_index_content")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BookIndexContentEntity {

    @Id
    private String word;

    @Id
    private Long bookId;

    @Column(nullable = false)
    private Integer frequency;
}