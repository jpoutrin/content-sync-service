"""Django bridge for RAG ACL context building.

This module provides integration between Django's authentication system and the RAG
module's ACL (Access Control List) system. It converts Django User instances into
QueryACLContext objects that can be used with the RAG vector search system.

Key functions:
    - build_acl_context(): Convert Django User to QueryACLContext
    - system_acl_context(): Create a system-level context that bypasses ACL checks
    - get_vector_store(): Factory function to get a configured PgVectorStore instance

Usage Examples:
    Basic usage in a Django view:

        from yt_sync.rag_bridge import build_acl_context, get_vector_store

        def search_view(request):
            # Build ACL context from authenticated user
            acl_context = build_acl_context(request.user)

            # Get vector store instance
            store = get_vector_store()

            # Perform search with ACL filtering
            results = store.search(
                query_vector=embedder.embed(request.GET['q']),
                top_k=10,
                acl_context=acl_context
            )
            return JsonResponse({'results': results})

    System operations (admin/background tasks):

        from yt_sync.rag_bridge import system_acl_context, get_vector_store

        def admin_cleanup_task():
            # Use system context to bypass ACL checks
            ctx = system_acl_context()
            store = get_vector_store()

            # Delete all chunks for a user (GDPR compliance)
            deleted_count = store.delete_by_owner(
                owner_id="user-123",
                tenant_id=None
            )
            return deleted_count

    Multi-tenant usage:

        # Assuming User model has a 'tenant_id' attribute
        def tenant_search_view(request):
            acl_context = build_acl_context(request.user)
            # acl_context.tenant_id will be automatically populated
            # if request.user has a tenant_id attribute

            store = get_vector_store()
            results = store.search(
                query_vector=embedder.embed(request.GET['q']),
                top_k=10,
                acl_context=acl_context
            )
            return JsonResponse({'results': results})
"""

from typing import TYPE_CHECKING

from django.conf import settings

from rag.core.acl import QueryACLContext

if TYPE_CHECKING:
    from rag.stores.pgvector import PgVectorStore
    from yt_sync.models import User


def build_acl_context(user: "User") -> QueryACLContext:
    """Build ACL context from Django User instance.

    Extracts the necessary ACL information from a Django User instance and creates
    a QueryACLContext that can be used with RAG search operations. This function
    handles:

    - Principal ID extraction (uses user.id converted to string)
    - Group membership resolution (via user.groups.all())
    - Tenant ID extraction (if user model has a tenant_id attribute)

    The returned QueryACLContext can be passed to VectorStoreInterface.search()
    to filter results based on the user's permissions.

    Args:
        user: Django User instance (must be authenticated)

    Returns:
        QueryACLContext: Fully populated ACL context for the user

    Example:
        >>> from django.contrib.auth import get_user_model
        >>> from yt_sync.rag_bridge import build_acl_context
        >>>
        >>> User = get_user_model()
        >>> user = User.objects.get(username='john')
        >>> acl_context = build_acl_context(user)
        >>> print(acl_context.principal_id)
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        >>> print(acl_context.member_of_groups)
        ['editors', 'viewers']

    Notes:
        - principal_id is always the user.id (UUID) converted to string
        - Groups are resolved from Django's auth system (user.groups.all())
        - Group IDs are converted to strings (using group.name by default)
        - tenant_id is extracted only if the User model has that attribute
        - For anonymous users, consider using system_acl_context() with appropriate
          logging/auditing, or create a dedicated anonymous context
    """
    # Extract principal ID from user (UUID converted to string)
    principal_id = str(user.id)

    # Resolve group memberships
    # Django groups are accessed via user.groups.all()
    # We use group.name as the group identifier (could also use group.id)
    member_of_groups = [group.name for group in user.groups.all()]

    # Extract tenant_id if present on user model
    # Use hasattr to safely check for multi-tenant deployments
    tenant_id = None
    if hasattr(user, 'tenant_id'):
        # tenant_id might be None even if attribute exists
        tenant_id = getattr(user, 'tenant_id', None)
        # Convert to string if not None
        if tenant_id is not None:
            tenant_id = str(tenant_id)

    return QueryACLContext(
        principal_id=principal_id,
        member_of_groups=member_of_groups,
        tenant_id=tenant_id,
        bypass_acl=False
    )


def system_acl_context() -> QueryACLContext:
    """Create a system-level ACL context that bypasses ACL checks.

    Returns a QueryACLContext with bypass_acl=True, which allows system-level
    operations to access all documents regardless of ACL settings. This should
    be used sparingly and only for:

    - Administrative operations (e.g., data cleanup, migrations)
    - Background tasks that operate on behalf of the system
    - Compliance operations (e.g., GDPR "right to be forgotten")
    - Monitoring and auditing tasks

    IMPORTANT: All uses of system_acl_context() should be logged and audited
    for security and compliance purposes.

    Returns:
        QueryACLContext: System context with bypass_acl=True

    Example:
        >>> from yt_sync.rag_bridge import system_acl_context, get_vector_store
        >>>
        >>> # GDPR compliance: delete all content for a user
        >>> def delete_user_data(user_id: str):
        ...     ctx = system_acl_context()
        ...     store = get_vector_store()
        ...
        ...     # This bypasses ACL checks and deletes all chunks owned by user
        ...     deleted_count = store.delete_by_owner(
        ...         owner_id=user_id,
        ...         tenant_id=None  # Delete across all tenants
        ...     )
        ...
        ...     # IMPORTANT: Log this action for audit trail
        ...     logger.info(
        ...         f"GDPR deletion: removed {deleted_count} chunks for user {user_id}"
        ...     )
        ...     return deleted_count

    Notes:
        - Principal ID is set to "system" by convention
        - bypass_acl=True means no ACL filtering will be applied
        - Should be paired with logging/auditing in production
        - Consider using more specific contexts (e.g., "admin", "migration")
          with appropriate principal_id values for better audit trails
    """
    return QueryACLContext.system_context()


def get_vector_store() -> "PgVectorStore":
    """Factory function to get a configured PgVectorStore instance.

    Reads database connection settings from Django's DATABASES configuration
    and returns a PgVectorStore instance connected to the default database.

    The connection string is built from Django settings.DATABASES['default'],
    which should be configured via the DATABASE_URL environment variable
    (when using django-environ) or directly in settings.py.

    Returns:
        PgVectorStore: Configured vector store instance

    Example:
        >>> from yt_sync.rag_bridge import get_vector_store
        >>>
        >>> # Get store instance
        >>> store = get_vector_store()
        >>>
        >>> # Use for search operations
        >>> results = store.search(
        ...     query_vector=embedding,
        ...     top_k=5,
        ...     acl_context=acl_context
        ... )

    Configuration:
        The function expects settings.DATABASES['default'] to contain:
        - ENGINE: 'django.db.backends.postgresql' (or compatible)
        - NAME: database name
        - USER: database user
        - PASSWORD: database password
        - HOST: database host
        - PORT: database port (defaults to 5432)

        Example .env file:
            DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

    Notes:
        - The PgVectorStore expects pgvector extension to be enabled in PostgreSQL
        - Connection pooling is handled by psycopg2 (used internally by PgVectorStore)
        - Table name defaults to "rag_embeddings" (configurable in PgVectorStore)
        - Dimensions default to 1536 (OpenAI text-embedding-ada-002 size)

    Raises:
        ImportError: If PgVectorStore is not available (dependency not met)
        KeyError: If DATABASES['default'] is not configured
        ValueError: If database configuration is invalid
    """
    # Import here to avoid circular imports and handle missing dependency
    from rag.stores.pgvector import PgVectorStore

    # Get database configuration from Django settings
    db_config = settings.DATABASES['default']

    # Build connection string from Django database configuration
    # Django uses 'django-environ' which parses DATABASE_URL into dict format
    engine = db_config.get('ENGINE', '')

    # Ensure we're using PostgreSQL (required for pgvector)
    if 'postgresql' not in engine.lower():
        raise ValueError(
            f"PgVectorStore requires PostgreSQL database. "
            f"Current ENGINE: {engine}"
        )

    # Extract connection parameters
    db_name = db_config.get('NAME', '')
    db_user = db_config.get('USER', '')
    db_password = db_config.get('PASSWORD', '')
    db_host = db_config.get('HOST', 'localhost')
    db_port = db_config.get('PORT', 5432)

    # Build PostgreSQL connection string
    # Format: postgresql://user:password@host:port/database
    connection_string = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    # Create and return PgVectorStore instance
    # Uses default table name "rag_embeddings" and dimensions 1536
    # These can be customized by passing parameters to PgVectorStore()
    return PgVectorStore(
        connection_string=connection_string,
        table_name="rag_embeddings",
        dimensions=1536
    )
