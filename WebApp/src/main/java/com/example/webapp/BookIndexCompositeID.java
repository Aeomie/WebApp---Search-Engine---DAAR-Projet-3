package com.example.webapp;

import lombok.Data;

import java.io.Serializable;

@Data
public class BookIndexCompositeID implements Serializable {
    private String word;
    private Long bookId;
}
