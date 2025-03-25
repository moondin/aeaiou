from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.security import APIKeyHeader
from typing import Optional

from app.models.generation import JobStatusResponse
from app.services.auth import verify_api_key
from app.services.queue_manager import get_job_status
from app.services.image_generation import check_generation_status

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key")

@router.get("/{job_id}", response_model=JobStatusResponse)
async def check_status(
    job_id: str = Path(..., description="The ID of the generation job to check"),
    api_key: str = Depends(api_key_header),
    user_id: str = Depends(verify_api_key),
):
    """
    Check the status of an image generation job.
    
    - **job_id**: ID of the generation job to check
    
    Returns the current status of the job (pending, processing, completed, failed)
    and additional information if available.
    """
    
    # Check if the job exists and belongs to the user
    job_info = await get_job_status(job_id)
    
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Verify the job belongs to the user (optional for extra security)
    if "params" in job_info and job_info["params"].get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this job")
    
    # Get detailed status from the generation service
    status_details = await check_generation_status(job_id)
    
    return JobStatusResponse(
        job_id=job_id,
        status=status_details["status"],
        message=status_details.get("message", ""),
        progress=status_details.get("progress"),
        image_url=status_details.get("image_url"),
        created_at=job_info.get("created_at"),
        completed_at=status_details.get("completed_at")
    )
