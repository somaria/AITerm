#!/usr/bin/env python3
"""Test script for command suggestions."""

import os
import sys
from aiterm.commands.command_suggester import CommandSuggester

def main():
    """Run the suggestion test."""
    suggester = CommandSuggester()
    
    # Add some sample history
    cwd = os.getcwd()
    suggester.record_command("git status", cwd, exit_code=0)
    suggester.record_command("git add .", cwd, exit_code=0)
    suggester.record_command("git commit -m 'update'", cwd, exit_code=0)
    suggester.record_command("ls -la", cwd, exit_code=0)
    suggester.record_command("python -m pytest", cwd, exit_code=0)
    suggester.record_command("docker ps", cwd, exit_code=0)
    suggester.record_command("docker-compose up -d", cwd, exit_code=0)
    
    print("\033[1mCommand Suggestion Tester\033[0m")
    print("------------------------")
    print("Type partial commands to see suggestions.")
    print("Common prefixes to try: git, ls, python, docker")
    print("Shortcuts: g=git, py=python, doc/dk=docker")
    print("Press Enter with no input to see default suggestions")
    print("Press Ctrl+C to exit")
    print()
    
    while True:
        try:
            # Get partial input
            partial = input("\033[1m>\033[0m ")
            
            # Get suggestions (increased to 5 suggestions)
            suggestions = suggester.suggest_commands(partial, max_suggestions=5)
            placeholder = suggester.get_current_placeholder()
            
            if not suggestions and not placeholder:
                print("No suggestions found")
                continue
            
            # Show results
            print("\n\033[1mSuggestions:\033[0m")
            print("-----------")
            for i, suggestion in enumerate(suggestions, 1):
                formatted = suggester._format_suggestion(
                    suggestion, 
                    is_default=(suggestion == placeholder)
                )
                if suggestion == placeholder:
                    # Highlight default suggestion
                    print(f"\033[92m{i}. {formatted}\033[0m")
                else:
                    print(f"{i}. {formatted}")
            
            if placeholder and placeholder not in suggestions:
                formatted = suggester._format_suggestion(placeholder, is_default=True)
                print(f"\n\033[2mPlaceholder: {formatted}\033[0m")
                print("(This would be shown as a dim suggestion in the terminal)")
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
