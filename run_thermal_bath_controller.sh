#!/bin/bash

# Display script banner
echo "========================================"
echo "  Thermal Bath Controller Launcher      "
echo "========================================"

# Find the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 to run this application."
    exit 1
fi

# Check for required packages and install if needed
echo "Checking required packages..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Installing venv..."
        sudo apt-get update && sudo apt-get install -y python3-venv
        python3 -m venv venv
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing required packages..."
pip install -r requirements.txt

# On Raspberry Pi, ensure tk is installed
if [ -f /sys/firmware/devicetree/base/model ] && grep -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
    echo "Raspberry Pi detected, ensuring Tkinter is installed..."
    if ! python3 -c "import tkinter" &> /dev/null; then
        echo "Tkinter not found. Installing python3-tk..."
        sudo apt-get update && sudo apt-get install -y python3-tk
    fi
fi

# Launch the application
echo "Launching Thermal Bath Controller..."
python3 gui_pi.py

# Deactivate virtual environment when done
deactivate