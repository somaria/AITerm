"""Main entry point for the AI Terminal application."""

import os
import sys
from aiterm.gui.window_manager import WindowManager

def main():
    """Main entry point."""
    # Get the window manager instance
    window_manager = WindowManager.get_instance()
    
    # Start the main event loop
    window_manager.root.mainloop()

if __name__ == "__main__":
    main()
