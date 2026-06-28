from pathlib import Path

from backend.chunker import chunk_files, chunk_text
from backend.file_parser import parse_repository
from backend.search_engine import SimpleCodeSearchEngine


def get_chunk_text(chunk):
    if isinstance(chunk, str):
        return chunk

    return (
        chunk.get("content")
        or chunk.get("text")
        or chunk.get("chunk")
        or chunk.get("snippet")
        or ""
    )


def normalize_path(path):
    return str(path).replace("\\", "/")


def test_chunk_text_splits_long_text():
    text = "authentication token validation " * 100

    chunks = chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert all(get_chunk_text(chunk).strip() for chunk in chunks)


def test_chunk_files_preserves_file_path_and_content():
    files = [
        {
            "path": "src/auth.py",
            "content": "def login():\n    validate_token()\n" * 50,
        }
    ]

    chunks = chunk_files(files)

    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "path" in first_chunk
    assert first_chunk["path"] == "src/auth.py"
    assert get_chunk_text(first_chunk).strip()


def test_file_parser_reads_supported_files_and_ignores_heavy_folders(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    main_file = src_dir / "main.py"
    main_file.write_text("print('hello from main')", encoding="utf-8")

    readme_file = tmp_path / "README.md"
    readme_file.write_text("# RepoPilot AI", encoding="utf-8")

    node_modules_dir = tmp_path / "node_modules"
    node_modules_dir.mkdir()

    ignored_file = node_modules_dir / "ignored.js"
    ignored_file.write_text("console.log('ignore me')", encoding="utf-8")

    image_file = tmp_path / "diagram.png"
    image_file.write_text("not a real image", encoding="utf-8")

    parsed_files = parse_repository(tmp_path)
    parsed_paths = [normalize_path(file["path"]) for file in parsed_files]

    assert any(path.endswith("src/main.py") for path in parsed_paths)
    assert any(path.endswith("README.md") for path in parsed_paths)
    assert not any("node_modules" in path for path in parsed_paths)
    assert not any(path.endswith("diagram.png") for path in parsed_paths)


def test_keyword_search_returns_relevant_ranked_results():
    engine = SimpleCodeSearchEngine()

    files = [
        {
            "path": "src/auth.py",
            "content": "login token authentication validation token token",
        },
        {
            "path": "src/database.py",
            "content": "database connection query transaction",
        },
        {
            "path": "README.md",
            "content": "project documentation setup installation",
        },
    ]

    engine.index_files(files)

    results = engine.search("token authentication", top_k=2)

    assert len(results) > 0
    assert results[0]["path"] == "src/auth.py"
    assert results[0]["score"] > 0
    assert "snippet" in results[0]


def test_keyword_search_respects_top_k():
    engine = SimpleCodeSearchEngine()

    files = [
        {"path": "a.py", "content": "search ranking indexing"},
        {"path": "b.py", "content": "search indexing"},
        {"path": "c.py", "content": "search"},
    ]

    engine.index_files(files)

    results = engine.search("search", top_k=2)

    assert len(results) <= 2


def test_repository_summary_request_model_defaults():
    from backend.models import RepoSummaryRequest

    request = RepoSummaryRequest()

    assert request.top_k == 10


def test_architecture_request_model_defaults():
    from backend.models import ArchitectureRequest

    request = ArchitectureRequest()

    assert request.top_k == 10


def test_bug_triage_request_model_defaults():
    from backend.models import BugTriageRequest

    request = BugTriageRequest(
        bug_description="Search results are empty after indexing."
    )

    assert request.bug_description == "Search results are empty after indexing."
    assert request.top_k == 8