from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from indexService import indexService
import asyncio
from concurrent.futures import ThreadPoolExecutor

class IndexRequest(BaseModel):
    index_type: str

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
indexing_thread_pool = ThreadPoolExecutor(max_workers=1)

@app.get("/openapi.json")
def custom_openapi():
    return app.openapi()

def run_indexing(index_type: str, num_processes: int = 4):
    """Synchronous indexing function to run in thread"""
    try:
        indexing_service.build_index_parallel(num_processes, index_type)
    except Exception as e:
        print(f"ERROR IN BACKGROUND INDEXING: {e}")
        indexing_service.indexing_status[index_type]['is_indexing'] = False
        indexing_service.indexing_status[index_type]['status'] = 'failed'

@app.post("/indexAPI/build")
async def build_index(request: IndexRequest):
    """Build index from catalog in the background"""
    try:
        if indexing_service.indexing_status[request.index_type]['is_indexing']:
            raise HTTPException(status_code=409, detail=f"{request.index_type} indexing already in progress")

        if request.index_type not in ["T", "TC"]:
            raise HTTPException(status_code=400, detail="index_type must be 'T' or 'TC'")

        # Run in dedicated indexing thread (no asyncio.run needed!)
        loop = asyncio.get_running_loop()
        loop.run_in_executor(indexing_thread_pool, run_indexing, request.index_type, 4)

        return {
            'message': f'Indexing started (type: {request.index_type})',
            'index_type': request.index_type
        }
    except HTTPException:
        raise
    except Exception as e:
        print("ERROR IN BUILD_INDEX:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indexAPI/status", response_model=IndexStatus)
async def get_index_status(index_type: str = "T") -> IndexStatus:
    """Get current indexing status for specific index type"""
    if index_type not in ["T", "TC"]:
        raise HTTPException(status_code=400, detail="index_type must be 'T' or 'TC'")
    return IndexStatus(**indexing_service.indexing_status[index_type])

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