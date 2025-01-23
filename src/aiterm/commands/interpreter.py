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
    # Standard Unix/macOS commands that should bypass AI interpretation
    STANDARD_COMMANDS = {
        # File operations
        'ls', 'cp', 'mv', 'rm', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown',
        # File viewing/editing
        'cat', 'more', 'less', 'vim', 'vi', 'nano', 'tail', 'head', 'diff',
        # Text processing
        'grep', 'sed', 'awk', 'sort', 'uniq', 'wc', 'cut', 'paste',
        # File search
        'find', 'locate', 'which', 'whereis',
        # Process management
        'ps', 'kill', 'killall', 'top', 'htop',
        # System info
        'df', 'du', 'free', 'mount', 'umount', 'lsof',
        # Network
        'ping', 'netstat', 'curl', 'wget', 'ssh', 'telnet', 'nc',
        # Archive
        'tar', 'gzip', 'gunzip', 'zip', 'unzip',
        # Shell built-ins
        'cd', 'pwd', 'echo', 'export', 'source', 'alias', 'unalias',
        # Package management
        'brew', 'port',
        # Git commands
        'git', 'svn',
        # Others
        'man', 'history', 'clear', 'exit', 'sudo', 'su', 'whoami', 'open'
    }

    @staticmethod
    def interpret(user_input):
        """
        Interpret natural language input into terminal commands
        """
        # Get the first word (command) from the input
        command = user_input.split()[0] if user_input else ""
        
        # Check if input starts with any standard command
        if command in CommandInterpreter.STANDARD_COMMANDS:
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
