"""
Chat Router - API endpoints for chat and RAG queries
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import ChatRequest, ChatResponse, ConversationHistory, Message
from app.services.rag_service import rag_service


router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a RAG-powered response
    
    Modes:
    - qa: Question answering based on documents
    - summary: Generate a summary of document content
    - quiz: Generate quiz questions from documents
    """
    try:
        result = rag_service.query(
            question=request.question,
            mode=request.mode,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            conversation_id=result["conversation_id"],
            mode=result["mode"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_history(conversation_id: str):
    """Get conversation history by ID"""
    history = rag_service.get_history(conversation_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationHistory(
        conversation_id=history["conversation_id"],
        messages=[
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                mode=msg.get("mode")
            )
            for msg in history["messages"]
        ],
        created_at=history["created_at"],
        updated_at=history["updated_at"]
    )


@router.delete("/history/{conversation_id}")
async def delete_history(conversation_id: str):
    """Delete conversation history"""
    deleted = rag_service.delete_history(conversation_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": f"Conversation {conversation_id} deleted"}


@router.get("/conversations")
async def list_conversations():
    """List all conversations"""
    return rag_service.list_conversations()
