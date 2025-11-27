package com.example.webapp.BookIndex;

import lombok.Data;

import java.io.Serializable;

@Data
public class BookIndexCompositeID implements Serializable {
    private String word;
    private Long bookId;
}
