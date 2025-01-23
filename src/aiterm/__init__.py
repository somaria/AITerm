"""AITerm package initialization."""

"""
AI-powered Terminal Application
"""

__version__ = '0.1.0'

# Import command-line functionality
from .commands import (
    GitCommand,
    CommandInterpreter,
    CommandInterpretationError,
    CommandExecutor,
    AICommandProcessor
)

from .utils.logger import get_logger

__all__ = [
    # Command-line functionality
    'GitCommand',
    'CommandInterpreter',
    'CommandInterpretationError',
    'CommandExecutor',
    'AICommandProcessor',
    'get_logger',
]

# Only import GUI components when needed
def get_gui_components():
    """Get GUI components for the application."""
    from .gui.terminal import TerminalGUI
    from .gui.window_manager import WindowManager
    from .utils.completer import TerminalCompleter
    
    return {
        'TerminalGUI': TerminalGUI,
        'WindowManager': WindowManager,
        'TerminalCompleter': TerminalCompleter
    }
