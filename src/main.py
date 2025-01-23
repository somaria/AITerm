"""Main entry point for the AI Terminal application."""

import os
import sys
from aiterm.gui.window_manager import WindowManager
from aiterm.commands.git_command import GitCommand
from aiterm.utils.logger import cleanup_logs

def handle_git_command(args):
    """Handle Git command execution."""
    git_handler = GitCommand()
    command_str = " ".join(args).strip()
    return git_handler.execute(command_str)

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "cleanup-logs":
            result = cleanup_logs()
            print(result)
            return

        command = sys.argv[1:]
        result = handle_git_command(command)
        print(result)
        return

    # GUI mode if no commands provided
    window_manager = WindowManager.get_instance()
    window_manager.root.mainloop()

if __name__ == "__main__":
    main()
