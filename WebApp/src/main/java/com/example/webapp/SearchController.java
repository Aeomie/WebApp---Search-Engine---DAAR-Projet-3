package com.example.webapp;


import com.example.webapp.DTOS.BookResponseDTO;
import com.example.webapp.DTOS.GenerateWordDTO;
import com.example.webapp.DTOS.SimpleSearchDTO;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("api/v1/search")
public class SearchController {

    private final SearchService searchService;

    public SearchController(SearchService searchService, BookRepository bookRepository) {
        this.searchService = searchService;
    }

    @PostMapping("/searchByTitle")
    public List<BookResponseDTO> searchTitle(
            @RequestBody SimpleSearchDTO simpleSearchDTO
    ){
        return searchService.searchByTitle(simpleSearchDTO.getPattern());
    }
    @PostMapping("/searchByTC")
    public List<BookResponseDTO> searchByTitleContent(
            @RequestBody GenerateWordDTO generateWordDTO
    ){
        /*
        Pattern here is a regex
         */
        return searchService.searchByTitleContent(generateWordDTO.getPattern(),
                generateWordDTO.getMaxWords(), generateWordDTO.getMaxLength());
    }
}
