"""Django management command for bulk transcript ingestion into RAG vector store."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rag.chunkers.transcript import TranscriptChunker
from rag.embedders.litellm import LiteLLMEmbedder
from rag.services import IngestionService
from rag.stores.pgvector import PgVectorStore
from yt_sync.models import Source, Video


class Command(BaseCommand):
    """
    Ingest video transcripts into the RAG vector store for semantic search.

    This command processes video transcripts by:
    1. Chunking transcripts using TranscriptChunker
    2. Generating embeddings via LiteLLMEmbedder
    3. Storing chunks and embeddings in PgVectorStore

    Examples:
        # Ingest all videos
        python manage.py rag_ingest --all

        # Ingest specific video
        python manage.py rag_ingest --video-id abc123-def456

        # Ingest videos from a source
        python manage.py rag_ingest --source my-channel

        # Preview without ingesting
        python manage.py rag_ingest --all --dry-run

        # Force re-ingestion
        python manage.py rag_ingest --all --reingest
    """

    help = "Ingest video transcripts into RAG vector store for semantic search"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        # Selection filters
        parser.add_argument(
            "--video-id",
            type=str,
            help="Ingest a specific video by ID (UUID or YouTube ID)",
        )
        parser.add_argument(
            "--source",
            type=str,
            help="Ingest all videos from a specific source (by slug or ID)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Ingest all videos with completed transcripts",
        )

        # Behavior modifiers
        parser.add_argument(
            "--reingest",
            action="store_true",
            help="Force re-ingestion of videos (delete existing chunks first)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be ingested without making changes",
        )

    def handle(self, *args, **options):
        """Execute the ingestion command."""
        video_id = options.get("video_id")
        source = options.get("source")
        ingest_all = bool(options.get("all"))
        reingest = bool(options.get("reingest"))
        dry_run = bool(options.get("dry_run"))

        # Validate arguments
        if not any([video_id, source, ingest_all]):
            raise CommandError(
                "You must specify one of: --video-id, --source, or --all"
            )

        if sum([bool(video_id), bool(source), bool(ingest_all)]) > 1:
            raise CommandError(
                "You can only specify one of: --video-id, --source, or --all"
            )

        # Display mode information
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made\n"))

        # Initialize RAG components
        try:
            chunker = self._create_chunker()
            embedder = self._create_embedder()
            vector_store = self._create_vector_store()
            service = IngestionService(chunker, embedder, vector_store)
        except Exception as e:
            raise CommandError(f"Failed to initialize RAG components: {e}") from e

        # Build queryset based on filters
        videos = self._get_videos_queryset(video_id, source, ingest_all)

        # Display summary
        total_videos = videos.count()
        self.stdout.write(f"Found {total_videos} videos to process\n")

        if total_videos == 0:
            self.stdout.write(self.style.WARNING("No videos to process"))
            return

        # Process videos
        success_count = 0
        error_count = 0
        skip_count = 0
        total_chunks = 0

        for video in videos:
            result = self._process_video(
                service=service,
                vector_store=vector_store,
                video=video,
                reingest=reingest,
                dry_run=dry_run,
            )

            if result["status"] == "success":
                success_count += 1
                total_chunks += result["chunk_count"]
            elif result["status"] == "skipped":
                skip_count += 1
            else:
                error_count += 1

        # Display final summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"Successfully ingested: {success_count}"))
        if skip_count > 0:
            self.stdout.write(self.style.WARNING(f"Skipped: {skip_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
        self.stdout.write(f"Total chunks indexed: {total_chunks}")

    def _create_chunker(self) -> TranscriptChunker:
        """Create TranscriptChunker from settings.

        Returns:
            Configured TranscriptChunker instance
        """
        return TranscriptChunker(
            gap_threshold=settings.RAG_CHUNK_GAP_THRESHOLD,
            max_chars=settings.RAG_CHUNK_MAX_CHARS,
            min_chars=settings.RAG_CHUNK_MIN_CHARS,
        )

    def _create_embedder(self) -> LiteLLMEmbedder:
        """Create LiteLLMEmbedder from settings.

        Returns:
            Configured LiteLLMEmbedder instance
        """
        provider = settings.RAG_EMBEDDING_PROVIDER
        model = settings.RAG_EMBEDDING_MODEL
        batch_size = settings.RAG_EMBEDDING_BATCH_SIZE

        return LiteLLMEmbedder(
            provider=provider,
            model=model,
            batch_size=batch_size,
        )

    def _create_vector_store(self) -> PgVectorStore:
        """Create PgVectorStore using Django database connection.

        Returns:
            Configured PgVectorStore instance
        """
        # Get database connection settings from Django
        db_settings = settings.DATABASES["default"]

        # Build PostgreSQL connection string
        connection_string = (
            f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}"
            f"@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        )

        # Get embedder to determine dimensions
        embedder = self._create_embedder()

        return PgVectorStore(
            connection_string=connection_string,
            table_name="rag_embeddings",
            dimensions=embedder.dimensions,
        )

    def _get_videos_queryset(
        self, video_id: str | None, source: str | None, ingest_all: bool
    ):
        """Build Video queryset based on filter arguments.

        Args:
            video_id: Video ID filter
            source: Source ID/slug filter
            ingest_all: Process all videos flag

        Returns:
            Video queryset with select_related optimization

        Raises:
            CommandError: If filters don't match any videos
        """
        # Base queryset with optimizations
        videos = Video.objects.select_related("source", "source__user")

        # Filter by completion status (must have transcript)
        videos = videos.filter(
            transcript_status=Video.ProcessingStatus.COMPLETED,
            transcript_data__isnull=False,
        ).exclude(transcript_data=[])

        # Apply additional filters
        if video_id:
            # Try UUID first (catches ValidationError if not valid UUID), then YouTube ID
            try:
                videos = videos.filter(id=video_id) | videos.filter(
                    youtube_video_id=video_id
                )
            except Exception:
                # If UUID validation fails, just try youtube_video_id
                videos = videos.filter(youtube_video_id=video_id)

            if not videos.exists():
                raise CommandError(f"Video with ID '{video_id}' not found")

        elif source:
            # Try source ID first (catches ValidationError if not valid UUID), then youtube_id
            try:
                source_obj = Source.objects.filter(id=source).first()
            except Exception:
                source_obj = None

            if not source_obj:
                source_obj = Source.objects.filter(youtube_id=source).first()

            if not source_obj:
                raise CommandError(f"Source '{source}' not found")
            videos = videos.filter(source=source_obj)

        elif ingest_all:
            # No additional filters needed
            pass

        return videos.order_by("published_at")

    def _process_video(
        self,
        service: IngestionService,
        vector_store: PgVectorStore,
        video: Video,
        reingest: bool,
        dry_run: bool,
    ) -> dict:
        """Process a single video for ingestion.

        Args:
            service: IngestionService instance
            vector_store: PgVectorStore instance
            video: Video to process
            reingest: Whether to force re-ingestion
            dry_run: Whether to skip actual ingestion

        Returns:
            Dict with status and chunk_count keys
        """
        # Display video info
        video_display = (
            f"{video.title[:50]}..." if len(video.title) > 50 else video.title
        )
        self.stdout.write(f"\nProcessing: {video_display}")
        self.stdout.write(f"  ID: {video.id}")
        self.stdout.write(f"  YouTube ID: {video.youtube_video_id}")

        # Check if already ingested (unless reingest flag is set)
        document_id = f"video:{video.pk}"

        if not reingest and not dry_run:
            # Check if chunks exist for this document
            with vector_store._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM {vector_store.table_name} WHERE document_id = %s",
                        (document_id,),
                    )
                    result = cur.fetchone()
                    existing_count = result[0] if result else 0

            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⊘ Skipped (already ingested, {existing_count} chunks) - use --reingest to force"
                    )
                )
                return {"status": "skipped", "chunk_count": 0}

        # Delete existing chunks if reingest flag is set
        if reingest and not dry_run:
            self.stdout.write("  ↻ Re-ingesting (deleting existing chunks)...")
            vector_store.delete_by_document(document_id)

        # Perform ingestion
        try:
            if dry_run:
                # Just validate without ingesting
                if not video.transcript_data:
                    raise ValueError("No transcript data")
                chunk_count = len(video.transcript_data)  # Rough estimate
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Would ingest (~{chunk_count} segments)")
                )
            else:
                chunk_count = service.ingest_video(video)
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Ingested {chunk_count} chunks")
                )

            return {"status": "success", "chunk_count": chunk_count}

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  ✗ Error: {e}"))
            return {"status": "error", "chunk_count": 0}
