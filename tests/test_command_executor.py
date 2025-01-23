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
        # pwd variations
        ("show current directory", "pwd"),
        ("display working folder", "pwd"),
        ("print current path", "pwd"),
        ("where am i", "pwd"),
        ("what directory", "pwd"),
        ("show folder", "pwd"),
        ("which directory", "pwd"),
        ("what is my current directory", "pwd"),
        ("show me where i am", "pwd"),
        ("print working directory", "pwd"),
        ("display current location", "pwd"),
        ("what's my current directory", "pwd"),
        ("tell me where i am", "pwd"),
        ("show current path", "pwd"),
    
        # ls variations
        ("show files", "ls -F"),
        ("list directory", "ls -F"),
        ("display files", "ls -F"),
        ("show python files", "ls -F *.py"),
        ("list javascript files", "ls -F *.js"),
        ("show text files", "ls -F *.txt"),
        ("show hidden files", "ls -a"),
        ("list all files with details", "ls -la"),
        ("show files with details", "ls -l"),
        ("display all files", "ls -F"),
        ("list everything", "ls -F"),
        ("show all python files", "ls -F *.py"),
        ("list all javascript files", "ls -F *.js"),
        ("show all text files", "ls -F *.txt"),
        ("display hidden files", "ls -a"),
        ("list files with permissions", "ls -l"),
    
        # cd variations
        ("cd to src", "cd src"),
        ("cd into documents", "cd documents"),
        ("cd src/aiterm folder", "cd src/aiterm"),
        ("cd to the home directory", "cd"),
        ("cd into the src directory", "cd src"),
        ("cd /absolute/path folder", "cd /absolute/path"),
        ("change to documents", "cd documents"),
        ("switch to home directory", "cd"),
        ("go to src folder", "cd src"),
        ("move to parent directory", "cd .."),
        ("change directory to downloads", "cd downloads"),
        ("cd back", "cd .."),
        ("cd up", "cd .."),
        ("cd home", "cd"),
        ("go back", "cd .."),
        ("return to previous directory", "cd .."),
        ("change to parent", "cd .."),
        ("go to home", "cd"),
        ("switch to downloads", "cd downloads"),
        ("go to home", "cd"),
        ("change to previous directory", "cd -"),
        ("go back", "cd -"),
        ("return to last directory", "cd -"),
        ("switch to previous folder", "cd -"),
        ("go to documents", "cd ~/Documents"),
        ("change to downloads", "cd ~/Downloads"),
        ("go to desktop", "cd ~/Desktop"),

        # find variations
        ("find a file name abcdefg", 'find . -name "abcdefg"'),
        ("search for test.py", 'find . -name "test.py"'),
        ("find all python files", 'find . -type f -name "*.py"'),
        ("search for js files", 'find . -type f -name "*.js"'),
        ("find file readme", 'find . -type f -iname "readme*"'),
        ("look for config files", 'find . -type f -name "*.config"'),
        ("find directory named tests", 'find . -type d -name "tests"'),
        ("search for text files", 'find . -type f -name "*.txt"'),
        ("find files modified today", 'find . -type f -mtime -1'),
        ("search for large files", 'find . -type f -size +10M'),
        ("find empty files", 'find . -type f -empty'),
        ("search for executable files", 'find . -type f -executable'),
        ("find files by name pattern", 'find . -name "pattern"'),
        ("search files case insensitive", 'find . -iname "pattern"'),
        ("find all directories", 'find . -type d'),
        ("search hidden files", 'find . -type f -name ".*"'),
    ])
    def test_natural_language_commands(self, executor, command, expected_output):
        """Test various natural language command variations."""
        with patch.object(executor.ai_processor, 'process_command') as mock_process:
            # Mock AI response
            mock_process.return_value = expected_output
            
            # Process command
            result = executor._process_command(command)
            assert result == expected_output, f"Failed on '{command}'"
            
            # Verify AI was called correctly
            mock_process.assert_called_once_with(command, command_type='shell')
    
    @pytest.mark.parametrize("command,expected_stdout,expected_stderr", [
        # Basic commands
        ("pwd", "/current/dir", None),
        ("ls -F", "file1\nfile2\n", None),
        ("ls -l", "total 2\n-rw-r--r-- file1\n", None),
        ("cd /path", "/path", None),
        ("cd invalid", None, "Directory not found: invalid"),
        
        # Natural language commands
        ("show current directory", "/current/dir", None),
        ("where am i", "/current/dir", None),
        ("list files", "file1\nfile2\n", None),
        ("show python files", "test.py\nmain.py\n", None),
        ("cd to home", "/Users/daryl", None),
        ("change to invalid folder", None, "Directory not found: invalid folder"),
        ("display all files", "file1\nfile2\n", None),
        ("show hidden files", ".git\n.env\n", None),
        ("go to src folder", "src", None),
        ("move to parent directory", "..", None),
    ])
    def test_execute_command(self, executor, command, expected_stdout, expected_stderr):
        """Test command execution with mocked subprocess."""
        with patch('subprocess.run') as mock_run, \
             patch.object(executor.ai_processor, 'process_command') as mock_process:
            
            # Mock AI processor
            if command.startswith(('cd', 'ls', 'pwd')):
                if 'home' in command:
                    mock_process.return_value = 'cd'
                else:
                    mock_process.return_value = command
            else:
                # Convert natural language to command
                if 'directory' in command or 'where' in command:
                    mock_process.return_value = 'pwd'
                elif 'files' in command:
                    if 'python' in command:
                        mock_process.return_value = 'ls -F *.py'
                    elif 'hidden' in command:
                        mock_process.return_value = 'ls -a'
                    else:
                        mock_process.return_value = 'ls -F'
                elif command.startswith(('go', 'move', 'change', 'cd')):
                    if 'home' in command:
                        mock_process.return_value = 'cd'
                    elif 'parent' in command:
                        mock_process.return_value = 'cd ..'
                    elif 'src' in command:
                        mock_process.return_value = 'cd src'
                    elif 'invalid' in command:
                        mock_process.return_value = 'cd invalid folder'
                    else:
                        path = command.split()[-1]
                        mock_process.return_value = f'cd {path}'
            
            # Mock subprocess response
            mock_result = MagicMock()
            mock_result.stdout = expected_stdout
            mock_result.stderr = expected_stderr
            mock_run.return_value = mock_result
            
            # For cd commands, also mock os.chdir and os.path
            if 'cd' in mock_process.return_value:
                with patch('os.chdir') as mock_chdir, \
                     patch('os.path.exists') as mock_exists, \
                     patch('os.path.isdir') as mock_isdir, \
                     patch('os.path.expanduser') as mock_expanduser:
                    
                    # Mock path checks
                    mock_exists.return_value = expected_stderr is None
                    mock_isdir.return_value = expected_stderr is None
                    
                    # Set up expanduser mock
                    if command == 'cd to home' or 'home' in command:
                        mock_expanduser.return_value = '/Users/daryl'
                    else:
                        mock_expanduser.side_effect = lambda x: x if x != '~' else '/Users/daryl'
                    
                    # Execute command
                    stdout, stderr = executor.execute(command)
                    
                    # Verify results
                    if expected_stderr is None:
                        if mock_process.return_value == 'cd':
                            # For 'cd' without arguments (home directory)
                            assert stdout == '/Users/daryl'
                            mock_chdir.assert_called_once_with('/Users/daryl')
                        else:
                            # For 'cd' with arguments
                            path = mock_process.return_value.split(None, 1)[1]
                            if 'invalid' in path:
                                assert stderr == "Directory not found: invalid folder"
                            else:
                                assert stdout == expected_stdout
                                if os.path.isabs(path):
                                    mock_chdir.assert_called_once_with(path)
                                else:
                                    mock_chdir.assert_called_once_with(os.path.join('/Volumes/wd/code/Python/AITerm', path))
                    else:
                        assert stdout == expected_stdout
                        assert stderr == expected_stderr
                        mock_chdir.assert_not_called()
            else:
                # Execute command for non-cd commands
                stdout, stderr = executor.execute(command)
                assert stdout == expected_stdout
                assert stderr == expected_stderr
    
    def test_change_directory(self, executor):
        """Test directory changing functionality."""
        with patch('os.chdir') as mock_chdir, \
             patch('os.path.exists') as mock_exists, \
             patch('os.path.isdir') as mock_isdir, \
             patch('os.path.expanduser') as mock_expanduser:
            
            # Mock path checks
            mock_exists.return_value = True
            mock_isdir.return_value = True
            home_path = '/Users/daryl'
            mock_expanduser.return_value = home_path
            
            # Test changing to home directory
            success, message = executor.change_directory()
            assert success
            mock_chdir.assert_called_once_with(home_path)
            
            # Reset mock
            mock_chdir.reset_mock()
            mock_expanduser.reset_mock()
            
            # Test changing to specific directory
            test_path = "/test/path"
            mock_exists.return_value = True
            mock_isdir.return_value = True
            mock_expanduser.side_effect = lambda x: x
            success, message = executor.change_directory(test_path)
            assert success
            mock_chdir.assert_called_once_with(test_path)
            
            # Test invalid directory
            mock_exists.return_value = False
            mock_isdir.return_value = False
            success, message = executor.change_directory("/invalid/path")
            assert not success
            assert "Directory not found" in message

    def test_find_command_with_no_results(self, executor):
        """Test that find command with no results returns appropriate message."""
        # Mock the AI processor
        executor.ai_processor.process_command = MagicMock(return_value='find . -name "nonexistent"')
        
        # Execute the command
        stdout, stderr = executor.execute("find a file named nonexistent")
        
        # Verify we get "No results found" message
        assert stdout == "No results found"
        assert stderr is None
        
    def test_find_command_with_error(self, executor):
        """Test that find command with invalid syntax returns error."""
        # Mock the AI processor to return an invalid find command
        executor.ai_processor.process_command = MagicMock(return_value='find -invalid-flag')
        
        # Execute the command
        stdout, stderr = executor.execute("find with invalid flag")
        
        # Verify we get an error message
        assert stdout is None
        assert stderr is not None
