"""
WSGI entry point for the DisasterLens application.
This file helps Render and other WSGI servers find and run the Flask application.
"""

from src.api.app import app

if __name__ == "__main__":
    app.run() 