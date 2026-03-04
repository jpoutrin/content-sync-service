"""Tests for RAG search API endpoint."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

import pytest

from rag.core.acl import QueryACLContext, Visibility
from rag.core.schemas import Chunk, SearchResult

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client for tests."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username='test-user-123')


@pytest.fixture
def mock_retriever():
    """Mock retriever that returns sample search results."""
    # Mock all the dependencies
    with patch('rag.api.views.LiteLLMEmbedder'), \
         patch('rag.api.views.PgVectorStore'), \
         patch('rag.api.views.DefaultRetriever') as mock_retriever_class:

        retriever_instance = MagicMock()
        mock_retriever_class.return_value = retriever_instance

        # Create sample chunk with metadata
        chunk = Chunk(
            id='video:42:chunk:5',
            document_id='video:42',
            content='To configure Django settings, edit the settings.py file...',
            index=5,
            owner_id='test-user-123',
            visibility=Visibility.PUBLIC,
            metadata={
                'start_time': 125.5,
                'end_time': 185.2,
                'video_title': 'Django Tutorial - Configuration Best Practices',
                'video_url': 'https://youtube.com/watch?v=abc123',
                'youtube_video_id': 'abc123',
            }
        )

        # Create sample search result
        result = SearchResult(
            chunk=chunk,
            score=0.89,
            document_metadata={
                'start_time': 125.5,
                'end_time': 185.2,
                'video_title': 'Django Tutorial - Configuration Best Practices',
                'video_url': 'https://youtube.com/watch?v=abc123',
                'youtube_video_id': 'abc123',
                'timestamp_url': 'https://youtube.com/watch?v=abc123&t=125',
            }
        )

        retriever_instance.retrieve.return_value = [result]
        yield retriever_instance


@pytest.mark.django_db
class TestSearchView:
    """Test cases for the SearchView API endpoint."""

    def test_search_requires_authentication(self, api_client):
        """Test that search endpoint requires authentication."""
        url = reverse('rag-search')
        response = api_client.get(url, {'q': 'test query'})
        # DRF returns 403 when IsAuthenticated permission fails
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_with_valid_query(self, api_client, user, mock_retriever):
        """Test successful search with valid query parameters."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        response = api_client.get(url, {
            'q': 'How to configure Django?',
            'top_k': 5,
            'min_score': 0.7
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert 'query' in data
        assert 'results' in data
        assert 'total' in data

        # Verify response values
        assert data['query'] == 'How to configure Django?'
        assert data['total'] == 1
        assert len(data['results']) == 1

        # Verify result item structure
        result = data['results'][0]
        assert result['chunk_id'] == 'video:42:chunk:5'
        assert result['content'] == 'To configure Django settings, edit the settings.py file...'
        assert result['score'] == 0.89
        assert result['video_id'] == '42'
        assert result['video_title'] == 'Django Tutorial - Configuration Best Practices'
        assert result['video_url'] == 'https://youtube.com/watch?v=abc123'
        assert result['start_time'] == 125.5
        assert result['end_time'] == 185.2
        assert result['timestamp_url'] == 'https://youtube.com/watch?v=abc123&t=125'

    def test_search_with_default_parameters(self, api_client, user, mock_retriever):
        """Test search with only required query parameter."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        response = api_client.get(url, {'q': 'test query'})

        assert response.status_code == status.HTTP_200_OK
        # Verify that default values were used
        mock_retriever.retrieve.assert_called_once()
        search_query = mock_retriever.retrieve.call_args[0][0]
        assert search_query.top_k == 5
        assert search_query.min_score == 0.0

    def test_search_missing_query_parameter(self, api_client, user):
        """Test that search fails when query parameter is missing."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'q' in response.json()

    def test_search_query_too_long(self, api_client, user):
        """Test that search fails when query exceeds max length."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        # Create query longer than 500 characters
        long_query = 'a' * 501

        response = api_client.get(url, {'q': long_query})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'q' in response.json()

    def test_search_invalid_top_k(self, api_client, user):
        """Test that search fails with invalid top_k values."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        # Test top_k = 0
        response = api_client.get(url, {'q': 'test', 'top_k': 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test top_k > 100
        response = api_client.get(url, {'q': 'test', 'top_k': 101})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_invalid_min_score(self, api_client, user):
        """Test that search fails with invalid min_score values."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        # Test min_score < 0
        response = api_client.get(url, {'q': 'test', 'min_score': -0.1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test min_score > 1.0
        response = api_client.get(url, {'q': 'test', 'min_score': 1.1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_builds_correct_acl_context(self, api_client, user, mock_retriever):
        """Test that ACL context is correctly built from authenticated user."""
        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        response = api_client.get(url, {'q': 'test query'})

        assert response.status_code == status.HTTP_200_OK

        # Verify ACL context was built correctly
        mock_retriever.retrieve.assert_called_once()
        search_query = mock_retriever.retrieve.call_args[0][0]
        acl_context = search_query.acl_context

        assert isinstance(acl_context, QueryACLContext)
        assert acl_context.principal_id == 'test-user-123'
        assert acl_context.bypass_acl is False
        assert acl_context.tenant_id is None

    def test_search_with_user_groups(self, api_client, user, mock_retriever, db):
        """Test that user's group memberships are included in ACL context."""
        from django.contrib.auth.models import Group

        # Create groups and add user to them
        group1 = Group.objects.create(name='editors')
        group2 = Group.objects.create(name='reviewers')
        user.groups.add(group1, group2)

        api_client.force_authenticate(user=user)
        url = reverse('rag-search')

        response = api_client.get(url, {'q': 'test query'})

        assert response.status_code == status.HTTP_200_OK

        # Verify group memberships in ACL context
        mock_retriever.retrieve.assert_called_once()
        search_query = mock_retriever.retrieve.call_args[0][0]
        acl_context = search_query.acl_context

        assert 'editors' in acl_context.member_of_groups
        assert 'reviewers' in acl_context.member_of_groups

    def test_search_empty_results(self, api_client, user):
        """Test search that returns no results."""
        with patch('rag.api.views.LiteLLMEmbedder'), \
             patch('rag.api.views.PgVectorStore'), \
             patch('rag.api.views.DefaultRetriever') as mock_retriever_class:

            retriever = MagicMock()
            retriever.retrieve.return_value = []
            mock_retriever_class.return_value = retriever

            api_client.force_authenticate(user=user)
            url = reverse('rag-search')

            response = api_client.get(url, {'q': 'nonexistent query'})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['total'] == 0
            assert len(data['results']) == 0

    def test_search_handles_retriever_value_error(self, api_client, user):
        """Test that ValueError from retriever returns 400."""
        with patch('rag.api.views.LiteLLMEmbedder'), \
             patch('rag.api.views.PgVectorStore'), \
             patch('rag.api.views.DefaultRetriever') as mock_retriever_class:

            retriever = MagicMock()
            retriever.retrieve.side_effect = ValueError("Invalid query")
            mock_retriever_class.return_value = retriever

            api_client.force_authenticate(user=user)
            url = reverse('rag-search')

            response = api_client.get(url, {'q': 'test'})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'error' in response.json()

    def test_search_handles_retriever_runtime_error(self, api_client, user):
        """Test that RuntimeError from retriever returns 500."""
        with patch('rag.api.views.DefaultRetriever') as mock_retriever_class:
            retriever = MagicMock()
            retriever.retrieve.side_effect = RuntimeError("Search failed")
            mock_retriever_class.return_value = retriever

            api_client.force_authenticate(user=user)
            url = reverse('rag-search')

            response = api_client.get(url, {'q': 'test'})

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.json()

    def test_search_multiple_results_sorted_by_score(self, api_client, user):
        """Test that multiple results are returned in score order."""
        with patch('rag.api.views.LiteLLMEmbedder'), \
             patch('rag.api.views.PgVectorStore'), \
             patch('rag.api.views.DefaultRetriever') as mock_retriever_class:

            retriever = MagicMock()

            # Create multiple results with different scores
            results = []
            for i, score in enumerate([0.95, 0.87, 0.76]):
                chunk = Chunk(
                    id=f'video:1:chunk:{i}',
                    document_id='video:1',
                    content=f'Content {i}',
                    index=i,
                    owner_id='test-user-123',
                    visibility=Visibility.PUBLIC,
                    metadata={
                        'start_time': float(i * 10),
                        'end_time': float(i * 10 + 5),
                        'video_title': 'Test Video',
                        'video_url': 'https://youtube.com/watch?v=test',
                        'youtube_video_id': 'test',
                    }
                )
                result = SearchResult(
                    chunk=chunk,
                    score=score,
                    document_metadata={
                        'start_time': float(i * 10),
                        'end_time': float(i * 10 + 5),
                        'video_title': 'Test Video',
                        'video_url': 'https://youtube.com/watch?v=test',
                        'youtube_video_id': 'test',
                        'timestamp_url': f'https://youtube.com/watch?v=test&t={i * 10}',
                    }
                )
                results.append(result)

            retriever.retrieve.return_value = results
            mock_retriever_class.return_value = retriever

            api_client.force_authenticate(user=user)
            url = reverse('rag-search')

            response = api_client.get(url, {'q': 'test', 'top_k': 10})

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data['total'] == 3

            # Verify results are in correct order
            assert data['results'][0]['score'] == 0.95
            assert data['results'][1]['score'] == 0.87
            assert data['results'][2]['score'] == 0.76
