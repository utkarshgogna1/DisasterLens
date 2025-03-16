"""
Web API for DisasterLens.

This module provides a Flask-based web API for accessing DisasterLens
functionality and visualizing results.
"""
import json
import os
from typing import Dict, Any, List
import copy

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_cors import CORS

from src.models.predictor import predict_disaster_impact
from src.optimization.allocator import allocate_resources
from src.utils.config import get_config
from src.utils.logger import logger

# Create Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
CORS(app)  # Enable CORS for all routes

# Load configuration
config = get_config()

# Flag to control debug information in responses
INCLUDE_DEBUG_INFO = os.environ.get("DISASTERLENS_DEBUG", "0") == "1"


def sanitize_prediction_result(result):
    """
    Sanitize prediction result to remove unnecessary debug information.
    
    Args:
        result (dict): The raw prediction result
        
    Returns:
        dict: The sanitized prediction result
    """
    # If debug mode is enabled, return the full result
    if INCLUDE_DEBUG_INFO:
        return result
    
    # Create a copy of the result to avoid modifying the original
    sanitized = copy.deepcopy(result)
    
    # Preserve coordinates if they exist
    coordinates = sanitized.get('coordinates')
    
    # Remove debug notes
    if 'note' in sanitized and 'dummy prediction' in sanitized['note'].lower():
        del sanitized['note']
    
    # Keep only essential features based on disaster type
    if 'features' in sanitized:
        disaster_type = sanitized.get('disaster_type', '').lower()
        essential_features = set()
        
        # Common features for all disaster types
        essential_features.update([
            'temperature', 'humidity', 'pressure', 'wind_speed', 
            'social_signal_count', 'max_urgency', 'avg_urgency'
        ])
        
        # Add disaster-specific features
        if disaster_type == 'flood':
            essential_features.update([
                'rainfall_1h', 'rainfall_3h', 'rainfall_24h', 'flood_factor',
                'river_level', 'distance_to_water', 'flood_depth'
            ])
        elif disaster_type == 'tornado':
            essential_features.update([
                'wind_gust', 'pressure_drop', 'tornado_factor',
                'tornado_category', 'tornado_width', 'tornado_path_length'
            ])
        elif disaster_type == 'winter storm':
            essential_features.update([
                'snow_1h', 'snow_24h', 'freezing_factor', 'wind_chill_factor',
                'winter_storm_factor', 'ice_accumulation', 'road_conditions'
            ])
        elif disaster_type == 'earthquake':
            essential_features.update([
                'magnitude', 'depth', 'distance_to_epicenter', 
                'aftershock_probability', 'earthquake_factor'
            ])
        elif disaster_type == 'landslide':
            essential_features.update([
                'rainfall_24h', 'rainfall_72h', 'soil_saturation', 
                'slope_factor', 'landslide_factor', 'slope_angle', 
                'soil_type', 'vegetation_cover'
            ])
        elif disaster_type == 'drought':
            essential_features.update([
                'rainfall_deficit', 'drought_factor', 'drought_index',
                'vegetation_health', 'water_level', 'soil_moisture'
            ])
        elif disaster_type == 'volcanic eruption':
            essential_features.update([
                'distance_to_volcano', 'ash_column_height', 'lava_flow_speed',
                'eruption_intensity', 'air_quality', 'visibility'
            ])
        elif disaster_type == 'wildfire':
            essential_features.update([
                'fire_intensity', 'fire_spread_rate', 'vegetation_type',
                'distance_to_fire', 'air_quality', 'wind_direction'
            ])
        elif disaster_type == 'tsunami':
            essential_features.update([
                'wave_height', 'distance_to_coast', 'elevation',
                'arrival_time', 'earthquake_magnitude'
            ])
        elif disaster_type in ['hurricane', 'hurricane/typhoon/cyclone']:
            essential_features.update([
                'wind_gust', 'rainfall_24h', 'storm_surge', 'hurricane_factor',
                'hurricane_category', 'storm_surge_height', 'distance_to_eye',
                'forward_speed', 'wave_height'
            ])
        
        # Filter features to keep only essential ones
        filtered_features = {}
        for key, value in sanitized['features'].items():
            if key in essential_features or key.startswith('_'):
                filtered_features[key] = value
        
        sanitized['features'] = filtered_features
    
    # Restore coordinates if they were present
    if coordinates:
        sanitized['coordinates'] = coordinates
    
    return sanitized


@app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy"}), 200


@app.route("/")
def index():
    """
    Render the main page.
    """
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """API endpoint for making predictions."""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        location = data.get('location')
        coordinates = data.get('coordinates')
        disaster_type = data.get('disaster_type')
        model_type = data.get('model_type', 'ensemble')
        
        # Log the request data for debugging
        logger.debug(f"Prediction request: location={location}, disaster_type={disaster_type}, coordinates={coordinates}")
        
        # Validate parameters
        if not location:
            return jsonify({"error": "Location is required"}), 400
        
        if not disaster_type:
            return jsonify({"error": "Disaster type is required"}), 400
        
        # Validate disaster type
        valid_disaster_types = [
            "flood", "tornado", "winter storm", "earthquake", 
            "landslide", "drought", "volcanic eruption", "wildfire", 
            "tsunami", "hurricane", "hurricane/typhoon/cyclone"
        ]
        
        if disaster_type.lower() not in valid_disaster_types:
            return jsonify({
                "error": f"Invalid disaster type. Valid types are: {', '.join(valid_disaster_types)}"
            }), 400
        
        # Normalize hurricane/typhoon/cyclone variations
        if disaster_type.lower() in ["hurricane", "typhoon", "cyclone"]:
            disaster_type = "hurricane/typhoon/cyclone"
        
        # Make prediction
        try:
            result = predict_disaster_impact(
                location=location,
                disaster_type=disaster_type,
                model_type=model_type
            )
            
            # Add coordinates to the result if provided
            if coordinates:
                result["coordinates"] = coordinates
            
            # Log the full prediction result for debugging
            logger.debug(f"Full prediction result: {json.dumps(result)}")
            
            # Return sanitized result to client
            sanitized_result = sanitize_prediction_result(result)
            
            # Ensure coordinates are preserved in the sanitized result
            if coordinates and "coordinates" not in sanitized_result:
                sanitized_result["coordinates"] = coordinates
                
            return jsonify(sanitized_result)
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/api/allocate", methods=["POST"])
def api_allocate():
    """API endpoint for allocating resources based on predictions."""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract parameters
        prediction = data.get('prediction')
        regions = data.get('regions', [])
        resources = data.get('resources', [])
        disaster_type = data.get('disaster_type')
        
        # Log the request data for debugging
        logger.debug(f"Allocation request: regions={regions}, resources={resources}, disaster_type={disaster_type}")
        
        # Validate parameters
        if not prediction:
            return jsonify({"error": "Prediction data is required"}), 400
        
        if not regions or not isinstance(regions, list) or len(regions) == 0:
            return jsonify({"error": "At least one region is required"}), 400
        
        if not resources or not isinstance(resources, list) or len(resources) == 0:
            return jsonify({"error": "At least one resource is required"}), 400
        
        # Make allocation
        try:
            # Create a dictionary to store allocations for each region
            allocations = {}
            predictions = {}
            
            # Process each region
            for region in regions:
                # Get prediction for this region if not already provided
                region_prediction = prediction
                if region != prediction.get('location'):
                    try:
                        region_prediction = predict_disaster_impact(
                            location=region,
                            disaster_type=disaster_type,
                            model_type="random_forest"
                        )
                    except Exception as e:
                        logger.error(f"Error predicting for region {region}: {str(e)}")
                        region_prediction = {
                            "location": region,
                            "disaster_type": disaster_type,
                            "impact_score": 0.1,
                            "impact_level": "minimal",
                            "features": {}
                        }
                
                # Store the prediction
                predictions[region] = region_prediction
                
                # Initialize allocation for this region
                allocations[region] = {}
            
            # Process each resource
            for resource in resources:
                resource_type = resource.get('type')
                resource_amount = resource.get('amount')
                
                if not resource_type or not resource_amount or not isinstance(resource_amount, int) or resource_amount <= 0:
                    continue
                
                # Calculate total impact score across all regions
                total_impact = sum(pred.get('impact_score', 0) for pred in predictions.values())
                
                # If total impact is 0, distribute equally
                if total_impact == 0:
                    amount_per_region = resource_amount // len(regions)
                    remainder = resource_amount % len(regions)
                    
                    for i, region in enumerate(regions):
                        allocations[region][resource_type] = amount_per_region + (1 if i < remainder else 0)
                else:
                    # Distribute based on impact scores
                    for region in regions:
                        impact_score = predictions[region].get('impact_score', 0)
                        allocation = int(resource_amount * (impact_score / total_impact))
                        allocations[region][resource_type] = allocation
                    
                    # Distribute any remaining resources to the highest impact region
                    allocated = sum(allocations[region].get(resource_type, 0) for region in regions)
                    remainder = resource_amount - allocated
                    
                    if remainder > 0:
                        # Find the region with the highest impact score
                        highest_impact_region = max(regions, key=lambda r: predictions[r].get('impact_score', 0))
                        allocations[highest_impact_region][resource_type] += remainder
            
            # Prepare the result
            result = {
                "allocations": allocations,
                "predictions": {region: sanitize_prediction_result(pred) for region, pred in predictions.items()},
                "explanation": "Resources were allocated based on the relative impact scores of each region."
            }
            
            # Log the full allocation result for debugging
            logger.debug(f"Full allocation result: {json.dumps(result)}")
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Allocation error: {str(e)}")
            return jsonify({"error": f"Resource allocation failed: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/api/disaster_types", methods=['GET'])
def api_disaster_types():
    """Return available disaster types."""
    disaster_types = [
        {"id": "flood", "name": "Flood"},
        {"id": "tornado", "name": "Tornado"},
        {"id": "winter storm", "name": "Winter Storm"},
        {"id": "earthquake", "name": "Earthquake"},
        {"id": "landslide", "name": "Landslide"},
        {"id": "drought", "name": "Drought"},
        {"id": "volcanic eruption", "name": "Volcanic Eruption"},
        {"id": "wildfire", "name": "Wildfire"},
        {"id": "tsunami", "name": "Tsunami"},
        {"id": "hurricane/typhoon/cyclone", "name": "Hurricane/Typhoon/Cyclone"}
    ]
    return jsonify(disaster_types)


@app.route("/api/resource_types")
def api_resource_types():
    """
    API endpoint for getting available resource types.
    """
    resource_types = [
        {"id": "water", "name": "Water", "unit": "liters"},
        {"id": "food", "name": "Food", "unit": "meals"},
        {"id": "medicine", "name": "Medicine", "unit": "kits"},
        {"id": "shelter", "name": "Shelter", "unit": "tents"},
        {"id": "blankets", "name": "Blankets", "unit": "pieces"},
        {"id": "clothing", "name": "Clothing", "unit": "sets"},
        {"id": "fuel", "name": "Fuel", "unit": "liters"},
        {"id": "power", "name": "Power", "unit": "generators"},
        {"id": "communication", "name": "Communication", "unit": "devices"},
    ]
    
    return jsonify(resource_types)


@app.route("/predict/<region>/<disaster_type>", methods=["GET"])
def predict_legacy(region, disaster_type):
    """Legacy API endpoint for making predictions (GET method)."""
    try:
        # Log the request data for debugging
        logger.debug(f"Legacy prediction request: region={region}, disaster_type={disaster_type}")
        
        # Validate disaster type
        valid_disaster_types = [
            "flood", "tornado", "winter storm", "earthquake", 
            "landslide", "drought", "volcanic eruption", "wildfire", 
            "tsunami", "hurricane", "hurricane/typhoon/cyclone"
        ]
        
        if disaster_type.lower() not in valid_disaster_types:
            return jsonify({
                "error": f"Invalid disaster type. Valid types are: {', '.join(valid_disaster_types)}"
            }), 400
        
        # Normalize hurricane/typhoon/cyclone variations
        if disaster_type.lower() in ["hurricane", "typhoon", "cyclone"]:
            disaster_type = "hurricane/typhoon/cyclone"
        
        # Make prediction
        try:
            # Get coordinates for the location (for map display)
            coordinates = None
            
            # Make the prediction
            result = predict_disaster_impact(
                location=region,
                disaster_type=disaster_type,
                model_type="random_forest"
            )
            
            # Log the full prediction result for debugging
            logger.debug(f"Legacy prediction result: {json.dumps(result)}")
            
            # Return result to client
            return jsonify({
                "risk": result["impact_score"],
                "impact_level": result["impact_level"],
                "impact_score": result["impact_score"],
                "weather": {
                    "temp": result["features"].get("temperature", 0),
                    "humidity": result["features"].get("humidity", 0),
                    "pressure": result["features"].get("pressure", 0),
                    "wind_speed": result["features"].get("wind_speed", 0)
                },
                "specific_factors": {k: v for k, v in result["features"].items() 
                                    if k not in ["temperature", "humidity", "pressure", "wind_speed", 
                                                "social_signal_count", "max_urgency", "avg_urgency"]},
                "distress_signals": result["features"].get("social_signal_count", 0),
                "urgency_metrics": {
                    "max_urgency": result["features"].get("max_urgency", 0),
                    "avg_urgency": result["features"].get("avg_urgency", 0)
                },
                "location": region,
                "disaster_type": disaster_type
            })
        except Exception as e:
            logger.error(f"Legacy prediction error: {str(e)}")
            return jsonify({"error": f"Prediction failed: {str(e)}"}), 500
    
    except Exception as e:
        logger.error(f"Legacy API error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    # Run the app
    app.run(
        host=config.get("FLASK_RUN_HOST", "0.0.0.0"),
        port=config.get("FLASK_RUN_PORT", 5000),
        debug=config.get("FLASK_DEBUG", "1") == "1",
    ) 