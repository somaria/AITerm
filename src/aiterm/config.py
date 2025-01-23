"""
Configuration module for AITerm
"""
import os
from dotenv import load_dotenv, find_dotenv
import openai
from .utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Find and load .env file
env_path = find_dotenv()
logger.info(f"Found .env file at: {env_path}")
load_dotenv(env_path)

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key not found in environment variables")

# Print masked API key for debugging
masked_key = f"{OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}"
logger.info(f"Loaded OpenAI API key (masked): {masked_key}")

# Set OpenAI API key globally
openai.api_key = OPENAI_API_KEY

# Get model name
OPENAI_MODEL = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')
logger.info(f"Using OpenAI model: {OPENAI_MODEL}")

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
