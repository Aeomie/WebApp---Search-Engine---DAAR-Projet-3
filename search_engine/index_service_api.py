# main.py
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from engine import engine_text
import asyncio
from functools import lru_cache
from pydantic import BaseModel
from typing import List, Optional
from indexService import indexService, Book
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from fastapi import HTTPException
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
build_executor = ProcessPoolExecutor(max_workers=4)

# Global service instance
indexing_service = indexService()

@app.post("/indexAPI/build")
async def build_index(request: IndexBuildRequest):
    """
    Build index from books in the background
    """
    try:
        if indexing_service.indexing_status['is_indexing']:
            raise HTTPException(status_code=409, detail="Indexing already in progress")

        if not request.books:
            raise HTTPException(status_code=400, detail="No books provided")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(build_executor, indexing_service.build_index, request.books)

        return {
            'message': 'Indexing started',
            'total_books': len(request.books)
        }

    except Exception as e:
        print("ERROR IN BUILD_INDEX:", e)
        raise HTTPException(status_code=500, detail=str(e))


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