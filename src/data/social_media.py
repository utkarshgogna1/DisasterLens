"""
Social media data fetching and analysis module for DisasterLens.

This module provides functions to fetch and analyze social media data,
particularly from Twitter/X, to detect disaster-related signals.
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import requests
from requests_oauthlib import OAuth1

from src.utils.config import get_api_key, DATA_DIR
from src.utils.logger import logger

# Cache directory for social media data
SOCIAL_CACHE_DIR = os.path.join(DATA_DIR, "social_cache")
os.makedirs(SOCIAL_CACHE_DIR, exist_ok=True)

# Disaster-related keywords for filtering tweets
DISASTER_KEYWORDS = [
    "flood", "flooding", "flooded",
    "earthquake", "quake", "tremor",
    "hurricane", "typhoon", "cyclone",
    "wildfire", "fire", "burning",
    "landslide", "mudslide",
    "tsunami", "tidal wave",
    "drought",
    "tornado", "twister",
    "avalanche",
    "volcanic eruption", "volcano",
    "help", "emergency", "disaster",
    "rescue", "evacuate", "evacuation",
    "trapped", "stranded",
    "damage", "destroyed", "collapsed",
]

# Urgency-related keywords
URGENCY_KEYWORDS = [
    "urgent", "emergency", "immediately",
    "help", "sos", "mayday",
    "trapped", "stranded", "stuck",
    "need assistance", "need help",
    "life threatening", "critical",
    "dying", "death", "dead",
    "injured", "hurt", "wounded",
    "missing", "lost",
    "evacuate", "evacuating", "evacuation",
    "rescue", "save",
]


class SocialMediaFetcher:
    """
    Class for fetching and analyzing social media data.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Initialize the SocialMediaFetcher.
        
        Args:
            api_key (Optional[str]): Twitter API key
            api_secret (Optional[str]): Twitter API secret
            access_token (Optional[str]): Twitter access token
            access_secret (Optional[str]): Twitter access token secret
            use_cache (bool): Whether to use cached data when available
        """
        # Get API credentials from environment if not provided
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        
        self.use_cache = use_cache
        self.auth = None
        
        # Check if we have valid credentials
        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            self.auth = OAuth1(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret
            )
        else:
            logger.warning("Twitter API credentials not complete. Social media fetching will be limited.")
    
    def search_tweets(
        self,
        query: str,
        location: Optional[str] = None,
        radius: str = "50km",
        count: int = 100,
        result_type: str = "recent",
        lang: str = "en",
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets matching a query.
        
        Args:
            query (str): Search query
            location (Optional[str]): Location as "latitude,longitude"
            radius (str): Radius around location (e.g., "50km")
            count (int): Number of tweets to retrieve (max 100)
            result_type (str): Type of results ("recent", "popular", or "mixed")
            lang (str): Language code
        
        Returns:
            List[Dict[str, Any]]: List of tweet data
        
        Raises:
            ValueError: If the API credentials are not set
            requests.RequestException: If the API request fails
        """
        if not self.auth:
            logger.warning("Twitter API credentials not set. Using mock data.")
            return self._get_mock_tweets(query, location, count)
        
        # Build the search query
        search_query = query
        
        # Add location if provided
        geo_params = {}
        if location:
            geo_params = {
                "geocode": f"{location},{radius}",
            }
        
        # Set up parameters
        params = {
            "q": search_query,
            "count": min(count, 100),
            "result_type": result_type,
            "lang": lang,
            "tweet_mode": "extended",  # Get full text
            **geo_params,
        }
        
        # Check cache first if enabled
        if self.use_cache:
            cache_key = f"tweets_{query.replace(' ', '_')}_{location or 'noloc'}_{count}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Make API request
        url = "https://api.twitter.com/1.1/search/tweets.json"
        logger.info(f"Searching tweets for query: {query}")
        
        try:
            response = requests.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            
            # Extract tweets
            tweets = data.get("statuses", [])
            
            # Cache the result
            if self.use_cache:
                self._save_to_cache(cache_key, tweets)
            
            return tweets
        
        except requests.RequestException as e:
            logger.error(f"Error fetching tweets: {e}")
            # Fall back to mock data
            return self._get_mock_tweets(query, location, count)
    
    def search_disaster_tweets(
        self,
        disaster_type: str,
        location: Optional[str] = None,
        radius: str = "50km",
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets related to a specific disaster type.
        
        Args:
            disaster_type (str): Type of disaster (e.g., "flood", "earthquake")
            location (Optional[str]): Location as "latitude,longitude"
            radius (str): Radius around location
            count (int): Number of tweets to retrieve
        
        Returns:
            List[Dict[str, Any]]: List of tweet data
        """
        # Build query with disaster type and related keywords
        query = disaster_type
        if disaster_type.lower() in ["flood", "flooding"]:
            query += " OR water OR submerged OR inundated"
        elif disaster_type.lower() in ["earthquake", "quake"]:
            query += " OR tremor OR shaking OR aftershock"
        elif disaster_type.lower() in ["hurricane", "typhoon", "cyclone"]:
            query += " OR storm OR wind OR evacuation"
        
        # Add common disaster-related terms
        query += " AND (emergency OR help OR rescue OR trapped OR stranded OR damage)"
        
        return self.search_tweets(query, location, radius, count)
    
    def analyze_tweet_urgency(self, tweet: Dict[str, Any]) -> float:
        """
        Analyze the urgency level of a tweet.
        
        Args:
            tweet (Dict[str, Any]): Tweet data
        
        Returns:
            float: Urgency score (0-1)
        """
        # Get the tweet text
        text = tweet.get("full_text", tweet.get("text", "")).lower()
        
        # Count urgency keywords
        urgency_count = sum(1 for keyword in URGENCY_KEYWORDS if keyword.lower() in text)
        
        # Check for specific urgent patterns
        if re.search(r"(help|sos|emergency).*?(urgent|immediately|now)", text, re.I):
            urgency_count += 2
        
        if re.search(r"(trapped|stranded).*?(need|require).*?(help|assistance|rescue)", text, re.I):
            urgency_count += 2
        
        if re.search(r"(life|lives).*?(risk|danger|threatening)", text, re.I):
            urgency_count += 2
        
        # Normalize to 0-1 range
        urgency_score = min(urgency_count / 10, 1.0)
        
        return urgency_score
    
    def extract_location_from_tweet(self, tweet: Dict[str, Any]) -> Optional[str]:
        """
        Extract location information from a tweet.
        
        Args:
            tweet (Dict[str, Any]): Tweet data
        
        Returns:
            Optional[str]: Location string or None if not found
        """
        # Check for geo coordinates
        if tweet.get("geo") and tweet["geo"].get("coordinates"):
            coords = tweet["geo"]["coordinates"]
            return f"{coords[0]},{coords[1]}"
        
        # Check for place information
        if tweet.get("place"):
            place = tweet["place"]
            if place.get("full_name"):
                return place["full_name"]
        
        # Check for user location
        if tweet.get("user", {}).get("location"):
            return tweet["user"]["location"]
        
        # Try to extract location from text using regex
        text = tweet.get("full_text", tweet.get("text", ""))
        
        # Look for "in [Location]" pattern
        location_match = re.search(r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
        if location_match:
            return location_match.group(1)
        
        # Look for "at [Location]" pattern
        location_match = re.search(r"at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
        if location_match:
            return location_match.group(1)
        
        return None
    
    def get_disaster_signals(
        self,
        location: str,
        disaster_type: str = "flood",
        count: int = 100,
        min_urgency: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Get disaster signals from social media for a location.
        
        Args:
            location (str): Location name or coordinates
            disaster_type (str): Type of disaster
            count (int): Number of tweets to analyze
            min_urgency (float): Minimum urgency score to include
        
        Returns:
            List[Dict[str, Any]]: List of disaster signals with urgency scores
        """
        # Search for disaster-related tweets
        tweets = self.search_disaster_tweets(disaster_type, location, count=count)
        
        # Analyze urgency and filter by minimum score
        signals = []
        
        for tweet in tweets:
            urgency = self.analyze_tweet_urgency(tweet)
            
            if urgency >= min_urgency:
                # Extract text and location
                text = tweet.get("full_text", tweet.get("text", ""))
                tweet_location = self.extract_location_from_tweet(tweet) or location
                
                # Create signal object
                signal = {
                    "text": text,
                    "location": tweet_location,
                    "urgency": urgency,
                    "timestamp": tweet.get("created_at"),
                    "user": tweet.get("user", {}).get("screen_name"),
                    "disaster_type": disaster_type,
                    "source": "twitter",
                }
                
                signals.append(signal)
        
        # Sort by urgency (highest first)
        signals.sort(key=lambda x: x["urgency"], reverse=True)
        
        return signals
    
    def _get_cache_path(self, cache_key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            cache_key (str): Cache key
        
        Returns:
            str: Cache file path
        """
        return os.path.join(SOCIAL_CACHE_DIR, f"{cache_key}.json")
    
    def _get_from_cache(self, cache_key: str, max_age_hours: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        Get data from cache if available and not expired.
        
        Args:
            cache_key (str): Cache key
            max_age_hours (int): Maximum age of cache in hours
        
        Returns:
            Optional[List[Dict[str, Any]]]: Cached data or None if not available
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
    
    def _save_to_cache(self, cache_key: str, data: List[Dict[str, Any]]) -> None:
        """
        Save data to cache.
        
        Args:
            cache_key (str): Cache key
            data (List[Dict[str, Any]]): Data to cache
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
            logger.debug(f"Saved data to cache: {cache_key}")
        except IOError as e:
            logger.warning(f"Error saving to cache: {e}")
    
    def _get_mock_tweets(
        self,
        query: str,
        location: Optional[str] = None,
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate mock tweets for testing when API is not available.
        
        Args:
            query (str): Search query
            location (Optional[str]): Location
            count (int): Number of mock tweets to generate
        
        Returns:
            List[Dict[str, Any]]: List of mock tweet data
        """
        logger.info("Generating mock tweets for testing")
        
        # Extract disaster type from query
        disaster_type = "disaster"
        for keyword in DISASTER_KEYWORDS:
            if keyword in query.lower():
                disaster_type = keyword
                break
        
        # Use location or default
        loc = location or "Unknown Location"
        if "," in loc:  # If it's coordinates, use a generic name
            loc = "the affected area"
        
        # Generate mock tweets
        mock_tweets = []
        
        # High urgency tweets
        high_urgency_templates = [
            f"URGENT! Need immediate help due to {disaster_type} in {loc}. People are trapped! #emergency #disaster",
            f"SOS! {disaster_type.title()} has hit {loc}. We need rescue teams ASAP! Many injured. #emergency",
            f"HELP! {disaster_type.title()} situation critical in {loc}. Families stranded without food or water. #disaster",
            f"Emergency! {disaster_type.title()} has destroyed homes in {loc}. People missing, need immediate assistance!",
            f"Mayday! {disaster_type.title()} has cut off {loc} from all supplies. Children and elderly at risk!",
        ]
        
        # Medium urgency tweets
        medium_urgency_templates = [
            f"The {disaster_type} in {loc} is getting worse. Roads blocked, need help soon. #disaster",
            f"{disaster_type.title()} update: Situation deteriorating in {loc}. Supplies running low. #emergency",
            f"Several families affected by {disaster_type} in {loc}. Need assistance with temporary shelter.",
            f"{loc} hit by {disaster_type}. Local resources overwhelmed, requesting additional support.",
            f"The {disaster_type} has caused significant damage in {loc}. Community center being used as shelter.",
        ]
        
        # Low urgency tweets
        low_urgency_templates = [
            f"{disaster_type.title()} warning for {loc}. Residents advised to prepare. #safety",
            f"Monitoring the {disaster_type} situation in {loc}. No major incidents reported yet.",
            f"Weather service predicts {disaster_type} conditions may affect {loc} in coming days.",
            f"Local authorities preparing for potential {disaster_type} in {loc}. Stay tuned for updates.",
            f"Information session about {disaster_type} preparedness tonight at {loc} community center.",
        ]
        
        # Combine templates based on count
        templates = []
        if count <= 5:
            templates = high_urgency_templates[:count]
        elif count <= 10:
            templates = high_urgency_templates + medium_urgency_templates[:count-5]
        else:
            templates = high_urgency_templates + medium_urgency_templates
            templates += low_urgency_templates * ((count - len(templates)) // 5 + 1)
            templates = templates[:count]
        
        # Generate tweets from templates
        for i, template in enumerate(templates[:count]):
            # Create timestamp (more recent for higher urgency)
            hours_ago = i // 2  # First tweets more recent
            timestamp = datetime.now() - timedelta(hours=hours_ago)
            created_at = timestamp.strftime("%a %b %d %H:%M:%S +0000 %Y")
            
            tweet = {
                "id": 1000000000 + i,
                "id_str": str(1000000000 + i),
                "full_text": template,
                "text": template[:140] + "..." if len(template) > 140 else template,
                "created_at": created_at,
                "user": {
                    "id": 10000 + i,
                    "id_str": str(10000 + i),
                    "name": f"User {i+1}",
                    "screen_name": f"user{i+1}",
                    "location": loc,
                },
                "geo": None,
                "coordinates": None,
                "place": {
                    "full_name": loc,
                },
                "entities": {
                    "hashtags": [
                        {"text": "disaster"} if "disaster" in template else {"text": "emergency"}
                    ],
                },
                "retweet_count": i % 10,
                "favorite_count": i % 5,
                "lang": "en",
            }
            
            mock_tweets.append(tweet)
        
        return mock_tweets


def get_social_media_signals(location: str, disaster_type: str = "flood") -> List[Dict[str, Any]]:
    """
    Get social media signals for a location and disaster type.
    
    Args:
        location (str): Location name or coordinates
        disaster_type (str): Type of disaster
    
    Returns:
        List[Dict[str, Any]]: List of social media signals
    """
    fetcher = SocialMediaFetcher()
    return fetcher.get_disaster_signals(location, disaster_type) 