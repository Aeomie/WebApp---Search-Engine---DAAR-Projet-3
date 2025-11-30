package com.example.webapp;


import com.example.webapp.BookIndex.BookIndexContentEntity;
import com.example.webapp.BookIndex.BookIndexContentRepository;
import com.example.webapp.BookIndex.BookIndexEntity;
import com.example.webapp.BookIndex.BookIndexRepository;
import com.example.webapp.DTOS.BookResponseDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

import org.springframework.web.client.RestTemplate;

@Service
public class SearchService {

    private final BookRepository bookRepository;
    private final BookIndexRepository bookIndexRepository;
    private final BookIndexContentRepository bookIndexContentRepository;
    private final RestTemplate restTemplate;
    @Value("${generate_words_api}")
    private String WORD_GENERATOR_API;

    @Value("${jacaard_pagerank_score_api}")
    private String GET_PAGERANK_SCORE_API;

    @Value("${jacaard_similarity_score_api}")
    private String GET_SIMILARITY_SCORE_API;
    private Set<Long> last_book_ids;
    private final int SUGGESTION_LIMIT = 10;



    public SearchService(BookRepository bookRepository, BookIndexRepository bookIndexRepository, BookIndexContentRepository bookIndexContentRepository, StartUpInitializer startupInitializer, RestTemplate restTemplate) {
        this.bookRepository = bookRepository;
        this.bookIndexRepository = bookIndexRepository;
        this.bookIndexContentRepository = bookIndexContentRepository;
        this.restTemplate = restTemplate;
        this.last_book_ids = new HashSet<>();
    }


    public List<BookResponseDTO> searchByTitle(String pattern) {
        /*
        Get all Words , Parse them into Ids , Get all Books after & return BookResponseDTO
         */
        List<BookIndexEntity> indexEntries = bookIndexRepository.findAllByWordContains(pattern);

        List<Long> bookIds = indexEntries.stream()
                .map(BookIndexEntity::getBookId)
                .toList();

        // Limit last_book_ids
        this.last_book_ids = bookIds.stream()
                .limit(SUGGESTION_LIMIT)
                .collect(Collectors.toSet());

        List<Book> books = bookRepository.findAllById(bookIds);

        return books.stream()
                .map(this::toDTO)
                .toList();
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

        // Limit last_book_ids
        this.last_book_ids = bookIds.stream()
                .limit(SUGGESTION_LIMIT)
                .collect(Collectors.toSet());

        // 6️⃣ Fetch all books in a single query
        List<Book> books = bookRepository.findAllById(bookIds);

        // 7️⃣ Map to BookResponseDTO
        return books.stream()
                .map(this::toDTO)
                .toList();
    }

    public List<BookResponseDTO> ClassingSearch(String regex,
                                                Integer maxWords, Integer maxLength) {
        // 1️⃣ Generate words
        Map<String, Object> requestBody = Map.of(
                "pattern", regex,
                "max_words", maxWords != null ? maxWords : 50,
                "max_length", maxLength != null ? maxLength : 50
        );

        Map<String, Object> response = restTemplate.postForObject(
                WORD_GENERATOR_API,
                requestBody,
                Map.class
        );

        List<String> generatedWords = (List<String>) response.get("generated_words");
        if (generatedWords == null || generatedWords.isEmpty()) return Collections.emptyList();

        // 2️⃣ Collect index entries
        Set<BookIndexContentEntity> indexEntriesSet = new HashSet<>();
        for (String word : generatedWords) {
            indexEntriesSet.addAll(bookIndexContentRepository.findAllByWordContains(word));
        }

        List<BookIndexContentEntity> indexEntries = new ArrayList<>(indexEntriesSet);
        if (indexEntries.isEmpty()) return Collections.emptyList();

        List<Long> bookIds = indexEntries.stream()
                .map(BookIndexContentEntity::getBookId)
                .distinct()
                .toList();

        // 3️⃣ Fetch PageRank scores
        List<Integer> bookIdsInt = bookIds.stream().map(Long::intValue).toList();
        Map<String, Object> pagerankResponse = restTemplate.getForObject(
                GET_PAGERANK_SCORE_API + "?book_ids=" + bookIdsInt.stream()
                        .map(String::valueOf)
                        .collect(Collectors.joining("&book_ids=")),
                Map.class
        );

        Map<Long, Double> pagerankScores = new HashMap<>();
        for (Map.Entry<String, Object> entry : pagerankResponse.entrySet()) {
            Long bookId = Long.valueOf(entry.getKey());
            Double score = ((Number) entry.getValue()).doubleValue();
            pagerankScores.put(bookId, score);
        }

        // 4️⃣ Sort all bookIds by PageRank once
        List<Long> sortedBookIds = bookIds.stream()
                .sorted((b1, b2) -> Double.compare(
                        pagerankScores.getOrDefault(b2, 0.0),
                        pagerankScores.getOrDefault(b1, 0.0)
                ))
                .toList();

        // 5️⃣ Update last_book_ids with top SUGGESTION_LIMIT
        this.last_book_ids = sortedBookIds.stream()
                .limit(SUGGESTION_LIMIT)
                .collect(Collectors.toSet());

        // 6️⃣ Fetch books and preserve order
        List<Book> books = bookRepository.findAllById(sortedBookIds);
        Map<Long, Book> bookMap = books.stream()
                .collect(Collectors.toMap(Book::getId, b -> b));

        return sortedBookIds.stream()
                .map(bookMap::get)
                .filter(Objects::nonNull)
                .map(this::toDTO)  // Use helper
                .toList();
    }

    public List<BookResponseDTO> suggestionSearch(int top_n) {
        // Map to store bookId -> max similarity across all last_book_ids
        Map<Long, Double> similarBooksMap = new HashMap<>();

        for (Long id : last_book_ids) {
            Map<String, Object> requestBody = Map.of(
                    "book_id", id,
                    "top_n", top_n
            );

            // Call Python API
            Map<String, Object> response = restTemplate.getForObject(
                    GET_SIMILARITY_SCORE_API + id + "?top_n=" + top_n,
                    Map.class
            );

            // Extract similar_books
            List<Map<String, Object>> similarBooks = (List<Map<String, Object>>) response.get("similar_books");
            if (similarBooks == null) continue;

            // Add/update bookId -> similarity
            for (Map<String, Object> entry : similarBooks) {
                Long bookId = ((Number) entry.get("book_id")).longValue();
                Double similarity = ((Number) entry.get("similarity")).doubleValue();

                // Keep the max similarity if the book appears multiple times
                similarBooksMap.merge(bookId, similarity, Math::max);
            }
        }

        if (similarBooksMap.isEmpty()) {
            return Collections.emptyList();
        }

        // Sort bookIds by similarity descending and take only top_n
        List<Long> sortedBookIds = similarBooksMap.entrySet().stream()
                .sorted(Map.Entry.<Long, Double>comparingByValue().reversed())
                .limit(top_n)
                .map(Map.Entry::getKey)
                .toList();

        // Fetch all books in one query
        List<Book> books = bookRepository.findAllById(sortedBookIds);

        // Preserve the order of sortedBookIds
        Map<Long, Book> bookById = books.stream()
                .collect(Collectors.toMap(Book::getId, b -> b));

        return sortedBookIds.stream()
                .map(bookById::get)
                .filter(Objects::nonNull)
                .map(this::toDTO)  // Use helper
                .toList();
    }


    public BookResponseDTO toDTO(Book book) {
        return BookResponseDTO.builder()
                .id(book.getId())
                .title(book.getTitle())
                .author(book.getAuthor())
                .sourceUrl(book.getSourceUrl())  // ← Map from entity
                .imgUrl(book.getImgUrl())        // ← Map from entity
                .build();
    }
}
