from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Source, Video
from .serializers import SourceSerializer, VideoSerializer

class SourceViewSet(viewsets.ModelViewSet):
    serializer_class = SourceSerializer

    def get_queryset(self):
        # Filter sources by the authenticated user
        return Source.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the user from the authenticated user
        serializer.save(user=self.request.user)

class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VideoSerializer

    def get_queryset(self):
        queryset = Video.objects.filter(source__user=self.request.user)
        
        # Filter by source_id
        source_id = self.request.query_params.get('source_id')
        if source_id:
            queryset = queryset.filter(source_id=source_id)
            
        # Filter by transcript_status
        transcript_status = self.request.query_params.get('transcript_status')
        if transcript_status:
            queryset = queryset.filter(transcript_status=transcript_status)
            
        # Filter by ai_analysis_status
        ai_analysis_status = self.request.query_params.get('ai_analysis_status')
        if ai_analysis_status:
            queryset = queryset.filter(ai_analysis_status=ai_analysis_status)
            
        # Search functionality
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
            
        return queryset.order_by('-published_at')
