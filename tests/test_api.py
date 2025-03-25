import pytest
from fastapi.testclient import TestClient
import os
import json
from unittest import mock

from app.main import app

client = TestClient(app)

# Mock API key for testing
TEST_API_KEY = "test_key"

@pytest.fixture
def api_key_header():
    return {"X-API-Key": TEST_API_KEY}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to aeaiou AI Image Generation API"
    assert response.json()["status"] == "operational"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@mock.patch("app.services.rate_limiter.check_rate_limit")
@mock.patch("app.services.auth.verify_api_key")
@mock.patch("app.services.queue_manager.add_to_queue")
@mock.patch("app.api.v1.endpoints.generation.generate_image")
def test_generate_image(mock_generate, mock_add_queue, mock_auth, mock_rate_limit, api_key_header):
    # Configure mocks
    mock_auth.return_value = "test_user"
    mock_rate_limit.return_value = True
    mock_add_queue.return_value = True
    mock_generate.return_value = None
    
    # Test request
    request_data = {
        "prompt": "A beautiful sunset over mountains",
        "width": 512,
        "height": 512,
        "num_inference_steps": 50,
        "guidance_scale": 7.5
    }
    
    response = client.post(
        "/api/v1/generate",
        json=request_data,
        headers=api_key_header
    )
    
    assert response.status_code == 202
    assert "job_id" in response.json()
    assert response.json()["status"] == "pending"
    
    # Verify mocks were called correctly
    mock_auth.assert_called_once()
    mock_rate_limit.assert_called_once()
    mock_add_queue.assert_called_once()

@mock.patch("app.services.auth.verify_api_key")
@mock.patch("app.services.queue_manager.get_job_status")
@mock.patch("app.services.image_generation.check_generation_status")
def test_check_status(mock_check_status, mock_get_status, mock_auth, api_key_header):
    # Configure mocks
    mock_auth.return_value = "test_user"
    mock_get_status.return_value = {
        "job_id": "test_job_id",
        "user_id": "test_user",
        "status": "completed",
        "created_at": "2025-03-25T10:00:00"
    }
    mock_check_status.return_value = {
        "status": "completed",
        "message": "Image generated successfully",
        "progress": 100,
        "image_url": "http://example.com/image.png",
        "completed_at": "2025-03-25T10:01:00"
    }
    
    response = client.get(
        "/api/v1/status/test_job_id",
        headers=api_key_header
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == "test_job_id"
    assert response.json()["status"] == "completed"
    assert response.json()["image_url"] == "http://example.com/image.png"
    
    # Verify mocks were called correctly
    mock_auth.assert_called_once()
    mock_get_status.assert_called_once_with("test_job_id")
    mock_check_status.assert_called_once_with("test_job_id")
