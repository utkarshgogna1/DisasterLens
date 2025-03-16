"""
Logging utilities for DisasterLens.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from src.utils.config import ROOT_DIR

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_format: str = DEFAULT_LOG_FORMAT,
    log_to_file: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a logger with the specified name and configuration.
    
    Args:
        name (str): Logger name
        level (int): Logging level (default: logging.INFO)
        log_format (str): Log format string
        log_to_file (bool): Whether to log to a file
        log_file (Optional[str]): Log file path (default: logs/{name}_{timestamp}.log)
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(LOGS_DIR, f"{name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = get_logger("disasterlens") 