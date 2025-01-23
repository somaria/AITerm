"""Logging utility for AITerm."""

import logging
import os
from datetime import datetime

def get_logger(name: str = None) -> logging.Logger:
    """Get or create a logger instance."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/aiterm_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Return logger instance
    return logging.getLogger(name if name else __name__)
