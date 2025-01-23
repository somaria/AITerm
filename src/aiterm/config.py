"""
Configuration module for AITerm
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')

# Terminal configuration
TERMINAL_FONT = ('Menlo', 12)  # Default monospace font for macOS
TERMINAL_BG_COLOR = 'black'
TERMINAL_FG_COLOR = 'white'
TERMINAL_CURSOR_COLOR = 'white'
TERMINAL_SELECT_BG = '#3584e4'  # Blue selection background
TERMINAL_SELECT_FG = 'white'

# Window configuration
WINDOW_TITLE = 'AITerm'
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1024
WINDOW_DEFAULT_HEIGHT = 768

# History configuration
MAX_HISTORY_SIZE = 1000
HISTORY_FILE = os.path.expanduser('~/.aiterm_history')

# Logging configuration
LOG_DIR = 'logs'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
LOG_LEVEL = 'DEBUG'  # Can be DEBUG, INFO, WARNING, ERROR, CRITICAL
