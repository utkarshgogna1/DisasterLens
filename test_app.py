import unittest
import requests
import time
import subprocess
import os
import signal
import sys

class DisasterLensTest(unittest.TestCase):
    """Basic tests for the DisasterLens application."""
    
    @classmethod
    def setUpClass(cls):
        """Start the Flask application before running tests."""
        print("Starting DisasterLens application...")
        cls.process = subprocess.Popen(
            ["python", "-m", "src.api.app"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "FLASK_RUN_PORT": "5001"}
        )
        # Give the server time to start
        time.sleep(3)
        
    @classmethod
    def tearDownClass(cls):
        """Stop the Flask application after tests are complete."""
        print("Stopping DisasterLens application...")
        cls.process.terminate()
        cls.process.wait()
        
    def test_home_page(self):
        """Test that the home page loads correctly."""
        response = requests.get("http://localhost:5001")
        self.assertEqual(response.status_code, 200)
        self.assertIn("DisasterLens", response.text)
        
    def test_prediction_endpoint(self):
        """Test that the prediction endpoint responds correctly."""
        data = {
            "location": "Mt. Fuji, Japan",
            "coordinates": "35.3606,138.7274",
            "disaster_type": "Landslide"
        }
        response = requests.post("http://localhost:5001/api/predict", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("impact_level", response.json())
        
if __name__ == "__main__":
    unittest.main() 