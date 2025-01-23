"""Command history management and analysis."""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class CommandHistory:
    """Manages command history and provides analysis for suggestions."""
    
    def __init__(self, history_file: str = None):
        """Initialize command history manager.
        
        Args:
            history_file: Path to history file. If None, uses default location.
        """
        if history_file is None:
            # Use default location in user's home directory
            history_file = os.path.expanduser("~/.aiterm/command_history.json")
        
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing history or create empty one
        self.history: List[Dict] = self._load_history()
        
    def _load_history(self) -> List[Dict]:
        """Load command history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
        return []
    
    def _save_history(self):
        """Save command history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_command(self, command: str, working_dir: str, exit_code: int = 0, output: str = ""):
        """Add a command to history.
        
        Args:
            command: The command that was executed
            working_dir: Working directory when command was executed
            exit_code: Command exit code (0 for success)
            output: Command output (truncated if too long)
        """
        entry = {
            "command": command,
            "working_dir": working_dir,
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "output": output[:1000] if output else ""  # Limit output size
        }
        self.history.append(entry)
        self._save_history()
    
    def get_recent_commands(self, count: int = 10) -> List[Dict]:
        """Get most recent commands.
        
        Args:
            count: Number of commands to return
            
        Returns:
            List of recent command entries
        """
        return self.history[-count:]
    
    def get_commands_in_directory(self, directory: str) -> List[Dict]:
        """Get commands executed in a specific directory.
        
        Args:
            directory: Directory path to filter by
            
        Returns:
            List of command entries executed in the directory
        """
        return [
            entry for entry in self.history 
            if entry["working_dir"] == directory
        ]
    
    def get_similar_commands(self, current_cmd: str, threshold: float = 0.6) -> List[str]:
        """Find similar commands from history.
        
        Args:
            current_cmd: Current command to find similar ones for
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar commands
        """
        # Simple similarity based on common words
        current_words = set(current_cmd.lower().split())
        similar = []
        
        for entry in self.history:
            cmd = entry["command"]
            cmd_words = set(cmd.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(current_words & cmd_words)
            union = len(current_words | cmd_words)
            
            if union > 0:
                similarity = intersection / union
                if similarity >= threshold and cmd != current_cmd:
                    similar.append(cmd)
        
        return similar
    
    def get_similar_commands(self, command: str) -> List[str]:
        """Get commands similar to the given command."""
        similar = []
        cmd_parts = command.lower().split()
        
        for entry in self.history:
            stored_cmd = entry["command"].lower()
            stored_parts = stored_cmd.split()
            
            # Check if command is a prefix or shares common words
            if stored_cmd.startswith(command.lower()) or any(part in stored_parts for part in cmd_parts):
                similar.append(entry["command"])
        
        return similar
    
    def get_command_context(self, last_n: int = 5) -> Dict:
        """Get context from recent commands.
        
        Args:
            last_n: Number of recent commands to include
            
        Returns:
            Dict containing contextual information
        """
        recent = self.get_recent_commands(last_n)
        if not recent:
            return {}
            
        # Get current working directory from most recent command
        current_dir = recent[-1]["working_dir"] if recent else None
        
        # Analyze command patterns
        commands = [entry["command"] for entry in recent]
        working_dirs = [entry["working_dir"] for entry in recent]
        
        return {
            "current_directory": current_dir,
            "recent_commands": commands,
            "recent_directories": working_dirs,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_all_commands(self) -> List[str]:
        """Get all commands from history across all directories."""
        all_commands = set()
        for entry in self.history:
            all_commands.add(entry["command"])
        return list(all_commands)
