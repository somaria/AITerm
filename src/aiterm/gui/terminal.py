"""
Terminal GUI implementation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import font as tkfont
import os

from ..commands.interpreter import CommandInterpreter, CommandInterpretationError
from ..commands.executor import CommandExecutor
from ..utils.formatter import OutputFormatter
from ..utils.completer import TerminalCompleter

class TerminalGUI:
    def __init__(self, root):
        self.root = root
        
        # Initialize components
        self.command_executor = CommandExecutor()
        self.output_formatter = OutputFormatter()
        self.completer = TerminalCompleter()
        self.current_completions = []
        self.completion_index = 0
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('Terminal.TFrame', background='black')
        self.main_frame['style'] = 'Terminal.TFrame'
        
        # Create terminal output area with padding
        self.terminal_font = tkfont.Font(family="Courier", size=12)
        self.output_area = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            font=self.terminal_font,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Show welcome message
        self._show_welcome_message()
        
        # Create command frame
        self._setup_command_frame()

    def _setup_command_frame(self):
        """Set up the command input frame"""
        # Create a frame for the directory and input
        self.command_frame = ttk.Frame(self.main_frame)
        self.command_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Create a vertical frame for directory and input
        self.input_frame = ttk.Frame(self.command_frame)
        self.input_frame.pack(fill=tk.X, expand=True, padx=(0, 15))
        
        # Directory display frame with more vertical spacing
        self.dir_frame = ttk.Frame(self.input_frame)
        self.dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side frame for DIRECTORY label
        self.dir_label_frame = ttk.Frame(self.dir_frame)
        self.dir_label_frame.pack(side=tk.LEFT)
        
        self.dir_label = tk.Label(
            self.dir_label_frame,
            text="DIRECTORY",
            font=(self.terminal_font.name, self.terminal_font.actual()['size'] - 1),
            bg='black',
            fg='light gray',
            padx=8
        )
        self.dir_label.pack(side=tk.LEFT)
        
        # Add space after DIRECTORY label
        ttk.Frame(self.dir_frame).pack(side=tk.LEFT, padx=15)
        
        # Directory path with custom background and padding
        self.path_frame = ttk.Frame(self.dir_frame)
        self.path_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.prompt_label = tk.Label(
            self.path_frame,
            text=f"{self.command_executor.working_directory}",
            font=self.terminal_font,
            bg='black',
            fg='light green',
            anchor='w',
            padx=8
        )
        self.prompt_label.pack(fill=tk.X)
        
        # AI mode toggle with custom style on the right
        self.ai_mode = tk.BooleanVar(value=True)
        
        # Create a frame for the AI mode toggle
        self.ai_toggle_frame = ttk.Frame(self.dir_frame)
        self.ai_toggle_frame.pack(side=tk.RIGHT, padx=(15, 0))
        
        # Create clickable label for AI MODE
        self.ai_toggle = tk.Label(
            self.ai_toggle_frame,
            text="AI MODE",
            font=(self.terminal_font.name, self.terminal_font.actual()['size'] - 1),
            bg='black',
            fg='cyan',
            padx=8,
            cursor="hand2"  # Change cursor to hand when hovering
        )
        self.ai_toggle.pack(side=tk.LEFT)
        
        # Add click binding
        self.ai_toggle.bind('<Button-1>', self._toggle_ai_mode)
        
        # Update initial color
        self._update_ai_mode_display()
        
        # Command input frame with increased vertical spacing
        self.cmd_frame = ttk.Frame(self.input_frame)
        self.cmd_frame.pack(fill=tk.X, pady=(12, 0))
        
        # Command prompt with custom style and padding
        self.cmd_prompt = tk.Label(
            self.cmd_frame,
            text="❯",
            font=(self.terminal_font.name, self.terminal_font.actual()['size'] + 2),
            bg='black',
            fg='cyan',
            padx=8
        )
        self.cmd_prompt.pack(side=tk.LEFT)
        
        # Command entry with custom border and increased padding
        self.command_entry = tk.Entry(
            self.cmd_frame,
            font=self.terminal_font,
            bg='black',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(15, 0))
        
        # Bind events
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.bind('<Tab>', self._handle_tab)
        self.command_entry.bind('<Up>', self._handle_up)
        self.command_entry.bind('<Down>', self._handle_down)
        
        # Bind click events to focus the command entry
        self.output_area.bind('<Button-1>', lambda e: self.command_entry.focus_set())
        self.main_frame.bind('<Button-1>', lambda e: self.command_entry.focus_set())
        self.cmd_frame.bind('<Button-1>', lambda e: self.command_entry.focus_set())
        
        # Initialize command history
        self.command_history = []
        self.history_index = 0

    def _show_welcome_message(self):
        """Display the welcome message"""
        messages = [
            ("Welcome to AITerm!", "cyan"),
            ("\nA modern terminal with AI capabilities.\n", "light blue"),
            ("Type commands as you would in a normal terminal.", "white"),
            ("\nAI Mode is enabled by default - your commands will be interpreted by AI.", "light gray"),
            ("\nClick 'AI MODE' to toggle AI interpretation.", "light gray")
        ]
        for msg, color in messages:
            self.append_output(msg, color)

    def update_prompt(self):
        """Update the prompt with current working directory"""
        self.prompt_label.config(text=f"{self.command_executor.working_directory}")

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
            self.root.quit()
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
    
    def _toggle_ai_mode(self, event=None):
        """Toggle AI mode and update display"""
        self.ai_mode.set(not self.ai_mode.get())
        self._update_ai_mode_display()
    
    def _update_ai_mode_display(self):
        """Update the AI mode toggle display"""
        if self.ai_mode.get():
            self.ai_toggle.configure(fg='cyan')
        else:
            self.ai_toggle.configure(fg='gray')

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
        
        return "break"  # Prevent default tab behavior
    
    def _handle_up(self, event):
        """Handle up arrow key press for command history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        return "break"
    
    def _handle_down(self, event):
        """Handle down arrow key press for command history"""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, tk.END)
        return "break"
