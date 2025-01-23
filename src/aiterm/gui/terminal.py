"""
Terminal GUI implementation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import os
import shlex
import subprocess
import threading
import queue
import pty
import select
import tty
import termios
import signal
import logging
from typing import Optional, Tuple, List, Dict

import math
import re
from ..commands.interpreter import CommandInterpreter, CommandInterpretationError
from ..commands.executor import CommandExecutor
from ..utils.formatter import OutputFormatter
from ..utils.completer import TerminalCompleter
from ..utils.logger import get_logger
from .suggestion_dropdown import SuggestionDropdown

logger = get_logger()

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

class PseudoTerminal:
    def __init__(self, callback, exit_callback, rows=24, cols=80):
        self.callback = callback
        self.exit_callback = exit_callback
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.running = False
        self.read_thread = None
        self.write_queue = queue.Queue()
        
        # Terminal size
        self.rows = rows
        self.cols = cols
        
        # Screen buffer
        self.screen = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.saved_cursor = (0, 0)
        self.alternate_screen = False
        
        # Environment variables
        self.env = os.environ.copy()
        self.env['TERM'] = 'xterm-256color'  # Set terminal type
        self.env['PAGER'] = 'more'  # Set default pager
        self.env['LESS'] = '-R'  # Make less behave more like more
        self.env['MORE'] = '-d'  # Enable user-friendly mode for more
        
        # Initialize empty screen
        self._init_screen()
        logger.info("Initializing PseudoTerminal")

    def _init_screen(self):
        """Initialize empty screen buffer"""
        self.screen = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]

    def _clear_screen(self):
        """Clear the screen buffer"""
        self._init_screen()
        self.cursor_x = 0
        self.cursor_y = 0

    def _process_escape_sequence(self, seq):
        """Process ANSI escape sequence"""
        if seq.startswith('[?'):
            # Handle mode changes
            mode = seq[2:-1]
            if mode == '1049':  # Alternate screen buffer
                if 'h' in seq:  # Enable alternate screen
                    self._clear_screen()
                    self.alternate_screen = True
                elif 'l' in seq:  # Disable alternate screen
                    self._clear_screen()
                    self.alternate_screen = False
            return

        if seq.startswith('['):
            cmd = seq[-1]
            params = seq[1:-1].split(';')
            params = [int(p) if p.isdigit() else 0 for p in params]
            
            if cmd == 'H':  # Cursor position
                self.cursor_y = (params[0] if params else 1) - 1
                self.cursor_x = (params[1] if len(params) > 1 else 1) - 1
            elif cmd == 'J':  # Clear screen
                if params[0] == 2:
                    self._clear_screen()
            elif cmd == 'K':  # Clear line
                if not params or params[0] == 0:  # Clear from cursor to end
                    for x in range(self.cursor_x, self.cols):
                        self.screen[self.cursor_y][x] = ' '
            elif cmd == 's':  # Save cursor position
                self.saved_cursor = (self.cursor_x, self.cursor_y)
            elif cmd == 'u':  # Restore cursor position
                self.cursor_x, self.cursor_y = self.saved_cursor

    def _process_output(self, data):
        """Process terminal output and update screen buffer"""
        text = data.decode('utf-8', errors='replace')
        i = 0
        while i < len(text):
            if text[i] == '\x1b':  # ESC
                # Find the end of the escape sequence
                j = i + 1
                while j < len(text) and text[j] not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@':
                    j += 1
                if j < len(text):
                    self._process_escape_sequence(text[i+1:j+1])
                    i = j + 1
                    continue
            
            char = text[i]
            if char == '\n':
                self.cursor_y += 1
                self.cursor_x = 0
            elif char == '\r':
                self.cursor_x = 0
            elif char == '\b':
                self.cursor_x = max(0, self.cursor_x - 1)
            elif char >= ' ':  # Printable characters
                if self.cursor_x < self.cols and self.cursor_y < self.rows:
                    self.screen[self.cursor_y][self.cursor_x] = char
                    self.cursor_x += 1
            
            # Handle line wrapping
            if self.cursor_x >= self.cols:
                self.cursor_x = 0
                self.cursor_y += 1
            
            # Handle scrolling
            if self.cursor_y >= self.rows:
                self.screen.pop(0)
                self.screen.append([' ' for _ in range(self.cols)])
                self.cursor_y = self.rows - 1
            
            i += 1

    def _set_window_size(self, fd):
        """Set the terminal window size"""
        winsize = struct.pack("HHHH", self.rows, self.cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def start(self, command):
        """Start the pseudo-terminal with the given command"""
        logger.debug(f"Starting PTY with command: {command}")
        
        try:
            # Create PTY
            self.master_fd, self.slave_fd = os.openpty()
            
            # Set terminal size
            self._set_window_size(self.slave_fd)
            
            # Split command and handle shell built-ins
            if isinstance(command, str):
                import shlex
                command = shlex.split(command)
            
            # Get environment
            env = os.environ.copy()
            env.update(self.env)
            
            # Start process with Popen
            self.process = subprocess.Popen(
                command,
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                env=env,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Close slave fd in parent
            os.close(self.slave_fd)
            
            # Start read thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            logger.debug("PTY started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start PTY: {e}")
            if self.master_fd:
                os.close(self.master_fd)
            if self.slave_fd:
                os.close(self.slave_fd)
            raise

    def stop(self):
        """Stop the pseudo-terminal"""
        logger.debug("Stopping pseudo-terminal")
        
        # Set running to False first to prevent race conditions
        self.running = False
        
        if hasattr(self, 'process') and self.process:
            try:
                # Try graceful termination first
                logger.debug("Attempting graceful process termination")
                self.process.terminate()
                
                # Wait a bit for the process to terminate
                try:
                    self.process.wait(timeout=1)
                    logger.debug("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # If process doesn't terminate gracefully, force kill
                    logger.warning("Process did not terminate gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait()
                    logger.debug("Process killed")
            except (OSError, ProcessLookupError) as e:
                logger.error(f"Error stopping process: {e}")
            finally:
                self.process = None
        
        # Close master fd if it exists
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
                logger.debug("Closed master file descriptor")
            except OSError as e:
                if e.errno != errno.EBADF:  # Ignore "Bad file descriptor" errors
                    logger.error(f"Error closing master fd: {e}")
            finally:
                self.master_fd = None

    def _read_loop(self):
        """Read loop for the pseudo-terminal"""
        while self.running:
            try:
                # Check for data to read
                r, w, e = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 1024)
                    if data:
                        self._process_output(data)
                        self.callback(self._get_screen_content())
                    else:
                        # EOF - process exited
                        break

                # Check for data to write
                try:
                    data = self.write_queue.get_nowait()
                    os.write(self.master_fd, data.encode())
                except queue.Empty:
                    pass

            except (OSError, IOError) as e:
                if e.errno != errno.EINTR:
                    break

        self.running = False
        self.stop()
        if self.exit_callback:
            self.exit_callback()

    def _get_screen_content(self):
        """Get the current screen content"""
        output = []
        for y, line in enumerate(self.screen):
            current_line = []
            for x, char in enumerate(line):
                if x == self.cursor_x and y == self.cursor_y:
                    current_line.append('█')
                else:
                    current_line.append(char)
            output.append(''.join(current_line).rstrip())
        return '\n'.join(output)

    def write(self, data):
        """Write data to the terminal"""
        if self.running:
            self.write_queue.put(data)

class TerminalGUI(ttk.Frame):
    """Terminal GUI component that handles command input/output and display."""
    
    def __init__(self, parent, command_executor, command_interpreter, command_suggester):
        """Initialize the terminal GUI."""
        super().__init__(parent)
        
        # Store components
        self.parent = parent
        self.command_executor = command_executor
        self.command_interpreter = command_interpreter
        self.command_suggester = command_suggester
        
        # Initialize state
        self.command_history = []
        self.history_index = 0
        self.pty = None
        self.in_pty_mode = False
        self.term_rows = 24
        self.term_cols = 80
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create AI mode toggle
        self.ai_mode = tk.BooleanVar(value=True)
        self.ai_toggle = ttk.Checkbutton(
            self.main_frame,
            text="AI MODE",
            variable=self.ai_mode,
            style='Toggle.TCheckbutton'
        )
        self.ai_toggle.pack(side=tk.TOP, anchor=tk.NW, padx=5, pady=5)
        
        # Create output area
        self.output_area = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Courier', 12),
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_area.pack(expand=True, fill=tk.BOTH, padx=5, pady=(0, 5))
        
        # Create command frame
        self.cmd_frame = ttk.Frame(self.main_frame)
        self.cmd_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Create directory frame
        self.dir_frame = ttk.Frame(self.cmd_frame)
        self.dir_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create directory label
        self.dir_label = ttk.Label(
            self.dir_frame,
            text="DIRECTORY",
            font=('Courier', 10)
        )
        self.dir_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create prompt label
        self.prompt_label = ttk.Label(
            self.dir_frame,
            text=self.command_executor.working_directory,
            font=('Courier', 12)
        )
        self.prompt_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create input frame
        self.input_frame = ttk.Frame(self.cmd_frame)
        self.input_frame.pack(fill=tk.X)
        
        # Create prompt symbol
        self.prompt_symbol = ttk.Label(
            self.input_frame,
            text="❯",
            font=('Courier', 12)
        )
        self.prompt_symbol.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create command entry
        self.command_entry = ttk.Entry(
            self.input_frame,
            font=('Courier', 12)
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Configure tags for colored output
        self.setup_text_tags()
        
        # Show welcome message
        self.append_output("Welcome to AI Terminal!\n", 'welcome')
        self.append_output("Click 'AI MODE' to toggle AI interpretation.\n", 'welcome')
        
        # Create suggestion dropdown
        self.suggestion_dropdown = SuggestionDropdown(self)
        
        # Bind events
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.bind('<Up>', self.history_up)
        self.command_entry.bind('<Down>', self.history_down)
        self.command_entry.bind('<Tab>', self.handle_tab)
        self.command_entry.bind('<Key>', self.handle_key_press)
        
        # Focus command entry
        self.command_entry.focus_set()

    def append_output(self, text: str, tag: str = None) -> None:
        """Append text to the output area."""
        # Get current position
        current = self.output_area.index(tk.INSERT)
        
        # Handle ANSI color codes
        if '\033[' in text:
            # Split text by ANSI escape sequences
            import re
            parts = re.split('(\033\\[[0-9;]*m)', text)
            
            # Process each part
            current_tag = None
            for part in parts:
                if part.startswith('\033['):
                    # Handle color code
                    if '34m' in part:  # Blue (directories)
                        current_tag = 'blue'
                    elif '31m' in part:  # Red
                        current_tag = 'red'
                    elif '32m' in part:  # Green
                        current_tag = 'green'
                    elif '33m' in part:  # Yellow
                        current_tag = 'yellow'
                    elif '36m' in part:  # Cyan
                        current_tag = 'cyan'
                    elif '35m' in part:  # Magenta
                        current_tag = 'magenta'
                    elif '0m' in part:  # Reset
                        current_tag = None
                elif part:
                    # Insert text with current color tag
                    start = self.output_area.index(tk.END)
                    self.output_area.insert(tk.END, part)
                    if current_tag:
                        self.output_area.tag_add(current_tag, start, tk.END)
        else:
            # No color codes, insert normally
            self.output_area.insert(tk.END, text)
            if tag:
                start = f"{current} linestart"
                end = f"{tk.END} lineend"
                self.output_area.tag_add(tag, start, end)
            
        # Scroll to end
        self.output_area.see(tk.END)
        
    def setup_text_tags(self) -> None:
        """Setup text tags for different types of output."""
        # Configure tags for different types of output
        self.output_area.tag_configure('red', foreground='red')
        self.output_area.tag_configure('green', foreground='green')
        self.output_area.tag_configure('blue', foreground='blue')
        self.output_area.tag_configure('cyan', foreground='cyan')
        self.output_area.tag_configure('yellow', foreground='yellow')
        self.output_area.tag_configure('magenta', foreground='magenta')
        self.output_area.tag_configure('white', foreground='white')
        self.output_area.tag_configure('output', foreground='white')
        self.output_area.tag_configure('error', foreground='red')
        
    def get_current_line(self) -> str:
        """Get the current command line text."""
        return self.command_entry.get().strip()
        
    def set_current_line(self, text: str) -> None:
        """Set the current command line text."""
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, text)
        
    def update_prompt(self):
        """Update the prompt with current working directory."""
        self.prompt_label.config(text=self.command_executor.working_directory)
        
    def execute_command(self, event=None) -> None:
        """Execute the entered command."""
        # Hide suggestion dropdown
        if self.suggestion_dropdown.is_visible():
            self.suggestion_dropdown.hide()
            
        # Get command
        command = self.get_current_line().strip()
        if not command:
            self.append_output('\n')
            self.update_prompt()
            return
            
        # Store the original command
        original_command = command
        
        # Clear the command entry
        self.command_entry.delete(0, tk.END)
        
        # Echo the command
        self.append_output(f"\n{self.command_executor.working_directory}$ {command}\n")
        
        # If AI mode is enabled and it's not a built-in command, interpret it
        if self.ai_mode.get() and not any(command.startswith(cmd) for cmd in ['cd', 'pwd', 'exit', 'clear', 'history', 'tail']):
            try:
                interpreted_command = self.command_interpreter.interpret(command)
                if interpreted_command:
                    self.append_output(f"Interpreted as: {interpreted_command}\n", 'cyan')
                    command = interpreted_command
            except Exception as e:
                self.append_output(f"Error interpreting command: {str(e)}\n", 'red')
                self.update_prompt()
                return
        
        # Execute the command
        stdout, stderr = self.command_executor.execute(command)
        
        # Handle output
        if stdout is not None:  # Check for None specifically since empty string is valid output
            # For ls command output, format it nicely
            if command.startswith('ls'):
                # Process the output
                lines = stdout.splitlines()
                if lines:
                    for line in lines:
                        if line.strip():
                            self.append_output(line + '\n')
                else:
                    self.append_output("No files found.\n")
            else:
                self.append_output(stdout)
        
        if stderr:
            # Handle common errors more gracefully
            if "command not found" in stderr.lower():
                self.append_output(f"Command not found: {command}\n", 'red')
            elif "permission denied" in stderr.lower():
                self.append_output("Permission denied.\n", 'red')
            else:
                self.append_output(stderr + '\n', 'red')
        
        # Add command to history
        self.command_history.append((original_command, command))
        self.history_index = len(self.command_history)
        
        # Show prompt
        self.update_prompt()
        
    def handle_key(self, event):
        """Handle key events in interactive mode"""
        if not self.in_pty_mode or not self.pty:
            logger.debug("Key event ignored - not in PTY mode")
            return
        
        # Debug logging
        logger.info(f"Key event - keysym: {event.keysym}, state: {event.state}, char: {repr(event.char)}")
        
        # Handle special keys
        if event.state & 0x4:  # Control key is pressed
            if event.keysym in ['c', 'C']:  # Ctrl+C
                logger.info("Sending SIGINT (Ctrl+C)")
                self.pty.write('\x03')  # Send SIGINT
                return "break"
            elif event.keysym in ['d', 'D']:  # Ctrl+D
                logger.info("Sending EOF (Ctrl+D)")
                self.pty.write('\x04')  # Send EOF
                return "break"
            elif event.keysym in ['z', 'Z']:  # Ctrl+Z
                logger.info("Sending SIGTSTP (Ctrl+Z)")
                self.pty.write('\x1A')  # Send SIGTSTP
                return "break"
        # Handle pager keys
        elif event.keysym == 'q':  # Quit
            logger.info("Sending quit command (q)")
            self.pty.write('q')
            return "break"
        elif event.keysym == 'space':  # Next page
            logger.info("Sending next page command (space)")
            self.pty.write(' ')
            return "break"
        elif event.keysym == 'b':  # Previous page
            logger.info("Sending previous page command (b)")
            self.pty.write('b')
            return "break"
        elif event.keysym == 'Return':
            logger.debug("Sending return")
            self.pty.write('\r')
            return "break"
        elif event.keysym == 'BackSpace':
            logger.debug("Sending backspace")
            self.pty.write('\x7f')  # Send backspace
            return "break"
        elif event.keysym == 'Tab':
            logger.debug("Sending tab")
            self.pty.write('\t')
            return "break"
        elif len(event.char) > 0:
            logger.debug(f"Sending character: {repr(event.char)}")
            self.pty.write(event.char)
            return "break"
    
    def handle_key_press(self, event):
        """Handle key press events for real-time suggestions"""
        # Skip if in PTY mode
        if self.in_pty_mode:
            return
            
        # Get current text
        text = self.command_entry.get()
        logger.info(f"Key press event - keysym: {event.keysym}, char: {event.char}, keycode: {event.keycode}")
        logger.info(f"Current text: '{text}'")
        
        # Hide suggestions if no text
        if not text:
            logger.info("No text, hiding suggestions")
            self.suggestion_dropdown.hide()
            return
            
        # Get suggestions
        suggestions = self.command_suggester.get_suggestions(text)
        
        # Show or hide dropdown based on suggestions
        if suggestions:
            # Calculate position below command entry
            x = self.command_entry.winfo_rootx()
            y = self.command_entry.winfo_rooty() + self.command_entry.winfo_height()
            
            # Show dropdown
            self.suggestion_dropdown.show(suggestions, x, y)
        else:
            logger.info("Hiding dropdown")
            self.suggestion_dropdown.hide()
        
    def handle_tab(self, event):
        """Handle tab key press for command completion"""
        if event.state & 0x1:  # Shift is pressed
            if self.suggestion_dropdown.is_visible():
                suggestion = self.suggestion_dropdown.prev_suggestion()
                if suggestion:
                    self.command_entry.delete(0, tk.END)
                    self.command_entry.insert(0, suggestion)
            return 'break'
        else:
            if self.suggestion_dropdown.is_visible():
                suggestion = self.suggestion_dropdown.next_suggestion()
                if suggestion:
                    self.command_entry.delete(0, tk.END)
                    self.command_entry.insert(0, suggestion)
            else:
                # Show suggestions on first tab
                text = self.get_current_line()
                suggestions = self.command_suggester.get_suggestions(text)
                if suggestions:
                    x = self.command_entry.winfo_rootx()
                    y = self.command_entry.winfo_rooty() + self.command_entry.winfo_height()
                    self.suggestion_dropdown.show(suggestions, x, y)
            return 'break'
        
    def history_up(self, event):
        """Handle up arrow key press for command history"""
        self.suggestion_dropdown.hide()
        if self.history_index < len(self.command_history):
            self.history_index += 1
            original_command, interpreted_command = self.command_history[-self.history_index]
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, original_command)
        return 'break'
        
    def history_down(self, event):
        """Handle down arrow key press for command history"""
        self.suggestion_dropdown.hide()
        if self.history_index > 1:
            self.history_index -= 1
            original_command, interpreted_command = self.command_history[-self.history_index]
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, original_command)
        elif self.history_index == 1:
            self.history_index = 0
            self.command_entry.delete(0, tk.END)
        return 'break'
        
    def destroy(self):
        """Clean up resources"""
        if self.pty:
            self.pty.stop()
        super().destroy()

    def pty_callback(self, data):
        """Callback for PTY output"""
        try:
            # Clear and update the output area
            self.output_area.delete(1.0, tk.END)
            self.output_area.insert(tk.END, data)
            
            # Ensure cursor is visible
            self.output_area.see(tk.END)
            
            # Update the display immediately
            self.output_area.update_idletasks()
            
            # Ensure cursor is visible again after update
            self.output_area.see(tk.END)
            
        except Exception as e:
            logger.error(f"Error in PTY callback: {e}")
            
    def pty_exit_callback(self):
        """Callback for PTY exit"""
        try:
            logger.debug("PTY process exited")
            self.in_pty_mode = False
            self.pty = None
            self.append_output("\nInteractive program exited. You can now use normal commands.\n", 'cyan')
            self.command_entry.focus_set()
        except Exception as e:
            logger.error(f"Error in PTY exit callback: {e}")
