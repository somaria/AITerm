"""
AI-powered command interpreter using OpenAI
"""

import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')

class CommandInterpreter:
    @staticmethod
    def interpret(user_input):
        """
        Interpret natural language input into terminal commands
        """
        # Check if input is already a valid shell command
        if any(user_input.startswith(cmd) for cmd in ['ls', 'cd', 'pwd', 'cat', 'more', 'less', 'vim', 'vi', 'nano', 'grep', 'find', 'echo']):
            return user_input
            
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a terminal command interpreter. Convert natural language into appropriate Unix/Linux terminal commands. Respond with ONLY the command, no explanations."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=50
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            raise CommandInterpretationError(str(e))

class CommandInterpretationError(Exception):
    """Exception raised when command interpretation fails"""
    pass
