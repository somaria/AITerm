"""Logging configuration for AITerm."""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name: str = None) -> logging.Logger:
    """Set up and return a logger instance."""
    # Create logger
    logger = logging.getLogger(name or __name__)
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Create file handler
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'aiterm_{timestamp}.log'
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger('aiterm')
