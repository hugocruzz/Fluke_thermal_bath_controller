#!/bin/bash

# Display script banner
echo "========================================"
echo "  Thermal Bath Controller Launcher      "
echo "========================================"
echo "  Repository: github.com/hugocruzz/Fluke_thermal_bath_controller"
echo "========================================"

# Find the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check for Git and update from repository if available
echo "Checking for updates from GitHub..."
if command -v git &> /dev/null; then
    if [ -d ".git" ]; then
        # Repository already exists, pull latest changes
        echo "Pulling latest changes..."
        git pull origin main
        if [ $? -ne 0 ]; then
            echo "Warning: Failed to update from GitHub. Continuing with current version."
        else
            echo "Successfully updated to the latest version."
        fi
    else
        # Repository doesn't exist locally, prompt to clone it
        echo "This directory is not a git repository."
        read -p "Do you want to clone the repository? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd ..
            echo "Cloning repository..."
            git clone https://github.com/hugocruzz/Fluke_thermal_bath_controller.git
            if [ $? -ne 0 ]; then
                echo "Failed to clone repository."
                exit 1
            else
                echo "Successfully cloned repository."
                cd Fluke_thermal_bath_controller
                SCRIPT_DIR="$( pwd )"
            fi
        fi
    fi
else
    echo "Git not found. Skipping update check."
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing Python..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    else
        echo "Error: Unable to install Python. Please install Python 3 manually."
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv 2>/dev/null
    
    # If venv creation failed, try installing python3-venv
    if [ $? -ne 0 ]; then
        echo "Installing python3-venv package..."
        sudo apt-get update && sudo apt-get install -y python3-venv
        python3 -m venv venv
        
        # If it still fails, try without venv
        if [ $? -ne 0 ]; then
            echo "Warning: Unable to create virtual environment. Proceeding without it."
            USE_VENV=0
        else
            USE_VENV=1
        fi
    else
        USE_VENV=1
    fi
else
    USE_VENV=1
fi

# Activate virtual environment if available
if [ $USE_VENV -eq 1 ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install required packages
echo "Installing required packages..."
if [ $USE_VENV -eq 1 ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    pip3 install --user -r requirements.txt
fi

# On Raspberry Pi, ensure tkinter is installed
if [ -f /sys/firmware/devicetree/base/model ] && grep -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
    echo "Raspberry Pi detected, checking tkinter installation..."
    if ! python3 -c "import tkinter" &> /dev/null; then
        echo "Installing tkinter..."
        sudo apt-get update && sudo apt-get install -y python3-tk
    fi
fi

# Create directories if they don't exist
mkdir -p "$SCRIPT_DIR/configs"
mkdir -p "$SCRIPT_DIR/logs"

# Launch the application
echo "Launching Thermal Bath Controller..."
if [ $USE_VENV -eq 1 ]; then
    python gui_pi.py
else
    python3 gui_pi.py
fi

# Deactivate virtual environment when done
if [ $USE_VENV -eq 1 ]; then
    deactivate
fi