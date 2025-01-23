"""
Command execution functionality
"""

import os
import subprocess
from typing import Tuple, Optional
from ..utils.logger import get_logger

logger = get_logger()

class CommandExecutor:
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or os.getcwd()
        self.previous_directory = None  # Store previous directory for cd -

    def execute(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Execute a shell command and return its output
        """
        try:
            # Add -F flag to ls command if not already present
            if command.startswith('ls') and '-F' not in command:
                command = command.replace('ls', 'ls -F', 1)
                
            logger.info(f"Executing command: {command} in {self.working_directory}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            
            # Log output for debugging
            logger.debug(f"Command stdout: {result.stdout}")
            logger.debug(f"Command stderr: {result.stderr}")
            
            return result.stdout, result.stderr
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None, str(e)

    def change_directory(self, path: str = None) -> Tuple[bool, str]:
        """
        Change the current working directory
        """
        try:
            logger.info(f"Changing directory to: {path}")
            
            # Handle no path or empty path
            if not path or path.strip() == '':
                new_dir = os.path.expanduser('~')
            elif path.strip() == '-':
                # Handle cd - to go to previous directory
                if self.previous_directory:
                    new_dir = self.previous_directory
                else:
                    return False, "No previous directory"
            else:
                # Expand user paths (e.g., ~ or ~user)
                path = os.path.expanduser(path.strip())
                
                # Handle relative paths
                if not os.path.isabs(path):
                    # Handle multiple ../ in the path
                    if path == '..' or path.startswith('../') or path.startswith('./'):
                        # Use os.path.abspath to resolve relative paths
                        new_dir = os.path.abspath(os.path.join(self.working_directory, path))
                    else:
                        new_dir = os.path.join(self.working_directory, path)
                else:
                    new_dir = path
                
                # Normalize path (resolve .. and .)
                new_dir = os.path.normpath(new_dir)
                
            logger.info(f"Resolved directory: {new_dir}")
                
            # Check if directory exists
            if not os.path.exists(new_dir):
                return False, f"Directory not found: {new_dir}"
            if not os.path.isdir(new_dir):
                return False, f"Not a directory: {new_dir}"
                
            # Store previous directory before changing
            self.previous_directory = self.working_directory
                
            # Change directory
            os.chdir(new_dir)
            self.working_directory = new_dir
            logger.info(f"Changed directory to: {self.working_directory}")
            return True, new_dir
            
        except Exception as e:
            logger.error(f"Error changing directory: {e}")
            return False, str(e)
