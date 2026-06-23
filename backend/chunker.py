from typing import List, Dict


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """
    Splits large file content into overlapping chunks.

    Why:
    - Large files may exceed embedding model limits.
    - Smaller chunks improve retrieval accuracy.
    - Overlap preserves context across chunk boundaries.
    """
    if not text.strip():
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == text_length:
            break

        start = end - overlap

    return chunks


def chunk_files(files: List[Dict]) -> List[Dict]:
    """
    Converts parsed repository files into searchable chunks.
    """
    all_chunks = []

    for file in files:
        path = file["path"]
        content = file["content"]

        chunks = chunk_text(content)

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{path}::chunk_{index}",
                "path": path,
                "chunk_index": index,
                "content": chunk
            })

    return all_chunks