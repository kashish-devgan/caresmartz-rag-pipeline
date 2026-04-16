from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class RawArticle(BaseModel):
    id: str
    type: str = "article"
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    author_id: Optional[int] = None
    state: Optional[str] = None
    url: Optional[str] = None
    updated_at: Optional[int] = None
    created_at: Optional[int] = None
    image_urls: list[str] = Field(default_factory=list)
    class Config:
        extra = "allow"

class ArticleSummary(BaseModel):
    id: str
    title: str = Field(default="Untitled")
    state: str = Field(default="unknown")
    updated_at: int = Field(default=0)
    url: Optional[str] = None

class ArticleChunk(BaseModel):
    chunk_id: str
    article_id: str
    title: str
    chunk_text: str
    chunk_index: int
    source_url: str
    image_urls: list[str] = Field(default_factory=list)
    updated_at: int = Field(default=0)

    @property
    def embedding_text(self) -> str:
        return f"Title: {self.title}\n\nContent: {self.chunk_text}"

    @property
    def pinecone_metadata(self) -> dict:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "body": self.chunk_text[:10000],
            "source_url": self.source_url,
            "chunk_index": self.chunk_index,
            "image_urls": self.image_urls,
            "updated_at": self.updated_at,
        }

class ArticleDocument(BaseModel):
    id: str
    title: str = Field(default="Untitled")
    description: str = Field(default="")
    body: str = Field(default="")
    source_url: str = Field(default="")
    updated_at: int = Field(default=0)
    image_urls: list[str] = Field(default_factory=list)

    @property
    def embedding_text(self) -> str:
        parts = [
            f"Title: {self.title}",
            f"Description: {self.description}" if self.description else "",
            f"Content: {self.body[:6000]}" if self.body else "",
        ]
        return "\n\n".join(p for p in parts if p)

    @property
    def pinecone_metadata(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "body": self.body[:10000],
            "source_url": self.source_url,
            "updated_at": self.updated_at,
            "image_urls": self.image_urls,
        }

class SyncResult(BaseModel):
    total_updated: int
    upserted: int
    skipped: int
    errors: int
    duration_seconds: float
    article_ids: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
