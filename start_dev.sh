#!/bin/bash
# Development Server Startup Script
# Usage: ./start_dev.sh

echo "=========================================="
echo "Backup Management System - Development"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Set environment variables
export FLASK_APP=app
export FLASK_ENV=development

# Create directories
mkdir -p data logs reports app/static/uploads

# Start development server
echo "Starting Flask development server..."
echo "Access: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop"
echo ""

python run.py
