#!/bin/bash

# Navigate to the project directory
echo "Navigating to the project directory..."
cd $(dirname "$0")

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

echo "Setup complete."
