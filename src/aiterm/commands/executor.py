"""
Command execution functionality
"""

import os
import shlex
import subprocess
from typing import Tuple, Dict, List, Optional

from aiterm.commands.ai_command_processor import AICommandProcessor
from aiterm.logger import logger

class CommandExecutor:
    """Execute shell commands with proper handling."""
    
    SPECIAL_COMMANDS = {
        'ls': ['ls', '-F'],  # Always add -F to ls
        'cd': ['cd'],        # cd needs special handling
        'pwd': ['pwd'],      # pwd is straightforward
        'clear': ['clear']   # clear is straightforward
    }
    
    def __init__(self, working_directory: str = None):
        """Initialize command executor."""
        self.working_directory = working_directory or os.getcwd()
        self.ai_processor = AICommandProcessor()
    
    def _process_command(self, command: str) -> str:
        """Process command to handle natural language."""
        try:
            # Use AI to process natural language
            processed = self.ai_processor.process_command(command, command_type='shell')
            logger.debug(f"Processed command '{command}' to '{processed}'")
            return processed
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return command
    
    def execute(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """Execute a command and return stdout and stderr."""
        try:
            # Process natural language command
            processed_command = self._process_command(command)
            
            # Split command into parts
            cmd_parts = shlex.split(processed_command)
            if not cmd_parts:
                return None, "Empty command"
            
            # Get base command
            base_cmd = cmd_parts[0]
            
            # Handle cd command specially
            if base_cmd == 'cd':
                if len(cmd_parts) > 1:
                    path = ' '.join(cmd_parts[1:])  # Handle paths with spaces
                    # Special handling for "cd to home" or similar
                    if 'home' in path.lower():
                        success, result = self.change_directory()
                    else:
                        success, result = self.change_directory(path)
                else:
                    success, result = self.change_directory()
                
                if success:
                    return result, None
                else:
                    return None, result
            
            # Handle other special commands
            if base_cmd in self.SPECIAL_COMMANDS:
                cmd_parts = self.SPECIAL_COMMANDS[base_cmd] + cmd_parts[1:]
            
            # Run command and capture output
            try:
                result = subprocess.run(
                    cmd_parts,
                    cwd=self.working_directory,
                    capture_output=True,
                    text=True
                )
                
                # Keep trailing newlines in stdout but strip from stderr
                stdout = result.stdout if result.stdout else "No results found"  # Return message instead of None
                stderr = result.stderr.rstrip('\n') if result.stderr else None
                
                # If command returned non-zero and has stderr, treat as error
                if result.returncode != 0 and stderr:
                    return None, stderr
                
                return stdout, stderr
                
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                return None, str(e)
                   
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None, str(e)
    
    def change_directory(self, path: str = None) -> Tuple[bool, str]:
        """Change the current working directory."""
        try:
            # Handle no path or empty path
            if not path or path.strip() == '':
                new_dir = os.path.expanduser('~')
            else:
                # Expand user paths (e.g., ~ or ~user)
                path = os.path.expanduser(path.strip())
                
                # Handle relative paths
                if not os.path.isabs(path):
                    new_dir = os.path.join(self.working_directory, path)
                else:
                    new_dir = path
                
                # Normalize path (resolve .. and .)
                new_dir = os.path.normpath(new_dir)
            
            # Check if directory exists and is accessible
            if not os.path.exists(new_dir):
                return False, f"Directory not found: {path if path else ''}"
            if not os.path.isdir(new_dir):
                return False, f"Not a directory: {path if path else ''}"
            
            # Try to change directory
            os.chdir(new_dir)
            self.working_directory = new_dir
            
            # Return relative path if possible
            if not path or path.strip() == '':
                return True, new_dir
            elif os.path.isabs(path):
                return True, new_dir
            else:
                return True, os.path.basename(path)
            
        except PermissionError:
            return False, f"Permission denied: {path if path else ''}"
        except Exception as e:
            return False, str(e)
