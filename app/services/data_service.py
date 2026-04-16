from __future__ import annotations
import re
import time
from app.models.article import RawArticle, ArticleChunk
from app.core.logger import logger

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks

def articles_to_chunks(articles: list[RawArticle]) -> list[ArticleChunk]:
    all_chunks: list[ArticleChunk] = []
    for article in articles:
        body = _clean_text(article.body or "")
        description = _clean_text(article.description or "")
        full_text = f"{description}\n\n{body}".strip() if description else body
        if not full_text:
            logger.warning(f"Article {article.id} has no body — skipping chunking")
            continue
        chunks = _split_into_chunks(full_text)
        logger.info(f"Article {article.id} '{article.title}' → {len(chunks)} chunk(s)")
        for idx, chunk_text in enumerate(chunks):
            all_chunks.append(ArticleChunk(
                chunk_id=f"{article.id}_chunk_{idx}",
                article_id=str(article.id),
                title=article.title or "Untitled",
                chunk_text=chunk_text,
                chunk_index=idx,
                source_url=article.url or "",
                image_urls=article.image_urls or [],
                updated_at=article.updated_at or int(time.time()),
            ))
    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks
