#!/bin/bash

echo "=== Speaker Data Standardization Setup ==="
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check MongoDB connection
echo
echo "Checking MongoDB connection..."
python3 -c "
import os
from pymongo import MongoClient
try:
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    print('✓ MongoDB connection successful!')
except Exception as e:
    print('✗ MongoDB connection failed:', str(e))
    print('  Make sure MongoDB is running and accessible')
    exit(1)
"

# Set default environment variables if not set
export MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}
export DATABASE=${DATABASE:-"speakers_db"}

echo
echo "Configuration:"
echo "  MONGO_URI: $MONGO_URI"
echo "  DATABASE: $DATABASE"
echo

# Run the standardization
echo "Running standardization..."
echo "========================="
python3 main.py

echo
echo "=== Standardization Complete ==="