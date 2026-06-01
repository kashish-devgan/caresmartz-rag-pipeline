"""
Pydantic models for the Hierarchical RAG pipeline.

Two-level document model:
  ParentDocument  - full article stored in Pinecone 'parents' namespace
  ChildChunk      - small overlapping window stored in 'children' namespace
                    each chunk carries parent_id to enable parent lookup
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ingestion models
# ---------------------------------------------------------------------------

class ParentDocument(BaseModel):
    """
    Level-2 node: one per Intercom article.
    Stored in Pinecone namespace='parents'.
    The embedding is built from title + description + full body so the
    parent vector captures the article's overall topic.
    """
    parent_id: str                          # "art_{article_id}"
    article_id: str
    title: str
    description: str = ""
    body: str                               # full cleaned article text
    source_url: str = ""
    image_urls: list[str] = Field(default_factory=list)
    updated_at: int = 0
    collection_id: Optional[str] = None    # Intercom collection, if available

    @property
    def embedding_text(self) -> str:
        """
        Text fed to the embedding model for the parent vector.
        Title is prepended twice to boost its weight in the embedding space.
        """
        parts = [
            f"Title: {self.title}",
            f"Title: {self.title}",             # intentional repetition for weight
            f"Description: {self.description}" if self.description else "",
            f"Content: {self.body[:8000]}"      # cap to avoid token overflow
        ]
        return "\n\n".join(p for p in parts if p)

    @property
    def pinecone_metadata(self) -> dict:
        """Metadata payload stored alongside the parent vector in Pinecone."""
        return {
            "article_id": self.article_id,
            "title": self.title,
            "description": self.description,
            "body": self.body[:10000],          # Pinecone metadata cap
            "source_url": self.source_url,
            "image_urls": self.image_urls,
            "updated_at": self.updated_at,
            "collection_id": self.collection_id or "",
            "doc_type": "parent",
        }


class ChildChunk(BaseModel):
    """
    Level-3 node: one per text window within an article.
    Stored in Pinecone namespace='children'.
    The child_id encodes both article and position for deterministic upserts.
    """
    chunk_id: str                           # "art_{article_id}_chunk_{n}"
    parent_id: str                          # "art_{article_id}" → links to ParentDocument
    article_id: str
    title: str                              # inherited from parent (aids retrieval)
    chunk_text: str                         # the small window of text
    chunk_index: int
    total_chunks: int                       # how many chunks this article produced
    source_url: str = ""
    image_urls: list[str] = Field(default_factory=list)
    updated_at: int = 0

    @property
    def embedding_text(self) -> str:
        """
        Text fed to the embedding model for the child vector.
        Title prefix anchors each chunk to its article topic, which
        dramatically improves retrieval recall for short queries.
        """
        return f"Title: {self.title}\n\nContent: {self.chunk_text}"

    @property
    def pinecone_metadata(self) -> dict:
        """Metadata payload stored alongside the child vector in Pinecone."""
        return {
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
            "article_id": self.article_id,
            "title": self.title,
            "chunk_text": self.chunk_text[:4000],
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "source_url": self.source_url,
            "image_urls": self.image_urls,
            "updated_at": self.updated_at,
            "doc_type": "child",
        }


class HierarchicalIngestResult(BaseModel):
    """Returned after a bulk ingestion run."""
    total_articles: int
    parents_upserted: int
    children_upserted: int
    skipped: int
    errors: int
    duration_seconds: float
    article_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Retrieval models
# ---------------------------------------------------------------------------

class RetrievedParent(BaseModel):
    """
    A parent document returned after child-match → parent-lookup.
    Carries the best child score so results can be ranked.
    """
    parent_id: str
    article_id: str
    title: str
    body: str
    source_url: str
    image_urls: list[str] = Field(default_factory=list)
    best_child_score: float     # highest cosine score among matched children
    matched_chunks: int         # how many children from this article matched


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------

class HierarchicalChatRequest(BaseModel):
    question: str
    top_k_children: int = Field(default=10, ge=3, le=25,
        description="Number of child chunks to retrieve before parent lookup")
    top_k_parents: int = Field(default=3, ge=1, le=5,
        description="Number of unique parent articles to send to the LLM")


class HierarchicalChatResponse(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    retrieval_debug: Optional[dict] = None  # populated in dev mode