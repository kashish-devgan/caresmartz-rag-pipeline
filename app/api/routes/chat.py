from fastapi import APIRouter, HTTPException
from app.models.article import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.core.logger import logger

router = APIRouter(prefix="/api/chat", tags=["RAG Chatbot"])

@router.post("", response_model=ChatResponse, summary="Ask the CareSmartz RAG chatbot")
async def chat(request: ChatRequest):
    try:
        svc = RAGService()
        return svc.answer(request)
    except Exception as exc:
        logger.error(f"Chat error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
