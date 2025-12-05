import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

class Source(models.Model):
    class SourceType(models.TextChoices):
        CHANNEL = 'CHANNEL', _('Channel')
        PLAYLIST = 'PLAYLIST', _('Playlist')

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        ERROR = 'ERROR', _('Error')
        PAUSED = 'PAUSED', _('Paused')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(help_text="Supabase Auth User ID")
    type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.CHANNEL)
    youtube_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    url = models.URLField()
    sync_frequency = models.CharField(max_length=20, default='daily')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'youtube_id')
        indexes = [
            models.Index(fields=['user_id', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.type})"

class Video(models.Model):
    class ProcessingStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='videos')
    youtube_video_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    duration = models.DurationField(null=True, blank=True)
    published_at = models.DateTimeField()
    
    transcript_text = models.TextField(blank=True, null=True)
    transcript_status = models.CharField(
        max_length=20, 
        choices=ProcessingStatus.choices, 
        default=ProcessingStatus.PENDING
    )
    ai_analysis_status = models.CharField(
        max_length=20, 
        choices=ProcessingStatus.choices, 
        default=ProcessingStatus.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['source', '-published_at']),
        ]

    def __str__(self):
        return self.title

class ProcessedContent(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='processed_content')
    summary = models.TextField()
    tags = models.JSONField(default=list)
    categories = models.JSONField(default=list)
    main_ideas = models.JSONField(default=list)
    key_moments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.video.title}"
