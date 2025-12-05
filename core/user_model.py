import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model with UUID as primary key.
    This is better for security and works well with Supabase Auth.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        db_table = 'auth_user'  # Keep the same table name for compatibility
