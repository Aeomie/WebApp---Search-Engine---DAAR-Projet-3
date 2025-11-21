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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class StartUpInitializer {


    private static final Logger logger = LoggerFactory.getLogger(StartUpInitializer.class);

    @Getter
    private Map<Long, Book> books;

    private List<BookResponseDTO> bookResponseDTOList;
    private final BookRepository bookRepository;
    private final BookResponseRepository indexRepository;
    private final RestTemplate restTemplate;

    // Path relative to resources folder
    @Value("${books.catalog_path}")
    private String BOOKS_DATA_CATALOG_JSON_PATH;
    @Value("${books.index_path}")
    private String INDEX_TABLE_JSON_PATH;


    @Autowired
    public StartUpInitializer(List<BookResponseDTO> bookResponseDTOList, BookRepository bookRepository, BookResponseRepository indexRepository, RestTemplate restTemplate) {
        this.bookResponseDTOList = bookResponseDTOList;
        this.bookRepository = bookRepository;
        this.indexRepository = indexRepository;
        this.restTemplate = restTemplate;
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

            createBooksIndex();

        } else {
            logger.info("✅ Database already has {} books", dbCount);
            loadBooksIntoMemory();
        }
    }

    private void loadBooksFromJson() {
        try {
            // Load from classpath (resources folder)
            Resource resource = new FileSystemResource(BOOKS_DATA_CATALOG_JSON_PATH);

            if (!resource.exists()) {
                throw new JsonFileNotFoundException(
                        "JSON file not found in resources: " + BOOKS_DATA_CATALOG_JSON_PATH
                );
            }

            logger.debug("✅ Found JSON file at: {}", resource.getFile().getPath());

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
            logger.error("💡 Make sure '{}' exists in src/main/resources/", BOOKS_DATA_CATALOG_JSON_PATH);
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

    private void createBooksIndex(){


        try {
            String pythonUrl = "http://localhost:5001/indexAPI/build";

            List<BookResponseDTO> bookData = books.values().stream()
                    .map(book -> BookResponseDTO.builder()
                            .id(book.getId())
                            .title(book.getTitle())
                            .author(book.getAuthor())
                            .build())
                    .toList();

            Map<String, Object> requestBody = Map.of("books", bookData);

            Map<String, Object> response = restTemplate.postForObject(
                    pythonUrl,
                    requestBody,
                    Map.class
            );

            System.out.println("Success: " + response.get("message"));

            // 1️⃣ Clear previous in-memory data (important!)
            bookResponseDTOList.clear();

            // 2️⃣ Reload JSON from Python output
            loadIndexTableFromJson();

            // 3️⃣ Clear old DB entries
            indexRepository.deleteAll();

            // 4️⃣ Reinsert fresh data
            loadIndexTableToDatabase();

        }
        catch (HttpClientErrorException e) {
            // Catches 4xx errors (400, 409, etc.)
            int statusCode = e.getStatusCode().value();
            String responseBody = e.getResponseBodyAsString();

            if (statusCode == 409) {
                logger.warn("Indexing already in progress!");
                // Parse the error detail
                // responseBody = {"detail":"Indexing already in progress"}
            } else if (statusCode == 400) {
                logger.warn("Bad request: " + responseBody);
            }

        } catch (HttpServerErrorException e) {
            // Catches 5xx errors
            logger.warn("Server error: " + e.getMessage());

        } catch (RestClientException e) {
            // Catches connection errors
            logger.warn("Connection failed: " + e.getMessage());
        }
    }

    private void loadIndexTableFromJson() {
        try {
            Resource resource = new FileSystemResource(INDEX_TABLE_JSON_PATH);

            if (!resource.exists()) {
                throw new JsonFileNotFoundException("JSON file not found at: " + INDEX_TABLE_JSON_PATH);
            }

            ObjectMapper mapper = new ObjectMapper();

            try (InputStream inputStream = resource.getInputStream()) {

                Map<String, Map<String, Object>> jsonData =
                        mapper.readValue(inputStream,
                                new TypeReference<Map<String, Map<String, Object>>>() {});

                logger.info("📖 JSON entries: {}", jsonData.size());

                bookResponseDTOList.clear(); // to be safe

                int successCount = 0;
                int failCount = 0;

                for (var entry : jsonData.entrySet()) {
                    try {
                        Map<String, Object> bookData = entry.getValue();

                        BookResponseDTO dto = new BookResponseDTO(
                                ((Number) bookData.get("id")).longValue(),
                                (String) bookData.get("title"),
                                (String) bookData.get("author")
                        );

                        bookResponseDTOList.add(dto);
                        successCount++;

                        if (successCount % 500 == 0) {
                            logger.info("  ... processed {}", successCount);
                        }

                    } catch (Exception e) {
                        failCount++;
                        logger.warn("⚠️ Skipping malformed entry {}: {}", entry.getKey(), e.getMessage());
                    }
                }

                logger.info("✅ Loaded {} entries", successCount);
                if (failCount > 0)
                    logger.warn("⚠️ Skipped {} malformed entries", failCount);
            }

        } catch (JsonFileNotFoundException e) {
            logger.error("❌ {}", e.getMessage());
            logger.error("💡 Make sure '{}' exists ", INDEX_TABLE_JSON_PATH);
            throw e;
        } catch (IOException e) {
            logger.error("❌ Error reading JSON file", e);
            throw new InitializationException("Failed to read JSON file", e);
        }
    }

    private void loadIndexTableToDatabase() {
        int loadCount = 0;
        int loadSteps = 500;

        while (loadCount < bookResponseDTOList.size()) {

            int end = Math.min(loadCount + loadSteps, bookResponseDTOList.size());
            List<BookResponseDTO> loadList = bookResponseDTOList.subList(loadCount, end);

            indexRepository.saveAll(loadList);
            logger.info("📦 Saved {} entries to DB ({}–{})",
                    loadList.size(), loadCount, end);

            loadCount = end;
        }
        logger.info("✅ Database load completed.");
    }

}
