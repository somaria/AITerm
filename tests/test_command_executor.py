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
    
    # Basic Command Execution Tests
    def test_basic_command_execution(self, executor):
        """Test basic command execution without AI processing."""
        # Test simple echo command
        command = "echo 'hello world'"
        stdout, stderr = executor.execute(command)
        assert stdout.strip() == "hello world"
        assert stderr is None
        
        # Test command with arguments
        command = "ls -l"
        stdout, stderr = executor.execute(command)
        assert stdout != ""
        assert stderr is None
        
    def test_command_not_found(self, executor):
        """Test handling of non-existent commands."""
        command = "nonexistentcommand"
        stdout, stderr = executor.execute(command)
        assert stdout is None
        assert "Command not found: nonexistentcommand" in stderr
        
    def test_command_with_invalid_args(self, executor):
        """Test handling of commands with invalid arguments."""
        command = "ls --invalid-flag"
        stdout, stderr = executor.execute(command)
        assert stdout is None
        assert stderr != ""
        
    def test_working_directory_management(self, executor):
        """Test working directory changes."""
        # Test changing to home directory
        success, error = executor.change_directory()
        assert success
        assert error is None
        assert executor.working_directory == os.path.expanduser('~')
        
        # Test changing to invalid directory
        success, error = executor.change_directory("/nonexistent/path")
        assert not success
        assert "Directory does not exist" in error
        
        # Test changing to a file instead of directory
        test_file = os.path.join(executor.working_directory, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")
        success, error = executor.change_directory(test_file)
        assert not success
        assert "Not a directory" in error
        os.remove(test_file)
        
    def test_command_with_pipes(self, executor):
        """Test handling of commands with pipes."""
        command = "echo 'hello world' | grep 'hello'"
        stdout, stderr = executor.execute(command)
        assert "hello world" in stdout
        assert stderr is None
        
    def test_find_commands(self, executor):
        """Test various find command variations."""
        # Mock the AI processor
        executor.ai_processor.process_command = MagicMock(return_value='find .')
        
        # Process the command
        processed = executor._process_command("find")
        
        # Verify the result
        assert processed == 'find .'
        
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
        assert stderr != ""
        
        # Test with invalid directory
        command = "find in nonexistent directory"
        executor.ai_processor.process_command = MagicMock(return_value='find /nonexistent/path -type f')
        stdout, stderr = executor.execute(command)
        assert stdout is None
        assert stderr != ""
        
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
        
    def test_find_with_multiple_file_types_and_sizes(self, executor):
        """Test finding files with multiple types and size constraints."""
        command = "find source code files larger than 1KB"
        expected = 'find . -type f \\( -name "*.py" -o -name "*.js" -o -name "*.cpp" -o -name "*.h" \\) -size +1k'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_date_ranges(self, executor):
        """Test finding files within specific date ranges."""
        command = "find files modified between last Monday and yesterday"
        expected = 'find . -type f -newermt "last Monday" ! -newermt "yesterday"'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
        
    def test_find_with_content_search(self, executor):
        """Test finding files containing specific content."""
        command = "find python files containing 'TODO'"
        expected = 'find . -type f -name "*.py" -exec grep -l "TODO" {} \\;'
        
        executor.ai_processor.process_command = MagicMock(return_value=expected)
        processed = executor._process_command(command)
        assert processed == expected
