package com.example.webapp;


import com.example.webapp.BookIndex.BookIndexContentEntity;
import com.example.webapp.BookIndex.BookIndexContentRepository;
import com.example.webapp.BookIndex.BookIndexEntity;
import com.example.webapp.BookIndex.BookIndexRepository;
import com.example.webapp.DTOS.BookResponseDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;

import org.springframework.web.client.RestTemplate;

@Service
public class SearchService {

    private final BookRepository bookRepository;
    private final BookIndexRepository bookIndexRepository;
    private final BookIndexContentRepository bookIndexContentRepository;
    private final RestTemplate restTemplate;
    @Value("${generate_words_api}")
    private String WORD_GENERATOR_API;



    public SearchService(BookRepository bookRepository, BookIndexRepository bookIndexRepository, BookIndexContentRepository bookIndexContentRepository, StartUpInitializer startupInitializer, RestTemplate restTemplate) {
        this.bookRepository = bookRepository;
        this.bookIndexRepository = bookIndexRepository;
        this.bookIndexContentRepository = bookIndexContentRepository;
        this.restTemplate = restTemplate;
    }


    public List<BookResponseDTO> searchByTitle(String pattern) {
        /*
        Get all Words , Parse them into Ids , Get all Books after & return BookResponseDTO
         */
        List<BookIndexEntity> indexEntries = bookIndexRepository.findAllByWordContains(pattern);

        List<Long> bookIds = indexEntries.stream()
                .map(BookIndexEntity::getBookId)
                .toList();

        List<Book> books = bookRepository.findAllById(bookIds);

        List<BookResponseDTO> results = books.stream()
                .map(book -> BookResponseDTO.builder()
                        .id(book.getId())
                        .title(book.getTitle())
                        .author(book.getAuthor())
                        .build())
                .toList();

        return results;
    }

    public List<BookResponseDTO> searchByTitleContent(String regex,
                                                      Integer maxWords, Integer maxLength) {
        // 1️⃣ Prepare request to Python word generator API
        Map<String, Object> requestBody = Map.of(
                "pattern", regex,
                "max_words", maxWords != null ? maxWords : 100,
                "max_length", maxLength != null ? maxLength : 50
        );

        // 2️⃣ Call Python API
        Map<String, Object> response = restTemplate.postForObject(
                WORD_GENERATOR_API,
                requestBody,
                Map.class
        );

        // 3️⃣ Extract generated words
        List<String> generatedWords = (List<String>) response.get("generated_words");
        if (generatedWords == null || generatedWords.isEmpty()) {
            return Collections.emptyList();
        }

        // Set to avoid dupes
        Set<BookIndexContentEntity> indexEntriesSet = new HashSet<>();
        for (String word : generatedWords) {
            indexEntriesSet.addAll(bookIndexContentRepository.findAllByWordContains(word));
        }

        List<BookIndexContentEntity> indexEntries = new ArrayList<>(indexEntriesSet);



        if (indexEntries.isEmpty()) {
            return Collections.emptyList();
        }

        // 5️⃣ Collect unique bookIds
        List<Long> bookIds = indexEntries.stream()
                .map(BookIndexContentEntity::getBookId)
                .distinct()
                .toList();

        // 6️⃣ Fetch all books in a single query
        List<Book> books = bookRepository.findAllById(bookIds);

        // 7️⃣ Map to BookResponseDTO
        return books.stream()
                .map(book -> BookResponseDTO.builder()
                        .id(book.getId())
                        .title(book.getTitle())
                        .author(book.getAuthor())
                        .build())
                .toList();
    }
}
