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
        self.commands = set([
            # File operations
            'ls', 'cd', 'pwd', 'mkdir', 'rm', 'cp', 'mv', 'touch',
            # File viewing/editing
            'cat', 'less', 'more', 'vim', 'nano', 'head', 'tail',
            # Text processing
            'grep', 'sed', 'awk', 'sort', 'uniq', 'wc',
            # Search
            'find', 'locate', 'which',
            # Process
            'ps', 'kill', 'top',
            # System
            'df', 'du', 'free',
            # Network
            'ping', 'curl', 'wget', 'ssh',
            # Archive
            'tar', 'gzip', 'zip', 'unzip',
            # Package management
            'pip', 'brew',
            # Version control
            'git', 'svn',
            # Others
            'echo', 'clear', 'python', 'node'
        ])
        
        self.git_patterns = {
            'show last': ['commits', 'changes'],
            'git show last': ['commits', 'changes'],
            'git log': ['-n', '--oneline', '--graph'],
            'git show': ['last', 'HEAD', 'master']
        }
        
        logger.info(f"Initialized TerminalCompleter with {len(self.commands)} commands")
        
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
        
        # Handle git command patterns
        if len(parts) >= 2:
            pattern = ' '.join(parts[:2])
            if pattern in self.git_patterns:
                return [f"{text} {suffix}" for suffix in self.git_patterns[pattern]]
        
        # If we have multiple parts, complete the last part as a path
        if len(parts) > 1:
            last_part = parts[-1]
            if last_part.startswith('~'):
                last_part = os.path.expanduser(last_part)
            
            # Get directory and base for path completion
            path_dir = os.path.dirname(last_part)
            path_base = os.path.basename(last_part)
            if path_dir == '':
                path_dir = '.'
            elif path_dir.startswith('~'):
                path_dir = os.path.expanduser(path_dir)
            
            try:
                logger.info(f"Trying path completion for: {path_dir}/{path_base}*")
                matches = glob.glob(os.path.join(path_dir, path_base + '*'))
                # Add trailing slash to directories
                matches = [f"{m}{'/' if os.path.isdir(m) else ''}" for m in matches]
                # Reconstruct full command with completion
                if matches:
                    suggestions = [' '.join(parts[:-1] + [m]) for m in matches]
                    logger.info(f"Path suggestions: {suggestions}")
            except Exception as e:
                logger.error(f"Error in path completion: {e}")
                
        # Single word - try path completion first, then command completion
        else:
            # Try path completion if it looks like a path
            if text.startswith('~') or '/' in text:
                try:
                    path_dir = os.path.dirname(text)
                    path_base = os.path.basename(text)
                    if path_dir == '':
                        path_dir = '.'
                    elif path_dir.startswith('~'):
                        path_dir = os.path.expanduser(path_dir)
                        
                    logger.info(f"Trying path completion for: {path_dir}/{path_base}*")
                    matches = glob.glob(os.path.join(path_dir, path_base + '*'))
                    suggestions.extend([f"{m}{'/' if os.path.isdir(m) else ''}" for m in matches])
                    logger.info(f"Path suggestions: {suggestions}")
                except Exception as e:
                    logger.error(f"Error in path completion: {e}")
            
            # Try command completion with fuzzy matching
            if not suggestions:
                # Convert commands set to sorted list for consistent matching
                command_list = sorted(self.commands)
                
                # First try prefix matches
                prefix_matches = [cmd for cmd in command_list if cmd.startswith(text)]
                logger.info(f"Prefix matches for '{text}': {prefix_matches}")
                suggestions.extend(prefix_matches)
                
                # Then try fuzzy matches if we don't have enough prefix matches
                if len(prefix_matches) < 5:
                    # Use list for fuzzy matching
                    fuzzy_matches = get_close_matches(text, command_list, n=5-len(prefix_matches), cutoff=0.3)
                    logger.info(f"Fuzzy matches for '{text}': {fuzzy_matches}")
                    # Only add fuzzy matches that aren't already in prefix matches
                    new_matches = [m for m in fuzzy_matches if m not in prefix_matches]
                    logger.info(f"New fuzzy matches: {new_matches}")
                    suggestions.extend(new_matches)
            
        logger.info(f"Final suggestions: {suggestions}")
        return suggestions
        
    def complete(self, text, state):
        """Return the state'th completion for text"""
        if state == 0:
            self.matches = self.get_suggestions(text)
        try:
            return self.matches[state]
        except IndexError:
            return None
