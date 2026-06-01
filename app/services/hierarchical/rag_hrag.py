"""
Hierarchical RAG service for the CareSmartz pipeline.

Orchestrates the full query lifecycle:
  1. Call HierarchicalPineconeService.query_hierarchical()
     -> returns RetrievedParent list (full article bodies)
  2. Build a structured prompt with rich multi-article context
  3. Call Groq LLM
  4. Return HierarchicalChatResponse with answer + sources + images

Prompt design:
  Each parent article is presented as a clearly labelled Source block
  so the LLM can attribute claims to specific articles.
  The system prompt enforces citation and prohibits hallucination.
"""
from __future__ import annotations

from groq import Groq

from app.core.config import settings
from app.core.logger import logger
from app.models.hierarchical_models import (
    HierarchicalChatRequest,
    HierarchicalChatResponse,
    RetrievedParent,
)
from app.services.hierarchical.pinecone_hrag import HierarchicalPineconeService

# ---------------------------------------------------------------------------
# Groq client singleton
# ---------------------------------------------------------------------------

_groq = Groq(api_key=settings.groq_api_key)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful and knowledgeable support assistant for CareSmartz360, a home care management software platform.

Your job is to answer user questions clearly, accurately, and concisely using ONLY the article content provided below as context.

Rules you must always follow:
- Base every claim on the provided articles. Do not use outside knowledge.
- If the context does not fully answer the question, say so honestly and suggest the user contact CareSmartz360 support.
- At the end of your response, list the article title(s) you referenced under a "Sources:" heading.
- Be concise and friendly. Use numbered steps for procedural answers.
- Do not repeat the user's question back to them."""


def _build_prompt(question: str, parents: list[RetrievedParent]) -> str:
    """
    Assemble the user-turn prompt.

    Each retrieved parent article is presented as a numbered Source block.
    The LLM sees full article bodies — this is the key advantage over
    flat RAG which only provides 3 small fragments.
    """
    context_blocks: list[str] = []
    for i, parent in enumerate(parents, 1):
        block = (
            f"--- Source {i}: {parent.title} ---\n"
            f"URL: {parent.source_url}\n\n"
            f"{parent.body}"
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)

    return (
        f"Context from the CareSmartz360 knowledge base "
        f"({len(parents)} article(s) retrieved):\n\n"
        f"{context_text}\n\n"
        f"---\n\n"
        f"User question: {question}\n\n"
        f"Answer:"
    )


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class HierarchicalRAGService:
    """
    Drop-in replacement for the flat RAGService.
    Uses two-level retrieval (child precision + parent context)
    instead of flat top-k chunk retrieval.
    """

    def __init__(self) -> None:
        self._pinecone = HierarchicalPineconeService()

    def answer(
        self,
        request: HierarchicalChatRequest,
    ) -> HierarchicalChatResponse:
        """
        Full pipeline: retrieve → prompt → generate → respond.

        Steps:
          1. Two-stage Pinecone retrieval (children → parents)
          2. Early-exit if nothing retrieved
          3. Prompt assembly with full article bodies
          4. Groq LLM call
          5. Response packaging with sources + images
        """
        logger.info(
            f"HRAG query: '{request.question}' "
            f"(top_k_children={request.top_k_children}, "
            f"top_k_parents={request.top_k_parents})"
        )

        # --- Step 1: Hierarchical retrieval ---
        parents = self._pinecone.query_hierarchical(
            question=request.question,
            top_k_children=request.top_k_children,
            top_k_parents=request.top_k_parents,
        )

        # --- Step 2: No results guard ---
        if not parents:
            logger.warning("HRAG: no parents retrieved — returning fallback")
            return HierarchicalChatResponse(
                answer=(
                    "I could not find relevant information in the "
                    "CareSmartz360 knowledge base for your question. "
                    "Please contact CareSmartz360 support for assistance."
                ),
                sources=[],
                image_urls=[],
            )

        # --- Step 3: Build prompt ---
        prompt = _build_prompt(request.question, parents)

        # --- Step 4: Groq LLM call ---
        try:
            response = _groq.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            answer_text = response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error(f"Groq LLM call failed: {exc}")
            return HierarchicalChatResponse(
                answer="Sorry, I encountered an error generating a response. Please try again.",
                sources=[],
                image_urls=[],
            )

        # --- Step 5: Package response ---
        sources = [
            {
                "title": p.title,
                "url": p.source_url,
                "score": p.best_child_score,
                "matched_chunks": p.matched_chunks,
            }
            for p in parents
        ]

        # Collect unique image URLs from all retrieved parents
        all_images: list[str] = []
        for parent in parents:
            for url in parent.image_urls:
                if url and url not in all_images:
                    all_images.append(url)

        # Debug metadata (returned in dev mode; stripped in production by caller)
        retrieval_debug = {
            "parents_retrieved": len(parents),
            "top_parent_title": parents[0].title,
            "top_parent_score": parents[0].best_child_score,
        }

        logger.info(
            f"HRAG answer generated. "
            f"Sources: {[s['title'] for s in sources]}"
        )

        return HierarchicalChatResponse(
            answer=answer_text,
            sources=sources,
            image_urls=all_images,
            retrieval_debug=(
                retrieval_debug if settings.app_env == "development" else None
            ),
        )