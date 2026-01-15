"""
Search Router - Semantic search endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service


router = APIRouter()


class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    """Single search result"""
    content: str
    filename: str
    similarity_score: float
    chunk_index: int


class SearchResponse(BaseModel):
    """Search response with results"""
    query: str
    results: List[SearchResult]
    total_results: int


@router.post("", response_model=SearchResponse)
async def search_documents(request: SearchQuery):
    """
    Search documents semantically.
    
    Finds the most similar document chunks based on meaning, not keywords.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Search in vector store
        results = vector_store.search(request.query, n_results=request.top_k)
        
        # Format results
        search_results = [
            SearchResult(
                content=r["content"],
                filename=r["metadata"].get("filename", "Unknown"),
                similarity_score=round(r["relevance_score"], 4),
                chunk_index=r["metadata"].get("chunk_index", 0)
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """Get statistics about indexed documents"""
    return {
        "total_chunks": vector_store.get_document_count(),
        "status": "ready" if vector_store.is_initialized() else "not initialized"
    }
