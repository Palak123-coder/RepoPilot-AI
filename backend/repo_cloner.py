import hashlib
import os
import shutil
import stat
import time
from pathlib import Path

from git import Repo


BASE_CLONE_DIR = Path("data/cloned_repos")


def get_repo_id(repo_url: str) -> str:
    return hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:12]


def handle_remove_readonly(func, path, exc_info):
    """
    Fixes Windows permission issues when deleting .git object files.
    Some Git files can become read-only, causing WinError 5.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def safe_remove_directory(path: Path) -> bool:
    """
    Attempts to remove a directory safely on Windows.
    Returns True if removed, False otherwise.
    """
    if not path.exists():
        return True

    for _ in range(3):
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return True
        except Exception:
            time.sleep(0.5)

    return False


def clone_repository(repo_url: str) -> Path:
    BASE_CLONE_DIR.mkdir(parents=True, exist_ok=True)

    repo_id = get_repo_id(repo_url)
    target_path = BASE_CLONE_DIR / repo_id

    if target_path.exists():
        removed = safe_remove_directory(target_path)

        if not removed:
            timestamp = int(time.time())
            target_path = BASE_CLONE_DIR / f"{repo_id}_{timestamp}"

    Repo.clone_from(repo_url, target_path)

    return target_path