package com.example.webapp;

import lombok.Data;

@Data
public class GenerateWordDTO {
    private String pattern;
    private int maxWords = 100;
    private int maxLength = 100;
}
