"""
Mock implementation of XParser for DisasterLens.

This module provides a mock implementation of the XParser class,
which is used to fetch and analyze distress signals from social media.
"""

class XParser:
    """
    Mock implementation of XParser for fetching and analyzing distress signals.
    """
    
    def __init__(self):
        """Initialize the XParser."""
        self._last_query = ""
        self._last_region = ""
        self._mock_signals = {
            "flood": [
                "Help! Our neighborhood is flooded #flood #emergency",
                "Water levels rising quickly in downtown area",
                "Need assistance, streets completely underwater"
            ],
            "tornado": [
                "Tornado just hit our area, need help",
                "House damaged by tornado, seeking shelter",
                "Trees down everywhere after tornado"
            ],
            "winter storm": [
                "Stranded in car due to snow #winterstorm",
                "No power for 2 days after ice storm",
                "Roads impassable, running low on supplies"
            ],
            "drought": [
                "Crops failing due to drought conditions #drought",
                "Water supply critically low in our town",
                "Need emergency water delivery due to drought"
            ],
            "earthquake": [
                "Felt shaking in our building! #earthquake",
                "Items fell off shelves during earthquake",
                "Minor damage to structures after tremor"
            ],
            "landslide": [
                "Small rockslide on the mountain path #landslide",
                "Some debris on the road after heavy rain",
                "Minor soil movement observed on hillside"
            ],
            "volcanic eruption": [
                "Ash falling from the sky near the volcano #eruption",
                "Authorities issued evacuation warning due to volcanic activity",
                "Smoke visible from the crater, monitoring situation"
            ],
            "wildfire": [
                "Smoke visible from our neighborhood #wildfire",
                "Evacuation orders issued for western areas",
                "Fire spreading quickly due to high winds"
            ],
            "tsunami": [
                "Coastal warning sirens activated #tsunami",
                "Water receding from shoreline, unusual pattern",
                "Small waves beginning to reach the harbor"
            ],
            "hurricane": [
                "Strong winds damaging roofs in our area #hurricane",
                "Storm surge flooding coastal roads",
                "Power outages reported across the county"
            ]
        }
        self._mock_urgency = {
            "flood": {"max_urgency": 0.75, "avg_urgency": 0.62},
            "tornado": {"max_urgency": 0.85, "avg_urgency": 0.70},
            "winter storm": {"max_urgency": 0.60, "avg_urgency": 0.45},
            "drought": {"max_urgency": 0.40, "avg_urgency": 0.37},
            "earthquake": {"max_urgency": 0.45, "avg_urgency": 0.35},
            "landslide": {"max_urgency": 0.40, "avg_urgency": 0.37},
            "volcanic eruption": {"max_urgency": 0.55, "avg_urgency": 0.42},
            "wildfire": {"max_urgency": 0.70, "avg_urgency": 0.58},
            "tsunami": {"max_urgency": 0.65, "avg_urgency": 0.50},
            "hurricane": {"max_urgency": 0.80, "avg_urgency": 0.65}
        }
        
        # Special cases for specific locations
        self._location_specific_signals = {
            "fuji": {
                "earthquake": [
                    "Felt tremors near Mount Fuji #earthquake",
                    "Minor shaking reported in Shizuoka Prefecture",
                    "Some tourists evacuated from Mount Fuji trails"
                ],
                "landslide": [
                    "Small rockfall reported on Mount Fuji trail #landslide",
                    "Minor soil movement observed on Fuji slopes after rain",
                    "Hikers advised to use caution due to loose rocks on path"
                ],
                "volcanic eruption": [
                    "Increased steam activity observed at Mount Fuji crater",
                    "Scientists monitoring volcanic activity on Fuji",
                    "Minor ash emissions reported from Mount Fuji"
                ]
            },
            "tokyo": {
                "earthquake": [
                    "Buildings swaying in Tokyo #earthquake",
                    "Train services temporarily suspended after tremor",
                    "Minor damage reported in some older buildings"
                ]
            },
            "california": {
                "wildfire": [
                    "Smoke visible from hills near California community",
                    "Evacuation warnings issued for parts of California county",
                    "Fire crews responding to wildfire in California forest"
                ],
                "drought": [
                    "Reservoir levels at historic lows in California",
                    "Water restrictions implemented across California counties",
                    "Farmers struggling with drought conditions in California"
                ],
                "tsunami": [
                    "Tsunami advisory issued for California coast",
                    "Small waves observed at California beaches after distant earthquake",
                    "Coastal areas in California monitoring for potential tsunami"
                ]
            }
        }
    
    def fetch_distress_signals(self, query, region, max_results=10):
        """
        Fetch mock distress signals based on the query.
        
        Args:
            query (str): The search query.
            region (str): The region to search in.
            max_results (int): Maximum number of results to return.
            
        Returns:
            list: A list of mock distress signals.
        """
        self._last_query = query
        self._last_region = region
        
        # Determine disaster type from query
        disaster_type = "flood"  # Default
        if "drought" in query.lower():
            disaster_type = "drought"
        elif "storm" in query.lower():
            disaster_type = "winter storm"
        elif "tornado" in query.lower():
            disaster_type = "tornado"
        elif "earthquake" in query.lower() or "tremor" in query.lower() or "seismic" in query.lower():
            disaster_type = "earthquake"
        elif "landslide" in query.lower() or "mudslide" in query.lower():
            disaster_type = "landslide"
        elif "volcano" in query.lower() or "eruption" in query.lower():
            disaster_type = "volcanic eruption"
        elif "fire" in query.lower() or "wildfire" in query.lower():
            disaster_type = "wildfire"
        elif "tsunami" in query.lower() or "wave" in query.lower():
            disaster_type = "tsunami"
        elif "hurricane" in query.lower() or "cyclone" in query.lower() or "typhoon" in query.lower():
            disaster_type = "hurricane"
        
        # Check for location-specific signals
        region_lower = region.lower()
        for location_key, disaster_signals in self._location_specific_signals.items():
            if location_key in region_lower and disaster_type in disaster_signals:
                return disaster_signals[disaster_type][:max_results]
        
        # Return mock signals for the disaster type
        signals = self._mock_signals.get(disaster_type, self._mock_signals["flood"])
        return signals[:max_results]
    
    def get_urgency_metrics(self):
        """
        Get mock urgency metrics for the last query.
        
        Returns:
            dict: A dictionary containing max_urgency and avg_urgency.
        """
        # Determine disaster type from last query
        disaster_type = "flood"  # Default
        if "drought" in self._last_query.lower():
            disaster_type = "drought"
        elif "storm" in self._last_query.lower():
            disaster_type = "winter storm"
        elif "tornado" in self._last_query.lower():
            disaster_type = "tornado"
        elif "earthquake" in self._last_query.lower() or "tremor" in self._last_query.lower() or "seismic" in self._last_query.lower():
            disaster_type = "earthquake"
        elif "landslide" in self._last_query.lower() or "mudslide" in self._last_query.lower():
            disaster_type = "landslide"
        elif "volcano" in self._last_query.lower() or "eruption" in self._last_query.lower():
            disaster_type = "volcanic eruption"
        elif "fire" in self._last_query.lower() or "wildfire" in self._last_query.lower():
            disaster_type = "wildfire"
        elif "tsunami" in self._last_query.lower() or "wave" in self._last_query.lower():
            disaster_type = "tsunami"
        elif "hurricane" in self._last_query.lower() or "cyclone" in self._last_query.lower() or "typhoon" in self._last_query.lower():
            disaster_type = "hurricane"
        
        # Return mock urgency metrics for the disaster type
        return self._mock_urgency.get(disaster_type, self._mock_urgency["flood"]) 