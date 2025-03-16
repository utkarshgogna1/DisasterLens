#!/bin/bash

# Exit on error
set -e

echo "Preparing DisasterLens for Render deployment..."

# Check if render-cli is installed
if ! command -v render &> /dev/null; then
    echo "render-cli is not installed. You can deploy manually by following the instructions in RENDER.md."
    echo "To install render-cli, run: npm install -g @render/cli"
    exit 1
fi

# Login to Render if not already logged in
render whoami || render login

# Deploy using render.yaml
echo "Deploying DisasterLens to Render..."
render blueprint apply

echo "Deployment initiated! Check the Render dashboard for progress."
echo "Your application will be available at: https://disasterlens-api.onrender.com"
echo ""
echo "If you encounter any issues, try the alternative deployment method in RENDER.md." 