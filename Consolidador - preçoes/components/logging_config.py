"""
Centralized logging configuration for the Price Monitoring System.
Provides structured logging with rotating file handlers and environment-based configuration.
"""
import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class LoggingConfig:
    """
    Centralized logging configuration manager.
    """
    
    # Default configuration
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_LOG_DIR = "logs"
    
    # Log levels mapping
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, 
                 log_dir: str = None,
                 log_level: str = None,
                 log_format: str = None,
                 date_format: str = None,
                 max_bytes: int = None,
                 backup_count: int = None,
                 console_enabled: bool = True,
                 file_enabled: bool = True):
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Log message format
            date_format: Date format for log messages
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_enabled: Enable console logging
            file_enabled: Enable file logging
        """
        # Get configuration from environment variables or use defaults
        self.log_dir = log_dir or os.getenv('PRICE_MONITOR_LOG_DIR', self.DEFAULT_LOG_DIR)
        self.log_level = log_level or os.getenv('PRICE_MONITOR_LOG_LEVEL', self.DEFAULT_LOG_LEVEL)
        self.log_format = log_format or os.getenv('PRICE_MONITOR_LOG_FORMAT', self.DEFAULT_LOG_FORMAT)
        self.date_format = date_format or os.getenv('PRICE_MONITOR_DATE_FORMAT', self.DEFAULT_DATE_FORMAT)
        self.max_bytes = max_bytes or int(os.getenv('PRICE_MONITOR_LOG_MAX_BYTES', str(self.DEFAULT_MAX_BYTES)))
        self.backup_count = backup_count or int(os.getenv('PRICE_MONITOR_LOG_BACKUP_COUNT', str(self.DEFAULT_BACKUP_COUNT)))
        self.console_enabled = console_enabled and os.getenv('PRICE_MONITOR_CONSOLE_LOG', 'true').lower() == 'true'
        self.file_enabled = file_enabled and os.getenv('PRICE_MONITOR_FILE_LOG', 'true').lower() == 'true'
        
        # Validate log level
        if self.log_level.upper() not in self.LOG_LEVELS:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of: {list(self.LOG_LEVELS.keys())}")
        
        # Create log directory
        self.log_dir_path = Path(self.log_dir)
        self.log_dir_path.mkdir(exist_ok=True)
        
        # Log file paths
        self.main_log_file = self.log_dir_path / "price_monitor.log"
        self.error_log_file = self.log_dir_path / "error.log"
        self.performance_log_file = self.log_dir_path / "performance.log"
        
        # Track if logging has been configured
        self._configured = False
    
    def configure_logging(self) -> None:
        """
        Configure the logging system with structured handlers.
        """
        if self._configured:
            return
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root logger level
        root_logger.setLevel(self.LOG_LEVELS[self.log_level.upper()])
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt=self.log_format,
            datefmt=self.date_format
        )
        
        simple_formatter = logging.Formatter(
            fmt="%(levelname)s - %(name)s - %(message)s"
        )
        
        handlers = []
        
        # Configure file handlers
        if self.file_enabled:
            # Main log file (all messages)
            main_handler = logging.handlers.RotatingFileHandler(
                filename=self.main_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            main_handler.setLevel(logging.DEBUG)
            main_handler.setFormatter(detailed_formatter)
            handlers.append(main_handler)
            
            # Error log file (ERROR and CRITICAL only)
            error_handler = logging.handlers.RotatingFileHandler(
                filename=self.error_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            handlers.append(error_handler)
            
            # Performance log file (for performance-related logs)
            performance_handler = logging.handlers.RotatingFileHandler(
                filename=self.performance_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            performance_handler.setLevel(logging.INFO)
            performance_handler.setFormatter(detailed_formatter)
            
            # Add filter to only log performance-related messages
            performance_handler.addFilter(self._performance_filter)
            handlers.append(performance_handler)
        
        # Configure console handler
        if self.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.LOG_LEVELS[self.log_level.upper()])
            
            # Use simple format for console in production, detailed in debug
            if self.log_level.upper() == 'DEBUG':
                console_handler.setFormatter(detailed_formatter)
            else:
                console_handler.setFormatter(simple_formatter)
            
            handlers.append(console_handler)
        
        # Add all handlers to root logger
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Log configuration info
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured - Level: {self.log_level}, "
                   f"File: {self.file_enabled}, Console: {self.console_enabled}")
        logger.info(f"Log directory: {self.log_dir_path.absolute()}")
        
        self._configured = True
    
    def _performance_filter(self, record: logging.LogRecord) -> bool:
        """
        Filter for performance-related log messages.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be logged to performance file
        """
        # Log messages from performance monitor or containing performance keywords
        performance_keywords = ['performance', 'timing', 'execution_time', 'metrics', 'benchmark']
        
        return (
            'performance' in record.name.lower() or
            any(keyword in record.getMessage().lower() for keyword in performance_keywords)
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger with the specified name.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        if not self._configured:
            self.configure_logging()
        
        return logging.getLogger(name)
    
    def get_performance_logger(self, name: str) -> logging.Logger:
        """
        Get a logger specifically for performance metrics.
        
        Args:
            name: Logger name
            
        Returns:
            Logger configured for performance logging
        """
        logger = self.get_logger(f"performance.{name}")
        return logger
    
    def log_startup_info(self, config_info: Dict[str, Any]) -> None:
        """
        Log application startup information.
        
        Args:
            config_info: Dictionary containing configuration information
        """
        logger = self.get_logger("startup")
        
        logger.info("=" * 50)
        logger.info("Price Monitoring System Starting")
        logger.info("=" * 50)
        logger.info(f"Startup time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Python version: {config_info.get('python_version', 'Unknown')}")
        logger.info(f"Working directory: {config_info.get('working_directory', 'Unknown')}")
        
        # Log configuration
        logger.info("Configuration:")
        for key, value in config_info.items():
            if 'password' not in key.lower() and 'secret' not in key.lower():
                logger.info(f"  {key}: {value}")
        
        logger.info("=" * 50)
    
    def log_shutdown_info(self, shutdown_reason: str = "Normal shutdown") -> None:
        """
        Log application shutdown information.
        
        Args:
            shutdown_reason: Reason for shutdown
        """
        logger = self.get_logger("shutdown")
        
        logger.info("=" * 50)
        logger.info("Price Monitoring System Shutting Down")
        logger.info("=" * 50)
        logger.info(f"Shutdown time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Shutdown reason: {shutdown_reason}")
        logger.info("=" * 50)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about log files.
        
        Returns:
            Dictionary containing log file statistics
        """
        stats = {}
        
        log_files = [
            ("main", self.main_log_file),
            ("error", self.error_log_file),
            ("performance", self.performance_log_file)
        ]
        
        for name, log_file in log_files:
            if log_file.exists():
                stat = log_file.stat()
                stats[name] = {
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                stats[name] = {
                    "size_bytes": 0,
                    "size_mb": 0,
                    "modified": "Not created"
                }
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clean up old log files beyond the rotation count.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of files cleaned up
        """
        logger = self.get_logger(__name__)
        cleaned_count = 0
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            # Find old log files
            for log_file in self.log_dir_path.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    try:
                        log_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old log file: {log_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up log file {log_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old log files")
            
        except Exception as e:
            logger.error(f"Error during log cleanup: {e}")
        
        return cleaned_count


# Global logging configuration instance
_logging_config: Optional[LoggingConfig] = None


def get_logging_config(**kwargs) -> LoggingConfig:
    """
    Get the global logging configuration instance.
    
    Args:
        **kwargs: Configuration parameters for LoggingConfig
        
    Returns:
        LoggingConfig instance
    """
    global _logging_config
    
    if _logging_config is None:
        _logging_config = LoggingConfig(**kwargs)
    
    return _logging_config


def setup_logging(**kwargs) -> None:
    """
    Setup logging for the entire application.
    
    Args:
        **kwargs: Configuration parameters for LoggingConfig
    """
    config = get_logging_config(**kwargs)
    config.configure_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name using the global configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    config = get_logging_config()
    return config.get_logger(name)


def get_performance_logger(name: str) -> logging.Logger:
    """
    Get a performance logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Performance logger instance
    """
    config = get_logging_config()
    return config.get_performance_logger(name)