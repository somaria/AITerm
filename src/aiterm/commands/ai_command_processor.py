"""AI-powered command processor for interpreting natural language commands."""

import os
import re
from typing import Optional

class AICommandProcessor:
    """Process natural language commands into shell commands using AI."""
    
    def __init__(self):
        """Initialize the AI command processor."""
        self.working_directory = os.path.expanduser('~')
    
    def process_command(self, command: str, command_type: str = 'shell') -> Optional[str]:
        """Process a natural language command into a shell command.
        
        Args:
            command: Natural language command to process
            command_type: Type of command to process ('shell', 'find', etc.)
            
        Returns:
            Processed shell command or None if command cannot be processed
        """
        # Basic command processing without actual AI for now
        # This will be enhanced with real AI processing later
        command = command.lower().strip()
        
        # Process find commands
        if command.startswith("find"):
            return self._process_find_command(command)
            
        # For basic shell commands, return as is
        if command_type == 'shell':
            return command
            
        return command
    
    def _process_find_command(self, command: str) -> str:
        """Process natural language find commands into shell find commands.
        
        Args:
            command: Natural language find command
            
        Returns:
            Shell find command
        """
        parts = command.split()
        find_cmd = ["find", "."]
        
        # Handle type specifications
        if "directory" in command or "directories" in command or "folders" in command:
            find_cmd.extend(["-type", "d"])
        elif "file" in command or "files" in command:
            find_cmd.extend(["-type", "f"])
            
        # Handle size constraints
        size_match = re.search(r"larger than (\d+)(mb|kb|m|k|b)", command)
        if size_match:
            size, unit = size_match.groups()
            unit_map = {"mb": "M", "m": "M", "kb": "k", "k": "k", "b": "c"}
            find_cmd.extend(["-size", f"+{size}{unit_map.get(unit.lower(), 'c')}"])
            
        # Handle time constraints
        if "modified" in command:
            if "today" in command:
                find_cmd.extend(["-mtime", "-1"])
            elif "last 24 hours" in command:
                find_cmd.extend(["-mtime", "-1"])
            elif "last week" in command:
                find_cmd.extend(["-mtime", "-7"])
                
        # Handle name patterns
        if "python" in command:
            find_cmd.extend(['-name', '"*.py"'])
        elif "javascript" in command or "js" in command:
            find_cmd.extend(['-name', '"*.js"'])
        elif "text" in command or "txt" in command:
            find_cmd.extend(['-name', '"*.txt"'])
            
        # Handle multiple extensions
        if "source code" in command:
            find_cmd.extend(['-type', 'f', '\\('])
            find_cmd.extend(['-name', '"*.py"', '-o', '-name', '"*.js"', '-o', '-name', '"*.cpp"', '-o', '-name', '"*.h"'])
            find_cmd.append('\\)')
            
        # Handle permissions
        if "executable" in command:
            find_cmd.append("-executable")
        elif "permission" in command and "777" in command:
            find_cmd.extend(["-perm", "777"])
            
        # Handle ownership
        if "owned by" in command and "current user" in command:
            find_cmd.extend(["-user", "$USER"])
            
        # Handle empty files/directories
        if "empty" in command:
            find_cmd.append("-empty")
            
        return " ".join(find_cmd)
