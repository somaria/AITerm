"""
Command interpreter for AITerm
"""

import os
import openai
import logging
from ..config import OPENAI_API_KEY, OPENAI_MODEL
from .errors import CommandInterpretationError

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Get logger
logger = logging.getLogger(__name__)

class CommandInterpreter:
    @staticmethod
    def interpret(user_input):
        """
        Interpret natural language input into terminal commands
        """
        logger.info(f"Interpreting command: {user_input}")
        
        # Handle git show commands directly without AI
        lower_input = user_input.lower()
        if any(phrase in lower_input for phrase in ['show last commit', 'show latest commit', 'show current commit']):
            logger.info("Directly interpreting as 'git show HEAD'")
            return 'git show HEAD'
        elif any(phrase in lower_input for phrase in ['show previous commit', 'show earlier commit']):
            logger.info("Directly interpreting as 'git show HEAD^'")
            return 'git show HEAD^'
        
        # Use AI to interpret other commands
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """You are a terminal command interpreter. Convert natural language into appropriate Unix/Linux terminal commands.
                     Rules:
                     1. Respond with ONLY the command, no explanations
                     2. For git commands:
                        - Use 'git show HEAD' for showing the latest/current/last commit
                        - Use 'git show HEAD^' for showing the previous/earlier commit
                        - Use 'git show HEAD~N' for showing N commits ago
                        - Use 'git log -n X' to show last X commits
                        - Use 'git status' to show current status
                        - Use 'git diff' to show uncommitted changes
                     3. For directory navigation:
                        - Use 'pwd' to show current directory
                        - Use 'ls -F' to show files with type indicators
                        - Use 'ls -la' to show all files including hidden
                     4. Keep commands simple and direct
                     5. Use standard Unix commands when possible
                     6. NEVER use ambiguous arguments like 'last' or 'previous' directly - always translate to proper git references like HEAD, HEAD^, etc."""},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=50
            )
            interpreted = response.choices[0].message['content'].strip()
            logger.info(f"AI interpreted command as: {interpreted}")
            
            # Special handling for cd to maintain directory navigation
            if interpreted.startswith('cd '):
                path = interpreted[3:].strip()
                # Expand home directory
                if path == '~' or path.startswith('~/'):
                    path = os.path.expanduser(path)
                # Handle relative paths
                elif not path.startswith('/'):
                    path = os.path.abspath(os.path.join(os.getcwd(), path))
                return f'cd {path}'
            
            logger.info(f"Final command: {interpreted}")
            return interpreted
            
        except Exception as e:
            logger.error(f"Error interpreting command: {str(e)}")
            raise CommandInterpretationError(str(e))

class CommandInterpretationError(Exception):
    """Exception raised when command interpretation fails"""
    pass
