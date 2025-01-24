"""AI-powered command processor using Pydantic."""

import os
from pydantic import BaseModel, Field
from typing import List
import openai
import logging
import subprocess
from ..utils.logger import get_logger
from ..config import OPENAI_MODEL, OPENAI_API_KEY

# Initialize logger
logger = get_logger("aiterm.commands.ai_processor")

class AICommandProcessor:
    """Process natural language into git commands using OpenAI."""
    
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
        
        # Load git command help for better context
        self.git_help = self._load_git_help()
    
    def _load_git_help(self) -> str:
        """Load git command help for context."""
        try:
            result = subprocess.run(['git', 'help', '-a'], 
                                  capture_output=True, 
                                  text=True)
            return result.stdout
        except:
            return ""  # Return empty string if command fails
    
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
    
    def process_command(self, command: str) -> List[str]:
        """Process natural language command into git arguments."""
        logger.info(f"Processing command: {command}")
        
        # Verify API key is still set
        if not openai.api_key:
            logger.error("OpenAI API key not set in process_command")
            raise ValueError("OpenAI API key not properly configured")
        
        try:
            # Check if command is a list command
            if any(word in command.lower() for word in ['list', 'ls', 'files', 'directories']):
                result = self._process_list_command(command)
            else:
                # Create a prompt that includes git command context
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
                
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[{
                        "role": "system",
                        "content": "You are a git command interpreter. Return only the command, no explanations."
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
                
                # Remove 'git' prefix if present
                if result.startswith('git '):
                    result = result[4:]
                    
            logger.info(f"AI interpreted command '{command}' as: {result}")
            return result.split()
            
        except Exception as e:
            logger.error(f"Error processing command with OpenAI: {str(e)}")
            # Fall back to simple splitting if AI fails
            return command.split()
