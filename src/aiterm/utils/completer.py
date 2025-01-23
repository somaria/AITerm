"""
Tab completion functionality for the terminal
"""

import os
import glob
import readline

class TerminalCompleter:
    def __init__(self):
        self.matches = []
        
    def complete(self, text, state):
        """Return the state'th completion for text"""
        if state == 0:  # First time for this text, build a match list
            # Split text into command and args
            parts = text.split()
            if not parts:
                return None
                
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
                    self.matches = glob.glob(os.path.join(path_dir, path_base + '*'))
                    # Add trailing slash to directories
                    self.matches = [f"{m}{'/' if os.path.isdir(m) else ''}" for m in self.matches]
                    # Reconstruct full command with completion
                    if self.matches:
                        self.matches = [' '.join(parts[:-1] + [m]) for m in self.matches]
                except Exception:
                    self.matches = []
                    
            # Single word - try path completion first, then command completion
            else:
                if text.startswith('~') or '/' in text:
                    path_dir = os.path.dirname(text)
                    path_base = os.path.basename(text)
                    if path_dir == '':
                        path_dir = '.'
                    elif path_dir.startswith('~'):
                        path_dir = os.path.expanduser(path_dir)
                    
                    try:
                        self.matches = glob.glob(os.path.join(path_dir, path_base + '*'))
                        # Add trailing slash to directories
                        self.matches = [f"{m}{'/' if os.path.isdir(m) else ''}" for m in self.matches]
                    except Exception:
                        self.matches = []
                else:
                    try:
                        # Get all executable files in PATH
                        paths = os.environ.get('PATH', '').split(os.pathsep)
                        self.matches = []
                        for path in paths:
                            if os.path.isdir(path):
                                for cmd in os.listdir(path):
                                    if cmd.startswith(text):
                                        cmd_path = os.path.join(path, cmd)
                                        if os.access(cmd_path, os.X_OK):
                                            self.matches.append(cmd)
                        self.matches = sorted(set(self.matches))
                    except Exception:
                        self.matches = []
        
        try:
            return self.matches[state]
        except IndexError:
            return None

    def get_completion_type(self, text):
        """Determine the type of completion needed"""
        if text.startswith('~') or '/' in text:
            return 'path'
        return 'command'
