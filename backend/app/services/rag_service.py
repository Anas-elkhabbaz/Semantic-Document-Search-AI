"""
RAG Service - Retrieval Augmented Generation using Gemini
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import uuid

import google.generativeai as genai

from app.config import settings
from app.services.vector_store import vector_store
from app.models.schemas import ChatMode, SourceChunk, Message


# Prompt templates for different modes
PROMPTS = {
    ChatMode.QA: """You are a helpful study assistant. Answer the following question based ONLY on the provided context from the student's documents.

**Rules:**
1. Only use information from the provided context
2. If the answer is not in the context, say "I couldn't find this information in your documents."
3. Be concise and clear
4. Cite which document the information comes from

**Context:**
{context}

**Question:** {question}

**Answer:**""",

    ChatMode.SUMMARY: """You are a helpful study assistant. Create a comprehensive summary of the provided content from the student's documents.

**Rules:**
1. Summarize the key points from the context
2. Organize the summary with bullet points or sections
3. Be concise but complete
4. Include the main concepts and important details

**Content to Summarize:**
{context}

**User Request:** {question}

**Summary:**""",

    ChatMode.QUIZ: """You are a helpful study assistant. Generate a quiz based on the provided content from the student's documents.

**Rules:**
1. Create 5 multiple choice questions (MCQs)
2. Each question should have 4 options (A, B, C, D)
3. Mark the correct answer
4. Questions should test understanding, not just memorization
5. Format clearly with question numbers

**Content:**
{context}

**User Request:** {question}

**Quiz:**"""
}


class RAGService:
    """Service for RAG-based question answering"""
    
    def __init__(self):
        self.history_dir = settings.history_dir
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini chat model"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def query(
        self,
        question: str,
        mode: ChatMode = ChatMode.QA,
        conversation_id: Optional[str] = None
    ) -> dict:
        """
        Process a query using RAG
        
        Args:
            question: User's question
            mode: Chat mode (qa, summary, quiz)
            conversation_id: Optional conversation ID for history
            
        Returns:
            Dict with answer, sources, and conversation_id
        """
        # Check if model is initialized
        if not self.model:
            return {
                "answer": "⚠️ Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file.",
                "sources": [],
                "conversation_id": conversation_id or str(uuid.uuid4())[:8],
                "mode": mode
            }
        
        # Generate new conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())[:8]
        
        # Retrieve relevant documents
        try:
            search_results = vector_store.search(question)
        except Exception as e:
            return {
                "answer": f"⚠️ Error searching documents: {str(e)}",
                "sources": [],
                "conversation_id": conversation_id,
                "mode": mode
            }
        
        if not search_results:
            return {
                "answer": "I don't have any documents to search. Please upload some documents first.",
                "sources": [],
                "conversation_id": conversation_id,
                "mode": mode
            }
        
        # Build context from search results
        context = self._build_context(search_results)
        
        # Get the appropriate prompt template
        prompt = PROMPTS[mode].format(
            context=context,
            question=question
        )
        
        # Generate response with error handling
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                answer = "⚠️ API rate limit reached. Please wait a moment and try again."
            elif "API key" in error_msg:
                answer = "⚠️ Invalid API key. Please check your GEMINI_API_KEY in the .env file."
            else:
                answer = f"⚠️ Error generating response: {error_msg}"
            
            return {
                "answer": answer,
                "sources": [],
                "conversation_id": conversation_id,
                "mode": mode
            }
        
        # Format sources
        sources = [
            SourceChunk(
                document=result["metadata"].get("filename", "Unknown"),
                content=result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                relevance_score=result["relevance_score"]
            )
            for result in search_results[:3]  # Top 3 sources
        ]
        
        # Save to history
        self._save_to_history(conversation_id, question, answer, mode)
        
        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id,
            "mode": mode
        }
    
    def _build_context(self, search_results: List[dict]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            filename = result["metadata"].get("filename", "Document")
            content = result["content"]
            context_parts.append(f"[Source {i}: {filename}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _save_to_history(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        mode: ChatMode
    ):
        """Save conversation to history file"""
        history_file = self.history_dir / f"{conversation_id}.json"
        
        # Load existing history or create new
        if history_file.exists():
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = {
                "conversation_id": conversation_id,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Add messages
        timestamp = datetime.now().isoformat()
        history["messages"].extend([
            {"role": "user", "content": question, "timestamp": timestamp, "mode": mode.value},
            {"role": "assistant", "content": answer, "timestamp": timestamp, "mode": mode.value}
        ])
        history["updated_at"] = timestamp
        
        # Save
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_history(self, conversation_id: str) -> Optional[dict]:
        """Get conversation history"""
        history_file = self.history_dir / f"{conversation_id}.json"
        
        if not history_file.exists():
            return None
        
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def delete_history(self, conversation_id: str) -> bool:
        """Delete conversation history"""
        history_file = self.history_dir / f"{conversation_id}.json"
        
        if history_file.exists():
            history_file.unlink()
            return True
        return False
    
    def list_conversations(self) -> List[dict]:
        """List all conversations"""
        conversations = []
        
        for file in self.history_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                conversations.append({
                    "conversation_id": data["conversation_id"],
                    "message_count": len(data["messages"]),
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"]
                })
        
        return sorted(conversations, key=lambda x: x["updated_at"], reverse=True)


# Singleton instance
rag_service = RAGService()
