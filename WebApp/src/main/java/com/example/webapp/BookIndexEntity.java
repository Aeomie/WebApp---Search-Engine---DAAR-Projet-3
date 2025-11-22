package com.example.webapp;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@IdClass(BookIndexCompositeID.class)
@Table(name = "books_index")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BookIndexEntity {

    @Id
    private String word;

    @Id
    private Long bookId;

    @Column(nullable = false)
    private Integer frequency;
}