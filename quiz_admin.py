"""
Quiz Admin Tool - Entry Point
Version: 2.1 Modular Edition
Main application launcher
"""

import tkinter as tk
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.constants import APP_TITLE, WINDOW_STATE
from admin_tool.main_window import MainWindow


def main():
    """Main application entry point"""
    try:
        # Create required folders if they don't exist
        if not os.path.exists('questions'):
            os.makedirs('questions')
        if not os.path.exists('images'):
            os.makedirs('images')
            
        # Create root window
        root = tk.Tk()
        root.title(APP_TITLE)
        
        # Set window state (full screen)
        try:
            root.state(WINDOW_STATE)
        except:
            # Fallback for systems that don't support 'zoomed'
            root.attributes('-zoomed', True)
        
        # Create and run main application
        app = MainWindow(root)
        
        # Start main loop
        root.mainloop()
    
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()