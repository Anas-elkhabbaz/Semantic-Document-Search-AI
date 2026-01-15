"""
Configuration management for Smart Study Assistant
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Paths
    upload_dir: Path = DATA_DIR / "uploads"
    chroma_dir: Path = DATA_DIR / "chroma"
    history_dir: Path = DATA_DIR / "history"
    
    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG settings
    top_k_results: int = 5
    
    # Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    chat_model: str = "gemini-1.5-flash"
    
    class Config:
        env_file = ".env"
        extra = "allow"


# Create singleton settings instance
settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
settings.history_dir.mkdir(parents=True, exist_ok=True)
