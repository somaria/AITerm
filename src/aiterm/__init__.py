"""AITerm package initialization."""

"""
AI-powered Terminal Application
"""

__version__ = '0.1.0'

from .gui.terminal import TerminalGUI
from .gui.window_manager import WindowManager
from .utils.logger import get_logger
from .utils.completer import TerminalCompleter

__all__ = ['TerminalGUI', 'WindowManager', 'get_logger', 'TerminalCompleter']
