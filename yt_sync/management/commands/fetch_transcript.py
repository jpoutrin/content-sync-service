from django.core.management.base import BaseCommand
from yt_sync.models import Video, Source
from yt_sync.services.transcript import TranscriptService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch transcripts from YouTube for videos (without LLM processing)'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--video-id', type=str, help='UUID of a specific video')
        group.add_argument('--source-id', type=str, help='UUID of a source to fetch transcripts for')
        group.add_argument('--pending', action='store_true', help='Fetch all videos with pending transcript status')
        group.add_argument('--failed', action='store_true', help='Retry all videos with failed transcript status')

    def handle(self, *args, **options):
        videos = Video.objects.none()

        if options['video_id']:
            videos = Video.objects.filter(id=options['video_id'])
        elif options['source_id']:
            videos = Video.objects.filter(source_id=options['source_id'])
        elif options['pending']:
            videos = Video.objects.filter(transcript_status=Video.ProcessingStatus.PENDING)
        elif options['failed']:
            videos = Video.objects.filter(transcript_status=Video.ProcessingStatus.FAILED)

        if not videos.exists():
            self.stdout.write(self.style.WARNING("No videos found to process."))
            return

        count = videos.count()
        self.stdout.write(f"Fetching transcripts for {count} videos...")

        transcript_service = TranscriptService()
        success_count = 0
        fail_count = 0

        for video in videos:
            self.stdout.write(f"  Processing: {video.title}")
            video.transcript_status = Video.ProcessingStatus.PROCESSING
            video.save()

            try:
                transcript_result = transcript_service.get_transcript(video.youtube_video_id)

                if transcript_result:
                    video.transcript_text = transcript_result['text']
                    video.transcript_data = transcript_result['data']
                    video.transcript_status = Video.ProcessingStatus.COMPLETED
                    video.processing_error = None
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"    OK: {video.title}"))
                else:
                    video.transcript_status = Video.ProcessingStatus.FAILED
                    video.processing_error = "No transcript available"
                    fail_count += 1
                    self.stdout.write(self.style.WARNING(f"    No transcript: {video.title}"))

            except Exception as e:
                video.transcript_status = Video.ProcessingStatus.FAILED
                video.processing_error = f"Transcript fetch error: {str(e)}"
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"    Error: {video.title} - {e}"))

            video.save()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Completed: {success_count} succeeded, {fail_count} failed"))
