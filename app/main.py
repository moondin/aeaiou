from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from app.api.v1.api import api_router
from app.core.config import settings
from app.services.queue_manager import start_queue_cleanup_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("aeaiou-api")

app = FastAPI(
    title="aeaiou API",
    description="AI Image Generation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting aeaiou API...")
    
    # Start the queue cleanup task
    await start_queue_cleanup_task()
    logger.info("Queue cleanup task started")

@app.get("/")
async def root():
    """Root endpoint to check if API is running."""
    return {"message": "Welcome to aeaiou AI Image Generation API", "status": "operational"}
