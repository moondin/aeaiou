# Deploying aeaiou API to Render.com

This guide will walk you through deploying the aeaiou API to Render.com with a custom domain (aeaiou.com).

## Prerequisites

1. A [Render.com](https://render.com) account
2. Your GitHub repository (https://github.com/moondin/aeaiou)
3. Domain name aeaiou.com registered and accessible to you
4. AWS account with S3 bucket for image storage
5. Replicate API token for AI image generation

## Setup Steps

### 1. Create a New Web Service on Render

1. Log in to your Render.com dashboard
2. Click on "New +" in the top right corner
3. Select "Blueprint" as your deployment option
4. Connect your GitHub repository (https://github.com/moondin/aeaiou) 
5. Render will automatically detect the `render.yaml` file in your repository
6. Click "Apply Blueprint"

### 2. Configure Environment Variables

After your blueprint is created, you'll need to configure environment variables for each service:

1. Click on the aeaiou-api service
2. Go to the "Environment" tab
3. Add the following environment variables:
   - `SECRET_KEY`: A secure random string for app security
   - `REPLICATE_API_TOKEN`: Your Replicate API token
   - `S3_BUCKET_NAME`: Your AWS S3 bucket name
   - `S3_REGION`: AWS region for your S3 bucket
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 3. Set Up Custom Domain

1. In your aeaiou-api service, go to the "Settings" tab
2. Scroll down to "Custom Domain"
3. Click "Add Custom Domain"
4. Enter your domain: `aeaiou.com`
5. Follow the instructions to verify domain ownership:
   - Update your DNS settings at your domain registrar
   - Add the specified CNAME or A records
   - Wait for DNS propagation (can take up to 48 hours)

### 4. Monitor Deployment

1. Go to the "Events" tab for your aeaiou-api service
2. Wait for the deployment to complete
3. Check for any errors in the build or deployment logs

## Testing Your Deployment

Once your deployment is complete:

1. Visit `https://aeaiou.com/api/v1/health` to verify the API is running
2. Test the API using the test client:
   ```
   python test_client.py --api-key your_api_key --url https://aeaiou.com
   ```

## Troubleshooting

If you encounter issues:

1. Check the deployment logs in the "Logs" tab of your Render service
2. Ensure all environment variables are correctly set
3. Verify your domain DNS settings are correct
4. Check that your AWS S3 bucket is properly configured for public read access

## Updating Your Deployment

Render automatically deploys when you push to your GitHub repository. To update your API:

1. Make changes to your code locally
2. Commit and push to GitHub
3. Render will automatically detect the changes and deploy the new version
