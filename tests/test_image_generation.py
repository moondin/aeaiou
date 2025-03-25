import pytest
from unittest import mock
import logging

from app.services.image_generation import generate_image

@pytest.mark.asyncio
@mock.patch("app.core.config.settings.REPLICATE_API_TOKEN", "")
@mock.patch("app.services.queue_manager.update_job_status")
async def test_generate_image_missing_token(mock_update_status):
    """Test that image generation properly validates the Replicate API token"""
    # Mock the update_job_status to avoid actual Redis calls
    mock_update_status.return_value = None
    
    # Test parameters
    params = {
        "job_id": "test_job_id",
        "user_id": "test_user",
        "prompt": "Test prompt",
        "width": 512,
        "height": 512
    }
    
    # Should fail with error about missing token
    result = await generate_image(params)
    
    assert result["status"] == "failed"
    assert "Replicate API token is not configured" in result["error"]
