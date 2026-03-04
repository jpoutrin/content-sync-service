"""Transcript-aware semantic chunking with timestamp and ACL metadata.

This module implements the TranscriptChunker, which splits video transcripts
into semantic chunks based on timestamp gaps while respecting character limits.
Each chunk preserves ACL metadata from the parent document for access control.
"""

from typing import Any

from rag.core.interfaces import ChunkerInterface
from rag.core.schemas import Chunk, Document


class TranscriptChunker(ChunkerInterface):
    """Transcript-aware semantic chunking with timestamp and ACL metadata.

    Splits timestamped transcript segments into chunks based on:
    - Temporal gaps between segments (configurable threshold)
    - Maximum and minimum character limits
    - Semantic boundaries (preserving complete segments where possible)

    Each chunk includes metadata with:
    - start_time, end_time: Temporal boundaries in seconds
    - segment_count: Number of transcript segments merged
    - video_title, video_url, youtube_video_id: Video metadata

    Chunk IDs follow the format: video:{video_pk}:chunk:{index}

    Args:
        gap_threshold: Maximum gap in seconds between segments to merge (default: 2.0)
        max_chars: Maximum characters per chunk (default: 1000)
        min_chars: Minimum characters per chunk (default: 100)

    Example:
        >>> chunker = TranscriptChunker(gap_threshold=2.0, max_chars=1000)
        >>> document = Document(
        ...     id="video:42",
        ...     content="",  # Not used for transcript chunking
        ...     owner_id="user:123",
        ...     metadata={
        ...         "transcript_segments": [
        ...             {"text": "Hello world", "start": 0.0, "duration": 2.0},
        ...             {"text": "Welcome", "start": 2.5, "duration": 1.5},
        ...         ],
        ...         "video_title": "My Video",
        ...         "video_url": "https://example.com/video/42",
        ...         "youtube_video_id": "abc123",
        ...     }
        ... )
        >>> chunks = chunker.chunk(document)
        >>> len(chunks)
        1
        >>> chunks[0].metadata["start_time"]
        0.0
    """

    def __init__(
        self,
        gap_threshold: float = 2.0,
        max_chars: int = 1000,
        min_chars: int = 100
    ):
        """Initialize the TranscriptChunker.

        Args:
            gap_threshold: Maximum gap in seconds between segments to merge into one chunk
            max_chars: Maximum characters per chunk
            min_chars: Minimum characters per chunk (avoid tiny fragments)

        Raises:
            ValueError: If parameters are invalid (e.g., max_chars < min_chars)
        """
        if max_chars < min_chars:
            raise ValueError(f"max_chars ({max_chars}) must be >= min_chars ({min_chars})")
        if gap_threshold < 0:
            raise ValueError(f"gap_threshold ({gap_threshold}) must be >= 0")
        if min_chars < 0:
            raise ValueError(f"min_chars ({min_chars}) must be >= 0")

        self.gap_threshold = gap_threshold
        self.max_chars = max_chars
        self.min_chars = min_chars

    def chunk(self, document: Document) -> list[Chunk]:
        """Split a transcript document into chunks.

        Processes transcript segments from document.metadata["transcript_segments"],
        merging segments into chunks based on temporal proximity and size constraints.

        Args:
            document: Document containing transcript_segments in metadata

        Returns:
            List of Chunk objects with timestamp metadata and ACL fields copied
            from the parent document

        Raises:
            ValueError: If document lacks required metadata or segments are invalid
        """
        # Extract transcript segments from metadata
        segments = document.metadata.get("transcript_segments", [])
        if not segments:
            raise ValueError("Document metadata must contain 'transcript_segments' list")

        # Extract video metadata for chunk annotations
        video_title = document.metadata.get("video_title", "")
        video_url = document.metadata.get("video_url", "")
        youtube_video_id = document.metadata.get("youtube_video_id", "")

        if not video_title or not video_url or not youtube_video_id:
            raise ValueError(
                "Document metadata must contain 'video_title', 'video_url', "
                "and 'youtube_video_id'"
            )

        # Extract video primary key from document ID (format: video:{pk})
        if not document.id.startswith("video:"):
            raise ValueError(f"Document ID must start with 'video:' (got: {document.id})")

        video_pk = document.id.split(":", 1)[1]

        # Validate segments have required fields
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                raise ValueError(f"Segment {i} must be a dictionary")
            if "text" not in segment or "start" not in segment or "duration" not in segment:
                raise ValueError(
                    f"Segment {i} must have 'text', 'start', and 'duration' fields"
                )

        # Build chunks by merging segments based on gaps and size
        chunks: list[Chunk] = []
        current_texts: list[str] = []
        current_start: float | None = None
        current_end: float | None = None
        current_segment_count = 0

        for segment in segments:
            text = segment["text"].strip()
            if not text:  # Skip empty segments
                continue

            start = float(segment["start"])
            duration = float(segment["duration"])
            end = start + duration

            # Check if we should start a new chunk
            should_split = False

            if current_start is None:
                # First non-empty segment - start new chunk
                current_start = start
                current_end = end
                current_texts = [text]
                current_segment_count = 1
            else:
                # Calculate gap from previous segment
                gap = start - (current_end or 0)

                # Calculate size if we add this segment
                combined_text = " ".join(current_texts + [text])

                # Split if:
                # 1. Gap exceeds threshold, OR
                # 2. Adding this segment would exceed max_chars
                if gap > self.gap_threshold or len(combined_text) > self.max_chars:
                    should_split = True

                if should_split:
                    # Create chunk from accumulated segments
                    chunk_text = " ".join(current_texts)

                    # When forced to split (by gap or max_chars), create the chunk
                    # even if it doesn't meet min_chars
                    chunk = self._create_chunk(
                        document=document,
                        video_pk=video_pk,
                        chunk_index=len(chunks),
                        text=chunk_text,
                        start_time=current_start,
                        end_time=current_end or current_start,
                        segment_count=current_segment_count,
                        video_title=video_title,
                        video_url=video_url,
                        youtube_video_id=youtube_video_id,
                    )
                    chunks.append(chunk)

                    # Start new chunk with current segment
                    current_start = start
                    current_end = end
                    current_texts = [text]
                    current_segment_count = 1
                else:
                    # Add segment to current chunk
                    current_texts.append(text)
                    current_end = end
                    current_segment_count += 1

        # Don't forget the last chunk
        if current_texts and current_start is not None:
            chunk_text = " ".join(current_texts)
            # Always create the final chunk
            chunk = self._create_chunk(
                document=document,
                video_pk=video_pk,
                chunk_index=len(chunks),
                text=chunk_text,
                start_time=current_start,
                end_time=current_end or current_start,
                segment_count=current_segment_count,
                video_title=video_title,
                video_url=video_url,
                youtube_video_id=youtube_video_id,
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        document: Document,
        video_pk: str,
        chunk_index: int,
        text: str,
        start_time: float,
        end_time: float,
        segment_count: int,
        video_title: str,
        video_url: str,
        youtube_video_id: str,
    ) -> Chunk:
        """Create a Chunk with proper ID format and metadata.

        Args:
            document: Parent document (for ACL fields)
            video_pk: Video primary key
            chunk_index: Zero-based index of this chunk
            text: Chunk text content
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            segment_count: Number of segments merged
            video_title: Title of source video
            video_url: URL to video page
            youtube_video_id: YouTube video ID

        Returns:
            Chunk with ACL fields copied from document
        """
        chunk_id = f"video:{video_pk}:chunk:{chunk_index}"

        metadata = {
            "start_time": start_time,
            "end_time": end_time,
            "segment_count": segment_count,
            "video_title": video_title,
            "video_url": video_url,
            "youtube_video_id": youtube_video_id,
        }

        # Use Chunk.from_document() factory to preserve ACL
        return Chunk.from_document(
            document,
            id=chunk_id,
            document_id=document.id,
            content=text,
            index=chunk_index,
            metadata=metadata,
        )
