"""
Integration tests for the main application entry point.
Tests the complete application flow and component integration.
"""
import os
import sys
import tempfile
import json
import sqlite3
import subprocess
import time
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from threading import Thread

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import PriceMonitoringApp, create_argument_parser, main
from models.data_models import SystemConfig, ProductConfig


class TestPriceMonitoringApp:
    """Test cases for PriceMonitoringApp class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.products_config_path = os.path.join(self.temp_dir, "test_produtos.json")
        self.system_config_path = os.path.join(self.temp_dir, "test_config.json")
        self.db_path = os.path.join(self.temp_dir, "test_precos.db")
        
        # Create test configuration files
        self._create_test_configs()
        
        # Initialize app
        self.app = PriceMonitoringApp(
            config_path=self.products_config_path,
            system_config_path=self.system_config_path
        )
    
    def teardown_method(self):
        """Cleanup after tests."""
        # Cleanup app
        if self.app:
            self.app.cleanup()
        
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Products configuration
        products_config = {
            "produtos": [
                {
                    "nome": "Test Product 1",
                    "url": "https://example.com/product1",
                    "preco_alvo": 100.0,
                    "ativo": True,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                },
                {
                    "nome": "Test Product 2",
                    "url": "https://example.com/product2",
                    "preco_alvo": 200.0,
                    "ativo": False,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                }
            ]
        }
        
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(products_config, f, indent=2, ensure_ascii=False)
        
        # System configuration
        system_config = {
            "intervalo_execucao": 60,
            "timeout_requisicao": 10,
            "max_retries": 3,
            "log_level": "INFO",
            "email_enabled": False,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "db_path": self.db_path
        }
        
        with open(self.system_config_path, 'w', encoding='utf-8') as f:
            json.dump(system_config, f, indent=2, ensure_ascii=False)
    
    def test_app_initialization(self):
        """Test application initialization."""
        assert self.app.config_path == self.products_config_path
        assert self.app.system_config_path == self.system_config_path
        assert not self.app.running
        assert self.app.config_manager is None
        assert self.app.system_config is None
    
    def test_setup_logging(self):
        """Test logging setup."""
        self.app.setup_logging(log_level="DEBUG")
        
        assert self.app.logger is not None
        assert self.app.logger.level <= 10  # DEBUG level
    
    def test_initialize_components(self):
        """Test component initialization."""
        # Setup logging first
        self.app.setup_logging()
        
        # Initialize components
        result = self.app.initialize_components()
        
        assert result is True
        assert self.app.config_manager is not None
        assert self.app.system_config is not None
        assert self.app.database_manager is not None
        assert self.app.web_scraper is not None
        assert self.app.notification_service is not None
        assert self.app.price_monitor is not None
        assert self.app.task_scheduler is not None
        
        # Check that database was created
        assert os.path.exists(self.db_path)
    
    @patch('services.web_scraper.WebScraper.scrape_product')
    def test_run_once(self, mock_scrape):
        """Test one-time monitoring execution."""
        # Setup mock scraping result
        from services.web_scraper import ScrapingResult
        mock_scrape.return_value = ScrapingResult(
            success=True,
            price=95.0,
            product_name="Test Product 1",
            url="https://example.com/product1"
        )
        
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Run once
        result = self.app.run_once()
        
        assert result is True
        
        # Check that scraping was called for active products only
        assert mock_scrape.call_count == 1  # Only one active product
        
        # Check database for stored records
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM precos")
        record_count = cursor.fetchone()[0]
        conn.close()
        
        assert record_count == 1
    
    @patch('services.web_scraper.WebScraper.scrape_product')
    def test_run_once_with_errors(self, mock_scrape):
        """Test one-time monitoring with scraping errors."""
        # Setup mock scraping result with error
        from services.web_scraper import ScrapingResult
        mock_scrape.return_value = ScrapingResult(
            success=False,
            error_message="Connection timeout"
        )
        
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Run once
        result = self.app.run_once()
        
        assert result is False  # Should return False due to scraping failure
    
    def test_setup_monitoring_task(self):
        """Test monitoring task setup."""
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Setup monitoring task
        result = self.app.setup_monitoring_task()
        
        assert result is True
        
        # Check that task was added to scheduler
        task_status = self.app.task_scheduler.get_task_status("price_monitoring")
        assert task_status is not None
        assert task_status['enabled'] is True
        assert task_status['interval'] == 60  # From test config
    
    @patch('services.web_scraper.WebScraper.scrape_product')
    def test_daemon_mode_startup_shutdown(self, mock_scrape):
        """Test daemon mode startup and shutdown."""
        # Setup mock scraping result
        from services.web_scraper import ScrapingResult
        mock_scrape.return_value = ScrapingResult(
            success=True,
            price=95.0,
            product_name="Test Product 1",
            url="https://example.com/product1"
        )
        
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Start daemon in a separate thread
        daemon_thread = Thread(target=self.app.run_daemon)
        daemon_thread.daemon = True
        daemon_thread.start()
        
        # Wait for daemon to start
        time.sleep(1.0)
        
        assert self.app.running is True
        assert self.app.task_scheduler.is_running() is True
        
        # Request shutdown
        self.app._shutdown_requested = True
        
        # Wait for daemon to stop
        daemon_thread.join(timeout=5.0)
        
        assert self.app.running is False
    
    def test_show_status(self, capsys):
        """Test status display."""
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Show status
        self.app.show_status()
        
        # Check output
        captured = capsys.readouterr()
        assert "Price Monitoring System Status" in captured.out
        assert "System Configuration" in captured.out
        assert "Products Configuration" in captured.out
        assert "Total products: 2" in captured.out
        assert "Active products: 1" in captured.out
    
    def test_cleanup(self):
        """Test application cleanup."""
        # Setup app
        self.app.setup_logging()
        self.app.initialize_components()
        
        # Start scheduler
        self.app.task_scheduler.start()
        
        # Cleanup
        self.app.cleanup()
        
        # Check that scheduler was stopped
        assert not self.app.task_scheduler.is_running()


class TestArgumentParser:
    """Test cases for command line argument parsing."""
    
    def test_create_argument_parser(self):
        """Test argument parser creation."""
        parser = create_argument_parser()
        
        assert parser is not None
        assert parser.description is not None
    
    def test_parse_once_mode(self):
        """Test parsing once mode arguments."""
        parser = create_argument_parser()
        args = parser.parse_args(['--once'])
        
        assert args.once is True
        assert args.daemon is False
        assert args.status is False
        assert args.config == 'produtos.json'
        assert args.log_level == 'INFO'
    
    def test_parse_daemon_mode(self):
        """Test parsing daemon mode arguments."""
        parser = create_argument_parser()
        args = parser.parse_args(['--daemon'])
        
        assert args.once is False
        assert args.daemon is True
        assert args.status is False
    
    def test_parse_status_mode(self):
        """Test parsing status mode arguments."""
        parser = create_argument_parser()
        args = parser.parse_args(['--status'])
        
        assert args.once is False
        assert args.daemon is False
        assert args.status is True
    
    def test_parse_with_custom_config(self):
        """Test parsing with custom configuration files."""
        parser = create_argument_parser()
        args = parser.parse_args([
            '--once',
            '--config', 'custom_produtos.json',
            '--system-config', 'custom_config.json'
        ])
        
        assert args.config == 'custom_produtos.json'
        assert args.system_config == 'custom_config.json'
    
    def test_parse_with_log_level(self):
        """Test parsing with custom log level."""
        parser = create_argument_parser()
        args = parser.parse_args(['--once', '--log-level', 'DEBUG'])
        
        assert args.log_level == 'DEBUG'
    
    def test_parse_mutually_exclusive_modes(self):
        """Test that execution modes are mutually exclusive."""
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--once', '--daemon'])
    
    def test_parse_no_mode_specified(self):
        """Test that at least one execution mode is required."""
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestMainFunction:
    """Test cases for the main function."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.products_config_path = os.path.join(self.temp_dir, "test_produtos.json")
        self.system_config_path = os.path.join(self.temp_dir, "test_config.json")
        self.db_path = os.path.join(self.temp_dir, "test_precos.db")
        
        # Create test configuration files
        self._create_test_configs()
    
    def teardown_method(self):
        """Cleanup after tests."""
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_configs(self):
        """Create test configuration files."""
        # Products configuration
        products_config = {
            "produtos": [
                {
                    "nome": "Test Product",
                    "url": "https://example.com/product",
                    "preco_alvo": 100.0,
                    "ativo": True,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                }
            ]
        }
        
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(products_config, f, indent=2, ensure_ascii=False)
        
        # System configuration
        system_config = {
            "intervalo_execucao": 60,
            "timeout_requisicao": 10,
            "max_retries": 3,
            "log_level": "INFO",
            "email_enabled": False,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "db_path": self.db_path
        }
        
        with open(self.system_config_path, 'w', encoding='utf-8') as f:
            json.dump(system_config, f, indent=2, ensure_ascii=False)
    
    @patch('sys.argv')
    @patch('services.web_scraper.WebScraper.scrape_product')
    def test_main_once_mode(self, mock_scrape, mock_argv):
        """Test main function in once mode."""
        # Setup mock arguments
        mock_argv.__getitem__.side_effect = lambda i: [
            'main.py', '--once', 
            '--config', self.products_config_path,
            '--system-config', self.system_config_path
        ][i]
        mock_argv.__len__.return_value = 5
        
        # Setup mock scraping result
        from services.web_scraper import ScrapingResult
        mock_scrape.return_value = ScrapingResult(
            success=True,
            price=95.0,
            product_name="Test Product",
            url="https://example.com/product"
        )
        
        # Run main function
        with patch('sys.argv', [
            'main.py', '--once',
            '--config', self.products_config_path,
            '--system-config', self.system_config_path
        ]):
            exit_code = main()
        
        assert exit_code == 0
    
    @patch('sys.argv')
    def test_main_status_mode(self, mock_argv):
        """Test main function in status mode."""
        # Run main function
        with patch('sys.argv', [
            'main.py', '--status',
            '--config', self.products_config_path,
            '--system-config', self.system_config_path
        ]):
            exit_code = main()
        
        assert exit_code == 0
    
    def test_main_with_invalid_config(self):
        """Test main function with invalid configuration."""
        with patch('sys.argv', [
            'main.py', '--once',
            '--config', 'non_existent.json'
        ]):
            exit_code = main()
        
        assert exit_code == 1
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_main_keyboard_interrupt(self, mock_input):
        """Test main function handling keyboard interrupt."""
        with patch('sys.argv', [
            'main.py', '--once',
            '--config', self.products_config_path,
            '--system-config', self.system_config_path
        ]):
            exit_code = main()
        
        assert exit_code == 130  # Standard exit code for Ctrl+C


class TestIntegrationScenarios:
    """Integration test scenarios for complete workflows."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.products_config_path = os.path.join(self.temp_dir, "integration_produtos.json")
        self.system_config_path = os.path.join(self.temp_dir, "integration_config.json")
        self.db_path = os.path.join(self.temp_dir, "integration_precos.db")
        
        # Create test configuration files
        self._create_integration_configs()
    
    def teardown_method(self):
        """Cleanup after tests."""
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_integration_configs(self):
        """Create integration test configuration files."""
        # Products configuration with multiple products
        products_config = {
            "produtos": [
                {
                    "nome": "Product Below Target",
                    "url": "https://example.com/product1",
                    "preco_alvo": 150.0,
                    "ativo": True,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                },
                {
                    "nome": "Product Above Target",
                    "url": "https://example.com/product2",
                    "preco_alvo": 50.0,
                    "ativo": True,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                },
                {
                    "nome": "Inactive Product",
                    "url": "https://example.com/product3",
                    "preco_alvo": 100.0,
                    "ativo": False,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                }
            ]
        }
        
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(products_config, f, indent=2, ensure_ascii=False)
        
        # System configuration
        system_config = {
            "intervalo_execucao": 60,  # Minimum valid interval
            "timeout_requisicao": 10,
            "max_retries": 2,
            "log_level": "DEBUG",
            "email_enabled": False,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "db_path": self.db_path
        }
        
        with open(self.system_config_path, 'w', encoding='utf-8') as f:
            json.dump(system_config, f, indent=2, ensure_ascii=False)
    
    @patch('services.web_scraper.WebScraper.scrape_product')
    @patch('services.notification_service.NotificationService.send_price_alert')
    def test_complete_monitoring_workflow_with_alerts(self, mock_send_alert, mock_scrape):
        """Test complete monitoring workflow with price alerts."""
        # Setup mock scraping results
        from services.web_scraper import ScrapingResult
        
        def scrape_side_effect(url, selectors=None):
            if "product1" in url:
                return ScrapingResult(
                    success=True,
                    price=120.0,  # Below target of 150.0
                    product_name="Product Below Target",
                    url=url
                )
            elif "product2" in url:
                return ScrapingResult(
                    success=True,
                    price=80.0,  # Above target of 50.0
                    product_name="Product Above Target",
                    url=url
                )
            else:
                return ScrapingResult(success=False, error_message="Product not found")
        
        mock_scrape.side_effect = scrape_side_effect
        
        # Initialize app
        app = PriceMonitoringApp(
            config_path=self.products_config_path,
            system_config_path=self.system_config_path
        )
        
        try:
            # Setup and run
            app.setup_logging()
            app.initialize_components()
            result = app.run_once()
            
            assert result is True
            
            # Check that scraping was called for active products only (2 calls)
            assert mock_scrape.call_count == 2
            
            # Check that alert was sent for product below target
            assert mock_send_alert.call_count == 1
            
            # Verify database records
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT nome_produto, preco FROM precos ORDER BY nome_produto")
            records = cursor.fetchall()
            conn.close()
            
            assert len(records) == 2
            assert records[0][0] == "Product Above Target"
            assert records[0][1] == 80.0
            assert records[1][0] == "Product Below Target"
            assert records[1][1] == 120.0
            
        finally:
            app.cleanup()
    
    @patch('services.web_scraper.WebScraper.scrape_product')
    def test_error_handling_and_recovery(self, mock_scrape):
        """Test error handling and recovery scenarios."""
        # Setup mock scraping results with mixed success/failure
        from services.web_scraper import ScrapingResult
        
        call_count = 0
        def scrape_side_effect(url, selectors=None):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call fails
                return ScrapingResult(success=False, error_message="Network timeout")
            else:
                # Second call succeeds
                return ScrapingResult(
                    success=True,
                    price=100.0,
                    product_name="Product Above Target",
                    url=url
                )
        
        mock_scrape.side_effect = scrape_side_effect
        
        # Initialize app
        app = PriceMonitoringApp(
            config_path=self.products_config_path,
            system_config_path=self.system_config_path
        )
        
        try:
            # Setup and run
            app.setup_logging()
            app.initialize_components()
            result = app.run_once()
            
            # Should return False due to failures
            assert result is False
            
            # Check that both products were attempted
            assert mock_scrape.call_count == 2
            
            # Verify database has one successful record and one failed record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM precos WHERE status = 'active'")
            active_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM precos WHERE status = 'failed'")
            failed_count = cursor.fetchone()[0]
            conn.close()
            
            assert active_count == 1  # One successful scrape
            assert failed_count == 1  # One failed scrape
            
        finally:
            app.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])