"""
Tests for the logging configuration module.
"""
import os
import tempfile
import shutil
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from components.logging_config import LoggingConfig, get_logging_config, setup_logging, get_logger


class TestLoggingConfig:
    """Test cases for LoggingConfig class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        
        # Clear any existing global config
        import components.logging_config
        components.logging_config._logging_config = None
    
    def teardown_method(self):
        """Cleanup test environment."""
        # Clear logging handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Remove temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clear global config
        import components.logging_config
        components.logging_config._logging_config = None
    
    def test_default_configuration(self):
        """Test default logging configuration."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        assert config.log_level == "INFO"
        assert config.log_format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.max_bytes == 10 * 1024 * 1024
        assert config.backup_count == 5
        assert config.console_enabled is True
        assert config.file_enabled is True
    
    def test_environment_variable_configuration(self):
        """Test configuration from environment variables."""
        env_vars = {
            'PRICE_MONITOR_LOG_LEVEL': 'DEBUG',
            'PRICE_MONITOR_LOG_FORMAT': '%(name)s - %(message)s',
            'PRICE_MONITOR_LOG_MAX_BYTES': '5242880',  # 5MB
            'PRICE_MONITOR_LOG_BACKUP_COUNT': '3',
            'PRICE_MONITOR_CONSOLE_LOG': 'false',
            'PRICE_MONITOR_FILE_LOG': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            config = LoggingConfig(log_dir=str(self.log_dir))
            
            assert config.log_level == "DEBUG"
            assert config.log_format == "%(name)s - %(message)s"
            assert config.max_bytes == 5242880
            assert config.backup_count == 3
            assert config.console_enabled is False
            assert config.file_enabled is True
    
    def test_invalid_log_level(self):
        """Test invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level"):
            LoggingConfig(log_dir=str(self.log_dir), log_level="INVALID")
    
    def test_log_directory_creation(self):
        """Test that log directory is created."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        assert self.log_dir.exists()
        assert self.log_dir.is_dir()
    
    def test_configure_logging_file_handlers(self):
        """Test file handler configuration."""
        config = LoggingConfig(
            log_dir=str(self.log_dir),
            log_level="DEBUG",
            console_enabled=False,
            file_enabled=True
        )
        
        config.configure_logging()
        
        # Check that log files are created when logging occurs
        logger = logging.getLogger("test")
        logger.info("Test message")
        logger.error("Test error")
        
        # Check main log file
        assert config.main_log_file.exists()
        
        # Check error log file
        assert config.error_log_file.exists()
        
        # Verify log content
        main_content = config.main_log_file.read_text()
        assert "Test message" in main_content
        assert "Test error" in main_content
        
        error_content = config.error_log_file.read_text()
        assert "Test error" in error_content
        assert "Test message" not in error_content  # Only errors in error log
    
    def test_configure_logging_console_handler(self):
        """Test console handler configuration."""
        config = LoggingConfig(
            log_dir=str(self.log_dir),
            log_level="INFO",
            console_enabled=True,
            file_enabled=False
        )
        
        config.configure_logging()
        
        # Check that console handler is added
        root_logger = logging.getLogger()
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0
    
    def test_performance_filter(self):
        """Test performance log filtering."""
        config = LoggingConfig(
            log_dir=str(self.log_dir),
            log_level="DEBUG",
            console_enabled=False,
            file_enabled=True
        )
        
        config.configure_logging()
        
        # Test performance-related logs
        perf_logger = logging.getLogger("performance.test")
        perf_logger.info("Performance metrics: execution_time=1.5s")
        
        regular_logger = logging.getLogger("regular.test")
        regular_logger.info("Regular log message")
        
        # Check performance log file
        if config.performance_log_file.exists():
            perf_content = config.performance_log_file.read_text()
            assert "Performance metrics" in perf_content
    
    def test_get_logger(self):
        """Test logger retrieval."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        logger = config.get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        assert config._configured is True
    
    def test_get_performance_logger(self):
        """Test performance logger retrieval."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        logger = config.get_performance_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "performance.test.module"
    
    def test_log_startup_info(self):
        """Test startup information logging."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        config.configure_logging()
        
        config_info = {
            "python_version": "3.11.0",
            "working_directory": "/test/dir",
            "database_path": "test.db",
            "password": "secret123"  # Should be filtered out
        }
        
        config.log_startup_info(config_info)
        
        # Check that startup info was logged
        main_content = config.main_log_file.read_text()
        assert "Price Monitoring System Starting" in main_content
        assert "python_version: 3.11.0" in main_content
        assert "database_path: test.db" in main_content
        assert "secret123" not in main_content  # Password should be filtered
    
    def test_log_shutdown_info(self):
        """Test shutdown information logging."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        config.configure_logging()
        
        config.log_shutdown_info("User requested shutdown")
        
        # Check that shutdown info was logged
        main_content = config.main_log_file.read_text()
        assert "Price Monitoring System Shutting Down" in main_content
        assert "User requested shutdown" in main_content
    
    def test_get_log_stats(self):
        """Test log file statistics."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        config.configure_logging()
        
        # Generate some log content
        logger = logging.getLogger("test")
        logger.info("Test message")
        logger.error("Test error")
        
        stats = config.get_log_stats()
        
        assert "main" in stats
        assert "error" in stats
        assert "performance" in stats
        
        # Check that main log has content
        assert stats["main"]["size_bytes"] > 0
        assert stats["main"]["size_mb"] > 0
        assert "modified" in stats["main"]
    
    def test_cleanup_old_logs(self):
        """Test old log file cleanup."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        # Create some old log files
        old_log = self.log_dir / "old.log.1"
        old_log.parent.mkdir(exist_ok=True)
        old_log.write_text("old log content")
        
        # Set modification time to 31 days ago
        import time
        old_time = time.time() - (31 * 24 * 3600)
        os.utime(old_log, (old_time, old_time))
        
        # Create recent log file
        recent_log = self.log_dir / "recent.log"
        recent_log.write_text("recent log content")
        
        config.configure_logging()
        cleaned_count = config.cleanup_old_logs(days_to_keep=30)
        
        assert cleaned_count == 1
        assert not old_log.exists()
        assert recent_log.exists()
    
    def test_multiple_configure_calls(self):
        """Test that multiple configure calls don't duplicate handlers."""
        config = LoggingConfig(log_dir=str(self.log_dir))
        
        config.configure_logging()
        initial_handler_count = len(logging.getLogger().handlers)
        
        config.configure_logging()
        final_handler_count = len(logging.getLogger().handlers)
        
        assert initial_handler_count == final_handler_count


class TestGlobalFunctions:
    """Test cases for global logging functions."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        
        # Clear any existing global config
        import components.logging_config
        components.logging_config._logging_config = None
    
    def teardown_method(self):
        """Cleanup test environment."""
        # Clear logging handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Remove temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clear global config
        import components.logging_config
        components.logging_config._logging_config = None
    
    def test_get_logging_config_singleton(self):
        """Test that get_logging_config returns singleton instance."""
        config1 = get_logging_config(log_dir=str(self.log_dir))
        config2 = get_logging_config(log_dir="different_dir")  # Should be ignored
        
        assert config1 is config2
        assert config1.log_dir == str(self.log_dir)  # First call parameters used
    
    def test_setup_logging(self):
        """Test setup_logging function."""
        setup_logging(log_dir=str(self.log_dir), log_level="DEBUG")
        
        # Check that logging is configured
        logger = logging.getLogger("test")
        logger.info("Test message")
        
        # Check that log file is created
        log_file = self.log_dir / "price_monitor.log"
        assert log_file.exists()
    
    def test_get_logger_function(self):
        """Test get_logger function."""
        setup_logging(log_dir=str(self.log_dir))
        
        logger = get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
    
    def test_logging_with_different_levels(self):
        """Test logging with different log levels."""
        setup_logging(log_dir=str(self.log_dir), log_level="WARNING")
        
        logger = get_logger("test")
        logger.debug("Debug message")  # Should not appear
        logger.info("Info message")    # Should not appear
        logger.warning("Warning message")  # Should appear
        logger.error("Error message")      # Should appear
        
        log_file = self.log_dir / "price_monitor.log"
        content = log_file.read_text()
        
        assert "Debug message" not in content
        assert "Info message" not in content
        assert "Warning message" in content
        assert "Error message" in content


if __name__ == "__main__":
    pytest.main([__file__])