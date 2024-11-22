#!/bin/bash

# Set the shell to exit immediately if a command exits with a non-zero status
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure Python is installed
if ! command_exists python3; then
    echo "Python3 is not installed. Please install Python3 to proceed."
    exit 1
fi

# Ensure the required Python packages are installed
echo "Checking for required Python packages..."
pip3 install -r requirements.txt

# Check if the .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file is missing. Please create one with the required environment variables."
    exit 1
fi

# Ensure the necessary directories exist
mkdir -p ./data/audio/podcast
mkdir -p ./data/transcripts

# Run the main.py script
echo "Running the Podcast Generator..."
python3 main.py

# Completion message
echo "Podcast generation and upload process completed successfully!"