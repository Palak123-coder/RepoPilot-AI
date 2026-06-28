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


class ArchitectureRequest(BaseModel):
    top_k: int = 10


class BugTriageRequest(BaseModel):
    bug_description: str
    top_k: int = 8

