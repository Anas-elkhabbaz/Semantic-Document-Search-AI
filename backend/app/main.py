"""
Semantic Document Search - FastAPI Backend
A simple AI-powered document search application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import documents, search
from app.services.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Starting Semantic Document Search Backend...")
    print(f"📊 Vector store has {vector_store.get_document_count()} chunks indexed")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Semantic Document Search API",
    description="AI-powered semantic search for documents using embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "Semantic Document Search",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": True,
            "vector_store": vector_store.is_initialized(),
            "chunks_indexed": vector_store.get_document_count()
        }
    }
