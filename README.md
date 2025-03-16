# DisasterLens

DisasterLens is a comprehensive disaster impact prediction and resource allocation optimization platform. It helps emergency management agencies, humanitarian organizations, and governments to predict the impact of various natural disasters and optimize resource allocation for effective disaster response.

## Features

- **Disaster Impact Prediction**: Predict the impact of various natural disasters including earthquakes, floods, hurricanes, wildfires, landslides, and tornadoes.
- **Resource Allocation Optimization**: Optimize the allocation of resources across affected regions based on impact predictions.
- **Interactive Map Visualization**: Visualize disaster impact and resource allocation on an interactive map.
- **Multi-factor Analysis**: Consider weather data, social vulnerability factors, and disaster-specific parameters in impact predictions.
- **API Integration**: Easily integrate with other systems through a RESTful API.

## Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Data Processing**: NumPy, Pandas
- **Machine Learning**: Scikit-learn
- **Visualization**: Plotly, Folium
- **Deployment**: Docker, Gunicorn

# DisasterLens
Predict the impact of natural disasters and optimize resource allocation.

**Live Demo:** [https://disasterlens-api.onrender.com](https://disasterlens-api.onrender.com)

## Installation

### Quick Setup

For first-time users, we provide a setup script that creates a virtual environment and installs all dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/DisasterLens.git
cd DisasterLens

# Run the setup script
./setup.sh
```

### Manual Setup

If you prefer to set up manually:

```bash
# Clone the repository
git clone https://github.com/yourusername/DisasterLens.git
cd DisasterLens

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data/raw data/processed

# Copy the example environment file
cp .env.example .env
```

## Running the Application

### Development Mode

```bash
python -m src.api.app
```

The application will be available at http://localhost:5001

### Production Mode

```bash
# Using the deployment script
./deploy.sh

# Or manually with Gunicorn
gunicorn --bind 0.0.0.0:5001 --workers 4 src.api.app:app
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Render Deployment

DisasterLens can be deployed to Render, a cloud platform for hosting web applications:

```bash
# Deploy to Render using the provided configuration
# See RENDER.md for detailed instructions
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md) and [RENDER.md](RENDER.md).


## Usage
1. Visit the live demo URL.
2. Enter a location (e.g., "Boston, Suffolk County, Massachusetts, United States").
3. Select a disaster type (e.g., "Winter Storm").
4. Click "Predict Impact" to see the predicted impact, weather conditions, and social signals.

## Testing

Run the automated tests:

```bash
./run_tests.sh
```

## Project Structure

```
DisasterLens/
├── src/                    # Source code
│   ├── api/                # Web API and frontend
│   ├── models/             # Prediction models
│   ├── optimization/       # Resource allocation optimization
│   ├── data/               # Data processing modules
│   ├── utils/              # Utility functions
│   └── visualization/      # Visualization modules
├── data/                   # Data files
│   ├── raw/                # Raw data
│   └── processed/          # Processed data
├── tests/                  # Test files
├── docs/                   # Documentation
├── logs/                   # Log files
├── setup.sh                # Setup script
├── deploy.sh               # Deployment script
├── run_tests.sh            # Test runner script
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # Project documentation
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Weather data provided by OpenWeatherMap API
- Social vulnerability data based on CDC's Social Vulnerability Index
- Map visualization powered by Leaflet and Folium
