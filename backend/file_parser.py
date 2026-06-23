from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".h",
    ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".md", ".txt", ".json",
    ".yml", ".yaml"
}

IGNORED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
    "build", ".next", ".idea", ".vscode"
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def parse_repository(repo_path: Path) -> list[dict]:
    files = []

    for path in repo_path.rglob("*"):
        if should_ignore(path):
            continue

        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if not content.strip():
            continue

        relative_path = path.relative_to(repo_path)

        files.append({
            "path": str(relative_path),
            "content": content
        })

    return files