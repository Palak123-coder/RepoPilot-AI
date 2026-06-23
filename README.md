# RepoPilot AI

RepoPilot AI is a FastAPI-based codebase search system that indexes public GitHub repositories and returns relevant source files, snippets, indexing time, and query-latency metrics.

This is the MVP version of a larger agentic codebase search and bug-triage system. The goal is to help developers understand unfamiliar repositories, locate relevant files, and debug code faster.

## Current Features

* Accepts a public GitHub repository URL
* Clones the repository locally using GitPython
* Parses supported source-code and documentation files
* Ignores heavy folders like `.git`, `node_modules`, `venv`, `dist`, and `build`
* Indexes file paths and file contents
* Supports keyword-based code search
* Returns relevant file paths, snippets, scores, and query latency
* Tracks repository indexing status, files indexed, indexing time, and errors
* Exposes API documentation through FastAPI Swagger UI

## Tech Stack

* Python
* FastAPI
* Uvicorn
* GitPython
* Pydantic
* Python-dotenv

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
│   └── search_engine.py
│
├── data/
│   └── cloned_repos/
│
├── screenshots/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## API Endpoints

### `GET /`

Checks whether the backend is running.

Example response:

```json
{
  "message": "RepoPilot AI backend is running",
  "status": {
    "status": "idle",
    "repo_url": null,
    "files_indexed": 0,
    "indexing_time_ms": 0,
    "error": null
  }
}
```

### `POST /index`

Indexes a public GitHub repository.

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
  "indexing_time_ms": 2519
}
```

### `POST /search`

Searches the indexed repository.

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
  "query": "multithreading synchronization",
  "top_k": 5,
  "query_latency_ms": 2,
  "results": [
    {
      "path": "README.md",
      "score": 8,
      "snippet": "This project demonstrates core software engineering concepts including data structures, algorithms, file processing, multithreading, synchronization..."
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
  "indexing_time_ms": 2519,
  "error": null
}
```

## How It Works

RepoPilot AI follows this flow:

```text
GitHub repository URL
        ↓
Clone repository using GitPython
        ↓
Parse supported source-code and documentation files
        ↓
Ignore large/generated folders
        ↓
Index file paths and file contents
        ↓
Search indexed files using keyword scoring
        ↓
Return relevant file paths, snippets, scores, and latency
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
* `.go`
* `.rs`
* `.md`
* `.txt`
* `.json`
* `.yml`
* `.yaml`

It ignores folders that are usually large, generated, or unnecessary for code understanding, such as:

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

## Search Logic

The current MVP uses keyword-based search.

For each indexed file:

1. The file content is tokenized.
2. Query terms are tokenized.
3. The search engine counts query-term matches in each file.
4. Files are ranked by match score.
5. The API returns the top-K relevant files with snippets.

This will later be upgraded to semantic search using embeddings and a vector database.

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/Palak123-coder/RepoPilot-AI.git
cd RepoPilot-AI
```

### 2. Create virtual environment

```powershell
py -3.10 -m venv venv
```

### 3. Activate virtual environment

```powershell
.\venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run the backend

```powershell
uvicorn backend.main:app --reload
```

### 6. Open Swagger UI

Open this URL in your browser:

```text
http://127.0.0.1:8000/docs
```

## Example Usage

### Index a repository

Use `POST /index` with:

```json
{
  "repo_url": "https://github.com/Palak123-coder/MiniSearchX"
}
```

### Search the indexed repository

Use `POST /search` with:

```json
{
  "query": "multithreading synchronization",
  "top_k": 5
}
```

## Current MVP Result

RepoPilot AI successfully indexed the MiniSearchX repository and returned relevant search results.

Example metrics:

```text
Files indexed: 6
Indexing time: 2519 ms
Query latency: 2 ms
```

## Current Status

This is the MVP version.

Completed:

* GitHub repository cloning
* Source-file parsing
* Ignored-folder filtering
* Keyword-based search
* Snippet extraction
* Indexing-status tracking
* Query-latency reporting
* FastAPI Swagger documentation

## Upcoming Improvements

* Add code chunking for large files
* Add semantic search using embeddings
* Add ChromaDB vector database integration
* Add RAG-based answers with grounded file references
* Add Gemini or Groq LLM integration
* Add Streamlit dashboard
* Add background indexing jobs
* Add retry handling and failed-job logs
* Add Docker support
* Add unit tests
