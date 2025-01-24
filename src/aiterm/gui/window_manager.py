"""
Window manager for handling multiple terminal windows
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from typing import Optional, Dict, List
from .terminal import TerminalGUI
from ..commands.executor import CommandExecutor
from ..commands.interpreter import CommandInterpreter
from ..commands.command_suggester import CommandSuggester
from ..utils.logger import get_logger

logger = get_logger()

class WindowManager:
    _instance = None
    
    def __init__(self):
        """Initialize the window manager"""
        if WindowManager._instance is not None:
            raise RuntimeError("WindowManager is a singleton!")
            
        # Create root window first
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Initialize theme state
        self.current_theme = tk.StringVar(self.root, value='retro')
        
        # Store window references
        self.windows = {}
        WindowManager._instance = self
        
        # Create first window
        self.create_window()
        
    @classmethod
    def get_instance(cls) -> 'WindowManager':
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = WindowManager()
        return cls._instance
        
    def create_window(self) -> None:
        """Create a new window"""
        window = NotebookWindow(self)
        self.windows[window] = window
        window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(window))
        
    def close_window(self, window) -> None:
        """Close a window"""
        if window in self.windows:
            del self.windows[window]
            window.destroy()
            
        # Exit if no windows left
        if not self.windows:
            self.root.quit()
            
    def apply_theme(self) -> None:
        """Apply the current theme to all windows"""
        theme = self.current_theme.get()
        for window in self.windows:
            window.apply_theme(theme)

class NotebookWindow(tk.Toplevel):
    """A window containing a notebook with multiple terminal tabs."""
    
    def __init__(self, manager):
        """Initialize notebook window."""
        super().__init__(manager.root)
        self.manager = manager
        
        # Set window size and position
        window_width = 800
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Set title
        self.title('AI Terminal')
        
        # Create notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')
        
        # Create first terminal tab
        self.add_terminal()
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.notebook.bind("<Button-2>", self._on_tab_middle_click)  # Middle click to close tab
        self.notebook.bind("<Control-t>", lambda e: self.add_terminal())  # Ctrl+T to open new tab
        
    def add_terminal(self):
        """Add a new terminal tab."""
        tab_frame = ttk.Frame(self.notebook)
        
        # Initialize components
        command_executor = CommandExecutor()
        command_interpreter = CommandInterpreter()
        command_suggester = CommandSuggester()
        
        # Create terminal with components
        terminal = TerminalGUI(
            tab_frame,
            command_executor=command_executor,
            command_interpreter=command_interpreter,
            command_suggester=command_suggester
        )
        terminal.pack(expand=True, fill='both')
        
        # Add tab to notebook
        tab_name = f"Terminal {len(self.notebook.tabs()) + 1}"
        self.notebook.add(tab_frame, text=tab_name)
        self.notebook.select(tab_frame)
        
    def _on_close(self):
        """Handle window close event"""
        self.manager.close_window(self)
        
    def _on_tab_middle_click(self, event):
        """Handle tab middle click event"""
        tab = self.notebook.identify(event.x, event.y)
        if tab:
            self.notebook.forget(tab)
            
    def apply_theme(self, theme):
        """Apply theme to all terminals"""
        for tab in self.notebook.tabs():
            for widget in tab.winfo_children():
                if isinstance(widget, TerminalGUI):
                    widget.apply_theme(theme)
