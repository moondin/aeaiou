#!/usr/bin/env bash
# build.sh - Build script for Render.com deployment

set -o errexit
set -o pipefail
set -o nounset

# Create necessary directories for storage
mkdir -p storage/images storage/metadata

# Install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt

# Print message to confirm build completed
echo "Build completed successfully!"
