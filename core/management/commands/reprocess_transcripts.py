from django.core.management.base import BaseCommand
from core.models import Video, Source
from core.tasks import process_video_pipeline_task

class Command(BaseCommand):
    help = 'Reprocess transcripts and run full pipeline for videos'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--video-id', type=str, help='UUID of a specific video')
        group.add_argument('--source-id', type=str, help='UUID of a source to reprocess all videos for')
        group.add_argument('--all', action='store_true', help='Reprocess ALL videos')

    def handle(self, *args, **options):
        videos = Video.objects.none()

        if options['video_id']:
            try:
                videos = Video.objects.filter(id=options['video_id'])
            except Exception:
                pass # Will check count below
        elif options['source_id']:
            videos = Video.objects.filter(source_id=options['source_id'])
        elif options['all']:
            videos = Video.objects.all()

        if not videos.exists():
            self.stdout.write(self.style.WARNING("No videos found to process."))
            return

        count = videos.count()
        self.stdout.write(f"Scheduling reprocessing for {count} videos...")

        for video in videos:
            task = process_video_pipeline_task.delay(str(video.id))
            self.stdout.write(f" - Dispatched task {task.id} for: {video.title} ({video.id})")

        self.stdout.write(self.style.SUCCESS(f"Successfully scheduled {count} tasks."))
