"""
Chunking Service - Intelligent text splitting for RAG
"""

from typing import List
import re

from app.config import settings


class ChunkingService:
    """Service for splitting documents into chunks"""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using different separators"""
        if not separators:
            return [text] if text else []
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # Split by current separator
        if separator:
            parts = text.split(separator)
        else:
            # Character-level split as last resort
            parts = list(text)
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            # Add separator back except for last item
            part_with_sep = part + separator if separator else part
            
            if len(current_chunk) + len(part_with_sep) <= self.chunk_size:
                current_chunk += part_with_sep
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If part itself is too large, recursively split it
                if len(part_with_sep) > self.chunk_size and remaining_separators:
                    sub_chunks = self._split_text_recursive(part, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part_with_sep
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _create_overlapping_chunks(self, chunks: List[str]) -> List[str]:
        """Add overlap between chunks for context continuity"""
        if not chunks or self.chunk_overlap <= 0:
            return chunks
        
        overlapping_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapping_chunks.append(chunk)
            else:
                # Get the end of the previous chunk for overlap
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
                overlapping_chunks.append(overlap_text + " " + chunk)
        
        return overlapping_chunks
    
    def split_text(self, text: str, doc_id: str, filename: str) -> List[dict]:
        """
        Split text into chunks with metadata
        
        Returns list of dicts with 'content' and 'metadata' keys
        """
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split the text recursively
        raw_chunks = self._split_text_recursive(text, self.separators)
        
        # Add overlap
        chunks = self._create_overlapping_chunks(raw_chunks)
        
        # Add metadata to each chunk
        result = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Only add non-empty chunks
                result.append({
                    "content": chunk,
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
        
        return result


# Singleton instance
chunking_service = ChunkingService()
