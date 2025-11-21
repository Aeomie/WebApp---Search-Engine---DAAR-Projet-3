# main.py
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from engine import engine_text

from functools import lru_cache
from pydantic import BaseModel
from typing import List, Optional
from indexService import indexService, Book


class IndexBuildRequest(BaseModel):
    books: List[Book]
class IndexStatus(BaseModel):
    is_indexing: bool
    progress: int  # Changed from float to int to match usage
    total_books: int
    indexed_books: int
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


app = FastAPI()


# Global service instance
indexing_service = indexService()

@app.post("/indexAPI/build")
async def build_index(request: IndexBuildRequest):
    """
    Build index from books in the background
    """
    if indexing_service.indexing_status['is_indexing']:
        raise HTTPException(status_code=409, detail="Indexing already in progress")

    if not request.books:
        raise HTTPException(status_code=400, detail="No books provided")

    # Need to await this since it's async
    await indexing_service.build_index_async(request.books)

    return {
        'message': 'Indexing started',
        'total_books': len(request.books)
    }


@app.get("/indexAPI/status", response_model=IndexStatus)
async def get_index_status() -> IndexStatus:
    """
    Get current indexing status
    """
    return IndexStatus(**indexing_service.indexing_status)


@app.get("/indexAPI/stats")
async def get_stats():
    """Get indexing statistics"""
    return {
        'total_books': len(indexing_service.indexing_status.get('total_books', 0)),
        'unique_words': len(indexing_service.indexing_dict),
        'indexing_status': indexing_service.indexing_status
    }