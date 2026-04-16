from __future__ import annotations
from groq import Groq
from app.core.config import settings
from app.core.logger import logger
from app.services.pinecone_service import PineconeService
from app.models.article import ChatRequest, ChatResponse

_groq = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are a helpful support assistant for CareSmartz360, a home care management software.
Answer user questions clearly and accurately based ONLY on the context provided below.
If the context does not contain enough information to answer the question, say so honestly.
Do not make up information. Always be concise, friendly, and professional.
At the end of your answer, mention the article title(s) you referenced."""

def build_prompt(question: str, context_chunks: list[dict]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"\n--- Source {i}: {chunk['title']} ---\n{chunk['body']}\n"
    return f"""Context from CareSmartz360 knowledge base:
{context_text}

User question: {question}

Answer:"""

class RAGService:
    def __init__(self):
        self._pinecone = PineconeService()

    def answer(self, request: ChatRequest) -> ChatResponse:
        logger.info(f"RAG query: '{request.question}'")

        chunks = self._pinecone.query(request.question, top_k=request.top_k)

        if not chunks:
            return ChatResponse(
                answer="I could not find relevant information in the CareSmartz360 knowledge base for your question. Please contact support for assistance.",
                sources=[],
                image_urls=[],
            )

        prompt = build_prompt(request.question, chunks)

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

        sources = [{"title": c["title"], "url": c["source_url"], "score": c["score"]} for c in chunks]
        all_images = []
        for chunk in chunks:
            for url in chunk.get("image_urls", []):
                if url and url not in all_images:
                    all_images.append(url)

        logger.info(f"RAG answer generated. Sources: {[s['title'] for s in sources]}")
        return ChatResponse(answer=answer_text, sources=sources, image_urls=all_images)
