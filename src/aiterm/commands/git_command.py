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
    
    def execute(self, command: str) -> str:
        """Execute a git command with AI interpretation if needed."""
        try:
            # If command already starts with 'git', execute directly
            if command.startswith('git '):
                return self._run_git_command(command)
            
            # Use AI to interpret the command
            logger.info(f"Processing command: {command}")
            git_command = self.ai_processor.process_command(command)
            logger.info(f"AI interpreted command '{command}' as: {git_command}")
            
            return self._run_git_command(git_command)
            
        except Exception as e:
            logger.error(f"Error executing git command: {str(e)}")
            return f"Error: {str(e)}"
    
    def _run_git_command(self, command: str) -> str:
        """Run a git command and return its output."""
        try:
            # Ensure command starts with 'git'
            if not command.startswith('git '):
                command = f"git {command}"
            
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            
            # Check for errors
            if result.stderr:
                return f"Error: {result.stderr}"
            
            return result.stdout if result.stdout else ""
            
        except subprocess.CalledProcessError as e:
            return f"Error: Git command failed with code {e.returncode}: {e.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"
