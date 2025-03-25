#!/usr/bin/env python
"""
aeaiou API Test Client

This script tests the functionality of the aeaiou API running at aeaiou.com.
Run this after deployment to verify that all endpoints are working correctly.
"""

import requests
import json
import time
import argparse
import sys
from datetime import datetime

class AeaiouClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self):
        """Test the health check endpoint"""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        return response.json()
    
    def generate_image(self, prompt, width=512, height=512):
        """Generate an image using the API"""
        url = f"{self.base_url}/api/v1/generate"
        payload = {
            "prompt": prompt,
            "width": width,
            "height": height
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    
    def check_status(self, job_id):
        """Check the status of a generation job"""
        url = f"{self.base_url}/api/v1/status/{job_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=120):
        """Wait for a job to complete with timeout"""
        start_time = time.time()
        print(f"Waiting for job {job_id} to complete...")
        
        while time.time() - start_time < timeout:
            status = self.check_status(job_id)
            if status["status"] in ["completed", "failed"]:
                return status
            
            print(f"Status: {status['status']}, Progress: {status.get('progress', 'N/A')}%")
            time.sleep(5)
        
        return {"status": "timeout", "message": f"Job took longer than {timeout} seconds"}
    
    def get_image_metadata(self, image_id):
        """Get metadata for an image"""
        url = f"{self.base_url}/api/v1/images/{image_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def run_full_test(self, prompt="A beautiful landscape with mountains"):
        """Run a full test of the API workflow"""
        print(f"\n{'='*50}")
        print(f"AEAIOU API TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        # Step 1: Check API health
        print("\n1. Testing health endpoint...")
        try:
            health = self.health_check()
            print(f"Health check: {json.dumps(health, indent=2)}")
            if health.get("status") != "healthy":
                print("WARNING: API health check did not return 'healthy' status")
        except Exception as e:
            print(f"ERROR: Health check failed: {str(e)}")
            return False
        
        # Step 2: Generate an image
        print("\n2. Testing image generation...")
        try:
            generation = self.generate_image(prompt)
            print(f"Generation response: {json.dumps(generation, indent=2)}")
            job_id = generation.get("job_id")
            if not job_id:
                print("ERROR: No job_id returned from generation request")
                return False
        except Exception as e:
            print(f"ERROR: Image generation failed: {str(e)}")
            return False
        
        # Step 3: Wait for the job to complete
        print("\n3. Checking job status...")
        try:
            result = self.wait_for_completion(job_id)
            print(f"Final status: {json.dumps(result, indent=2)}")
            
            if result["status"] == "failed":
                print(f"ERROR: Job failed: {result.get('message', 'No error message')}")
                return False
            
            if result["status"] == "timeout":
                print("ERROR: Job timed out, but may still complete")
                return False
            
            image_id = result.get("image_id")
            if not image_id:
                print("ERROR: No image_id in completed job")
                return False
        except Exception as e:
            print(f"ERROR: Status check failed: {str(e)}")
            return False
        
        # Step 4: Get image metadata
        print("\n4. Getting image metadata...")
        try:
            metadata = self.get_image_metadata(image_id)
            print(f"Image metadata: {json.dumps(metadata, indent=2)}")
            
            if not metadata.get("url"):
                print("ERROR: No URL in image metadata")
                return False
        except Exception as e:
            print(f"ERROR: Failed to get image metadata: {str(e)}")
            return False
        
        print("\n✅ All tests passed! The API is working correctly.")
        return True

def main():
    parser = argparse.ArgumentParser(description="Test the aeaiou API")
    parser.add_argument("--url", default="https://aeaiou.com", help="Base URL of the API")
    parser.add_argument("--api-key", required=True, help="Your API key")
    parser.add_argument("--prompt", default="A beautiful landscape with mountains", help="Prompt for image generation")
    
    args = parser.parse_args()
    
    client = AeaiouClient(args.url, args.api_key)
    success = client.run_full_test(args.prompt)
    
    if not success:
        print("\n❌ Test failed. Please check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
