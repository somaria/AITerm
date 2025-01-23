"""AI-powered command processor using Pydantic."""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
import openai
import logging
from ..utils.logger import get_logger

load_dotenv()
# Initialize logger with module name
logger = get_logger("aiterm.commands.ai_processor")

class AICommandProcessor:
    """Process natural language into git commands using OpenAI."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment")
        openai.api_key = self.api_key
    
    def process_command(self, command: str) -> List[str]:
        """Process natural language command into git arguments."""
        logger.info(f"Processing command: {command}")
        
        # Strip 'git' prefix if present
        command = command.strip()
        if command.startswith('git '):
            command = command[4:]
        
        # Pre-defined patterns processing
        if "show last" in command or "last" in command:
            parts = command.split()
            try:
                last_index = parts.index("last")
                if len(parts) > last_index + 1 and parts[last_index + 1].isdigit():
                    count = parts[last_index + 1]
                    interpreted = ["log", "--oneline", f"-{count}"]
                    logger.info(f"Pattern matched - Interpreted as: git {' '.join(interpreted)}")
                    return interpreted
            except ValueError:
                pass
        
        # If no pattern matches, use OpenAI
        try:
            prompt = f"""
            Convert this git command to proper syntax:
            "{command}"
            If it's asking to show recent commits, always use "log --oneline -N" format.
            Return only the command arguments as a comma-separated list.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip()
            interpreted = result.split(",")
            logger.info(f"AI interpreted command: git {' '.join(interpreted)}")
            return interpreted
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return command.split()
