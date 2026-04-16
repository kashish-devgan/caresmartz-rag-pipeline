from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api.routes.articles import router as articles_router
from app.api.routes.sync import router as sync_router
from app.api.routes.chat import router as chat_router
from app.api.routes.admin import router as admin_router
from app.services.pinecone_service import ensure_pinecone_index
from app.services.scheduler_service import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CareSmartz RAG service starting...")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Pinecone    : {settings.pinecone_index_name}")
    logger.info(f"  Embed model : {settings.embedding_model}")
    logger.info(f"  LLM         : {settings.groq_model}")
    logger.info(f"  Daily sync  : {settings.sync_trigger_hour:02d}:{settings.sync_trigger_minute:02d} UTC")
    ensure_pinecone_index()
    start_scheduler()
    logger.info("Ready to serve requests.")
    yield
    stop_scheduler()
    logger.info("Shutting down.")

app = FastAPI(title="CareSmartz RAG API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(articles_router)
app.include_router(sync_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "env": settings.app_env, "version": "2.0.0"}
