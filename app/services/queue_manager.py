import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
import functools
import logging

from app.core.config import settings

# Initialize Redis client
try:
    # Use REDIS_URL if available (Railway.app and other platforms provide this)
    if settings.REDIS_URL:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    else:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    # Test connection
    redis_client.ping()
except redis.RedisError as e:
    logging.warning(f"Redis connection error: {str(e)}. Some functionality may be limited.")
    redis_client = None

class QueueError(Exception):
    """Custom exception for queue-related errors"""
    pass

def redis_connection_handler(default_return_value=None):
    """Decorator to handle Redis connection errors gracefully"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if redis_client is None:
                    logging.error("Redis client is not available")
                    return default_return_value
                return await func(*args, **kwargs)
            except redis.RedisError as e:
                logging.error(f"Redis error in {func.__name__}: {str(e)}")
                raise QueueError(f"Queue service unavailable: {str(e)}")
        return wrapper
    return decorator

@redis_connection_handler(default_return_value=False)
async def add_to_queue(job_id: str, params: Dict[str, Any]) -> bool:
    """
    Add a job to the queue.
    Returns True if successful, False otherwise.
    """
    # Create job data structure
    job_data = {
        "job_id": job_id,
        "params": params,
        "status": "pending",
        "message": "Job added to queue",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Add to Redis
    # We use two data structures:
    # 1. A hash for the job data
    # 2. A sorted set for the queue itself
    
    # Store job data
    redis_client.hset(
        f"job:{job_id}",
        mapping={
            "data": json.dumps(job_data),
            "status": "pending"
        }
    )
    
    # Add to queue with priority based on timestamp
    score = datetime.utcnow().timestamp()
    redis_client.zadd("image_generation_queue", {job_id: score})
    
    # Set expiration (24 hours)
    redis_client.expire(f"job:{job_id}", 86400)
    
    return True

@redis_connection_handler(default_return_value=False)
async def update_job_status(
    job_id: str,
    status: str,
    message: str,
    progress: Optional[float] = None,
    image_url: Optional[str] = None
) -> bool:
    """
    Update the status of a job in the queue.
    Returns True if successful, False otherwise.
    """
    # Get current job data
    job_data = await get_job_status(job_id)
    if not job_data:
        raise QueueError(f"Job {job_id} not found")
    
    # Update job data
    job_data.update({
        "status": status,
        "message": message,
        "updated_at": datetime.utcnow().isoformat()
    })
    
    if progress is not None:
        job_data["progress"] = progress
        
    if image_url is not None:
        job_data["image_url"] = image_url
        
    if status in ["completed", "failed"]:
        job_data["completed_at"] = datetime.utcnow().isoformat()
    
    # Store updated data
    redis_client.hset(
        f"job:{job_id}",
        mapping={
            "data": json.dumps(job_data),
            "status": status
        }
    )
    
    # If job is complete or failed, remove from queue
    if status in ["completed", "failed"]:
        redis_client.zrem("image_generation_queue", job_id)
    
    return True

@redis_connection_handler(default_return_value=None)
async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current status of a job.
    Returns None if job not found.
    """
    # Get job data from Redis
    job_data = redis_client.hget(f"job:{job_id}", "data")
    
    if job_data:
        return json.loads(job_data)
    return None

@redis_connection_handler(default_return_value={"queue_length": 0, "processing_jobs": 0, "jobs": []})
async def get_queue_status() -> Dict[str, Any]:
    """
    Get the current status of the queue.
    Returns information about queue length and processing jobs.
    """
    # Get queue length
    queue_length = redis_client.zcard("image_generation_queue")
    
    # Get currently processing jobs
    processing_jobs = []
    for job_id in redis_client.zrange("image_generation_queue", 0, -1):
        job_data = await get_job_status(job_id)
        if job_data and job_data["status"] == "processing":
            processing_jobs.append(job_data)
    
    return {
        "queue_length": queue_length,
        "processing_jobs": len(processing_jobs),
        "jobs": processing_jobs
    }

@redis_connection_handler(default_return_value=0)
async def clean_queue() -> int:
    """
    Clean up completed and failed jobs older than 24 hours.
    Returns the number of jobs cleaned up.
    """
    cleaned = 0
    cutoff = datetime.utcnow().timestamp() - 86400  # 24 hours ago
    
    # Get all jobs from queue
    jobs = redis_client.zrangebyscore("image_generation_queue", 0, cutoff)
    
    for job_id in jobs:
        job_data = await get_job_status(job_id)
        if job_data and job_data["status"] in ["completed", "failed"]:
            # Remove job data and from queue
            redis_client.delete(f"job:{job_id}")
            redis_client.zrem("image_generation_queue", job_id)
            cleaned += 1
    
    return cleaned

# Optional: Set up background task for queue cleanup
async def start_queue_cleanup_task():
    """
    Start a background task to periodically clean up the queue.
    This would typically be called when your application starts.
    """
    import asyncio
    
    async def cleanup_task():
        while True:
            try:
                await clean_queue()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logging.error(f"Error in queue cleanup task: {str(e)}")
                # Continue running despite errors
                await asyncio.sleep(3600)
    
    asyncio.create_task(cleanup_task())
