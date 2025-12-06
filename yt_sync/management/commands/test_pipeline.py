from django.core.management.base import BaseCommand
from yt_sync.models import Source, Video, ProcessedContent
from yt_sync.services.transcript import TranscriptService
from yt_sync.services.llm import LLMService
import uuid

class Command(BaseCommand):
    help = 'Test the processing pipeline with a specific YouTube video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=str, help='YouTube video ID to test')
        parser.add_argument('--skip-llm', action='store_true', help='Skip LLM processing (useful for testing without API key)')

    def handle(self, *args, **options):
        video_id = options['video_id']
        skip_llm = options['skip_llm']
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"🧪 Testing Pipeline with Video: {video_id}")
        self.stdout.write(f"{'='*60}\n")
        
        # Create test source and video
        test_user_id = uuid.uuid4()
        
        source = Source.objects.create(
            user_id=test_user_id,
            type=Source.SourceType.CHANNEL,
            youtube_id='test_channel',
            title='Test Channel',
            url='https://youtube.com/channel/test',
            status=Source.Status.ACTIVE
        )
        self.stdout.write(self.style.SUCCESS(f"✅ Created test source: {source.title}"))
        
        video, created = Video.objects.get_or_create(
            youtube_video_id=video_id,
            defaults={
                'source': source,
                'title': f'Test Video {video_id}',
                'url': f'https://youtube.com/watch?v={video_id}',
                'published_at': '2024-01-01T00:00:00Z',
                'transcript_status': Video.ProcessingStatus.PENDING,
                'ai_analysis_status': Video.ProcessingStatus.PENDING
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created test video: {video.title}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Using existing video: {video.title}"))
        
        # Step 1: Extract transcript
        self.stdout.write("\n📝 Step 1: Extracting transcript...")
        transcript_service = TranscriptService()
        transcript_result = transcript_service.get_transcript(video_id)
        
        if transcript_result:
            transcript_text = transcript_result['text']
            video.transcript_text = transcript_text
            video.transcript_data = transcript_result['data']
            video.transcript_status = Video.ProcessingStatus.COMPLETED
            video.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Transcript extracted ({len(transcript_text)} characters)"))
            self.stdout.write(f"   Preview: {transcript_text[:200]}...")
        else:
            video.transcript_status = Video.ProcessingStatus.FAILED
            video.save()
            self.stdout.write(self.style.ERROR("❌ Failed to extract transcript"))
            self.stdout.write(self.style.WARNING("   This video may not have captions available"))
            return
        
        # Step 2: Generate summary (if not skipped)
        if not skip_llm:
            self.stdout.write("\n🤖 Step 2: Generating AI summary...")
            try:
                llm_service = LLMService()
                summary_data = llm_service.generate_summary(transcript_text)
                
                if summary_data:
                    video.ai_analysis_status = Video.ProcessingStatus.COMPLETED
                    video.save()
                    
                    # Save processed content
                    ProcessedContent.objects.create(
                        video=video,
                        summary=summary_data.get('summary', ''),
                        tags=summary_data.get('tags', []),
                        categories=summary_data.get('categories', []),
                        main_ideas=summary_data.get('main_ideas', []),
                        key_moments=summary_data.get('key_moments', [])
                    )
                    
                    self.stdout.write(self.style.SUCCESS("✅ AI summary generated"))
                    self.stdout.write(f"\n   Summary: {summary_data.get('summary', '')}")
                    self.stdout.write(f"   Tags: {', '.join(summary_data.get('tags', []))}")
                    self.stdout.write(f"   Categories: {', '.join(summary_data.get('categories', []))}")
                else:
                    video.ai_analysis_status = Video.ProcessingStatus.FAILED
                    video.save()
                    self.stdout.write(self.style.ERROR("❌ Failed to generate summary"))
            except Exception as e:
                video.ai_analysis_status = Video.ProcessingStatus.FAILED
                video.save()
                self.stdout.write(self.style.ERROR(f"❌ LLM Error: {str(e)}"))
                self.stdout.write(self.style.WARNING("   Make sure ANTHROPIC_API_KEY is set in .env"))
        else:
            self.stdout.write(self.style.WARNING("\n⏭️  Skipping LLM processing (--skip-llm flag)"))
        
        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("📊 Test Summary")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Video ID: {video.id}")
        self.stdout.write(f"Transcript Status: {video.transcript_status}")
        self.stdout.write(f"AI Analysis Status: {video.ai_analysis_status}")
        
        # Cleanup option
        cleanup = input("\n🗑️  Delete test data? (y/N): ").lower()
        if cleanup == 'y':
            source.delete()
            self.stdout.write(self.style.SUCCESS("✅ Test data cleaned up"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Test data kept. Source ID: {source.id}"))
        
        self.stdout.write(self.style.SUCCESS("\n✨ Pipeline test complete!"))
