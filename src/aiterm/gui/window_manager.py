"""
Window manager for handling multiple terminal windows
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from typing import Optional, Dict, List
from .terminal import TerminalGUI
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
    def __init__(self, manager):
        """Initialize notebook window"""
        super().__init__(manager.root)
        self.manager = manager
        
        # Store initial position for dragging
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Set up the window
        self.title('AI Terminal')
        self.geometry('800x600')
        
        # Create title bar for frameless mode
        self.title_bar = None
        
        # Create menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New Tab', command=self.add_terminal)
        file_menu.add_command(label='Close Tab', command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label='Close Window', command=self.close_window)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Copy', command=self.copy_selection)
        edit_menu.add_command(label='Paste', command=self.paste_clipboard)
        
        # Theme menu (synced with main window)
        theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Theme', menu=theme_menu)
        theme_menu.add_radiobutton(label='Retro', value='retro',
                                 variable=manager.current_theme,
                                 command=manager.apply_theme)
        theme_menu.add_radiobutton(label='Modern', value='modern',
                                 variable=manager.current_theme,
                                 command=manager.apply_theme)
        
        # Configure style for tabs
        style = ttk.Style()
        style.configure('TNotebook', tabposition='nw')
        style.configure('TNotebook.Tab', padding=[10, 5])
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Keep track of terminals and tab labels
        self.terminals = {}
        self.tab_labels = {}
        
        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Set minimum size
        self.minsize(600, 400)
        
        # Add initial tab
        self.add_terminal()
        
    def add_terminal(self):
        """Add a new terminal tab"""
        # Create a frame for the terminal
        tab_frame = ttk.Frame(self.notebook)
        
        # Create terminal in the frame
        terminal = TerminalGUI(tab_frame)
        terminal.frame.pack(fill=tk.BOTH, expand=True)
        
        # Add to notebook
        self.notebook.add(tab_frame, text=f'Terminal {len(self.terminals) + 1}')
        
        # Store references
        self.terminals[tab_frame] = terminal
        self.tab_labels[tab_frame] = f'Terminal {len(self.terminals)}'
        
        # Select the new tab
        self.notebook.select(tab_frame)
        
    def close_tab(self, tab_frame):
        """Close a specific tab"""
        if tab_frame in self.terminals:
            terminal = self.terminals[tab_frame]
            del self.terminals[tab_frame]
            del self.tab_labels[tab_frame]
            self.notebook.forget(tab_frame)
            
            # Create new tab if last one closed
            if not self.terminals:
                self.add_terminal()
                
    def close_current_tab(self):
        """Close the currently selected tab"""
        current = self.notebook.select()
        if current:
            self.close_tab(current)
            
    def close_window(self):
        """Close this window"""
        self.manager.close_window(self)
        
    def _on_tab_changed(self, event):
        """Handle tab change event"""
        current = self.notebook.select()
        if current in self.terminals:
            self.terminals[current].command_entry.focus_set()
            
    def copy_selection(self):
        """Copy selected text"""
        current = self.notebook.select()
        if current in self.terminals:
            self.terminals[current].copy_selection()
            
    def paste_clipboard(self):
        """Paste clipboard content"""
        current = self.notebook.select()
        if current in self.terminals:
            self.terminals[current].paste_clipboard()
            
    def apply_theme(self, theme):
        """Apply theme to all terminals"""
        for terminal in self.terminals.values():
            terminal.apply_theme(theme)
