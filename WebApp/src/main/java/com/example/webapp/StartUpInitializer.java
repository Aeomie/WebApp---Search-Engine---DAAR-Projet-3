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
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class StartUpInitializer {


    private static final Logger logger = LoggerFactory.getLogger(StartUpInitializer.class);

    @Getter
    private Map<Long, Book> books;

    private List<BookIndexEntity> bookIndexEntities;
    private final BookRepository bookRepository;
    private final BookIndexRepository indexRepository;
    private final RestTemplate restTemplate;

    // Path relative to resources folder
    @Value("${books.catalog_path}")
    private String BOOKS_DATA_CATALOG_JSON_PATH;
    @Value("${books.index_title_path}")
    private String INDEX_TITLE_TABLE_JSON_PATH;

    @Value("${books.index_title_content_path}")
    private String INDEX_TITLE_CONTENT_TABLE_JSON_PATH;

    @Value("${build_index_api}")
    private String BUILD_INDEX_API;

    @Value("${index_status_api}")
    private String STATUS_INDEX_API;
    @Autowired
    public StartUpInitializer(BookRepository bookRepository, BookIndexRepository indexRepository, RestTemplate restTemplate) {
        this.bookRepository = bookRepository;
        this.indexRepository = indexRepository;
        this.restTemplate = restTemplate;
        this.books = new HashMap<>();
        this.bookIndexEntities = new ArrayList<>();
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


    private void waitforIndexingCompletion() throws InterruptedException {
        while (true) {
            Map<String, Object> status = restTemplate.getForObject(STATUS_INDEX_API, Map.class);
            String statusStr = (String) status.get("status");
            if ("completed".equals(statusStr)) {
                break;
            }
            Thread.sleep(300);
        }
    }
    private void createBooksIndex(){

        try {

            Map<String, Object> requestBodyTitle = Map.of("index_type", "T");
            restTemplate.postForObject(BUILD_INDEX_API, requestBodyTitle, Map.class);
            logger.info("Title index build started");
            waitforIndexingCompletion();
            logger.info("Title index completed");

//            Map<String, Object> requestBodyTC = Map.of("index_type", "TC");
//            restTemplate.postForObject(BUILD_INDEX_API, requestBodyTC, Map.class);
//            logger.info("Title+Content index build started");
//            waitforIndexingCompletion();
//            logger.info("Title+Content index completed");

            System.out.println("Indexing completed. Reading JSON...");

            // 1️⃣ Clear previous in-memory data (important!)
            bookIndexEntities.clear();

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
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    private void loadIndexTableFromJson() {
        try {
            Resource resource = new FileSystemResource(INDEX_TITLE_TABLE_JSON_PATH);

            if (!resource.exists()) {
                throw new JsonFileNotFoundException("JSON file not found at: " + INDEX_TITLE_TABLE_JSON_PATH);
            }

            ObjectMapper mapper = new ObjectMapper();

            try (InputStream inputStream = resource.getInputStream()) {

                Map<String, List<Map<String, Object>>> jsonData =
                        mapper.readValue(inputStream,
                                new TypeReference<Map<String, List<Map<String, Object>>>>() {});

                logger.info("📖 JSON entries: {}", jsonData.size());

                bookIndexEntities.clear(); // to be safe

                int successCount = 0;
                int failCount = 0;

                for (var entry : jsonData.entrySet()) {
                    String word = entry.getKey();
                    List<Map<String, Object>> bookList = (List<Map<String, Object>>) entry.getValue();

                    for (Map<String, Object> bookData : bookList) {
                        try {
                            BookIndexEntity entity = new BookIndexEntity();
                            entity.setWord(word);
                            entity.setBookId(((Number) bookData.get("book_id")).longValue());
                            entity.setFrequency(((Number) bookData.get("frequency")).intValue());

                            bookIndexEntities.add(entity);
                            successCount++;

                            if (successCount % 500 == 0) {
                                logger.info("  ... processed {}", successCount);
                            }

                        } catch (Exception e) {
                            failCount++;
                            logger.warn("⚠️ Skipping malformed entry {}: {}", word, e.getMessage());
                        }
                    }
                }

                logger.info("✅ Loaded {} entries", successCount);
                if (failCount > 0)
                    logger.warn("⚠️ Skipped {} malformed entries", failCount);
            }

        } catch (JsonFileNotFoundException e) {
            logger.error("❌ {}", e.getMessage());
            logger.error("💡 Make sure '{}' exists ", INDEX_TITLE_TABLE_JSON_PATH);
            throw e;
        } catch (IOException e) {
            logger.error("❌ Error reading INDEX JSON file", e);
            throw new InitializationException("Failed to read JSON file", e);
        }
    }

    private void loadIndexTableToDatabase() {
        int loadCount = 0;
        int loadSteps = 500;

        while (loadCount < bookIndexEntities.size()) {

            int end = Math.min(loadCount + loadSteps, bookIndexEntities.size());
            List<BookIndexEntity> loadList = bookIndexEntities.subList(loadCount, end);

            indexRepository.saveAll(loadList);
            logger.info("📦 Saved {} entries to DB ({}–{})",
                    loadList.size(), loadCount, end);

            loadCount = end;
        }
        logger.info("✅ Database load completed.");
    }

}
