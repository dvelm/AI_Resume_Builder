#!/usr/bin/env python3
"""
Script to rename the project folder from 'Jobs_Applier_AI_Agent_AIHawk' to 'AI_Resume_Builder'.
"""

import os
import sys

# Path to the parent directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Folder names
OLD_FOLDER_NAME = "Jobs_Applier_AI_Agent_AIHawk"
NEW_FOLDER_NAME = "AI_Resume_Builder"

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

# Determine current folder name
if os.path.exists(os.path.join(PARENT_DIR, OLD_FOLDER_NAME)):
    CURRENT_FOLDER_NAME = OLD_FOLDER_NAME
elif os.path.exists(os.path.join(PARENT_DIR, NEW_FOLDER_NAME)):
    CURRENT_FOLDER_NAME = NEW_FOLDER_NAME
    print_warning(f"The project folder is already named '{NEW_FOLDER_NAME}'. No action needed.")
    sys.exit(0)
else:
    print_error(f"Project directory not found. Please make sure either '{OLD_FOLDER_NAME}' or '{NEW_FOLDER_NAME}' exists in {PARENT_DIR}")
    sys.exit(1)

def rename_project_folder():
    """Rename the project folder."""
    # Current folder path
    current_folder_path = os.path.join(PARENT_DIR, CURRENT_FOLDER_NAME)

    # New folder path
    new_folder_path = os.path.join(PARENT_DIR, NEW_FOLDER_NAME)

    # Check if the current folder exists
    if not os.path.exists(current_folder_path):
        print_error(f"The project folder '{CURRENT_FOLDER_NAME}' does not exist in {PARENT_DIR}.")
        print_error("Please make sure the path is correct.")
        sys.exit(1)

    # Check if the current folder name is already the new name
    if os.path.basename(current_folder_path) == NEW_FOLDER_NAME:
        print_warning(f"The project folder is already named '{NEW_FOLDER_NAME}'. No action needed.")
        return

    # Check if the new folder already exists
    if os.path.exists(new_folder_path):
        print_error(f"A folder named '{NEW_FOLDER_NAME}' already exists in {PARENT_DIR}.")
        print_error("Please rename or remove it before running this script.")
        sys.exit(1)

    # Rename the folder
    try:
        print_info(f"Renaming project folder from '{CURRENT_FOLDER_NAME}' to '{NEW_FOLDER_NAME}'...")
        os.rename(current_folder_path, new_folder_path)
        print_success(f"Successfully renamed project folder to '{NEW_FOLDER_NAME}'!")
        print_info(f"New project path: {new_folder_path}")

        print_warning("\nIMPORTANT: The project folder has been renamed.")
        print_warning(f"The project is now located at: {new_folder_path}")
    except Exception as e:
        print_error(f"Error renaming project folder: {e}")
        sys.exit(1)

def main():
    """Main function to rename the project folder."""
    print_info("Starting project folder renaming process...")
    rename_project_folder()
    print_success("Project folder renamed successfully!")

if __name__ == "__main__":
    main()
