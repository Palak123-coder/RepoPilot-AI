# RepoPilot AI

RepoPilot AI is a FastAPI-based codebase intelligence system that indexes public GitHub repositories and answers developer questions using keyword search, semantic search, RAG-based answer generation, and background indexing jobs.

The project helps developers understand unfamiliar repositories, locate relevant files, and debug code faster using repository parsing, code chunking, embeddings, vector search, Groq-powered grounded answers, asynchronous job tracking, and an interactive Streamlit dashboard.

## Current Features

* Accepts a public GitHub repository URL
* Clones the repository locally using GitPython
* Parses supported source-code and documentation files
* Ignores heavy/generated folders like `.git`, `node_modules`, `venv`, `dist`, and `build`
* Indexes file paths and file contents
* Supports keyword-based code search through `/search`
* Splits repository files into overlapping code chunks
* Generates embeddings for code and documentation chunks using SentenceTransformers
* Stores semantic vectors in ChromaDB
* Supports semantic code search through `/semantic-search`
* Supports RAG-based question answering through `/ask`
* Uses semantic retrieval over indexed code chunks before generating answers
* Generates grounded answers using Groq LLM with relevant file references
* Supports synchronous repository indexing through `/index`
* Supports background indexing jobs through `/index-job`
* Provides job tracking through `/jobs/{job_id}`
* Provides job history through `/jobs`
* Tracks job status as `pending`, `running`, `completed`, or `failed`
* Tracks job metadata including `created_at`, `started_at`, and `completed_at`
* Provides an interactive Streamlit dashboard for repository indexing, keyword search, semantic search, and RAG-based question answering
* Displays files indexed, chunks indexed, indexing time, query latency, answer latency, generated answers, and source file references
* Tracks repository indexing status, files indexed, chunks indexed, indexing time, and errors
* Exposes API documentation through FastAPI Swagger UI

## Tech Stack

* Python
* FastAPI
* Uvicorn
* GitPython
* Pydantic
* Python-dotenv
* ChromaDB
* SentenceTransformers
* Groq API
* RAG
* Streamlit
* Requests
* BackgroundTasks
* Threading
* UUID-based job tracking

## Project Structure

```text
RepoPilot-AI/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── repo_cloner.py
│   ├── file_parser.py
│   ├── search_engine.py
│   ├── chunker.py
│   ├── vector_store.py
│   └── rag_agent.py
│
├── frontend/
│   └── app.py
│
├── data/
│   ├── .gitkeep
│   └── cloned_repos/
│
├── screenshots/
│   ├── index-success.png
│   ├── semantic-search-success.png
│   ├── ask-success.png
│   ├── dashboard-index.png
│   ├── dashboard-search.png
│   ├── dashboard-rag.png
│   ├── index-job-started.png
│   └── job-status-completed.png
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## How It Works

RepoPilot AI follows this workflow:

```text
GitHub repository URL
        ↓
Clone repository using GitPython
        ↓
Parse supported source-code and documentation files
        ↓
Ignore large/generated folders
        ↓
Store files for keyword search
        ↓
Split files into overlapping chunks
        ↓
Generate embeddings for chunks
        ↓
Store embeddings in ChromaDB
        ↓
Retrieve relevant chunks using semantic search
        ↓
Generate grounded answers using Groq LLM
        ↓
Return answer with source file references
```

For background indexing, the workflow becomes:

```text
POST /index-job
        ↓
Create job_id
        ↓
Return response immediately
        ↓
Run indexing in background
        ↓
Update job status
        ↓
GET /jobs/{job_id}
        ↓
Check pending/running/completed/failed status
```

## File Parsing

RepoPilot AI supports common source-code and documentation file types, including:

* `.py`
* `.js`
* `.ts`
* `.tsx`
* `.jsx`
* `.java`
* `.cpp`
* `.c`
* `.h`
* `.hpp`
* `.cs`
* `.go`
* `.rs`
* `.php`
* `.rb`
* `.md`
* `.txt`
* `.json`
* `.yml`
* `.yaml`

It ignores folders that are usually large, generated, or unnecessary for code understanding:

* `.git`
* `node_modules`
* `venv`
* `.venv`
* `__pycache__`
* `dist`
* `build`
* `.next`
* `.idea`
* `.vscode`

## Keyword Search

The `/search` endpoint performs keyword-based search.

For each indexed file:

1. The file content is tokenized.
2. The query is tokenized.
3. Query-term matches are counted in each file.
4. Files are ranked by match score.
5. The API returns the top-K relevant files with snippets.

This is useful when the user knows the exact terms they want to search for, such as `multithreading`, `synchronization`, `database`, or `authentication`.

## Semantic Search

The `/semantic-search` endpoint performs semantic search using embeddings and ChromaDB.

For each indexed repository:

1. Parsed files are split into overlapping chunks.
2. Each chunk is converted into an embedding using SentenceTransformers.
3. Embeddings are stored in ChromaDB.
4. User queries are converted into embeddings.
5. ChromaDB retrieves semantically similar chunks.
6. The API returns relevant file paths, chunk indexes, distance scores, snippets, and query latency.

This allows RepoPilot AI to find relevant code even when the query does not exactly match the wording used inside the repository.

Example semantic query:

```text
Where is synchronization handled in this project?
```

## RAG Answer Generation

The `/ask` endpoint performs RAG-based question answering over the indexed repository.

For each question:

1. The question is converted into an embedding.
2. ChromaDB retrieves the most relevant code/documentation chunks.
3. Retrieved chunks are passed to the Groq LLM as grounded context.
4. The LLM generates an answer using only the retrieved repository context.
5. The API returns the answer along with relevant file references.

This makes RepoPilot AI useful for architecture understanding, debugging, and feature-navigation questions.

Example RAG question:

```text
Where is synchronization handled in this project?
```

## Background Indexing Jobs

RepoPilot AI supports background indexing jobs for a more scalable and production-like workflow.

Instead of waiting for repository indexing to complete in the same request, `/index-job` returns a `job_id` immediately. The indexing process then runs in the background, and the client can poll `/jobs/{job_id}` to check progress.

This demonstrates:

* Asynchronous backend workflow
* Job tracking
* Status polling
* Error reporting
* System reliability design
* Backend state management

Job statuses:

```text
pending   → job has been created
running   → repository indexing is in progress
completed → repository indexing completed successfully
failed    → repository indexing failed
```

## Streamlit Dashboard

RepoPilot AI includes a Streamlit dashboard for using the system through a simple interface instead of only Swagger API calls.

The dashboard supports:

* Repository URL input
* Repository indexing button
* Files indexed, chunks indexed, and indexing-time metrics
* Keyword search with ranked results
* Semantic search with chunk-level results
* RAG-based question answering
* Answer latency display
* Source file references table

## API Endpoints

### `GET /`

Checks whether the backend is running.

Example response:

```json
{
  "message": "RepoPilot AI backend is running",
  "version": "0.5.0",
  "status": {
    "status": "idle",
    "repo_url": null,
    "files_indexed": 0,
    "chunks_indexed": 0,
    "indexing_time_ms": 0,
    "error": null
  }
}
```

### `POST /index`

Indexes a public GitHub repository synchronously.

Request body:

```json
{
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX"
}
```

Example response:

```json
{
  "message": "Repository indexed successfully",
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX",
  "files_indexed": 6,
  "chunks_indexed": 29,
  "indexing_time_ms": 5530
}
```

### `POST /index-job`

Starts repository indexing as a background job and returns a `job_id` immediately.

Request body:

```json
{
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX"
}
```

Example response:

```json
{
  "message": "Indexing job started",
  "job_id": "ebf3db6c-749f-45cb-bca1-b70b17eb3882",
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX",
  "status": "pending",
  "status_url": "/jobs/ebf3db6c-749f-45cb-bca1-b70b17eb3882"
}
```

### `GET /jobs/{job_id}`

Returns the status and metadata of a specific indexing job.

Example response:

```json
{
  "job_id": "ebf3db6c-749f-45cb-bca1-b70b17eb3882",
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX",
  "status": "completed",
  "files_indexed": 6,
  "chunks_indexed": 29,
  "indexing_time_ms": 5176,
  "error": null,
  "created_at": "2026-06-25T13:52:51.372864Z",
  "started_at": "2026-06-25T13:52:51.374285Z",
  "completed_at": "2026-06-25T13:52:56.550375Z"
}
```

### `GET /jobs`

Returns all indexing jobs stored during the current backend session.

Example response:

```json
{
  "total_jobs": 1,
  "jobs": [
    {
      "job_id": "ebf3db6c-749f-45cb-bca1-b70b17eb3882",
      "repo_url": "https://github.com/Palak123-coder/MiniSearchX",
      "status": "completed",
      "files_indexed": 6,
      "chunks_indexed": 29,
      "indexing_time_ms": 5176,
      "error": null,
      "created_at": "2026-06-25T13:52:51.372864Z",
      "started_at": "2026-06-25T13:52:51.374285Z",
      "completed_at": "2026-06-25T13:52:56.550375Z"
    }
  ]
}
```

### `POST /search`

Performs keyword-based search over indexed repository files.

Request body:

```json
{
  "query": "multithreading synchronization",
  "top_k": 5
}
```

Example response:

```json
{
  "search_type": "keyword",
  "query": "multithreading synchronization",
  "top_k": 5,
  "query_latency_ms": 1,
  "results": [
    {
      "path": "README.md",
      "score": 8,
      "snippet": "This project demonstrates core software engineering concepts including data structures, algorithms, file processing, multithreading, synchronization..."
    }
  ]
}
```

### `POST /semantic-search`

Performs semantic search over indexed code chunks.

Request body:

```json
{
  "query": "Where is synchronization handled in this project?",
  "top_k": 5
}
```

Example response:

```json
{
  "search_type": "semantic",
  "query": "Where is synchronization handled in this project?",
  "top_k": 5,
  "query_latency_ms": 45,
  "results": [
    {
      "path": "data\\doc3.txt",
      "chunk_index": 0,
      "distance": 1.031865119934082,
      "snippet": "Operating systems use threads, synchronization, mutexes, and scheduling for concurrent execution."
    },
    {
      "path": "README.md",
      "chunk_index": 1,
      "distance": 1.4639391899108887,
      "snippet": "Tech Stack\\n\\n- C++\\n- STL\\n- Hash Maps\\n- Priority Queue\\n- File I/O\\n- TF-IDF Ranking\\n- BM25 Ranking\\n- Windows Threads\\n- Critical Sections for Synchronization..."
    }
  ]
}
```

### `POST /ask`

Answers a natural-language question about the indexed repository using semantic retrieval and Groq LLM.

Request body:

```json
{
  "question": "Where is synchronization handled in this project?",
  "top_k": 5
}
```

Example response:

```json
{
  "answer_type": "rag",
  "question": "Where is synchronization handled in this project?",
  "top_k": 5,
  "answer_latency_ms": 815,
  "answer": "Based on the retrieved context, synchronization is handled using Windows Critical Sections. The project uses Windows Critical Sections to prevent multiple threads from writing to the shared data structure at the same time, avoiding race conditions and maintaining correctness during parallel indexing.",
  "sources": [
    {
      "path": "data\\doc3.txt",
      "chunk_index": 0,
      "distance": 1.031865119934082
    },
    {
      "path": "README.md",
      "chunk_index": 1,
      "distance": 1.4639391899108887
    }
  ]
}
```

### `GET /status`

Returns the current repository indexing status.

Example response:

```json
{
  "status": "completed",
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX",
  "files_indexed": 6,
  "chunks_indexed": 29,
  "indexing_time_ms": 5176,
  "error": null
}
```

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/Palak123-coder/RepoPilot-AI.git
cd RepoPilot-AI
```

### 2. Create a virtual environment

```powershell
py -3.10 -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### 6. Run the FastAPI backend

```powershell
uvicorn backend.main:app
```

For development with auto-reload:

```powershell
uvicorn backend.main:app --reload
```

### 7. Open Swagger UI

Open this URL in your browser:

```text
http://127.0.0.1:8000/docs
```

### 8. Run the Streamlit dashboard

Open a new terminal, activate the virtual environment again, and run:

```powershell
streamlit run frontend/app.py
```

Then open the Streamlit local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Example Usage

### Step 1: Start a background indexing job

Use `POST /index-job` with:

```json
{
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX"
}
```

The API returns a `job_id`.

### Step 2: Check job status

Use `GET /jobs/{job_id}`.

Example completed response:

```json
{
  "status": "completed",
  "files_indexed": 6,
  "chunks_indexed": 29,
  "indexing_time_ms": 5176,
  "error": null
}
```

### Step 3: Run keyword search

Use `POST /search` or the Streamlit dashboard with:

```json
{
  "query": "multithreading synchronization",
  "top_k": 5
}
```

### Step 4: Run semantic search

Use `POST /semantic-search` or the Streamlit dashboard with:

```json
{
  "query": "Where is synchronization handled in this project?",
  "top_k": 5
}
```

### Step 5: Ask a RAG question

Use `POST /ask` or the Streamlit dashboard with:

```json
{
  "question": "Where is synchronization handled in this project?",
  "top_k": 5
}
```

## Current Demo Metrics

RepoPilot AI successfully indexed the MiniSearchX repository and returned keyword search, semantic search, RAG answer-generation, and background job tracking results.

```text
Files indexed: 6
Chunks indexed: 29
Background indexing time: 5176 ms
Keyword query latency: 1 ms
Semantic query latency: 45 ms
RAG answer latency: 815 ms
```

## Demo Screenshots

### Repository Indexing

![Index Success](screenshots/index-success.png)

### Semantic Search

![Semantic Search Success](screenshots/semantic-search-success.png)

### RAG Answer Generation

![Ask Success](screenshots/ask-success.png)

### Streamlit Dashboard - Repository Indexing

![Dashboard Index](screenshots/dashboard-index.png)

### Streamlit Dashboard - Search

![Dashboard Search](screenshots/dashboard-search.png)

### Streamlit Dashboard - RAG Answering

![Dashboard RAG](screenshots/dashboard-rag.png)

### Background Job Started

![Index Job Started](screenshots/index-job-started.png)

### Background Job Completed

![Job Status Completed](screenshots/job-status-completed.png)

## Current Status

This is version `0.5.0`.

Completed:

* GitHub repository cloning
* Source-file parsing
* Ignored-folder filtering
* Keyword-based search
* Code chunking
* Embedding generation
* ChromaDB vector storage
* Semantic search
* RAG-based answer generation
* Groq LLM integration
* Grounded answers with source file references
* Background indexing jobs
* UUID-based job IDs
* Job-status polling
* Job history for current backend session
* Job timestamps
* Error tracking for failed jobs
* Streamlit dashboard
* Snippet extraction
* Indexing-status tracking
* Query-latency reporting
* Answer-latency reporting
* FastAPI Swagger documentation
* Demo screenshots


## Upcoming Improvements

* Update Streamlit dashboard to start `/index-job` and poll `/jobs/{job_id}`
* Add persistent job storage using SQLite or PostgreSQL
* Add retry handling and failed-job logs
* Add Celery/Redis-based background workers
* Add Docker support
* Add unit tests
* Add repository summary generation
* Add architecture explanation endpoint
* Add bug-triage suggestions based on retrieved code chunks
* Add support for private repositories
