"""
AI Terminal main entry point
"""

import os
import sys
import tkinter as tk
import openai
from dotenv import load_dotenv
from tkinter import ttk, scrolledtext, font as tkfont
import subprocess

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from aiterm.gui.window_manager import WindowManager
from aiterm.utils.logger import get_logger

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')

logger = get_logger()

class TerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Terminal")
        self.current_directory = os.getcwd()
        
        # Configure the main window
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('Terminal.TFrame', background='black')
        self.main_frame['style'] = 'Terminal.TFrame'
        
        # Create terminal output area
        self.terminal_font = tkfont.Font(family="Courier", size=12)
        self.output_area = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            font=self.terminal_font,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.output_area.pack(fill=tk.BOTH, expand=True)
        self.output_area.insert(tk.END, "AI Terminal (type 'exit' to quit)\n")
        self.output_area.insert(tk.END, "You can use natural language commands!\n")
        self.output_area.insert(tk.END, "Examples:\n")
        self.output_area.insert(tk.END, "- 'list the files in this directory'\n")
        self.output_area.insert(tk.END, "- 'show me where I am'\n")
        self.output_area.insert(tk.END, "- 'go to parent directory'\n\n")
        
        # Create command entry
        self.command_frame = ttk.Frame(self.main_frame)
        self.command_frame.pack(fill=tk.X, pady=(5, 0))
        
        # AI mode toggle
        self.ai_mode = tk.BooleanVar(value=True)
        self.ai_toggle = ttk.Checkbutton(
            self.command_frame,
            text="AI",
            variable=self.ai_mode,
            style='Toggle.TCheckbutton'
        )
        self.ai_toggle.pack(side=tk.LEFT, padx=(0, 5))
        
        # Prompt label
        self.prompt_label = tk.Label(
            self.command_frame,
            text=f"{self.current_directory}$ ",
            font=self.terminal_font,
            bg='black',
            fg='green'
        )
        self.prompt_label.pack(side=tk.LEFT)
        
        # Command entry
        self.command_entry = tk.Entry(
            self.command_frame,
            font=self.terminal_font,
            bg='black',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT
        )
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind('<Return>', self.execute_command)
        self.command_entry.focus_set()

    def update_prompt(self):
        self.prompt_label.config(text=f"{self.current_directory}$ ")

    def append_output(self, text, color='white'):
        self.output_area.insert(tk.END, text + '\n')
        self.output_area.see(tk.END)

    def interpret_command(self, user_input):
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a terminal command interpreter. Convert natural language into appropriate Unix/Linux terminal commands. Respond with ONLY the command, no explanations."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=50
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            self.append_output(f"Error interpreting command: {str(e)}", 'red')
            return None

    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        
        # Show command in output area
        self.append_output(f"{self.current_directory}$ {command}", 'green')
        
        if not command:
            return

        # If AI mode is enabled and it's not a built-in command, interpret it
        if self.ai_mode.get() and not any(command.startswith(cmd) for cmd in ['cd', 'pwd', 'exit', 'clear']):
            interpreted_command = self.interpret_command(command)
            if interpreted_command:
                self.append_output(f"Interpreted as: {interpreted_command}", 'cyan')
                command = interpreted_command
        
        try:
            # Handle built-in commands
            if command == 'exit':
                self.root.quit()
            elif command == 'pwd':
                self.append_output(self.current_directory)
            elif command.startswith('cd'):
                # Handle cd command
                parts = command.split(maxsplit=1)
                new_dir = parts[1] if len(parts) > 1 else os.path.expanduser('~')
                os.chdir(new_dir)
                self.current_directory = os.getcwd()
                self.update_prompt()
            elif command == 'clear':
                self.output_area.delete(1.0, tk.END)
            else:
                # Execute other shell commands
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    cwd=self.current_directory
                )
                if result.stdout:
                    self.append_output(result.stdout.rstrip())
                if result.stderr:
                    self.append_output(result.stderr.rstrip(), 'red')

        except FileNotFoundError:
            self.append_output(f"Command not found: {command}", 'red')
        except PermissionError:
            self.append_output("Permission denied", 'red')
        except Exception as e:
            self.append_output(f"Error: {str(e)}", 'red')

def main():
    """Main entry point"""
    logger.info("Starting AI Terminal")
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    # Create window manager
    window_manager = WindowManager.get_instance()
    
    # Create Terminal GUI
    app = TerminalGUI(root)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()