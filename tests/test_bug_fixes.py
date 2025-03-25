import pytest
from fastapi.testclient import TestClient
import os
import json
from unittest import mock
from datetime import datetime, timezone

from app.main import app
from app.services.auth import get_user_rate_limit, create_api_key
from app.services.storage import get_image_path, get_image_metadata, image_exists, StorageError
from app.core.config import settings

client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test_key"
TEST_USER_ID = "test_user_id"

@pytest.fixture
def api_key_header():
    return {"X-API-Key": TEST_API_KEY}

# Test auth service fixes
@pytest.mark.asyncio
@mock.patch("app.services.auth.API_KEYS", {TEST_API_KEY: {"user_id": TEST_USER_ID, "rate_limit": 20}})
async def test_get_user_rate_limit():
    # Test with valid API key
    rate_limit = await get_user_rate_limit(TEST_API_KEY)
    assert rate_limit == 20
    
    # Test with unknown API key (should return default rate limit)
    rate_limit = await get_user_rate_limit("unknown_key")
    assert rate_limit == settings.RATE_LIMIT_PER_MINUTE

# Test S3 storage service fixes
@pytest.mark.asyncio
@mock.patch("app.core.config.settings.STORAGE_TYPE", "s3")
@mock.patch("app.core.config.settings.S3_BUCKET_NAME", None)
async def test_storage_s3_missing_config():
    # Test S3 storage with missing bucket name
    with pytest.raises(StorageError, match="S3 bucket name or region not configured"):
        await get_image_path("test_image_id")
    
    with pytest.raises(StorageError, match="S3 bucket name or region not configured"):
        await image_exists("test_image_id")
    
    # For this function, we should get None instead of an exception
    assert await get_image_metadata("test_image_id") is None

# Test with proper S3 configuration
@pytest.mark.asyncio
@mock.patch("app.core.config.settings.STORAGE_TYPE", "s3")
@mock.patch("app.core.config.settings.S3_BUCKET_NAME", "test-bucket")
@mock.patch("app.core.config.settings.S3_REGION", "us-east-1")
@mock.patch("boto3.client")
async def test_storage_s3_with_config(mock_boto3):
    # Mock boto3 client
    mock_s3 = mock.MagicMock()
    mock_boto3.return_value = mock_s3
    
    # Test get_image_path
    image_path = await get_image_path("test_image_id")
    assert image_path == "https://test-bucket.s3.us-east-1.amazonaws.com/images/test_image_id.png"
    
    # Verify boto3 client was called with region_name
    mock_boto3.assert_called_with('s3', region_name='us-east-1')

# Test status endpoint fix
@mock.patch("app.services.auth.verify_api_key")
@mock.patch("app.services.queue_manager.get_job_status")
@mock.patch("app.services.image_generation.check_generation_status")
def test_check_status_with_params(mock_check_status, mock_get_status, mock_auth, api_key_header):
    # Configure mocks
    mock_auth.return_value = TEST_USER_ID
    mock_get_status.return_value = {
        "job_id": "test_job_id",
        "params": {
            "user_id": TEST_USER_ID
        },
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    mock_check_status.return_value = {
        "status": "completed",
        "message": "Image generated successfully",
        "progress": 100,
        "image_url": "http://example.com/image.png",
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = client.get(
        "/api/v1/status/test_job_id",
        headers=api_key_header
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == "test_job_id"
    assert response.json()["status"] == "completed"

# Test images endpoint fix for missing metadata
@mock.patch("app.services.auth.verify_api_key")
@mock.patch("app.services.storage.image_exists")
@mock.patch("app.services.storage.get_image_metadata")
def test_image_with_missing_metadata(mock_get_metadata, mock_image_exists, mock_auth, api_key_header):
    # Configure mocks
    mock_auth.return_value = TEST_USER_ID
    mock_image_exists.return_value = True
    mock_get_metadata.return_value = None
    
    response = client.get(
        "/api/v1/images/test_image_id",
        headers=api_key_header
    )
    
    # Should return 404 when metadata is missing
    assert response.status_code == 404
    assert "Image metadata not found" in response.json()["detail"]

# Test image generation with missing Replicate API token
@pytest.mark.asyncio
@mock.patch("app.core.config.settings.REPLICATE_API_TOKEN", "")
@mock.patch("app.services.queue_manager.update_job_status")
async def test_generate_image_missing_token(mock_update_status):
    # Test parameters
    params = {
        "job_id": "test_job_id",
        "user_id": TEST_USER_ID,
        "prompt": "Test prompt",
        "width": 512,
        "height": 512
    }
    
    # Import here to avoid circular imports
    from app.services.image_generation import generate_image
    
    # Stub the update_job_status call
    mock_update_status.return_value = None
    
    # Should fail with error about missing token
    result = await generate_image(params)
    
    assert result["status"] == "failed"
    assert "Replicate API token is not configured" in result["error"]
    
    # Verify job status was updated to failed
    mock_update_status.assert_called_with(
        job_id="test_job_id",
        status="failed",
        message=mock.ANY,
        progress=None
    )
