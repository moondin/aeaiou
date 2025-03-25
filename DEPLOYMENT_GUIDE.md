# Deployment Guide for aeaiou.com

This guide outlines the complete process for deploying the aeaiou-api to aeaiou.com.

## Prerequisites

- A server with domain name 'aeaiou.com' pointed to it
- SSH access to the server
- Docker and Docker Compose installed on the server
- Replicate API token for image generation
- AWS account with S3 access (if using S3 storage)

## Deployment Steps

### 1. Prepare the Local Package

```bash
# Initialize git repository (if not already done)
git init

# Add all files to git
git add .

# Commit changes
git commit -m "Prepare for deployment to aeaiou.com"
```

### 2. Configure Environment Variables

Create a `.env` file with your production credentials:

```
# API Configuration
SECRET_KEY=your_secure_random_string_here
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["https://aeaiou.com", "https://www.aeaiou.com"]
RATE_LIMIT_PER_MINUTE=60

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Replicate API
REPLICATE_API_TOKEN=your_replicate_api_token_here

# Storage Configuration
STORAGE_TYPE=s3
S3_BUCKET_NAME=aeaiou-images
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
```

### 3. Transfer Files to Server

```bash
# Create deployment directory on the server (if needed)
ssh user@aeaiou.com "mkdir -p /var/www/aeaiou-api"

# Transfer files (excluding unnecessary directories)
rsync -avz --exclude '.git' --exclude 'venv' --exclude '__pycache__' . user@aeaiou.com:/var/www/aeaiou-api/
```

### 4. Set Up Server and Start Services

SSH into your server and set everything up:

```bash
# Connect to your server
ssh user@aeaiou.com

# Navigate to the application directory
cd /var/www/aeaiou-api

# Create directories for certbot (SSL certificates)
mkdir -p certbot/conf certbot/www

# Start the services using the production docker-compose file
docker-compose -f docker-compose.prod.yml up -d

# Initialize SSL certificates
docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email admin@aeaiou.com --agree-tos --no-eff-email -d aeaiou.com -d www.aeaiou.com

# Restart nginx to apply SSL certificates
docker-compose -f docker-compose.prod.yml restart nginx
```

### 5. Verify Deployment

- Check if the services are running: `docker-compose -f docker-compose.prod.yml ps`
- View logs: `docker-compose -f docker-compose.prod.yml logs -f api`
- Test the API: `curl https://aeaiou.com/api/v1/health`

### 6. Set Up Domain and DNS

Ensure your domain has the following DNS records:

- A record: `aeaiou.com` → Your server IP
- A record: `www.aeaiou.com` → Your server IP

### 7. Maintenance and Updates

To update the application:

```bash
# Pull the latest code (if using git)
git pull

# Or upload new files via rsync
rsync -avz --exclude '.git' --exclude 'venv' --exclude '__pycache__' . user@aeaiou.com:/var/www/aeaiou-api/

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 8. Troubleshooting

- Check logs: `docker-compose -f docker-compose.prod.yml logs -f api nginx redis`
- Check if the containers are running: `docker ps`
- Check Redis connectivity: `docker exec -it aeaiou-api_redis_1 redis-cli ping`

## Backup Strategy

Set up regular backups of:

1. Redis data: `/var/www/aeaiou-api/redis-data`
2. SSL certificates: `/var/www/aeaiou-api/certbot/conf`
3. Local storage (if used): `/var/www/aeaiou-api/storage`

## Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Regularly update Docker images for security patches
- Set up a firewall allowing only ports 80 and 443
- Configure AWS IAM permissions with the principle of least privilege
- Implement rate limiting to prevent abuse
- Set up monitoring and alerts for unusual activity

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Docker Documentation: https://docs.docker.com/
- Nginx Documentation: https://nginx.org/en/docs/
- Certbot Documentation: https://certbot.eff.org/docs/
