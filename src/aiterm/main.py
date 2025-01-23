"""Main entry point for AITerm."""

import os
import sys
import logging
from dotenv import load_dotenv, find_dotenv
import openai
from .utils.logger import get_logger
from .commands.git_command import GitCommand
from .commands.executor import CommandExecutor
from .utils.logger import cleanup_logs
from .config import OPENAI_API_KEY, OPENAI_MODEL

# Initialize logger
logger = get_logger(__name__)

def setup_openai():
    """Set up OpenAI configuration."""
    try:
        # Get API key from config (which should be loaded from .env)
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in config")
            raise ValueError("OpenAI API key not found in config")
        
        # Print masked API key for debugging
        masked_key = f"{OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}"
        logger.info(f"Setting up OpenAI with API key (masked): {masked_key}")
        
        # Configure OpenAI
        openai.api_key = OPENAI_API_KEY
        
        # Test the API key
        response = openai.Model.list()
        logger.info(f"OpenAI API test successful. Found {len(response['data'])} models")
        
    except Exception as e:
        logger.error(f"Failed to set up OpenAI: {str(e)}")
        raise

def handle_command(args):
    """Handle command execution."""
    try:
        # Join args into a command string
        command_str = " ".join(args).strip()
        logger.info(f"Received command: {command_str}")
        
        # Initialize handlers
        git_handler = GitCommand()
        executor = CommandExecutor()
        
        # First try standard command execution
        processed_cmd = executor._process_command(command_str)
        if processed_cmd != command_str:
            # Command was recognized and processed
            logger.info(f"Executing command directly: {command_str}")
            stdout, stderr = executor.execute(command_str)
            if stderr:
                return f"Error: {stderr}"
            return stdout if stdout else ""
        
        # Then check if this is a git-related command
        git_indicators = {
            'git', 'show', 'log', 'commit', 'push', 'pull', 
            'status', 'branch', 'checkout', 'merge', 'add'
        }
        
        is_git_command = False
        first_word = args[0].lower() if args else ""
        
        # Check various conditions that indicate this is a git command
        if (first_word in git_indicators or
            command_str.startswith('git ') or
            any(indicator in command_str.lower() for indicator in ['commit', 'show last', 'branch'])):
            is_git_command = True
        
        if is_git_command:
            logger.info(f"Handling as git command: {command_str}")
            result = git_handler.execute(command_str)
            return result
            
        # If not recognized as any special command, execute directly
        logger.info(f"Executing command directly: {command_str}")
        stdout, stderr = executor.execute(command_str)
        if stderr:
            return f"Error: {stderr}"
        return stdout if stdout else ""
            
    except Exception as e:
        logger.error(f"Error handling command: {str(e)}")
        return f"Error: {str(e)}"

def start_gui():
    """Start the GUI application."""
    try:
        # Import GUI components only when needed
        import tkinter as tk
        from .gui.terminal_gui import TerminalGUI
        
        root = tk.Tk()
        root.title("AI Terminal")
        
        # Set window size (80% of screen)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create and start terminal GUI
        terminal = TerminalGUI(root)
        root.mainloop()
        return 0
    except Exception as e:
        logger.error(f"Error starting GUI: {str(e)}")
        return 1

def main():
    """Main entry point."""
    try:
        # Set up OpenAI configuration first
        setup_openai()
        
        # Check if we're in command-line mode
        if len(sys.argv) > 1:
            if sys.argv[1] == "cleanup-logs":
                result = cleanup_logs()
                print(result)
                return 0

            # Get all arguments after the script name
            args = sys.argv[1:]
            logger.info(f"Command arguments: {args}")
            
            result = handle_command(args)
            print(result)
            return 0 if result else 1
            
        # If no arguments, start GUI mode
        return start_gui()
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
