import replicate
import asyncio
import logging
from typing import Dict, Any, Optional
import json
import time
import traceback

from app.core.config import settings
from app.services.storage import save_image
from app.services.queue_manager import update_job_status, get_job_status

class ImageGenerationError(Exception):
    """Custom exception for image generation errors"""
    pass

async def generate_image(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an image using the Replicate API.
    Handles the actual image generation process and updates job status.
    """
    job_id = params["job_id"]
    
    try:
        # Check if Replicate API token is configured
        if not settings.REPLICATE_API_TOKEN:
            error_message = "Replicate API token is not configured"
            await update_job_status(job_id, "failed", f"Generation failed: {error_message}")
            return {
                "status": "failed",
                "error": error_message,
                "job_id": job_id
            }
            
        logging.info(f"Starting image generation for job {job_id}")
        # Update job status to processing
        await update_job_status(job_id, "processing", "Starting image generation")
        
        # Initialize Replicate client
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
        # Prepare model inputs
        model_inputs = {
            "prompt": params["prompt"],
            "width": params["width"],
            "height": params["height"],
            "num_inference_steps": params["num_inference_steps"],
            "guidance_scale": params["guidance_scale"],
        }
        
        if params.get("negative_prompt"):
            model_inputs["negative_prompt"] = params["negative_prompt"]
        if params.get("seed") is not None:
            model_inputs["seed"] = params["seed"]
        
        logging.info(f"Running Replicate model for job {job_id}")
        # Start the generation
        try:
            output = client.run(
                settings.REPLICATE_MODEL_VERSION,
                input=model_inputs
            )
        except Exception as e:
            raise ImageGenerationError(f"Replicate API error: {str(e)}")
        
        if not output:
            raise ImageGenerationError("No output received from model")
        
        # Get the image URL from the output
        image_url = output[0] if isinstance(output, list) else output
        logging.info(f"Successfully generated image for job {job_id}")
        
        # Save the image to our storage
        try:
            image_data = await save_image(
                job_id,
                image_url,
                params["user_id"],
                params["prompt"],
                params["width"],
                params["height"]
            )
        except Exception as e:
            logging.error(f"Failed to save image for job {job_id}: {str(e)}")
            await update_job_status(
                job_id, 
                "failed", 
                f"Image generation succeeded but storage failed: {str(e)}"
            )
            raise ImageGenerationError(f"Failed to save image: {str(e)}")
        
        # Update job status to completed
        await update_job_status(
            job_id,
            "completed",
            "Image generation successful",
            image_url=image_data["url"]
        )
        
        logging.info(f"Image generation process completed for job {job_id}")
        return {
            "status": "completed",
            "image_url": image_data["url"],
            "metadata": image_data
        }
        
    except Exception as e:
        # Capture full exception details
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logging.error(f"Image generation failed for job {job_id}: {error_message}\n{stack_trace}")
        
        # Update job status to failed
        try:
            await update_job_status(job_id, "failed", f"Generation failed: {error_message}")
        except Exception as update_error:
            logging.error(f"Failed to update job status after error: {str(update_error)}")
            
        # Return error information instead of raising an exception
        return {
            "status": "failed",
            "error": error_message,
            "job_id": job_id
        }

async def check_generation_status(job_id: str) -> Dict[str, Any]:
    """
    Check the status of an image generation job.
    Returns the current status and any available results.
    """
    try:
        logging.info(f"Checking generation status for job {job_id}")
        # Get the current status from the queue manager
        status = await get_job_status(job_id)
        
        if not status:
            logging.warning(f"Job not found: {job_id}")
            raise ImageGenerationError("Job not found")
        
        return {
            "status": status["status"],
            "message": status.get("message", ""),
            "progress": status.get("progress"),
            "image_url": status.get("image_url"),
            "created_at": status.get("created_at"),
            "completed_at": status.get("completed_at")
        }
        
    except Exception as e:
        logging.error(f"Failed to check job status for {job_id}: {str(e)}")
        raise ImageGenerationError(f"Failed to check job status: {str(e)}")
