from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine
import app.models  # Ensures all models (User, Document, DocumentChunk, Conversation, ChatMessage) are registered
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.search import router as search_router
from app.routers.ask import router as ask_router
from app.routers.conversations import router as conversations_router

app = FastAPI(
    title="MemoraAI API",
    description="AI-Powered Personal Knowledge Intelligence Platform",
    version="0.2.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(conversations_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "MemoraAI Backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MemoraAI Backend"
    }


@app.get("/api/database-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {
            "database": "connected",
            "result": result.scalar()
        }