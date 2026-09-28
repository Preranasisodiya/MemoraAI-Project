from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine
from app.database.database import Base, engine
from app.models.user import User
from app.routers.auth import router as auth_router
from app.models.document import Document
from app.routers.documents import router as documents_router
from app.routers.search import router as search_router
from app.routers.ask import router as ask_router
from app.models.document_chunk import DocumentChunk

app = FastAPI(
    title="MemoraAI API",
    description="AI-Powered Personal Knowledge Intelligence Platform",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(ask_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
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