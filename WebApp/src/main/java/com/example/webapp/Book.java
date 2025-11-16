package com.example.webapp;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "books")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Book {

    @Id
    private Long id;

    @Column(nullable = false, length = 500)
    private String title;  // ← lowercase 't'

    @Column(length = 200)
    private String author;  // ← lowercase 'a'

    @Column(name = "file_path", nullable = false)
    private String filePath;

    @Column(name = "source_url")
    private String sourceUrl;
}