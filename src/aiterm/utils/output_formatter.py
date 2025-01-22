"""Output formatter for terminal output."""
import os
import re

class OutputFormatter:
    """Format terminal output with colors and styling."""
    
    def __init__(self):
        """Initialize the output formatter."""
        # ANSI color codes
        self.colors = {
            'black': '\033[30m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'reset': '\033[0m'
        }
        
        # File type colors for ls output
        self.file_colors = {
            'directory': 'blue',
            'executable': 'green',
            'symlink': 'cyan',
            'archive': 'red',
            'image': 'magenta',
            'text': 'white'
        }
    
    def format_output(self, output):
        """Format command output with colors and styling."""
        if not output:
            return ""
            
        # Convert bytes to string if needed
        if isinstance(output, bytes):
            output = output.decode('utf-8')
            
        # Handle ls command output specially
        if output.startswith('total ') or any(line.startswith('drwx') or line.startswith('-rwx') for line in output.split('\n')):
            return self.colorize_ls_output(output)
            
        return output.rstrip()
    
    def colorize_ls_output(self, output):
        """Colorize ls command output."""
        result = []
        for line in output.split('\n'):
            if not line:
                continue
                
            # Handle directory entries
            if line.startswith('d'):
                result.append((line, 'blue'))
            # Handle executable files
            elif 'x' in line[1:4]:
                result.append((line, 'green'))
            # Handle symlinks
            elif line.startswith('l'):
                result.append((line, 'cyan'))
            # Handle regular files
            else:
                # Check file extension
                filename = line.split()[-1]
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.zip', '.tar', '.gz', '.bz2', '.rar']:
                    result.append((line, 'red'))
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    result.append((line, 'magenta'))
                elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                    result.append((line, 'white'))
                else:
                    result.append((line, 'white'))
        
        return '\n'.join(f'{self.colors.get(color, "")}{text}{self.colors["reset"]}' for text, color in result)
