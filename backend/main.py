import time

from fastapi import FastAPI, HTTPException

from backend.chunker import chunk_files
from backend.file_parser import parse_repository
from backend.models import IndexRequest, SearchRequest, SemanticSearchRequest, AskRequest
from backend.rag_agent import RAGAgent
from backend.repo_cloner import clone_repository
from backend.search_engine import SimpleCodeSearchEngine
from backend.vector_store import SemanticCodeVectorStore


app = FastAPI(
    title="RepoPilot AI",
    description="Agentic codebase search and bug triage system",
    version="0.3.0"
)

keyword_search_engine = SimpleCodeSearchEngine()
semantic_vector_store = SemanticCodeVectorStore()
rag_agent = RAGAgent()

repo_status = {
    "status": "idle",
    "repo_url": None,
    "files_indexed": 0,
    "chunks_indexed": 0,
    "indexing_time_ms": 0,
    "error": None
}


@app.get("/")
def root():
    return {
        "message": "RepoPilot AI backend is running",
        "version": "0.3.0",
        "status": repo_status
    }


@app.post("/index")
def index_repository(request: IndexRequest):
    start_time = time.time()

    repo_status["status"] = "indexing"
    repo_status["repo_url"] = request.repo_url
    repo_status["files_indexed"] = 0
    repo_status["chunks_indexed"] = 0
    repo_status["indexing_time_ms"] = 0
    repo_status["error"] = None

    try:
        repo_path = clone_repository(request.repo_url)

        files = parse_repository(repo_path)
        keyword_search_engine.index_files(files)

        chunks = chunk_files(files)

        semantic_vector_store.reset()
        chunks_indexed = semantic_vector_store.index_chunks(chunks)

        elapsed_ms = int((time.time() - start_time) * 1000)

        repo_status["status"] = "completed"
        repo_status["files_indexed"] = len(files)
        repo_status["chunks_indexed"] = chunks_indexed
        repo_status["indexing_time_ms"] = elapsed_ms

        return {
            "message": "Repository indexed successfully",
            "repo_url": request.repo_url,
            "files_indexed": len(files),
            "chunks_indexed": chunks_indexed,
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

    results = keyword_search_engine.search(request.query, request.top_k)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "search_type": "keyword",
        "query": request.query,
        "top_k": request.top_k,
        "query_latency_ms": elapsed_ms,
        "results": results
    }


@app.post("/semantic-search")
def semantic_search_repository(request: SemanticSearchRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first."
        )

    results = semantic_vector_store.semantic_search(request.query, request.top_k)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "search_type": "semantic",
        "query": request.query,
        "top_k": request.top_k,
        "query_latency_ms": elapsed_ms,
        "results": results
    }


@app.post("/ask")
def ask_repository(request: AskRequest):
    start_time = time.time()

    if repo_status["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="No repository indexed yet. Please index a repository first."
        )

    try:
        retrieved_chunks = semantic_vector_store.semantic_search(
            request.question,
            request.top_k
        )

        rag_response = rag_agent.answer_question(
            request.question,
            retrieved_chunks
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "answer_type": "rag",
            "question": request.question,
            "top_k": request.top_k,
            "answer_latency_ms": elapsed_ms,
            "answer": rag_response["answer"],
            "sources": rag_response["sources"]
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/status")
def get_status():
    return repo_status