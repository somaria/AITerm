"""
AI Command Processor for interpreting natural language commands
"""

import openai
import logging
import subprocess
from typing import List, Union
from ..utils.logger import get_logger
from ..config import OPENAI_MODEL, OPENAI_API_KEY

logger = get_logger(__name__)

class AICommandProcessor:
    """Process natural language into shell and git commands using OpenAI."""
    
    def __init__(self):
        """Initialize AI command processor."""
        # Set OpenAI API key
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in config")
            raise ValueError("OpenAI API key not found in config")
        
        # Print masked API key for debugging
        masked_key = f"{OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}"
        logger.info(f"Initializing AI processor with API key (masked): {masked_key}")
        
        openai.api_key = OPENAI_API_KEY
        logger.info(f"Using OpenAI model: {OPENAI_MODEL}")
        
        # Load command help for better context
        self.git_help = self._load_git_help()
        self.shell_help = self._load_shell_help()
    
    def _load_git_help(self) -> str:
        """Load git command help for context."""
        try:
            result = subprocess.run(['git', 'help', '-a'], 
                                  capture_output=True, 
                                  text=True)
            return result.stdout
        except:
            return ""  # Return empty string if command fails
            
    def _load_shell_help(self) -> str:
        """Load shell command help for context."""
        common_commands = """
        Common shell commands:
        pwd - Print working directory
        ls - List directory contents
        cd - Change directory
        mkdir - Create directory
        rm - Remove files or directories
        cp - Copy files or directories
        mv - Move/rename files or directories
        cat - Display file contents
        grep - Search for patterns
        find - Search for files
        clear - Clear terminal screen
        """
        return common_commands
    
    def process_command(self, command: str, command_type: str = 'auto') -> Union[List[str], str]:
        """Process natural language command into shell or git command.
        
        Args:
            command: Natural language command to process
            command_type: Type of command to interpret ('git', 'shell', or 'auto')
        """
        logger.info(f"Processing command: {command}")
        
        # Verify API key is still set
        if not openai.api_key:
            logger.error("OpenAI API key not set in process_command")
            raise ValueError("OpenAI API key not properly configured")
            
        # Determine command type if auto
        if command_type == 'auto':
            if any(word in command.lower() for word in ['git', 'commit', 'push', 'pull', 'branch', 'merge']):
                command_type = 'git'
            else:
                command_type = 'shell'
        
        try:
            # Create appropriate prompt based on command type
            if command_type == 'git':
                prompt = f"""You are a git command interpreter. Convert natural language into the correct git command.
                Available git commands and their descriptions:
                {self.git_help}
                
                Rules:
                1. Return ONLY the git command, no explanations
                2. Do not include the word 'git' at the start
                3. Use proper git command syntax
                4. For show/log commands, prefer using -n N format
                5. If unsure, use a safe command like 'status'
                
                Convert this to a git command: {command}
                """
            else:
                prompt = f"""You are a shell command interpreter. Convert natural language into the correct shell command.
                Available shell commands:
                {self.shell_help}
                
                Rules:
                1. Return ONLY the shell command, no explanations
                2. Use proper shell command syntax
                3. For ls, always add -F flag unless other flags are specified
                4. For cd with no path, use home directory
                5. For file search commands:
                   - Use 'find . -name "pattern"' for exact name matches
                   - Use 'find . -iname "pattern"' for case-insensitive matches
                   - Use 'find . -type f -name "pattern"' to search only files
                   - Use 'find . -type d -name "pattern"' to search only directories
                6. If unsure, return the command as-is
                
                Convert this to a shell command: {command}
                """
            
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{
                    "role": "system",
                    "content": f"You are a {command_type} command interpreter. Return only the command, no explanations."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1,  # Low temperature for more consistent output
                max_tokens=50,    # Commands are short
                presence_penalty=-0.5,  # Encourage using known commands
                frequency_penalty=-0.5   # Encourage common command patterns
            )
            
            # Extract and clean the command
            result = response.choices[0].message.content.strip()
            
            # Remove 'git' prefix if present for git commands
            if command_type == 'git' and result.startswith('git '):
                result = result[4:]
                
            logger.info(f"AI interpreted command '{command}' as: {result}")
            
            # For git commands, split into arguments
            if command_type == 'git':
                return result.split()
            
            # For shell commands, return as string
            return result
            
        except Exception as e:
            logger.error(f"Error processing command with OpenAI: {str(e)}")
            # Fall back to simple command cleaning
            if command_type == 'git':
                return command.split()
            return command
