"""
Embedding Service - Generate embeddings using local Sentence Transformers
Fast, free, and no rate limits - perfect for RAG applications.
"""

from typing import List
from sentence_transformers import SentenceTransformer
from app.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using local Sentence Transformers"""
    
    def __init__(self):
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the local embedding model"""
        try:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise e
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise e
    
    def get_query_embedding(self, text: str) -> List[float]:
        """Get embedding for a query (same as document embedding for this model)"""
        return self.get_embedding(text)
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts at once (very fast - no delays needed)"""
        if not texts:
            return []
        
        logger.info(f"Processing {len(texts)} chunks in batch...")
        
        try:
            # Process all texts at once - sentence-transformers handles batching efficiently
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            result = [emb.tolist() for emb in embeddings]
            logger.info(f"Completed all {len(texts)} chunks")
            return result
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise e


# Singleton instance
embedding_service = EmbeddingService()
