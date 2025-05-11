"""
Loading screen utility for the AI Resume Builder application.
This module provides a loading screen with animation during PDF generation.
"""
import sys
import time
import threading
from itertools import cycle
from src.utils.ui_translations import get_ui_string

class LoadingScreen:
    """
    A class to display a loading screen with animation in the console.
    """
    def __init__(self, message, language="English"):
        """
        Initialize the loading screen.
        
        Args:
            message (str): The message to display
            language (str): The language to use for the loading screen
        """
        self.message = message
        self.language = language
        self.is_running = False
        self.thread = None
        
        # Animation frames
        self.spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner = cycle(self.spinner_frames)
        
        # Progress messages
        self.progress_messages = {
            "English": [
                "Analyzing content...",
                "Formatting document...",
                "Applying styles...",
                "Optimizing layout...",
                "Finalizing PDF..."
            ],
            "Italiano": [
                "Analisi del contenuto...",
                "Formattazione del documento...",
                "Applicazione degli stili...",
                "Ottimizzazione del layout...",
                "Finalizzazione del PDF..."
            ]
        }
        
        # Default to English if language not supported
        if language not in self.progress_messages:
            self.language = "English"
            
        self.progress_cycle = cycle(self.progress_messages[self.language])
    
    def _animate(self):
        """
        Animation function that runs in a separate thread.
        """
        start_time = time.time()
        progress_update_interval = 3  # seconds
        last_progress_update = start_time
        current_progress = self.message
        
        while self.is_running:
            # Update progress message periodically
            current_time = time.time()
            if current_time - last_progress_update > progress_update_interval:
                current_progress = next(self.progress_cycle)
                last_progress_update = current_time
            
            # Get next spinner frame
            spinner_char = next(self.spinner)
            
            # Calculate elapsed time
            elapsed = int(current_time - start_time)
            minutes, seconds = divmod(elapsed, 60)
            
            # Create the loading message
            if self.language == "English":
                time_msg = f"Time elapsed: {minutes:02d}:{seconds:02d}"
            else:
                time_msg = f"Tempo trascorso: {minutes:02d}:{seconds:02d}"
                
            # Print the loading message
            sys.stdout.write(f"\r{spinner_char} {current_progress} {time_msg}")
            sys.stdout.flush()
            time.sleep(0.1)
    
    def start(self):
        """
        Start the loading animation in a separate thread.
        """
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._animate)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """
        Stop the loading animation and clear the line.
        """
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join(timeout=0.5)
            
            # Clear the line
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
            
            # Print completion message
            if self.language == "English":
                print("✓ PDF generation completed successfully!")
            else:
                print("✓ Generazione del PDF completata con successo!")


def show_loading_screen(action_type, language="English"):
    """
    Create and return a loading screen for the specified action type.
    
    Args:
        action_type (str): The type of action being performed (resume, cover_letter, etc.)
        language (str): The language to use for the loading screen
        
    Returns:
        LoadingScreen: The loading screen object
    """
    # Get the appropriate message based on action type
    if action_type == "resume":
        message_key = "generating_resume_loading"
    elif action_type == "resume_tailored":
        message_key = "generating_tailored_resume_loading"
    elif action_type == "cover_letter":
        message_key = "generating_cover_letter_loading"
    else:
        message_key = "generating_document_loading"
    
    # Add these keys to UI_STRINGS in ui_translations.py
    message = get_ui_string(message_key, language)
    
    # Create and start the loading screen
    loading_screen = LoadingScreen(message, language)
    loading_screen.start()
    
    return loading_screen
