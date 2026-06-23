import re
from collections import Counter


class SimpleCodeSearchEngine:
    def __init__(self):
        self.files = []

    def index_files(self, files: list[dict]) -> None:
        self.files = files

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        results = []

        for file in self.files:
            content = file["content"]
            content_tokens = self._tokenize(content)
            token_counts = Counter(content_tokens)

            score = 0

            for token in query_tokens:
                score += token_counts.get(token, 0)

            if score > 0:
                snippet = self._get_snippet(content, query_tokens)

                results.append({
                    "path": file["path"],
                    "score": score,
                    "snippet": snippet
                })

        results.sort(key=lambda item: item["score"], reverse=True)

        return results[:top_k]

    def _get_snippet(self, content: str, query_tokens: list[str]) -> str:
        lines = content.splitlines()

        for line in lines:
            lower_line = line.lower()

            if any(token in lower_line for token in query_tokens):
                return line.strip()[:300]

        return content[:300]