"""
Command interpreter for AITerm
"""

import os
import openai
from ..config import OPENAI_MODEL
from .errors import CommandInterpretationError
from .git_command import GitCommand
from .ai_command_processor import AICommandProcessor

class CommandInterpreter:
    """Interprets natural language commands into executable commands."""
    
    # Commands that should bypass AI interpretation
    STANDARD_COMMANDS = {
        'ls', 'cd', 'pwd', 'mkdir', 'touch', 'rm', 'cp', 'mv',
        'cat', 'less', 'more', 'head', 'tail', 'grep', 'find',
        'ps', 'top', 'kill', 'chmod', 'chown', 'df', 'du'
    }
    
    def __init__(self):
        """Initialize command interpreter."""
        self.ai_processor = AICommandProcessor()
        self.git_handler = GitCommand()
    
    def is_git_command(self, command: str) -> bool:
        """Check if this is a git-related command."""
        command = command.lower().strip()
        
        # Common git-related keywords
        git_indicators = {
            'git', 'commit', 'push', 'pull', 'branch', 'merge',
            'show', 'log', 'status', 'add', 'reset', 'checkout'
        }
        
        # Check various conditions
        first_word = command.split()[0] if command else ""
        return (
            first_word in git_indicators or
            command.startswith('git ') or
            any(indicator in command for indicator in ['commit', 'show last', 'branch'])
        )
        
    def is_list_command(self, command: str) -> bool:
        """Check if command is a list command."""
        command = command.lower()
        list_keywords = ['list', 'ls', 'show', 'display', 'files', 'directories', 'dir', 'folder']
        return any(keyword in command for keyword in list_keywords)
        
    def interpret(self, command: str) -> str:
        """Interpret a natural language command into an executable command."""
        # Handle empty commands
        if not command:
            return ""
            
        # Handle list commands
        if self.is_list_command(command):
            # Basic ls command
            ls_cmd = []
            
            # Start with base command
            ls_cmd.append('ls')
            
            # Add options based on command
            if any(word in command.lower() for word in ['all', 'hidden']):
                ls_cmd.append('-a')
                
            if 'long' in command.lower() or 'details' in command.lower():
                ls_cmd.append('-l')
                
            # Handle different listing types
            if 'python' in command.lower() or '.py' in command.lower():
                ls_cmd.append('*.py')
            elif 'javascript' in command.lower() or '.js' in command.lower():
                ls_cmd.append('*.js')
            elif 'markdown' in command.lower() or '.md' in command.lower():
                ls_cmd.append('*.md')
            elif 'text' in command.lower() or '.txt' in command.lower():
                ls_cmd.append('*.txt')
            elif any(word in command.lower() for word in ['directory', 'folder', 'directories', 'folders']):
                ls_cmd.extend(['-d', '*/'])
                
            return ' '.join(ls_cmd)
            
        # Handle git commands through git handler
        if self.is_git_command(command):
            return self.git_handler.execute(command)
            
        # Handle standard commands directly, except for list-related commands
        first_word = command.split()[0].lower() if command else ""
        if first_word in self.STANDARD_COMMANDS and not self.is_list_command(command):
            return command
            
        # Use AI interpretation for other commands
        return self.ai_processor.process_command(command)

class AICommandProcessor:
    # ... existing code ...

    def _process_list_command(self, command: str) -> str:
        """Process a command that lists files or directories."""
        # Basic ls command
        ls_cmd = "ls"
        
        # Add options based on command
        if any(word in command.lower() for word in ['all', 'hidden']):
            ls_cmd += " -a"
            
        if 'long' in command.lower() or 'details' in command.lower():
            ls_cmd += " -l"
            
        # Handle different listing types
        if 'python' in command.lower() or '.py' in command.lower():
            ls_cmd += " *.py"
        elif 'javascript' in command.lower() or '.js' in command.lower():
            ls_cmd += " *.js"
        elif 'markdown' in command.lower() or '.md' in command.lower():
            ls_cmd += " *.md"
        elif 'text' in command.lower() or '.txt' in command.lower():
            ls_cmd += " *.txt"
        elif 'directory' in command.lower() or 'folder' in command.lower() or 'directories' in command.lower():
            ls_cmd += " -d */"
        
        return ls_cmd

class CommandInterpretationError(Exception):
    """Exception raised when command interpretation fails"""
    pass
