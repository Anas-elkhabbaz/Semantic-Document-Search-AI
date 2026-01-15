"""
Documents Router - API endpoints for document management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from app.models.schemas import DocumentUploadResponse, DocumentInfo
from app.services.document_service import document_service
from app.services.chunking_service import chunking_service
from app.services.vector_store import vector_store


router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document (PDF or TXT)
    
    The document will be:
    1. Saved to storage
    2. Text extracted
    3. Split into chunks
    4. Embedded and indexed in vector store
    """
    # Validate file type
    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        doc_id = document_service.save_file(file.filename, content)
        
        # Extract text
        text = document_service.extract_text(doc_id)
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from document"
            )
        
        # Chunk text
        chunks = chunking_service.split_text(text, doc_id, file.filename)
        
        # Add to vector store
        chunk_count = vector_store.add_documents(chunks, doc_id)
        
        # Update metadata
        document_service.update_chunk_count(doc_id, chunk_count)
        
        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            chunk_count=chunk_count,
            message=f"Document uploaded and indexed successfully with {chunk_count} chunks"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    documents = document_service.list_documents()
    
    return [
        DocumentInfo(
            id=doc["id"],
            filename=doc["filename"],
            upload_date=doc["upload_date"],
            chunk_count=doc["chunk_count"],
            file_size=doc["file_size"]
        )
        for doc in documents
    ]


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    doc = document_service.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentInfo(
        id=doc["id"],
        filename=doc["filename"],
        upload_date=doc["upload_date"],
        chunk_count=doc["chunk_count"],
        file_size=doc["file_size"]
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its vectors"""
    # Delete from vector store
    vector_store.delete_document(doc_id)
    
    # Delete file and metadata
    deleted = document_service.delete_document(doc_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": f"Document {doc_id} deleted successfully"}
