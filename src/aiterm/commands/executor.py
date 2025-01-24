"""
Command execution functionality
"""

import os
import shlex
import subprocess
from typing import Tuple, Dict, List, Optional

from aiterm.commands.ai_command_processor import AICommandProcessor
from aiterm.commands.command_suggester import CommandSuggester
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
        self.suggester = CommandSuggester()
    
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
    
    def get_suggestions(self, partial_input: str = "", max_suggestions: int = 3) -> List[str]:
        """Get command suggestions based on current context.
        
        Args:
            partial_input: Partial command input from user
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggested commands
        """
        return self.suggester.suggest_commands(
            partial_input=partial_input,
            max_suggestions=max_suggestions
        )
    
    def _expand_docker_command(self, cmd_parts: List[str]) -> List[str]:
        """Expand partial Docker commands into full commands."""
        if not cmd_parts:
            return cmd_parts
            
        # Common Docker command expansions
        docker_expansions = {
            'i': 'images',
            'im': 'images',
            'img': 'images',
            'p': 'ps',
            'ps': 'ps',
            'r': 'run',
            'e': 'exec',
            'ex': 'exec',
            'l': 'logs',
            's': 'system',
            'sys': 'system',
            'b': 'build',
            'c': 'container',
            'cont': 'container',
            'v': 'volume',
            'n': 'network',
            'net': 'network',
            'cp': 'cp',
            'rm': 'rm',
            'rmi': 'rmi',
            'h': 'help',
            'i': 'inspect',
            'in': 'inspect',
            'st': 'stats',
            'stats': 'stats',
        }
        
        # Docker-compose expansions
        compose_expansions = {
            'u': 'up',
            'up': 'up',
            'd': 'down',
            'down': 'down',
            'p': 'ps',
            'ps': 'ps',
            'l': 'logs',
            'log': 'logs',
            'r': 'restart',
            'rs': 'restart',
            'b': 'build',
            'c': 'config',
            'cf': 'config',
            'e': 'exec',
            'ex': 'exec',
            'pull': 'pull',
            'push': 'push',
            'st': 'start',
            'sp': 'stop',
            'rm': 'rm',
            'run': 'run',
        }
        
        base_cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # First check if it's a docker command
        if base_cmd in ['docker', 'dock', 'doc', 'do', 'd', 'dk']:
            # It's a docker command
            if not args:
                return ['docker']
                
            # Check if it's a compose command
            if args[0] in ['c', 'comp', 'compose', '-c', 'dc']:
                compose_args = args[1:] if len(args) > 1 else []
                if not compose_args:
                    return ['docker-compose']
                    
                # Handle special flags
                if compose_args[0].startswith('-'):
                    return ['docker-compose'] + compose_args
                    
                # Expand compose subcommand
                if compose_args[0] in compose_expansions:
                    expanded = ['docker-compose', compose_expansions[compose_args[0]]] + compose_args[1:]
                    return expanded
                    
                # Handle special case for 'up -d'
                if compose_args[0] == 'up' and len(compose_args) > 1 and compose_args[1] == '-d':
                    return ['docker-compose', 'up', '-d'] + compose_args[2:]
                    
                return ['docker-compose'] + compose_args
            
            # Regular docker command
            if args[0] in docker_expansions:
                expanded = ['docker', docker_expansions[args[0]]] + args[1:]
                return expanded
                
            # Handle special case for system commands
            if args[0] == 'system' and len(args) > 1:
                if args[1] in ['p', 'pr', 'prune']:
                    return ['docker', 'system', 'prune'] + args[2:]
                    
            return ['docker'] + args
            
        # Check if it's a direct docker-compose command
        if base_cmd in ['docker-compose', 'docker-c', 'dcomp', 'd-c', 'dc']:
            if not args:
                return ['docker-compose']
                
            # Handle special flags
            if args[0].startswith('-'):
                return ['docker-compose'] + args
                
            if args[0] in compose_expansions:
                expanded = ['docker-compose', compose_expansions[args[0]]] + args[1:]
                return expanded
                
            # Handle special case for 'up -d'
            if args[0] == 'up' and len(args) > 1 and args[1] == '-d':
                return ['docker-compose', 'up', '-d'] + args[2:]
                
            return ['docker-compose'] + args
            
        return cmd_parts
    
    def execute(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """Execute a command and return stdout and stderr."""
        try:
            # Split command into parts
            cmd_parts = shlex.split(command)
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
                    self.suggester.record_command(command, self.working_directory, exit_code=0)
                    return "", None
                else:
                    self.suggester.record_command(command, self.working_directory, exit_code=1)
                    return None, result
            
            # Handle ls command specially
            if base_cmd == 'ls':
                # Always use shell=True for ls to handle wildcards
                # Split command and rebuild with proper spacing
                cmd_parts = command.split()
                base = cmd_parts[0]  # 'ls'
                args = []
                
                # Add color flag first
                args.append('--color=always')
                
                # Add any other flags (starting with -)
                flags = [arg for arg in cmd_parts[1:] if arg.startswith('-')]
                args.extend(flags)
                
                # Add remaining arguments
                other_args = [arg for arg in cmd_parts[1:] if not arg.startswith('-')]
                args.extend(other_args)
                
                # Build final command
                command = f"{base} {' '.join(args)}"
                
                result = subprocess.run(
                    command,
                    cwd=self.working_directory,
                    capture_output=True,
                    text=True,
                    shell=True,
                    env={"LANG": "en_US.UTF-8", "TERM": "xterm-256color"}  # Ensure consistent output
                )
                
                # Record command in history
                self.suggester.record_command(
                    command=command,
                    working_dir=self.working_directory,
                    exit_code=result.returncode,
                    output=result.stdout if result.stdout else result.stderr
                )
                
                # For ls command, always return stdout (even if empty) and only return stderr on error
                if result.returncode == 0:
                    return result.stdout.rstrip('\n') if result.stdout else "", None
                else:
                    return None, result.stderr.rstrip('\n') if result.stderr else "Unknown error"
            
            # For other commands, use normal execution
            try:
                result = subprocess.run(
                    cmd_parts,
                    cwd=self.working_directory,
                    capture_output=True,
                    text=True
                )
                
                # Record command in history
                self.suggester.record_command(
                    command=command,
                    working_dir=self.working_directory,
                    exit_code=result.returncode,
                    output=result.stdout if result.stdout else result.stderr
                )
                
                # If command returned non-zero and has stderr, treat as error
                if result.returncode != 0 and result.stderr:
                    return None, result.stderr.rstrip('\n')
                
                return result.stdout.rstrip('\n') if result.stdout else "", result.stderr.rstrip('\n') if result.stderr else None
                
            except FileNotFoundError:
                logger.error(f"Command not found: {base_cmd}")
                self.suggester.record_command(
                    command=command,
                    working_dir=self.working_directory,
                    exit_code=127  # Standard "command not found" exit code
                )
                return None, f"Command not found: {base_cmd}"
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                self.suggester.record_command(
                    command=command,
                    working_dir=self.working_directory,
                    exit_code=1,
                    output=str(e)
                )
                return None, str(e)
                   
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None, str(e)
    
    def change_directory(self, path: str = None) -> Tuple[bool, str]:
        """Change current working directory.
        
        Args:
            path: Path to change to. If None, changes to home directory
            
        Returns:
            Tuple of (success, error_message)
            success: True if directory was changed successfully
            error_message: None if successful, error message if failed
        """
        if path is None:
            path = os.path.expanduser('~')
        
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.working_directory, path)
            
            # Resolve path and check if exists
            path = os.path.realpath(path)
            
            # Check if path exists first
            if not os.path.exists(path):
                return False, "Directory does not exist"
            
            # Then check if it's a directory
            if not os.path.isdir(path):
                return False, "Not a directory"
            
            self.working_directory = path
            return True, None
            
        except Exception as e:
            return False, str(e)
