from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_channel_details(self, channel_id=None, for_username=None):
        """
        Get channel details including the uploads playlist ID.
        """
        try:
            kwargs = {'part': 'contentDetails,snippet'}
            if channel_id:
                kwargs['id'] = channel_id
            elif for_username:
                kwargs['forUsername'] = for_username
            else:
                raise ValueError("Must provide channel_id or for_username")

            response = self.youtube.channels().list(**kwargs).execute()

            if not response['items']:
                return None

            item = response['items'][0]
            return {
                'id': item['id'],
                'title': item['snippet']['title'],
                'uploads_playlist_id': item['contentDetails']['relatedPlaylists']['uploads']
            }
        except HttpError as e:
            logger.error(f"YouTube API Error: {e}")
            raise

    def get_playlist_videos(self, playlist_id, limit=10):
        """
        Get latest videos from a playlist.
        """
        try:
            # 1. Get playlist items (videos)
            playlist_response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=limit
            ).execute()

            if not playlist_response.get('items'):
                return []

            video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]
            
            # 2. Get detailed video info (needed for duration)
            videos_response = self.youtube.videos().list(
                part='contentDetails,snippet,statistics',
                id=','.join(video_ids)
            ).execute()

            videos = []
            for item in videos_response['items']:
                duration_iso = item['contentDetails']['duration']
                duration = isodate.parse_duration(duration_iso)
                
                videos.append({
                    'youtube_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url'),
                    'duration': duration,
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })
            
            return videos

        except HttpError as e:
            logger.error(f"YouTube API Error: {e}")
            raise
