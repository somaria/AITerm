"""Logging utility for AITerm."""

import logging
import os
import glob
from datetime import datetime

def cleanup_logs() -> str:
    """Remove all log files from the logs directory."""
    try:
        log_files = glob.glob('logs/aiterm_*.log')
        if not log_files:
            return "No log files found to clean up."
        
        for log_file in log_files:
            os.remove(log_file)
        return f"Successfully removed {len(log_files)} log files."
    except Exception as e:
        return f"Error cleaning up logs: {str(e)}"

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
