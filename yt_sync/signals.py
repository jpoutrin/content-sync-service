"""Signal handlers for automatic transcript ingestion.

This module contains signal handlers that automatically trigger transcript
ingestion when video processing is completed.

The handler listens for Video.transcript_status changes to COMPLETED and
queues a Django-Q async task to ingest the transcript into the vector store.
"""

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_q.tasks import async_task

from yt_sync.models import Video

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def trigger_transcript_ingestion(
    sender: type[Video],
    instance: Video,
    created: bool,
    update_fields: set[str] | None,
    **kwargs,
) -> None:
    """Trigger transcript ingestion when transcript_status becomes COMPLETED.

    This signal handler is called after a Video is saved. It checks if:
    1. RAG_AUTO_INGEST setting is enabled
    2. transcript_status changed to COMPLETED
    3. Video has transcript data

    If all conditions are met, it queues a Django-Q async task to ingest
    the transcript into the vector store.

    Args:
        sender: The Video model class
        instance: The Video instance being saved
        created: True if this is a new instance
        update_fields: Set of field names that were updated (if available)
        **kwargs: Additional signal arguments

    Note:
        Uses task_id based on video ID to prevent duplicate task queueing.
        If a task with the same ID is already queued, Django-Q will not
        create a duplicate.
    """
    # Check if auto-ingestion is enabled
    if not getattr(settings, "RAG_AUTO_INGEST", True):
        return

    # Only trigger on transcript_status change to COMPLETED
    if instance.transcript_status != Video.ProcessingStatus.COMPLETED:
        return

    # Verify transcript data exists
    if not instance.transcript_data:
        logger.warning(
            f"Video {instance.id} has transcript_status=COMPLETED but no transcript_data"
        )
        return

    # If update_fields is provided, check if transcript_status was actually updated
    # This prevents re-triggering on unrelated field changes
    if update_fields is not None and "transcript_status" not in update_fields:
        return

    # Queue async task for ingestion
    # Use task_id to prevent duplicate tasks for the same video
    task_id = f"ingest_video_{instance.pk}"

    try:
        async_task(
            "rag.tasks.ingest_video_task",
            instance.pk,
            task_id=task_id,
        )
        logger.info(
            f"Queued ingestion task {task_id} for video {instance.id} "
            f"('{instance.title}')"
        )
    except Exception as e:
        logger.error(
            f"Failed to queue ingestion task for video {instance.id}: {e}",
            exc_info=True,
        )
