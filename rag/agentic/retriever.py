"""Agentic RAG retriever using LangGraph for intelligent retrieval.

This implementation uses LangGraph to create a stateful workflow that enables:
- Multi-step reasoning and query decomposition
- Iterative query refinement
- Context-aware retrieval
- Result validation and filtering
- Conversation state management

The retriever wraps the existing DefaultRetriever and adds intelligent layers
using LangGraph's graph-based workflow capabilities.
"""

from typing import Optional, List, Dict, Any, Tuple
import time
from datetime import datetime

from typing import Optional, List, Dict, Any, Tuple
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from rag.core.schemas import SearchQuery, SearchResult
from rag.core.acl import Visibility

try:
    from rag.retrievers.default import DefaultRetriever
except ImportError:
    # Fallback for when running in parallel worktree
    from rag.core.interfaces import RetrieverInterface

    class DefaultRetriever:
        """Fallback DefaultRetriever for when the real one isn't available."""

        def __init__(self, embedder, store):
            self.embedder = embedder
            self.store = store

        def retrieve(self, query):
            # Mock implementation
            from rag.core.schemas import SearchResult, Chunk

            return [
                SearchResult(
                    chunk=Chunk(
                        id="mock",
                        document_id="mock",
                        content="Mock result",
                        index=0,
                        owner_id=query.acl_context.principal_id
                        if query.acl_context
                        else "system",
                        visibility="public",  # type: ignore[arg-type]
                    ),
                    score=0.8,
                )
            ]


from .schemas import (
    AgenticRetrievalResult,
    ConversationContext,
    RetrievalPlan,
    RetrievalStrategy,
    SubQuestion,
    QueryRefinement,
    ValidationResult,
    AgenticState,
)


class QueryPlanner:
    """Plans retrieval strategies for complex queries."""

    def __init__(self, max_sub_questions: int = 5):
        self.max_sub_questions = max_sub_questions

    def analyze_query_complexity(self, query_text: str) -> float:
        """Analyze query complexity to determine if multi-step is needed."""
        # Simple heuristic: count clauses, conjunctions, etc.
        text = query_text.lower()
        complexity_score = 0.0

        # Check for multiple questions
        question_words = ["what", "how", "why", "when", "where", "who", "which"]
        question_count = sum(1 for word in question_words if word in text)
        complexity_score += min(question_count * 0.2, 0.6)

        # Check for conjunctions
        conjunctions = ["and", "or", "but", "however", "although", "while"]
        conjunction_count = sum(1 for word in conjunctions if word in text)
        complexity_score += min(conjunction_count * 0.15, 0.4)

        # Check for comparative language
        comparative_words = ["compare", "difference", "vs", "versus", "better", "worse"]
        if any(word in text for word in comparative_words):
            complexity_score += 0.3

        # Check length
        word_count = len(text.split())
        complexity_score += min(word_count * 0.01, 0.3)

        return min(complexity_score, 1.0)

    def should_use_multi_step(
        self, query_text: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Determine if multi-step retrieval is appropriate."""
        complexity = self.analyze_query_complexity(query_text)

        # Multi-step if complexity is high or context suggests it
        if complexity > 0.7:
            return True

        # Check context for hints
        if context and context.get("force_multi_step", False):
            return True

        return False

    def decompose_query(self, query_text: str) -> List[str]:
        """Decompose complex query into sub-questions."""
        # This is a simple implementation - could be enhanced with LLM
        text = query_text.lower()
        sub_questions = []

        # Handle comparative questions
        if any(word in text for word in ["compare", "difference", "vs", "versus"]):
            parts = query_text.split(" and ")
            if len(parts) == 2:
                sub_questions.extend(
                    [
                        f"What are the key features of {parts[0].strip()}?",
                        f"What are the key features of {parts[1].strip()}?",
                        f"How do {parts[0].strip()} and {parts[1].strip()} compare?",
                    ]
                )
                return sub_questions

        # Handle multi-part questions with conjunctions
        if " and " in text:
            parts = [p.strip() for p in query_text.split(" and ") if p.strip()]
            if len(parts) <= self.max_sub_questions:
                return parts

        # Default: return original query
        return [query_text]

    def create_plan(
        self, query: SearchQuery, context: Optional[ConversationContext] = None
    ) -> RetrievalPlan:
        """Create a retrieval plan for the given query."""
        query_text = query.text

        # Determine if multi-step is needed
        requires_multi_step = self.should_use_multi_step(
            query_text, context.get_relevant_context() if context else None
        )

        # Create sub-questions if needed
        sub_questions_text = (
            self.decompose_query(query_text) if requires_multi_step else []
        )

        sub_questions = []
        for i, sub_q in enumerate(sub_questions_text):
            sub_questions.append(
                SubQuestion(
                    text=sub_q,
                    purpose=f"Sub-question {i + 1} of {len(sub_questions_text)}",
                    dependency_of=[] if i == 0 else [sub_questions_text[i - 1]],
                )
            )

        # Determine strategy
        if requires_multi_step and len(sub_questions) > 1:
            strategy = RetrievalStrategy.MULTI_STEP
        else:
            strategy = RetrievalStrategy.SIMPLE

        return RetrievalPlan(
            original_query=query_text,
            strategy=strategy,
            sub_questions=sub_questions,
            requires_multi_step=requires_multi_step,
            context_used=context.get_relevant_context() if context else {},
            execution_steps=[
                "analyze_query",
                "create_plan",
                "execute_retrieval",
                "validate_results",
            ],
        )


class ResultValidator:
    """Validates and filters retrieval results."""

    def __init__(self, min_score_threshold: float = 0.3, max_results: int = 10):
        self.min_score_threshold = min_score_threshold
        self.max_results = max_results

    def validate_result_quality(
        self, result: SearchResult
    ) -> Tuple[bool, Optional[str]]:
        """Validate a single search result."""
        # Check score threshold
        if result.score < self.min_score_threshold:
            return False, "score_too_low"

        # Check content quality (simple heuristic)
        content = result.chunk.content.strip()
        if len(content.split()) < 3:  # Too short
            return False, "content_too_short"

        if len(content) > 5000:  # Too long
            return False, "content_too_long"

        # Check for meaningful content (not just numbers, symbols, etc.)
        alpha_chars = sum(1 for c in content if c.isalpha())
        if alpha_chars < len(content) * 0.3:  # Less than 30% alphabetic
            return False, "low_quality_content"

        return True, None

    def validate_results(
        self, results: List[SearchResult]
    ) -> Tuple[List[SearchResult], ValidationResult]:
        """Validate a list of search results."""
        original_count = len(results)
        validated_results = []
        validation_reasons: Dict[str, int] = {}

        for result in results:
            is_valid, reason = self.validate_result_quality(result)
            if is_valid:
                validated_results.append(result)
            else:
                if reason:
                    validation_reasons[reason] = validation_reasons.get(reason, 0) + 1

        # Apply result limits
        if len(validated_results) > self.max_results:
            validated_results = validated_results[: self.max_results]
            validation_reasons["result_limit"] = len(results) - self.max_results

        # Calculate quality score (simple heuristic)
        if original_count > 0:
            quality_score = len(validated_results) / original_count
            # Penalize if many results were filtered for quality
            if validation_reasons.get("low_quality_content", 0) > original_count * 0.3:
                quality_score *= 0.7
        else:
            quality_score = 0.0

        return validated_results, ValidationResult(
            original_count=original_count,
            validated_count=len(validated_results),
            filtered_out=original_count - len(validated_results),
            validation_reasons=validation_reasons,
            quality_score=min(max(quality_score, 0.0), 1.0),
        )


class IterativeRefiner:
    """Refines queries based on initial results and context."""

    def __init__(self, max_refinements: int = 2):
        self.max_refinements = max_refinements

    def analyze_results_quality(
        self, results: List[SearchResult], query: SearchQuery
    ) -> float:
        """Analyze if results need refinement."""
        if not results:
            return 0.0  # No results - definitely needs refinement

        # Check average score
        avg_score = sum(r.score for r in results) / len(results)

        # Check diversity of sources
        unique_docs = len(set(r.chunk.document_id for r in results))
        doc_diversity = unique_docs / len(results) if results else 0.0

        # Simple quality score (0-1, lower = needs more refinement)
        quality_score = (avg_score * 0.6) + (doc_diversity * 0.4)

        return quality_score

    def should_refine(
        self, results: List[SearchResult], query: SearchQuery, refinement_count: int
    ) -> bool:
        """Determine if query should be refined."""
        if refinement_count >= self.max_refinements:
            return False

        quality_score = self.analyze_results_quality(results, query)

        # Refine if quality is low
        if quality_score < 0.5:
            return True

        # Also refine if we have very few results
        if len(results) < 3:
            return True

        return False

    def refine_query(self, original_query: str, results: List[SearchResult]) -> str:
        """Generate a refined query based on initial results."""
        # Simple refinement strategy: expand query with key terms from results
        if not results:
            # If no results, try broadening the query
            return f"{original_query} (expand search)"

        # Extract key terms from top results
        key_terms: set[str] = set()
        for result in results[:3]:  # Look at top 3 results
            content = result.chunk.content.lower()
            # Simple term extraction (could use NLP for better results)
            words = content.split()
            # Filter out very common words
            stop_words = {
                "the",
                "and",
                "or",
                "a",
                "an",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
            }
            key_terms.update(
                word for word in words if word not in stop_words and len(word) > 3
            )

        if key_terms:
            # Add some key terms to the query
            term_list = ", ".join(list(key_terms)[:5])  # Top 5 terms
            return f"{original_query} (related to: {term_list})"
        else:
            # Fallback: try synonyms or broader search
            return f"{original_query} (broader search)"


class AgenticRetriever:
    """Agentic RAG retriever using LangGraph workflow.

    This class wraps a RetrieverInterface implementation and adds agentic capabilities.
    It does not directly implement RetrieverInterface to avoid type conflicts with
    the enhanced return type (AgenticRetrievalResult vs List[SearchResult]).
    """

    def __init__(self, base_retriever):
        """Initialize the agentic retriever.

        Args:
            base_retriever: The underlying DefaultRetriever for basic operations
        """
        self.base_retriever = base_retriever
        self.query_planner = QueryPlanner()
        self.result_validator = ResultValidator()
        self.iterative_refiner = IterativeRefiner()
        self.context_manager = {}  # conversation_id -> ConversationContext

        # Build LangGraph workflow
        self.workflow = self._build_langgraph_workflow()

    def _build_langgraph_workflow(self):
        """Build the LangGraph workflow for agentic retrieval."""
        workflow = StateGraph(AgenticState)

        # Add nodes for each step
        workflow.add_node("plan_retrieval", self._plan_retrieval_node)
        workflow.add_node("execute_retrieval", self._execute_retrieval_node)
        workflow.add_node("validate_results", self._validate_results_node)
        workflow.add_node("refine_query", self._refine_query_node)

        # Define edges
        workflow.add_edge("plan_retrieval", "execute_retrieval")
        workflow.add_edge("execute_retrieval", "validate_results")

        # Conditional edge for refinement
        workflow.add_conditional_edges(
            "validate_results",
            self._should_refine_router,
            {"refine": "refine_query", "complete": "complete_retrieval"},
        )

        workflow.add_edge("refine_query", "execute_retrieval")

        # Add completion node
        workflow.add_node("complete_retrieval", self._complete_retrieval_node)
        workflow.add_edge("complete_retrieval", END)

        # Set entry point
        workflow.set_entry_point("plan_retrieval")

        return workflow

    def _plan_retrieval_node(
        self, state: AgenticState, config: RunnableConfig
    ) -> AgenticState:
        """Plan the retrieval strategy."""
        state.add_execution_step("plan_retrieval")

        # Create or get conversation context
        conversation_context = state.conversation_context
        if conversation_context is None and state.query.acl_context:
            # Create new context if none exists
            conversation_context = ConversationContext(
                conversation_id=f"conv_{datetime.utcnow().timestamp()}",
                user_preferences={"preferred_strategy": "balanced", "result_limit": 10},
            )
            state.conversation_context = conversation_context

        # Create retrieval plan
        plan = self.query_planner.create_plan(state.query, conversation_context)
        state.current_plan = plan

        return state

    def _execute_retrieval_node(
        self, state: AgenticState, config: RunnableConfig
    ) -> AgenticState:
        """Execute the retrieval based on current plan."""
        state.add_execution_step("execute_retrieval")

        plan = state.current_plan
        if not plan:
            raise ValueError("No retrieval plan available")

        if plan.requires_multi_step:
            # Execute multi-step retrieval
            results = self._execute_multi_step_retrieval(state)
        else:
            # Execute simple retrieval
            results = self.base_retriever.retrieve(state.query)

        state.add_intermediate_results(results)

        return state

    def _execute_multi_step_retrieval(self, state: AgenticState) -> List[SearchResult]:
        """Execute multi-step retrieval for complex queries."""
        plan = state.current_plan
        if not plan:
            raise ValueError("No retrieval plan available")

        all_results = []

        # Execute each sub-question
        for sub_question in plan.sub_questions:
            # Create modified query for sub-question
            sub_query = SearchQuery(
                text=sub_question.text,
                top_k=state.query.top_k // len(plan.sub_questions),  # Divide top_k
                min_score=state.query.min_score,
                filters=state.query.filters,
                acl_context=state.query.acl_context,
            )

            # Execute sub-question
            sub_results = self.base_retriever.retrieve(sub_query)
            sub_question.results = sub_results
            all_results.extend(sub_results)

        return all_results

    def _validate_results_node(
        self, state: AgenticState, config: RunnableConfig
    ) -> AgenticState:
        """Validate and filter results."""
        state.add_execution_step("validate_results")

        all_results = state.intermediate_results
        if not all_results:
            # No results to validate
            validation_result = ValidationResult(
                original_count=0,
                validated_count=0,
                filtered_out=0,
                validation_reasons={},
                quality_score=0.0,
            )
            state.add_validation_result(validation_result)
            return state

        # Validate results
        validated_results, validation_result = self.result_validator.validate_results(
            all_results
        )
        state.add_validation_result(validation_result)

        # Replace intermediate results with validated ones
        state.intermediate_results = validated_results

        return state

    def _should_refine_router(self, state: AgenticState) -> str:
        """Determine if query should be refined."""
        refinement_count = len(state.refinements)
        results = state.intermediate_results

        if self.iterative_refiner.should_refine(results, state.query, refinement_count):
            return "refine"
        else:
            return "complete"

    def _refine_query_node(
        self, state: AgenticState, config: RunnableConfig
    ) -> AgenticState:
        """Refine the query based on current results."""
        state.add_execution_step("refine_query")

        original_query = state.query.text
        results = state.intermediate_results

        # Generate refined query
        refined_query_text = self.iterative_refiner.refine_query(
            original_query, results
        )

        # Create query refinement record
        refinement = QueryRefinement(
            original_query=original_query,
            refined_query=refined_query_text,
            refinement_reason="low_result_quality",
            improvement_metrics={
                "original_results": len(results),
                "expected_improvement": 0.3,  # Estimate
            },
        )
        state.add_refinement(refinement)

        # Update query with refined text
        state.query = SearchQuery(
            text=refined_query_text,
            top_k=state.query.top_k,
            min_score=state.query.min_score,
            filters=state.query.filters,
            acl_context=state.query.acl_context,
        )

        # Clear previous results for new retrieval
        state.intermediate_results = []

        return state

    def _complete_retrieval_node(
        self, state: AgenticState, config: RunnableConfig
    ) -> AgenticRetrievalResult:
        """Complete the retrieval process and return final result."""
        state.add_execution_step("complete_retrieval")

        # Get final results and validation
        final_results = state.intermediate_results
        validation_result = (
            state.validation_results[-1]
            if state.validation_results
            else ValidationResult(
                original_count=0,
                validated_count=0,
                filtered_out=0,
                validation_reasons={},
                quality_score=0.0,
            )
        )

        # Create conversation context if it doesn't exist
        conversation_context = state.conversation_context
        if conversation_context is None:
            conversation_context = ConversationContext(
                conversation_id="ephemeral", user_preferences={}
            )

        # Update conversation context
        conversation_context.add_query(state.query)
        conversation_context.add_results(final_results)

        # Ensure we have a valid plan
        final_plan = state.current_plan
        if final_plan is None:
            # Create a minimal plan if none exists
            final_plan = RetrievalPlan(
                original_query=state.query.text,
                strategy=RetrievalStrategy.SIMPLE,
                sub_questions=[],
                requires_multi_step=False,
                context_used={},
                execution_steps=["direct_retrieval"],
            )

        # Update conversation context
        conversation_context.add_query(state.query)
        conversation_context.add_results(final_results)

        return AgenticRetrievalResult(
            query=state.query,
            results=final_results,
            plan=final_plan,
            context_used=conversation_context,
            refinements=state.refinements,
            validation=validation_result,
            execution_time_ms=0,  # Will be set by retrieve method
        )

        # Update conversation context
        conversation_context.add_query(state.query)
        conversation_context.add_results(final_results)

        return AgenticRetrievalResult(
            query=state.query,
            results=final_results,
            plan=state.current_plan,
            context_used=conversation_context,
            refinements=state.refinements,
            validation=validation_result,
            execution_time_ms=0,  # Will be set by retrieve method
        )

    def retrieve(
        self, query: SearchQuery, conversation_id: Optional[str] = None
    ) -> AgenticRetrievalResult:
        """Execute agentic retrieval with LangGraph workflow.

        Args:
            query: SearchQuery with text and ACL context
            conversation_id: Optional conversation ID for context management

        Returns:
            AgenticRetrievalResult with comprehensive retrieval information
        """
        # Get or create conversation context
        conversation_context = None
        if conversation_id:
            conversation_context = self.context_manager.get(conversation_id)
            if conversation_context is None:
                conversation_context = ConversationContext(
                    conversation_id=conversation_id
                )
                self.context_manager[conversation_id] = conversation_context

        # Create initial state
        initial_state = AgenticState(
            query=query, conversation_context=conversation_context
        )

        # Execute workflow
        start_time = time.time()

        # Use LangGraph to execute the workflow
        workflow_result = self.workflow.compile().invoke(initial_state)

        execution_time_ms = (time.time() - start_time) * 1000

        # The workflow returns the final state as a dictionary
        # Our AgenticRetrievalResult should be in the state
        if isinstance(workflow_result, dict):
            # The state contains all our data, we need to reconstruct the result
            final_state = workflow_result

            # Extract data from state
            final_results = final_state.get("intermediate_results", [])
            validation_result = (
                final_state.get(
                    "validation_results",
                    [
                        ValidationResult(
                            original_count=0,
                            validated_count=0,
                            filtered_out=0,
                            validation_reasons={},
                            quality_score=0.0,
                        )
                    ],
                )[-1]
                if final_state.get("validation_results")
                else ValidationResult(
                    original_count=0,
                    validated_count=0,
                    filtered_out=0,
                    validation_reasons={},
                    quality_score=0.0,
                )
            )
            refinements = final_state.get("refinements", [])
            current_plan = final_state.get("current_plan")
            conversation_context = final_state.get("conversation_context")

            # Create the result object
            final_result = AgenticRetrievalResult(
                query=query,
                results=final_results,
                plan=current_plan,
                context_used=conversation_context,
                refinements=refinements,
                validation=validation_result,
                execution_time_ms=execution_time_ms,
            )
        else:
            # Direct result (shouldn't happen but handle it)
            final_result = workflow_result
            final_result.execution_time_ms = execution_time_ms

        # Update conversation context if it exists
        if conversation_id and conversation_context:
            conversation_context.add_query(query)
            conversation_context.add_results(final_result.results)

        return final_result

    def get_conversation_context(
        self, conversation_id: str
    ) -> Optional[ConversationContext]:
        """Get conversation context by ID."""
        return self.context_manager.get(conversation_id)

    def clear_conversation_context(self, conversation_id: str) -> None:
        """Clear conversation context."""
        if conversation_id in self.context_manager:
            del self.context_manager[conversation_id]

    def index_document(self, document) -> int:
        """Delegate to base retriever."""
        return self.base_retriever.index_document(document)

    def remove_document(self, document_id: str) -> None:
        """Delegate to base retriever."""
        return self.base_retriever.remove_document(document_id)
