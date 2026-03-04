"""RAG service layer for orchestrating chunking, embedding, and storage."""

from .ingestion import IngestionService

__all__ = ["IngestionService"]
