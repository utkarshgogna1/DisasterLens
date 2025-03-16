# DisasterLens Deployment Guide

This guide provides instructions for deploying the DisasterLens application in various environments.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Option 1: Local Deployment with Gunicorn

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DisasterLens.git
   cd DisasterLens
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

4. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

5. Access the application at http://localhost:5001

## Option 2: Linux Server Deployment with Systemd

1. Clone the repository on your server:
   ```bash
   git clone https://github.com/yourusername/DisasterLens.git
   cd DisasterLens
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install gunicorn
   ```

4. Edit the `disasterlens.service` file to update paths:
   ```bash
   nano disasterlens.service
   # Update the paths to match your server configuration
   ```

5. Copy the service file to systemd:
   ```bash
   sudo cp disasterlens.service /etc/systemd/system/
   ```

6. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable disasterlens
   sudo systemctl start disasterlens
   ```

7. Check the status:
   ```bash
   sudo systemctl status disasterlens
   ```

8. Access the application at http://your-server-ip:5001

## Option 3: Docker Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DisasterLens.git
   cd DisasterLens
   ```

2. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the application at http://localhost:5001

4. To stop the application:
   ```bash
   docker-compose down
   ```

## Option 4: Cloud Deployment

### AWS Elastic Beanstalk

1. Install the EB CLI:
   ```bash
   pip install awsebcli
   ```

2. Initialize EB application:
   ```bash
   eb init -p python-3.12 disasterlens
   ```

3. Create an environment and deploy:
   ```bash
   eb create disasterlens-env
   ```

4. Access the application at the provided URL

### Heroku

1. Install the Heroku CLI and login:
   ```bash
   heroku login
   ```

2. Create a Heroku app:
   ```bash
   heroku create disasterlens
   ```

3. Add a Procfile to the repository:
   ```
   web: gunicorn src.api.app:app
   ```

4. Deploy to Heroku:
   ```bash
   git push heroku main
   ```

5. Access the application at the provided URL

## Troubleshooting

- **Port already in use**: Kill the process using the port:
  ```bash
  lsof -i :5001 | grep LISTEN
  kill -9 <PID>
  ```

- **Application not starting**: Check the logs:
  ```bash
  # For local deployment
  cat logs/error.log
  
  # For systemd
  sudo journalctl -u disasterlens
  
  # For Docker
  docker-compose logs
  ```

- **Twitter API errors**: The application will generate mock data if Twitter API access fails. To use real Twitter data, set up proper API credentials in your environment variables. 