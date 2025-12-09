"""
JapaLearn Backend API
Main FastAPI application
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.cache import close_redis
from app.core.config import get_settings
from app.core.db import init_db
from app.routers import auth, chat, conversation, translate, voice, word

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "JapaLearn API",
        "version": settings.app_version,
        "docs": "/docs",
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(translate.router, prefix="/api/v1", tags=["Translation"])
app.include_router(word.router, prefix="/api/v1/word", tags=["Words"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(conversation.router, prefix="/api/v1/conversation", tags=["Conversation Practice"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.debug,
    )
