"""Tests for command suggestion functionality."""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from aiterm.commands.command_history import CommandHistory
from aiterm.commands.command_suggester import CommandSuggester

class TestCommandHistory:
    """Test cases for CommandHistory."""
    
    @pytest.fixture
    def history_file(self):
        """Create a temporary history file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump([], f)
            return f.name
    
    @pytest.fixture
    def history(self, history_file):
        """Create a CommandHistory instance."""
        return CommandHistory(history_file)
    
    def test_add_command(self, history):
        """Test adding commands to history."""
        history.add_command("ls -l", "/home/user")
        history.add_command("git status", "/home/user/project")
        
        recent = history.get_recent_commands(2)
        assert len(recent) == 2
        assert recent[0]["command"] == "ls -l"
        assert recent[1]["command"] == "git status"
    
    def test_get_commands_in_directory(self, history):
        """Test filtering commands by directory."""
        dir1 = "/home/user"
        dir2 = "/home/user/project"
        
        history.add_command("ls -l", dir1)
        history.add_command("pwd", dir1)
        history.add_command("git status", dir2)
        
        dir1_commands = history.get_commands_in_directory(dir1)
        assert len(dir1_commands) == 2
        assert all(cmd["working_dir"] == dir1 for cmd in dir1_commands)
        
        dir2_commands = history.get_commands_in_directory(dir2)
        assert len(dir2_commands) == 1
        assert dir2_commands[0]["working_dir"] == dir2
    
    def test_get_similar_commands(self, history):
        """Test finding similar commands."""
        history.add_command("git status", "/home/user/project")
        history.add_command("git commit -m 'test'", "/home/user/project")
        history.add_command("ls -l", "/home/user/project")
        
        similar = history.get_similar_commands("git push")
        assert len(similar) > 0
        assert all("git" in cmd for cmd in similar)
        
        # Non-git command should not be in results
        assert "ls -l" not in similar
    
    def test_get_command_context(self, history):
        """Test getting command context."""
        dir1 = "/home/user/project"
        
        history.add_command("git status", dir1)
        history.add_command("git add .", dir1)
        history.add_command("git commit", dir1)
        
        context = history.get_command_context(last_n=3)
        assert context["current_directory"] == dir1
        assert len(context["recent_commands"]) == 3
        assert all(cmd.startswith("git") for cmd in context["recent_commands"])

class TestCommandSuggester:
    """Test cases for CommandSuggester."""
    
    @pytest.fixture
    def suggester(self):
        """Create a CommandSuggester instance."""
        return CommandSuggester()
    
    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a temporary git repository."""
        repo_dir = tmp_path / "git_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        return str(repo_dir)
    
    @pytest.fixture
    def python_project(self, tmp_path):
        """Create a temporary Python project."""
        project_dir = tmp_path / "python_project"
        project_dir.mkdir()
        (project_dir / "main.py").write_text("print('hello')")
        return str(project_dir)
    
    @pytest.fixture
    def docker_project(self, tmp_path):
        """Create a temporary Docker project."""
        project_dir = tmp_path / "docker_project"
        project_dir.mkdir()
        (project_dir / "Dockerfile").write_text("FROM python:3.9")
        return str(project_dir)
    
    def test_default_suggestions_git(self, suggester, git_repo):
        """Test default suggestions in git repository."""
        suggestions = suggester._get_default_suggestions(git_repo)
        assert any('git status' in cmd for cmd in suggestions)
        assert any('git log' in cmd for cmd in suggestions)
    
    def test_default_suggestions_python(self, suggester, python_project):
        """Test default suggestions in Python project."""
        suggestions = suggester._get_default_suggestions(python_project)
        assert any('pytest' in cmd for cmd in suggestions)
        assert any('pip' in cmd for cmd in suggestions)
    
    def test_default_suggestions_docker(self, suggester, docker_project):
        """Test default suggestions in Docker project."""
        suggestions = suggester._get_default_suggestions(docker_project)
        assert any('docker ps' in cmd for cmd in suggestions)
        assert any('docker-compose' in cmd for cmd in suggestions)
    
    def test_placeholder_suggestions(self, suggester, git_repo):
        """Test placeholder suggestions."""
        # Mock context
        context = {"current_directory": git_repo}
        
        # Empty input in git repo should suggest 'git status'
        placeholder = suggester._get_best_placeholder("", [], context)
        assert placeholder == "git status"
        
        # Empty input in non-git repo should suggest 'ls -la'
        context["current_directory"] = "/tmp"
        placeholder = suggester._get_best_placeholder("", [], context)
        assert placeholder == "ls -la"
        
        # Partial input should match suggestions
        suggestions = ["git status", "git log", "git branch"]
        placeholder = suggester._get_best_placeholder("git", suggestions, context)
        assert placeholder == "git status"
    
    def test_suggest_commands_with_history(self, suggester):
        """Test command suggestions based on history."""
        # Add some history
        suggester.record_command("git status", "/home/user/project")
        suggester.record_command("git add .", "/home/user/project")
        
        # Mock AI processor response
        suggester.ai_processor.process_command = MagicMock(
            return_value="git commit -m 'update'\ngit push origin main"
        )
        
        suggestions = suggester.suggest_commands("git")
        assert len(suggestions) > 0
        assert all(cmd.startswith("git") for cmd in suggestions)
        
        # Check placeholder
        assert suggester.get_current_placeholder() is not None
        assert suggester.get_current_placeholder().startswith("git")
    
    def test_suggest_commands_with_partial_input(self, suggester):
        """Test suggestions with partial input."""
        suggester.ai_processor.process_command = MagicMock(
            return_value="ls -la\nls -R\nls --color=auto"
        )
        
        suggestions = suggester.suggest_commands("ls")
        assert len(suggestions) > 0
        assert all(cmd.startswith("ls") for cmd in suggestions)
        
        # Check placeholder
        assert suggester.get_current_placeholder() is not None
        assert suggester.get_current_placeholder().startswith("ls")
    
    def test_suggest_commands_fallback(self, suggester):
        """Test fallback to history when AI fails."""
        # Add some history
        suggester.record_command("docker ps", "/home/user")
        suggester.record_command("docker images", "/home/user")
        
        # Make AI processor fail
        suggester.ai_processor.process_command = MagicMock(
            side_effect=Exception("AI service unavailable")
        )
        
        # Should fall back to similar commands from history and defaults
        suggestions = suggester.suggest_commands("docker")
        assert len(suggestions) > 0
        assert any("docker" in cmd for cmd in suggestions)
        
        # Check placeholder
        assert suggester.get_current_placeholder() is not None
        assert "docker" in suggester.get_current_placeholder()
    
    def test_accept_suggestion(self, suggester):
        """Test accepting suggestions."""
        # Set up a suggestion
        suggester.current_placeholder = "git status"
        
        # Accept the suggestion
        accepted = suggester.accept_suggestion()
        assert accepted == "git status"
        
        # No suggestion
        suggester.current_placeholder = None
        assert suggester.accept_suggestion() is None
