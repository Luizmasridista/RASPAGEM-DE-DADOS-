"""
Unit tests for the PriceMonitor class.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import time
from datetime import datetime
from typing import List

from models.data_models import ProductConfig, PriceRecord, ProductResult, MonitoringResult
from services.price_monitor import PriceMonitor
from services.web_scraper import ScrapingResult


class TestPriceMonitor(unittest.TestCase):
    """Test cases for PriceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_scraper = Mock()
        self.mock_database = Mock()
        self.mock_notifier = Mock()
        
        # Create PriceMonitor instance
        self.price_monitor = PriceMonitor(
            scraper=self.mock_scraper,
            database=self.mock_database,
            notifier=self.mock_notifier,
            max_workers=2
        )
        
        # Sample product configurations
        self.sample_products = [
            ProductConfig(
                nome="Produto Teste 1",
                url="https://example.com/produto1",
                preco_alvo=100.0,
                ativo=True
            ),
            ProductConfig(
                nome="Produto Teste 2",
                url="https://example.com/produto2",
                preco_alvo=200.0,
                ativo=True
            ),
            ProductConfig(
                nome="Produto Inativo",
                url="https://example.com/produto3",
                preco_alvo=150.0,
                ativo=False
            )
        ]
    
    def test_init(self):
        """Test PriceMonitor initialization."""
        self.assertEqual(self.price_monitor.scraper, self.mock_scraper)
        self.assertEqual(self.price_monitor.database, self.mock_database)
        self.assertEqual(self.price_monitor.notifier, self.mock_notifier)
        self.assertEqual(self.price_monitor.max_workers, 2)
        self.assertEqual(self.price_monitor.total_executions, 0)
    
    def test_check_price_alerts_should_alert(self):
        """Test price alert check when alert should be triggered."""
        # Current price is below target
        result = self.price_monitor.check_price_alerts(90.0, 100.0)
        self.assertTrue(result)
        
        # Current price equals target
        result = self.price_monitor.check_price_alerts(100.0, 100.0)
        self.assertTrue(result)
    
    def test_check_price_alerts_should_not_alert(self):
        """Test price alert check when alert should not be triggered."""
        # Current price is above target
        result = self.price_monitor.check_price_alerts(110.0, 100.0)
        self.assertFalse(result)
    
    def test_check_price_alerts_invalid_prices(self):
        """Test price alert check with invalid prices."""
        # Zero prices
        result = self.price_monitor.check_price_alerts(0.0, 100.0)
        self.assertFalse(result)
        
        result = self.price_monitor.check_price_alerts(100.0, 0.0)
        self.assertFalse(result)
        
        # Negative prices
        result = self.price_monitor.check_price_alerts(-10.0, 100.0)
        self.assertFalse(result)
    
    def test_monitor_single_product_success_no_alert(self):
        """Test successful monitoring of single product without alert."""
        product = self.sample_products[0]
        
        # Mock successful scraping (price above target)
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=True,
            product_name="Produto Teste 1",
            price=120.0,
            url=product.url
        )
        
        # Execute monitoring
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result
        self.assertTrue(result.sucesso)
        self.assertEqual(result.produto, product)
        self.assertEqual(result.preco_atual, 120.0)
        self.assertFalse(result.alerta_enviado)
        self.assertIsNone(result.erro)
        self.assertGreaterEqual(result.tempo_execucao, 0)
        
        # Verify database was called
        self.mock_database.insert_price_record.assert_called_once()
        
        # Verify no alert was sent
        self.mock_notifier.send_price_alert.assert_not_called()
    
    def test_monitor_single_product_success_with_alert(self):
        """Test successful monitoring of single product with alert."""
        product = self.sample_products[0]
        
        # Mock successful scraping (price below target)
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=True,
            product_name="Produto Teste 1",
            price=90.0,
            url=product.url
        )
        
        # Execute monitoring
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result
        self.assertTrue(result.sucesso)
        self.assertEqual(result.produto, product)
        self.assertEqual(result.preco_atual, 90.0)
        self.assertTrue(result.alerta_enviado)
        self.assertIsNone(result.erro)
        
        # Verify database was called
        self.mock_database.insert_price_record.assert_called_once()
        
        # Verify alert was sent
        self.mock_notifier.send_price_alert.assert_called_once_with(product, 90.0)
    
    def test_monitor_single_product_scraping_failure(self):
        """Test monitoring single product when scraping fails."""
        product = self.sample_products[0]
        
        # Mock failed scraping
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=False,
            url=product.url,
            error_message="Network timeout"
        )
        
        # Execute monitoring
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result
        self.assertFalse(result.sucesso)
        self.assertEqual(result.produto, product)
        self.assertIsNone(result.preco_atual)
        self.assertFalse(result.alerta_enviado)
        self.assertIn("Network timeout", result.erro)
        
        # Verify failed record was stored
        self.mock_database.insert_price_record.assert_called_once()
        stored_record = self.mock_database.insert_price_record.call_args[0][0]
        self.assertEqual(stored_record.status, "failed")
        self.assertEqual(stored_record.preco, 0.0)
    
    def test_monitor_single_product_inactive_product(self):
        """Test monitoring inactive product."""
        product = self.sample_products[2]  # Inactive product
        
        # Execute monitoring
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result
        self.assertFalse(result.sucesso)
        self.assertEqual(result.produto, product)
        self.assertIn("not active", result.erro)
        
        # Verify scraper was not called
        self.mock_scraper.scrape_product.assert_not_called()
    
    def test_monitor_single_product_invalid_price(self):
        """Test monitoring when invalid price is extracted."""
        product = self.sample_products[0]
        
        # Mock scraping with invalid price
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=True,
            product_name="Produto Teste 1",
            price=0.0,  # Invalid price
            url=product.url
        )
        
        # Execute monitoring
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result
        self.assertFalse(result.sucesso)
        self.assertEqual(result.preco_atual, 0.0)
        self.assertIn("Invalid price", result.erro)
    
    def test_monitor_single_product_database_error(self):
        """Test monitoring when database operation fails."""
        product = self.sample_products[0]
        
        # Mock successful scraping
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=True,
            product_name="Produto Teste 1",
            price=90.0,
            url=product.url
        )
        
        # Mock database error
        self.mock_database.insert_price_record.side_effect = Exception("Database error")
        
        # Execute monitoring (should not fail completely)
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result (should still be successful despite DB error)
        self.assertTrue(result.sucesso)
        self.assertEqual(result.preco_atual, 90.0)
        self.assertTrue(result.alerta_enviado)  # Alert should still be sent
    
    def test_monitor_single_product_notification_error(self):
        """Test monitoring when notification fails."""
        product = self.sample_products[0]
        
        # Mock successful scraping (price below target)
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=True,
            product_name="Produto Teste 1",
            price=90.0,
            url=product.url
        )
        
        # Mock notification error
        self.mock_notifier.send_price_alert.side_effect = Exception("Email error")
        
        # Execute monitoring (should not fail completely)
        result = self.price_monitor.monitor_single_product(product)
        
        # Verify result (should still be successful despite notification error)
        self.assertTrue(result.sucesso)
        self.assertEqual(result.preco_atual, 90.0)
        self.assertFalse(result.alerta_enviado)  # Alert marked as not sent due to error
    
    def test_monitor_all_products_empty_list(self):
        """Test monitoring with empty product list."""
        result = self.price_monitor.monitor_all_products([])
        
        # Verify result
        self.assertEqual(result.total_products, 0)
        self.assertEqual(result.successful_scrapes, 0)
        self.assertEqual(result.failed_scrapes, 0)
        self.assertEqual(result.alerts_sent, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("No products configured", result.errors[0])
    
    def test_monitor_all_products_success(self):
        """Test successful monitoring of all products."""
        # Mock successful scraping for both active products
        def mock_scrape_product(url, selectors=None):
            if "produto1" in url:
                return ScrapingResult(success=True, product_name="Produto Teste 1", price=90.0, url=url)
            elif "produto2" in url:
                return ScrapingResult(success=True, product_name="Produto Teste 2", price=250.0, url=url)
            else:
                return ScrapingResult(success=False, url=url, error_message="Unknown product")
        
        self.mock_scraper.scrape_product.side_effect = mock_scrape_product
        
        # Execute monitoring
        result = self.price_monitor.monitor_all_products(self.sample_products)
        
        # Verify result (only 2 active products should be processed)
        self.assertEqual(result.total_products, 2)  # Only active products
        self.assertEqual(result.successful_scrapes, 2)
        self.assertEqual(result.failed_scrapes, 0)
        self.assertEqual(result.alerts_sent, 1)  # Only produto1 triggers alert (90 <= 100)
        self.assertEqual(len(result.results), 2)
        self.assertGreater(result.execution_time, 0)
        
        # Verify database calls (2 active products)
        self.assertEqual(self.mock_database.insert_price_record.call_count, 2)
        
        # Verify notification calls (only 1 alert)
        self.assertEqual(self.mock_notifier.send_price_alert.call_count, 1)
    
    def test_monitor_all_products_mixed_results(self):
        """Test monitoring with mixed success and failure results."""
        # Mock mixed scraping results
        def mock_scrape_product(url, selectors=None):
            if "produto1" in url:
                return ScrapingResult(success=True, product_name="Produto Teste 1", price=90.0, url=url)
            elif "produto2" in url:
                return ScrapingResult(success=False, url=url, error_message="Network error")
            else:
                return ScrapingResult(success=False, url=url, error_message="Unknown product")
        
        self.mock_scraper.scrape_product.side_effect = mock_scrape_product
        
        # Execute monitoring
        result = self.price_monitor.monitor_all_products(self.sample_products)
        
        # Verify result
        self.assertEqual(result.total_products, 2)  # Only active products
        self.assertEqual(result.successful_scrapes, 1)
        self.assertEqual(result.failed_scrapes, 1)
        self.assertEqual(result.alerts_sent, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Network error", result.errors[0])
    
    def test_monitor_all_products_high_failure_rate(self):
        """Test monitoring with high failure rate triggers system alert."""
        # Mock all scraping to fail
        self.mock_scraper.scrape_product.return_value = ScrapingResult(
            success=False,
            url="test",
            error_message="All failed"
        )
        
        # Execute monitoring
        result = self.price_monitor.monitor_all_products(self.sample_products)
        
        # Verify result
        self.assertEqual(result.successful_scrapes, 0)
        self.assertEqual(result.failed_scrapes, 2)  # Only active products
        
        # Verify system alert was sent for high failure rate
        self.mock_notifier.send_system_alert.assert_called()
        alert_call = self.mock_notifier.send_system_alert.call_args
        self.assertIn("High failure rate", alert_call[0][0])
        self.assertEqual(alert_call[0][1], "WARNING")
    
    def test_monitor_all_products_critical_error(self):
        """Test monitoring when critical error occurs."""
        # Mock scraper to raise exception
        self.mock_scraper.scrape_product.side_effect = Exception("Critical error")
        
        # Execute monitoring
        result = self.price_monitor.monitor_all_products(self.sample_products)
        
        # Verify result
        self.assertEqual(result.successful_scrapes, 0)
        self.assertEqual(result.failed_scrapes, 2)  # All active products failed
        self.assertGreater(len(result.errors), 0)
        
        # Verify critical system alert was sent
        self.mock_notifier.send_system_alert.assert_called()
    
    def test_get_performance_metrics_no_executions(self):
        """Test performance metrics with no executions."""
        metrics = self.price_monitor.get_performance_metrics()
        
        # Check legacy metrics structure
        legacy_metrics = metrics['legacy_metrics']
        self.assertEqual(legacy_metrics['total_executions'], 0)
        self.assertEqual(legacy_metrics['successful_executions'], 0)
        self.assertEqual(legacy_metrics['failed_executions'], 0)
        self.assertEqual(legacy_metrics['success_rate'], 0.0)
        self.assertEqual(legacy_metrics['average_execution_time'], 0.0)
        self.assertIn('scraper_metrics', legacy_metrics)
        
        # Check enhanced metrics structure
        enhanced_metrics = metrics['enhanced_statistics']
        self.assertEqual(enhanced_metrics['total_executions'], 0)
        self.assertEqual(enhanced_metrics['overall_success_rate'], 0.0)
    
    def test_get_performance_metrics_with_executions(self):
        """Test performance metrics after executions."""
        # Simulate some executions by updating counters
        self.price_monitor.total_executions = 10
        self.price_monitor.successful_executions = 8
        self.price_monitor.failed_executions = 2
        self.price_monitor.total_execution_time = 50.0
        
        # Mock scraper metrics
        self.mock_scraper.get_performance_metrics.return_value = {
            'total_requests': 20,
            'success_rate': 85.0
        }
        
        metrics = self.price_monitor.get_performance_metrics()
        
        # Check legacy metrics structure
        legacy_metrics = metrics['legacy_metrics']
        self.assertEqual(legacy_metrics['total_executions'], 10)
        self.assertEqual(legacy_metrics['successful_executions'], 8)
        self.assertEqual(legacy_metrics['failed_executions'], 2)
        self.assertEqual(legacy_metrics['success_rate'], 80.0)
        self.assertEqual(legacy_metrics['average_execution_time'], 5.0)
        self.assertEqual(legacy_metrics['scraper_metrics']['total_requests'], 20)
        
        # Check enhanced metrics structure
        enhanced_metrics = metrics['enhanced_statistics']
        self.assertIn('total_executions', enhanced_metrics)
        self.assertIn('overall_success_rate', enhanced_metrics)
    
    def test_reset_metrics(self):
        """Test resetting performance metrics."""
        # Set some values
        self.price_monitor.total_executions = 5
        self.price_monitor.successful_executions = 3
        self.price_monitor.failed_executions = 2
        self.price_monitor.total_execution_time = 25.0
        
        # Reset metrics
        self.price_monitor.reset_metrics()
        
        # Verify reset
        self.assertEqual(self.price_monitor.total_executions, 0)
        self.assertEqual(self.price_monitor.successful_executions, 0)
        self.assertEqual(self.price_monitor.failed_executions, 0)
        self.assertEqual(self.price_monitor.total_execution_time, 0.0)
        
        # Verify scraper metrics were also reset
        self.mock_scraper.reset_metrics.assert_called_once()
    
    def test_health_check_all_healthy(self):
        """Test health check when all components are healthy."""
        # Mock healthy responses
        self.mock_database.get_database_stats.return_value = {'total_records': 100}
        self.mock_scraper.get_performance_metrics.return_value = {'success_rate': 95.0}
        
        # Mock console notifier
        mock_console_notifier = Mock()
        mock_console_notifier.is_enabled.return_value = True
        self.mock_notifier.get_notifier.return_value = mock_console_notifier
        
        health = self.price_monitor.health_check()
        
        self.assertEqual(health['overall_status'], 'healthy')
        self.assertEqual(health['components']['database']['status'], 'healthy')
        self.assertEqual(health['components']['scraper']['status'], 'healthy')
        self.assertEqual(health['components']['notifications']['status'], 'healthy')
        self.assertIn('performance_metrics', health)
    
    def test_health_check_database_unhealthy(self):
        """Test health check when database is unhealthy."""
        # Mock database error
        self.mock_database.get_database_stats.side_effect = Exception("DB connection failed")
        self.mock_scraper.get_performance_metrics.return_value = {'success_rate': 95.0}
        
        # Mock console notifier
        mock_console_notifier = Mock()
        mock_console_notifier.is_enabled.return_value = True
        self.mock_notifier.get_notifier.return_value = mock_console_notifier
        
        health = self.price_monitor.health_check()
        
        self.assertEqual(health['overall_status'], 'degraded')
        self.assertEqual(health['components']['database']['status'], 'unhealthy')
        self.assertIn('DB connection failed', health['components']['database']['error'])
    
    def test_context_manager(self):
        """Test PriceMonitor as context manager."""
        with self.price_monitor as monitor:
            self.assertIs(monitor, self.price_monitor)
        
        # Verify cleanup was called
        self.mock_scraper.close.assert_called_once()
        self.mock_database.close_connections.assert_called_once()
    
    def test_close(self):
        """Test closing PriceMonitor."""
        self.price_monitor.close()
        
        # Verify cleanup was called
        self.mock_scraper.close.assert_called_once()
        self.mock_database.close_connections.assert_called_once()


if __name__ == '__main__':
    unittest.main()