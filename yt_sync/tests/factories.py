"""
Factory classes for creating test data.

Uses factory_boy to generate realistic test fixtures
for the yt_sync models.
"""
import uuid
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from yt_sync.models import ProcessedContent, Source, User, Video


class UserFactory(DjangoModelFactory):
    """Factory for creating test User instances."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    is_active = True
    is_staff = False


class SourceFactory(DjangoModelFactory):
    """Factory for creating test Source instances."""

    class Meta:
        model = Source

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    type = Source.SourceType.CHANNEL
    youtube_id = factory.Sequence(lambda n: f"UC{n:024d}")
    title = factory.Sequence(lambda n: f"Test Channel {n}")
    url = factory.LazyAttribute(
        lambda obj: f"https://www.youtube.com/channel/{obj.youtube_id}"
    )
    sync_frequency = "daily"
    status = Source.Status.ACTIVE


class VideoFactory(DjangoModelFactory):
    """Factory for creating test Video instances."""

    class Meta:
        model = Video

    id = factory.LazyFunction(uuid.uuid4)
    source = factory.SubFactory(SourceFactory)
    youtube_video_id = factory.Sequence(lambda n: f"vid_{n:011d}")
    title = factory.Sequence(lambda n: f"Test Video {n}")
    url = factory.LazyAttribute(
        lambda obj: f"https://www.youtube.com/watch?v={obj.youtube_video_id}"
    )
    duration = timedelta(minutes=10)
    published_at = factory.LazyFunction(timezone.now)
    transcript_status = Video.ProcessingStatus.PENDING
    ai_analysis_status = Video.ProcessingStatus.PENDING


class ProcessedContentFactory(DjangoModelFactory):
    """Factory for creating test ProcessedContent instances."""

    class Meta:
        model = ProcessedContent

    video = factory.SubFactory(VideoFactory)
    summary = factory.Faker("paragraph", nb_sentences=3)
    tags = factory.LazyFunction(lambda: ["tag1", "tag2", "tag3"])
    categories = factory.LazyFunction(lambda: ["Technology", "Education"])
    main_ideas = factory.LazyFunction(
        lambda: ["Main idea 1", "Main idea 2", "Main idea 3"]
    )
    key_moments = factory.LazyFunction(
        lambda: [
            {"time": "00:00", "description": "Introduction"},
            {"time": "05:00", "description": "Main content"},
            {"time": "09:00", "description": "Conclusion"},
        ]
    )
