"""
Dropdown widget for showing command suggestions
"""

import tkinter as tk
from tkinter import ttk
from ..utils.logger import get_logger

logger = get_logger()

class SuggestionDropdown(tk.Toplevel):
    def __init__(self, parent, suggestions=None):
        logger.info("Initializing SuggestionDropdown")
        super().__init__(parent)
        
        # Remove window decorations and set attributes
        self.overrideredirect(True)
        self.attributes('-topmost', True)  # Keep above other windows
        self.transient(parent)  # Make window transient (will close with parent)
        
        # Set background color
        self.configure(bg='#1e1e1e')
        
        # Create frame with border
        self.frame = tk.Frame(
            self,
            bg='#1e1e1e',
            highlightbackground='#4a4a4a',
            highlightthickness=1
        )
        self.frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Create listbox for suggestions
        self.listbox = tk.Listbox(
            self.frame,
            bg='#1e1e1e',
            fg='#ffffff',
            selectmode=tk.SINGLE,
            font=('Courier', 12),
            selectbackground='#4a4a4a',
            selectforeground='#ffffff',
            borderwidth=0,
            highlightthickness=0,
            height=10,  # Show up to 10 items
            width=40    # Set minimum width
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        # Initialize state
        self.suggestions = suggestions or []
        self.selected_index = 0
        self.visible = False
        
        # Hide initially
        self.withdraw()
        logger.info("SuggestionDropdown initialized and hidden")
        
        # Bind events
        self.listbox.bind('<Double-Button-1>', self._on_select)
        self.listbox.bind('<Return>', self._on_select)
        self.listbox.bind('<KP_Enter>', self._on_select)  # Numpad Enter
        
    def show(self, suggestions, x, y):
        """Show dropdown with suggestions at specified position"""
        if not suggestions:
            logger.info("No suggestions provided, hiding dropdown")
            self.hide()
            return
            
        logger.info(f"Showing dropdown with {len(suggestions)} suggestions at ({x}, {y})")
        
        # Convert suggestions to strings if they aren't already
        self.suggestions = [str(s) for s in suggestions]
        self.selected_index = 0
        
        # Update listbox items
        self.listbox.delete(0, tk.END)
        for suggestion in self.suggestions:
            self.listbox.insert(tk.END, suggestion)
            
        # Update size based on content
        width = max(len(str(s)) for s in self.suggestions) + 5  # Add padding
        self.listbox.configure(width=max(40, width))
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate window size
        self.update_idletasks()  # Make sure size is updated
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Adjust position if dropdown would go off screen
        if x + window_width > screen_width:
            x = screen_width - window_width
        if y + window_height > screen_height:
            y = y - window_height - self.master.winfo_height()
            
        # Position window
        self.geometry(f"+{x}+{y}")
        logger.info(f"Setting geometry to: {self.winfo_geometry()}")
        
        # Show window and select first item
        self.deiconify()
        self.lift()  # Bring to front
        self.attributes('-topmost', True)  # Ensure it stays on top
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(0)
        self.visible = True
        logger.info("Dropdown shown and configured")
        
    def hide(self):
        """Hide the dropdown"""
        logger.info("Hiding dropdown")
        self.withdraw()
        self.visible = False
        
    def next_suggestion(self):
        """Select next suggestion"""
        if not self.suggestions:
            logger.info("No suggestions available for next")
            return None
            
        self.selected_index = (self.selected_index + 1) % len(self.suggestions)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)  # Ensure selected item is visible
        suggestion = self.suggestions[self.selected_index]
        logger.info(f"Selected next suggestion: {suggestion}")
        return suggestion
        
    def prev_suggestion(self):
        """Select previous suggestion"""
        if not self.suggestions:
            logger.info("No suggestions available for prev")
            return None
            
        self.selected_index = (self.selected_index - 1) % len(self.suggestions)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)
        self.listbox.see(self.selected_index)  # Ensure selected item is visible
        suggestion = self.suggestions[self.selected_index]
        logger.info(f"Selected previous suggestion: {suggestion}")
        return suggestion
        
    def get_selected(self):
        """Get currently selected suggestion"""
        if not self.suggestions:
            return None
        return self.suggestions[self.selected_index]
        
    def is_visible(self):
        """Check if dropdown is visible"""
        return self.visible
        
    def _on_select(self, event=None):
        """Handle selection event"""
        if not self.suggestions:
            return
            
        # Get selected suggestion
        suggestion = self.get_selected()
        if suggestion:
            logger.info(f"Selected suggestion: {suggestion}")
            # Update command entry
            if hasattr(self.master, 'command_entry'):
                self.master.command_entry.delete(0, tk.END)
                self.master.command_entry.insert(0, suggestion)
                self.master.command_entry.focus_set()
            # Hide dropdown
            self.hide()
