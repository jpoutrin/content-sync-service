"""Django management command for agentic RAG search.

Usage:
    python manage.py agentic_search "your query" [--user USER_ID] [--top_k NUM] [--debug]

Examples:
    python manage.py agentic_search "What is Django 5.0?"
    python manage.py agentic_search "Compare Django and Flask" --user admin --top_k 3
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import time
import sys


def setup_agentic_retriever():
    """Setup the agentic retriever with mock components for management command use."""
    from rag.agentic.retriever import AgenticRetriever
    from rag.core.schemas import SearchQuery
    from rag.core.acl import QueryACLContext

    # Create mock base retriever for management command
    class MockBaseRetriever:
        def __init__(self):
            # Mock knowledge base
            self.knowledge_base = {
                "django": {
                    "features": "Django 5.0 introduces async views, improved performance, and better security features.",
                    "async": "Async views in Django allow handling requests asynchronously using async/await syntax.",
                    "performance": "Django 5.0 offers 20-30% better performance through optimized ORM and template rendering.",
                    "comparison": "Django is a full-featured framework while Flask is a microframework. Django includes ORM, admin interface, and authentication out of the box.",
                },
                "flask": {
                    "features": "Flask is a lightweight microframework for Python web development.",
                    "comparison": "Flask provides more flexibility but requires manual setup for features like ORM and authentication.",
                },
                "python": {
                    "web": "Python offers several web frameworks including Django, Flask, and FastAPI."
                },
                "agentic": {
                    "rag": "Agentic RAG adds multi-step reasoning, iterative refinement, and context-aware retrieval to traditional RAG systems.",
                    "features": "Agentic RAG systems can decompose complex queries, refine searches based on results, and maintain conversation context.",
                },
            }

        def retrieve(self, query):
            """Mock retrieval that searches our knowledge base."""
            from rag.core.schemas import SearchResult, Chunk

            query_text = query.text.lower()
            results = []

            # Search through our knowledge base
            for category, items in self.knowledge_base.items():
                for topic, content in items.items():
                    # Simple keyword matching
                    if any(keyword in query_text for keyword in [category, topic]):
                        chunk = Chunk(
                            id=f"{category}_{topic}",
                            document_id=f"doc_{category}",
                            content=content,
                            index=0,
                            owner_id=query.acl_context.principal_id
                            if query.acl_context
                            else "system",
                            visibility="public",  # type: ignore[arg-type]
                        )

                        # Calculate a simple relevance score
                        keyword_count = sum(
                            1 for keyword in [category, topic] if keyword in query_text
                        )
                        score = min(0.5 + keyword_count * 0.15, 1.0)

                        results.append(SearchResult(chunk=chunk, score=score))

            # Sort by score (highest first)
            return sorted(results, key=lambda x: x.score, reverse=True)[: query.top_k]

    # Create the retrievers
    mock_base_retriever = MockBaseRetriever()
    agentic_retriever = AgenticRetriever(mock_base_retriever)

    return agentic_retriever, SearchQuery, QueryACLContext


def format_results(result, debug: bool = False) -> str:
    """Format the agentic retrieval results for management command output."""
    output = []

    # Header
    output.append("=" * 60)
    output.append("🎯 AGENTIC RAG RESULTS")
    output.append("=" * 60)

    # Query info
    output.append(f"📋 Query: {result.query.text}")
    output.append(f"🕒 Execution time: {result.execution_time_ms:.2f}ms")
    output.append(f"📊 Strategy: {result.plan.strategy.value.upper()}")
    output.append(f"🔄 Multi-step: {'Yes' if result.has_multi_step else 'No'}")
    output.append(f"✨ Quality: {result.result_quality.upper()}")
    output.append("")

    # Results
    output.append("📄 RETRIEVAL RESULTS:")
    output.append("-" * 60)

    if result.results:
        for i, search_result in enumerate(result.results, 1):
            chunk = search_result.chunk
            output.append(f"{i}. [{search_result.score:.3f}]")
            output.append(f"   {chunk.content}")
            output.append(f"   (Source: {chunk.document_id}, Chunk: {chunk.id})")
            output.append("")
    else:
        output.append("   No results found.")
        output.append("")

    # Validation info
    if debug:
        output.append("🔍 VALIDATION DETAILS:")
        output.append("-" * 60)
        output.append(f"   Original results: {result.validation.original_count}")
        output.append(f"   Validated results: {result.validation.validated_count}")
        output.append(f"   Filtered out: {result.validation.filtered_out}")
        output.append(f"   Quality score: {result.validation.quality_score:.3f}")
        if result.validation.validation_reasons:
            output.append("   Filter reasons:")
            for reason, count in result.validation.validation_reasons.items():
                output.append(f"     • {reason}: {count}")
        output.append("")

    # Refinements
    if result.refinements and debug:
        output.append("🔄 QUERY REFINEMENTS:")
        output.append("-" * 60)
        for i, refinement in enumerate(result.refinements, 1):
            output.append(f"   {i}. {refinement.refinement_reason}")
            output.append(f"      Original: {refinement.original_query[:50]}...")
            output.append(f"      Refined:  {refinement.refined_query[:50]}...")
        output.append("")

    # Footer
    output.append("=" * 60)
    output.append(f"💬 Conversation ID: {result.context_used.conversation_id}")
    output.append(
        f"📈 Results returned: {len(result.results)} of {result.validation.original_count} total"
    )
    output.append("=" * 60)

    return "\n".join(output)


class Command(BaseCommand):
    help = "Execute agentic RAG search queries"

    def add_arguments(self, parser):
        parser.add_argument("query", type=str, help="The search query to execute")

        parser.add_argument(
            "--user",
            type=str,
            default="system",
            help="User ID for ACL context (default: system)",
        )

        parser.add_argument(
            "--top-k",
            type=int,
            default=5,
            help="Number of results to return (default: 5)",
        )

        parser.add_argument(
            "--debug", action="store_true", help="Show detailed debugging information"
        )

        parser.add_argument(
            "--conversation-id",
            type=str,
            default=None,
            help="Conversation ID for context continuity",
        )

    def handle(self, *args, **options):
        query_text = options["query"]
        user_id = options["user"]
        top_k = options["top_k"]
        debug = options["debug"]
        conversation_id = options["conversation_id"]

        if not query_text.strip():
            self.stderr.write(self.style.ERROR("Error: Query cannot be empty"))
            sys.exit(1)

        try:
            # Import agentic components
            from rag.agentic.retriever import AgenticRetriever
            from rag.core.schemas import SearchQuery
            from rag.core.acl import QueryACLContext

            # Setup retriever
            agentic_retriever, SearchQuery, QueryACLContext = setup_agentic_retriever()

            # Create ACL context
            acl_context = QueryACLContext(
                principal_id=user_id,
                member_of_groups=["admin"],  # Admin group for management commands
                tenant_id=None,
                bypass_acl=False,
            )

            # Create search query
            search_query = SearchQuery(
                text=query_text, top_k=top_k, acl_context=acl_context
            )

            # Execute retrieval
            self.stdout.write(f'🚀 Processing query: "{query_text}"...')
            start_time = time.time()

            result = agentic_retriever.retrieve(
                search_query, conversation_id=conversation_id
            )

            execution_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(f"✅ Completed in {execution_time:.3f} seconds")
            )
            self.stdout.write("")

            # Format and display results
            formatted_output = format_results(result, debug=debug)
            self.stdout.write(formatted_output)

        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"Import error: {e}"))
            self.stderr.write(
                self.style.WARNING("Agentic RAG components may not be installed")
            )
            sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
            if debug:
                import traceback

                traceback.print_exc()
            sys.exit(1)
