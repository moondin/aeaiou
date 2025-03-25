from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class GenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., description="Text description of the image to generate", min_length=3, max_length=1000)
    width: int = Field(512, description="Width of the generated image", ge=256, le=1024)
    height: int = Field(512, description="Height of the generated image", ge=256, le=1024)
    num_inference_steps: int = Field(50, description="Number of denoising steps", ge=20, le=100)
    guidance_scale: float = Field(7.5, description="Scale for classifier-free guidance", ge=1.0, le=20.0)
    negative_prompt: Optional[str] = Field(None, description="Text to guide what not to include in the image")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    
    @field_validator('prompt')
    def validate_prompt(cls, v):
        # Add any content moderation checks here
        banned_terms = ["explicit", "nsfw", "offensive"]  # Example - expand with real moderation
        for term in banned_terms:
            if term in v.lower():
                raise ValueError(f"Prompt contains banned term: {term}")
        return v

class GenerationResponse(BaseModel):
    """Response model for image generation requests"""
    job_id: str = Field(..., description="Unique ID for the generation job")
    status: str = Field(..., description="Status of the generation job")
    message: str = Field(..., description="Informational message about the job")

class JobStatusResponse(BaseModel):
    """Response model for job status checks"""
    job_id: str = Field(..., description="Unique ID for the generation job")
    status: str = Field(..., description="Current status (pending, processing, completed, failed)")
    message: Optional[str] = Field(None, description="Additional information or error message")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    image_url: Optional[str] = Field(None, description="URL to the generated image if completed")
    created_at: Optional[datetime] = Field(None, description="When the job was created")
    completed_at: Optional[datetime] = Field(None, description="When the job was completed")

class ImageResponse(BaseModel):
    """Response model for image metadata"""
    image_id: str = Field(..., description="Unique ID for the image")
    url: str = Field(..., description="URL to access the image content")
    prompt: str = Field(..., description="Original prompt used to generate the image")
    width: int = Field(..., description="Width of the image in pixels")
    height: int = Field(..., description="Height of the image in pixels")
    created_at: datetime = Field(..., description="When the image was created")
