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
        'downloads': '~/Downloads',
        'download': '~/Downloads',
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
        # Get the first word (command)
        parts = user_input.split(maxsplit=1)
        command = parts[0] if parts else ""

        # If it's a standard command with proper syntax, use it directly
        if command in CommandInterpreter.STANDARD_COMMANDS:
            # Check if it's a complete command (has expected syntax)
            if CommandInterpreter._is_valid_command(user_input):
                return user_input

        # Special handling for cd command to maintain directory navigation
        if command == 'cd':
            args = parts[1] if len(parts) > 1 else ""
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
                
            # Handle ... as ../..
            if arg_lower == '...':
                return 'cd ../..'
            elif arg_lower == '....':
                return 'cd ../../..'
            elif arg_lower == '.....':
                return 'cd ../../../..'
                
            # If it's already a path starting with standard markers, use it as is
            if args.startswith(('~', '/', '.')):
                return f'cd {args}'

        # Use AI to interpret the command
        try:
            response = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """You are a terminal command interpreter. Convert natural language into appropriate Unix/Linux terminal commands.
                     - Respond with ONLY the command, no explanations
                     - For git log commands, always include -n to limit output
                     - For ls commands, prefer -F to show file types
                     - Never use cd - in git commands
                     - Keep commands simple and direct"""},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=50
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            raise CommandInterpretationError(str(e))

    @staticmethod
    def _is_valid_command(command_str):
        """Check if the command string has valid syntax for standard commands"""
        parts = command_str.split()
        if not parts:
            return False
            
        base_cmd = parts[0]
        
        # Common command patterns
        if base_cmd == 'ls' and len(parts) <= 2:  # ls or ls <dir>
            return True
        if base_cmd == 'cd' and len(parts) <= 2:  # cd or cd <dir>
            return True
        if base_cmd == 'git' and len(parts) >= 2:  # git <subcommand> [args]
            return True
        if base_cmd in ['pwd', 'clear']:  # Commands with no args
            return len(parts) == 1
            
        # For other commands, require proper flag syntax
        for part in parts[1:]:
            if part.startswith('-') and not part.startswith('--'):
                if not all(c.isalpha() for c in part[1:]):
                    return False
                    
        return True

class CommandInterpretationError(Exception):
    """Exception raised when command interpretation fails"""
    pass
