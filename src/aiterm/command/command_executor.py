"""Command executor for terminal commands."""
import os
import subprocess
import shlex
import pty

class CommandExecutor:
    """Execute terminal commands and manage working directory."""
    
    # Commands that typically need paging
    PAGED_COMMANDS = {'git show', 'git log', 'less', 'more', 'man'}
    
    def __init__(self):
        """Initialize command executor with current directory."""
        self.working_directory = os.path.expanduser('~')
    
    def execute(self, command):
        """Execute a shell command and return stdout and stderr."""
        try:
            # Split command into arguments while respecting quotes
            args = shlex.split(command)
            
            # Check if command needs paging
            needs_paging = any(cmd in ' '.join(args[:2]) for cmd in self.PAGED_COMMANDS)
            
            if needs_paging:
                # For paged commands, use PTY to handle pagination
                master_fd, slave_fd = pty.openpty()
                process = subprocess.Popen(
                    args,
                    cwd=self.working_directory,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    text=True
                )
                stdout = os.read(master_fd, 1024*1024).decode('utf-8')
                os.close(slave_fd)
                os.close(master_fd)
                return stdout, ""
            else:
                # For regular commands, use normal execution
                process = subprocess.Popen(
                    args,
                    cwd=self.working_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate()
                return stdout, stderr
            
        except FileNotFoundError:
            return "", f"Command not found: {command}"
        except Exception as e:
            return "", str(e)
    
    def change_directory(self, path=None):
        """Change current working directory."""
        if path is None:
            path = os.path.expanduser('~')
        
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.working_directory, path)
            
            # Resolve path and check if exists
            path = os.path.realpath(path)
            if not os.path.exists(path):
                return False, "Directory does not exist"
            if not os.path.isdir(path):
                return False, "Not a directory"
            
            self.working_directory = path
            return True, None
            
        except Exception as e:
            return False, str(e)
