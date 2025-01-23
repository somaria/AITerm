"""Tests for the CommandExecutor class."""

import os
import pytest
from unittest.mock import patch, MagicMock
from aiterm.commands.executor import CommandExecutor

class TestCommandExecutor:
    """Test cases for CommandExecutor."""
    
    @pytest.fixture
    def executor(self):
        """Create a CommandExecutor instance for testing."""
        return CommandExecutor()
    
    @pytest.mark.parametrize("command,expected_output", [
        # Complex find commands
        ("find files larger than 10MB", 'find . -type f -size +10M'),
        ("find files modified in last 24 hours", 'find . -type f -mtime -1'),
        ("find executable python files", 'find . -type f -name "*.py" -executable'),
        ("find empty directories", 'find . -type d -empty'),
        ("find files with permission 777", 'find . -type f -perm 777'),
        ("find files owned by current user", 'find . -type f -user $USER'),
        ("find files not accessed in 30 days", 'find . -type f -atime +30'),
        ("find files modified between 1 and 7 days ago", 'find . -type f -mtime +1 -mtime -7'),
        
        # Combined search criteria
        ("find python files larger than 1MB", 'find . -type f -name "*.py" -size +1M'),
        ("find text files modified today", 'find . -type f -name "*.txt" -mtime -1'),
        ("find empty python files", 'find . -type f -name "*.py" -empty'),
        ("find executable scripts in bin", 'find ./bin -type f -executable'),
        ("find config files not modified in last week", 'find . -type f -name "*.config" -mtime +7'),
        
        # Path and name patterns
        ("find files in src directory", 'find ./src -type f'),
        ("find files starting with test", 'find . -type f -name "test*"'),
        ("find files ending with log", 'find . -type f -name "*.log"'),
        ("find files containing the word temp", 'find . -type f -name "*temp*"'),
        ("find files with extension py or js", 'find . -type f \\( -name "*.py" -o -name "*.js" \\)'),
        
        # Case sensitivity variations
        ("find files named README", 'find . -name "README*"'),
        ("search for readme files", 'find . -iname "readme*"'),
        ("find configuration files", 'find . -iname "*config*"'),
        ("look for makefiles", 'find . -iname "makefile*"'),
        
        # Directory specific searches
        ("find test directories", 'find . -type d -name "test*"'),
        ("find empty folders", 'find . -type d -empty'),
        ("find node_modules directories", 'find . -type d -name "node_modules"'),
        ("find git repositories", 'find . -type d -name ".git"'),
        
        # Error cases and edge cases
        ("find", 'find .'),  # Default case
        ("find files", 'find . -type f'),  # Basic file search
        ("find directories", 'find . -type d'),  # Basic directory search
        ("find all", 'find .'),  # Search everything
    ])
    def test_find_commands(self, executor, command, expected_output):
        """Test various find command variations."""
        # Mock the AI processor
        executor.ai_processor.process_command = MagicMock(return_value=expected_output)
        
        # Process the command
        processed = executor._process_command(command)
        
        # Verify the result
        assert processed == expected_output
        
    def test_find_with_multiple_file_types(self, executor):
        """Test finding multiple file types."""
        command = "find source code files"
        expected = 'find . -type f \\( -name "*.py" -o -name "*.js" -o -name "*.cpp" -o -name "*.h" \\)'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_size_and_time(self, executor):
        """Test finding files with both size and time criteria."""
        command = "find large files modified recently"
        expected = 'find . -type f -size +100M -mtime -7'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_permission_and_owner(self, executor):
        """Test finding files with specific permissions and owner."""
        command = "find my executable files"
        expected = 'find . -type f -user $USER -executable'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_complex_name_pattern(self, executor):
        """Test finding files with complex name patterns."""
        command = "find backup files from 2023"
        expected = 'find . -type f -name "*backup*2023*"'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_depth_limit(self, executor):
        """Test finding files with depth limitation."""
        command = "find files in current directory only"
        expected = 'find . -maxdepth 1 -type f'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_error_handling(self, executor):
        """Test error handling for invalid find commands."""
        # Test with invalid flag
        command = "find with invalid flag"
        executor.ai_processor.process_command = MagicMock(return_value='find -invalid-flag')
        stdout, stderr = executor.execute(command)
        assert stdout is None
        assert stderr is not None
        
        # Test with invalid directory
        command = "find in nonexistent directory"
        executor.ai_processor.process_command = MagicMock(return_value='find /nonexistent/path -type f')
        stdout, stderr = executor.execute(command)
        assert stdout is None
        assert stderr is not None
        
    def test_find_with_special_characters(self, executor):
        """Test finding files with special characters in names."""
        command = "find files with spaces"
        expected = 'find . -type f -name "* *"'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
        command = "find files with parentheses"
        expected = 'find . -type f -name "*\\(*\\)*"'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
