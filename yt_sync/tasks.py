from django_q.tasks import async_task
from django.utils import timezone
from .models import Source, Video, ProcessedContent
from .services.youtube import YouTubeService
from .services.transcript import TranscriptService
from .services.llm import LLMService
import logging

logger = logging.getLogger(__name__)

def sync_sources_task():
    """
    Periodic task to iterate through active sources and dispatch fetch tasks.
    """
    active_sources = Source.objects.filter(status=Source.Status.ACTIVE)
    for source in active_sources:
        async_task('yt_sync.tasks.fetch_source_videos_task', str(source.id))

def fetch_source_videos_task(source_id):
    """
    Fetches latest videos from YouTube for a given source.
    """
    try:
        source = Source.objects.get(id=source_id)
        logger.info(f"Fetching videos for source: {source.title}")
        
        youtube_service = YouTubeService()
        
        playlist_id = None
        if source.type == Source.SourceType.CHANNEL:
            details = youtube_service.get_channel_details(channel_id=source.youtube_id)
            if details:
                playlist_id = details['uploads_playlist_id']
        else:
            playlist_id = source.youtube_id
            
        if not playlist_id:
            logger.error(f"Could not determine playlist ID for source {source.id}")
            return

        videos = youtube_service.get_playlist_videos(playlist_id)
        
        new_videos_count = 0
        for video_data in videos:
            video, created = Video.objects.get_or_create(
                youtube_video_id=video_data['youtube_id'],
                defaults={
                    'source': source,
                    'title': video_data['title'],
                    'url': video_data['url'],
                    'duration': video_data['duration'],
                    'published_at': video_data['published_at'],
                    'transcript_status': Video.ProcessingStatus.PENDING,
                    'ai_analysis_status': Video.ProcessingStatus.PENDING
                }
            )
            
            if created:
                new_videos_count += 1
                logger.info(f"Found new video: {video.title}")
                async_task('yt_sync.tasks.process_video_pipeline_task', str(video.id))
        
        source.last_sync_at = timezone.now()
        source.save()
        
        logger.info(f"Sync complete for {source.title}. Added {new_videos_count} new videos.")
        
    except Source.DoesNotExist:
        logger.error(f"Source {source_id} not found")
    except Exception as e:
        logger.error(f"Error syncing source {source_id}: {str(e)}")

def process_video_pipeline_task(video_id):
    """
    Orchestrates the processing pipeline for a video.
    Runs the full pipeline synchronously within a single task.
    """
    logger.info(f"Starting processing pipeline for video {video_id}")

    # Step 1: Extract transcript
    transcript_result = extract_transcript_task(video_id)
    if not transcript_result:
        logger.error(f"Pipeline failed at transcript extraction for video {video_id}")
        return

    # Step 2: Generate summary
    summary_result = generate_summary_task(transcript_result)
    if not summary_result:
        logger.error(f"Pipeline failed at summary generation for video {video_id}")
        return

    # Step 3: Save results
    save_results_task(summary_result, video_id)
    logger.info(f"Pipeline completed for video {video_id}")

def extract_transcript_task(video_id):
    """
    Extracts transcript from a YouTube video.
    Returns: dict with video_id and transcript_text
    """
    try:
        video = Video.objects.get(id=video_id)
        video.transcript_status = Video.ProcessingStatus.PROCESSING
        video.save()
        
        logger.info(f"Extracting transcript for video: {video.title}")
        
        transcript_service = TranscriptService()
        transcript_result = transcript_service.get_transcript(video.youtube_video_id)
        
        if transcript_result:
            video.transcript_text = transcript_result['text']
            video.transcript_data = transcript_result['data']
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            logger.info(f"Successfully extracted transcript for {video.title}")
        else:
            video.transcript_status = Video.ProcessingStatus.FAILED
            logger.warning(f"No transcript available for {video.title}")
        
        video.save()
        
        return {
            'video_id': str(video_id),
            'transcript_text': transcript_result['text'] if transcript_result else None
        }
        
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error extracting transcript for {video_id}: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.transcript_status = Video.ProcessingStatus.FAILED
            video.processing_error = f"Transcript Extraction: {str(e)}"
            video.save()
        except:
            pass
        return None

def generate_summary_task(transcript_result):
    """
    Generates AI summary from transcript.
    Returns: dict with video_id, transcript_text, and summary_data
    """
    if not transcript_result or not transcript_result.get('transcript_text'):
        logger.warning("No transcript data to process")
        # We need to know WHICH video failed if possible, but transcript_data might be None
        # However, save_results_task will handle the missing result.
        # Ideally, we pass video_id even on failure, but chained tasks make this tricky if previous returned None.
        return None
    
    video_id = transcript_result['video_id']
    transcript_text = transcript_result['transcript_text']
    
    try:
        video = Video.objects.get(id=video_id)
        video.ai_analysis_status = Video.ProcessingStatus.PROCESSING
        video.save()
        
        logger.info(f"Generating AI summary for video: {video.title}")
        
        llm_service = LLMService()
        summary_data = llm_service.generate_summary(transcript_text)
        
        if summary_data:
            video.ai_analysis_status = Video.ProcessingStatus.COMPLETED
            logger.info(f"Successfully generated summary for {video.title}")
        else:
            video.ai_analysis_status = Video.ProcessingStatus.FAILED
            logger.warning(f"Failed to generate summary for {video.title}")
        
        video.save()
        
        return {
            'video_id': video_id,
            'summary_data': summary_data
        }
        
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error generating summary for {video_id}: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.ai_analysis_status = Video.ProcessingStatus.FAILED
            video.processing_error = f"AI Summary: {str(e)}"
            video.save()
        except:
            pass
        return None

def save_results_task(summary_result, video_id):
    """
    Saves the processed results to the database.
    """
    if not summary_result or not summary_result.get('summary_data'):
        logger.warning(f"No summary data to save for video {video_id}")
        try:
            video = Video.objects.get(id=video_id)
            if video.ai_analysis_status != Video.ProcessingStatus.FAILED:
                # If status isn't FAILED, but we have no data, something happened in between
                video.processing_error = "Save Results: No summary data received from previous step."
                video.ai_analysis_status = Video.ProcessingStatus.FAILED
                video.save()
        except:
            pass
        return
    
    try:
        video = Video.objects.get(id=video_id)
        summary_data = summary_result['summary_data']
        
        # Create or update ProcessedContent
        ProcessedContent.objects.update_or_create(
            video=video,
            defaults={
                'summary': summary_data.get('summary', ''),
                'tags': summary_data.get('tags', []),
                'categories': summary_data.get('categories', []),
                'main_ideas': summary_data.get('main_ideas', []),
                'key_moments': summary_data.get('key_moments', [])
            }
        )
        
        logger.info(f"Successfully saved processed content for {video.title}")
        
    except Video.DoesNotExist:
        logger.error(f"Video {video_id} not found")
    except Exception as e:
        logger.error(f"Error saving results for {video_id}: {str(e)}")
        try:
            video = Video.objects.get(id=video_id)
            video.processing_error = f"Save Results: {str(e)}"
            video.save()
        except:
            pass
