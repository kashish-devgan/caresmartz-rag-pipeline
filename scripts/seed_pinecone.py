import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logger import logger
from app.services.pinecone_service import ensure_pinecone_index, PineconeService
from app.services.data_service import articles_to_chunks
from app.data.seed_data import get_fabricated_articles

def main():
    logger.info("Seeding Pinecone with 30 CareSmartz articles...")
    ensure_pinecone_index()
    articles = get_fabricated_articles()
    chunks = articles_to_chunks(articles)
    logger.info(f"Total chunks to upsert: {len(chunks)}")
    svc = PineconeService()
    result = svc.upsert_chunks_batch(chunks)
    logger.info(f"Done — upserted={result['upserted']} errors={result['errors']}")

if __name__ == "__main__":
    main()
