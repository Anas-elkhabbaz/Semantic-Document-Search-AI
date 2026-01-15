"""
Vector Store Service - ChromaDB for storing and searching embeddings
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.embedding_service import embedding_service


class VectorStore:
    """ChromaDB-based vector store for document chunks"""
    
    def __init__(self):
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create the main collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def is_initialized(self) -> bool:
        """Check if vector store is initialized"""
        return self.collection is not None
    
    def add_documents(self, chunks: List[dict], doc_id: str) -> int:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of dicts with 'content' and 'metadata' keys
            doc_id: Document ID for reference
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.get_embeddings_batch(texts)
        
        # Prepare data for ChromaDB
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        return len(chunks)
    
    def search(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching documents with scores
        """
        if n_results is None:
            n_results = settings.top_k_results
        
        # Get query embedding
        query_embedding = embedding_service.get_query_embedding(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "relevance_score": 1 - (results["distances"][0][i] if results["distances"] else 0)
                })
        
        return formatted
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document"""
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            
            return True
        except Exception:
            return False
    
    def get_document_count(self) -> int:
        """Get total number of chunks in the store"""
        return self.collection.count()
    
    def get_all_documents(self) -> List[str]:
        """Get unique document IDs"""
        results = self.collection.get(include=["metadatas"])
        
        doc_ids = set()
        for metadata in results.get("metadatas", []):
            if metadata and "doc_id" in metadata:
                doc_ids.add(metadata["doc_id"])
        
        return list(doc_ids)


# Singleton instance
vector_store = VectorStore()
