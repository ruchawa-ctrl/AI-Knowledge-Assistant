from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    num_chunks: int
    num_chars: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class Source(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    snippet: str
    score: float


class ChatRequest(BaseModel):
    message: str
    top_k: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: list[Source] = []
    created_at: datetime
