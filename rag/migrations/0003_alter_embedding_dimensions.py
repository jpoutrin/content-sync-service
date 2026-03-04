"""
Alter embedding column dimensions from 1536 to 384.

This migration changes the vector dimensions to match the default local
embedding model (sentence-transformers/all-MiniLM-L6-v2) which produces
384-dimensional vectors.

WARNING: This migration will truncate the rag_embeddings table to avoid
dimension mismatch errors. If you have existing embeddings, they will be lost.
Re-run ingestion after this migration.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0002_add_chunk_position_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop existing indexes that depend on the embedding column
                DROP INDEX IF EXISTS idx_rag_embeddings_embedding;

                -- Truncate table to avoid dimension mismatch with existing data
                -- This is necessary because pgvector cannot convert between dimensions
                TRUNCATE TABLE rag_embeddings;

                -- Alter the embedding column to use 384 dimensions (local model)
                ALTER TABLE rag_embeddings
                ALTER COLUMN embedding TYPE vector(384);

                -- Recreate the HNSW index with the new dimensions
                CREATE INDEX idx_rag_embeddings_embedding
                ON rag_embeddings
                USING hnsw (embedding vector_cosine_ops);
            """,
            reverse_sql="""
                -- Drop the index
                DROP INDEX IF EXISTS idx_rag_embeddings_embedding;

                -- Truncate table before reversing
                TRUNCATE TABLE rag_embeddings;

                -- Revert to 1536 dimensions
                ALTER TABLE rag_embeddings
                ALTER COLUMN embedding TYPE vector(1536);

                -- Recreate the original HNSW index
                CREATE INDEX idx_rag_embeddings_embedding
                ON rag_embeddings
                USING hnsw (embedding vector_cosine_ops);
            """,
        ),
    ]
