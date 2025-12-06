from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SourceViewSet, VideoViewSet

router = DefaultRouter()
router.register(r'sources', SourceViewSet, basename='source')
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]
