from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from yt_sync.models import Video

User = get_user_model()

class Command(BaseCommand):
    help = 'List videos for a specific username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument('--limit', type=int, default=20, help='Limit number of videos shown (default: 20)')

    def handle(self, *args, **options):
        username = options['username']
        limit = options['limit']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' does not exist"))
            return

        videos = Video.objects.filter(source__user=user).select_related('source').order_by('-published_at')
        total_count = videos.count()
        
        display_videos = videos[:limit]

        self.stdout.write(f"Found {total_count} videos for user '{username}'\n")
        
        if total_count == 0:
            return

        # Header
        self.stdout.write(f"{'ID':<36} | {'T. Status':<10} | {'AI Status':<10} | {'Source ID':<36} | {'Source':<20} | {'Title'}")
        self.stdout.write("-" * 160)

        for video in display_videos:
            t_status = video.transcript_status
            ai_status = video.ai_analysis_status
            
            # Truncate title if too long
            title = video.title
            if len(title) > 40:
                title = title[:37] + "..."
            
            # Truncate source if too long
            source_title = video.source.title
            if len(source_title) > 20:
                source_title = source_title[:17] + "..."
            
            line = f"{str(video.id):<36} | {t_status:<10} | {ai_status:<10} | {str(video.source.id):<36} | {source_title:<20} | {title}"
            self.stdout.write(line)

            if video.processing_error:
                self.stdout.write(self.style.ERROR(f"    └── Error: {video.processing_error}"))

        if total_count > limit:
            self.stdout.write(f"\n... and {total_count - limit} more videos (use --limit to see more)")
