package com.example.webapp;


import com.example.webapp.BookIndex.BookIndexContentEntity;
import com.example.webapp.BookIndex.BookIndexContentRepository;
import com.example.webapp.BookIndex.BookIndexEntity;
import com.example.webapp.BookIndex.BookIndexRepository;
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
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
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
    private List<BookIndexContentEntity>  bookIndexContentEntities;

    private final BookRepository bookRepository;
    private final BookIndexRepository indexRepository;
    private final BookIndexContentRepository indexContentRepository;
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

    @Value("${jaccard_status_api}")
    private String JACCARD_STATUS_API;

    @Value("${jaccard_build_api}")
    private String BUILD_JACARD_API;

    @Value("${jaccard_run_pagerank_api}")
    private String GENERATE_PAGERANK_SCORES_API;

    @Value("${jaccard_load_api}")
    private String LOAD_JACCARD_API;

    @Value("${jaccard_password}")
    private String JACCARD_PASSWORD;

    @Autowired
    public StartUpInitializer(BookRepository bookRepository, BookIndexRepository indexRepository,
                              BookIndexContentRepository indexContentRepository,
                              RestTemplate restTemplate) {
        this.bookRepository = bookRepository;
        this.indexRepository = indexRepository;
        this.indexContentRepository = indexContentRepository;
        this.restTemplate = restTemplate;
        this.books = new HashMap<>();
        this.bookIndexEntities = new ArrayList<>();
        this.bookIndexContentEntities = new ArrayList<>();
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


    private void waitforIndexingCompletion(String indexType) throws InterruptedException {
        while (true) {
            // Add index_type query parameter
            String statusUrl = STATUS_INDEX_API + "?index_type=" + indexType;
            Map<String, Object> status = restTemplate.getForObject(statusUrl, Map.class);
            String statusStr = (String) status.get("status");
            if ("completed".equals(statusStr)) {
                break;
            }
            Thread.sleep(500);
        }
    }

    private void createBooksIndex(){

        try {

            if ( fileExists(INDEX_TITLE_TABLE_JSON_PATH) && fileExists(INDEX_TITLE_CONTENT_TABLE_JSON_PATH) ){

            }
            else{
                String indexType = "T";


                // To Build Title Index
                Map<String, Object> requestBodyTitle = Map.of("index_type", indexType);
                restTemplate.postForObject(BUILD_INDEX_API, requestBodyTitle, Map.class);
                logger.info("Title index build started");
                waitforIndexingCompletion(indexType);
                logger.info("Title index completed");

                indexType = "TC";

                // to Build Title Content Index
                Map<String, Object> requestBodyTC = Map.of("index_type", indexType);
                restTemplate.postForObject(BUILD_INDEX_API, requestBodyTC, Map.class);
                logger.info("Title+Content index build started");
                waitforIndexingCompletion(indexType);
                logger.info("Title+Content index completed");

                System.out.println("Indexing completed. Reading JSON...");
            }

            // 1️⃣ Clear previous in-memory data (important!)
            bookIndexEntities.clear();

            // 2️⃣ Reload JSON from Python output
            loadIndexTableFromJson();

            // 3️⃣ Clear old DB entries
            indexRepository.deleteAll();

            // 4️⃣ Reinsert fresh data
            loadIndexTableToDatabase();

            // Initialise Jaccard
            initJaccardService();

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
        loadIndexFromFile(INDEX_TITLE_TABLE_JSON_PATH, bookIndexEntities, "Title", BookIndexEntity.class);
        loadIndexFromFile(INDEX_TITLE_CONTENT_TABLE_JSON_PATH, bookIndexContentEntities, "Title+Content", BookIndexContentEntity.class);
    }

    private boolean fileExists(String filePath) {
        /*
        Function Used in the test period
         */
        Resource resource = new FileSystemResource(filePath);
        return resource.exists();
    }
    private <T> void loadIndexFromFile(String filePath, List<T> targetList, String indexType, Class<T> entityClass) {
        try {
            Resource resource = new FileSystemResource(filePath);

            if (!resource.exists()) {
                throw new JsonFileNotFoundException("JSON file not found at: " + filePath);
            }

            ObjectMapper mapper = new ObjectMapper();

            try (InputStream inputStream = resource.getInputStream();
                 InputStreamReader reader = new InputStreamReader(inputStream, StandardCharsets.UTF_8)) {

                Map<String, List<Map<String, Object>>> jsonData =
                        mapper.readValue(reader,
                                new TypeReference<Map<String, List<Map<String, Object>>>>() {});

                logger.info("📖 {} Index - JSON entries: {}", indexType, jsonData.size());

                targetList.clear();

                int successCount = 0;
                int failCount = 0;

                for (var entry : jsonData.entrySet()) {
                    String word = entry.getKey();
                    List<Map<String, Object>> bookList = entry.getValue();

                    for (Map<String, Object> bookData : bookList) {
                        try {
                            T entity = entityClass.getDeclaredConstructor().newInstance();

                            // Use reflection to set fields
                            entityClass.getMethod("setWord", String.class).invoke(entity, word);
                            entityClass.getMethod("setBookId", Long.class).invoke(entity, ((Number) bookData.get("book_id")).longValue());
                            entityClass.getMethod("setFrequency", Integer.class).invoke(entity, ((Number) bookData.get("frequency")).intValue());

                            targetList.add(entity);
                            successCount++;

                            if (successCount % 500 == 0) {
                                logger.info("  ... {} Index processed {}", indexType, successCount);
                            }

                        } catch (Exception e) {
                            failCount++;
                            logger.warn("⚠️ {} Index - Skipping malformed entry {}: {}", indexType, word, e.getMessage());
                        }
                    }
                }

                logger.info("✅ {} Index - Loaded {} entries", indexType, successCount);
                if (failCount > 0)
                    logger.warn("⚠️ {} Index - Skipped {} malformed entries", indexType, failCount);
            }
        } catch (JsonFileNotFoundException e) {
            logger.error("❌ {} Index - {}", indexType, e.getMessage());
            logger.error("💡 Make sure '{}' exists ", filePath);
            throw e;
        } catch (IOException e) {
            logger.error("❌ {} Index - Error reading JSON file", indexType, e);
            throw new InitializationException("Failed to read JSON file: " + filePath, e);
        }
    }

    private void loadIndexTableToDatabase() {
        loadIndexToDatabase(bookIndexEntities, indexRepository, "Title");
        loadIndexToDatabase(bookIndexContentEntities, indexContentRepository, "Title+Content");
    }

    private <T> void loadIndexToDatabase(List<T> entities, JpaRepository<T, ?> repository, String indexType) {
        int loadCount = 0;
        int loadSteps = 500;

        logger.info("📤 Loading {} Index to database...", indexType);

        while (loadCount < entities.size()) {
            int end = Math.min(loadCount + loadSteps, entities.size());
            List<T> loadList = entities.subList(loadCount, end);

            repository.saveAll(loadList);
            logger.info("📦 {} Index - Saved {} entries to DB ({}–{})",
                    indexType, loadList.size(), loadCount, end);

            loadCount = end;
        }

        logger.info("✅ {} Index - Database load completed ({} total entries)", indexType, entities.size());
    }


    private void waitForJaccardField(String field, Object expectedValue, long intervalMs, int MaxTime) throws InterruptedException {
        int maxRetries = (int) (MaxTime/ intervalMs);
        int retries = 0;
        String statusUrl = JACCARD_STATUS_API;

        while (true) {
            Map<String, Object> status = restTemplate.getForObject(statusUrl, Map.class);
            if (status == null) throw new RuntimeException("Failed to get Jaccard status");

            Object value = status.get(field);
            if (expectedValue.equals(value)) break;

            Thread.sleep(intervalMs);
            retries++;
            if (retries >= maxRetries)
                throw new RuntimeException("Timeout waiting for " + field + " to reach " + expectedValue);
        }
    }

    private void initJaccardService() {
        System.out.println("DEBUG: Password being sent: " + JACCARD_PASSWORD );
        Map<String, Object> requestBody = Map.of("password", JACCARD_PASSWORD);

        try {
            // Try to load existing graph + pagerank
            restTemplate.postForObject(LOAD_JACCARD_API, requestBody, Map.class);
            waitForJaccardField("loaded", true, 200, 300000); // 5 mns max
            System.out.println("Jaccard graph & PageRank Scores loaded successfully.");
        } catch (Exception e) {
            System.out.println("Failed to load Jaccard graph. Rebuilding...");
            try {
                restTemplate.postForObject(BUILD_JACARD_API, requestBody, Map.class);
                waitForJaccardField("status", "completed", 300, 300000); // 5 mns max
                System.out.println("Jaccard graph rebuilt successfully.");

                try {
                    restTemplate.postForObject(GENERATE_PAGERANK_SCORES_API, requestBody, Map.class);
                    waitForJaccardField("rank_status", "completed", 500, 300000); // 5 mns max
                    System.out.println("PageRank Scores generated successfully.");
                } catch (Exception ex) {
                    System.out.println("Failed to generate PageRank Scores.");
                }
            } catch (Exception buildError) {
                System.err.println("FATAL: Could not build Jaccard graph, Either Wrong Password or Build Failed.");
            }
        }
    }


}
