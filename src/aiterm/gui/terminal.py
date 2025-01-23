"""
Terminal GUI implementation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import font as tkfont
import os
import math

from ..commands.interpreter import CommandInterpreter, CommandInterpretationError
from ..commands.executor import CommandExecutor
from ..utils.formatter import OutputFormatter
from ..utils.completer import TerminalCompleter

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg='black', height=32, corner_radius=16, **kwargs):
        super().__init__(parent, bg=bg, height=height, highlightthickness=0, **kwargs)
        self._corner_radius = corner_radius
        self.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        self.delete("rounded")
        width = self.winfo_width()
        height = self.winfo_height()
        self.create_rounded_rect(0, 0, width, height, self._corner_radius, 
                               fill='black', outline='#333333', width=1, tags="rounded")

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for i in range(0, 360, 5):  
            angle = i * math.pi / 180
            if 0 <= i < 90:
                points.extend([x2 - radius + math.cos(angle) * radius,
                             y1 + radius - math.sin(angle) * radius])
            elif 90 <= i < 180:
                points.extend([x1 + radius - math.cos(math.pi - angle) * radius,
                             y1 + radius - math.sin(math.pi - angle) * radius])
            elif 180 <= i < 270:
                points.extend([x1 + radius - math.cos(angle - math.pi) * radius,
                             y2 - radius + math.sin(angle - math.pi) * radius])
            else:
                points.extend([x2 - radius + math.cos(2 * math.pi - angle) * radius,
                             y2 - radius + math.sin(2 * math.pi - angle) * radius])
        return self.create_polygon(points, smooth=True, **kwargs)

class TerminalGUI:
    def __init__(self, parent):
        """Initialize terminal GUI"""
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize components
        self.command_executor = CommandExecutor()
        self.command_history = []
        self.history_index = 0
        self.current_completions = []
        self.completion_index = 0
        self.ai_mode = tk.BooleanVar(value=True)  
        self.completer = TerminalCompleter()
        self.last_completion_text = ""
        
        # Create output area
        self.output_area = tk.Text(
            self.frame,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            insertbackground='white',
            selectbackground='#4a4a4a',
            font=('Courier', 12)
        )
        self.output_area.pack(expand=True, fill='both', padx=5, pady=(5,0))
        
        # Create command frame
        self.cmd_frame = ttk.Frame(self.frame)
        self.cmd_frame.pack(fill='x', padx=5, pady=5)
        
        # Create directory frame (first line)
        self.dir_frame = ttk.Frame(self.cmd_frame)
        self.dir_frame.pack(fill='x', pady=(0, 5))
        
        # Create directory label
        self.dir_label = tk.Label(
            self.dir_frame,
            text="DIRECTORY",
            font=('Courier', 10),
            bg='black',
            fg='gray'
        )
        self.dir_label.pack(side='left', padx=(0, 10))
        
        # Create prompt label
        self.prompt_label = ttk.Label(
            self.dir_frame,
            text=self.command_executor.working_directory,
            font=('Courier', 12)
        )
        self.prompt_label.pack(side='left', fill='x', expand=True)
        
        # Create AI mode toggle frame on directory line
        self.ai_toggle_frame = tk.Frame(
            self.dir_frame,
            bg='cyan',  
            bd=1,
            relief='solid'
        )
        self.ai_toggle_frame.pack(side='right', padx=5)
        
        # Create AI mode toggle
        self.ai_toggle = tk.Label(
            self.ai_toggle_frame,
            text="AI MODE",
            cursor="hand2",
            bg='cyan',  
            fg='black',  
            padx=8,
            pady=2,
            font=('Courier', 10, 'bold'),
            relief='solid'  
        )
        self.ai_toggle.pack()
        self.ai_toggle.bind('<Button-1>', self._toggle_ai_mode)
        
        # Create input frame (second line)
        self.input_frame = ttk.Frame(self.cmd_frame)
        self.input_frame.pack(fill='x')
        
        # Create prompt symbol
        self.prompt_symbol = tk.Label(
            self.input_frame,
            text="❯",
            font=('Courier', 12),
            bg='black',
            fg='cyan'
        )
        self.prompt_symbol.pack(side='left', padx=(0, 5))
        
        # Create rounded frame for input
        self.entry_frame = RoundedFrame(self.input_frame)
        self.entry_frame.pack(side='left', fill='x', expand=True, pady=2)  
        
        # Create command entry
        self.command_entry = tk.Entry(
            self.entry_frame,
            bg='black',
            fg='white',
            insertbackground='white',
            font=('Courier', 12),
            bd=0,
            highlightthickness=0
        )
        # Place the entry widget in the canvas
        self.entry_frame.create_window(12, 16, window=self.command_entry,  
                                     anchor='w', width=self.entry_frame.winfo_width() - 24)
        
        # Bind frame resize to update entry width
        self.entry_frame.bind('<Configure>', self._on_frame_resize)
        
        # Configure tags for colored output
        self.output_area.tag_configure('red', foreground='red')
        self.output_area.tag_configure('green', foreground='green')
        self.output_area.tag_configure('blue', foreground='blue')
        self.output_area.tag_configure('cyan', foreground='cyan')
        self.output_area.tag_configure('white', foreground='white')
        
        # Bind events
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.bind('<Up>', self._history_up)
        self.command_entry.bind('<Down>', self._history_down)
        self.command_entry.bind('<Tab>', self._handle_tab)
        
        # Focus command entry
        self.command_entry.focus_set()
        
        # Show welcome message
        self.append_output("Welcome to AI Terminal!\nClick 'AI MODE' to toggle AI interpretation.", 'cyan')
    
    def _toggle_ai_mode(self, event=None):
        """Toggle AI mode and update display"""
        self.ai_mode.set(not self.ai_mode.get())
        self._update_ai_mode_display()
    
    def _update_ai_mode_display(self):
        """Update the AI mode toggle display"""
        if self.ai_mode.get():
            self.ai_toggle.configure(
                fg='black',
                bg='cyan',
                relief='solid'
            )
            self.ai_toggle_frame.configure(
                bg='cyan'
            )
        else:
            self.ai_toggle.configure(
                fg='gray',
                bg='black',
                relief='flat'
            )
            self.ai_toggle_frame.configure(
                bg='black'
            )
    
    def append_output(self, text, color=None):
        """Append text to output area with optional color"""
        if not text:
            return
            
        # Add newline if needed
        if not text.endswith('\n'):
            text += '\n'
            
        # Get current position
        pos = self.output_area.index(tk.END)
        
        # Insert text
        self.output_area.insert(tk.END, text)
        
        # Apply color tag if specified
        if color:
            # Calculate end position
            start = f"{float(pos) - 1.0}"
            end = self.output_area.index(tk.END)
            self.output_area.tag_add(color, start, end)
            self.output_area.tag_config(color, foreground=color)
        
        # Scroll to end
        self.output_area.see(tk.END)
    
    def execute_command(self, event=None):
        """Execute the entered command"""
        command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        
        if not command:
            return

        # Reset completion state
        self.current_completions = []
        self.completion_index = 0

        # Add command to history
        if not self.command_history or command != self.command_history[-1]:
            self.command_history.append(command)
            self.history_index = len(self.command_history)

        # Show command in output area
        self.append_output(f"\n{self.command_executor.working_directory}$ {command}")
        
        # Handle exit command
        if command == 'exit':
            self.parent.quit()
            return

        # If AI mode is enabled and it's not a built-in command, interpret it
        if self.ai_mode.get() and not any(command.startswith(cmd) for cmd in ['cd', 'pwd', 'exit', 'clear']):
            try:
                interpreted_command = CommandInterpreter.interpret(command)
                if interpreted_command:
                    self.append_output(f"\nInterpreted as: {interpreted_command}\n", 'cyan')
                    command = interpreted_command
            except Exception as e:
                self.append_output(f"\nError interpreting command: {str(e)}\n", 'red')
                return
        
        try:
            # Handle built-in commands
            if command == 'pwd':
                self.append_output(self.command_executor.working_directory)
            elif command.startswith('cd'):
                parts = command.split(maxsplit=1)
                success, result = self.command_executor.change_directory(
                    parts[1] if len(parts) > 1 else None
                )
                if not success:
                    self.append_output(f"\nError: {result}\n", 'red')
                self.update_prompt()
            elif command == 'clear':
                self.output_area.delete(1.0, tk.END)
            else:
                # Execute external command
                stdout, stderr = self.command_executor.execute(command)
                
                if stdout:
                    if command.startswith('ls'):
                        # Format ls output
                        for line in stdout.rstrip().split('\n'):
                            if os.path.isdir(os.path.join(self.command_executor.working_directory, line)):
                                self.append_output(line, 'blue')
                            elif os.access(os.path.join(self.command_executor.working_directory, line), os.X_OK):
                                self.append_output(line, 'green')
                            else:
                                self.append_output(line)
                    else:
                        self.append_output(stdout.rstrip())
                
                if stderr:
                    self.append_output(f"\n{stderr.rstrip()}\n", 'red')

        except Exception as e:
            self.append_output(f"\nError: {str(e)}\n", 'red')
    
    def update_prompt(self):
        """Update the prompt with current working directory"""
        self.prompt_label.config(text=f"{self.command_executor.working_directory}")

    def _handle_tab(self, event):
        """Handle tab key press for command completion"""
        current_text = self.command_entry.get()
        cursor_pos = self.command_entry.index(tk.INSERT)
        text_before_cursor = current_text[:cursor_pos]
        
        # If we don't have completions or pressed tab on new text
        if not self.current_completions or self.last_completion_text != text_before_cursor:
            self.current_completions = self.completer.get_completions(text_before_cursor)
            self.completion_index = 0
            self.last_completion_text = text_before_cursor
        
        if self.current_completions:
            # Get the completion and update index
            completion = self.current_completions[self.completion_index]
            self.completion_index = (self.completion_index + 1) % len(self.current_completions)
            
            # Replace the text
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, completion)
        
        return "break"  

    def _history_up(self, event):
        """Handle up arrow key press for command history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        return "break"
    
    def _history_down(self, event):
        """Handle down arrow key press for command history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, tk.END)
        return "break"

    def _on_frame_resize(self, event):
        """Update entry width when frame is resized"""
        self.entry_frame.create_window(12, 16, window=self.command_entry,  
                                     anchor='w', width=event.width - 24)  
