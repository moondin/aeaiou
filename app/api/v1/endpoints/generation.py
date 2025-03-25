from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Query
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any
from uuid import uuid4
import json

from app.core.config import settings
from app.models.generation import GenerationRequest, GenerationResponse
from app.services.auth import verify_api_key
from app.services.rate_limiter import check_rate_limit
from app.services.image_generation import generate_image
from app.services.queue_manager import add_to_queue

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")

@router.post("", response_model=GenerationResponse, status_code=202)
async def create_generation(
    background_tasks: BackgroundTasks,
    request: GenerationRequest,
    api_key: str = Depends(api_key_header),
    user_id: str = Depends(verify_api_key),
    rate_limited: bool = Depends(check_rate_limit),
):
    """
    Create a new image generation job.
    
    - **prompt**: Text description of the image to generate
    - **width**: Optional image width (default: 512)
    - **height**: Optional image height (default: 512)
    - **num_inference_steps**: Optional number of diffusion steps (default: 50)
    - **guidance_scale**: Optional guidance scale (default: 7.5)
    - **negative_prompt**: Optional negative prompt to guide generation
    - **seed**: Optional seed for reproducibility
    """
    
    # Generate unique job ID
    job_id = str(uuid4())
    
    # Prepare parameters for the generation task
    params = {
        "job_id": job_id,
        "user_id": user_id,
        "prompt": request.prompt,
        "width": request.width,
        "height": request.height,
        "num_inference_steps": request.num_inference_steps,
        "guidance_scale": request.guidance_scale,
        "negative_prompt": request.negative_prompt,
        "seed": request.seed,
        "model_version": settings.REPLICATE_MODEL_VERSION
    }
    
    # Add job to the queue (Redis or other message queue)
    await add_to_queue(job_id, params)
    
    # Start background processing task
    background_tasks.add_task(generate_image, params)
    
    return GenerationResponse(
        job_id=job_id,
        status="pending",
        message="Image generation job added to queue"
    )
