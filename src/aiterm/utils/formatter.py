"""
Output formatting utilities
"""

from typing import List, Tuple

class OutputFormatter:
    @staticmethod
    def colorize_ls_output(output: str) -> List[Tuple[str, str]]:
        """
        Colorize ls command output based on file types
        Returns a list of (line, color) tuples
        """
        lines = output.split('\n')
        result = []
        for line in lines:
            if not line.strip():
                continue
            
            # Check for different file types and add appropriate colors
            if line.endswith('/'):  # Directory
                result.append((line, 'deep sky blue'))
            elif line.endswith('*'):  # Executable
                result.append((line, 'light green'))
            elif line.endswith('@'):  # Symlink
                result.append((line, 'magenta'))
            elif line.endswith('|'):  # FIFO/pipe
                result.append((line, 'yellow'))
            elif line.endswith('='):  # Socket
                result.append((line, 'red'))
            elif '.' in line:  # Files with extensions
                ext = line.split('.')[-1].lower()
                if ext in ['py', 'js', 'cpp', 'c', 'java', 'sh']:
                    result.append((line, 'orange'))  # Source code files
                elif ext in ['txt', 'md', 'log', 'json', 'yml', 'yaml', 'env']:
                    result.append((line, 'light gray'))  # Text files
                else:
                    result.append((line, 'white'))  # Other files
            else:
                result.append((line, 'white'))  # Regular files
        
        return result
