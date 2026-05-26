"""Agentic RAG module using LangGraph for intelligent retrieval.

This module implements an agentic retrieval system that adds multi-step reasoning,
iterative refinement, context-aware retrieval, query planning, and result validation
to the base RAG system using LangGraph's stateful workflow capabilities.

Key components:
    - AgenticRetriever: Main entry point using LangGraph
    - QueryPlanner: Breaks down complex queries into sub-questions
    - ContextManager: Maintains conversation state
    - ResultValidator: Filters and validates results
    - IterativeRefiner: Improves queries based on feedback

Usage:
    from rag.agentic import AgenticRetriever
    from rag.retrievers.default import DefaultRetriever
    from rag.core.schemas import SearchQuery
    from yt_sync.rag_bridge import build_acl_context

    # Setup
    base_retriever = DefaultRetriever(embedder, vector_store)
    agentic_retriever = AgenticRetriever(base_retriever)

    # Create query with ACL context
    acl_context = build_acl_context(request.user)
    query = SearchQuery(text="complex question", acl_context=acl_context)

    # Execute agentic retrieval
    result = agentic_retriever.retrieve(query, conversation_id="session-123")
"""

from .retriever import AgenticRetriever
from .schemas import AgenticRetrievalResult, ConversationContext, RetrievalPlan

__all__ = [
    "AgenticRetriever",
    "AgenticRetrievalResult",
    "ConversationContext",
    "RetrievalPlan",
]
