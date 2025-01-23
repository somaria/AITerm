"""
Git command handling.
"""

import subprocess
from typing import Optional
from .ai_command_processor import AICommandProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GitCommand:
    """Handle git commands with AI interpretation."""
    
    def __init__(self, working_directory: Optional[str] = None):
        """Initialize git command handler."""
        self.working_directory = working_directory
        self.ai_processor = AICommandProcessor()
        
        # Common git command patterns
        self.command_patterns = {
            'show last': self._handle_show_last,
            'log last': self._handle_show_last,
            'recent': self._handle_show_last,
        }
    
    def _handle_show_last(self, args: list) -> str:
        """Handle 'git show last N commits' pattern with improved formatting"""
        try:
            # Parse number of commits
            n = 1  # Default to 1 commit
            for i, arg in enumerate(args):
                if arg.isdigit():
                    n = int(arg)
                    break
            
            # Build the git log command with more detailed output
            cmd = [
                "git log",
                f"-{n}",
                "--pretty=format:'%C(yellow)%h%Creset - %s %C(green)(%cr)%Creset %C(blue)<%an>%Creset'",
                "--abbrev-commit",
                "--no-merges"  # Exclude merge commits for cleaner output
            ]
            
            # Add section markers for clarity
            output = self._run_git_command(' '.join(cmd))
            if not output.startswith('Error'):
                return f"=== Last {n} Commit(s) ===\n{output}\n===================="
            return output
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def execute(self, command: str) -> str:
        """Execute a git command with AI interpretation if needed."""
        try:
            # Split command into parts
            parts = command.split()
            if not parts:
                return "Error: Empty command"
            
            # Direct git command
            if command.startswith('git '):
                return self._run_git_command(command, raw_output=True)
            
            # Use AI to interpret the command
            logger.info(f"Processing command: {command}")
            git_command = self.ai_processor.process_command(command)
            logger.info(f"AI interpreted command '{command}' as: {git_command}")
            
            # Return AI output in testing mode
            if hasattr(self, '_testing') and self._testing:
                return git_command
            
            return self._run_git_command(git_command)
            
        except Exception as e:
            logger.error(f"Error executing git command: {str(e)}")
            return f"Error: {str(e)}"

    def _run_git_command(self, command: str, raw_output: bool = False) -> str:
        """Run a git command and return its output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            
            # Handle error cases
            if result.stderr and not result.stdout:
                return f"Error: {result.stderr}"
            
            # Return raw output if requested or in testing mode
            if raw_output or (hasattr(self, '_testing') and self._testing):
                return result.stdout.strip()
            
            # Format output based on command type
            cmd_type = command.split()[1] if len(command.split()) > 1 else ""
            if cmd_type == "status":
                return f"=== Git Status ===\n{result.stdout.strip()}\n================"
            elif cmd_type == "log":
                return f"=== Git log Output ===\n{result.stdout.strip()}\n===================="
            elif cmd_type == "diff":
                return f"=== Git Diff ===\n{result.stdout.strip()}\n=============="
            else:
                return result.stdout.strip()
                
        except Exception as e:
            return f"Error: {str(e)}"
