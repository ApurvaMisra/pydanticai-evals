from typing import Literal

from pydantic import BaseModel


class Citation(BaseModel):
    source_type: Literal["web", "internal_db"]
    url_or_doc_id: str
    snippet: str


class FinalAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Literal["high", "medium", "low"]
