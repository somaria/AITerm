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
    """Interprets and processes commands."""
    
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
    
    def interpret(self, command: str) -> str:
        """Interpret the command and return the processed version."""
        if not command:
            return command
            
        # Handle git commands through git handler
        if self.is_git_command(command):
            return self.git_handler.execute(command)
            
        # Handle standard commands directly
        first_word = command.split()[0].lower() if command else ""
        if first_word in self.STANDARD_COMMANDS:
            return command
            
        # Use AI interpretation for other commands
        return self.ai_processor.process_command(command)

class CommandInterpretationError(Exception):
    """Exception raised when command interpretation fails"""
    pass
