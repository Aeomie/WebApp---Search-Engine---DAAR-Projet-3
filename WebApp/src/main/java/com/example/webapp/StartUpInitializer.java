package com.example.webapp;


import com.example.webapp.exception.InitializationException;
import com.example.webapp.exception.JsonFileNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import jakarta.annotation.PostConstruct;
import lombok.Getter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Component
public class StartUpInitializer {


    private static final Logger logger = LoggerFactory.getLogger(StartUpInitializer.class);

    @Getter
    private Map<Long, Book> books;
    private final BookRepository bookRepository;

    // Path relative to resources folder
    private static final String JSON_FILE_PATH = "books_data/books_catalog.json";


    @Autowired
    public StartUpInitializer(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
        this.books = new HashMap<>();
    }

    @PostConstruct
    public void initialize() {
        logger.info("=".repeat(60));
        logger.info("INITIALIZING SEARCH ENGINE");
        logger.info("=".repeat(60));

        try {
            initializeBooks();
            logger.info("=".repeat(60));
            logger.info("✅ INITIALIZATION COMPLETE - {} books loaded", books.size());
            logger.info("=".repeat(60));
        } catch (Exception e) {
            logger.error("=".repeat(60));
            logger.error("❌ INITIALIZATION FAILED", e);
            logger.error("=".repeat(60));
            logger.warn("⚠️  Server will start but book functionality may be limited");
        }
    }

    private void initializeBooks() {
        long dbCount = bookRepository.count();

        if (dbCount == 0) {
            logger.info("📚 Database is empty. Loading books from JSON...");
            loadBooksFromJson();

            if (!books.isEmpty()) {
                logger.info("💾 Saving {} books to database...", books.size());
                bookRepository.saveAll(books.values());
                logger.info("✅ Saved {} books to database", books.size());
            }
        } else {
            logger.info("✅ Database already has {} books", dbCount);
            loadBooksIntoMemory();
        }
    }

    private void loadBooksFromJson() {
        try {
            // Load from classpath (resources folder)
            ClassPathResource resource = new ClassPathResource(JSON_FILE_PATH);

            if (!resource.exists()) {
                throw new JsonFileNotFoundException(
                        "JSON file not found in resources: " + JSON_FILE_PATH
                );
            }

            logger.debug("✅ Found JSON file at: {}", resource.getPath());

            ObjectMapper mapper = new ObjectMapper();

            try (InputStream inputStream = resource.getInputStream()) {
                Map<String, Map<String, Object>> jsonData = mapper.readValue(
                        inputStream,
                        new TypeReference<Map<String, Map<String, Object>>>() {}
                );

                logger.info("📖 Parsing {} book entries from JSON...", jsonData.size());

                books = new HashMap<>();
                int successCount = 0;
                int failCount = 0;

                for (Map.Entry<String, Map<String, Object>> entry : jsonData.entrySet()) {
                    try {
                        Map<String, Object> bookData = entry.getValue();
                        Book book = new Book();

                        // FIX: Get "id" from the map!
                        book.setId(((Number) bookData.get("id")).longValue());
                        book.setTitle((String) bookData.get("title"));
                        book.setAuthor((String) bookData.get("author"));
                        book.setFilePath((String) bookData.get("file_path"));
                        book.setSourceUrl((String) bookData.get("source_url"));

                        books.put(book.getId(), book);
                        successCount++;

                        if (successCount % 500 == 0) {
                            logger.info("  ... processed {} books", successCount);
                        }

                    } catch (Exception e) {
                        failCount++;
                        logger.warn("⚠️  Skipping malformed book entry: {} - {}",
                                entry.getKey(), e.getMessage());
                    }
                }

                logger.info("✅ Loaded {} books from JSON into memory", successCount);
                if (failCount > 0) {
                    logger.warn("⚠️  Skipped {} malformed entries", failCount);
                }
            }

        } catch (JsonFileNotFoundException e) {
            logger.error("❌ {}", e.getMessage());
            logger.error("💡 Make sure '{}' exists in src/main/resources/", JSON_FILE_PATH);
            throw e;
        } catch (IOException e) {
            logger.error("❌ Error reading JSON file", e);
            throw new InitializationException("Failed to read JSON file", e);
        }
    }

    private void loadBooksIntoMemory() {
        try {
            logger.info("📚 Loading books from database into memory...");
            books = new HashMap<>();

            for (Book book : bookRepository.findAll()) {
                books.put(book.getId(), book);
            }

            logger.info("✅ Loaded {} books into memory from database", books.size());
        } catch (Exception e) {
            logger.error("❌ Failed to load books from database", e);
            throw new InitializationException("Failed to load from database", e);
        }
    }

}
