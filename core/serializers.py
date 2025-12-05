from rest_framework import serializers
from .models import Source, Video, ProcessedContent

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_sync_at')

class ProcessedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedContent
        fields = ['summary', 'tags', 'categories', 'main_ideas', 'key_moments', 'created_at', 'updated_at']

class VideoSerializer(serializers.ModelSerializer):
    processed_content = ProcessedContentSerializer(read_only=True)
    
    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'published_at', 'duration')
