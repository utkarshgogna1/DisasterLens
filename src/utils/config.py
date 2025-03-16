"""
Configuration utilities for DisasterLens.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = os.path.join(ROOT_DIR, os.getenv("DATA_DIR", "data"))
MODEL_CACHE_DIR = os.path.join(ROOT_DIR, os.getenv("MODEL_CACHE_DIR", "models/cache"))

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# API Keys
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Default configuration
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "Kathmandu")
DEFAULT_DISASTER_TYPE = os.getenv("DEFAULT_DISASTER_TYPE", "flood")

# Flask configuration
FLASK_APP = os.getenv("FLASK_APP", "src.api.app")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1")
FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT", "5000"))
FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")

def get_config() -> Dict[str, Any]:
    """
    Get the configuration as a dictionary.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    return {
        "ROOT_DIR": str(ROOT_DIR),
        "DATA_DIR": DATA_DIR,
        "MODEL_CACHE_DIR": MODEL_CACHE_DIR,
        "OPENWEATHERMAP_API_KEY": OPENWEATHERMAP_API_KEY,
        "TWITTER_API_KEY": TWITTER_API_KEY,
        "DEFAULT_REGION": DEFAULT_REGION,
        "DEFAULT_DISASTER_TYPE": DEFAULT_DISASTER_TYPE,
        "FLASK_APP": FLASK_APP,
        "FLASK_ENV": FLASK_ENV,
        "FLASK_DEBUG": FLASK_DEBUG,
        "FLASK_RUN_PORT": FLASK_RUN_PORT,
        "FLASK_RUN_HOST": FLASK_RUN_HOST,
    }

def validate_config() -> bool:
    """
    Validate that all required configuration variables are set.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    required_vars = ["OPENWEATHERMAP_API_KEY"]
    
    for var in required_vars:
        if not os.getenv(var):
            print(f"Error: Required environment variable {var} is not set.")
            return False
    
    return True

def get_api_key(service: str) -> Optional[str]:
    """
    Get the API key for a specific service.
    
    Args:
        service (str): Service name (e.g., 'openweathermap', 'twitter')
    
    Returns:
        Optional[str]: API key if available, None otherwise
    """
    if service.lower() == "openweathermap":
        return OPENWEATHERMAP_API_KEY
    elif service.lower() == "twitter":
        return TWITTER_API_KEY
    else:
        return None 