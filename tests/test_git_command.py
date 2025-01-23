"""Tests for the GitCommand class."""

import pytest
from unittest.mock import patch, MagicMock
from aiterm.commands.git_command import GitCommand
from aiterm.commands.ai_command_processor import AICommandProcessor

class TestGitCommand:
    """Test cases for GitCommand."""
    
    @pytest.fixture
    def git_command(self):
        """Create a GitCommand instance for testing."""
        return GitCommand()
    
    @pytest.mark.parametrize("command,expected_ai_output,expected_cmd", [
        # Show commits variations
        ("show last 2 commits", "git log -n 2", "git log -n 2"),
        ("display recent commits", "git log -n 5", "git log -n 5"),
        ("show commit history", "git log", "git log"),
        ("what were the recent changes", "git log -n 3", "git log -n 3"),
        ("display commit log", "git log", "git log"),
        ("show me the last commit", "git log -n 1", "git log -n 1"),
        ("view commit details", "git log --stat", "git log --stat"),
        ("who made recent changes", "git log --author", "git log --author"),
        
        # Status variations
        ("show status", "git status", "git status"),
        ("what changed", "git status", "git status"),
        ("show changes", "git status", "git status"),
        ("what's modified", "git status", "git status"),
        ("check repository status", "git status", "git status"),
        ("any pending changes", "git status", "git status"),
        ("what files changed", "git status", "git status"),
        ("show unstaged changes", "git status", "git status"),
        
        # Branch variations
        ("show branches", "git branch", "git branch"),
        ("list all branches", "git branch -a", "git branch -a"),
        ("display current branch", "git branch --show-current", "git branch --show-current"),
        ("what branch am i on", "git branch --show-current", "git branch --show-current"),
        ("show remote branches", "git branch -r", "git branch -r"),
        ("display all branches", "git branch -a", "git branch -a"),
        ("list local branches", "git branch", "git branch"),
        ("which branch", "git branch --show-current", "git branch --show-current"),
        
        # Commit variations
        ("commit changes with message 'test'", 'git commit -m "test"', 'git commit -m "test"'),
        ("commit all with message 'update'", 'git commit -am "update"', 'git commit -am "update"'),
        ("save changes with message 'fix bug'", 'git commit -m "fix bug"', 'git commit -m "fix bug"'),
        ("commit everything", "git commit -a", "git commit -a"),
        ("stage and commit all changes", 'git commit -am "update"', 'git commit -am "update"'),
        ("commit with message", 'git commit -m "update"', 'git commit -m "update"'),
        ("save all modifications", 'git commit -am "update"', 'git commit -am "update"'),
        
        # Push/Pull variations
        ("push changes", "git push", "git push"),
        ("push to origin", "git push origin", "git push origin"),
        ("pull updates", "git pull", "git pull"),
        ("pull from origin", "git pull origin", "git pull origin"),
        ("upload changes", "git push", "git push"),
        ("download updates", "git pull", "git pull"),
        ("sync with remote", "git pull && git push", "git pull && git push"),
        ("update from remote", "git pull", "git pull"),
        ("push to remote", "git push", "git push"),
        ("get latest changes", "git pull", "git pull"),
        
        # Diff variations
        ("show differences", "git diff", "git diff"),
        ("what did i change", "git diff", "git diff"),
        ("show file changes", "git diff", "git diff"),
        ("display modifications", "git diff", "git diff"),
        ("what's different", "git diff", "git diff"),
        ("show staged changes", "git diff --staged", "git diff --staged"),
        
        # Add variations
        ("stage all changes", "git add .", "git add ."),
        ("add modified files", "git add -u", "git add -u"),
        ("stage this file", "git add", "git add"),
        ("add all files", "git add .", "git add ."),
        ("stage everything", "git add -A", "git add -A"),
        ("prepare for commit", "git add .", "git add ."),
        
        # Stash variations
        ("save my changes", "git stash", "git stash"),
        ("stash modifications", "git stash", "git stash"),
        ("temporarily store changes", "git stash", "git stash"),
        ("apply stashed changes", "git stash pop", "git stash pop"),
        ("restore stashed work", "git stash apply", "git stash apply"),
        ("show stashed changes", "git stash list", "git stash list"),
    ])
    def test_command_interpretation(self, git_command, command, expected_ai_output, expected_cmd):
        """Test git command interpretation through AI."""
        with patch.object(AICommandProcessor, 'process_command') as mock_process:
            # Mock AI response
            mock_process.return_value = expected_ai_output
            
            # Mock subprocess call
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.stdout = "Command output"
                mock_result.stderr = None
                mock_run.return_value = mock_result
                
                # Execute command
                result = git_command.execute(command)
                
                # Verify AI was called correctly
                mock_process.assert_called_once_with(command)
                
                # Verify the correct git command was executed
                mock_run.assert_called_once()
                actual_cmd = mock_run.call_args[0][0]
                assert actual_cmd == expected_cmd, f"Expected {expected_cmd}, got {actual_cmd}"
    
    def test_error_handling(self, git_command):
        """Test error handling in git commands."""
        with patch.object(AICommandProcessor, 'process_command') as mock_process, \
             patch('subprocess.run') as mock_run:
            
            # Test AI processing error
            mock_process.side_effect = Exception("AI processing failed")
            result = git_command.execute("show commits")
            assert "Error" in result
            assert "AI processing failed" in result
            
            # Test git command execution error
            mock_process.side_effect = None
            mock_process.return_value = "git log"
            mock_run.side_effect = Exception("Git command failed")
            
            result = git_command.execute("show commits")
            assert "Error" in result
            assert "Git command failed" in result
    
    @pytest.mark.parametrize("command,expected_output", [
        ("git status", "On branch main\nNothing to commit"),
        ("git log", "commit abc123\nAuthor: Test"),
        ("git branch", "* main\n  develop"),
        ("git diff", "diff --git a/file b/file\n+new line"),
        ("git stash list", "stash@{0}: WIP on main"),
        ("git remote -v", "origin git@github.com:user/repo.git"),
    ])
    def test_direct_git_commands(self, git_command, command, expected_output):
        """Test direct git commands without AI interpretation."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = expected_output
            mock_result.stderr = None
            mock_run.return_value = mock_result
            
            result = git_command.execute(command)
            assert result == expected_output
            mock_run.assert_called_once_with(command, shell=True, capture_output=True, text=True, cwd=None)
