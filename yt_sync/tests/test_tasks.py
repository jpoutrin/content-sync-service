"""
Tests for yt_sync tasks.

These tests verify the functionality of the task functions,
particularly the reprocess_llm_task and related components.
"""
import uuid
from unittest.mock import patch, MagicMock

import pytest
from django_q.tasks import async_task

from yt_sync.models import ProcessedContent, Video
from yt_sync.tasks import reprocess_llm_task

from .factories import (
    ProcessedContentFactory,
    SourceFactory,
    VideoFactory,
)


class TestReprocessLlmTask:
    """Tests for the reprocess_llm_task function."""

    @pytest.mark.django_db
    @patch('yt_sync.tasks.LLMService')
    def test_reprocess_llm_task_success(self, mock_llm_service_class):
        """Test successful LLM reprocessing with transcript."""
        # Setup
        video = VideoFactory(
            transcript_text="This is a test transcript for the video.",
            ai_analysis_status=Video.ProcessingStatus.COMPLETED,
        )
        mock_llm_service = MagicMock()
        mock_llm_service.generate_summary.return_value = {
            'summary': 'Test summary',
            'tags': ['test', 'video'],
            'categories': ['Technology'],
            'main_ideas': ['Idea 1'],
            'key_moments': [],
        }
        mock_llm_service_class.return_value = mock_llm_service

        # Execute
        reprocess_llm_task(str(video.id))

        # Assert
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.COMPLETED
        assert ProcessedContent.objects.filter(video=video).exists()
        content = ProcessedContent.objects.get(video=video)
        assert content.summary == 'Test summary'
        assert content.tags == ['test', 'video']

    @pytest.mark.django_db
    def test_reprocess_llm_task_no_transcript(self):
        """Test that LLM is not called when video has no transcript."""
        # Setup
        video = VideoFactory(
            transcript_text=None,
            ai_analysis_status=Video.ProcessingStatus.PENDING,
        )

        # Execute
        with patch('yt_sync.tasks.generate_summary_task') as mock_generate:
            reprocess_llm_task(str(video.id))
            mock_generate.assert_not_called()

        # Assert status unchanged
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.PENDING

    @pytest.mark.django_db
    def test_reprocess_llm_task_empty_transcript(self):
        """Test that LLM is not called when transcript is empty string."""
        # Setup
        video = VideoFactory(
            transcript_text="",
            ai_analysis_status=Video.ProcessingStatus.PENDING,
        )

        # Execute
        with patch('yt_sync.tasks.generate_summary_task') as mock_generate:
            reprocess_llm_task(str(video.id))
            mock_generate.assert_not_called()

        # Assert status unchanged
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.PENDING

    @pytest.mark.django_db
    def test_reprocess_llm_task_video_not_found(self):
        """Test handling of non-existent video ID."""
        # Execute - should not raise exception
        non_existent_id = str(uuid.uuid4())
        reprocess_llm_task(non_existent_id)
        # No assertion needed - just verify no exception raised

    @pytest.mark.django_db
    @patch('yt_sync.tasks.LLMService')
    def test_reprocess_llm_task_llm_failure(self, mock_llm_service_class):
        """Test handling when LLM returns None."""
        # Setup
        video = VideoFactory(
            transcript_text="Valid transcript text.",
            ai_analysis_status=Video.ProcessingStatus.PENDING,
        )
        mock_llm_service = MagicMock()
        mock_llm_service.generate_summary.return_value = None
        mock_llm_service_class.return_value = mock_llm_service

        # Execute
        reprocess_llm_task(str(video.id))

        # Assert
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.FAILED
        assert not ProcessedContent.objects.filter(video=video).exists()

    @pytest.mark.django_db
    @patch('yt_sync.tasks.LLMService')
    def test_reprocess_llm_task_resets_status(self, mock_llm_service_class):
        """Test that ai_analysis_status is reset to PENDING before processing."""
        # Setup
        video = VideoFactory(
            transcript_text="Transcript content.",
            ai_analysis_status=Video.ProcessingStatus.COMPLETED,  # Already completed
        )
        mock_llm_service = MagicMock()
        mock_llm_service.generate_summary.return_value = {
            'summary': 'New summary',
            'tags': [],
            'categories': [],
            'main_ideas': [],
            'key_moments': [],
        }
        mock_llm_service_class.return_value = mock_llm_service

        # Execute
        reprocess_llm_task(str(video.id))

        # Assert - status should be COMPLETED after successful reprocessing
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.COMPLETED

    @pytest.mark.django_db
    @patch('yt_sync.tasks.LLMService')
    def test_reprocess_llm_task_overwrites_existing_content(self, mock_llm_service_class):
        """Test that existing ProcessedContent is updated."""
        # Setup
        video = VideoFactory(
            transcript_text="Original transcript.",
            ai_analysis_status=Video.ProcessingStatus.COMPLETED,
        )
        existing_content = ProcessedContentFactory(
            video=video,
            summary="Old summary",
            tags=["old", "tags"],
        )
        
        mock_llm_service = MagicMock()
        mock_llm_service.generate_summary.return_value = {
            'summary': 'New updated summary',
            'tags': ['new', 'updated', 'tags'],
            'categories': ['New Category'],
            'main_ideas': ['New idea'],
            'key_moments': [],
        }
        mock_llm_service_class.return_value = mock_llm_service

        # Execute
        reprocess_llm_task(str(video.id))

        # Assert
        video.refresh_from_db()
        assert video.ai_analysis_status == Video.ProcessingStatus.COMPLETED
        
        # Should still be only one ProcessedContent, but updated
        assert ProcessedContent.objects.filter(video=video).count() == 1
        content = ProcessedContent.objects.get(video=video)
        assert content.summary == 'New updated summary'
        assert content.tags == ['new', 'updated', 'tags']


class TestScheduleLlmReprocessing:
    """Tests for the schedule_llm_reprocessing service function."""

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_schedule_by_video_id(self, mock_async_task):
        """Test scheduling by specific video ID."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup
        video = VideoFactory(transcript_text="Transcript content.")
        mock_async_task.return_value = "task-123"

        # Execute
        result = schedule_llm_reprocessing(video_id=str(video.id))

        # Assert
        assert result['count'] == 1
        assert len(result['tasks']) == 1
        assert result['tasks'][0]['task_id'] == "task-123"
        assert result['tasks'][0]['video_id'] == str(video.id)
        mock_async_task.assert_called_once_with(
            'yt_sync.tasks.reprocess_llm_task',
            str(video.id)
        )

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_schedule_by_source_id(self, mock_async_task):
        """Test scheduling by source ID."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup
        source = SourceFactory()
        videos = [
            VideoFactory(source=source, transcript_text=f"Content {i}")
            for i in range(3)
        ]
        mock_async_task.return_value = "task-id"

        # Execute
        result = schedule_llm_reprocessing(source_id=str(source.id))

        # Assert
        assert result['count'] == 3
        assert len(result['tasks']) == 3
        assert mock_async_task.call_count == 3

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_schedule_all_videos(self, mock_async_task):
        """Test scheduling all videos with transcripts."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup
        videos = [
            VideoFactory(transcript_text=f"Transcript {i}.")
            for i in range(3)
        ]
        mock_async_task.return_value = "task-id"

        # Execute
        result = schedule_llm_reprocessing(all_videos=True)

        # Assert
        assert result['count'] == 3
        video_ids = {str(v.id) for v in videos}
        called_ids = {call[0][1] for call in mock_async_task.call_args_list}
        assert video_ids == called_ids

    @pytest.mark.django_db
    def test_schedule_no_videos_found_raises_value_error(self):
        """Test that ValueError is raised when no videos with transcripts found."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup - videos without transcripts
        VideoFactory(transcript_text=None)
        VideoFactory(transcript_text="")

        # Execute & Assert
        with pytest.raises(ValueError, match="No videos with transcripts found"):
            schedule_llm_reprocessing(all_videos=True)

    @pytest.mark.django_db
    def test_schedule_invalid_video_id_raises_value_error(self):
        """Test that ValueError is raised for non-existent video ID."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Execute & Assert
        with pytest.raises(ValueError, match="No videos with transcripts found"):
            schedule_llm_reprocessing(video_id=str(uuid.uuid4()))

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_schedule_skips_videos_without_transcript(self, mock_async_task):
        """Test that videos without transcripts are excluded."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup
        video_with_transcript = VideoFactory(transcript_text="Has transcript.")
        VideoFactory(transcript_text=None)
        VideoFactory(transcript_text="")

        # Execute
        result = schedule_llm_reprocessing(all_videos=True)

        # Assert - only one task dispatched
        assert result['count'] == 1
        mock_async_task.assert_called_once_with(
            'yt_sync.tasks.reprocess_llm_task',
            str(video_with_transcript.id)
        )

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_schedule_returns_task_details(self, mock_async_task):
        """Test that result includes task_id, video_id, and title."""
        from yt_sync.services.llm_processor import schedule_llm_reprocessing
        
        # Setup
        video = VideoFactory(title="Test Video Title", transcript_text="Content.")
        mock_async_task.return_value = "task-abc"

        # Execute
        result = schedule_llm_reprocessing(video_id=str(video.id))

        # Assert
        task = result['tasks'][0]
        assert task['task_id'] == "task-abc"
        assert task['video_id'] == str(video.id)
        assert task['title'] == "Test Video Title"


class TestReprocessLlmCommand:
    """Tests for the reprocess_llm management command."""

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_dispatches_task_for_video_id(self, mock_async_task):
        """Test that command dispatches task for a specific video ID."""
        from django.core.management import call_command
        
        # Setup
        video = VideoFactory(transcript_text="Transcript content.")
        mock_async_task.return_value = "task-123"

        # Execute
        call_command('reprocess_llm', video_id=str(video.id))

        # Assert
        mock_async_task.assert_called_once_with(
            'yt_sync.tasks.reprocess_llm_task',
            str(video.id)
        )

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_skips_videos_without_transcript(self, mock_async_task):
        """Test that videos without transcripts are skipped."""
        from django.core.management import call_command
        
        # Setup
        video_with_transcript = VideoFactory(transcript_text="Has transcript.")
        VideoFactory(transcript_text=None)
        VideoFactory(transcript_text="")

        # Execute
        call_command('reprocess_llm', all=True)

        # Assert - only one task dispatched for video with transcript
        assert mock_async_task.call_count == 1
        mock_async_task.assert_called_with(
            'yt_sync.tasks.reprocess_llm_task',
            str(video_with_transcript.id)
        )

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_all_flag(self, mock_async_task):
        """Test --all flag dispatches tasks for all videos with transcripts."""
        from django.core.management import call_command
        
        # Setup
        videos = [
            VideoFactory(transcript_text=f"Transcript {i}.")
            for i in range(3)
        ]
        mock_async_task.return_value = "task-id"

        # Execute
        call_command('reprocess_llm', all=True)

        # Assert
        assert mock_async_task.call_count == 3
        video_ids = {str(v.id) for v in videos}
        called_ids = {call[0][1] for call in mock_async_task.call_args_list}
        assert video_ids == called_ids

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_source_id_flag(self, mock_async_task):
        """Test --source-id flag dispatches tasks only for that source's videos."""
        from django.core.management import call_command
        
        # Setup
        source1 = SourceFactory()
        source2 = SourceFactory()
        
        source1_videos = [
            VideoFactory(source=source1, transcript_text=f"Content {i}")
            for i in range(2)
        ]
        VideoFactory(source=source2, transcript_text="Other")

        # Execute
        call_command('reprocess_llm', source_id=str(source1.id))

        # Assert - only source1 videos processed
        assert mock_async_task.call_count == 2
        called_video_ids = {call[0][1] for call in mock_async_task.call_args_list}
        expected_ids = {str(v.id) for v in source1_videos}
        assert called_video_ids == expected_ids

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_no_videos_found(self, mock_async_task):
        """Test warning message when no videos with transcripts found."""
        from django.core.management import call_command
        from io import StringIO
        
        # Setup - videos without transcripts
        VideoFactory(transcript_text=None)
        VideoFactory(transcript_text="")
        
        stdout = StringIO()

        # Execute
        call_command('reprocess_llm', all=True, stdout=stdout)

        # Assert
        mock_async_task.assert_not_called()
        output = stdout.getvalue()
        assert "No videos with transcripts found" in output

    @pytest.mark.django_db
    @patch('yt_sync.services.llm_processor.async_task')
    def test_command_invalid_video_id(self, mock_async_task):
        """Test handling of invalid video ID."""
        from django.core.management import call_command
        from io import StringIO
        
        stdout = StringIO()

        # Execute with non-existent UUID
        call_command('reprocess_llm', video_id=str(uuid.uuid4()), stdout=stdout)

        # Assert
        mock_async_task.assert_not_called()
        output = stdout.getvalue()
        assert "No videos with transcripts found" in output
