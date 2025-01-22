"""
Window manager for handling multiple terminal windows
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from typing import Optional, Dict, List

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
        
        # Set up the main window
        self.root.title('AI Terminal')
        self.root.geometry('800x600')
        
        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New Terminal', command=self.create_window)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Copy', command=self.copy_selection)
        edit_menu.add_command(label='Paste', command=self.paste_clipboard)
        
        # Theme menu
        theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Theme', menu=theme_menu)
        theme_menu.add_radiobutton(label='Retro', value='retro', 
                                 variable=self.current_theme, 
                                 command=self.apply_theme)
        theme_menu.add_radiobutton(label='Modern', value='modern', 
                                 variable=self.current_theme,
                                 command=self.apply_theme)
    
    @classmethod
    def get_instance(cls) -> 'WindowManager':
        if cls._instance is None:
            cls._instance = WindowManager()
        return cls._instance
    
    def create_window(self) -> None:
        """Create a new terminal window"""
        window = NotebookWindow(self)
        self.windows[window] = window
        
        # If this is the first window, set up the application menu
        if len(self.windows) == 1:
            self._setup_application_menu(self.root)
    
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
                command=lambda: self.active_window.add_terminal() if self.active_window else None,
                accelerator="⌘T"
            )
            shell_menu.add_separator()
            shell_menu.add_command(
                label="Close Window",
                command=lambda: self.close_window(self.active_window),
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
            root.bind('<Command-t>', lambda e: self.active_window.add_terminal() if self.active_window else None)
            root.bind('<Command-w>', lambda e: self.close_window(self.active_window))
            root.bind('<Command-d>', lambda e: self.active_window.close_current_tab() if self.active_window else None)
    
    @property
    def active_window(self) -> Optional['NotebookWindow']:
        """Get the currently active window"""
        for window in self.windows.values():
            if window.focus_get():
                return window
        return next(iter(self.windows.values())) if self.windows else None
    
    def close_window(self, window: 'NotebookWindow') -> None:
        """Close a terminal window"""
        if window in self.windows:
            window.destroy()
            del self.windows[window]
            
            # If no windows left, quit the application
            if not self.windows:
                sys.exit(0)
    
    def apply_theme(self):
        """Apply the selected theme to all windows"""
        theme = self.current_theme.get()
        
        style = ttk.Style()
        if theme == 'retro':
            # Retro theme (current look)
            style.configure('TNotebook', tabposition='nw')
            style.configure('TNotebook.Tab', 
                padding=[10, 5],
                anchor='w',
                background='black',
                foreground='white'
            )
            style.map('TNotebook.Tab',
                background=[('selected', '#333333'), ('!selected', 'black')],
                foreground=[('selected', 'white'), ('!selected', '#999999')]
            )
            
            # Update all windows
            for window in self.windows.values():
                # Restore window decorations
                window.overrideredirect(False)
                
                # Update terminal colors
                for tab in window.terminals.values():
                    tab.output_area.configure(
                        bg='black',
                        fg='white',
                        insertbackground='white',
                        selectbackground='#4a4a4a'
                    )
                    tab.command_entry.configure(
                        bg='black',
                        fg='white',
                        insertbackground='white'
                    )
                
        else:  # modern theme
            # Modern theme (sleek look)
            style.configure('TNotebook', tabposition='nw')
            style.configure('TNotebook.Tab', 
                padding=[10, 5],
                anchor='w',
                background='#2b2b2b',
                foreground='#d4d4d4'
            )
            style.map('TNotebook.Tab',
                background=[('selected', '#1e1e1e'), ('!selected', '#2b2b2b')],
                foreground=[('selected', '#ffffff'), ('!selected', '#d4d4d4')]
            )
            
            # Update all windows
            for window in self.windows.values():
                # Make window frameless
                window.overrideredirect(True)
                
                # Add drag functionality
                window.bind('<Button-1>', window._on_drag_start)
                window.bind('<B1-Motion>', window._on_drag_motion)
                
                # Add close button
                if not hasattr(window, 'title_bar'):
                    window._create_title_bar()
                
                # Update terminal colors
                for tab in window.terminals.values():
                    tab.output_area.configure(
                        bg='#1e1e1e',
                        fg='#d4d4d4',
                        insertbackground='#d4d4d4',
                        selectbackground='#264f78'
                    )
                    tab.command_entry.configure(
                        bg='#1e1e1e',
                        fg='#d4d4d4',
                        insertbackground='#d4d4d4'
                    )
    
    def copy_selection(self):
        # Implement copy functionality
        pass
    
    def paste_clipboard(self):
        # Implement paste functionality
        pass


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
    
    def add_terminal(self) -> None:
        """Add a new terminal tab"""
        from .terminal import TerminalGUI  # Import here to avoid circular import
        
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        
        # Create header frame for tab label and close button
        header_frame = ttk.Frame(tab_frame)
        header_frame.pack(fill='x', side='top')
        
        # Add tab label
        tab_num = len(self.terminals) + 1
        label = ttk.Label(header_frame, text=f"Terminal {tab_num}")
        label.pack(side='left', padx=5)
        
        # Add close button
        close_button = ttk.Button(header_frame, text="×", width=2,
                                command=lambda: self.close_tab(tab_frame))
        close_button.pack(side='right', padx=5)
        
        # Create terminal
        terminal = TerminalGUI(tab_frame)
        terminal.frame.pack(fill='both', expand=True)
        self.terminals[tab_frame] = terminal
        
        # Add the tab to notebook
        self.notebook.add(tab_frame, text=f"Terminal {tab_num}")
        
        # Select the new tab
        self.notebook.select(tab_frame)
        terminal.command_entry.focus_set()
    
    def close_tab(self, tab_frame):
        """Close a specific tab"""
        if len(self.terminals) > 1:
            # Remove the terminal
            if tab_frame in self.terminals:
                del self.terminals[tab_frame]
            
            # Remove the tab
            self.notebook.forget(tab_frame)
            
            # Update remaining tab numbers
            for i, tab in enumerate(self.notebook.tabs(), 1):
                self.notebook.tab(tab, text=f"Terminal {i}")
        else:
            # If this is the last tab, close the window
            self.close_window()
    
    def close_current_tab(self):
        """Close the currently selected tab"""
        current = self.notebook.select()
        if current:
            self.close_tab(current)
    
    def close_window(self):
        self.destroy()
    
    def _on_tab_changed(self, event):
        """Handle tab change event"""
        current = self.notebook.select()
        if current in self.terminals:
            # Focus the terminal's command entry
            self.terminals[current].command_entry.focus_set()
    
    def copy_selection(self):
        # Implement copy functionality
        pass
    
    def paste_clipboard(self):
        # Implement paste functionality
        pass
    
    def _create_title_bar(self):
        """Create custom title bar for frameless mode"""
        # Create title bar frame
        self.title_bar = tk.Frame(self, bg='#2b2b2b', height=30)
        self.title_bar.pack(fill='x', side='top')
        
        # Add title label
        title_label = tk.Label(self.title_bar, text='AI Terminal', 
                             bg='#2b2b2b', fg='#d4d4d4')
        title_label.pack(side='left', padx=10)
        
        # Add close button
        close_button = tk.Label(self.title_bar, text='×', 
                              bg='#2b2b2b', fg='#d4d4d4',
                              font=('Arial', 16))
        close_button.pack(side='right', padx=10)
        close_button.bind('<Button-1>', lambda e: self.destroy())
        
        # Make title bar draggable
        self.title_bar.bind('<Button-1>', self._on_drag_start)
        self.title_bar.bind('<B1-Motion>', self._on_drag_motion)
        title_label.bind('<Button-1>', self._on_drag_start)
        title_label.bind('<B1-Motion>', self._on_drag_motion)
    
    def _on_drag_start(self, event):
        """Start window drag"""
        self.drag_start_x = event.x_root - self.winfo_x()
        self.drag_start_y = event.y_root - self.winfo_y()
    
    def _on_drag_motion(self, event):
        """Handle window drag"""
        x = event.x_root - self.drag_start_x
        y = event.y_root - self.drag_start_y
        self.geometry(f'+{x}+{y}')


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
