from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader
import redis
import time
import logging
from typing import Optional

from app.core.config import settings
from app.services.auth import get_user_rate_limit

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logging.info("Redis connection for rate limiter successfully established")
except redis.RedisError as e:
    logging.warning(f"Redis connection error in rate limiter: {str(e)}. Rate limiting may not work properly.")
    redis_client = None

async def check_rate_limit(
    api_key: str = Depends(APIKeyHeader(name="X-API-Key"))
) -> bool:
    """
    Check if the request is within rate limits.
    Uses a sliding window rate limiter implemented with Redis.
    """
    try:
        # Check if Redis is available
        if redis_client is None:
            logging.warning("Redis is not available, skipping rate limiting.")
            return True
            
        # Get user's rate limit
        rate_limit = await get_user_rate_limit(api_key)
        
        # Create a unique key for this user's rate limit
        key = f"rate_limit:{api_key}"
        
        # Get the current timestamp
        now = int(time.time())
        
        # Clean up old requests (older than 1 minute)
        redis_client.zremrangebyscore(key, 0, now - 60)
        
        # Count recent requests
        recent_requests = redis_client.zcard(key)
        
        if recent_requests >= rate_limit:
            logging.warning(f"Rate limit exceeded for API key: {api_key}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add this request to the sorted set with current timestamp
        redis_client.zadd(key, {str(now): now})
        
        # Set expiration on the key (cleanup)
        redis_client.expire(key, 60)
        
        return True
        
    except redis.RedisError as e:
        # If Redis is unavailable, log the error and allow the request
        logging.error(f"Redis error in rate limiter: {str(e)}")
        return True
    except Exception as e:
        # Log other unexpected errors but allow the request to proceed
        logging.error(f"Unexpected error in rate limiter: {str(e)}")
        return True
