import time

from fastapi import FastAPI, HTTPException

from backend.file_parser import parse_repository
from backend.models import IndexRequest, SearchRequest
from backend.repo_cloner import clone_repository
from backend.search_engine import SimpleCodeSearchEngine


app = FastAPI(
    title="RepoPilot AI",
    description="Agentic codebase search and bug triage system",
    version="0.1.0"
)

search_engine = SimpleCodeSearchEngine()

repo_status = {
    "status": "idle",
    "repo_url": None,
    "files_indexed": 0,
    "indexing_time_ms": 0,
    "error": None
}


@app.get("/")
def root():
    return {
        "message": "RepoPilot AI backend is running",
        "status": repo_status
    }


@app.post("/index")
def index_repository(request: IndexRequest):
    start_time = time.time()

    repo_status["status"] = "indexing"
    repo_status["repo_url"] = request.repo_url
    repo_status["files_indexed"] = 0
    repo_status["indexing_time_ms"] = 0
    repo_status["error"] = None

    try:
        repo_path = clone_repository(request.repo_url)
        files = parse_repository(repo_path)

        search_engine.index_files(files)

        elapsed_ms = int((time.time() - start_time) * 1000)

        repo_status["status"] = "completed"
        repo_status["files_indexed"] = len(files)
        repo_status["indexing_time_ms"] = elapsed_ms

        return {
            "message": "Repository indexed successfully",
            "repo_url": request.repo_url,
            "files_indexed": len(files),
            "indexing_time_ms": elapsed_ms
        }

    except Exception as error:
        repo_status["status"] = "failed"
        repo_status["error"] = str(error)

        raise HTTPException(status_code=500, detail=str(error))


@app.post("/search")
def search_repository(request: SearchRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first."
        )

    results = search_engine.search(request.query, request.top_k)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "query": request.query,
        "top_k": request.top_k,
        "query_latency_ms": elapsed_ms,
        "results": results
    }


@app.get("/status")
def get_status():
    return repo_status