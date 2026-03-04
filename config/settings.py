from pathlib import Path
import environ
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_q',
    
    # Local
    'yt_sync',
    'rag',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model with UUID primary key
# Custom User Model with UUID primary key
AUTH_USER_MODEL = 'yt_sync.User'

# Django Q Configuration (using ORM backend - no Redis required)
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': env.int('DJANGO_Q_WORKERS', default=4),
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'orm': 'default',  # Use Django ORM as broker
}

# Supabase Configuration
SUPABASE_URL = env('SUPABASE_URL', default='')
SUPABASE_KEY = env('SUPABASE_KEY', default='')
SUPABASE_JWT_SECRET = env('SUPABASE_JWT_SECRET', default='')

# External APIs
YOUTUBE_API_KEY = env('YOUTUBE_API_KEY', default='')
# ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'yt_sync.authentication.SupabaseAuthentication',
        'rest_framework.authentication.SessionAuthentication', 
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True  # For dev only

# =============================================================================
# RAG (Retrieval-Augmented Generation) Configuration
# =============================================================================

# Embedding Provider Configuration
RAG_EMBEDDING_PROVIDER = env('RAG_EMBEDDING_PROVIDER', default='local')
"""
Embedding provider for transcript vectorization.
Options: 'local' (sentence-transformers), 'openai', 'cohere', etc.
"""

RAG_EMBEDDING_MODEL = env(
    'RAG_EMBEDDING_MODEL',
    default='sentence-transformers/all-MiniLM-L6-v2'
)
"""
Model identifier for embeddings.
Examples:
- 'sentence-transformers/all-MiniLM-L6-v2' (local, 384 dims)
- 'text-embedding-3-small' (OpenAI, 1536 dims)
- 'embed-english-v3.0' (Cohere)
"""

# Ingestion Settings
RAG_AUTO_INGEST = env.bool('RAG_AUTO_INGEST', default=True)
"""
Automatically trigger transcript ingestion when new videos are synced.
Set to False to manually trigger ingestion via management command.
"""

# Chunking Configuration
RAG_CHUNK_GAP_THRESHOLD = env.float('RAG_CHUNK_GAP_THRESHOLD', default=2.0)
"""
Maximum gap in seconds between transcript segments to merge into one chunk.
Segments separated by longer pauses will be split into separate chunks.
"""

RAG_CHUNK_MAX_CHARS = env.int('RAG_CHUNK_MAX_CHARS', default=1000)
"""
Maximum characters per chunk.
Larger chunks provide more context but may dilute semantic relevance.
"""

RAG_CHUNK_MIN_CHARS = env.int('RAG_CHUNK_MIN_CHARS', default=100)
"""
Minimum characters per chunk to avoid tiny fragments.
Smaller values allow more granular search but increase storage costs.
"""

# Embedding Batch Processing
RAG_EMBEDDING_BATCH_SIZE = env.int('RAG_EMBEDDING_BATCH_SIZE', default=50)
"""
Number of text chunks to embed in a single API call.
Higher values improve throughput but may hit API rate limits.
"""
