#!/bin/bash

# Terms & Conditions Risk Analyzer - Run Script

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Warning: AWS credentials not set. Please export them:"
    echo "  export AWS_DEFAULT_REGION=us-west-2"
    echo "  export AWS_ACCESS_KEY_ID=your_key"
    echo "  export AWS_SECRET_ACCESS_KEY=your_secret"
    echo "  export AWS_SESSION_TOKEN=your_token"
fi

# Run the application
echo "Starting server..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
