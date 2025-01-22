"""
Window manager for handling multiple terminal windows
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from typing import Optional, Dict, List

class WindowManager:
    _instance: Optional['WindowManager'] = None
    
    def __init__(self):
        if WindowManager._instance is not None:
            raise RuntimeError("WindowManager is a singleton!")
        self.windows: Dict[tk.Tk, 'NotebookWindow'] = {}
        WindowManager._instance = self
    
    @classmethod
    def get_instance(cls) -> 'WindowManager':
        if cls._instance is None:
            cls._instance = WindowManager()
        return cls._instance
    
    def create_window(self) -> None:
        """Create a new terminal window"""
        root = tk.Tk()
        window = NotebookWindow(root)
        self.windows[root] = window
        
        # If this is the first window, set up the application menu
        if len(self.windows) == 1:
            self._setup_application_menu(root)
    
    def _setup_application_menu(self, root: tk.Tk) -> None:
        """Set up the application menu bar"""
        if sys.platform == 'darwin':  # macOS
            # Create the Shell menu
            root.createcommand('tk::mac::ShowPreferences', lambda: None)  # Disable preferences
            
            # Add Shell menu items
            shell_menu = tk.Menu(root)
            
            shell_menu.add_command(
                label="New Window",
                command=self.create_window,
                accelerator="⌘N"
            )
            shell_menu.add_command(
                label="New Tab",
                command=lambda: self.active_window.add_tab() if self.active_window else None,
                accelerator="⌘T"
            )
            shell_menu.add_separator()
            shell_menu.add_command(
                label="Close Window",
                command=lambda: self.close_window(root),
                accelerator="⌘W"
            )
            shell_menu.add_command(
                label="Close Tab",
                command=lambda: self.active_window.close_current_tab() if self.active_window else None,
                accelerator="⌘D"
            )
            
            # Add menu to the menubar
            root.createcommand('::tk::mac::ShowWindowsMenu', lambda: None)  # Disable Windows menu
            menubar = tk.Menu(root)
            menubar.add_cascade(label="Shell", menu=shell_menu)
            root.config(menu=menubar)
            
            # Bind keyboard shortcuts
            root.bind('<Command-n>', lambda e: self.create_window())
            root.bind('<Command-t>', lambda e: self.active_window.add_tab() if self.active_window else None)
            root.bind('<Command-w>', lambda e: self.close_window(root))
            root.bind('<Command-d>', lambda e: self.active_window.close_current_tab() if self.active_window else None)
    
    @property
    def active_window(self) -> Optional['NotebookWindow']:
        """Get the currently active window"""
        for window in self.windows.values():
            if window.root.focus_get():
                return window
        return next(iter(self.windows.values())) if self.windows else None
    
    def close_window(self, root: tk.Tk) -> None:
        """Close a terminal window"""
        if root in self.windows:
            self.windows[root].root.destroy()
            del self.windows[root]
            
            # If no windows left, quit the application
            if not self.windows:
                sys.exit(0)


class NotebookWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AITerm")
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        
        # Configure style for tabs
        style = ttk.Style()
        style.configure('TNotebook', background='black')
        style.configure('TNotebook.Tab', padding=[5, 5], background='black', foreground='white')
        style.map('TNotebook.Tab',
                 background=[('selected', '#333333'), ('!selected', 'black')],
                 foreground=[('selected', 'white'), ('!selected', '#999999')])
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Keep track of terminals
        self.terminals = {}
        
        # Bind events for tab selection
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Set minimum size
        self.root.minsize(600, 400)
        
        # Add initial tab
        self.add_tab()
    
    def add_tab(self) -> None:
        """Add a new terminal tab"""
        from .terminal import TerminalGUI  # Import here to avoid circular import
        
        # Create a frame for the new tab
        tab_frame = ttk.Frame(self.notebook)
        terminal = TerminalGUI(tab_frame)
        
        # Store reference to terminal
        self.terminals[tab_frame] = terminal
        
        # Add the tab to the notebook with title
        tab_num = self.notebook.index('end') + 1
        self.notebook.add(tab_frame, text=f"Terminal {tab_num}")
        
        # Select the new tab
        self.notebook.select(tab_frame)
        
        # Focus the terminal's command entry
        terminal.command_entry.focus_set()
    
    def close_current_tab(self) -> None:
        """Close the currently selected tab"""
        current = self.notebook.select()
        if current and self.notebook.index('end') > 1:  # Don't close last tab
            # Clean up references
            if current in self.terminals:
                del self.terminals[current]
            self.notebook.forget(current)
            
            # Focus the new current tab's terminal
            current = self.notebook.select()
            if current in self.terminals:
                self.terminals[current].command_entry.focus_set()
    
    def _on_tab_changed(self, event):
        """Handle tab change event"""
        current = self.notebook.select()
        if current in self.terminals:
            # Focus the terminal's command entry
            self.terminals[current].command_entry.focus_set()


class TerminalGUI:
    def __init__(self, master):
        self.master = master
        self._setup_terminal()
        self._setup_command_entry()
    
    def _setup_terminal(self):
        """Setup the terminal widget"""
        # Create output area
        self.output_area = tk.Text(
            self.master,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            insertbackground='white',
            selectbackground='#4a4a4a',
            font=('Courier', 12)
        )
        self.output_area.pack(expand=True, fill='both')
        
        # Configure text colors
        self.output_area.tag_config('red', foreground='red')
        self.output_area.tag_config('green', foreground='#00ff00')
        self.output_area.tag_config('blue', foreground='#00aaff')
        self.output_area.tag_config('cyan', foreground='#00ffff')
        self.output_area.tag_config('yellow', foreground='#ffff00')
        self.output_area.tag_config('magenta', foreground='#ff00ff')
        self.output_area.tag_config('white', foreground='white')
    
    def _setup_command_entry(self):
        """Setup the command entry widget"""
        self.command_entry = tk.Entry(self.master, bg='black', fg='white', insertbackground='white')
        self.command_entry.pack(fill='x')
