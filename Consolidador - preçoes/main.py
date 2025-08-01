#!/usr/bin/env python3
"""
Main application entry point for the Price Monitoring System.
Provides command-line interface and integrates all components.
"""
import sys
import os
import argparse
import logging
import signal
import time
from typing import Optional, List
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from components.config_manager import ConfigManager
from services.web_scraper import WebScraper
from services.database_manager import DatabaseManager
from services.notification_service import NotificationService
from services.price_monitor import PriceMonitor
from services.task_scheduler import TaskScheduler
from models.data_models import SystemConfig, ProductConfig


class PriceMonitoringApp:
    """
    Main application class that orchestrates all components.
    """
    
    def __init__(self, config_path: str = "produtos.json", system_config_path: str = "config.json"):
        """
        Initialize the price monitoring application.
        
        Args:
            config_path: Path to products configuration file
            system_config_path: Path to system configuration file
        """
        self.config_path = config_path
        self.system_config_path = system_config_path
        
        # Components
        self.config_manager: Optional[ConfigManager] = None
        self.system_config: Optional[SystemConfig] = None
        self.web_scraper: Optional[WebScraper] = None
        self.database_manager: Optional[DatabaseManager] = None
        self.notification_service: Optional[NotificationService] = None
        self.price_monitor: Optional[PriceMonitor] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        
        # Application state
        self.running = False
        self.logger: Optional[logging.Logger] = None
        
        # Signal handling
        self._shutdown_requested = False
        
    def setup_logging(self, log_level: str = "INFO") -> None:
        """
        Setup logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Setup file handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            logs_dir / "price_monitor.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            handlers=[file_handler, console_handler],
            format=log_format
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Logging initialized with level: {log_level}")
    
    def initialize_components(self) -> bool:
        """
        Initialize all application components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing application components...")
            
            # Initialize configuration manager
            self.config_manager = ConfigManager(
                products_config_path=self.config_path,
                system_config_path=self.system_config_path
            )
            
            # Load system configuration
            self.system_config = self.config_manager.get_system_config()
            self.logger.info(f"System configuration loaded: {self.system_config}")
            
            # Initialize database manager
            self.database_manager = DatabaseManager(db_path=self.system_config.db_path)
            self.database_manager.create_tables()
            self.logger.info("Database manager initialized")
            
            # Initialize web scraper
            from services.web_scraper import ScrapingConfig
            scraping_config = ScrapingConfig(
                timeout=self.system_config.timeout_requisicao,
                max_retries=self.system_config.max_retries
            )
            self.web_scraper = WebScraper(config=scraping_config)
            self.logger.info("Web scraper initialized")
            
            # Initialize notification service
            self.notification_service = NotificationService()
            
            # Add email notifier if enabled
            if self.system_config.email_enabled:
                from services.notification_service import EmailNotifier, SMTPConfig
                smtp_config = SMTPConfig(
                    server=self.system_config.smtp_server,
                    port=self.system_config.smtp_port,
                    username=self.system_config.smtp_username,
                    password=self.system_config.smtp_password,
                    use_tls=True
                )
                email_notifier = EmailNotifier(smtp_config)
                self.notification_service.add_notifier("email", email_notifier)
            self.logger.info("Notification service initialized")
            
            # Initialize price monitor
            self.price_monitor = PriceMonitor(
                scraper=self.web_scraper,
                database=self.database_manager,
                notifier=self.notification_service
            )
            self.logger.info("Price monitor initialized")
            
            # Initialize task scheduler
            self.task_scheduler = TaskScheduler(system_config=self.system_config)
            self.logger.info("Task scheduler initialized")
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize components: {str(e)}", exc_info=True)
            else:
                print(f"Failed to initialize components: {str(e)}")
            return False
    
    def setup_monitoring_task(self) -> bool:
        """
        Setup the main monitoring task in the scheduler.
        
        Returns:
            True if task setup successful, False otherwise
        """
        try:
            def monitoring_task():
                """Main monitoring task that processes all products."""
                try:
                    self.logger.info("Starting scheduled monitoring execution")
                    
                    # Load current products configuration
                    products = self.config_manager.load_products_config()
                    
                    if not products:
                        self.logger.warning("No products configured for monitoring")
                        return True
                    
                    # Execute monitoring
                    result = self.price_monitor.monitor_all_products(products)
                    
                    # Log results
                    self.logger.info(
                        f"Monitoring completed: {result.successful_scrapes}/{result.total_products} successful, "
                        f"{result.alerts_sent} alerts sent, {result.execution_time:.2f}s"
                    )
                    
                    if result.errors:
                        self.logger.warning(f"Monitoring errors: {result.errors}")
                    
                    return result.successful_scrapes > 0 or result.total_products == 0
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring task: {str(e)}", exc_info=True)
                    return False
            
            # Add monitoring task to scheduler
            success = self.task_scheduler.add_task(
                name="price_monitoring",
                job_func=monitoring_task,
                interval=self.system_config.intervalo_execucao,
                enabled=True
            )
            
            if success:
                self.logger.info(f"Monitoring task scheduled with {self.system_config.intervalo_execucao}s interval")
            else:
                self.logger.error("Failed to schedule monitoring task")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitoring task: {str(e)}", exc_info=True)
            return False
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received {signal_name} signal, initiating shutdown...")
            self._shutdown_requested = True
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            self.logger.debug("Signal handlers setup for graceful shutdown")
        except Exception as e:
            self.logger.warning(f"Failed to setup signal handlers: {str(e)}")
    
    def run_once(self) -> bool:
        """
        Run monitoring once and exit.
        
        Returns:
            True if monitoring successful, False otherwise
        """
        try:
            self.logger.info("Running price monitoring once...")
            
            # Load products configuration
            products = self.config_manager.load_products_config()
            
            if not products:
                self.logger.warning("No products configured for monitoring")
                return True
            
            # Execute monitoring
            result = self.price_monitor.monitor_all_products(products)
            
            # Log results
            self.logger.info(
                f"One-time monitoring completed: {result.successful_scrapes}/{result.total_products} successful, "
                f"{result.alerts_sent} alerts sent, {result.execution_time:.2f}s"
            )
            
            if result.errors:
                self.logger.warning(f"Monitoring errors: {result.errors}")
                for error in result.errors:
                    self.logger.error(f"  - {error}")
            
            # Print summary to console
            print(f"\n=== Monitoring Results ===")
            print(f"Products processed: {result.total_products}")
            print(f"Successful scrapes: {result.successful_scrapes}")
            print(f"Failed scrapes: {result.failed_scrapes}")
            print(f"Alerts sent: {result.alerts_sent}")
            print(f"Execution time: {result.execution_time:.2f}s")
            
            if result.errors:
                print(f"\nErrors:")
                for error in result.errors:
                    print(f"  - {error}")
            
            return result.failed_scrapes == 0
            
        except Exception as e:
            self.logger.error(f"Error in one-time monitoring: {str(e)}", exc_info=True)
            return False
    
    def run_daemon(self) -> bool:
        """
        Run as daemon with scheduled monitoring.
        
        Returns:
            True if daemon ran successfully, False otherwise
        """
        try:
            self.logger.info("Starting price monitoring daemon...")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Setup monitoring task
            if not self.setup_monitoring_task():
                self.logger.error("Failed to setup monitoring task")
                return False
            
            # Start scheduler
            if not self.task_scheduler.start():
                self.logger.error("Failed to start task scheduler")
                return False
            
            self.running = True
            self.logger.info("Price monitoring daemon started successfully")
            
            # Print startup information
            print(f"\n=== Price Monitoring Daemon Started ===")
            print(f"Monitoring interval: {self.system_config.intervalo_execucao} seconds")
            print(f"Database: {self.system_config.db_path}")
            print(f"Email notifications: {'Enabled' if self.system_config.email_enabled else 'Disabled'}")
            print(f"Log level: {self.system_config.log_level}")
            print(f"Press Ctrl+C to stop gracefully")
            print("=" * 40)
            
            # Main daemon loop
            try:
                while not self._shutdown_requested:
                    time.sleep(1.0)
                    
                    # Check if scheduler is still running
                    if not self.task_scheduler.is_running():
                        self.logger.error("Task scheduler stopped unexpectedly")
                        break
                        
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                self._shutdown_requested = True
            
            # Graceful shutdown
            self.logger.info("Shutting down daemon...")
            
            if self.task_scheduler:
                self.task_scheduler.stop(timeout=30)
            
            self.running = False
            self.logger.info("Price monitoring daemon stopped")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in daemon mode: {str(e)}", exc_info=True)
            return False
    
    def show_status(self) -> None:
        """Show current application status."""
        try:
            print("\n=== Price Monitoring System Status ===")
            
            # System configuration
            print(f"\nSystem Configuration:")
            print(f"  Monitoring interval: {self.system_config.intervalo_execucao} seconds")
            print(f"  Request timeout: {self.system_config.timeout_requisicao} seconds")
            print(f"  Max retries: {self.system_config.max_retries}")
            print(f"  Database: {self.system_config.db_path}")
            print(f"  Email notifications: {'Enabled' if self.system_config.email_enabled else 'Disabled'}")
            print(f"  Log level: {self.system_config.log_level}")
            
            # Products configuration
            products = self.config_manager.load_products_config()
            print(f"\nProducts Configuration:")
            print(f"  Total products: {len(products)}")
            print(f"  Active products: {len([p for p in products if p.ativo])}")
            
            if products:
                print(f"\nProduct Details:")
                for i, product in enumerate(products, 1):
                    status = "Active" if product.ativo else "Inactive"
                    print(f"  {i}. {product.nome} - R$ {product.preco_alvo:.2f} ({status})")
            
            # Database statistics
            if self.database_manager:
                try:
                    stats = self.database_manager.get_database_stats()
                    print(f"\nDatabase Statistics:")
                    print(f"  Total records: {stats.get('total_records', 'N/A')}")
                    print(f"  Active records: {stats.get('active_records', 'N/A')}")
                    print(f"  Database size: {stats.get('database_size_mb', 'N/A')} MB")
                except Exception as e:
                    print(f"  Database stats unavailable: {str(e)}")
            
            # Performance metrics
            if self.price_monitor:
                try:
                    metrics = self.price_monitor.get_performance_metrics()
                    legacy_metrics = metrics.get('legacy_metrics', {})
                    print(f"\nPerformance Metrics:")
                    print(f"  Total executions: {legacy_metrics.get('total_executions', 0)}")
                    print(f"  Success rate: {legacy_metrics.get('success_rate', 0):.1f}%")
                    print(f"  Average execution time: {legacy_metrics.get('average_execution_time', 0):.2f}s")
                except Exception as e:
                    print(f"  Performance metrics unavailable: {str(e)}")
            
            print("=" * 40)
            
        except Exception as e:
            self.logger.error(f"Error showing status: {str(e)}", exc_info=True)
            print(f"Error showing status: {str(e)}")
    
    def cleanup(self) -> None:
        """Cleanup application resources."""
        try:
            self.logger.info("Cleaning up application resources...")
            
            if self.task_scheduler and self.task_scheduler.is_running():
                self.task_scheduler.stop()
            
            if self.price_monitor:
                self.price_monitor.close()
            
            if self.database_manager:
                self.database_manager.close_connections()
            
            if self.web_scraper:
                self.web_scraper.close()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during cleanup: {str(e)}")
            else:
                print(f"Error during cleanup: {str(e)}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Price Monitoring System - Monitor product prices and send alerts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --once                    # Run monitoring once and exit
  %(prog)s --daemon                  # Run as daemon with scheduled monitoring
  %(prog)s --status                  # Show current system status
  %(prog)s --config produtos.json    # Use custom products configuration file
  %(prog)s --log-level DEBUG         # Set logging level to DEBUG
        """
    )
    
    # Execution modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--once',
        action='store_true',
        help='Run monitoring once and exit'
    )
    mode_group.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon with scheduled monitoring'
    )
    mode_group.add_argument(
        '--status',
        action='store_true',
        help='Show current system status and exit'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        default='produtos.json',
        help='Path to products configuration file (default: produtos.json)'
    )
    parser.add_argument(
        '--system-config',
        default='config.json',
        help='Path to system configuration file (default: config.json)'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output (log to file only)'
    )
    
    return parser


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Initialize application
    app = PriceMonitoringApp(
        config_path=args.config,
        system_config_path=args.system_config
    )
    
    try:
        # Setup logging
        app.setup_logging(log_level=args.log_level)
        
        # Initialize components
        if not app.initialize_components():
            print("Failed to initialize application components", file=sys.stderr)
            return 1
        
        # Execute based on mode
        if args.status:
            app.show_status()
            return 0
        elif args.once:
            success = app.run_once()
            return 0 if success else 1
        elif args.daemon:
            success = app.run_daemon()
            return 0 if success else 1
        else:
            print("No execution mode specified", file=sys.stderr)
            return 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        if app.logger:
            app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        else:
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1
    finally:
        # Cleanup
        app.cleanup()


if __name__ == "__main__":
    sys.exit(main())