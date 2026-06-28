import os
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class RAGAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def build_context(self, retrieved_chunks: List[Dict]) -> str:
        context_parts = []

        for index, chunk in enumerate(retrieved_chunks, start=1):
            path = chunk.get("path", "unknown")
            chunk_index = chunk.get("chunk_index", "unknown")
            snippet = chunk.get("snippet", "")

            context_parts.append(
                f"[Source {index}]\n"
                f"File: {path}\n"
                f"Chunk: {chunk_index}\n"
                f"Content:\n{snippet}\n"
            )

        return "\n\n".join(context_parts)

    def build_sources(self, retrieved_chunks: List[Dict]) -> List[Dict]:
        sources = []
        seen = set()

        for chunk in retrieved_chunks:
            path = chunk.get("path", "unknown")
            chunk_index = chunk.get("chunk_index", "unknown")
            key = f"{path}:{chunk_index}"

            if key in seen:
                continue

            seen.add(key)

            sources.append(
                {
                    "path": path,
                    "chunk_index": chunk_index,
                    "distance": chunk.get("distance"),
                }
            )

        return sources

    def answer_question(self, question: str, retrieved_chunks: List[Dict]) -> Dict:
        if not retrieved_chunks:
            return {
                "answer": (
                    "I could not find enough relevant information in the indexed repository "
                    "to answer this question."
                ),
                "sources": [],
            }

        context = self.build_context(retrieved_chunks)

        system_prompt = """
You are RepoPilot AI, a codebase assistant.

Your job is to answer questions about a GitHub repository using only the retrieved code/documentation context.

Rules:
1. Ground your answer in the provided context.
2. Mention relevant file paths when explaining.
3. If the context is insufficient, say that clearly.
4. Do not invent files, functions, APIs, or implementation details.
5. Keep the answer practical and useful for a developer.
"""

        user_prompt = f"""
Question:
{question}

Retrieved repository context:
{context}

Answer the question using the retrieved context. Include a short "Relevant files" section at the end.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                },
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                },
            ],
            temperature=0.2,
            max_completion_tokens=700,
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": self.build_sources(retrieved_chunks),
        }

    def summarize_repository(self, retrieved_chunks: List[Dict]) -> Dict:
        if not retrieved_chunks:
            return {
                "summary": (
                    "I could not generate a repository summary because no relevant "
                    "repository chunks were available."
                ),
                "sources": [],
            }

        context = self.build_context(retrieved_chunks)

        system_prompt = """
You are RepoPilot AI, a repository analysis assistant.

Your job is to summarize an indexed GitHub repository using only the retrieved repository context.

Rules:
1. Ground the summary only in the provided context.
2. Do not invent files, libraries, endpoints, features, or architecture.
3. Mention relevant file paths when useful.
4. Keep the output structured and useful for a developer exploring the repository.
5. If some information is unclear, say that it is not visible from the retrieved context.
"""

        user_prompt = f"""
Retrieved repository context:
{context}

Generate a concise repository summary with these sections:

1. Repository Purpose
2. Main Technologies
3. Core Features
4. Important Files or Modules
5. Architecture / Data Flow
6. What a New Developer Should Read First

Use only the retrieved context.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                },
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                },
            ],
            temperature=0.2,
            max_completion_tokens=900,
        )

        summary = response.choices[0].message.content

        return {
            "summary": summary,
            "sources": self.build_sources(retrieved_chunks),
        }









