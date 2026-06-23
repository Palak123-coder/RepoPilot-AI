from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer


class SemanticCodeVectorStore:
    def __init__(self):
        self.persist_dir = Path("data/chroma_db")
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection_name = "repo_code_chunks"

        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        self.collection = self._create_fresh_collection()

    def _create_fresh_collection(self):
        """
        Creates a fresh collection for each indexed repository.

        For MVP:
        - We support one indexed repo at a time.
        - Re-indexing replaces the old semantic index.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        return self.client.get_or_create_collection(name=self.collection_name)

    def reset(self) -> None:
        self.collection = self._create_fresh_collection()

    def index_chunks(self, chunks: List[Dict]) -> int:
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk["id"])
            documents.append(chunk["content"])
            metadatas.append({
                "path": chunk["path"],
                "chunk_index": chunk["chunk_index"]
            })

        embeddings = self.embedding_model.encode(documents).tolist()

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

        return len(chunks)

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query.strip():
            return []

        query_embedding = self.embedding_model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        output = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(documents, metadatas, distances):
            output.append({
                "path": metadata["path"],
                "chunk_index": metadata["chunk_index"],
                "distance": distance,
                "snippet": document[:500]
            })

        return output