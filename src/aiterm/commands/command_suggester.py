"""AI-powered command suggestions based on history and context."""

import os
from typing import List, Dict, Optional, Tuple
from .command_history import CommandHistory
from .ai_command_processor import AICommandProcessor
import re
import logging

logger = logging.getLogger(__name__)

class CommandSuggester:
    """Suggests commands based on user input and command history."""
    
    # Command descriptions for better help
    COMMAND_DESCRIPTIONS = {
        'docker': {
            # Docker commands
            'docker ps': 'List running containers',
            'docker images': 'List all images',
            'docker system prune': 'Clean up unused data',
            'docker logs -f': 'Follow container logs',
            'docker exec -it': 'Enter a running container',
            'docker build -t': 'Build an image',
            'docker container ls': 'List all containers',
            # Docker-compose commands
            'docker-compose up': 'Start services',
            'docker-compose up -d': 'Start services in background',
            'docker-compose down': 'Stop and remove containers',
            'docker-compose ps': 'List compose services',
            'docker-compose pull': 'Update service images',
            'docker-compose restart': 'Restart services',
            'docker-compose logs': 'View service logs',
            'docker-compose build': 'Build/rebuild services',
            'docker-compose config': 'Validate compose file',
            'docker-compose exec': 'Execute command in service',
        }
    }

    # Default suggestions for different contexts
    DEFAULT_SUGGESTIONS = {
        'general': [
            'ls -la',  # List all files with details
            'pwd',     # Show current directory
            'df -h',   # Show disk usage
            'top',     # Show system usage
        ],
        'git': [
            'git status',
            'git log --oneline',
            'git branch -a',
            'git diff',
            'git push origin main',
            'git pull origin main',
        ],
        'python': [
            'python -m pytest',
            'pip list',
            'python setup.py develop',
            'python -m venv .venv',
            'pip install -r requirements.txt',
            'python -m pip install --upgrade pip',
        ],
        'docker': [
            # Docker container commands
            'docker ps',                    
            'docker images',                
            'docker system prune',          
            'docker logs -f',               
            'docker exec -it',              
            'docker build -t myapp .',      
            'docker container ls',          
            # Docker-compose commands
            'docker-compose up',            
            'docker-compose up -d',         
            'docker-compose down',          
            'docker-compose ps',            
            'docker-compose pull',          
            'docker-compose restart',       
            'docker-compose logs',          
            'docker-compose build',         
            'docker-compose config',        
            'docker-compose exec',          
        ]
    }
    
    def __init__(self):
        """Initialize the command suggester."""
        self.command_history = CommandHistory()
        self.ai_processor = AICommandProcessor()
        self.current_suggestions: List[str] = []
        self.current_placeholder: Optional[str] = None
        
        # Default commands
        self.default_commands = {
            # Theme commands
            "dark": "Switch to dark theme",
            "light": "Switch to light theme",
            
            # Git commands
            "status": "Check git status",
            "commit": "Commit changes",
            "push": "Push changes",
            "pull": "Pull changes",
            "add": "Stage files",
            "branch": "List branches",
            "checkout": "Switch branches",
            "merge": "Merge branches",
            "stash": "Stash changes",
            "log": "View commit history",
            "diff": "Show changes",
            
            # Docker commands
            "docker": "Run docker command",
            "docker-compose": "Run docker-compose command",
            "docker ps": "List containers",
            "docker images": "List images",
            "docker build": "Build image",
            "docker run": "Run container",
            
            # Python commands
            "python": "Run python script",
            "pip": "Package installer",
            "pytest": "Run tests",
            "python -m": "Run module",
            "pip install": "Install package",
            "pip uninstall": "Remove package",
        }
        
        # Add default commands to history with a default working directory
        for cmd in self.default_commands:
            self.command_history.add_command(cmd, working_dir="/", exit_code=0, output="")

    def get_similar_commands(self, command: str, max_suggestions: int = 5) -> List[str]:
        """Get commands similar to the given command."""
        # Get all commands from history
        all_commands = self.command_history.get_all_commands()
        
        # Calculate similarity scores
        scores = []
        for cmd in all_commands:
            score = self._calculate_similarity(command, cmd['command'])
            if score > 0.3:  # Only include reasonably similar commands
                scores.append((score, cmd))
        
        # Sort by similarity score and return top N
        scores.sort(reverse=True)
        return [cmd['command'] for _, cmd in scores[:max_suggestions]]
    
    def get_current_placeholder(self) -> Optional[str]:
        """Get the current placeholder suggestion."""
        if self.current_suggestions:
            return self.current_suggestions[0]
        return None
    
    def suggest_commands(self, command: str) -> List[str]:
        """Suggest commands based on input."""
        suggestions = []

        # Get similar commands from history
        if command:
            similar = self.command_history.get_similar_commands(command)
            suggestions.extend(similar)

        # Add default suggestions
        if command in self.default_commands:
            suggestions.append(command)
        else:
            # Try to fix typos
            fixed = self._fix_typos(command)
            suggestions.extend(fixed)

        # Get suggestions from AI
        try:
            ai_suggestions = self.ai_processor.process_command(command)
            if ai_suggestions:
                suggestions.extend(ai_suggestions.split('\n'))
        except Exception as e:
            logger.error(f"Error getting AI suggestions: {str(e)}")

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)

        return unique_suggestions

    def get_suggestions(self, text: str) -> List[str]:
        """Get command suggestions based on current input."""
        if not text:
            return []
            
        # Fix any typos first
        fixed_command = self._fix_typos(text)
        logger.info(f"Corrected '{text}' to '{fixed_command}'")
        
        # Split into parts
        parts = fixed_command.split()
        if not parts:
            return []
            
        # Get command part
        cmd = parts[0].lower()
        
        # Get relevant history entries
        history_entries = self.command_history.history if hasattr(self.command_history, 'history') else []
        suggestions = []
        
        # First try exact matches from history
        for hist_entry in history_entries:
            if not isinstance(hist_entry, dict) or 'command' not in hist_entry:
                continue
                
            # Try both original and interpreted commands
            hist_cmd = hist_entry['command']
            interpreted_cmd = hist_entry.get('interpreted_as')
            
            # Check original command
            hist_parts = hist_cmd.lower().split()
            if hist_parts and hist_parts[0].startswith(cmd):
                if hist_cmd not in suggestions:
                    suggestions.append(hist_cmd)
                    
            # Check interpreted command if present
            if interpreted_cmd:
                int_parts = interpreted_cmd.lower().split()
                if int_parts and int_parts[0].startswith(cmd):
                    if interpreted_cmd not in suggestions:
                        suggestions.append(interpreted_cmd)
                    
        # Then try default commands
        for default_cmd in self.default_commands:
            if default_cmd.lower().startswith(cmd):
                if default_cmd not in suggestions:
                    suggestions.append(default_cmd)
                    
        # If no matches found, try similar commands
        if not suggestions:
            for hist_entry in history_entries:
                if not isinstance(hist_entry, dict) or 'command' not in hist_entry:
                    continue
                    
                # Try both original and interpreted commands
                hist_cmd = hist_entry['command']
                interpreted_cmd = hist_entry.get('interpreted_as')
                
                # Check original command
                hist_parts = hist_cmd.lower().split()
                if hist_parts:
                    similarity = self._similarity(cmd, hist_parts[0])
                    if similarity > 0.7:  # Threshold for similarity
                        if hist_cmd not in suggestions:
                            suggestions.append(hist_cmd)
                            
                # Check interpreted command if present
                if interpreted_cmd:
                    int_parts = interpreted_cmd.lower().split()
                    if int_parts:
                        similarity = self._similarity(cmd, int_parts[0])
                        if similarity > 0.7:  # Threshold for similarity
                            if interpreted_cmd not in suggestions:
                                suggestions.append(interpreted_cmd)
                        
        # Limit number of suggestions
        return suggestions[:5]  # Return top 5 suggestions

    def _prioritize_suggestions(self, suggestions: List[str], partial_args: str = "") -> List[str]:
        """Prioritize suggestions based on partial arguments."""
        if not partial_args:
            return suggestions
            
        # Split suggestions into command and description
        parsed = []
        for s in suggestions:
            cmd = s
            desc = ""
            if "(" in s and ")" in s:
                cmd = s[:s.find("(")].strip()
                desc = s[s.find("("):].strip()
            parsed.append((cmd, desc))
        
        # Get command context
        cmd_parts = partial_args.lower().split()
        context = self._get_command_context(['docker'] + cmd_parts)
        
        # Get context-specific suggestions
        context_suggestions = self._get_command_suggestions_by_type(context['type'], context['subtype'])
        
        # Score each suggestion based on argument match
        scored = []
        for cmd, desc in parsed:
            score = 0
            cmd_parts = cmd.lower().split()
            partial_parts = partial_args.lower().split()
            
            # Context matching
            if cmd in context_suggestions:
                score += 5
            
            # Type matching
            if context['type'] == 'compose':
                if 'docker-compose' in cmd.lower():
                    score += 3
            elif context['type'] == 'docker':
                if not 'docker-compose' in cmd.lower():
                    score += 3
            
            # Subtype matching
            if context['subtype']:
                if context['subtype'] in cmd.lower():
                    score += 2
                if context['action'] and context['action'] in cmd.lower():
                    score += 2
            
            # Exact matches score higher
            for part in partial_parts:
                if any(p == part for p in cmd_parts[1:]):
                    score += 3
                elif any(p.startswith(part) for p in cmd_parts[1:]):
                    score += 2
                elif any(part in p for p in cmd_parts[1:]):
                    score += 1
            
            # Prefer simpler commands
            if len(cmd_parts) <= 3:
                score += 1
            
            # Boost frequently used commands
            common_commands = {
                'docker ps': 2,
                'docker images': 2,
                'docker system prune': 2,
                'docker-compose up -d': 2,
                'docker-compose up': 1,
                'docker-compose down': 2,
                'docker exec -it': 1,
                'docker logs -f': 1,
            }
            base_cmd = ' '.join(cmd_parts[:2])
            if base_cmd in common_commands:
                score += common_commands[base_cmd]
            
            # Special handling for lifecycle commands
            lifecycle_commands = ['start', 'stop', 'restart']
            if any(lc in cmd.lower() for lc in lifecycle_commands):
                for part in partial_parts:
                    if any(lc.startswith(part) for lc in lifecycle_commands):
                        score += 2
            
            scored.append((score, cmd, desc))
        
        # Sort by score and rebuild suggestions
        scored.sort(reverse=True)
        result = []
        default_set = False
        
        for score, cmd, desc in scored:
            if score > 0 and not default_set:
                result.append(f"{cmd} {desc} (default)")
                default_set = True
            else:
                result.append(f"{cmd} {desc}".strip())
        
        # Add remaining suggestions that didn't match
        for score, cmd, desc in scored:
            if score == 0 and f"{cmd} {desc}".strip() not in result:
                result.append(f"{cmd} {desc}".strip())
        
        return result

    def _get_command_context(self, cmd_parts: List[str]) -> dict:
        """Get context information about the command."""
        if not cmd_parts:
            return {'type': None, 'subtype': None, 'action': None}
            
        cmd = cmd_parts[0].lower()
        action = cmd_parts[1].lower() if len(cmd_parts) > 1 else None
        subaction = cmd_parts[2].lower() if len(cmd_parts) > 2 else None
        
        # Common command patterns
        contexts = {
            'images': {'type': 'docker', 'subtype': 'image', 'actions': ['i', 'im', 'ima', 'img', 'image', 'images']},
            'logs': {'type': 'docker', 'subtype': 'logs', 'actions': ['l', 'log', 'logs']},
            'system': {'type': 'docker', 'subtype': 'system', 'actions': ['s', 'sys', 'system']},
            'ps': {'type': 'docker', 'subtype': 'process', 'actions': ['p', 'ps', 'proc', 'process']},
            'exec': {'type': 'docker', 'subtype': 'exec', 'actions': ['e', 'ex', 'exe', 'exec']},
            'compose': {'type': 'docker', 'subtype': 'compose', 'actions': ['c', 'comp', 'compose']},
            'build': {'type': 'docker', 'subtype': 'build', 'actions': ['b', 'build']},
            'run': {'type': 'docker', 'subtype': 'run', 'actions': ['r', 'run']},
            'start': {'type': 'docker', 'subtype': 'lifecycle', 'actions': ['st', 'start']},
            'stop': {'type': 'docker', 'subtype': 'lifecycle', 'actions': ['sp', 'stop']},
            'restart': {'type': 'docker', 'subtype': 'lifecycle', 'actions': ['rs', 'restart']},
            'stats': {'type': 'docker', 'subtype': 'monitoring', 'actions': ['st', 'stats']},
        }
        
        # Docker-compose specific contexts
        compose_contexts = {
            'up': {'type': 'compose', 'subtype': 'lifecycle', 'actions': ['u', 'up']},
            'down': {'type': 'compose', 'subtype': 'lifecycle', 'actions': ['d', 'down']},
            'start': {'type': 'compose', 'subtype': 'lifecycle', 'actions': ['st', 'start']},
            'stop': {'type': 'compose', 'subtype': 'lifecycle', 'actions': ['sp', 'stop']},
            'restart': {'type': 'compose', 'subtype': 'lifecycle', 'actions': ['rs', 'restart']},
            'logs': {'type': 'compose', 'subtype': 'logs', 'actions': ['l', 'log', 'logs']},
            'ps': {'type': 'compose', 'subtype': 'process', 'actions': ['p', 'ps']},
            'pull': {'type': 'compose', 'subtype': 'image', 'actions': ['pull']},
            'push': {'type': 'compose', 'subtype': 'image', 'actions': ['push']},
            'config': {'type': 'compose', 'subtype': 'config', 'actions': ['c', 'cf', 'config']},
        }
        
        # First check if it's a compose command
        if action in ['c', 'comp', 'compose', 'dc'] and subaction:
            for context_type, context in compose_contexts.items():
                if subaction in context['actions']:
                    return {
                        'type': context['type'],
                        'subtype': context['subtype'],
                        'action': context_type
                    }
            # If no specific match but it is a compose command
            return {'type': 'compose', 'subtype': None, 'action': None}
        
        # Then check regular docker commands
        if action:
            for context_type, context in contexts.items():
                if action in context['actions']:
                    return {
                        'type': context['type'],
                        'subtype': context['subtype'],
                        'action': context_type
                    }
        
        return {'type': None, 'subtype': None, 'action': None}

    def _get_ai_suggestions(self, partial_input: str, context: Dict) -> List[str]:
        """Get suggestions from AI model.
        
        Args:
            partial_input: Partial command input
            context: Command context dictionary
            
        Returns:
            List of suggested commands
        """
        try:
            prompt = self._build_suggestion_prompt(partial_input, context)
            suggestions = self.ai_processor.process_command(
                prompt,
                command_type='suggestion'
            )
            
            # Clean and filter suggestions
            commands = []
            for line in suggestions.strip().split('\n'):
                # Skip empty lines and lines that look like prose rather than commands
                line = line.strip()
                if (line and 
                    not line.startswith(('suggest', 'current', 'recent', 'partial')) and
                    not any(word in line.lower() for word in ['directory:', 'commands:', 'based on:', 'provide', 'input:'])):
                    commands.append(line)
            
            return commands
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return []
    
    def _get_default_suggestions(self, directory: str) -> List[str]:
        """Get default suggestions based on directory context.
        
        Args:
            directory: Current working directory
            
        Returns:
            List of default suggestions
        """
        suggestions = []
        
        # Add general suggestions
        suggestions.extend(self.DEFAULT_SUGGESTIONS['general'])
        
        # Check for git repository
        if os.path.exists(os.path.join(directory, '.git')):
            suggestions.extend(self.DEFAULT_SUGGESTIONS['git'])
        
        # Check for Python project
        if any(f.endswith('.py') for f in os.listdir(directory)):
            suggestions.extend(self.DEFAULT_SUGGESTIONS['python'])
        
        # Check for Docker project
        if any(f in os.listdir(directory) for f in ['Dockerfile', 'docker-compose.yml']):
            suggestions.extend(self.DEFAULT_SUGGESTIONS['docker'])
        
        return suggestions
    
    def _get_best_placeholder(self, partial_input: str, suggestions: List[str], context: Dict) -> Optional[str]:
        """Get the best suggestion to show as placeholder.
        
        Args:
            partial_input: Partial command input
            suggestions: List of current suggestions
            context: Command context
            
        Returns:
            Best suggestion for placeholder
        """
        current_dir = context.get('current_directory', '')
        
        if not partial_input:
            # Check for git repository
            if os.path.exists(os.path.join(current_dir, '.git')):
                return 'git status'
            # Check for Python files
            elif any(f.endswith('.py') for f in os.listdir(current_dir)):
                return 'python -m pytest'
            # Check for Docker
            elif any(f in os.listdir(current_dir) for f in ['Dockerfile', 'docker-compose.yml']):
                return 'docker-compose up'
            # Default to ls
            return 'ls -la'
        
        # If we have suggestions matching the partial input exactly, prioritize those
        exact_matches = [
            s for s in suggestions
            if s.lower().startswith(partial_input.lower())
        ]
        if exact_matches:
            # Prioritize commands from history in current directory
            dir_history = self.command_history.get_commands_in_directory(current_dir)
            dir_commands = [cmd['command'] for cmd in dir_history]
            for cmd in exact_matches:
                if cmd in dir_commands:
                    return cmd
            return exact_matches[0]
        
        # If no direct matches but we have suggestions, use the first one
        if suggestions:
            return suggestions[0]
        
        return None
    
    def accept_suggestion(self) -> Optional[str]:
        """Accept the current placeholder suggestion.
        
        Returns:
            Accepted suggestion or None if no placeholder
        """
        return self.current_placeholder
    
    def _build_suggestion_prompt(self, partial_input: str, context: Dict) -> str:
        """Build prompt for AI command suggestions.
        
        Args:
            partial_input: Partial command input
            context: Command context dictionary
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "Suggest relevant shell commands based on:",
            f"\nCurrent directory: {context.get('current_directory', os.getcwd())}",
        ]
        
        if context.get('recent_commands'):
            prompt_parts.append("\nRecent commands:")
            for cmd in context['recent_commands']:
                prompt_parts.append(f"  {cmd}")
                
        if partial_input:
            prompt_parts.append(f"\nPartial input: {partial_input}")
            
        prompt_parts.append("\nProvide specific, contextually relevant command suggestions.")
        
        return '\n'.join(prompt_parts)
    
    def record_command(self, command: str, working_dir: str, exit_code: int = 0, output: str = ""):
        """Record an executed command in history.
        
        Args:
            command: The command that was executed
            working_dir: Working directory when command was executed
            exit_code: Command exit code (0 for success)
            output: Command output
        """
        self.command_history.add_command(command, working_dir, exit_code, output)

    def _get_fallback_suggestions(self, partial_input: str, current_dir: str) -> List[str]:
        """Get fallback suggestions when main suggestion logic fails.
        
        Args:
            partial_input: Partial command input
            current_dir: Current working directory
            
        Returns:
            List of fallback suggestions
        """
        default_suggestions = self._get_default_suggestions(current_dir)
        if partial_input:
            default_suggestions = [
                cmd for cmd in default_suggestions 
                if self._is_command_match(cmd, partial_input, None)
            ]
        return default_suggestions[:3]

    def _format_suggestion(self, cmd: str, is_default: bool = False) -> str:
        """Format a command suggestion with its description if available."""
        if cmd.startswith('docker'):
            # Get the base command without arguments for description lookup
            base_cmd = cmd.split(' | ')[0]
            # Try exact match first
            desc = self.COMMAND_DESCRIPTIONS.get('docker', {}).get(base_cmd)
            if not desc:
                # Try matching just the start of the command
                for cmd_pattern, description in self.COMMAND_DESCRIPTIONS['docker'].items():
                    if base_cmd.startswith(cmd_pattern):
                        desc = description
                        break
            
            if desc:
                formatted = f"{cmd} ({desc})"
                if is_default:
                    formatted += " (default)"
                return formatted
        
        return f"{cmd} (default)" if is_default else cmd

    def _is_command_match(self, cmd: str, partial: str, cmd_type: Optional[str], strict: bool = False) -> bool:
        """Check if a command matches the partial input and command type."""
        cmd_lower = cmd.lower()
        partial_lower = self._fix_typos(partial.lower())
        
        # Special handling for docker-compose commands
        if any(partial_lower.startswith(prefix) for prefix in ['docker-c', 'docker-compose', 'dcomp', 'docket-c']):
            return cmd_lower.startswith('docker-compose')
        
        # Special handling for Docker commands
        if cmd_type == 'docker':
            if partial_lower.startswith('docker-'):
                # If specifically looking for docker-compose commands
                return cmd_lower.startswith('docker-compose')
            elif partial_lower == 'docker':
                # If just 'docker', show all docker commands
                return cmd_lower.startswith('docker')
            else:
                # Otherwise show both
                return (cmd_lower.startswith('docker') or cmd_lower.startswith('docker-compose'))
        
        # If we have a command type, check if command matches type
        if cmd_type:
            if strict:
                return cmd_lower.startswith(cmd_type) and partial_lower in cmd_lower
            else:
                return cmd_type in cmd_lower and partial_lower in cmd_lower
        
        # If no command type, just check if command contains partial
        return partial_lower in cmd_lower

    def _get_docker_suggestions(self) -> List[str]:
        """Get Docker-specific command suggestions."""
        return [
            "docker ps (List running containers)",
            "docker images (List all images)",
            "docker system prune (Clean up unused data)",
            "docker logs -f (Follow container logs)",
            "docker exec -it (Enter a running container)",
            "docker container ls (List all containers)",
            "docker inspect (View container details)",
            "docker stats (View resource usage)",
            "docker-compose up -d (Start services in background)",
            "docker-compose down (Stop and remove containers)",
        ]

    def _get_docker_compose_suggestions(self) -> List[str]:
        """Get Docker Compose specific suggestions."""
        return [
            "docker-compose up -d (Start services in background)",
            "docker-compose up (Start services)",
            "docker-compose down (Stop and remove containers)",
            "docker-compose ps (List services)",
            "docker-compose logs (View service logs)",
            "docker-compose restart (Restart services)",
            "docker-compose pull (Update service images)",
            "docker-compose config (Validate compose file)",
            "docker-compose exec (Run command in service)",
            "docker-compose build (Build service images)",
        ]

    def _get_command_suggestions_by_type(self, cmd_type: str, subtype: str = None) -> List[str]:
        """Get suggestions based on command type and subtype."""
        suggestions = []
        
        if cmd_type == 'docker':
            if subtype == 'image':
                suggestions = [
                    "docker images (List all images)",
                    "docker pull (Pull an image)",
                    "docker push (Push an image)",
                    "docker build (Build an image)",
                    "docker rmi (Remove images)",
                ]
            elif subtype == 'container':
                suggestions = [
                    "docker ps (List running containers)",
                    "docker container ls (List all containers)",
                    "docker exec -it (Enter a running container)",
                    "docker logs -f (Follow container logs)",
                    "docker inspect (View container details)",
                ]
            elif subtype == 'system':
                suggestions = [
                    "docker system prune (Clean up unused data)",
                    "docker system df (Show docker disk usage)",
                    "docker info (Display system-wide info)",
                ]
            elif subtype == 'logs':
                suggestions = [
                    "docker logs -f (Follow container logs)",
                    "docker logs (View container logs)",
                ]
            elif subtype == 'lifecycle':
                suggestions = [
                    "docker start (Start containers)",
                    "docker stop (Stop containers)",
                    "docker restart (Restart containers)",
                    "docker pause (Pause containers)",
                    "docker unpause (Unpause containers)",
                ]
            elif subtype == 'monitoring':
                suggestions = [
                    "docker stats (View resource usage)",
                    "docker top (Display container processes)",
                    "docker events (Get real time events)",
                ]
        elif cmd_type == 'compose':
            if subtype == 'lifecycle':
                suggestions = [
                    "docker-compose up -d (Start services in background)",
                    "docker-compose up (Start services)",
                    "docker-compose down (Stop and remove containers)",
                    "docker-compose start (Start services)",
                    "docker-compose stop (Stop services)",
                    "docker-compose restart (Restart services)",
                ]
            elif subtype == 'logs':
                suggestions = [
                    "docker-compose logs -f (Follow service logs)",
                    "docker-compose logs (View service logs)",
                ]
            elif subtype == 'process':
                suggestions = [
                    "docker-compose ps (List services)",
                    "docker-compose top (Display service processes)",
                ]
            elif subtype == 'image':
                suggestions = [
                    "docker-compose pull (Update service images)",
                    "docker-compose push (Push service images)",
                    "docker-compose build (Build service images)",
                ]
            elif subtype == 'config':
                suggestions = [
                    "docker-compose config (Validate compose file)",
                    "docker-compose convert (Convert compose file)",
                ]
        
        return suggestions if suggestions else self._get_docker_suggestions()

    def _fuzzy_match_docker(self, cmd: str) -> bool:
        """Fuzzy match for docker command variations."""
        # Common patterns that indicate a docker command
        patterns = [
            r'^d[aoe]?c?k.*',  # Matches: d, da, do, dk, dock, etc.
            r'^d[aoe]r?k.*',   # Matches: dark, dork, etc.
            r'^d[aoe].*r.*k.*', # Matches variations with r and k
            r'^d.*o.*c.*k.*',  # Matches variations of dock
            r'^d.*[oa].*[ck].*', # More flexible pattern
        ]
        
        # Convert to lowercase for matching
        cmd = cmd.lower()
        
        # First check exact prefixes
        docker_prefixes = {'d', 'do', 'doc', 'dock', 'da', 'dk'}
        if any(cmd.startswith(prefix) for prefix in docker_prefixes):
            return True
        
        # Then try regex patterns
        return any(re.match(pattern, cmd) for pattern in patterns)

    def _fix_typos(self, text: str) -> str:
        """Fix common typos in commands based on history."""
        if not text:
            return text
            
        # Get command part (first word)
        parts = text.split()
        if not parts:
            return text
            
        cmd = parts[0].lower()
        
        # Get history entries
        history_entries = self.command_history.history if hasattr(self.command_history, 'history') else []
        
        # Check against history
        for hist_entry in history_entries:
            if not isinstance(hist_entry, dict) or 'command' not in hist_entry:
                continue
                
            hist_cmd = hist_entry['command']
            hist_parts = hist_cmd.lower().split()
            if not hist_parts:
                continue
                
            # If very similar, use the historical command
            similarity = self._similarity(cmd, hist_parts[0])
            if similarity > 0.8:  # High threshold for auto-correction
                logger.info(f"Auto-correcting '{cmd}' to '{hist_parts[0]}'")
                # Replace just the command part
                parts[0] = hist_parts[0]
                return ' '.join(parts)
                
        # No correction needed
        return text
        
    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        if not s1 or not s2:
            return 0.0
            
        # Convert to lowercase for comparison
        s1 = s1.lower()
        s2 = s2.lower()
        
        # If strings are equal, return 1.0
        if s1 == s2:
            return 1.0
            
        # Calculate Levenshtein distance
        m = len(s1)
        n = len(s2)
        
        # Create matrix
        d = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(m + 1):
            d[i][0] = i
        for j in range(n + 1):
            d[0][j] = j
            
        # Fill in the rest of the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1
                    
        # Calculate similarity score
        max_len = max(m, n)
        if max_len == 0:
            return 0.0
        return 1.0 - (d[m][n] / max_len)

    def _calculate_similarity(self, cmd1: str, cmd2: str) -> float:
        """Calculate similarity score between two commands."""
        # Simple substring matching for now
        cmd1 = cmd1.lower()
        cmd2 = cmd2.lower()
        
        # Direct substring match
        if cmd1 in cmd2 or cmd2 in cmd1:
            return 1.0
        
        # Split into words and check for common words
        words1 = set(cmd1.split())
        words2 = set(cmd2.split())
        common_words = words1.intersection(words2)
        
        if not words1 or not words2:
            return 0.0
            
        # Calculate Jaccard similarity
        similarity = len(common_words) / len(words1.union(words2))
        return similarity

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1 
                deletions = current_row[j] + 1  
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
