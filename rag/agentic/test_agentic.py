"""Test the agentic RAG retriever."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_agentic_retriever():
    """Test the agentic retriever with mock components."""

    # Import after path is set
    from agentic.retriever import (
        AgenticRetriever,
        QueryPlanner,
        ResultValidator,
        IterativeRefiner,
    )
    from rag.agentic.schemas import (
        AgenticRetrievalResult,
        ConversationContext,
        RetrievalPlan,
        RetrievalStrategy,
    )
    from rag.core.schemas import SearchQuery
    from rag.core.acl import QueryACLContext

    print("🧪 Testing Agentic RAG Components...")

    # Test QueryPlanner
    print("\n1. Testing QueryPlanner...")
    planner = QueryPlanner()

    # Simple query
    simple_complexity = planner.analyze_query_complexity("What is Django?")
    print(f"   Simple query complexity: {simple_complexity:.3f}")

    # Complex query
    complex_complexity = planner.analyze_query_complexity(
        "What are the key differences between Django 4.2 and 5.0 and how do they impact performance and security?"
    )
    print(f"   Complex query complexity: {complex_complexity:.3f}")

    # Test decomposition
    complex_query = (
        "Compare Django and Flask in terms of performance, security, and ease of use"
    )
    sub_questions = planner.decompose_query(complex_query)
    print(f"   Decomposed into {len(sub_questions)} sub-questions:")
    for i, sub_q in enumerate(sub_questions, 1):
        print(f"     {i}. {sub_q[:50]}...")

    # Test ResultValidator
    print("\n2. Testing ResultValidator...")
    validator = ResultValidator()

    # Mock search results
    from rag.core.schemas import SearchResult, Chunk

    mock_results = [
        SearchResult(
            chunk=Chunk(
                id="1",
                document_id="doc1",
                content="Django is a high-level Python web framework that enables rapid development of secure and maintainable websites.",
                index=0,
                owner_id="user1",
                visibility="public",  # type: ignore[arg-type],  # type: ignore[arg-type]
            ),
            score=0.85,
        ),
        SearchResult(
            chunk=Chunk(
                id="2",
                document_id="doc2",
                content="Flask is a micro web framework for Python.",
                index=0,
                owner_id="user1",
                visibility="public",  # type: ignore[arg-type],
            ),
            score=0.78,
        ),
        SearchResult(
            chunk=Chunk(
                id="3",
                document_id="doc3",
                content="Short.",  # This should be filtered out
                index=0,
                owner_id="user1",
                visibility="public",  # type: ignore[arg-type],
            ),
            score=0.2,  # Low score
        ),
    ]

    validated_results, validation_report = validator.validate_results(mock_results)
    print(f"   Original results: {len(mock_results)}")
    print(f"   Validated results: {len(validated_results)}")
    print(f"   Filtered out: {validation_report.filtered_out}")
    print(f"   Quality score: {validation_report.quality_score:.3f}")
    print(f"   Validation reasons: {validation_report.validation_reasons}")

    # Test IterativeRefiner
    print("\n3. Testing IterativeRefiner...")
    refiner = IterativeRefiner()

    # Create a mock query for testing
    from rag.core.acl import QueryACLContext

    mock_query = SearchQuery(
        text="test query",
        acl_context=QueryACLContext(principal_id="test", bypass_acl=False),
    )

    quality_score = refiner.analyze_results_quality(validated_results, mock_query)
    print(f"   Results quality score: {quality_score:.3f}")

    should_refine = refiner.should_refine(validated_results, mock_query, 0)
    print(f"   Should refine query: {should_refine}")

    if validated_results:
        refined_query = refiner.refine_query("What is Django?", validated_results)
        print(f"   Original: What is Django?")
        print(f"   Refined:  {refined_query}")

    # Test full AgenticRetriever (with mock base retriever)
    print("\n4. Testing AgenticRetriever...")

    # Create mock base retriever
    class MockBaseRetriever:
        def retrieve(self, query):
            return mock_results

    mock_base_retriever = MockBaseRetriever()
    agentic_retriever = AgenticRetriever(mock_base_retriever)

    # Create test query
    acl_context = QueryACLContext(
        principal_id="user123",
        member_of_groups=["developers"],
        tenant_id=None,
        bypass_acl=False,
    )

    test_query = SearchQuery(
        text="What are the advantages of Django over Flask?",
        top_k=5,
        acl_context=acl_context,
    )

    # Execute retrieval
    result = agentic_retriever.retrieve(test_query, conversation_id="test_session")

    print(f"   Retrieval completed in {result.execution_time_ms:.2f}ms")
    print(f"   Strategy: {result.plan.strategy.value}")
    print(f"   Multi-step: {'Yes' if result.has_multi_step else 'No'}")
    print(f"   Results returned: {len(result.results)}")
    print(f"   Result quality: {result.result_quality}")
    print(f"   Validation quality: {result.validation.quality_score:.3f}")

    print("\n🎉 All tests completed successfully!")

    return True


if __name__ == "__main__":
    try:
        test_agentic_retriever()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
