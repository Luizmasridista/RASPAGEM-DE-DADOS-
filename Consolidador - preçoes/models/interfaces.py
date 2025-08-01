"""
Base interfaces and abstract classes for the price monitoring system.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from .data_models import ProductConfig, SystemConfig, PriceRecord, ProductData, MonitoringResult


class ConfigManagerInterface(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def load_products_config(self) -> List[ProductConfig]:
        """Load product configurations from storage."""
        pass
    
    @abstractmethod
    def save_products_config(self, products: List[ProductConfig]) -> None:
        """Save product configurations to storage."""
        pass
    
    @abstractmethod
    def get_system_config(self) -> SystemConfig:
        """Get system configuration."""
        pass
    
    @abstractmethod
    def validate_product_config(self, product: ProductConfig) -> bool:
        """Validate a product configuration."""
        pass


class WebScraperInterface(ABC):
    """Interface for web scraping functionality."""
    
    @abstractmethod
    def scrape_product(self, url: str, selectors: Optional[Dict[str, List[str]]] = None) -> ProductData:
        """Scrape product data from a URL."""
        pass


class DatabaseManagerInterface(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def create_tables(self) -> None:
        """Create necessary database tables."""
        pass
    
    @abstractmethod
    def insert_price_record(self, record: PriceRecord) -> None:
        """Insert a price record into the database."""
        pass
    
    @abstractmethod
    def get_price_history(self, product_name: str, days: int = 30) -> List[PriceRecord]:
        """Get price history for a product."""
        pass
    
    @abstractmethod
    def get_latest_prices(self) -> List[PriceRecord]:
        """Get the latest prices for all products."""
        pass
    
    @abstractmethod
    def cleanup_old_records(self, days: int = 365) -> None:
        """Clean up old price records."""
        pass


class NotificationServiceInterface(ABC):
    """Interface for notification services."""
    
    @abstractmethod
    def send_price_alert(self, product: ProductConfig, current_price: float) -> None:
        """Send a price alert notification."""
        pass
    
    @abstractmethod
    def send_system_alert(self, message: str, level: str = "INFO") -> None:
        """Send a system alert notification."""
        pass


class PriceMonitorInterface(ABC):
    """Interface for price monitoring orchestration."""
    
    @abstractmethod
    def monitor_all_products(self) -> MonitoringResult:
        """Monitor all configured products."""
        pass
    
    @abstractmethod
    def monitor_single_product(self, product: ProductConfig) -> 'ProductResult':
        """Monitor a single product."""
        pass
    
    @abstractmethod
    def check_price_alerts(self, current_price: float, target_price: float) -> bool:
        """Check if a price alert should be triggered."""
        pass