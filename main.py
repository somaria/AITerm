"""Main entry point for the AI Terminal application."""

import os
import sys
from aiterm.gui.window_manager import WindowManager
from aiterm.commands.git_command import GitCommand
from aiterm.commands.executor import CommandExecutor
from aiterm.utils.logger import cleanup_logs
from aiterm.config import OPENAI_API_KEY, OPENAI_MODEL  # Import OpenAI config
import openai

# Initialize OpenAI configuration
openai.api_key = OPENAI_API_KEY

def handle_command(args):
    """Handle command execution."""
    command_str = " ".join(args).strip()
    
    # Create command handlers
    git_handler = GitCommand()
    cmd_executor = CommandExecutor()
    
    # Check if it's a git command
    if command_str.startswith('git ') or any(word in command_str.lower() for word in ['commit', 'push', 'pull', 'branch', 'status']):
        return git_handler.execute(command_str)
        
    # Handle standard shell commands
    stdout, stderr = cmd_executor.execute(command_str)
    if stderr:
        return stderr
    return stdout

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "cleanup-logs":
            result = cleanup_logs()
            print(result)
            return

        command = sys.argv[1:]
        result = handle_command(command)
        print(result)
        return

    # GUI mode if no commands provided
    window_manager = WindowManager.get_instance()
    window_manager.root.mainloop()

if __name__ == "__main__":
    main()
