from django.core.management.base import BaseCommand
from yt_sync.models import Source
from yt_sync.tasks import fetch_source_videos_task

class Command(BaseCommand):
    help = 'Manually sync a source'

    def add_arguments(self, parser):
        parser.add_argument('source_id', type=str, help='UUID of the source to sync')

    def handle(self, *args, **options):
        source_id = options['source_id']
        try:
            source = Source.objects.get(id=source_id)
            self.stdout.write(f"Triggering sync for source: {source.title}")
            # We call it synchronously for the management command to see output, 
            # or we could just dispatch it. Let's dispatch it to test the worker integration,
            # but for debugging it's often better to call the function directly if we want to see errors immediately.
            # However, since it's a shared_task, calling it directly works but bypasses Celery broker.
            # Let's call it directly for immediate feedback in CLI.
            fetch_source_videos_task(source_id)
            self.stdout.write(self.style.SUCCESS(f"Successfully synced source: {source.title}"))
        except Source.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Source with ID {source_id} does not exist"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
