from fastapi import APIRouter
from app.api.v1.endpoints import generation, images, status

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(generation.router, prefix="/generate", tags=["generation"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
