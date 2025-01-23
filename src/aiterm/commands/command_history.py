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
        self._history: List[Dict] = self._load_history()
        
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
                json.dump(self._history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_command(self, command: str, working_dir: str, exit_code: int = 0, output: str = "", interpreted_as: str = None):
        """Add a command to history.
        
        Args:
            command: The command that was executed
            working_dir: Working directory when command was executed
            exit_code: Exit code from command execution
            output: Command output (truncated)
            interpreted_as: If command was interpreted from natural language, the actual command executed
        """
        entry = {
            "command": command,
            "working_dir": working_dir,
            "timestamp": datetime.now().isoformat(),
            "exit_code": exit_code,
            "output": output[:1000] if output else "",  # Limit output size
            "interpreted_as": interpreted_as  # Store interpreted command if present
        }
        self._history.append(entry)
        self._save_history()
    
    def get_recent_commands(self, count: int = 10) -> List[str]:
        """Get most recent commands.
        
        Args:
            count: Number of commands to return
            
        Returns:
            List of recent command entries
        """
        return [entry["command"] for entry in self._history[-count:]]

    def get_commands_in_directory(self, directory: str) -> List[str]:
        """Get commands executed in a specific directory.
        
        Args:
            directory: Directory path to filter by
            
        Returns:
            List of command entries executed in the directory
        """
        return [
            entry["command"] for entry in self._history 
            if entry["working_dir"] == directory
        ]
    
    def get_similar_commands(self, command: str) -> List[str]:
        """Get commands similar to the given command."""
        similar = []
        for cmd in self._history:
            if command.lower() in cmd['command'].lower():
                similar.append(cmd['command'])
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
        current_dir = self._history[-1]["working_dir"] if self._history else None
        
        # Analyze command patterns
        working_dirs = [entry["working_dir"] for entry in self._history[-last_n:]]
        
        return {
            "current_directory": current_dir,
            "recent_commands": recent,
            "recent_directories": working_dirs,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_all_commands(self) -> List[str]:
        """Get all commands in history."""
        return [cmd['command'] for cmd in self._history]

    def get_command_strings(self) -> List[str]:
        """Get list of command strings from history.
        
        Returns:
            List of command strings, most recent first.
        """
        return [entry['command'] for entry in reversed(self._history)]
        
    @property 
    def history(self) -> List[Dict]:
        """Get the command history.
        
        Returns:
            List of command history entries.
        """
        return self._load_history()
