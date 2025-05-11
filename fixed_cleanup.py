#!/usr/bin/env python3
"""
Cleanup script to remove generated files and prepare the repository for GitHub.
This script removes all generated files, logs, and temporary data.
"""

import os
import shutil
from pathlib import Path
import glob
import sys

# Determine the project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Project name
PROJECT_NAME = "AI_Resume_Builder"

# Check if the project folder exists
if not os.path.exists(os.path.join(PROJECT_DIR, PROJECT_NAME)):
    print(f"\033[91mERROR: Project directory not found. Please make sure '{PROJECT_NAME}' exists in {PROJECT_DIR}\033[0m")
    sys.exit(1)

# Set the full project path
PROJECT_DIR = os.path.join(PROJECT_DIR, PROJECT_NAME)

def print_colored(text, color_code):
    """Print colored text to the console."""
    print(f"\033[{color_code}m{text}\033[0m")

def print_info(text):
    """Print info message in blue."""
    print_colored(text, "94")

def print_success(text):
    """Print success message in green."""
    print_colored(text, "92")

def print_warning(text):
    """Print warning message in yellow."""
    print_colored(text, "93")

def print_error(text):
    """Print error message in red."""
    print_colored(text, "91")

def remove_directory(directory):
    """Remove a directory and all its contents."""
    try:
        if os.path.exists(directory):
            print_info(f"Removing directory: {directory}")
            shutil.rmtree(directory)
            print_success(f"Successfully removed: {directory}")
        else:
            print_info(f"Directory does not exist, skipping: {directory}")
    except Exception as e:
        print_error(f"Error removing directory {directory}: {e}")

def remove_file(file_path):
    """Remove a file if it exists."""
    try:
        if os.path.exists(file_path):
            print_info(f"Removing file: {file_path}")
            os.remove(file_path)
            print_success(f"Successfully removed: {file_path}")
        else:
            print_info(f"File does not exist, skipping: {file_path}")
    except Exception as e:
        print_error(f"Error removing file {file_path}: {e}")

def remove_files_by_pattern(directory, pattern):
    """Remove all files matching a pattern in a directory."""
    try:
        files = glob.glob(os.path.join(directory, pattern))
        for file_path in files:
            remove_file(file_path)
    except Exception as e:
        print_error(f"Error removing files with pattern {pattern} in {directory}: {e}")

def clean_data_folder():
    """Clean the data_folder directory."""
    print_info("\n=== Cleaning data_folder ===")

    # Remove output directory
    remove_directory(os.path.join(PROJECT_DIR, "data_folder/output"))

    # Create empty output directory
    os.makedirs(os.path.join(PROJECT_DIR, "data_folder/output"), exist_ok=True)
    print_success("Created empty data_folder/output directory")

    # Remove any log files
    remove_files_by_pattern(os.path.join(PROJECT_DIR, "data_folder"), "*.log")

    # Remove any JSON files (like open_ai_calls.json)
    remove_files_by_pattern(os.path.join(PROJECT_DIR, "data_folder"), "*.json")

def clean_job_applications():
    """Clean the job_applications directory."""
    print_info("\n=== Cleaning job_applications ===")
    remove_directory(os.path.join(PROJECT_DIR, "job_applications"))

    # Create empty job_applications directory
    os.makedirs(os.path.join(PROJECT_DIR, "job_applications"), exist_ok=True)
    print_success("Created empty job_applications directory")

def clean_logs():
    """Clean log files."""
    print_info("\n=== Cleaning log files ===")

    # Remove log files in the root directory
    remove_files_by_pattern(PROJECT_DIR, "*.log")

    # Remove log files in the src directory
    remove_files_by_pattern(os.path.join(PROJECT_DIR, "src"), "*.log")

def clean_pycache():
    """Clean __pycache__ directories."""
    print_info("\n=== Cleaning __pycache__ directories ===")

    # Find all __pycache__ directories
    for root, dirs, files in os.walk(PROJECT_DIR):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                remove_directory(os.path.join(root, dir_name))

def clean_temp_files():
    """Clean temporary files."""
    print_info("\n=== Cleaning temporary files ===")

    # Remove .pyc files
    remove_files_by_pattern(PROJECT_DIR, "*.pyc")

    # Remove .pyo files
    remove_files_by_pattern(PROJECT_DIR, "*.pyo")

    # Remove .pyd files
    remove_files_by_pattern(PROJECT_DIR, "*.pyd")

    # Remove .DS_Store files (for macOS)
    remove_files_by_pattern(PROJECT_DIR, ".DS_Store")

def create_gitignore():
    """Create or update .gitignore file."""
    print_info("\n=== Creating .gitignore file ===")

    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
virtual/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Application specific
data_folder/output/*
!data_folder/output/.gitkeep
job_applications/*
!job_applications/.gitkeep
*.log
*.json
"""

    with open(os.path.join(PROJECT_DIR, ".gitignore"), "w") as f:
        f.write(gitignore_content)

    print_success("Created .gitignore file")

def create_empty_files():
    """Create empty .gitkeep files to preserve directory structure."""
    print_info("\n=== Creating .gitkeep files ===")

    # Create .gitkeep files
    directories = [
        "data_folder/output",
        "job_applications"
    ]

    for directory in directories:
        full_path = os.path.join(PROJECT_DIR, directory)
        os.makedirs(full_path, exist_ok=True)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        with open(gitkeep_path, "w") as f:
            pass
        print_success(f"Created {gitkeep_path}")

def main():
    """Main function to clean up the repository."""
    print_info(f"Starting cleanup process for project at: {PROJECT_DIR}")

    # Check if the project directory exists
    if not os.path.exists(PROJECT_DIR):
        print_error(f"Project directory not found: {PROJECT_DIR}")
        print_error("Please make sure the path is correct.")
        sys.exit(1)

    # Clean directories and files
    clean_data_folder()
    clean_job_applications()
    clean_logs()
    clean_pycache()
    clean_temp_files()

    # Create necessary files
    create_gitignore()
    create_empty_files()

    print_success("\nCleanup completed successfully!")
    print_info("The repository is now ready to be renamed and uploaded to GitHub.")

if __name__ == "__main__":
    main()
