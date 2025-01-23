"""
Tab completion functionality for the terminal
"""

import os
import glob
import readline
from difflib import get_close_matches
from ..utils.logger import get_logger

logger = get_logger()

class TerminalCompleter:
    def __init__(self):
        self.matches = []
        # Expanded command set
        self.commands = {
            'git': {
                'description': 'Git version control',
                'subcommands': [
                    'status', 'add', 'commit', 'push', 'pull', 'checkout', 'branch',
                    'merge', 'rebase', 'fetch', 'clone', 'init', 'log', 'diff',
                    'stash', 'remote', 'reset', 'tag'
                ]
            },
            'docker': {
                'description': 'Docker container management',
                'subcommands': [
                    'ps', 'images', 'run', 'exec', 'build', 'pull', 'push',
                    'logs', 'stop', 'start', 'restart', 'rm', 'rmi', 'network',
                    'volume', 'compose'
                ]
            },
            'file': {
                'description': 'File operations',
                'commands': ['ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'touch']
            },
            'text': {
                'description': 'Text operations',
                'commands': ['cat', 'less', 'more', 'vim', 'nano', 'head', 'tail']
            },
            'search': {
                'description': 'Search operations',
                'commands': ['grep', 'find', 'locate', 'which']
            },
            'process': {
                'description': 'Process management',
                'commands': ['ps', 'kill', 'top']
            },
            'network': {
                'description': 'Network operations',
                'commands': ['ping', 'curl', 'wget', 'ssh']
            },
            'archive': {
                'description': 'Archive operations',
                'commands': ['tar', 'gzip', 'zip', 'unzip']
            },
            'package': {
                'description': 'Package management',
                'commands': ['pip', 'brew']
            },
            'other': {
                'description': 'Other commands',
                'commands': ['echo', 'clear', 'python', 'node']
            }
        }
        
        # Flatten commands for quick lookup
        self.all_commands = set()
        for category in self.commands.values():
            if 'commands' in category:
                self.all_commands.update(category['commands'])
            if 'subcommands' in category:
                self.all_commands.add(category['description'].split()[0].lower())

        logger.info(f"Initialized TerminalCompleter with {len(self.all_commands)} commands")
        
    def get_suggestions(self, text):
        """Get all matching suggestions for the given text"""
        # Split text into command and args
        parts = text.split()
        if not parts:
            logger.info("No text to get suggestions for")
            return []
            
        suggestions = []
        text = parts[0].lower()  # Only match first word, case insensitive
        logger.info(f"Getting suggestions for text: '{text}'")
        
        # Handle command with subcommands (like git)
        if len(parts) >= 2:
            main_command = parts[0].lower()
            subcommand = parts[1].lower()
            
            # Check if this is a command with subcommands
            for category, info in self.commands.items():
                if info.get('subcommands') and category == main_command:
                    # Get matching subcommands
                    matches = [cmd for cmd in info['subcommands'] if cmd.startswith(subcommand)]
                    if matches:
                        return [f"{main_command} {cmd}" for cmd in matches]
                    
                    # If no exact matches, try fuzzy matching with higher cutoff
                    fuzzy_matches = get_close_matches(subcommand, info['subcommands'], n=5, cutoff=0.6)
                    if fuzzy_matches:
                        return [f"{main_command} {cmd}" for cmd in fuzzy_matches]
        
        # Handle single command completion
        if len(parts) == 1:
            # First try exact category matches
            for category, info in self.commands.items():
                if category.startswith(text):
                    suggestions.append(category)
            
            # Then try command matches from all categories
            command_matches = []
            for category in self.commands.values():
                if 'commands' in category:
                    command_matches.extend([cmd for cmd in category['commands'] if cmd.startswith(text)])
            suggestions.extend(command_matches)
            
            # If we don't have enough matches, try fuzzy matching with higher cutoff
            if len(suggestions) < 5:
                all_commands = list(self.all_commands)
                fuzzy_matches = get_close_matches(text, all_commands, n=5-len(suggestions), cutoff=0.6)
                suggestions.extend([m for m in fuzzy_matches if m not in suggestions])
        
        logger.info(f"Final suggestions: {suggestions}")
        return suggestions[:5]  # Limit to top 5 suggestions
        
    def complete(self, text, state):
        """Return the state'th completion for text"""
        if state == 0:
            self.matches = self.get_suggestions(text)
        try:
            return self.matches[state]
        except IndexError:
            return None
