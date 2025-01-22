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
                command.split(),
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
            new_dir = path if path else os.path.expanduser('~')
            os.chdir(new_dir)
            self.working_directory = os.getcwd()
            return True, self.working_directory
        except Exception as e:
            return False, str(e)
