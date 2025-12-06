from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from yt_sync.models import Source
from yt_sync.services.youtube import YouTubeService
import uuid
import re
from urllib.parse import urlparse, parse_qs

User = get_user_model()

class Command(BaseCommand):
    help = 'Add a new YouTube source (auto-detects channel or playlist from URL)'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='YouTube channel or playlist URL')
        parser.add_argument('username', type=str, help='Django username to assign this source to')

    def handle(self, *args, **options):
        url = options['url']
        username = options['username']

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"🔍 Analyzing YouTube URL")
        self.stdout.write(f"{'='*60}\n")
        
        # Get the user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"👤 User: {user.username} (ID: {user.id})\n")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User not found: {username}"))
            self.stdout.write("   Available users:")
            for u in User.objects.all()[:5]:
                self.stdout.write(f"   - {u.username}")
            return
        
        # Parse the URL to determine type
        source_type, identifier = self.parse_youtube_url(url)
        
        if not source_type:
            self.stdout.write(self.style.ERROR("❌ Could not parse YouTube URL"))
            self.stdout.write(self.style.WARNING("   Supported formats:"))
            self.stdout.write("   - Playlist: https://www.youtube.com/playlist?list=PLxxx")
            self.stdout.write("   - Channel: https://www.youtube.com/@channelname")
            self.stdout.write("   - Channel: https://www.youtube.com/channel/UCxxx")
            self.stdout.write("   - Channel: https://www.youtube.com/c/channelname")
            return

        self.stdout.write(f"📝 Detected: {source_type}")
        self.stdout.write(f"   Identifier: {identifier}\n")

        service = YouTubeService()
        
        try:
            if source_type == 'PLAYLIST':
                # For playlists, we can get details directly
                # TODO: Add playlist details fetching to YouTubeService
                source, created = Source.objects.get_or_create(
                    user=user,
                    youtube_id=identifier,
                    defaults={
                        'title': f"Playlist {identifier}",
                        'type': Source.SourceType.PLAYLIST,
                        'url': url,
                        'status': Source.Status.ACTIVE
                    }
                )
            else:  # CHANNEL
                # Try to get channel details
                details = None
                
                # If it's a channel ID (starts with UC)
                if identifier.startswith('UC'):
                    details = service.get_channel_details(channel_id=identifier)
                # If it's a username/handle
                else:
                    self.stdout.write(f"   Trying handle lookup for: @{identifier}")
                    # Try as handle first (most common nowadays)
                    details = service.get_channel_details(for_handle=identifier)
                    
                    if not details:
                        self.stdout.write(f"   ⚠️ Handle lookup failed, trying legacy username: {identifier}")
                        # Fallback to legacy username
                        details = service.get_channel_details(for_username=identifier)
                    
                    # If that fails, it might be a custom URL - we need the channel ID
                    if not details:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️  Could not find channel with handle/username '{identifier}'"
                        ))
                        self.stdout.write("   Please provide the channel ID (starts with UC) instead")
                        self.stdout.write("   You can find it in the channel's 'About' page URL")
                        return
                
                if not details:
                    self.stdout.write(self.style.ERROR(f"❌ Channel not found: {identifier}"))
                    return

                source, created = Source.objects.get_or_create(
                    user=user,
                    youtube_id=details['id'],
                    defaults={
                        'title': details['title'],
                        'type': Source.SourceType.CHANNEL,
                        'url': f"https://www.youtube.com/channel/{details['id']}",
                        'status': Source.Status.ACTIVE
                    }
                )

            if created:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Created source: {source.title}"))
                self.stdout.write(f"   ID: {source.id}")
                self.stdout.write(f"   Type: {source.type}")
                self.stdout.write(f"   URL: {source.url}")
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Source already exists: {source.title}"))
                self.stdout.write(f"   ID: {source.id}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error adding source: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())

    def parse_youtube_url(self, url):
        """
        Parse YouTube URL and return (source_type, identifier)
        
        Supported formats:
        - Playlist: https://www.youtube.com/playlist?list=PLxxx
        - Channel (@handle): https://www.youtube.com/@channelname
        - Channel (ID): https://www.youtube.com/channel/UCxxx
        - Channel (custom): https://www.youtube.com/c/channelname
        """
        try:
            parsed = urlparse(url)
            
            # Check for playlist
            if 'playlist' in parsed.path:
                query_params = parse_qs(parsed.query)
                if 'list' in query_params:
                    playlist_id = query_params['list'][0]
                    return ('PLAYLIST', playlist_id)
            
            # Check for channel with @ handle
            if '/@' in parsed.path:
                handle = parsed.path.split('/@')[1].split('/')[0]
                return ('CHANNEL', handle)
            
            # Check for channel with /channel/
            if '/channel/' in parsed.path:
                channel_id = parsed.path.split('/channel/')[1].split('/')[0]
                return ('CHANNEL', channel_id)
            
            # Check for channel with /c/
            if '/c/' in parsed.path:
                custom_name = parsed.path.split('/c/')[1].split('/')[0]
                return ('CHANNEL', custom_name)
            
            # Check for channel with /user/
            if '/user/' in parsed.path:
                username = parsed.path.split('/user/')[1].split('/')[0]
                return ('CHANNEL', username)
            
            return (None, None)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error parsing URL: {e}"))
            return (None, None)
