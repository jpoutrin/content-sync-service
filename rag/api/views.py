"""DRF views for RAG search API."""

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rag.core.acl import QueryACLContext
from rag.core.schemas import SearchQuery
from rag.embedders.litellm import LiteLLMEmbedder
from rag.retrievers.default import DefaultRetriever
from rag.stores.pgvector import PgVectorStore

from .serializers import SearchQuerySerializer, SearchResponseSerializer


class SearchView(APIView):
    """
    Semantic search endpoint for transcript content.

    GET /api/rag/search

    Performs semantic similarity search across indexed video transcripts
    with ACL filtering based on the authenticated user's permissions.

    Query Parameters:
        q (required): Search query text (1-500 chars)
        top_k (optional): Maximum results to return (1-100, default 5)
        min_score (optional): Minimum similarity score (0.0-1.0, default 0.0)

    Returns:
        200: Search results with query, results array, and total count
        400: Invalid query parameters
        401: Authentication required
        500: Internal server error

    Example:
        GET /api/rag/search?q=How+to+configure+Django&top_k=10&min_score=0.7

    Response:
        {
            "query": "How to configure Django",
            "results": [
                {
                    "chunk_id": "video:42:chunk:5",
                    "content": "To configure Django settings...",
                    "score": 0.89,
                    "video_id": "42",
                    "video_title": "Django Tutorial",
                    "video_url": "https://youtube.com/watch?v=abc123",
                    "start_time": 125.5,
                    "end_time": 185.2,
                    "timestamp_url": "https://youtube.com/watch?v=abc123&t=125"
                }
            ],
            "total": 1
        }
    """

    def get(self, request):
        """
        Handle GET request for semantic search.

        Validates query parameters, builds ACL context from authenticated user,
        performs semantic search using the retriever, and formats results.

        Args:
            request: DRF request object with query parameters and user

        Returns:
            Response: JSON response with search results or error
        """
        # Validate query parameters
        query_serializer = SearchQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                query_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = query_serializer.validated_data

        # Build ACL context from authenticated user
        acl_context = self._build_acl_context(request.user)

        # Create SearchQuery object
        search_query = SearchQuery(
            text=validated_data['q'],
            top_k=validated_data['top_k'],
            min_score=validated_data.get('min_score'),
            acl_context=acl_context
        )

        try:
            # Initialize retriever components
            # Note: In production, these should be dependency-injected or cached
            embedder = LiteLLMEmbedder(
                provider=settings.RAG_EMBEDDING_PROVIDER,
                model=settings.RAG_EMBEDDING_MODEL
            )

            # Build PostgreSQL connection string from Django database settings
            db_settings = settings.DATABASES['default']
            connection_string = f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"

            store = PgVectorStore(connection_string=connection_string)
            retriever = DefaultRetriever(embedder=embedder, store=store)

            # Execute search
            search_results = retriever.retrieve(search_query)

            # Transform results to API format
            results = []
            for result in search_results:
                chunk = result.chunk
                metadata = result.document_metadata

                # Extract video ID from chunk ID (format: video:{pk}:chunk:{index})
                video_id = chunk.id.split(':')[1] if ':' in chunk.id else ''

                result_item = {
                    'chunk_id': chunk.id,
                    'content': chunk.content,
                    'score': result.score,
                    'video_id': video_id,
                    'video_title': metadata.get('video_title', ''),
                    'video_url': metadata.get('video_url', ''),
                    'start_time': metadata.get('start_time', 0.0),
                    'end_time': metadata.get('end_time', 0.0),
                    'timestamp_url': metadata.get('timestamp_url', ''),
                }
                results.append(result_item)

            # Format response
            response_data = {
                'query': validated_data['q'],
                'results': results,
                'total': len(results)
            }

            # Validate response format
            response_serializer = SearchResponseSerializer(data=response_data)
            if not response_serializer.is_valid():
                # This shouldn't happen, but log it if it does
                return Response(
                    {'error': 'Internal error formatting response'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(response_serializer.validated_data)

        except ValueError as e:
            # Handle validation errors from retriever
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Handle unexpected errors
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_acl_context(self, user) -> QueryACLContext:
        """
        Build QueryACLContext from authenticated Django user.

        Extracts the user's ID and group memberships to create an ACL context
        for filtering search results based on permissions.

        Args:
            user: Django User instance from request.user

        Returns:
            QueryACLContext: ACL context for search filtering

        Note:
            In a multi-tenant setup, this would also extract tenant_id.
            Group memberships would be resolved from the user's groups.
        """
        # Use the user's username (which is the UUID from Supabase) as principal_id
        principal_id = str(user.username)

        # Get user's group memberships
        # In production, you might want to cache this
        group_ids = list(user.groups.values_list('name', flat=True))

        # For now, we're not using multi-tenant isolation
        # If needed, extract tenant_id from user profile or JWT claims
        tenant_id = None

        return QueryACLContext(
            principal_id=principal_id,
            member_of_groups=group_ids,
            tenant_id=tenant_id,
            bypass_acl=False
        )
