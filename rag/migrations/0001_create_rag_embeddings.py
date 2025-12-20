"""
Database migration for RAG embeddings table with ACL support.

This migration creates the rag_embeddings table with:
- pgvector extension for vector similarity search
- ACL fields (owner_id, visibility, shared_with_users, shared_with_groups, tenant_id)
- HNSW index for efficient vector similarity search
- B-tree indexes for ACL filtering
- GIN indexes for array column searches
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
                -- Enable pgvector extension
                CREATE EXTENSION IF NOT EXISTS vector;

                -- Create rag_embeddings table
                CREATE TABLE rag_embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    document_id VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    owner_id VARCHAR(255) NOT NULL,
                    visibility VARCHAR(50) NOT NULL DEFAULT 'PRIVATE',
                    shared_with_users TEXT[] DEFAULT '{}',
                    shared_with_groups TEXT[] DEFAULT '{}',
                    tenant_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                -- Create HNSW index on embedding column for vector similarity search
                CREATE INDEX idx_rag_embeddings_embedding ON rag_embeddings USING hnsw (embedding vector_cosine_ops);

                -- Create B-tree indexes for ACL filtering
                CREATE INDEX idx_rag_embeddings_owner ON rag_embeddings (owner_id);
                CREATE INDEX idx_rag_embeddings_visibility ON rag_embeddings (visibility);
                CREATE INDEX idx_rag_embeddings_document ON rag_embeddings (document_id);

                -- Create partial B-tree index for tenant_id (only for non-NULL values)
                CREATE INDEX idx_rag_embeddings_tenant ON rag_embeddings (tenant_id) WHERE tenant_id IS NOT NULL;

                -- Create GIN indexes for array column searches
                CREATE INDEX idx_rag_embeddings_shared_users ON rag_embeddings USING gin (shared_with_users);
                CREATE INDEX idx_rag_embeddings_shared_groups ON rag_embeddings USING gin (shared_with_groups);
            """,
            reverse_sql="""
                -- Drop indexes first
                DROP INDEX IF EXISTS idx_rag_embeddings_shared_groups;
                DROP INDEX IF EXISTS idx_rag_embeddings_shared_users;
                DROP INDEX IF EXISTS idx_rag_embeddings_tenant;
                DROP INDEX IF EXISTS idx_rag_embeddings_document;
                DROP INDEX IF EXISTS idx_rag_embeddings_visibility;
                DROP INDEX IF EXISTS idx_rag_embeddings_owner;
                DROP INDEX IF EXISTS idx_rag_embeddings_embedding;

                -- Drop table
                DROP TABLE IF EXISTS rag_embeddings;

                -- Note: We don't drop the pgvector extension as other tables might use it
            """,
        ),
    ]
