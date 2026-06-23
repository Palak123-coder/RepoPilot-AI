from pydantic import BaseModel


class IndexRequest(BaseModel):
    repo_url: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5