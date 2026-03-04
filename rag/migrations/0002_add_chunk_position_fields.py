"""
Add chunk position and offset fields to rag_embeddings table.

This migration adds:
- chunk_index: Position of chunk within document
- start_char: Start character offset in original document
- end_char: End character offset in original document
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rag', '0001_create_rag_embeddings'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Add chunk position fields
                ALTER TABLE rag_embeddings
                ADD COLUMN chunk_index INTEGER NOT NULL DEFAULT 0,
                ADD COLUMN start_char INTEGER,
                ADD COLUMN end_char INTEGER;

                -- Create index on chunk_index for ordering
                CREATE INDEX idx_rag_embeddings_chunk_index ON rag_embeddings (document_id, chunk_index);
            """,
            reverse_sql="""
                -- Drop index
                DROP INDEX IF EXISTS idx_rag_embeddings_chunk_index;

                -- Drop columns
                ALTER TABLE rag_embeddings
                DROP COLUMN IF EXISTS chunk_index,
                DROP COLUMN IF EXISTS start_char,
                DROP COLUMN IF EXISTS end_char;
            """,
        ),
    ]
