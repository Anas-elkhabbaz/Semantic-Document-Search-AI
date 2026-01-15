# Semantic Document Search

An AI-powered document search application that finds content by **meaning**, not just keywords.

## Features

- 📄 **Upload Documents** - Support for PDF and TXT files
- 🔍 **Semantic Search** - Find similar content using AI embeddings
- 📊 **Similarity Scores** - See how relevant each result is
- 💻 **100% Local** - No API keys needed, no quota limits

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Embeddings | sentence-transformers (local) |
| Vector DB | ChromaDB |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

### 3. Open in Browser

- **App**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

## How It Works

1. **Upload** a document (PDF or TXT)
2. The document is split into chunks
3. Each chunk is converted to an **embedding** (vector representation)
4. Embeddings are stored in **ChromaDB** (vector database)
5. When you **search**, your query is also converted to an embedding
6. **Semantic similarity** finds the most relevant chunks

## Project Structure

```
📁 AI Project 3/
├── 📁 backend/
│   └── 📁 app/
│       ├── main.py              # FastAPI application
│       ├── config.py            # Configuration
│       ├── 📁 routers/
│       │   ├── documents.py     # Upload/delete endpoints
│       │   └── search.py        # Search endpoint
│       └── 📁 services/
│           ├── embedding_service.py  # Local embeddings
│           ├── vector_store.py       # ChromaDB
│           ├── document_service.py   # File handling
│           └── chunking_service.py   # Text splitting
├── 📁 frontend/
│   └── app.py                   # Streamlit UI
├── requirements.txt
├── run.py                       # Start script
└── README.md
```

## Team Members

- [Add your names here]

## Supervisor

- [Add supervisor name]
