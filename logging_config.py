#!/usr/bin/env python3
"""
Logging Configuration for TorWAR
Author: Mohamed Toraif

Centralized logging configuration with different levels and handlers
for better performance and debugging control.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime

class TorWARLogger:
    """Centralized logging manager for TorWAR application."""
    
    def __init__(self, app_name="TorWAR", log_dir="logs"):
        self.app_name = app_name
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.loggers = {}
        
    def ensure_log_directory(self):
        """Ensure log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def get_logger(self, name="main", level=None):
        """Get or create a logger with the specified name and level."""
        if name in self.loggers:
            return self.loggers[name]
            
        # Determine log level
        if level is None:
            level = self.get_log_level_from_env()
            
        logger = logging.getLogger(f"{self.app_name}.{name}")
        logger.setLevel(level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler (only for WARNING and above in production)
        console_handler = logging.StreamHandler(sys.stdout)
        if self.is_production():
            console_handler.setLevel(logging.WARNING)
        else:
            console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # File handler for all logs
        log_file = os.path.join(self.log_dir, f"{name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error file handler for errors only
        error_file = os.path.join(self.log_dir, f"{name}_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        # Performance log handler for timing information
        if name == "performance":
            perf_file = os.path.join(self.log_dir, "performance.log")
            perf_handler = logging.handlers.RotatingFileHandler(
                perf_file, maxBytes=5*1024*1024, backupCount=2
            )
            perf_handler.setLevel(logging.INFO)
            perf_formatter = logging.Formatter(
                '%(asctime)s - %(message)s'
            )
            perf_handler.setFormatter(perf_formatter)
            logger.addHandler(perf_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_log_level_from_env(self):
        """Get log level from environment variable."""
        level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str, logging.INFO)
    
    def is_production(self):
        """Check if running in production environment."""
        return os.environ.get('FLASK_ENV', 'development').lower() == 'production'
    
    def set_debug_mode(self, enabled=True):
        """Enable or disable debug mode for all loggers."""
        level = logging.DEBUG if enabled else logging.INFO
        for logger in self.loggers.values():
            logger.setLevel(level)
            # Update console handler level
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    handler.setLevel(logging.DEBUG if enabled else logging.WARNING)

class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, logger, operation_name):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.2f}s: {exc_val}")

# Global logger instance
torwar_logger = TorWARLogger()

# Convenience functions
def get_logger(name="main", level=None):
    """Get a logger instance."""
    return torwar_logger.get_logger(name, level)

def get_performance_logger():
    """Get performance logger."""
    return torwar_logger.get_logger("performance")

def time_operation(operation_name, logger=None):
    """Decorator or context manager for timing operations."""
    if logger is None:
        logger = get_performance_logger()
    return PerformanceTimer(logger, operation_name)

def set_debug_mode(enabled=True):
    """Enable or disable debug mode."""
    torwar_logger.set_debug_mode(enabled)

# Logging decorators
def log_function_call(logger=None):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if logger is None:
                func_logger = get_logger("functions")
            else:
                func_logger = logger
                
            func_logger.debug(f"Calling {func.__name__} with args={len(args)}, kwargs={list(kwargs.keys())}")
            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"Successfully completed {func.__name__}")
                return result
            except Exception as e:
                func_logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

def log_performance(operation_name=None, logger=None):
    """Decorator to log function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if logger is None:
                perf_logger = get_performance_logger()
            else:
                perf_logger = logger
                
            op_name = operation_name or func.__name__
            with time_operation(op_name, perf_logger):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Initialize logging on import
def initialize_logging():
    """Initialize logging system."""
    # Set up root logger to prevent other libraries from being too verbose
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    
    # Suppress noisy third-party loggers
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Create main application logger
    app_logger = get_logger("main")
    app_logger.info("TorWAR logging system initialized")
    
    return app_logger

# Auto-initialize when module is imported
main_logger = initialize_logging()
