"""
Hierarchical Pinecone service for the CareSmartz RAG pipeline.

Manages TWO namespaces inside a single Pinecone index:

  NAMESPACE_PARENTS   — one vector per article (full article embedding)
  NAMESPACE_CHILDREN  — one vector per chunk  (small window embedding)

Index setup:
  Reuses the same index name as Phase 2 but with namespaces to keep
  hierarchical and flat vectors separated. No new Pinecone index needed.
  If the old flat vectors are in the default namespace they remain
  untouched — hierarchical vectors live in their own namespaces.

Retrieval contract:
  query_hierarchical(question, top_k_children, top_k_parents)
    1. Embed the question
    2. Search NAMESPACE_CHILDREN for top_k_children matches
    3. Extract unique parent_ids from matched children
    4. Fetch those parent vectors from NAMESPACE_PARENTS
    5. Deduplicate + rank by best child score
    6. Return top_k_parents RetrievedParent objects
"""
from __future__ import annotations

import time
from collections import defaultdict

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logger import logger
from app.models.hierarchical_models import (
    ParentDocument,
    ChildChunk,
    RetrievedParent,
)

# ---------------------------------------------------------------------------
# Namespace constants
# ---------------------------------------------------------------------------

NAMESPACE_PARENTS = "hrag_parents"
NAMESPACE_CHILDREN = "hrag_children"

# ---------------------------------------------------------------------------
# Module-level singletons (loaded once at import time)
# ---------------------------------------------------------------------------

_model = SentenceTransformer(settings.embedding_model)
_pc = Pinecone(api_key=settings.pinecone_api_key)


# ---------------------------------------------------------------------------
# Index bootstrap
# ---------------------------------------------------------------------------

def ensure_hierarchical_index() -> None:
    """
    Create the Pinecone index if it does not exist.
    Namespaces are created implicitly on first upsert — no extra setup needed.
    Logs a clear message if the index already exists (Phase 2 reuse case).
    """
    existing = [idx["name"] for idx in _pc.list_indexes()]
    if settings.pinecone_index_name in existing:
        logger.info(
            f"Pinecone index '{settings.pinecone_index_name}' already exists — "
            f"hierarchical namespaces will be created on first upsert"
        )
        return

    logger.info(f"Creating Pinecone index '{settings.pinecone_index_name}'")
    _pc.create_index(
        name=settings.pinecone_index_name,
        dimension=settings.embedding_dimensions,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
        ),
    )
    logger.info("Waiting for index to become ready...")
    for _ in range(20):
        if _pc.describe_index(settings.pinecone_index_name).status.get("ready"):
            break
        time.sleep(3)
    logger.info(f"Index '{settings.pinecone_index_name}' is ready")


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class HierarchicalPineconeService:
    """
    All Pinecone operations for the hierarchical RAG pipeline.

    Embedding is done here (not in the chunker) so the same model
    instance is reused across all operations in a request lifecycle.
    """

    def __init__(self) -> None:
        self._index = _pc.Index(settings.pinecone_index_name)

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns a 384-dim float list."""
        return _model.encode(text, show_progress_bar=False).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Batch embed for efficiency during ingestion.
        sentence-transformers handles batching internally.
        """
        return _model.encode(texts, show_progress_bar=False, batch_size=32).tolist()

    # ------------------------------------------------------------------
    # Upsert — parents
    # ------------------------------------------------------------------

    def upsert_parent(self, parent: ParentDocument) -> bool:
        """Embed and upsert a single parent document."""
        try:
            vector = self.embed(parent.embedding_text)
            self._index.upsert(
                vectors=[{
                    "id": parent.parent_id,
                    "values": vector,
                    "metadata": parent.pinecone_metadata,
                }],
                namespace=NAMESPACE_PARENTS,
            )
            return True
        except Exception as exc:
            logger.error(f"Failed to upsert parent {parent.parent_id}: {exc}")
            return False

    def upsert_parents_batch(self, parents: list[ParentDocument]) -> dict:
        """
        Batch upsert parents.
        Embeds all texts in one model call then upserts in batches of 100
        (Pinecone upsert limit per request).
        """
        if not parents:
            return {"upserted": 0, "errors": 0}

        texts = [p.embedding_text for p in parents]
        try:
            vectors = self.embed_batch(texts)
        except Exception as exc:
            logger.error(f"Batch embed (parents) failed: {exc}")
            return {"upserted": 0, "errors": len(parents)}

        upserted, errors = 0, 0
        batch_size = 100
        for i in range(0, len(parents), batch_size):
            batch_parents = parents[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            pinecone_batch = [
                {
                    "id": p.parent_id,
                    "values": v,
                    "metadata": p.pinecone_metadata,
                }
                for p, v in zip(batch_parents, batch_vectors)
            ]
            try:
                self._index.upsert(
                    vectors=pinecone_batch,
                    namespace=NAMESPACE_PARENTS,
                )
                upserted += len(pinecone_batch)
                logger.info(
                    f"Parents upserted: {upserted}/{len(parents)}"
                )
            except Exception as exc:
                logger.error(f"Parents batch upsert [{i}:{i+batch_size}] failed: {exc}")
                errors += len(pinecone_batch)

        return {"upserted": upserted, "errors": errors}

    # ------------------------------------------------------------------
    # Upsert — children
    # ------------------------------------------------------------------

    def upsert_children_batch(self, children: list[ChildChunk]) -> dict:
        """
        Batch upsert child chunks.
        Same pattern as parents: single batch embed, chunked upsert.
        """
        if not children:
            return {"upserted": 0, "errors": 0}

        texts = [c.embedding_text for c in children]
        try:
            vectors = self.embed_batch(texts)
        except Exception as exc:
            logger.error(f"Batch embed (children) failed: {exc}")
            return {"upserted": 0, "errors": len(children)}

        upserted, errors = 0, 0
        batch_size = 100
        for i in range(0, len(children), batch_size):
            batch_children = children[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            pinecone_batch = [
                {
                    "id": c.chunk_id,
                    "values": v,
                    "metadata": c.pinecone_metadata,
                }
                for c, v in zip(batch_children, batch_vectors)
            ]
            try:
                self._index.upsert(
                    vectors=pinecone_batch,
                    namespace=NAMESPACE_CHILDREN,
                )
                upserted += len(pinecone_batch)
                logger.info(
                    f"Children upserted: {upserted}/{len(children)}"
                )
            except Exception as exc:
                logger.error(
                    f"Children batch upsert [{i}:{i+batch_size}] failed: {exc}"
                )
                errors += len(pinecone_batch)

        return {"upserted": upserted, "errors": errors}

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query_hierarchical(
        self,
        question: str,
        top_k_children: int = 10,
        top_k_parents: int = 3,
    ) -> list[RetrievedParent]:
        """
        Core two-stage retrieval:

        Stage 1 — search children namespace
          Embed the query and find top_k_children similar child chunks.
          Small chunks give precise semantic matching.

        Stage 2 — fetch parent documents
          Group matched children by parent_id.
          Fetch the full parent metadata for each unique parent_id.
          Rank parents by their best child score (highest cosine match).
          Return top_k_parents unique parents.

        Returns:
            List of RetrievedParent sorted by relevance (best score first).
        """
        query_vector = self.embed(question)

        # --- Stage 1: search children ---
        try:
            child_results = self._index.query(
                vector=query_vector,
                top_k=top_k_children,
                namespace=NAMESPACE_CHILDREN,
                include_metadata=True,
            )
        except Exception as exc:
            logger.error(f"Child namespace query failed: {exc}")
            return []

        if not child_results.matches:
            logger.warning("No child matches found for query")
            return []

        logger.info(
            f"Child matches: {len(child_results.matches)} "
            f"(top score: {child_results.matches[0].score:.4f})"
        )

        # --- Stage 2: group by parent_id ---
        # parent_id -> {best_score, matched_chunks}
        parent_scores: dict[str, dict] = defaultdict(
            lambda: {"best_score": 0.0, "matched_chunks": 0}
        )
        for match in child_results.matches:
            pid = match.metadata.get("parent_id", "")
            if not pid:
                continue
            if match.score > parent_scores[pid]["best_score"]:
                parent_scores[pid]["best_score"] = round(match.score, 4)
            parent_scores[pid]["matched_chunks"] += 1

        # Sort parent_ids by best child score descending
        ranked_parent_ids = sorted(
            parent_scores.keys(),
            key=lambda pid: parent_scores[pid]["best_score"],
            reverse=True,
        )[:top_k_parents]

        logger.info(
            f"Unique parents found: {len(parent_scores)} — "
            f"fetching top {len(ranked_parent_ids)}"
        )

        # --- Stage 3: fetch parent metadata ---
        try:
            fetch_result = self._index.fetch(
                ids=ranked_parent_ids,
                namespace=NAMESPACE_PARENTS,
            )
        except Exception as exc:
            logger.error(f"Parent namespace fetch failed: {exc}")
            return []

        retrieved: list[RetrievedParent] = []
        vectors = fetch_result.get("vectors", {})

        for pid in ranked_parent_ids:
            if pid not in vectors:
                logger.warning(f"Parent {pid} not found in index — skipping")
                continue
            meta = vectors[pid].get("metadata", {})
            retrieved.append(RetrievedParent(
                parent_id=pid,
                article_id=meta.get("article_id", ""),
                title=meta.get("title", "Untitled"),
                body=meta.get("body", ""),
                source_url=meta.get("source_url", ""),
                image_urls=meta.get("image_urls", []),
                best_child_score=parent_scores[pid]["best_score"],
                matched_chunks=parent_scores[pid]["matched_chunks"],
            ))

        logger.info(
            f"Hierarchical retrieval complete: {len(retrieved)} parents returned"
        )
        return retrieved

    # ------------------------------------------------------------------
    # Stats / admin
    # ------------------------------------------------------------------

    def index_stats(self) -> dict:
        """Returns vector counts per namespace for the admin endpoint."""
        try:
            stats = self._index.describe_index_stats()
            ns = stats.namespaces or {}
            return {
                "total_vector_count": int(stats.total_vector_count),
                "dimension": int(stats.dimension),
                "namespaces": {
                    NAMESPACE_PARENTS: {
                        "vector_count": int(
                            ns.get(NAMESPACE_PARENTS, {}).get("vector_count", 0)
                        )
                    },
                    NAMESPACE_CHILDREN: {
                        "vector_count": int(
                            ns.get(NAMESPACE_CHILDREN, {}).get("vector_count", 0)
                        )
                    },
                },
            }
        except Exception as exc:
            logger.error(f"index_stats error: {exc}")
            return {"total_vector_count": 0, "dimension": 0, "namespaces": {}}

    def delete_article(self, article_id: str) -> dict:
        """
        Delete all vectors (parent + children) for a given article_id.
        Used when an Intercom article is deleted or unpublished.
        """
        parent_id = f"art_{article_id}"
        deleted_parents, deleted_children = 0, 0

        # delete parent
        try:
            self._index.delete(ids=[parent_id], namespace=NAMESPACE_PARENTS)
            deleted_parents = 1
        except Exception as exc:
            logger.error(f"Failed to delete parent {parent_id}: {exc}")

        # delete children (chunk IDs are deterministic: art_{id}_chunk_{n})
        # fetch up to 50 chunks; real articles rarely exceed this
        child_ids = [f"{parent_id}_chunk_{i}" for i in range(50)]
        try:
            self._index.delete(ids=child_ids, namespace=NAMESPACE_CHILDREN)
            deleted_children = 1  # best-effort; Pinecone ignores missing IDs
        except Exception as exc:
            logger.error(f"Failed to delete children for {parent_id}: {exc}")

        return {
            "article_id": article_id,
            "deleted_parents": deleted_parents,
            "deleted_children_attempted": len(child_ids),
        }