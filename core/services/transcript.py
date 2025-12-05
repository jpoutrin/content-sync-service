from youtube_transcript_api import YouTubeTranscriptApi
import logging

logger = logging.getLogger(__name__)

class TranscriptService:
    @staticmethod
    def get_transcript(video_id):
        """
        Fetches the transcript for a given YouTube video ID.
        Returns the transcript text or None if not found.
        """
        try:
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id, languages=['en'])
            
            if not transcript_list:
                logger.warning(f"No transcript found for video {video_id}")
                return None

            # Combine into a single string
            full_text = " ".join([entry.text for entry in transcript_list])
            return full_text

        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            # Try without language specification as fallback
            try:
                api = YouTubeTranscriptApi()
                transcript_list = api.fetch(video_id)
                if transcript_list:
                    full_text = " ".join([entry.text for entry in transcript_list])
                    return full_text
            except Exception as e2:
                logger.error(f"Fallback also failed for {video_id}: {e2}")
            return None
