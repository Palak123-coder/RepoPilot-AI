import time
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException

from backend.chunker import chunk_files
from backend.file_parser import parse_repository
from backend.job_store import (
    create_indexing_job,
    create_job_log,
    current_timestamp,
    get_job,
    get_job_logs,
    init_job_store,
    list_jobs,
    update_job,
)
from backend.models import (
    AskRequest,
    IndexRequest,
    RepoSummaryRequest,
    SearchRequest,
    SemanticSearchRequest,
)
from backend.rag_agent import RAGAgent
from backend.repo_cloner import clone_repository
from backend.search_engine import SimpleCodeSearchEngine
from backend.vector_store import SemanticCodeVectorStore


MAX_INDEXING_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 2

app = FastAPI(
    title="RepoPilot AI",
    description="Agentic codebase search and bug triage system",
    version="0.8.0",
)

init_job_store()

keyword_search_engine = SimpleCodeSearchEngine()
semantic_vector_store = SemanticCodeVectorStore()
rag_agent = RAGAgent()

repo_status = {
    "status": "idle",
    "repo_url": None,
    "files_indexed": 0,
    "chunks_indexed": 0,
    "indexing_time_ms": 0,
    "error": None,
}


def reset_repo_status_for_indexing(repo_url: str):
    repo_status["status"] = "indexing"
    repo_status["repo_url"] = repo_url
    repo_status["files_indexed"] = 0
    repo_status["chunks_indexed"] = 0
    repo_status["indexing_time_ms"] = 0
    repo_status["error"] = None


def perform_indexing(repo_url: str):
    start_time = time.time()

    repo_path = clone_repository(repo_url)

    files = parse_repository(repo_path)
    keyword_search_engine.index_files(files)

    chunks = chunk_files(files)

    semantic_vector_store.reset()
    chunks_indexed = semantic_vector_store.index_chunks(chunks)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "message": "Repository indexed successfully",
        "repo_url": repo_url,
        "files_indexed": len(files),
        "chunks_indexed": chunks_indexed,
        "indexing_time_ms": elapsed_ms,
    }


def run_indexing_job(job_id: str, repo_url: str):
    reset_repo_status_for_indexing(repo_url)

    last_error = None

    for attempt in range(1, MAX_INDEXING_ATTEMPTS + 1):
        update_job(
            job_id,
            status="running",
            started_at=current_timestamp(),
            attempts=attempt,
        )

        create_job_log(
            job_id=job_id,
            attempt=attempt,
            level="info",
            message=f"Indexing attempt {attempt} started.",
        )

        try:
            result = perform_indexing(repo_url)

            repo_status["status"] = "completed"
            repo_status["files_indexed"] = result["files_indexed"]
            repo_status["chunks_indexed"] = result["chunks_indexed"]
            repo_status["indexing_time_ms"] = result["indexing_time_ms"]
            repo_status["error"] = None

            update_job(
                job_id,
                status="completed",
                files_indexed=result["files_indexed"],
                chunks_indexed=result["chunks_indexed"],
                indexing_time_ms=result["indexing_time_ms"],
                error=None,
                completed_at=current_timestamp(),
                attempts=attempt,
            )

            create_job_log(
                job_id=job_id,
                attempt=attempt,
                level="info",
                message="Indexing completed successfully.",
            )

            return

        except Exception as error:
            last_error = str(error)

            create_job_log(
                job_id=job_id,
                attempt=attempt,
                level="error",
                message=f"Indexing attempt {attempt} failed.",
                error=last_error,
            )

            if attempt < MAX_INDEXING_ATTEMPTS:
                create_job_log(
                    job_id=job_id,
                    attempt=attempt,
                    level="warning",
                    message=f"Retrying indexing job after {RETRY_DELAY_SECONDS} seconds.",
                    error=last_error,
                )

                time.sleep(RETRY_DELAY_SECONDS)

    repo_status["status"] = "failed"
    repo_status["error"] = last_error

    update_job(
        job_id,
        status="failed",
        error=last_error,
        completed_at=current_timestamp(),
        attempts=MAX_INDEXING_ATTEMPTS,
    )

    create_job_log(
        job_id=job_id,
        attempt=MAX_INDEXING_ATTEMPTS,
        level="error",
        message="Indexing job failed after maximum retry attempts.",
        error=last_error,
    )


@app.get("/")
def root():
    return {
        "message": "RepoPilot AI backend is running",
        "version": "0.8.0",
        "status": repo_status,
    }


@app.post("/index")
def index_repository(request: IndexRequest):
    if repo_status["status"] == "indexing":
        raise HTTPException(
            status_code=409,
            detail="Another repository is currently being indexed.",
        )

    reset_repo_status_for_indexing(request.repo_url)

    try:
        result = perform_indexing(request.repo_url)

        repo_status["status"] = "completed"
        repo_status["files_indexed"] = result["files_indexed"]
        repo_status["chunks_indexed"] = result["chunks_indexed"]
        repo_status["indexing_time_ms"] = result["indexing_time_ms"]
        repo_status["error"] = None

        return result

    except Exception as error:
        repo_status["status"] = "failed"
        repo_status["error"] = str(error)

        raise HTTPException(status_code=500, detail=str(error))


@app.post("/index-job")
def start_indexing_job(request: IndexRequest, background_tasks: BackgroundTasks):
    if repo_status["status"] == "indexing":
        raise HTTPException(
            status_code=409,
            detail="Another repository is currently being indexed.",
        )

    job = create_indexing_job(request.repo_url)

    reset_repo_status_for_indexing(request.repo_url)

    background_tasks.add_task(run_indexing_job, job["job_id"], request.repo_url)

    return {
        "message": "Indexing job started",
        "job_id": job["job_id"],
        "repo_url": request.repo_url,
        "status": job["status"],
        "status_url": f"/jobs/{job['job_id']}",
        "logs_url": f"/jobs/{job['job_id']}/logs",
    }


@app.get("/jobs/{job_id}")
def get_indexing_job(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Indexing job not found.",
        )

    return job


@app.get("/jobs/{job_id}/logs")
def get_indexing_job_logs(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Indexing job not found.",
        )

    logs = get_job_logs(job_id)

    return {
        "job_id": job_id,
        "total_logs": len(logs),
        "logs": logs,
    }


@app.get("/jobs")
def list_indexing_jobs(status: Optional[str] = None, limit: int = 50):
    jobs = list_jobs(status=status, limit=limit)

    return {
        "total_jobs": len(jobs),
        "jobs": jobs,
    }


@app.post("/search")
def search_repository(request: SearchRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first.",
        )

    results = keyword_search_engine.search(request.query, request.top_k)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "search_type": "keyword",
        "query": request.query,
        "top_k": request.top_k,
        "query_latency_ms": elapsed_ms,
        "results": results,
    }


@app.post("/semantic-search")
def semantic_search_repository(request: SemanticSearchRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first.",
        )

    results = semantic_vector_store.semantic_search(request.query, request.top_k)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "search_type": "semantic",
        "query": request.query,
        "top_k": request.top_k,
        "query_latency_ms": elapsed_ms,
        "results": results,
    }


@app.post("/repo-summary")
def generate_repo_summary(request: RepoSummaryRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first.",
        )

    try:
        summary_query = (
            "repository overview architecture main modules technologies "
            "features setup usage API endpoints data flow README"
        )

        retrieved_chunks = semantic_vector_store.semantic_search(
            summary_query,
            request.top_k,
        )

        summary_response = rag_agent.summarize_repository(retrieved_chunks)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "answer_type": "repo_summary",
            "repo_url": repo_status["repo_url"],
            "top_k": request.top_k,
            "summary_latency_ms": elapsed_ms,
            "summary": summary_response["summary"],
            "sources": summary_response["sources"],
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/ask")
def ask_repository(request: AskRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first.",
        )

    try:
        retrieved_chunks = semantic_vector_store.semantic_search(
            request.question,
            request.top_k,
        )

        rag_response = rag_agent.answer_question(
            request.question,
            retrieved_chunks,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "answer_type": "rag",
            "question": request.question,
            "top_k": request.top_k,
            "answer_latency_ms": elapsed_ms,
            "answer": rag_response["answer"],
            "sources": rag_response["sources"],
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/status")
def get_status():
    return repo_status