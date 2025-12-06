"""
Pytest configuration for content-sync-service.

This file is automatically loaded by pytest and configures
Django settings and common fixtures.
"""
import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests by default."""
    pass


@pytest.fixture
def api_client():
    """Return a DRF test client."""
    from rest_framework.test import APIClient

    return APIClient()
