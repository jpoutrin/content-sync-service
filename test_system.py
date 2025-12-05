"""
Simple test script to verify the core functionality.
This tests the models and basic task structure without external API calls.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Source, Video, ProcessedContent
from django.utils import timezone
from datetime import timedelta
import uuid

def test_models():
    """Test that we can create and query models."""
    print("🧪 Testing Models...")
    
    # Create a test user ID
    test_user_id = uuid.uuid4()
    
    # Create a test source
    source = Source.objects.create(
        user_id=test_user_id,
        type=Source.SourceType.CHANNEL,
        youtube_id='UC_test_channel_id',
        title='Test Channel',
        url='https://youtube.com/channel/UC_test_channel_id',
        status=Source.Status.ACTIVE
    )
    print(f"✅ Created source: {source.title}")
    
    # Create a test video
    video = Video.objects.create(
        source=source,
        youtube_video_id='test_video_123',
        title='Test Video',
        url='https://youtube.com/watch?v=test_video_123',
        duration=timedelta(minutes=10),
        published_at=timezone.now(),
        transcript_text='This is a test transcript.',
        transcript_status=Video.ProcessingStatus.COMPLETED,
        ai_analysis_status=Video.ProcessingStatus.PENDING
    )
    print(f"✅ Created video: {video.title}")
    
    # Create processed content
    processed = ProcessedContent.objects.create(
        video=video,
        summary='This is a test summary.',
        tags=['test', 'demo'],
        categories=['Testing'],
        main_ideas=['Idea 1', 'Idea 2'],
        key_moments=[
            {'timestamp': '00:01:00', 'description': 'Introduction'},
            {'timestamp': '00:05:00', 'description': 'Main content'}
        ]
    )
    print(f"✅ Created processed content for: {video.title}")
    
    # Query and verify
    sources = Source.objects.filter(user_id=test_user_id)
    print(f"✅ Found {sources.count()} source(s) for user")
    
    videos = Video.objects.filter(source__user_id=test_user_id)
    print(f"✅ Found {videos.count()} video(s) for user")
    
    # Test the relationship
    video_with_content = Video.objects.filter(
        processed_content__isnull=False
    ).first()
    if video_with_content:
        print(f"✅ Video has processed content: {video_with_content.processed_content.summary[:50]}...")
    
    # Cleanup
    source.delete()
    print("✅ Cleaned up test data")
    
    print("\n✨ All model tests passed!")
    return True

def test_services():
    """Test service imports and basic structure."""
    print("\n🧪 Testing Services...")
    
    try:
        from core.services.youtube import YouTubeService
        print("✅ YouTubeService imported successfully")
        
        from core.services.transcript import TranscriptService
        print("✅ TranscriptService imported successfully")
        
        from core.services.llm import LLMService
        print("✅ LLMService imported successfully")
        
        print("\n✨ All service imports passed!")
        return True
    except Exception as e:
        print(f"❌ Service import failed: {e}")
        return False

def test_tasks():
    """Test task imports."""
    print("\n🧪 Testing Tasks...")
    
    try:
        from core.tasks import (
            sync_sources_task,
            fetch_source_videos_task,
            process_video_pipeline_task,
            extract_transcript_task,
            generate_summary_task,
            save_results_task
        )
        print("✅ All tasks imported successfully")
        print("\n✨ All task imports passed!")
        return True
    except Exception as e:
        print(f"❌ Task import failed: {e}")
        return False

def test_api():
    """Test API serializers and views."""
    print("\n🧪 Testing API Components...")
    
    try:
        from core.serializers import SourceSerializer, VideoSerializer, ProcessedContentSerializer
        print("✅ All serializers imported successfully")
        
        from core.views import SourceViewSet, VideoViewSet
        print("✅ All viewsets imported successfully")
        
        from core.authentication import SupabaseAuthentication
        print("✅ Authentication imported successfully")
        
        print("\n✨ All API component imports passed!")
        return True
    except Exception as e:
        print(f"❌ API component import failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ContentSync Test Suite")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Models", test_models()))
        results.append(("Services", test_services()))
        results.append(("Tasks", test_tasks()))
        results.append(("API", test_api()))
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{name:20s} {status}")
        
        all_passed = all(result[1] for result in results)
        
        if all_passed:
            print("\n🎉 All tests passed! The system is ready.")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
