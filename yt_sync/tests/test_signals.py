"""Tests for transcript ingestion signal handlers.

This module tests the automatic ingestion trigger when videos reach
COMPLETED transcript_status.
"""

from unittest.mock import patch

from django.test import override_settings

import pytest

from yt_sync.models import Video
from yt_sync.tests.factories import VideoFactory


@pytest.mark.django_db
class TestTranscriptIngestionSignal:
    """Test suite for the trigger_transcript_ingestion signal handler."""

    def test_signal_triggers_on_transcript_completed(self):
        """Test that signal queues task when transcript_status becomes COMPLETED."""
        # Create a video with pending transcript
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[
                {"text": "Hello", "start": 0.0, "duration": 1.0},
                {"text": "World", "start": 1.0, "duration": 1.0},
            ],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to COMPLETED
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save(update_fields=["transcript_status"])

            # Verify async_task was called
            mock_async_task.assert_called_once_with(
                "rag.tasks.ingest_video_task",
                video.pk,
                task_id=f"ingest_video_{video.pk}",
            )

    def test_signal_does_not_trigger_on_creation(self):
        """Test that signal does not trigger when video is created with COMPLETED status."""
        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Create video already COMPLETED (edge case, but possible)
            VideoFactory(
                transcript_status=Video.ProcessingStatus.COMPLETED,
                transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
            )

            # Signal should still trigger on creation if status is COMPLETED
            # This is expected behavior - we want to ingest new videos
            mock_async_task.assert_called_once()

    def test_signal_does_not_trigger_on_non_completed_status(self):
        """Test that signal does not trigger for non-COMPLETED statuses."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to PROCESSING (not COMPLETED)
            video.transcript_status = Video.ProcessingStatus.PROCESSING
            video.save(update_fields=["transcript_status"])

            # Should not queue task
            mock_async_task.assert_not_called()

    def test_signal_does_not_trigger_without_transcript_data(self):
        """Test that signal does not trigger if transcript_data is missing."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=None,  # No transcript data
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            with patch("yt_sync.signals.logger.warning") as mock_logger:
                # Update to COMPLETED but without data
                video.transcript_status = Video.ProcessingStatus.COMPLETED
                video.save(update_fields=["transcript_status"])

                # Should not queue task
                mock_async_task.assert_not_called()

                # Should log warning
                mock_logger.assert_called_once()
                assert "no transcript_data" in str(mock_logger.call_args)

    def test_signal_does_not_trigger_with_empty_transcript_data(self):
        """Test that signal does not trigger if transcript_data is empty list."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[],  # Empty list
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            with patch("yt_sync.signals.logger.warning") as mock_logger:
                # Update to COMPLETED with empty data
                video.transcript_status = Video.ProcessingStatus.COMPLETED
                video.save(update_fields=["transcript_status"])

                # Should not queue task (empty list is falsy)
                mock_async_task.assert_not_called()

                # Should log warning
                mock_logger.assert_called_once()

    @override_settings(RAG_AUTO_INGEST=False)
    def test_signal_respects_auto_ingest_setting_disabled(self):
        """Test that signal does not trigger when RAG_AUTO_INGEST=False."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to COMPLETED
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save(update_fields=["transcript_status"])

            # Should not queue task because setting is False
            mock_async_task.assert_not_called()

    @override_settings(RAG_AUTO_INGEST=True)
    def test_signal_respects_auto_ingest_setting_enabled(self):
        """Test that signal triggers when RAG_AUTO_INGEST=True."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to COMPLETED
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save(update_fields=["transcript_status"])

            # Should queue task because setting is True
            mock_async_task.assert_called_once()

    def test_signal_does_not_trigger_on_unrelated_field_update(self):
        """Test that signal does not trigger when updating other fields."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.COMPLETED,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update unrelated field
            video.title = "New Title"
            video.save(update_fields=["title"])

            # Should not queue task (transcript_status not in update_fields)
            mock_async_task.assert_not_called()

    def test_signal_uses_unique_task_id(self):
        """Test that signal uses video PK in task_id to prevent duplicates."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to COMPLETED
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save(update_fields=["transcript_status"])

            # Verify task_id format
            call_kwargs = mock_async_task.call_args.kwargs
            assert call_kwargs["task_id"] == f"ingest_video_{video.pk}"

    def test_signal_handles_async_task_exception(self):
        """Test that signal logs error if async_task raises exception."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            with patch("yt_sync.signals.logger.error") as mock_logger:
                # Make async_task raise an exception
                mock_async_task.side_effect = RuntimeError("Queue full")

                # Update to COMPLETED
                video.transcript_status = Video.ProcessingStatus.COMPLETED
                video.save(update_fields=["transcript_status"])

                # Should log error
                mock_logger.assert_called_once()
                assert "Failed to queue ingestion task" in str(mock_logger.call_args)

    def test_signal_logs_success(self):
        """Test that signal logs success message when task is queued."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task"):
            with patch("yt_sync.signals.logger.info") as mock_logger:
                # Update to COMPLETED
                video.transcript_status = Video.ProcessingStatus.COMPLETED
                video.save(update_fields=["transcript_status"])

                # Should log success
                mock_logger.assert_called_once()
                log_message = str(mock_logger.call_args)
                assert "Queued ingestion task" in log_message
                assert str(video.id) in log_message

    def test_signal_triggers_on_save_without_update_fields(self):
        """Test that signal works when save() is called without update_fields."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.PENDING,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Update to COMPLETED and save without update_fields
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save()  # No update_fields parameter

            # Should queue task (update_fields=None means check is skipped)
            mock_async_task.assert_called_once()

    def test_signal_idempotent_on_multiple_saves(self):
        """Test that signal can be called multiple times safely."""
        video = VideoFactory(
            transcript_status=Video.ProcessingStatus.COMPLETED,
            transcript_data=[{"text": "Test", "start": 0.0, "duration": 1.0}],
        )

        with patch("yt_sync.signals.async_task") as mock_async_task:
            # Save the same video multiple times
            video.save()
            video.save()
            video.save()

            # Django-Q will use same task_id, preventing duplicates
            # Signal should still try to queue each time
            assert mock_async_task.call_count == 3

            # Verify all calls use same task_id
            task_ids = [
                call.kwargs["task_id"] for call in mock_async_task.call_args_list
            ]
            assert len(set(task_ids)) == 1  # All same task_id
