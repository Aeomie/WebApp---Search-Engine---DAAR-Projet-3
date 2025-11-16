package com.example.webapp.exception;

public class JsonFileNotFoundException extends RuntimeException {
    public JsonFileNotFoundException(String message) {
        super(message);
    }

    public JsonFileNotFoundException(String message, Throwable cause) {
        super(message, cause);
    }
}
