from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from indexService import indexService, Book


class IndexBuildRequest(BaseModel):
    books: List[Book]


class IndexStatus(BaseModel):
    is_indexing: bool
    progress: int
    total_books: int
    indexed_books: int
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


app = FastAPI()

# Global service instance
indexing_service = indexService()


async def run_indexing(books: List[Book], num_processes: int = 4):
    """Background task to run indexing"""
    try:
        await indexing_service.build_index_parallel(books, num_processes)
    except Exception as e:
        print(f"ERROR IN BACKGROUND INDEXING: {e}")
        indexing_service.indexing_status['is_indexing'] = False
        indexing_service.indexing_status['status'] = 'failed'


@app.post("/indexAPI/build")
async def build_index(request: IndexBuildRequest, background_tasks: BackgroundTasks):
    """
    Build index from books in the background
    """
    try:
        if indexing_service.indexing_status['is_indexing']:
            raise HTTPException(status_code=409, detail="Indexing already in progress")

        if not request.books:
            raise HTTPException(status_code=400, detail="No books provided")

        # Add indexing task to background
        background_tasks.add_task(run_indexing, request.books, 4)

        return {
            'message': 'Indexing started',
            'total_books': len(request.books)
        }
    except HTTPException:
        raise
    except Exception as e:
        print("ERROR IN BUILD_INDEX:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/indexAPI/status", response_model=IndexStatus)
async def get_index_status() -> IndexStatus:
    """
    Get current indexing status - always responsive
    """
    return IndexStatus(**indexing_service.indexing_status)


@app.get("/indexAPI/stats")
async def get_stats():
    """Get indexing statistics - always responsive"""
    return {
        'total_books': indexing_service.indexing_status.get('total_books', 0),
        'unique_words': len(indexing_service.indexing_dict),
        'indexing_status': indexing_service.indexing_status
    }


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}
