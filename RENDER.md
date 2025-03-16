# Deploying DisasterLens to Render

This document provides instructions for deploying the DisasterLens application to Render.

## Deployment Steps

1. Create a Render account at https://render.com/
2. Connect your GitHub repository to Render
3. Create a new Web Service
4. Use the following settings:
   - Name: disasterlens-api
   - Environment: Python
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `gunicorn src.api.app:app --bind 0.0.0.0:$PORT`
   - Health Check Path: `/health`
   - Python Version: 3.10.0
   - Environment Variables:
     - FLASK_ENV: production
     - PYTHONPATH: .

## Alternative Deployment Using wsgi.py

If you encounter module import issues, you can use the wsgi.py file:

1. Create a new Web Service
2. Use the following settings:
   - Name: disasterlens-api
   - Environment: Python
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
   - Health Check Path: `/health`
   - Python Version: 3.10.0
   - Environment Variables:
     - FLASK_ENV: production
     - PYTHONPATH: .

## Accessing the Deployed Application

Once deployed, your application will be available at:
https://disasterlens-api.onrender.com

## Troubleshooting

If you encounter any issues during deployment, check the Render logs for error messages.

Common issues:
- **Module not found errors**: Make sure the PYTHONPATH environment variable is set to `.` to include the root directory in the Python path.
- **Missing dependencies**: Make sure all required packages are listed in requirements-render.txt
- **Environment variables**: Ensure all necessary environment variables are set in the Render dashboard
- **Port configuration**: Render automatically sets the PORT environment variable, make sure your application uses it

## Local Testing

To test the application locally before deploying to Render:

```bash
# Install dependencies
pip install -r requirements-render.txt

# Run the application
FLASK_RUN_PORT=5001 gunicorn src.api.app:app --bind 0.0.0.0:5001
```

The application will be available at http://localhost:5001

Note: When deployed to Render, the application will use the PORT environment variable provided by Render, not port 5001. 