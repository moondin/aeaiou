import os
import aiohttp
import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

from app.core.config import settings

class StorageError(Exception):
    """Custom exception for storage-related errors"""
    pass

async def save_image(
    job_id: str,
    image_url: str,
    user_id: str,
    prompt: str,
    width: int,
    height: int
) -> Dict[str, Any]:
    """
    Save an image from a URL to the configured storage backend.
    Returns metadata about the saved image.
    """
    try:
        # Generate a unique image ID based on job_id
        image_id = hashlib.sha256(f"{job_id}:{datetime.utcnow().timestamp()}".encode()).hexdigest()[:16]
        
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise StorageError(f"Failed to download image: HTTP {response.status}")
                image_data = await response.read()
        
        # Prepare metadata
        metadata = {
            "image_id": image_id,
            "user_id": user_id,
            "prompt": prompt,
            "width": width,
            "height": height,
            "created_at": datetime.utcnow().isoformat(),
            "job_id": job_id,
        }
        
        if settings.STORAGE_TYPE == "s3":
            # Store in S3
            return await _save_to_s3(image_id, image_data, metadata)
        else:
            # Store locally
            return await _save_locally(image_id, image_data, metadata)
            
    except Exception as e:
        raise StorageError(f"Failed to save image: {str(e)}")

async def _save_locally(image_id: str, image_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Save image and metadata to local storage"""
    try:
        # Create directories if they don't exist
        os.makedirs("storage/images", exist_ok=True)
        os.makedirs("storage/metadata", exist_ok=True)
        
        # Save image
        image_path = f"storage/images/{image_id}.png"
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # Save metadata
        metadata_path = f"storage/metadata/{image_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        
        # Add local path to metadata
        metadata["url"] = f"/api/v1/images/{image_id}/content"
        return metadata
        
    except Exception as e:
        raise StorageError(f"Failed to save locally: {str(e)}")

async def _save_to_s3(image_id: str, image_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Save image and metadata to S3"""
    try:
        # Check if S3 configuration is available
        if not settings.S3_BUCKET_NAME or not settings.S3_REGION:
            raise StorageError("S3 bucket name or region not configured")
            
        s3 = boto3.client('s3', region_name=settings.S3_REGION)
        
        # Save image
        image_key = f"images/{image_id}.png"
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=image_key,
            Body=image_data,
            ContentType="image/png"
        )
        
        # Save metadata
        metadata_key = f"metadata/{image_id}.json"
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType="application/json"
        )
        
        # Generate S3 URL
        url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/{image_key}"
        metadata["url"] = url
        return metadata
        
    except Exception as e:
        raise StorageError(f"Failed to save to S3: {str(e)}")

async def get_image_path(image_id: str) -> str:
    """Get the path or URL to an image"""
    if settings.STORAGE_TYPE == "s3":
        # Check if S3 configuration is available
        if not settings.S3_BUCKET_NAME or not settings.S3_REGION:
            raise StorageError("S3 bucket name or region not configured")
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.S3_REGION}.amazonaws.com/images/{image_id}.png"
    else:
        return f"storage/images/{image_id}.png"

async def get_image_metadata(image_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for an image"""
    try:
        if settings.STORAGE_TYPE == "s3":
            # Check if S3 configuration is available
            if not settings.S3_BUCKET_NAME or not settings.S3_REGION:
                raise StorageError("S3 bucket name or region not configured")
                
            s3 = boto3.client('s3', region_name=settings.S3_REGION)
            response = s3.get_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=f"metadata/{image_id}.json"
            )
            return json.loads(response['Body'].read())
        else:
            metadata_path = f"storage/metadata/{image_id}.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    return json.load(f)
            return None
    except Exception as e:
        # For metadata retrieval, we fail silently with None
        return None

async def image_exists(image_id: str) -> bool:
    """Check if an image exists in storage"""
    try:
        if settings.STORAGE_TYPE == "s3":
            # Check if S3 configuration is available
            if not settings.S3_BUCKET_NAME or not settings.S3_REGION:
                raise StorageError("S3 bucket name or region not configured")
                
            s3 = boto3.client('s3', region_name=settings.S3_REGION)
            s3.head_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=f"images/{image_id}.png"
            )
            return True
        else:
            return os.path.exists(f"storage/images/{image_id}.png")
    except Exception:
        return False
