"""PostgreSQL pgvector implementation of VectorStoreInterface.

This module provides a production-ready vector store implementation using
PostgreSQL with the pgvector extension. It supports ACL-based filtering
at the database level for efficient permission enforcement.

Key features:
- Native pgvector similarity search (cosine distance)
- SQL-level ACL filtering for security and performance
- Batch operations for efficiency
- Connection pooling via context managers
- Parameterized queries for SQL injection prevention
"""

import json
from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection as Connection
from psycopg2.extras import execute_values

from rag.core.acl import ACLFilterSpec, QueryACLContext, Visibility
from rag.core.interfaces import VectorStoreInterface
from rag.core.schemas import Chunk, Embedding


class PgVectorStore(VectorStoreInterface):
    """PostgreSQL pgvector-based vector store with ACL filtering.

    This implementation uses PostgreSQL with the pgvector extension to store
    and search document chunks with their embeddings. ACL filtering is performed
    at the database level using SQL WHERE clauses for optimal performance.

    The store creates a table with the following schema:
    - chunk_id (TEXT PRIMARY KEY)
    - document_id (TEXT)
    - content (TEXT)
    - embedding (vector)
    - metadata (JSONB)
    - owner_id (TEXT)
    - visibility (TEXT)
    - shared_with_users (TEXT[])
    - shared_with_groups (TEXT[])
    - tenant_id (TEXT, nullable)

    Args:
        connection_string: PostgreSQL connection URL
            Format: postgresql://user:password@host:port/database
        table_name: Name of the table to store embeddings (default: 'rag_embeddings')
        dimensions: Vector embedding dimensions (default: 1536 for OpenAI ada-002)

    Example:
        >>> store = PgVectorStore(
        ...     connection_string="postgresql://user:pass@localhost/db",
        ...     table_name="my_embeddings",
        ...     dimensions=1536
        ... )
        >>> store.upsert(chunk, embedding)
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "rag_embeddings",
        dimensions: int = 1536
    ):
        """Initialize the PgVectorStore.

        Args:
            connection_string: PostgreSQL connection URL
            table_name: Table name for storing embeddings
            dimensions: Embedding vector dimensions
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.dimensions = dimensions
        self._ensure_table_exists()

    @contextmanager
    def _get_connection(self) -> Generator[Connection, None, None]:
        """Get a database connection with automatic cleanup.

        Yields:
            Connection: A psycopg2 connection object

        Raises:
            psycopg2.Error: If connection fails
        """
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_table_exists(self) -> None:
        """Create the embeddings table if it doesn't exist.

        Creates the table with pgvector extension and appropriate indexes.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # Create table with ACL fields
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector({self.dimensions}) NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        start_char INTEGER,
                        end_char INTEGER,
                        metadata JSONB DEFAULT '{{}}',
                        owner_id TEXT NOT NULL,
                        visibility TEXT NOT NULL DEFAULT 'private',
                        shared_with_users TEXT[] DEFAULT '{{}}',
                        shared_with_groups TEXT[] DEFAULT '{{}}',
                        tenant_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for efficient queries
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_document_id
                    ON {self.table_name}(document_id)
                """)
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_owner_id
                    ON {self.table_name}(owner_id)
                """)
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tenant_id
                    ON {self.table_name}(tenant_id)
                """)
                # Vector similarity index using cosine distance
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding_cosine
                    ON {self.table_name}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)

    def upsert(self, chunk: Chunk, embedding: Embedding) -> None:
        """Insert or update a chunk with its embedding.

        Args:
            chunk: The chunk to store
            embedding: The embedding for the chunk
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.table_name} (
                        chunk_id, document_id, content, embedding,
                        chunk_index, start_char, end_char, metadata,
                        owner_id, visibility, shared_with_users, shared_with_groups, tenant_id
                    ) VALUES (
                        %s, %s, %s, %s::vector,
                        %s, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        chunk_index = EXCLUDED.chunk_index,
                        start_char = EXCLUDED.start_char,
                        end_char = EXCLUDED.end_char,
                        metadata = EXCLUDED.metadata,
                        owner_id = EXCLUDED.owner_id,
                        visibility = EXCLUDED.visibility,
                        shared_with_users = EXCLUDED.shared_with_users,
                        shared_with_groups = EXCLUDED.shared_with_groups,
                        tenant_id = EXCLUDED.tenant_id
                """, (
                    chunk.id,
                    chunk.document_id,
                    chunk.content,
                    json.dumps(embedding.vector),  # Convert list to JSON for vector type
                    chunk.index,
                    chunk.start_char,
                    chunk.end_char,
                    json.dumps(chunk.metadata),
                    chunk.owner_id,
                    chunk.visibility.value,
                    chunk.shared_with_users,
                    chunk.shared_with_groups,
                    chunk.tenant_id
                ))

    def upsert_batch(self, chunks: list[Chunk], embeddings: list[Embedding]) -> None:
        """Batch insert/update chunks with embeddings.

        Args:
            chunks: List of chunks to store
            embeddings: List of embeddings (same order as chunks)

        Raises:
            ValueError: If chunks and embeddings lists have different lengths
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks and embeddings must have same length: "
                f"{len(chunks)} != {len(embeddings)}"
            )

        if not chunks:
            return

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Prepare data for batch insert
                values = [
                    (
                        chunk.id,
                        chunk.document_id,
                        chunk.content,
                        json.dumps(embedding.vector),
                        chunk.index,
                        chunk.start_char,
                        chunk.end_char,
                        json.dumps(chunk.metadata),
                        chunk.owner_id,
                        chunk.visibility.value,
                        chunk.shared_with_users,
                        chunk.shared_with_groups,
                        chunk.tenant_id
                    )
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ]

                # Use execute_values for efficient batch insert
                execute_values(
                    cur,
                    f"""
                    INSERT INTO {self.table_name} (
                        chunk_id, document_id, content, embedding,
                        chunk_index, start_char, end_char, metadata,
                        owner_id, visibility, shared_with_users, shared_with_groups, tenant_id
                    ) VALUES %s
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        chunk_index = EXCLUDED.chunk_index,
                        start_char = EXCLUDED.start_char,
                        end_char = EXCLUDED.end_char,
                        metadata = EXCLUDED.metadata,
                        owner_id = EXCLUDED.owner_id,
                        visibility = EXCLUDED.visibility,
                        shared_with_users = EXCLUDED.shared_with_users,
                        shared_with_groups = EXCLUDED.shared_with_groups,
                        tenant_id = EXCLUDED.tenant_id
                    """,
                    values,
                    template="""(
                        %s, %s, %s, %s::vector,
                        %s, %s, %s, %s::jsonb,
                        %s, %s, %s, %s, %s
                    )"""
                )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict | None = None,
        acl_context: QueryACLContext | None = None
    ) -> list[tuple[Chunk, float]]:
        """Search for similar chunks with optional ACL filtering.

        Uses cosine distance for vector similarity. ACL filtering is applied
        at the SQL level for security and performance.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters (not implemented yet)
            acl_context: ACL context for access control filtering.
                        Required unless bypass_acl=True.

        Returns:
            List of (chunk, score) tuples sorted by similarity (highest first)

        Raises:
            ValueError: If acl_context is None and bypass not enabled
        """
        # Validate ACL context requirement
        if acl_context is None:
            raise ValueError(
                "acl_context is required for search operations. "
                "Use QueryACLContext.system_context() for system operations."
            )

        # Build SQL query with similarity score in SELECT
        vector_json = json.dumps(query_vector)
        params = []

        # Start with SELECT including similarity calculation
        sql_parts = [
            f"SELECT *, (1 - (embedding <=> %s::vector)) as similarity FROM {self.table_name}"
        ]
        params.append(vector_json)

        # Apply ACL filtering unless bypassed
        if not acl_context.bypass_acl:
            # Build ACL filter spec
            acl_spec = ACLFilterSpec(
                principal_id=acl_context.principal_id,
                group_ids=acl_context.member_of_groups,
                tenant_id=acl_context.tenant_id,
                include_public=True,
                include_internal=True
            )
            acl_sql, acl_params = acl_spec.to_sql_conditions()
            sql_parts.append(f"WHERE {acl_sql}")
            params.extend(acl_params)

        # Add vector similarity ordering
        sql_parts.append("ORDER BY embedding <=> %s::vector")
        params.append(vector_json)

        sql_parts.append("LIMIT %s")
        params.append(top_k)

        # Build final SQL
        sql = " ".join(sql_parts)

        # Replace $N with %s for psycopg2 compatibility (for ACL params only)
        if not acl_context.bypass_acl:
            acl_params_count = len(acl_spec.to_sql_conditions()[1])
            for i in range(acl_params_count, 0, -1):
                sql = sql.replace(f"${i}", "%s", 1)

        # Execute query
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        # Convert rows to Chunk objects with scores
        # Column mapping (0-indexed):
        # 0:id, 1:chunk_id, 2:document_id, 3:content, 4:embedding, 5:metadata,
        # 6:owner_id, 7:visibility, 8:shared_with_users, 9:shared_with_groups,
        # 10:tenant_id, 11:created_at, 12:updated_at, 13:chunk_index,
        # 14:start_char, 15:end_char, 16:similarity
        results = []
        for row in rows:
            chunk = Chunk(
                id=row[1],  # chunk_id
                document_id=row[2],
                content=row[3],
                index=row[13],  # chunk_index
                start_char=row[14],
                end_char=row[15],
                metadata=row[5] if row[5] else {},
                owner_id=row[6],
                visibility=Visibility(row[7]),
                shared_with_users=row[8] if row[8] else [],
                shared_with_groups=row[9] if row[9] else [],
                tenant_id=row[10]
            )
            similarity = row[16]  # similarity column
            results.append((chunk, float(similarity)))

        return results

    def delete(self, chunk_ids: list[str]) -> None:
        """Delete chunks by ID.

        Args:
            chunk_ids: List of chunk IDs to delete
        """
        if not chunk_ids:
            return

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table_name} WHERE chunk_id = ANY(%s)",
                    (chunk_ids,)
                )

    def delete_by_document(self, document_id: str) -> None:
        """Delete all chunks belonging to a document.

        Args:
            document_id: Document ID whose chunks should be deleted
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self.table_name} WHERE document_id = %s",
                    (document_id,)
                )

    def delete_by_owner(self, owner_id: str, tenant_id: str | None = None) -> int:
        """Delete all chunks owned by a specific principal (GDPR compliance).

        This method supports the "right to be forgotten" by removing all content
        owned by a user. If tenant_id is provided, deletion is scoped to that tenant.

        Args:
            owner_id: The principal ID (user/service) whose chunks should be deleted
            tenant_id: Optional tenant ID to scope deletion. If None, deletes across
                      all tenants (or in single-tenant deployments). If provided,
                      only deletes chunks where tenant_id matches.

        Returns:
            int: Count of chunks deleted

        Raises:
            ValueError: If owner_id is empty or invalid
        """
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id cannot be empty")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                if tenant_id is not None:
                    cur.execute(
                        f"DELETE FROM {self.table_name} WHERE owner_id = %s AND tenant_id = %s",
                        (owner_id, tenant_id)
                    )
                else:
                    cur.execute(
                        f"DELETE FROM {self.table_name} WHERE owner_id = %s",
                        (owner_id,)
                    )
                return cur.rowcount

    def update_document_acl(
        self,
        document_id: str,
        visibility: Visibility | None = None,
        shared_with_users: list[str] | None = None,
        shared_with_groups: list[str] | None = None
    ) -> int:
        """Update ACL settings for all chunks belonging to a document.

        This method allows updating ACL fields without re-embedding the document.
        Only non-None parameters are updated, allowing partial updates.

        Args:
            document_id: The document ID whose chunks should be updated
            visibility: New visibility level (if provided)
            shared_with_users: New list of user IDs with access (if provided).
                              Replaces existing list completely.
            shared_with_groups: New list of group IDs with access (if provided).
                               Replaces existing list completely.

        Returns:
            int: Count of chunks updated

        Raises:
            ValueError: If document_id is empty or no update parameters provided
        """
        if not document_id or not document_id.strip():
            raise ValueError("document_id cannot be empty")

        # Build UPDATE statement with only non-None parameters
        update_fields: list[str] = []
        params: list[str | list[str]] = []

        if visibility is not None:
            update_fields.append("visibility = %s")
            params.append(visibility.value)

        if shared_with_users is not None:
            update_fields.append("shared_with_users = %s")
            params.append(shared_with_users)

        if shared_with_groups is not None:
            update_fields.append("shared_with_groups = %s")
            params.append(shared_with_groups)

        if not update_fields:
            raise ValueError("At least one ACL parameter must be provided for update")

        # Add document_id to params
        params.append(document_id)

        sql = f"""
            UPDATE {self.table_name}
            SET {', '.join(update_fields)}
            WHERE document_id = %s
        """

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount
