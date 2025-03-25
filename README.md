# aeaiou AI Image Generation API

A scalable and secure RESTful API for AI image generation using Stable Diffusion.

## Features

- RESTful API design
- Asynchronous image generation with job queuing
- Rate limiting and API key authentication
- Support for both local and S3 storage
- Detailed job status tracking and error handling
- Configurable image generation parameters
- Comprehensive API documentation

## Requirements

- Python 3.8+
- Redis server
- Optional: AWS S3 bucket for cloud storage

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aeaiou-api.git
cd aeaiou-api
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
# API Configuration
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Replicate API
REPLICATE_API_TOKEN=your-replicate-api-token
REPLICATE_MODEL_VERSION=db21e94d2eda158a3bf169282768c2a61aabab93cbdd385669865480734c35ad

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional-redis-password

# Storage Configuration
STORAGE_TYPE=local  # or "s3"
S3_BUCKET_NAME=your-bucket-name  # if using S3
S3_REGION=your-region  # if using S3

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
```

## Running the API

1. Start the Redis server:
```bash
redis-server
```

2. Start the API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. API documentation can be found at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

All endpoints require an API key to be passed in the `X-API-Key` header.

### Image Generation

- `POST /api/v1/generate`
  - Generate a new image
  - Request body:
    ```json
    {
      "prompt": "A beautiful sunset over mountains",
      "width": 512,
      "height": 512,
      "num_inference_steps": 50,
      "guidance_scale": 7.5,
      "negative_prompt": "Optional text to avoid",
      "seed": null
    }
    ```

### Job Status

- `GET /api/v1/status/{job_id}`
  - Check the status of an image generation job

### Images

- `GET /api/v1/images/{image_id}`
  - Get metadata for a generated image
- `GET /api/v1/images/{image_id}/content`
  - Get the actual image file

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project uses Black for code formatting and isort for import sorting:

```bash
black .
isort .
```

## Deployment

### Deployment Status

This API is deployed automatically via GitHub Actions.

The API can be deployed using Docker:

```bash
docker build -t aeaiou-api .
docker run -p 8000:8000 aeaiou-api
```

For production deployment, consider using:
- Kubernetes for orchestration
- AWS ECS or GCP Cloud Run for container management
- CloudFront or similar CDN for image delivery
- Managed Redis service (e.g., Redis Labs, AWS ElastiCache)

## License

MIT License - see LICENSE file for details
