#!/bin/bash

# Exit on error
set -e

echo "Deploying DisasterLens..."

# Pull latest changes if in a git repository
if [ -d .git ]; then
    echo "Pulling latest changes..."
    git pull
fi

# Install or update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing Gunicorn..."
    pip install gunicorn
fi

# Stop any running instances
echo "Stopping any running instances..."
pkill -f "gunicorn.*src.api.app:app" || true

# Start the application with Gunicorn
echo "Starting DisasterLens with Gunicorn..."
gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 --log-file logs/gunicorn.log --log-level info --daemon src.api.app:app

echo "DisasterLens deployed successfully! Running on http://localhost:5001" 