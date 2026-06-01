"""
CareSmartz Hierarchical RAG — service package.

Public surface:
    HierarchicalRAGService      — answer() method for chat
    HierarchicalPineconeService — query_hierarchical(), upsert_*, index_stats()
    run_full_sync               — ingest all 705 articles
    run_delta_sync              — ingest recently updated articles
    ensure_hierarchical_index   — idempotent index bootstrap
"""
from app.services.hierarchical.rag_hrag import HierarchicalRAGService
from app.services.hierarchical.pinecone_hrag import (
    HierarchicalPineconeService,
    ensure_hierarchical_index,
)
from app.services.hierarchical.ingest import run_full_sync, run_delta_sync

__all__ = [
    "HierarchicalRAGService",
    "HierarchicalPineconeService",
    "ensure_hierarchical_index",
    "run_full_sync",
    "run_delta_sync",
]