from django.core.management.base import BaseCommand
from yt_sync.services.llm_processor import schedule_llm_reprocessing


class Command(BaseCommand):
    help = 'Reprocess LLM/AI analysis for videos that already have transcripts (skips transcript fetching)'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--video-id', type=str, help='UUID of a specific video')
        group.add_argument('--source-id', type=str, help='UUID of a source to reprocess all videos for')
        group.add_argument('--all', action='store_true', help='Reprocess ALL videos with transcripts')

    def handle(self, *args, **options):
        try:
            result = schedule_llm_reprocessing(
                video_id=options.get('video_id'),
                source_id=options.get('source_id'),
                all_videos=options.get('all', False),
            )
        except ValueError as e:
            self.stdout.write(self.style.WARNING(str(e)))
            return

        self.stdout.write(f"Scheduling LLM reprocessing for {result['count']} videos...")
        for task in result['tasks']:
            self.stdout.write(f" - Dispatched task {task['task_id']} for: {task['title']} ({task['video_id']})")

        self.stdout.write(self.style.SUCCESS(f"Successfully scheduled {result['count']} LLM reprocessing tasks."))
