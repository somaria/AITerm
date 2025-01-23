"""Pydantic models for AI command processing."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GitCommandInput(BaseModel):
    """AI-powered command interpretation model."""
    raw_command: str = Field(..., description="The original command entered by user")
    is_git_command: bool = Field(True, description="Whether this is a git command")
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        frozen = False

    def get_git_args(self) -> List[str]:
        """Convert natural language to git arguments using AI."""
        # Log the original command
        logger.info(f"Interpreting command: {self.raw_command}")
        
        # Handle common patterns first
        if "show last" in self.raw_command:
            parts = self.raw_command.split()
            try:
                count_index = parts.index("last") + 1
                count = parts[count_index]
                logger.info(f"Interpreted as: git log --oneline -{count}")
                return ["log", "--oneline", f"-{count}"]
            except (ValueError, IndexError):
                pass
        
        # Default to splitting the command
        return self.raw_command.split()

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
        input_model = GitCommandInput(raw_command=command)
        return input_model.get_git_args()
