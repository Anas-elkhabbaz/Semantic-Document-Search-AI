"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ChatMode(str, Enum):
    """Available chat modes"""
    QA = "qa"
    SUMMARY = "summary"
    QUIZ = "quiz"


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    id: str
    filename: str
    chunk_count: int
    message: str


class DocumentInfo(BaseModel):
    """Document information"""
    id: str
    filename: str
    upload_date: str
    chunk_count: int
    file_size: int


class ChatRequest(BaseModel):
    """Chat request payload"""
    question: str = Field(..., min_length=1, description="User's question")
    mode: ChatMode = Field(default=ChatMode.QA, description="Chat mode")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for history")


class SourceChunk(BaseModel):
    """Source chunk from document"""
    document: str
    content: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Chat response payload"""
    answer: str
    sources: List[SourceChunk]
    conversation_id: str
    mode: ChatMode


class Message(BaseModel):
    """Single message in conversation history"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    mode: Optional[ChatMode] = None


class ConversationHistory(BaseModel):
    """Conversation history"""
    conversation_id: str
    messages: List[Message]
    created_at: str
    updated_at: str
