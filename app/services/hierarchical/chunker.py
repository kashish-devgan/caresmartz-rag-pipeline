"""
Hierarchical chunker for the CareSmartz RAG pipeline.

For each Intercom article this module produces TWO levels of representation:

  ParentDocument  — the full cleaned article text (one per article)
  ChildChunk list — small overlapping windows (many per article)

Why two levels?
  Child chunks are small (~100 words) so their embeddings are precise —
  a user query matches tightly against the exact paragraph that answers it.
  The parent carries the full article so the LLM receives rich context,
  not just the 100-word fragment that matched.

Chunking strategy:
  - Sentence-aware splitting: never cuts mid-sentence
  - Configurable CHILD_SIZE (words) and CHILD_OVERLAP (words)
  - Minimum chunk guard: chunks shorter than MIN_CHUNK_WORDS are merged
    into the previous chunk to avoid near-empty embeddings
"""
from __future__ import annotations

import re
import time

from app.core.logger import logger
from app.models.article import RawArticle          # existing model, reused
from app.models.hierarchical_models import ParentDocument, ChildChunk

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHILD_SIZE = 100        # target words per child chunk
CHILD_OVERLAP = 20      # words of overlap between consecutive children
MIN_CHUNK_WORDS = 30    # discard or merge chunks shorter than this


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    if not text:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, char in {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&nbsp;": " ",
    }.items():
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


def _split_sentences(text: str) -> list[str]:
    """
    Naive sentence splitter that handles common abbreviations.
    Good enough for help-article prose; avoids heavy NLP dependencies.
    """
    # Split on . ! ? followed by whitespace + uppercase
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in raw if s.strip()]


def _sentences_to_word_chunks(
    sentences: list[str],
    chunk_size: int = CHILD_SIZE,
    overlap: int = CHILD_OVERLAP,
    min_words: int = MIN_CHUNK_WORDS,
) -> list[str]:
    """
    Slides a word-count window over the sentence list.
    Always breaks on sentence boundaries — never mid-sentence.

    Algorithm:
      1. Accumulate sentences until word count >= chunk_size
      2. Record that window as a chunk
      3. Back up `overlap` words worth of sentences for the next window
    """
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())
        current.append(sentence)
        current_words += sentence_words

        if current_words >= chunk_size:
            chunks.append(" ".join(current))
            # slide back: drop sentences from the front until we've
            # shed (chunk_size - overlap) words
            words_to_drop = chunk_size - overlap
            dropped = 0
            while current and dropped < words_to_drop:
                dropped += len(current[0].split())
                current.pop(0)
            current_words = sum(len(s.split()) for s in current)

    # flush remaining sentences
    if current:
        tail = " ".join(current)
        if chunks and len(tail.split()) < min_words:
            # merge short tail into last chunk
            chunks[-1] = chunks[-1] + " " + tail
        else:
            chunks.append(tail)

    # final guard: drop any chunk that is still too short
    return [c for c in chunks if len(c.split()) >= min_words]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def article_to_hierarchy(
    article: RawArticle,
) -> tuple[ParentDocument, list[ChildChunk]]:
    """
    Convert a single RawArticle into one ParentDocument and N ChildChunks.

    Returns:
        (parent, children)  — both ready to upsert into Pinecone
    """
    body = _clean_text(article.body or "")
    description = _clean_text(article.description or "")
    full_text = f"{description}\n\n{body}".strip() if description else body

    parent_id = f"art_{article.id}"
    now = article.updated_at or int(time.time())

    parent = ParentDocument(
        parent_id=parent_id,
        article_id=str(article.id),
        title=article.title or "Untitled",
        description=description,
        body=full_text,
        source_url=article.url or "",
        image_urls=article.image_urls or [],
        updated_at=now,
        collection_id=None,                # populated by caller if available
    )

    if not full_text:
        logger.warning(f"Article {article.id} '{article.title}' has no body — "
                       "parent stored, no children created")
        return parent, []

    sentences = _split_sentences(full_text)
    raw_chunks = _sentences_to_word_chunks(sentences)

    children: list[ChildChunk] = []
    for idx, chunk_text in enumerate(raw_chunks):
        children.append(ChildChunk(
            chunk_id=f"{parent_id}_chunk_{idx}",
            parent_id=parent_id,
            article_id=str(article.id),
            title=article.title or "Untitled",
            chunk_text=chunk_text,
            chunk_index=idx,
            total_chunks=len(raw_chunks),
            source_url=article.url or "",
            image_urls=article.image_urls or [],
            updated_at=now,
        ))

    logger.info(
        f"Article {article.id} '{article.title}' -> "
        f"1 parent, {len(children)} children "
        f"(~{len(full_text.split())} words total)"
    )
    return parent, children


def articles_to_hierarchy(
    articles: list[RawArticle],
) -> tuple[list[ParentDocument], list[ChildChunk]]:
    """
    Batch conversion: list of RawArticles -> (all_parents, all_children).
    Skips articles that produce zero children with a warning.
    """
    all_parents: list[ParentDocument] = []
    all_children: list[ChildChunk] = []

    for article in articles:
        parent, children = article_to_hierarchy(article)
        all_parents.append(parent)
        all_children.extend(children)

    logger.info(
        f"Hierarchical chunking complete: "
        f"{len(all_parents)} parents, {len(all_children)} children "
        f"from {len(articles)} articles"
    )
    return all_parents, all_children