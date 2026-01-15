"""
Document Service - Handles PDF and TXT file processing
"""

import fitz  # PyMuPDF
import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

from app.config import settings


class DocumentService:
    """Service for document upload and text extraction"""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.metadata_file = self.upload_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load document metadata from file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save document metadata to file"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def save_file(self, filename: str, content: bytes) -> str:
        """Save uploaded file and return document ID"""
        doc_id = str(uuid.uuid4())[:8]
        
        # Create safe filename
        safe_filename = f"{doc_id}_{filename}"
        file_path = self.upload_dir / safe_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store metadata
        self.metadata[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "saved_as": safe_filename,
            "upload_date": datetime.now().isoformat(),
            "file_size": len(content),
            "chunk_count": 0
        }
        self._save_metadata()
        
        return doc_id
    
    def extract_text(self, doc_id: str) -> str:
        """Extract text from a document"""
        if doc_id not in self.metadata:
            raise ValueError(f"Document {doc_id} not found")
        
        doc_info = self.metadata[doc_id]
        file_path = self.upload_dir / doc_info["saved_as"]
        filename = doc_info["filename"].lower()
        
        if filename.endswith(".pdf"):
            return self._extract_pdf(file_path)
        elif filename.endswith(".txt"):
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text_parts = []
        
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_txt(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        # Try different encodings
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Fallback: read as binary and decode with errors ignored
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    
    def update_chunk_count(self, doc_id: str, count: int):
        """Update the chunk count for a document"""
        if doc_id in self.metadata:
            self.metadata[doc_id]["chunk_count"] = count
            self._save_metadata()
    
    def get_document(self, doc_id: str) -> Optional[dict]:
        """Get document metadata"""
        return self.metadata.get(doc_id)
    
    def list_documents(self) -> list:
        """List all documents"""
        return list(self.metadata.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id not in self.metadata:
            return False
        
        doc_info = self.metadata[doc_id]
        file_path = self.upload_dir / doc_info["saved_as"]
        
        # Delete file
        if file_path.exists():
            os.remove(file_path)
        
        # Remove from metadata
        del self.metadata[doc_id]
        self._save_metadata()
        
        return True


# Singleton instance
document_service = DocumentService()
