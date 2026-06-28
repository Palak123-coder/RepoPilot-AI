from pydantic import BaseModel


class IndexRequest(BaseModel):
    repo_url: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class RepoSummaryRequest(BaseModel):
    top_k: int = 10




