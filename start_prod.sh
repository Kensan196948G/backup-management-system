#!/bin/bash
# Production Server Startup Script
# Usage: ./start_prod.sh

echo "=========================================="
echo "Backup Management System - Production"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found."
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found."
    echo "Please create .env from .env.example"
    exit 1
fi

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=production

# Create directories
mkdir -p data logs reports app/static/uploads

# Check dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Start production server with Waitress
echo "Starting Waitress WSGI server..."
echo "Access: http://0.0.0.0:8080"
echo "Press Ctrl+C to stop"
echo ""

python run.py --production --host 0.0.0.0 --port 8080
