from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Source, Video, ProcessedContent, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'user', 'status', 'last_sync_at', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('title', 'youtube_id', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'transcript_status', 'ai_analysis_status', 'published_at')
    list_filter = ('transcript_status', 'ai_analysis_status', 'published_at')
    search_fields = ('title', 'youtube_video_id')
    readonly_fields = ('id', 'created_at')

@admin.register(ProcessedContent)
class ProcessedContentAdmin(admin.ModelAdmin):
    list_display = ('video', 'created_at', 'updated_at')
    search_fields = ('video__title', 'summary')
    readonly_fields = ('created_at', 'updated_at')
