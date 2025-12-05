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
            # Use instance method as seen in library source
            api = YouTubeTranscriptApi()
            # fetch() returns a FetchedTranscript object which is iterable
            transcript_list = api.fetch(video_id, languages=['en'])
            
            if not transcript_list:
                logger.warning(f"No transcript found for video {video_id}")
                return None

            # Convert to list of dicts
            transcript_data = []
            full_text_parts = []
            
            for entry in transcript_list:
                # Handle both object attributes and dict access just to be safe
                if hasattr(entry, 'text'):
                    text = entry.text
                    start = entry.start
                    duration = entry.duration
                elif isinstance(entry, dict):
                    text = entry.get('text', '')
                    start = entry.get('start', 0)
                    duration = entry.get('duration', 0)
                else:
                    # Fallback or skip
                    continue
                
                transcript_data.append({
                    'text': text,
                    'start': start,
                    'duration': duration
                })
                full_text_parts.append(text)

            full_text = " ".join(full_text_parts)
            
            return {
                'text': full_text,
                'data': transcript_data
            }

        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            
            # Fallback: try listing all and picking first
            try:
                api = YouTubeTranscriptApi()
                # Use .list() instance method
                transcript_list_obj = api.list(video_id)
                # Just take the first available transcript
                for transcript in transcript_list_obj:
                    fetched_data = transcript.fetch()
                    
                    transcript_data = []
                    full_text_parts = []
                    for entry in fetched_data:
                        if hasattr(entry, 'text'):
                            text = entry.text
                            start = entry.start
                            duration = entry.duration
                        elif isinstance(entry, dict):
                            text = entry.get('text', '')
                            start = entry.get('start', 0)
                            duration = entry.get('duration', 0)
                        else:
                            continue
                            
                        transcript_data.append({
                            'text': text,
                            'start': start,
                            'duration': duration
                        })
                        full_text_parts.append(text)
                    
                    full_text = " ".join(full_text_parts)
                    return {
                        'text': full_text,
                        'data': transcript_data
                    }
            except Exception as e2:
                logger.error(f"Fallback also failed for {video_id}: {e2}")
            return None
