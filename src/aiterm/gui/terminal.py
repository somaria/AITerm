"""
Terminal GUI implementation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import font as tkfont
import os
import pty
import termios
import select
import fcntl
import struct
import signal
import threading
import queue
import subprocess
import re
import math
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

class TerminalGUI:
    def __init__(self, parent):
        """Initialize terminal GUI"""
        self.parent = parent  # Store the parent
        # Create main frame
        self.frame = ttk.Frame(self.parent)
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
        self.pty = None
        self.in_pty_mode = False
        
        # Create suggestion dropdown
        self.suggestion_dropdown = SuggestionDropdown(self.frame)
        self.suggestion_dropdown.withdraw()  # Hide initially
        
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
        self.command_entry.bind('<KP_Enter>', self.execute_command)  # Numpad Enter
        self.command_entry.bind('<Up>', self._history_up)
        self.command_entry.bind('<Down>', self._history_down)
        self.command_entry.bind('<Tab>', self._handle_tab)
        self.command_entry.bind('<Shift-Tab>', self._handle_tab)  # Add Shift-Tab binding
        self.command_entry.bind('<ISO_Left_Tab>', self._handle_tab)  # Alternative Shift-Tab binding
        self.command_entry.bind('<KeyRelease>', self._handle_key_release)
        self.command_entry.bind('<Escape>', self._hide_suggestions)
        
        # Focus command entry
        self.command_entry.focus_set()
        
        # Calculate terminal size based on font
        font = tkfont.Font(font=('Courier', 12))
        char_width = font.measure('0')
        char_height = font.metrics()['linespace']
        self.term_cols = 80
        self.term_rows = 24
        
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
    
    def update_prompt(self):
        """Update the command prompt"""
        # Get current working directory
        cwd = self.command_executor.working_directory
        
        # Replace home directory with ~
        home = os.path.expanduser("~")
        if cwd.startswith(home):
            cwd = "~" + cwd[len(home):]
            
        # Update directory label
        self.prompt_label.config(text=cwd)
            
        # Set prompt
        prompt = f"\n{cwd}$ "
        self.append_output(prompt)
        
    def append_output(self, text, color='white'):
        """Append text to the output area"""
        if not text:
            return
            
        # Add newline if text doesn't end with one
        if not text.endswith('\n'):
            text += '\n'
            
        # Get current position
        current = self.output_area.index(tk.END)
        
        # Insert text
        self.output_area.insert(tk.END, text)
        
        # Apply color tag
        start = current
        end = self.output_area.index(tk.END)
        self.output_area.tag_add(color, start, end)
        
        # Scroll to end
        self.output_area.see(tk.END)
    
    def execute_command(self, event=None):
        """Execute the entered command"""
        # Hide suggestions first
        self._hide_suggestions()
        
        # Get command text
        command = self.command_entry.get().strip()
        if not command:
            return 'break'
            
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Clear command entry
        self.command_entry.delete(0, tk.END)
        
        try:
            # Show command in output
            self.append_output(f"\n{self.command_executor.working_directory}$ {command}")
            
            # Execute command
            if self.in_pty_mode:
                # In PTY mode, send command directly to PTY
                self.pty.write(command + '\n')
            else:
                # Use command interpreter in AI mode
                if self.ai_mode.get():
                    from ..commands.interpreter import CommandInterpreter
                    try:
                        interpreted_command = CommandInterpreter.interpret(command)
                        logger.info(f"Interpreted command '{command}' as '{interpreted_command}'")
                        stdout, stderr = self.command_executor.execute(interpreted_command)
                    except Exception as e:
                        self.append_output(f"Error interpreting command: {str(e)}", 'red')
                        return 'break'
                else:
                    # Execute command directly in non-AI mode
                    stdout, stderr = self.command_executor.execute(command)
                
                if stdout:
                    self.append_output(stdout)
                if stderr:
                    self.append_output(f"Error: {stderr}", 'red')
                
                # Update prompt if directory changed
                self.update_prompt()
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            self.append_output(f"Error: {str(e)}", 'red')
            
        return 'break'
    
    def start_pty_mode(self, command):
        """Start PTY mode with the given command"""
        logger.debug(f"Starting PTY mode with command: {command}")
        
        # Stop existing PTY if any
        if self.pty:
            logger.debug("Stopping existing PTY")
            self.pty.stop()
            self.pty = None
        
        # Create new PTY
        self.pty = PseudoTerminal(self.pty_callback, self.pty_exit_callback, rows=self.term_rows, cols=self.term_cols)
        
        try:
            # Start PTY with command
            self.pty.start(command)
            self.in_pty_mode = True
            
            # Show help message for interactive mode
            self.append_output("\nEntered interactive mode. Use Ctrl+C to exit, Ctrl+D for EOF, Ctrl+Z to suspend.\n", 'cyan')
            
            # Bind key events for PTY input
            self.output_area.bind('<Key>', self.handle_key)
            self.output_area.bind('<Control-c>', lambda e: self.handle_key(e))
            self.output_area.bind('<Control-d>', lambda e: self.handle_key(e))
            self.output_area.bind('<Control-z>', lambda e: self.handle_key(e))
            self.output_area.focus_set()
            
        except Exception as e:
            logger.error(f"Failed to start PTY mode: {e}")
            self.pty = None
            self.in_pty_mode = False
            self.append_output(f"\nError starting interactive mode: {e}\n", 'red')
            return
    
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
    
    def _handle_tab(self, event=None):
        """Handle tab key press"""
        logger.info("Tab pressed")
        
        # Check if dropdown is visible
        if self.suggestion_dropdown.is_visible():
            # Get next/prev suggestion based on shift key
            if event.state & 0x1:  # Shift is pressed
                suggestion = self.suggestion_dropdown.prev_suggestion()
                logger.info(f"Selected previous suggestion: {suggestion}")
            else:
                suggestion = self.suggestion_dropdown.next_suggestion()
                logger.info(f"Selected next suggestion: {suggestion}")
                
            if suggestion:
                # Update command entry with suggestion
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, suggestion)
        else:
            # Show suggestions if not visible
            self._update_suggestions()
            
        return 'break'  # Prevent default tab behavior
        
    def _handle_key_release(self, event):
        """Handle key release events for command entry"""
        # Ignore special keys
        if event.keysym in {'Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                           'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right'}:
            logger.debug(f"Ignoring special key: {event.keysym}")
            return
            
        # Get current text
        current_text = self.command_entry.get()
        logger.debug(f"Key released: {event.keysym}, current text: {current_text}")
        
        # Update suggestions
        self._update_suggestions(current_text)
        
    def _hide_suggestions(self, event=None):
        """Hide suggestion dropdown"""
        if self.suggestion_dropdown.is_visible():
            self.suggestion_dropdown.hide()
            
    def _update_suggestions(self, text=None):
        """Update suggestions based on current text"""
        if text is None:
            text = self.command_entry.get()
            
        logger.info(f"Updating suggestions for text: '{text}'")
        
        # Get suggestions from completer
        try:
            suggestions = self.completer.get_suggestions(text)
            logger.info(f"Got suggestions: {suggestions}")
            
            if suggestions:
                # Show dropdown below command entry
                x = self.command_entry.winfo_rootx()
                y = self.command_entry.winfo_rooty() + self.command_entry.winfo_height()
                self.suggestion_dropdown.show(suggestions, x, y)
            else:
                self._hide_suggestions()
                
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            self._hide_suggestions()

    def _history_up(self, event):
        """Handle up arrow key press for command history"""
        self._hide_suggestions()
        if self.history_index < len(self.command_history):
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[-self.history_index])
        return 'break'
        
    def _history_down(self, event):
        """Handle down arrow key press for command history"""
        self._hide_suggestions()
        if self.history_index > 1:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[-self.history_index])
        elif self.history_index == 1:
            self.history_index = 0
            self.command_entry.delete(0, tk.END)
        return 'break'
        
    def _on_frame_resize(self, event):
        """Update entry width when frame is resized"""
        self.entry_frame.create_window(12, 16, window=self.command_entry,  
                                     anchor='w', width=event.width - 24)  

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
