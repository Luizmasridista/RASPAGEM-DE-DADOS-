"""
Price monitoring orchestration class for the price monitoring system.
Coordinates web scraping, database operations, and notifications.
"""
import time
import logging
import asyncio
import concurrent.futures
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from models.data_models import ProductConfig, PriceRecord, ProductResult, MonitoringResult
from models.interfaces import PriceMonitorInterface
from services.web_scraper import WebScraper, ScrapingResult
from services.database_manager import DatabaseManager
from services.notification_service import NotificationService
from services.performance_monitor import PerformanceMonitor, ExecutionMetrics, PerformanceStatistics


class PriceMonitor(PriceMonitorInterface):
    """
    Main orchestration class for price monitoring operations.
    Coordinates scraping, database operations, and notifications.
    """
    
    def __init__(self, 
                 scraper: WebScraper,
                 database: DatabaseManager,
                 notifier: NotificationService,
                 max_workers: int = 5,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize price monitor with required services.
        
        Args:
            scraper: Web scraper instance
            database: Database manager instance
            notifier: Notification service instance
            max_workers: Maximum number of concurrent workers for parallel processing
            performance_monitor: Optional performance monitor instance
        """
        self.scraper = scraper
        self.database = database
        self.notifier = notifier
        self.max_workers = max_workers
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize performance monitor
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        
        # Legacy performance tracking (kept for backward compatibility)
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        
        self.logger.info(f"PriceMonitor initialized with max_workers={max_workers}")
    
    def monitor_all_products(self, products: List[ProductConfig]) -> MonitoringResult:
        """
        Monitor all configured products with parallel processing.
        
        Args:
            products: List of product configurations to monitor
            
        Returns:
            MonitoringResult with execution statistics
        """
        start_time = time.time()
        self.total_executions += 1
        
        if not products:
            self.logger.warning("No products configured for monitoring")
            return MonitoringResult(
                total_products=0,
                successful_scrapes=0,
                failed_scrapes=0,
                alerts_sent=0,
                execution_time=time.time() - start_time,
                errors=["No products configured"],
                results=[]
            )
        
        self.logger.info(f"Starting monitoring of {len(products)} products")
        
        # Filter active products
        active_products = [p for p in products if p.ativo]
        if len(active_products) != len(products):
            self.logger.info(f"Monitoring {len(active_products)} active products out of {len(products)} total")
        
        # Start performance monitoring
        self.performance_monitor.start_execution(len(active_products))
        
        results = []
        errors = []
        alerts_sent = 0
        
        try:
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all monitoring tasks
                future_to_product = {
                    executor.submit(self.monitor_single_product, product): product
                    for product in active_products
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_product):
                    product = future_to_product[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.alerta_enviado:
                            alerts_sent += 1
                        
                        if result.erro:
                            errors.append(f"{product.nome}: {result.erro}")
                            
                    except Exception as e:
                        error_msg = f"Unexpected error monitoring {product.nome}: {str(e)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg, exc_info=True)
                        
                        # Create failed result
                        failed_result = ProductResult(
                            produto=product,
                            sucesso=False,
                            erro=str(e),
                            tempo_execucao=0.0
                        )
                        results.append(failed_result)
            
            # Calculate statistics
            successful_scrapes = sum(1 for r in results if r.sucesso)
            failed_scrapes = len(results) - successful_scrapes
            execution_time = time.time() - start_time
            
            # Update legacy performance tracking
            self.total_execution_time += execution_time
            if failed_scrapes == 0:
                self.successful_executions += 1
            else:
                self.failed_executions += 1
            
            # Record performance metrics
            execution_metrics = self.performance_monitor.end_execution(
                successful_scrapes=successful_scrapes,
                failed_scrapes=failed_scrapes,
                alerts_sent=alerts_sent,
                errors=errors
            )
            
            # Create monitoring result
            monitoring_result = MonitoringResult(
                total_products=len(active_products),
                successful_scrapes=successful_scrapes,
                failed_scrapes=failed_scrapes,
                alerts_sent=alerts_sent,
                execution_time=execution_time,
                errors=errors,
                results=results
            )
            
            # Log summary with performance metrics
            self.logger.info(
                f"Monitoring completed: {successful_scrapes}/{len(active_products)} successful, "
                f"{alerts_sent} alerts sent, {execution_time:.2f}s "
                f"(Success rate: {execution_metrics.success_rate:.1f}%)"
            )
            
            # Send system alert if there were significant failures
            failure_rate = failed_scrapes / len(active_products) if active_products else 0
            if failure_rate > 0.5:  # More than 50% failures
                self.notifier.send_system_alert(
                    f"High failure rate in monitoring: {failed_scrapes}/{len(active_products)} products failed",
                    "WARNING"
                )
            
            return monitoring_result
            
        except Exception as e:
            self.failed_executions += 1
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            error_msg = f"Critical error in monitor_all_products: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # Record failed execution in performance monitor
            try:
                self.performance_monitor.end_execution(
                    successful_scrapes=0,
                    failed_scrapes=len(active_products),
                    alerts_sent=0,
                    errors=[error_msg]
                )
            except Exception:
                pass  # Don't let performance monitoring errors break the main flow
            
            # Send critical system alert
            self.notifier.send_system_alert(error_msg, "CRITICAL")
            
            return MonitoringResult(
                total_products=len(active_products),
                successful_scrapes=0,
                failed_scrapes=len(active_products),
                alerts_sent=0,
                execution_time=execution_time,
                errors=[error_msg],
                results=[]
            )
    
    def monitor_single_product(self, product: ProductConfig) -> ProductResult:
        """
        Monitor a single product with complete error handling.
        
        Args:
            product: Product configuration to monitor
            
        Returns:
            ProductResult with monitoring outcome
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Starting monitoring for product: {product.nome}")
            
            # Validate product configuration
            if not product.ativo:
                return ProductResult(
                    produto=product,
                    sucesso=False,
                    erro="Product is not active",
                    tempo_execucao=time.time() - start_time
                )
            
            # Scrape product data
            scraping_result = self.scraper.scrape_product(
                product.url,
                product.seletores_personalizados
            )
            
            if not scraping_result.success:
                error_msg = f"Scraping failed: {scraping_result.error_message}"
                self.logger.warning(f"Failed to scrape {product.nome}: {error_msg}")
                
                # Store failed record in database
                failed_record = PriceRecord(
                    nome_produto=product.nome,
                    url=product.url,
                    preco=0.0,
                    preco_alvo=product.preco_alvo,
                    data_hora=datetime.now(),
                    status="failed",
                    erro=error_msg
                )
                
                try:
                    self.database.insert_price_record(failed_record)
                except Exception as db_error:
                    self.logger.error(f"Failed to store error record: {db_error}")
                
                return ProductResult(
                    produto=product,
                    sucesso=False,
                    erro=error_msg,
                    tempo_execucao=time.time() - start_time
                )
            
            # Extract price from scraping result
            current_price = scraping_result.price
            if current_price is None or current_price <= 0:
                error_msg = "Invalid price extracted from page"
                self.logger.warning(f"Invalid price for {product.nome}: {current_price}")
                
                return ProductResult(
                    produto=product,
                    sucesso=False,
                    preco_atual=current_price,
                    erro=error_msg,
                    tempo_execucao=time.time() - start_time
                )
            
            # Store price record in database
            price_record = PriceRecord(
                nome_produto=product.nome,
                url=product.url,
                preco=current_price,
                preco_alvo=product.preco_alvo,
                data_hora=datetime.now(),
                status="active"
            )
            
            try:
                self.database.insert_price_record(price_record)
                self.logger.debug(f"Stored price record for {product.nome}: R$ {current_price}")
            except Exception as db_error:
                self.logger.error(f"Failed to store price record: {db_error}")
                # Continue execution even if database storage fails
            
            # Check if price alert should be triggered
            alert_sent = False
            if self.check_price_alerts(current_price, product.preco_alvo):
                try:
                    self.notifier.send_price_alert(product, current_price)
                    alert_sent = True
                    self.logger.info(f"Price alert sent for {product.nome}: R$ {current_price} <= R$ {product.preco_alvo}")
                except Exception as notification_error:
                    self.logger.error(f"Failed to send price alert: {notification_error}")
                    # Don't fail the entire operation if notification fails
            
            execution_time = time.time() - start_time
            
            return ProductResult(
                produto=product,
                sucesso=True,
                preco_atual=current_price,
                alerta_enviado=alert_sent,
                tempo_execucao=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Error monitoring {product.nome}: {error_msg}", exc_info=True)
            
            return ProductResult(
                produto=product,
                sucesso=False,
                erro=error_msg,
                tempo_execucao=execution_time
            )
    
    def check_price_alerts(self, current_price: float, target_price: float) -> bool:
        """
        Check if a price alert should be triggered.
        
        Args:
            current_price: Current price found
            target_price: Target price threshold
            
        Returns:
            True if alert should be sent, False otherwise
        """
        try:
            # Validate inputs
            if current_price <= 0 or target_price <= 0:
                self.logger.warning(f"Invalid prices for alert check: current={current_price}, target={target_price}")
                return False
            
            # Check if current price is at or below target price
            should_alert = current_price <= target_price
            
            self.logger.debug(f"Price alert check: {current_price} <= {target_price} = {should_alert}")
            
            return should_alert
            
        except Exception as e:
            self.logger.error(f"Error in price alert check: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring operations.
        
        Returns:
            Dictionary with performance statistics
        """
        # Get enhanced performance statistics
        enhanced_stats = self.performance_monitor.get_current_statistics()
        
        # Legacy metrics for backward compatibility
        legacy_metrics = {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': (self.successful_executions / self.total_executions * 100) if self.total_executions > 0 else 0.0,
            'average_execution_time': self.total_execution_time / self.total_executions if self.total_executions > 0 else 0.0,
            'scraper_metrics': self.scraper.get_performance_metrics()
        }
        
        # Combine enhanced and legacy metrics
        return {
            'enhanced_statistics': {
                'total_executions': enhanced_stats.total_executions,
                'total_products_processed': enhanced_stats.total_products_processed,
                'overall_success_rate': enhanced_stats.overall_success_rate,
                'average_execution_time': enhanced_stats.average_execution_time,
                'median_execution_time': enhanced_stats.median_execution_time,
                'min_execution_time': enhanced_stats.min_execution_time,
                'max_execution_time': enhanced_stats.max_execution_time,
                'total_alerts_sent': enhanced_stats.total_alerts_sent,
                'total_alert_rate': enhanced_stats.total_alert_rate,
                'total_errors': enhanced_stats.total_errors,
                'most_common_errors': enhanced_stats.most_common_errors,
                'success_rate_trend': enhanced_stats.success_rate_trend,
                'performance_trend': enhanced_stats.performance_trend
            },
            'legacy_metrics': legacy_metrics
        }
    
    def get_detailed_performance_statistics(self) -> PerformanceStatistics:
        """
        Get detailed performance statistics from the performance monitor.
        
        Returns:
            PerformanceStatistics object with comprehensive metrics
        """
        return self.performance_monitor.get_current_statistics()
    
    def get_recent_executions(self, count: int = 10) -> List[ExecutionMetrics]:
        """
        Get recent execution metrics.
        
        Args:
            count: Number of recent executions to return
            
        Returns:
            List of ExecutionMetrics objects
        """
        return self.performance_monitor.get_recent_executions(count)
    
    def get_hourly_statistics(self, hours_back: int = 24) -> Dict[str, Dict[str, float]]:
        """
        Get hourly performance statistics.
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary with hourly statistics
        """
        return self.performance_monitor.get_hourly_statistics(hours_back)
    
    def get_daily_statistics(self, days_back: int = 7) -> Dict[str, Dict[str, float]]:
        """
        Get daily performance statistics.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with daily statistics
        """
        return self.performance_monitor.get_daily_statistics(days_back)
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Get detailed error analysis.
        
        Returns:
            Dictionary with error analysis data
        """
        return self.performance_monitor.get_error_analysis()
    
    def export_performance_data(self) -> Dict[str, Any]:
        """
        Export all performance data for external analysis.
        
        Returns:
            Dictionary with all performance data
        """
        return self.performance_monitor.export_metrics()
    
    def reset_metrics(self) -> None:
        """Reset performance metrics counters."""
        # Reset legacy metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        
        # Reset enhanced performance monitor
        self.performance_monitor.reset_metrics()
        
        # Reset scraper metrics
        self.scraper.reset_metrics()
        
        self.logger.info("All performance metrics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.
        
        Returns:
            Dictionary with health status of all components
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        try:
            # Check database health
            try:
                db_stats = self.database.get_database_stats()
                health_status['components']['database'] = {
                    'status': 'healthy',
                    'stats': db_stats
                }
            except Exception as e:
                health_status['components']['database'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
            
            # Check scraper health
            try:
                scraper_metrics = self.scraper.get_performance_metrics()
                health_status['components']['scraper'] = {
                    'status': 'healthy',
                    'metrics': scraper_metrics
                }
            except Exception as e:
                health_status['components']['scraper'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
            
            # Check notification service health
            try:
                # Test console notifier (should always be available)
                console_notifier = self.notifier.get_notifier('console')
                if console_notifier and console_notifier.is_enabled():
                    health_status['components']['notifications'] = {
                        'status': 'healthy',
                        'console_enabled': True
                    }
                else:
                    health_status['components']['notifications'] = {
                        'status': 'degraded',
                        'console_enabled': False
                    }
            except Exception as e:
                health_status['components']['notifications'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['overall_status'] = 'degraded'
            
            # Add performance metrics
            health_status['performance_metrics'] = self.get_performance_metrics()
            
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status
    
    def close(self) -> None:
        """Close the price monitor and clean up resources."""
        try:
            if self.scraper:
                self.scraper.close()
            
            if self.database:
                self.database.close_connections()
            
            metrics = self.get_performance_metrics()
            self.logger.info(f"PriceMonitor closing - Final metrics: {metrics}")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    print("PriceMonitor module loaded successfully")
    print(f"PriceMonitor class: {PriceMonitor}")