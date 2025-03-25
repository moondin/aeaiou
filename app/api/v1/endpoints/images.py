from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse, RedirectResponse
from typing import Optional
import os

from app.models.generation import ImageResponse
from app.services.auth import verify_api_key
from app.services.storage import get_image_path, get_image_metadata, image_exists
from app.core.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image_metadata(
    image_id: str = Path(..., description="The ID of the image to retrieve"),
    api_key: str = Depends(api_key_header),
    user_id: str = Depends(verify_api_key),
):
    """
    Get metadata for a generated image.
    
    - **image_id**: ID of the image to retrieve
    
    Returns metadata including the URL to access the image directly.
    """
    
    # Check if the image exists
    if not await image_exists(image_id):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get image metadata
    metadata = await get_image_metadata(image_id)
    
    # Check if metadata exists
    if not metadata:
        raise HTTPException(status_code=404, detail="Image metadata not found")
    
    # Verify the image belongs to the user (optional for extra security)
    if metadata.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this image")
    
    return ImageResponse(
        image_id=image_id,
        url=f"/api/v1/images/{image_id}/content",
        prompt=metadata.get("prompt", ""),
        width=metadata.get("width", 512),
        height=metadata.get("height", 512),
        created_at=metadata.get("created_at")
    )

@router.get("/{image_id}/content")
async def get_image_content(
    image_id: str = Path(..., description="The ID of the image to retrieve"),
    api_key: str = Depends(api_key_header),
    user_id: str = Depends(verify_api_key),
    download: bool = Query(False, description="Set to true to download the image instead of viewing it"),
):
    """
    Get the actual image content for a generated image.
    
    - **image_id**: ID of the image to retrieve
    - **download**: Set to true to download the image instead of viewing it
    
    Returns the image file or a redirect to the image URL if using cloud storage.
    """
    
    # Check if the image exists
    if not await image_exists(image_id):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get image metadata to verify ownership
    metadata = await get_image_metadata(image_id)
    
    # Check if metadata exists
    if not metadata:
        raise HTTPException(status_code=404, detail="Image metadata not found")
    
    # Verify the image belongs to the user (optional for extra security)
    if metadata.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this image")
    
    # Get the path or URL to the image
    image_path = await get_image_path(image_id)
    
    # Handle different storage types
    if settings.STORAGE_TYPE == "local":
        # For local storage, serve the file directly
        filename = f"aeaiou-image-{image_id}.png"
        if download:
            return FileResponse(
                path=image_path,
                filename=filename,
                media_type="image/png"
            )
        else:
            return FileResponse(
                path=image_path,
                media_type="image/png"
            )
    else:
        # For cloud storage (S3, etc.), redirect to the URL
        return RedirectResponse(url=image_path)
