#!/bin/bash

echo "==================================================="
echo "AI Resume Builder - Installation Script"
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

# Create virtual environment if it doesn't exist
if [ ! -d "virtual" ]; then
    echo "Creating virtual environment..."
    python3 -m venv virtual
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment and install requirements
echo "Activating virtual environment and installing requirements..."
source virtual/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "==================================================="
echo "Installation completed successfully!"
echo
echo "To run the application, use the run_app.sh script."
echo "==================================================="
echo

# Make run script executable
chmod +x run_app.sh
