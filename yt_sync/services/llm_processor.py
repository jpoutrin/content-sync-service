"""
Service for scheduling LLM reprocessing tasks.
"""
from django_q.tasks import async_task
from yt_sync.models import Video


def schedule_llm_reprocessing(
    video_id: str | None = None,
    source_id: str | None = None,
    all_videos: bool = False,
) -> dict:
    """
    Schedule LLM reprocessing tasks for videos that have transcripts.

    Args:
        video_id: UUID of a specific video to reprocess.
        source_id: UUID of a source to reprocess all videos for.
        all_videos: If True, reprocess ALL videos with transcripts.

    Returns:
        dict with keys:
            - count: number of videos scheduled
            - tasks: list of dicts with task_id, video_id, and title

    Raises:
        ValueError: If no videos with transcripts are found.
    """
    # Base queryset - only videos with transcripts
    videos = Video.objects.filter(transcript_text__isnull=False).exclude(transcript_text='')

    if video_id:
        videos = videos.filter(id=video_id)
    elif source_id:
        videos = videos.filter(source_id=source_id)
    # else all_videos=True: keep the base queryset

    if not videos.exists():
        raise ValueError("No videos with transcripts found to process.")

    tasks = []
    for video in videos:
        task_id = async_task('yt_sync.tasks.reprocess_llm_task', str(video.id))
        tasks.append({
            'task_id': task_id,
            'video_id': str(video.id),
            'title': video.title,
        })

    return {
        'count': len(tasks),
        'tasks': tasks,
    }