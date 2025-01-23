"""Pydantic models for AI command processing."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class GitShowCommand(BaseModel):
    """Model for 'show' type commands."""
    command_type: Literal["show"] = "show"
    count: Optional[int] = Field(None, description="Number of items to show")
    type: str = Field(..., description="What to show (commits, changes, history)")
    
    def to_git_command(self) -> List[str]:
        """Convert to git command arguments."""
        if self.type == "commits":
            return ["log", "--oneline", f"-{self.count}"]
        elif self.type == "changes":
            return ["status"]
        elif self.type == "history":
            return ["log", "--oneline"]
        return []

class GitCommandProcessor:
    """Process natural language into git commands using AI models."""
    
    @staticmethod
    def process(command: str) -> List[str]:
        """Process natural language command into git arguments."""
        command = command.strip().lower()
        
        # Try to parse as show command
        try:
            if "show" in command:
                parts = command.split()
                if "last" in command and "commits" in command:
                    count = int(parts[parts.index("last") + 1])
                    return GitShowCommand(count=count, type="commits").to_git_command()
                elif "changes" in command:
                    return GitShowCommand(type="changes").to_git_command()
                elif "history" in command:
                    return GitShowCommand(type="history").to_git_command()
        except (ValueError, IndexError):
            pass
        
        # Fall back to original command
        return command.split()
