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
        
        prompt = f"""
        Convert this natural language git command to proper git syntax:
        "{command}"
        Return only the git command arguments as a comma-separated list.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip()
            interpreted_command = result.split(",")
            logger.info(f"AI interpreted command: git {' '.join(interpreted_command)}")
            return interpreted_command
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            logger.info(f"Falling back to basic command splitting: {command}")
            return command.split()
