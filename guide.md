# API Endpoints Documentation

**Note:** All endpoints return a list of `BookResponseDTO` objects with the following structure:

```
[
  {
    "id": 28675,
    "title": "Red Men and White by Owen Wister",
    "author": "Read or download for free"
  }
]
```

## 2.1 Search by Title

**Endpoint:** `POST http://localhost:8080/api/v1/search/searchByTitle`

**Request Body (JSON):**
```
{
  "pattern": "h"
}
```

**Response:** `List[BookResponseDTO]`

---

## 2.2 Search by Title + Content

**Endpoint:** `POST http://localhost:8080/api/v1/search/searchByTC`

**Request Body (JSON):**
```
{
  "pattern": "a+",
  "maxWords": 100,
  "maxLength": 500
}
```

**Response:** `List[BookResponseDTO]`

---

## 2.3 Class Search (Advanced / Word Generator)

**Endpoint:** `POST http://localhost:8080/api/v1/search/classSearch`

**Request Body (JSON):**
```
{
  "pattern": "h",
  "maxWords": 1000,
  "maxLength": 5000
}
```

**Response:** `List[BookResponseDTO]`

Returns books ranked by PageRank or centrality (Jaccard) scores.

---

## 2.4 Suggestion Search

**Endpoint:** `GET http://localhost:8080/api/v1/search/suggestionSearch?top_n=10`

**Parameters:**
- `top_n` → number of suggestions to return

**Response:** `List[BookResponseDTO]`

Returns books related to the last search results, sorted by similarity.

---

## Notes / Best Practices

- All results share the same type (`BookResponseDTO`). You can safely handle them in your frontend or backend in the same way.
- `suggestionSearch` depends on the last search call, so always call a search endpoint before fetching suggestions.
- `classSearch` can return many results; consider limiting the IDs stored for suggestions (e.g., top 10).
- Use `top_n` in `suggestionSearch` to control the number of results returned.
- If the API hangs or a Jaccard/Index service is rebuilding, the endpoint might take a few seconds—consider using wait loops like `waitForJaccardField`.
```

Copy everything from the first line (starting with `# API Endpoints Documentation`) to the last line. This format ensures all JSON examples with curly braces `{}` are properly contained within code blocks, making them display correctly in any markdown viewer or documentation system.[1][2]
