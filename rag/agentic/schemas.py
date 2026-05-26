"""Schemas for agentic RAG system using LangGraph."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from rag.core.schemas import SearchQuery, SearchResult, Document


class RetrievalStrategy(str, Enum):
    """Strategy for retrieval execution."""

    SIMPLE = "simple"  # Single direct query
    MULTI_STEP = "multi_step"  # Break into sub-questions
    ITERATIVE = "iterative"  # Refine based on initial results
    HYBRID = "hybrid"  # Combine multiple strategies


class SubQuestion(BaseModel):
    """A sub-question generated during query planning."""

    text: str = Field(..., description="Sub-question text")
    purpose: str = Field(..., description="Purpose of this sub-question")
    dependency_of: Optional[List[str]] = Field(
        default=None, description="IDs of sub-questions this depends on"
    )
    results: List[SearchResult] = Field(
        default_factory=list, description="Results for this sub-question"
    )


class RetrievalPlan(BaseModel):
    """Plan for executing a retrieval operation."""

    original_query: str = Field(..., description="Original user query")
    strategy: RetrievalStrategy = Field(..., description="Chosen retrieval strategy")
    sub_questions: List[SubQuestion] = Field(
        default_factory=list, description="Sub-questions for multi-step retrieval"
    )
    requires_multi_step: bool = Field(
        ..., description="Whether multi-step processing is needed"
    )
    context_used: Dict[str, Any] = Field(
        default_factory=dict, description="Context information used in planning"
    )
    execution_steps: List[str] = Field(
        default_factory=list, description="Planned execution steps"
    )


class ConversationContext(BaseModel):
    """Context maintained across a conversation session."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When conversation started"
    )
    query_history: List[SearchQuery] = Field(
        default_factory=list, description="History of queries in this conversation"
    )
    result_history: List[SearchResult] = Field(
        default_factory=list, description="History of results returned"
    )
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User-specific preferences and settings"
    )
    session_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional session metadata"
    )

    def add_query(self, query: SearchQuery) -> None:
        """Add a query to the conversation history."""
        self.query_history.append(query)

    def add_results(self, results: List[SearchResult]) -> None:
        """Add results to the conversation history."""
        self.result_history.extend(results)

    def get_recent_queries(self, limit: int = 5) -> List[SearchQuery]:
        """Get recent queries from history."""
        return self.query_history[-limit:]

    def get_relevant_context(self) -> Dict[str, Any]:
        """Extract relevant context for current retrieval."""
        return {
            "recent_queries": [q.text for q in self.get_recent_queries(3)],
            "user_preferences": self.user_preferences,
            "session_metadata": self.session_metadata,
        }


class QueryRefinement(BaseModel):
    """Information about query refinement."""

    original_query: str = Field(..., description="Original query text")
    refined_query: str = Field(..., description="Refined query text")
    refinement_reason: str = Field(..., description="Reason for refinement")
    improvement_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Metrics showing improvement"
    )


class ValidationResult(BaseModel):
    """Result of validation process."""

    original_count: int = Field(..., description="Original number of results")
    validated_count: int = Field(..., description="Number of results after validation")
    filtered_out: int = Field(..., description="Number of results filtered out")
    validation_reasons: Dict[str, int] = Field(
        default_factory=dict, description="Reasons for filtering (reason: count)"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall quality score of results"
    )


class AgenticRetrievalResult(BaseModel):
    """Complete result from agentic retrieval."""

    query: SearchQuery = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Final validated results")
    plan: RetrievalPlan = Field(..., description="Execution plan used")
    context_used: ConversationContext = Field(..., description="Conversation context")
    refinements: List[QueryRefinement] = Field(
        default_factory=list, description="Query refinements made during process"
    )
    validation: ValidationResult = Field(..., description="Validation information")
    execution_time_ms: float = Field(
        ..., ge=0.0, description="Total execution time in milliseconds"
    )

    @property
    def has_multi_step(self) -> bool:
        """Whether multi-step processing was used."""
        return self.plan.requires_multi_step

    @property
    def refinement_count(self) -> int:
        """Number of query refinements made."""
        return len(self.refinements)

    @property
    def result_quality(self) -> str:
        """Get quality rating based on validation score."""
        score = self.validation.quality_score
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "poor"


class AgenticState(BaseModel):
    """State object for LangGraph workflow."""

    query: SearchQuery = Field(..., description="Current search query")
    conversation_context: Optional[ConversationContext] = Field(
        default=None, description="Conversation context if available"
    )
    current_plan: Optional[RetrievalPlan] = Field(
        default=None, description="Current retrieval plan"
    )
    intermediate_results: List[SearchResult] = Field(
        default_factory=list, description="Intermediate results from sub-questions"
    )
    refinements: List[QueryRefinement] = Field(
        default_factory=list, description="Query refinements made so far"
    )
    validation_results: List[ValidationResult] = Field(
        default_factory=list, description="Validation results from each step"
    )
    execution_steps: List[str] = Field(
        default_factory=list, description="Steps executed so far"
    )

    def add_execution_step(self, step: str) -> None:
        """Add an execution step to the history."""
        self.execution_steps.append(step)

    def add_intermediate_results(self, results: List[SearchResult]) -> None:
        """Add intermediate results."""
        self.intermediate_results.extend(results)

    def add_refinement(self, refinement: QueryRefinement) -> None:
        """Add a query refinement."""
        self.refinements.append(refinement)

    def add_validation_result(self, validation: ValidationResult) -> None:
        """Add a validation result."""
        self.validation_results.append(validation)
