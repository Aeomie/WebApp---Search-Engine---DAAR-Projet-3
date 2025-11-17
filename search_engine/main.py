# main.py
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from engine import engine_text

from functools import lru_cache
from pydantic import BaseModel
from typing import List


class SearchRequest(BaseModel):
    pattern: str
    texts: List[str]  # can handle one or multiple titles
    verbose: bool = False


class AdvancedSearchRequest(BaseModel):
    pattern: str
    book_ids: List[int]  # the books to load
    verbose: bool = False


app = FastAPI()

@app.post("/searchRegex")
def search_regex(pattern: str, text: str, verbose: bool = False):
    result = engine_text(pattern, text, mode="regex", verbose=verbose)
    return result

@app.post("/searchBoyer")
def search_boyer(request: SearchRequest):
    results = []
    for text in request.texts:
        engine_result = engine_text(
            request.pattern,
            text,
            mode="boyer",
            verbose=request.verbose  # always get total_count & indexes
        )
        if request.verbose:
            results.append({
                "text": text,
                "total_count": engine_result.get("total_count", 0),
                "indexes": engine_result.get("indexes", [])
            })
        else:
            results.append({
                "text": text,
                "total_count": engine_result.get("total_count", 0)
            })
    return {"results": results}


def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

@lru_cache(maxsize=128)
def load_book_text(book_id: int) -> str:
    Books_location = "../books/"
    file_path = f"{Books_location}{book_id}.txt"

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Book {book_id} not found"
    except Exception as e:
        return f"Error reading book {book_id}: {str(e)}"


@app.post("/advancedSearch")
def search_advanced(request: AdvancedSearchRequest):
    BATCH_SIZE = 200
    results = []

    # Process book_ids in chunks of 200
    for batch_ids in chunks(request.book_ids, BATCH_SIZE):

        # load batch texts
        texts = {}
        for book_id in batch_ids:
            text = load_book_text(book_id)

            if text.startswith("Error"):
                results.append({
                    "book_id": book_id,
                    "error": text
                })
                continue

            texts[book_id] = text

        # run regex on each loaded text
        for book_id, text in texts.items():
            engine_result = engine_text(
                request.pattern,
                text,
                mode="regex",
                verbose=request.verbose
            )

            entry = {
                "book_id": book_id,
                "total_count": engine_result.get("total_count", 0)
            }

            if request.verbose:
                entry["indexes"] = engine_result.get("indexes", [])

            results.append(entry)

    return {"results": results}


def regex_worker(args):
    book_id, text, pattern, verbose = args

    try:
        from engine import engine_text
        result = engine_text(pattern, text, mode="regex", verbose=verbose)

        entry = {
            "book_id": book_id,
            "total_count": result.get("total_count", 0)
        }

        if verbose:
            entry["indexes"] = result.get("indexes", [])

        return entry

    except Exception as e:
        # Crash-safe return
        return {
            "book_id": book_id,
            "error": f"Worker error: {str(e)}"
        }

@app.post("/advancedSearchParallel")
def search_advanced_parallel(request: AdvancedSearchRequest):

    BATCH_SIZE = 200
    results = []

    # Loop on book_ids by batches of 200
    for batch_ids in chunks(request.book_ids, BATCH_SIZE):

        # Prepare work units
        tasks = []
        for book_id in batch_ids:
            text = load_book_text(book_id)

            if text.startswith("Error"):
                results.append({"book_id": book_id, "error": text})
                continue

            tasks.append((book_id, text, request.pattern, request.verbose))

        # Run parallel workers
        with ProcessPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(regex_worker, tasks))

        results.extend(batch_results)

    return {"results": results}