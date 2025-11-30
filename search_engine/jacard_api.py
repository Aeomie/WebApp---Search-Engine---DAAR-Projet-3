from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from JaccardGraph import JaccardGraph
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from fastapi import Query
from typing import List
from contextlib import asynccontextmanager

# --- Password request model ---
class BuildPasswordRequest(BaseModel):
    password: str

# --- Progress model ---
class JacardStatus(BaseModel):
    total_pairs: int
    processed_pairs: int
    is_building: bool
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_ranking: bool
    rank_status: str
    rank_start_time: Optional[str] = None
    rank_end_time: Optional[str] = None

"""
Order has to be set up like this
Load jacard , startup Checks if graph and pagerank exist
If not exist build graph from inverted index
Then compute pagerank
Save both graph and pagerank
"""
# --- Global service instance ---
jacard_graph = JaccardGraph(threshold=0.1, max_frac=0.2)
jacard_thread_pool = ThreadPoolExecutor(max_workers=1)

# --- StartUp Event ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - runs on startup and shutdown"""
    # Startup: Load graph and PageRank
    print("\n=== Starting Jaccard Graph Service ===")

    graph_loaded = jacard_graph.load_graph()
    pagerank_loaded = jacard_graph.load_pagerank()

    if graph_loaded and pagerank_loaded:
        print(" Service ready with pre-computed graph and PageRank")
    elif graph_loaded:
        print(" Graph loaded but PageRank not found")
    elif pagerank_loaded:
        print(" PageRank loaded but graph not found")
    else:
        print(" No pre-computed data found. Use /jacardAPI/build to create graph")

    print("=" * 40 + "\n")

    yield  # Server runs here

    # Shutdown: Cleanup code (optional)
    print("\n=== Shutting down Jaccard Graph Service ===")

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

# --- Custom OpenAPI ---
@app.get("/openapi.json")
def custom_openapi():
    return app.openapi()

# --- Graph build function (runs in thread) ---
def build_graph():
    jacard_graph.progress['is_building'] = True
    jacard_graph.progress['status'] = 'running'
    jacard_graph.progress['start_time'] = datetime.now().isoformat()
    try:
        jacard_graph.build_graph_from_inverted_index(
            inverted_index_path="../books_data/index_TableTC.json",
            catalog_path="../books_data/catalog.json",
            progress_interval=0.01
        )
        jacard_graph.progress['status'] = 'completed'
    except Exception as e:
        print(f"ERROR IN GRAPH BUILD: {e}")
        jacard_graph.progress['status'] = 'failed'
    finally:
        jacard_graph.progress['is_building'] = False
        jacard_graph.progress['end_time'] = datetime.now().isoformat()

# --- PageRank function (runs in thread) ---
def run_pagerank():
    jacard_graph.progress['is_ranking'] = True
    jacard_graph.progress['rank_status'] = 'running'
    jacard_graph.progress['rank_start_time'] = datetime.now().isoformat()
    try:
        jacard_graph.calculate_pagerank_numpy(
            max_iterations=100,  # safe default
            damping=0.85
        )
        jacard_graph.progress['rank_status'] = 'completed'
    except Exception as e:
        print(f"ERROR IN PAGERANK: {e}")
        jacard_graph.progress['rank_status'] = 'failed'
    finally:
        jacard_graph.progress['is_ranking'] = False
        jacard_graph.progress['rank_end_time'] = datetime.now().isoformat()

# --- Build Graph Endpoint ---
@app.post("/jacardAPI/build")
async def build_jacard_index(request: BuildPasswordRequest):
    if request.password != "supersecret":
        raise HTTPException(status_code=403, detail="Forbidden")
    if jacard_graph.progress['is_building']:
        raise HTTPException(status_code=409, detail="Build already in progress")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(jacard_thread_pool, build_graph)
    return {"message": "Jaccard graph build started"}

# --- Run PageRank Endpoint ---
@app.post("/jacardAPI/run_pagerank")
async def start_jacard_pagerank(request: BuildPasswordRequest):
    if request.password != "supersecret":
        raise HTTPException(status_code=403, detail="Forbidden")
    if jacard_graph.progress['status'] != 'completed':
        raise HTTPException(status_code=409, detail="Graph building in progress or not completed")
    if jacard_graph.progress['is_ranking']:
        raise HTTPException(status_code=409, detail="PageRank already in progress")

    loop = asyncio.get_running_loop()
    loop.run_in_executor(jacard_thread_pool, run_pagerank)
    return {"message": "PageRank computation started"}

# --- Get Progress Endpoint ---
@app.get("/jacardAPI/status", response_model=JacardStatus)
async def get_index_status() -> JacardStatus:
    return JacardStatus(**jacard_graph.progress)

# --- Get Stats Endpoint ---
@app.get("/jacardAPI/stats")
async def get_stats():
    return {
        "total_pairs": jacard_graph.progress.get("total_pairs", 0),
        "processed_pairs": jacard_graph.progress.get("processed_pairs", 0),
        "status": jacard_graph.progress.get("status", "idle"),
        "is_building": jacard_graph.progress.get("is_building", False),
        "is_ranking": jacard_graph.progress.get("is_ranking", False),
        "rank_status": jacard_graph.progress.get("rank_status", "idle")
    }

@app.get("/jacardAPI/pagerank")
async def get_pagerank(book_ids: List[int] = Query(...)):
    """Return PageRank scores for the requested book IDs"""
    if not jacard_graph.pagerank_scores:
        raise HTTPException(status_code=400, detail="PageRank not calculated yet")

    print(f"Looking for book_ids: {book_ids}")
    print(f"Type of first book_id: {type(book_ids[0])}")

    result = {book_id: jacard_graph.pagerank_scores.get(book_id, 0.0) for book_id in book_ids}
    return result

@app.get("/jacardAPI/similar/{book_id}")
async def get_similar_books(book_id: int, top_n: int = 5):
    """Return top N most similar books based on Jaccard similarity"""
    neighbors = jacard_graph.get_neighbors(book_id)
    if not neighbors:
        return {"book_id": book_id, "similar_books": []}

    # Sort neighbors by similarity descending
    neighbors_sorted = sorted(neighbors, key=lambda x: x[1], reverse=True)
    top_neighbors = neighbors_sorted[:top_n]

    return {
        "book_id": book_id,
        "similar_books": [{"book_id": b, "similarity": sim} for b, sim in top_neighbors]
    }



@app.post("/jacardAPI/load")
async def load_graph(request: BuildPasswordRequest):
    if request.password != "supersecret":
        raise HTTPException(status_code=403)

    jacard_graph.load_graph()
    jacard_graph.load_pagerank()
    return {"message": "Graph and PageRank loaded"}