"""
Main entry point for the AI Terminal application
"""

import tkinter as tk
from aiterm.gui.window_manager import WindowManager

def main():
    # Create window manager and first window
    window_manager = WindowManager.get_instance()
    window_manager.create_window()
    
    # Start the main event loop using the first window's root
    first_window = next(iter(window_manager.windows.values()))
    first_window.root.mainloop()

if __name__ == "__main__":
    main()
