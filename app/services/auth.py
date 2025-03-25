import secrets
import logging
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from datetime import datetime, timedelta
import hmac
import hashlib

from app.core.config import settings

# In-memory API key store (replace with database in production)
API_KEYS: Dict[str, Dict] = {
    "test_key": {
        "user_id": "test_user",
        "rate_limit": 100,  # requests per minute
        "created_at": datetime.utcnow(),
    }
}

api_key_header = APIKeyHeader(name="X-API-Key")

class AuthError(Exception):
    """Custom exception for authentication errors"""
    pass

async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verify that the API key is valid and return the associated user ID.
    Raises HTTPException if the API key is invalid.
    """
    try:
        if api_key not in API_KEYS:
            logging.warning(f"Invalid API key attempt: {api_key[:5]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        user_id = API_KEYS[api_key]["user_id"]
        logging.debug(f"Successful API key verification for user: {user_id}")
        return user_id
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logging.error(f"Unexpected error in API key verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )

async def get_user_rate_limit(api_key: str) -> int:
    """
    Get the rate limit for a user based on their API key.
    Returns the default rate limit if the API key is not found.
    """
    try:
        if api_key not in API_KEYS:
            # Use default rate limit for unknown API keys
            return settings.RATE_LIMIT_PER_MINUTE
        
        return API_KEYS[api_key].get("rate_limit", settings.RATE_LIMIT_PER_MINUTE)
        
    except Exception as e:
        logging.error(f"Error getting user rate limit: {str(e)}")
        # Fall back to default rate limit in case of error
        return settings.RATE_LIMIT_PER_MINUTE

async def create_api_key(user_id: str, rate_limit: Optional[int] = None) -> str:
    """
    Create a new API key for a user.
    In production, this would create an entry in a database.
    """
    try:
        # Generate a secure API key
        timestamp = datetime.utcnow().timestamp()
        key_base = f"{user_id}:{timestamp}"
        api_key = hmac.new(
            settings.SECRET_KEY.encode(),
            key_base.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        # Store in our mock database
        API_KEYS[api_key] = {
            "user_id": user_id,
            "rate_limit": rate_limit or settings.RATE_LIMIT_PER_MINUTE,
            "created_at": datetime.utcnow(),
        }
        
        logging.info(f"Created new API key for user: {user_id}")
        return api_key
        
    except Exception as e:
        logging.error(f"Failed to create API key: {str(e)}")
        raise AuthError(f"Failed to create API key: {str(e)}")

async def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key.
    In production, this would delete or invalidate the key in a database.
    """
    try:
        if api_key in API_KEYS:
            user_id = API_KEYS[api_key]["user_id"]
            del API_KEYS[api_key]
            logging.info(f"Revoked API key for user: {user_id}")
            return True
        return False
        
    except Exception as e:
        logging.error(f"Failed to revoke API key: {str(e)}")
        raise AuthError(f"Failed to revoke API key: {str(e)}")

async def get_user_api_keys(user_id: str) -> Dict[str, Any]:
    """
    Get all API keys for a user.
    In production, this would query a database.
    """
    try:
        keys = {}
        for key, data in API_KEYS.items():
            if data["user_id"] == user_id:
                keys[key] = data
        
        return keys
        
    except Exception as e:
        logging.error(f"Failed to get user API keys: {str(e)}")
        raise AuthError(f"Failed to get user API keys: {str(e)}")
