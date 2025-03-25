import pytest
import os
import json
from unittest import mock

from app.services.auth import get_user_rate_limit
from app.services.storage import StorageError, get_image_path
from app.core.config import settings

# Test auth service fixes
@pytest.mark.asyncio
@mock.patch("app.services.auth.API_KEYS", {"test_key": {"user_id": "test_user", "rate_limit": 20}})
async def test_get_user_rate_limit():
    """Test the get_user_rate_limit function to ensure it works without redundant imports"""
    # Test with valid API key
    rate_limit = await get_user_rate_limit("test_key")
    assert rate_limit == 20
    
    # Test with unknown API key (should return default rate limit)
    rate_limit = await get_user_rate_limit("unknown_key")
    assert rate_limit == settings.RATE_LIMIT_PER_MINUTE

# Test S3 storage service fixes
@pytest.mark.asyncio
@mock.patch("app.core.config.settings.STORAGE_TYPE", "s3")
@mock.patch("app.core.config.settings.S3_BUCKET_NAME", None)
@mock.patch("app.core.config.settings.S3_REGION", "us-east-1")
async def test_s3_missing_bucket():
    """Test that proper error is raised when S3 bucket name is missing"""
    with pytest.raises(StorageError, match="S3 bucket name or region not configured"):
        await get_image_path("test_image_id")

@pytest.mark.asyncio
@mock.patch("app.core.config.settings.STORAGE_TYPE", "s3")
@mock.patch("app.core.config.settings.S3_BUCKET_NAME", "test-bucket")
@mock.patch("app.core.config.settings.S3_REGION", None)
async def test_s3_missing_region():
    """Test that proper error is raised when S3 region is missing"""
    with pytest.raises(StorageError, match="S3 bucket name or region not configured"):
        await get_image_path("test_image_id")

@pytest.mark.asyncio
@mock.patch("app.core.config.settings.STORAGE_TYPE", "s3")
@mock.patch("app.core.config.settings.S3_BUCKET_NAME", "test-bucket")
@mock.patch("app.core.config.settings.S3_REGION", "us-east-1")
async def test_s3_correct_url_format():
    """Test that S3 URL is formatted correctly"""
    url = await get_image_path("test_image_id")
    assert url == "https://test-bucket.s3.us-east-1.amazonaws.com/images/test_image_id.png"
