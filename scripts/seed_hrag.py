"""
One-shot script to populate the hierarchical Pinecone index.

Run this ONCE to ingest all 705 Intercom articles into the
hrag_parents and hrag_children namespaces.

Usage:
    python scripts/seed_hrag.py

Prerequisites:
    - .env configured with INTERCOM_ACCESS_TOKEN, PINECONE_API_KEY, etc.
    - pip install -r requirements.txt
    - Server does NOT need to be running (standalone script)

After this completes, start the server and test with:
    curl -X POST http://localhost:8000/api/hrag/chat \
         -H "Content-Type: application/json" \
         -d '{"question": "how do I add a caregiver?"}'
"""
import sys
import time
from pathlib import Path

# Make sure project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logger import logger
from app.services.hierarchical.pinecone_hrag import ensure_hierarchical_index
from app.services.hierarchical.ingest import run_full_sync


def main() -> None:
    logger.info("=" * 60)
    logger.info("CareSmartz Hierarchical RAG — Full Seed")
    logger.info("=" * 60)
    logger.info("Step 1: Ensuring Pinecone index exists...")
    ensure_hierarchical_index()

    logger.info("Step 2: Starting full sync of all Intercom articles...")
    logger.info("  This fetches all 705 articles — expect 5-15 minutes.")
    logger.info("  Progress is logged every 50 articles.")

    t0 = time.time()
    result = run_full_sync()
    elapsed = round(time.time() - t0, 1)

    logger.info("=" * 60)
    logger.info("Seed complete!")
    logger.info(f"  Total articles   : {result.total_articles}")
    logger.info(f"  Parents upserted : {result.parents_upserted}")
    logger.info(f"  Children upserted: {result.children_upserted}")
    logger.info(f"  Skipped          : {result.skipped}")
    logger.info(f"  Errors           : {result.errors}")
    logger.info(f"  Duration         : {elapsed}s")
    logger.info("=" * 60)

    if result.errors > 0:
        logger.warning(
            f"{result.errors} errors during ingestion — "
            "check logs above for details. Re-run to retry failed articles."
        )
        sys.exit(1)

    logger.info("Ready. Start the server and POST to /api/hrag/chat")


if __name__ == "__main__":
    main()