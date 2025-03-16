#!/bin/bash

# Exit on error
set -e

echo "Testing DisasterLens with Gunicorn (Render configuration)..."

# Install Gunicorn if not already installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing Gunicorn..."
    pip install gunicorn
fi

# Stop any running instances
echo "Stopping any running instances..."
pkill -f "gunicorn.*src.api.app:app" || true
pkill -f "gunicorn.*wsgi:app" || true

# Test the direct module path (as in render.yaml)
echo "Testing direct module path: gunicorn src.api.app:app"
PYTHONPATH=. gunicorn src.api.app:app --bind 0.0.0.0:5001 --timeout 5 --log-level debug &
DIRECT_PID=$!

# Wait a moment
sleep 3

# Check if the process is still running
if kill -0 $DIRECT_PID 2>/dev/null; then
    echo "✅ Direct module path works! Process is running."
    echo "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:5001/health)
    if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        echo "✅ Health endpoint works!"
        
        echo "Testing disaster types endpoint..."
        DISASTER_TYPES_RESPONSE=$(curl -s http://localhost:5001/api/disaster_types)
        if [[ "$DISASTER_TYPES_RESPONSE" == *"flood"* ]]; then
            echo "✅ Disaster types endpoint works!"
        else
            echo "❌ Disaster types endpoint failed: $DISASTER_TYPES_RESPONSE"
        fi
    else
        echo "❌ Health endpoint failed: $HEALTH_RESPONSE"
    fi
    kill $DIRECT_PID
else
    echo "❌ Direct module path failed. Process exited."
fi

# Wait a moment
sleep 2

# Test the wsgi.py approach (as in render-alt.yaml)
echo "Testing wsgi.py approach: gunicorn wsgi:app"
PYTHONPATH=. gunicorn wsgi:app --bind 0.0.0.0:5001 --timeout 5 --log-level debug &
WSGI_PID=$!

# Wait a moment
sleep 3

# Check if the process is still running
if kill -0 $WSGI_PID 2>/dev/null; then
    echo "✅ wsgi.py approach works! Process is running."
    echo "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:5001/health)
    if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        echo "✅ Health endpoint works!"
        
        echo "Testing disaster types endpoint..."
        DISASTER_TYPES_RESPONSE=$(curl -s http://localhost:5001/api/disaster_types)
        if [[ "$DISASTER_TYPES_RESPONSE" == *"flood"* ]]; then
            echo "✅ Disaster types endpoint works!"
        else
            echo "❌ Disaster types endpoint failed: $DISASTER_TYPES_RESPONSE"
        fi
    else
        echo "❌ Health endpoint failed: $HEALTH_RESPONSE"
    fi
    kill $WSGI_PID
else
    echo "❌ wsgi.py approach failed. Process exited."
fi

echo "Test completed!" 