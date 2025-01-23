"""
Command interpreter for AITerm
"""

import os
import openai
from ..config import OPENAI_API_KEY, OPENAI_MODEL
from .errors import CommandInterpretationError

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

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
        'pwd', 'echo', 'export', 'source', 'alias', 'unalias',
        # Package management
        'brew', 'port',
        # Git commands
        'git', 'svn',
        # Others
        'man', 'history', 'clear', 'exit', 'sudo', 'su', 'whoami', 'open'
    }

    # Common paths and their mappings
    CD_PATHS = {
        'home': '~',
        'downloads': '~/Downloads',  # Fixed capitalization
        'download': '~/Downloads',   # Added common variation
        'documents': '~/Documents',
        'docs': '~/Documents',
        'desktop': '~/Desktop',
        'pictures': '~/Pictures',
        'music': '~/Music',
        'movies': '~/Movies',
        'applications': '/Applications',
        'apps': '/Applications',
        'root': '/',
        'tmp': '/tmp',
        'temp': '/tmp'
    }

    @staticmethod
    def interpret(user_input):
        """
        Interpret natural language input into terminal commands
        """
        # Get the first word (command) and arguments
        parts = user_input.split(maxsplit=1)
        command = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        # Special handling for cd command
        if command == 'cd':
            # If no arguments or just 'cd', go to home directory
            if not args:
                return 'cd ~'
                
            # Clean up the argument
            args = args.strip()
            if args.startswith('cd '):  # Remove duplicate cd if present
                args = args[3:].strip()
                
            # Check if the argument matches any special paths
            arg_lower = args.lower().strip()
            if arg_lower in CommandInterpreter.CD_PATHS:
                return f'cd {CommandInterpreter.CD_PATHS[arg_lower]}'
                
            # Handle special cases
            if arg_lower in ['~', '/', '.', '..', '-']:
                return f'cd {arg_lower}'
                
            # If it's already a path starting with standard markers, use it as is
            if args.startswith(('~', '/', '.')):
                return f'cd {args}'
                
            # If the directory doesn't exist, try AI interpretation
            try:
                response = openai.ChatCompletion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a terminal command interpreter. Convert natural language paths into appropriate Unix/Linux paths. Respond with ONLY the path, no explanations or 'cd' command."},
                        {"role": "user", "content": f"Convert this path: {args}"}
                    ],
                    temperature=0.3,
                    max_tokens=50
                )
                interpreted_path = response.choices[0].message['content'].strip()
                # Remove 'cd' if the AI included it
                if interpreted_path.startswith('cd '):
                    interpreted_path = interpreted_path[3:].strip()
                    
                # If the interpreted path is one of our special paths, use that
                if interpreted_path.lower() in CommandInterpreter.CD_PATHS:
                    return f'cd {CommandInterpreter.CD_PATHS[interpreted_path.lower()]}'
                    
                return f'cd {interpreted_path}'
            except Exception as e:
                raise CommandInterpretationError(str(e))
        
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
