"""
Command execution functionality
"""

import os
import subprocess
from typing import Tuple, Optional

class CommandExecutor:
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or os.getcwd()

    def execute(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Execute a shell command and return its output
        """
        try:
            # Add -F flag to ls command if not already present
            if command.startswith('ls') and '-F' not in command:
                command = command.replace('ls', 'ls -F', 1)

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            return result.stdout, result.stderr
        except Exception as e:
            return None, str(e)

    def change_directory(self, path: str = None) -> Tuple[bool, str]:
        """
        Change the current working directory
        """
        try:
            # Handle no path or empty path
            if not path or path.strip() == '':
                new_dir = os.path.expanduser('~')
            else:
                # Expand user paths (e.g., ~ or ~user)
                path = os.path.expanduser(path.strip())
                
                # Handle relative paths
                if not os.path.isabs(path):
                    path = os.path.join(self.working_directory, path)
                
                # Normalize path (resolve .. and .)
                new_dir = os.path.normpath(path)
            
            # Check if directory exists
            if not os.path.exists(new_dir):
                return False, f"Directory not found: {new_dir}"
                
            # Check if it's a directory
            if not os.path.isdir(new_dir):
                return False, f"Not a directory: {new_dir}"
                
            # Change directory
            os.chdir(new_dir)
            self.working_directory = os.getcwd()
            return True, self.working_directory
            
        except PermissionError:
            return False, f"Permission denied: {path}"
        except Exception as e:
            return False, str(e)
