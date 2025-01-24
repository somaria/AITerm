"""AI-powered command processor for interpreting natural language commands."""

import os
import re
from typing import Optional

class AICommandProcessor:
    """Process natural language commands into shell commands using AI."""
    
    def __init__(self):
        """Initialize the AI command processor."""
        self.working_directory = os.path.expanduser('~')
    
    def process_command(self, command: str, command_type: str = 'shell') -> Optional[str]:
        """Process a natural language command into a shell command.
        
        Args:
            command: Natural language command to process
            command_type: Type of command to process ('shell', 'list', etc.)
            
        Returns:
            Processed shell command or None if command cannot be processed
        """
        command = command.lower().strip()
        
        # Process list commands
        if command_type == 'list' or \
           any(word in command for word in ["show", "list", "display", "view"]) and \
           any(word in command for word in ["files", "directory", "folder", "contents"]):
            return self._process_list_command(command)
            
        # Process find commands
        if command.startswith("find"):
            return self._process_find_command(command)
            
        # For basic shell commands, return as is
        return command
        
    def _process_find_command(self, command: str) -> str:
        """Process natural language find commands into shell find commands.
        
        Args:
            command: Natural language find command
            
        Returns:
            Shell find command
        """
        parts = command.split()
        find_cmd = ["find", "."]
        
        # Handle type specifications
        if "directory" in command or "directories" in command or "folders" in command:
            find_cmd.extend(["-type", "d"])
        elif "file" in command or "files" in command:
            find_cmd.extend(["-type", "f"])
            
        # Handle size constraints
        size_match = re.search(r"larger than (\d+)(mb|kb|m|k|b)", command)
        if size_match:
            size, unit = size_match.groups()
            unit_map = {"mb": "M", "m": "M", "kb": "k", "k": "k", "b": "c"}
            find_cmd.extend(["-size", f"+{size}{unit_map.get(unit.lower(), 'c')}"])
            
        # Handle time constraints
        if "modified" in command:
            if "today" in command:
                find_cmd.extend(["-mtime", "-1"])
            elif "last 24 hours" in command:
                find_cmd.extend(["-mtime", "-1"])
            elif "last week" in command:
                find_cmd.extend(["-mtime", "-7"])
                
        # Handle name patterns
        if "python" in command:
            find_cmd.extend(['-name', '"*.py"'])
        elif "javascript" in command or "js" in command:
            find_cmd.extend(['-name', '"*.js"'])
        elif "text" in command or "txt" in command:
            find_cmd.extend(['-name', '"*.txt"'])
            
        # Handle multiple extensions
        if "source code" in command:
            find_cmd.extend(['-type', 'f', '\\('])
            find_cmd.extend(['-name', '"*.py"', '-o', '-name', '"*.js"', '-o', '-name', '"*.cpp"', '-o', '-name', '"*.h"'])
            find_cmd.append('\\)')
            
        # Handle permissions
        if "executable" in command:
            find_cmd.append("-executable")
        elif "permission" in command and "777" in command:
            find_cmd.extend(["-perm", "777"])
            
        # Handle ownership
        if "owned by" in command and "current user" in command:
            find_cmd.extend(["-user", "$USER"])
            
        # Handle empty files/directories
        if "empty" in command:
            find_cmd.append("-empty")
            
        return " ".join(find_cmd)

    def _process_list_command(self, command: str) -> str:
        """Process natural language list commands into shell ls commands.
        
        Args:
            command: Natural language list command
            
        Returns:
            Shell ls command
        """
        # Start with basic ls command
        cmd = ["ls"]
        
        # Add common flags based on command
        if any(word in command for word in ["all", "hidden", "show all", "show hidden", "including hidden"]):
            cmd.append("-a")  # Show hidden files
            
        if any(word in command for word in ["long", "details", "detailed", "size", "permissions", "show details", "with details"]):
            cmd.append("-l")  # Long format
            
        if any(word in command for word in ["human", "readable", "human readable", "show sizes"]):
            cmd.append("-h")  # Human readable sizes
            
        if any(word in command for word in ["time", "date", "newest", "latest", "recent", "by time", "by date", "sort by time", "sort by date"]):
            cmd.append("-t")  # Sort by time
            
        if any(word in command for word in ["recursive", "subdirectories", "all directories", "include subdirectories", "show subdirectories"]):
            cmd.append("-R")  # Recursive
            
        if any(word in command for word in ["size", "largest", "biggest", "sort by size", "ordered by size"]):
            cmd.append("-S")  # Sort by size
            
        if "reverse" in command or "descending" in command:
            cmd.append("-r")  # Reverse order
            
        # Handle specific file types
        if any(word in command for word in ["directories", "folders", "dirs", "show directories", "show folders", "only directories", "only folders"]):
            cmd.extend(["-d", "*/"])  # List directories only
        elif any(word in command for word in ["only files", "just files", "files only"]):
            cmd.append("-p")  # List files only
            
        # Handle specific file extensions
        if any(word in command for word in ["python", "py files", "python files"]):
            cmd.append("*.py")  # Python files
        elif any(word in command for word in ["javascript", "js", "js files", "javascript files"]):
            cmd.append("*.js")
        elif any(word in command for word in ["text", "txt", "text files"]):
            cmd.append("*.txt")
        elif any(word in command for word in ["markdown", "md", "md files", "markdown files"]):
            cmd.append("*.md")
        elif any(word in command for word in ["html", "html files", "web files"]):
            cmd.append("*.html")
        elif any(word in command for word in ["css", "css files", "style files"]):
            cmd.append("*.css")
        elif any(word in command for word in ["json", "json files"]):
            cmd.append("*.json")
        elif any(word in command for word in ["yaml", "yml", "yaml files"]):
            cmd.append("*.{yaml,yml}")
        elif any(word in command for word in ["image", "images", "picture", "pictures", "photos"]):
            cmd.append("*.{jpg,jpeg,png,gif,bmp}")
        elif any(word in command for word in ["video", "videos", "movie", "movies"]):
            cmd.append("*.{mp4,avi,mov,wmv,flv,mkv}")
        elif any(word in command for word in ["audio", "music", "sound", "sounds"]):
            cmd.append("*.{mp3,wav,ogg,m4a,flac}")
        elif any(word in command for word in ["document", "documents", "docs"]):
            cmd.append("*.{doc,docx,pdf,odt,rtf}")
        elif any(word in command for word in ["spreadsheet", "spreadsheets", "excel"]):
            cmd.append("*.{xls,xlsx,ods,csv}")
        elif any(word in command for word in ["source", "source code", "code files"]):
            cmd.append("*.{py,js,java,cpp,c,h,hpp,cs,go,rs,rb,php}")
            
        # Join the command parts with spaces
        return " ".join(cmd)
