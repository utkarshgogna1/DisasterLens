"""
Weather data fetching module for DisasterLens.

This module provides functions to fetch weather data from the OpenWeatherMap API.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

import requests

from src.utils.config import get_api_key, DATA_DIR
from src.utils.logger import logger

# Cache directory for weather data
WEATHER_CACHE_DIR = os.path.join(DATA_DIR, "weather_cache")
os.makedirs(WEATHER_CACHE_DIR, exist_ok=True)


class WeatherDataFetcher:
    """
    Class for fetching weather data from OpenWeatherMap API.
    """

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialize the WeatherDataFetcher.
        
        Args:
            api_key (Optional[str]): OpenWeatherMap API key. If None, will try to get from environment.
            use_cache (bool): Whether to use cached data when available.
        """
        self.api_key = api_key or get_api_key("openweathermap")
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not found. Weather data fetching will not work.")
        
        self.use_cache = use_cache
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather data for a location.
        
        Args:
            location (str): Location name (e.g., "Kathmandu") or coordinates (e.g., "27.7172,85.3240")
        
        Returns:
            Dict[str, Any]: Weather data
        
        Raises:
            ValueError: If the API key is not set
            requests.RequestException: If the API request fails
        """
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not set")
        
        # Check if we have coordinates or a location name
        if "," in location and all(part.replace(".", "", 1).replace("-", "", 1).isdigit() 
                                for part in location.split(",")):
            lat, lon = location.split(",")
            params = {"lat": lat.strip(), "lon": lon.strip()}
        else:
            params = {"q": location}
        
        # Add API key and units
        params.update({
            "appid": self.api_key,
            "units": "metric"  # Use metric units (Celsius, meters/sec, etc.)
        })
        
        # Check cache first if enabled
        if self.use_cache:
            cache_key = f"current_{location.replace(' ', '_').lower()}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Make API request
        url = f"{self.base_url}/weather"
        logger.info(f"Fetching current weather data for {location}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            if self.use_cache:
                self._save_to_cache(cache_key, data)
            
            return data
        
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            raise
    
    def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location (str): Location name (e.g., "Kathmandu") or coordinates
            days (int): Number of days for forecast (max 5 for free tier)
        
        Returns:
            Dict[str, Any]: Forecast data
        
        Raises:
            ValueError: If the API key is not set
            requests.RequestException: If the API request fails
        """
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not set")
        
        # Ensure days is within valid range
        days = min(max(1, days), 5)
        
        # Check if we have coordinates or a location name
        if "," in location and all(part.replace(".", "", 1).replace("-", "", 1).isdigit() 
                                for part in location.split(",")):
            lat, lon = location.split(",")
            params = {"lat": lat.strip(), "lon": lon.strip()}
        else:
            params = {"q": location}
        
        # Add API key and units
        params.update({
            "appid": self.api_key,
            "units": "metric",  # Use metric units
            "cnt": days * 8,    # 8 data points per day (3-hour intervals)
        })
        
        # Check cache first if enabled
        if self.use_cache:
            cache_key = f"forecast_{location.replace(' ', '_').lower()}_{days}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Make API request
        url = f"{self.base_url}/forecast"
        logger.info(f"Fetching {days}-day forecast for {location}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            if self.use_cache:
                self._save_to_cache(cache_key, data)
            
            return data
        
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast data: {e}")
            raise
    
    def get_rainfall(self, location: str, days: int = 5) -> List[Tuple[datetime, float]]:
        """
        Get rainfall data for a location.
        
        Args:
            location (str): Location name or coordinates
            days (int): Number of days for forecast
        
        Returns:
            List[Tuple[datetime, float]]: List of (timestamp, rainfall in mm) tuples
        """
        forecast = self.get_forecast(location, days)
        rainfall_data = []
        
        for item in forecast.get("list", []):
            timestamp = datetime.fromtimestamp(item.get("dt", 0))
            rain_3h = item.get("rain", {}).get("3h", 0)  # Rain in mm for 3 hours
            rainfall_data.append((timestamp, rain_3h))
        
        return rainfall_data
    
    def get_total_rainfall(self, location: str, days: int = 5) -> float:
        """
        Get total rainfall for a location over a period.
        
        Args:
            location (str): Location name or coordinates
            days (int): Number of days for forecast
        
        Returns:
            float: Total rainfall in mm
        """
        rainfall_data = self.get_rainfall(location, days)
        return sum(rain for _, rain in rainfall_data)
    
    def get_snow(self, location: str, days: int = 5) -> List[Tuple[datetime, float]]:
        """
        Get snow data for a location.
        
        Args:
            location (str): Location name or coordinates
            days (int): Number of days for forecast
        
        Returns:
            List[Tuple[datetime, float]]: List of (timestamp, snow in mm) tuples
        """
        forecast = self.get_forecast(location, days)
        snow_data = []
        
        for item in forecast.get("list", []):
            timestamp = datetime.fromtimestamp(item.get("dt", 0))
            snow_3h = item.get("snow", {}).get("3h", 0)  # Snow in mm for 3 hours
            snow_data.append((timestamp, snow_3h))
        
        return snow_data
    
    def get_total_snow(self, location: str, days: int = 5) -> float:
        """
        Get total snow for a location over a period.
        
        Args:
            location (str): Location name or coordinates
            days (int): Number of days for forecast
        
        Returns:
            float: Total snow in mm
        """
        snow_data = self.get_snow(location, days)
        return sum(snow for _, snow in snow_data)
    
    def _get_cache_path(self, cache_key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            cache_key (str): Cache key
        
        Returns:
            str: Cache file path
        """
        return os.path.join(WEATHER_CACHE_DIR, f"{cache_key}.json")
    
    def _get_from_cache(self, cache_key: str, max_age_hours: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if available and not expired.
        
        Args:
            cache_key (str): Cache key
            max_age_hours (int): Maximum age of cache in hours
        
        Returns:
            Optional[Dict[str, Any]]: Cached data or None if not available
        """
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check if cache is expired
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            logger.debug(f"Cache expired for {cache_key} (age: {age_hours:.1f} hours)")
            return None
        
        # Load cache
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
            logger.debug(f"Using cached data for {cache_key}")
            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Save data to cache.
        
        Args:
            cache_key (str): Cache key
            data (Dict[str, Any]): Data to cache
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
            logger.debug(f"Saved data to cache: {cache_key}")
        except IOError as e:
            logger.warning(f"Error saving to cache: {e}")


def get_weather_features(location: str) -> Dict[str, float]:
    """
    Get weather features for a location.
    
    Args:
        location (str): Location name or coordinates
    
    Returns:
        Dict[str, float]: Weather features
    """
    try:
        # Initialize weather data fetcher
        fetcher = WeatherDataFetcher()
        
        # Get current weather
        current = fetcher.get_current_weather(location)
        
        # Extract basic weather data
        features = {
            "temperature": current.get("main", {}).get("temp", 0.0),
            "humidity": current.get("main", {}).get("humidity", 0.0),
            "pressure": current.get("main", {}).get("pressure", 0.0),
            "wind_speed": current.get("wind", {}).get("speed", 0.0),
        }
        
        # Get rainfall data
        try:
            rainfall_1h = current.get("rain", {}).get("1h", 0.0)
            rainfall_3h = current.get("rain", {}).get("3h", 0.0)
            
            # Get 24h and 5d rainfall from forecast
            rainfall_24h = 0.0
            rainfall_5d = 0.0
            
            try:
                rainfall_24h = sum(rain for _, rain in fetcher.get_rainfall(location, 1))
                rainfall_5d = fetcher.get_total_rainfall(location, 5)
            except Exception as e:
                logger.warning(f"Error getting rainfall forecast: {e}")
            
            features.update({
                "rainfall_1h": rainfall_1h,
                "rainfall_3h": rainfall_3h,
                "rainfall_24h": rainfall_24h,
                "rainfall_5d": rainfall_5d,
            })
        except Exception as e:
            logger.warning(f"Error getting rainfall data: {e}")
            features.update({
                "rainfall_1h": 0.0,
                "rainfall_3h": 0.0,
                "rainfall_24h": 0.0,
                "rainfall_5d": 0.0,
            })
        
        # Get snow data
        try:
            snow_1h = current.get("snow", {}).get("1h", 0.0)
            snow_3h = current.get("snow", {}).get("3h", 0.0)
            
            # Get 24h snow from forecast
            snow_24h = 0.0
            snow_5d = 0.0
            
            try:
                snow_24h = sum(snow for _, snow in fetcher.get_snow(location, 1))
                snow_5d = fetcher.get_total_snow(location, 5)
            except Exception as e:
                logger.warning(f"Error getting snow forecast: {e}")
            
            features.update({
                "snow_1h": snow_1h,
                "snow_3h": snow_3h,
                "snow_24h": snow_24h,
                "snow_5d": snow_5d,
            })
        except Exception as e:
            logger.warning(f"Error getting snow data: {e}")
            features.update({
                "snow_1h": 0.0,
                "snow_3h": 0.0,
                "snow_24h": 0.0,
                "snow_5d": 0.0,
            })
        
        # Add wind gust if available
        if "gust" in current.get("wind", {}):
            features["wind_gust"] = current["wind"]["gust"]
        
        return features
    
    except Exception as e:
        logger.error(f"Error getting weather features: {e}")
        # Return default values
        return {
            "temperature": 25.0,
            "humidity": 70.0,
            "pressure": 1013.0,
            "wind_speed": 5.0,
            "rainfall_1h": 0.0,
            "rainfall_3h": 0.0,
            "rainfall_24h": 0.0,
            "rainfall_5d": 0.0,
            "snow_1h": 0.0,
            "snow_3h": 0.0,
            "snow_24h": 0.0,
            "snow_5d": 0.0,
        } 