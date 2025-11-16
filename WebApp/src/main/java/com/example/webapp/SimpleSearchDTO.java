package com.example.webapp;

import lombok.Data;

@Data
public class SimpleSearchDTO {
    private String pattern;
    private boolean verbose;
}
