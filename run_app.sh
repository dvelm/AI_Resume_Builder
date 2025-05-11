#!/bin/bash

echo "==================================================="
echo "AI Resume Builder - Launch Script"
echo "==================================================="
echo

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    echo "Please install Python 3.10 or higher."
    echo "For Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "For macOS: brew install python3"
    echo
    exit 1
fi

# Check for updates
echo "Checking for updates..."
if command -v git &> /dev/null; then
    git fetch
    if git status -uno | grep -q "behind"; then
        echo "Updates are available. Would you like to update? (y/n)"
        read update_choice
        if [[ "$update_choice" == "y" || "$update_choice" == "Y" ]]; then
            git pull
            echo "Repository updated successfully."
        else
            echo "Update skipped."
        fi
    else
        echo "No updates available."
    fi
else
    echo "Git not found. Skipping update check."
fi

# Check if virtual environment exists
if [ ! -d "virtual" ]; then
    echo "Virtual environment not found. Running installation script..."
    bash install_requirements.sh
fi

# Activate virtual environment and run the application
echo "Activating virtual environment and launching application..."
source virtual/bin/activate
python3 main.py

echo
echo "==================================================="
echo "Application closed."
echo "==================================================="
echo
