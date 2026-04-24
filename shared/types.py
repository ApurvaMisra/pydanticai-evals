from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class InternalDoc(BaseModel):
    id: str
    title: str
    topic: str
    body: str
    created_at: str
