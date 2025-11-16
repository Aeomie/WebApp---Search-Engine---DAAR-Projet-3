package com.example.webapp;


import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.web.client.RestTemplate;

@Service
public class SearchService {

    private final BookRepository bookRepository;
    private final StartUpInitializer startupInitializer;
    private final RestTemplate restTemplate;


    public SearchService(BookRepository bookRepository, StartUpInitializer startupInitializer, RestTemplate restTemplate) {
        this.bookRepository = bookRepository;
        this.startupInitializer = startupInitializer;
        this.restTemplate = restTemplate;
    }

    public List<BookResponseDTO> searchBoyer(String pattern,  boolean verbose) {

        String pythonUrl = "http://localhost:8001/searchBoyer";
        Map<Long, Book> books = startupInitializer.getBooks();
        List<String> titles = books.values().stream()
                .map(Book::getTitle)
                .toList();

        // Prepare request body
        // verbose always false as of now
        Map<String, Object> requestBody = Map.of(
                "pattern", pattern,
                "texts", titles,
                "verbose", verbose
        );

        // Call Python API
        Map<String, Object> response = restTemplate.postForObject(
                pythonUrl,
                requestBody,
                Map.class
        );

        // Extract results
        List<Map<String, Object>> apiResults = (List<Map<String, Object>>) response.get("results");

        List<BookResponseDTO> results = new ArrayList<>();
        for (Map<String, Object> item : apiResults) {
            int totalCount = (Integer) item.get("total_count");
            if (totalCount > 0) {
                // Find the book corresponding to this title
                String title = (String) item.get("text");
                books.values().stream()
                        .filter(b -> b.getTitle().equals(title))
                        .findFirst().ifPresent(book -> results.add(BookResponseDTO.builder()
                                .id(book.getId())
                                .title(book.getTitle())
                                .author(book.getAuthor())
                                .build()
                        ));

            }
        }

        return results;

    }
}
