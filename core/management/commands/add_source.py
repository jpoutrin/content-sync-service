from django.core.management.base import BaseCommand
from core.models import Source
from core.services.youtube import YouTubeService
import uuid

class Command(BaseCommand):
    help = 'Add a new YouTube source'

    def add_arguments(self, parser):
        parser.add_argument('identifier', type=str, help='Channel ID or Username')
        parser.add_argument('user_id', type=str, help='User UUID to assign this source to')
        parser.add_argument('--type', type=str, default='CHANNEL', choices=['CHANNEL', 'PLAYLIST'], help='Source type')

    def handle(self, *args, **options):
        identifier = options['identifier']
        user_id = options['user_id']
        source_type = options['type']

        service = YouTubeService()
        
        try:
            if source_type == 'CHANNEL':
                # Check if it's a channel ID (starts with UC) or username
                if identifier.startswith('UC'):
                    details = service.get_channel_details(channel_id=identifier)
                else:
                    details = service.get_channel_details(for_username=identifier)
                
                if not details:
                    self.stdout.write(self.style.ERROR(f"Channel not found: {identifier}"))
                    return

                source, created = Source.objects.get_or_create(
                    user_id=user_id,
                    youtube_id=details['id'],
                    defaults={
                        'title': details['title'],
                        'type': Source.SourceType.CHANNEL,
                        'url': f"https://www.youtube.com/channel/{details['id']}",
                        'status': Source.Status.ACTIVE
                    }
                )
            else:
                # Playlist logic (simplified, assuming identifier is playlist ID)
                # We should ideally fetch playlist details to get the title
                # For now, just create it
                source, created = Source.objects.get_or_create(
                    user_id=user_id,
                    youtube_id=identifier,
                    defaults={
                        'title': f"Playlist {identifier}", # TODO: Fetch actual title
                        'type': Source.SourceType.PLAYLIST,
                        'url': f"https://www.youtube.com/playlist?list={identifier}",
                        'status': Source.Status.ACTIVE
                    }
                )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created source: {source.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Source already exists: {source.title}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error adding source: {str(e)}"))
