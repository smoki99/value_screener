"""
Logging Configuration Module

Centralized logging setup for the NASDAQ-100 Screener application.
Log level can be configured via LOG_LEVEL environment variable.
"""

import logging
import os
from datetime import datetime


def get_log_level():
    """
    Get log level from environment variable.
    
    Returns:
        int: Logging level constant (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Environment Variables:
        LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
                   Default: INFO
    """
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    return getattr(logging, log_level_str, logging.INFO)


def setup_logging():
    """
    Configure logging for the application.
    
    Sets up root logger with formatted output suitable for Docker containers.
    Logs are written to stdout/stderr which Docker captures automatically.
    
    Returns:
        Logger: Root logger instance
    """
    log_level = get_log_level()
    
    # Configure root logger
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=log_level,
        handlers=[logging.StreamHandler()]  # Output to stdout/stderr
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized at level: %s", logging.getLevelName(log_level))
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance for a specific module.
    
    Args:
        name (str, optional): Logger name. If None, returns root logger.
    
    Returns:
        Logger: Logger instance
    """
    return logging.getLogger(name)
