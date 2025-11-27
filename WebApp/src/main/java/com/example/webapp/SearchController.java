package com.example.webapp;


import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("api/v1/search")
public class SearchController {

    private final SearchService searchService;

    public SearchController(SearchService searchService, BookRepository bookRepository) {
        this.searchService = searchService;
    }

    @PostMapping("/Boyer")
    public List<BookResponseDTO> searchBoyer(
            @RequestBody SimpleSearchDTO simpleSearchDTO
    ){
        return searchService.searchBoyer(simpleSearchDTO.getPattern(),
                simpleSearchDTO.isVerbose());
    }

    @PostMapping("/searchByTitle")
    public List<BookResponseDTO> searchTitle(
            @RequestParam String pattern
    ){
        return searchService.searchByTitle(pattern);
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
