from __future__ import annotations
import time
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from app.core.logger import logger
from app.models.article import ArticleChunk

_model = SentenceTransformer(settings.embedding_model)
_pc = Pinecone(api_key=settings.pinecone_api_key)

def ensure_pinecone_index() -> None:
    existing = [idx["name"] for idx in _pc.list_indexes()]
    if settings.pinecone_index_name in existing:
        logger.info(f"Pinecone index '{settings.pinecone_index_name}' already exists")
        return
    logger.info(f"Creating Pinecone index '{settings.pinecone_index_name}'")
    _pc.create_index(
        name=settings.pinecone_index_name,
        dimension=settings.embedding_dimensions,
        metric="cosine",
        spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region)
    )
    logger.info("Waiting for index to become ready...")
    for _ in range(20):
        if _pc.describe_index(settings.pinecone_index_name).status.get("ready"):
            break
        time.sleep(3)
    logger.info(f"Index '{settings.pinecone_index_name}' is ready")

class PineconeService:
    def __init__(self):
        self._index = _pc.Index(settings.pinecone_index_name)

    def embed_text(self, text: str) -> list[float]:
        return _model.encode(text).tolist()

    def upsert_chunk(self, chunk: ArticleChunk) -> bool:
        try:
            vector = self.embed_text(chunk.embedding_text)
            self._index.upsert(vectors=[{
                "id": chunk.chunk_id,
                "values": vector,
                "metadata": chunk.pinecone_metadata,
            }])
            return True
        except Exception as exc:
            logger.error(f"Failed to upsert chunk {chunk.chunk_id}: {exc}")
            return False

    def upsert_chunks_batch(self, chunks: list[ArticleChunk]) -> dict:
        upserted, errors = 0, 0
        for chunk in chunks:
            if self.upsert_chunk(chunk):
                upserted += 1
            else:
                errors += 1
        return {"upserted": upserted, "errors": errors}

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        vector = self.embed_text(question)
        results = self._index.query(vector=vector, top_k=top_k, include_metadata=True)
        matches = []
        for match in results.matches:
            matches.append({
                "score": round(match.score, 4),
                "chunk_id": match.id,
                "article_id": match.metadata.get("article_id"),
                "title": match.metadata.get("title"),
                "body": match.metadata.get("body"),
                "source_url": match.metadata.get("source_url"),
                "image_urls": match.metadata.get("image_urls", []),
            })
        return matches

    def get_images_by_article_id(self, article_id: str) -> list[str]:
        chunk_ids = [f"{article_id}_chunk_{i}" for i in range(20)]
        try:
            result = self._index.fetch(ids=chunk_ids)
            image_urls = []
            vectors = result.get("vectors", {})
            for vec_id, vec_data in vectors.items():
                metadata = vec_data.get("metadata", {})
                for url in metadata.get("image_urls", []):
                    if url and url not in image_urls:
                        image_urls.append(url)
            return image_urls
        except Exception as exc:
            logger.error(f"Failed to fetch images for {article_id}: {exc}")
            return []

    def index_stats(self) -> dict:
        try:
            stats = self._index.describe_index_stats()
            return {
                "total_vector_count": int(stats.total_vector_count),
                "dimension": int(stats.dimension),
                "index_fullness": float(stats.index_fullness),
                "namespaces": {},
            }
        except Exception as exc:
            logger.error(f"index_stats error: {exc}")
            return {"total_vector_count": 0, "dimension": 0, "index_fullness": 0.0, "namespaces": {}}
