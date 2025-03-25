#!/bin/bash
# Deployment script for aeaiou-api to aeaiou.com

# Exit on error
set -e

echo "Starting deployment process for aeaiou-api to aeaiou.com..."

# Step 1: Package the application
echo "Creating deployment package..."
git add .
git commit -m "Prepare for deployment to aeaiou.com"

# Step 2: Set up environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# API Configuration
SECRET_KEY=your_secret_key_here
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["*"]
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
EOL
    echo ".env file created. Please edit it with your actual credentials."
    exit 1
else
    echo ".env file already exists."
fi

# Step 3: Deploy to server
echo "Deploying to aeaiou.com..."
echo "This step would typically involve:"
echo "1. Transferring files to the server (rsync, scp, etc.)"
echo "2. SSH into the server"
echo "3. Navigate to the deployment directory"
echo "4. Pull the latest changes"
echo "5. Restart the services"

# Example SSH command (commented out - replace with actual deployment)
# ssh user@aeaiou.com "cd /path/to/app && docker-compose down && docker-compose up -d"

echo ""
echo "============================================="
echo "Manual deployment steps for aeaiou.com:"
echo "============================================="
echo "1. Transfer the entire project directory to your server:"
echo "   rsync -avz --exclude '.git' --exclude 'venv' . user@aeaiou.com:/path/to/deployment/"
echo ""
echo "2. SSH into your server:"
echo "   ssh user@aeaiou.com"
echo ""
echo "3. Navigate to the deployment directory:"
echo "   cd /path/to/deployment"
echo ""
echo "4. Edit the .env file with production credentials:"
echo "   nano .env"
echo ""
echo "5. Ensure Docker and Docker Compose are installed"
echo ""
echo "6. Start the services:"
echo "   docker-compose up -d"
echo ""
echo "7. Set up a reverse proxy (Nginx) to map aeaiou.com to the API service"
echo "   - Create an Nginx configuration in /etc/nginx/sites-available/"
echo "   - Enable the site and restart Nginx"
echo ""
echo "8. Set up SSL with Let's Encrypt:"
echo "   certbot --nginx -d aeaiou.com"
echo ""
echo "Deployment manual instructions generated. Update with actual server details before use."
