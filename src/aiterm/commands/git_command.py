"""Git command handler for AITerm."""

from .ai_processor import AICommandProcessor
from .models import GitCommandProcessor
import os
import subprocess
import re
from typing import List, Optional, Union

class GitCommand:
    """Handles Git command execution."""
    
    def __init__(self):
        self.ai_processor = AICommandProcessor()
        self.git_commands = {'show', 'log', 'status', 'commit', 'push', 'pull'}  # Add more as needed
    
    def _is_native_git_command(self, command: str) -> bool:
        """Check if the first word is a native git command."""
        parts = command.strip().split()
        return parts[0] in self.git_commands if parts else False

    def _normalize_command(self, command: str) -> str:
        """Normalize command by removing 'git' prefix and extra spaces."""
        parts = command.strip().split()
        if parts and parts[0] == 'git':
            parts = parts[1:]
        return " ".join(parts)

    def _preprocess_command(self, command: str) -> List[str]:
        """Preprocess command using AI interpretation."""
        # Let AI processor handle all command variations
        return self.ai_processor.process_command(command)

    def _rewrite_command(self, command: str) -> List[str]:
        """Rewrite command using AI processor."""
        return self.ai_processor.process_command(command)

    def find_git_repo(self, path: str = os.getcwd()) -> Optional[str]:
        """Find the Git repository from current path up to root."""
        current = os.path.abspath(path)
        while current != '/':
            if os.path.exists(os.path.join(current, '.git')):
                return current
            current = os.path.dirname(current)
        return None

    def _handle_show_last_commits(self, command: str) -> List[str]:
        """Convert 'show last N commits' or equivalent to proper git log command."""
        patterns = [
            r"^show\s+last\s+(\d+)\s+commits$",  # matches "show last N commits"
            r"^log\s+-n\s+(\d+)$"                # matches "log -n N"
        ]
        
        command = command.strip()
        for pattern in patterns:
            match = re.match(pattern, command)
            if match:
                num_commits = match.group(1)
                return ["log", "--oneline", f"-{num_commits}"]
        
        # If no pattern matches, split and return as is
        return command.split()

    def _interpret_error(self, error_msg: str) -> str:
        """Interpret Git error messages into user-friendly format."""
        error_patterns = {
            r"ambiguous argument '(.+?)'": 
                "I see you're trying to use '{}' as an argument. For viewing recent commits, try:\n" +
                "- 'git log -n 5' for last 5 commits\n" +
                "- 'git show last 5 commits' (our custom syntax)\n" +
                "- 'git log --oneline' for compact history",
            r"not a git repository": 
                "This directory is not a Git repository. Try running 'git init' first.",
            r"fatal: Path '(.+?)' does not exist": 
                "The file or directory '{}' was not found.",
            r"did you mean ([^?]+)\?": 
                "Git suggests using: {}"
        }
        
        # Special handling for the "show last N commits" syntax error
        if "ambiguous argument 'last'" in error_msg:
            return ("AI Interpretation: It looks like you're trying to view recent commits. " +
                   "Our custom 'show last N commits' command might not be processing correctly. " +
                   "Try these alternatives:\n" +
                   "1. git log -n 5\n" +
                   "2. git log --oneline -5")

        for pattern, template in error_patterns.items():
            match = re.search(pattern, error_msg)
            if match:
                return "AI Interpretation: " + template.format(*match.groups())
        return f"Error: {error_msg}"

    def execute(self, command: Union[str, List[str]]) -> str:
        """Execute a git command with given arguments."""
        repo_path = self.find_git_repo()
        if not repo_path:
            return self._interpret_error("not a git repository")
        
        # Process command through AI interpretation
        args = self._preprocess_command(command if isinstance(command, str) 
                                      else " ".join(command))
        
        try:
            command = ['git'] + args
            result = subprocess.run(command,
                                 cwd=repo_path,
                                 capture_output=True,
                                 text=True,
                                 check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return self._interpret_error(e.stderr)
