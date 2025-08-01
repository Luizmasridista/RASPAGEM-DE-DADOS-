# Models package for data structures and configurations

from .data_models import (
    ProductConfig,
    SystemConfig,
    PriceRecord,
    ProductData,
    ProductResult,
    MonitoringResult
)

from .interfaces import (
    ConfigManagerInterface,
    WebScraperInterface,
    DatabaseManagerInterface,
    NotificationServiceInterface,
    PriceMonitorInterface
)

__all__ = [
    # Data models
    'ProductConfig',
    'SystemConfig',
    'PriceRecord',
    'ProductData',
    'ProductResult',
    'MonitoringResult',
    
    # Interfaces
    'ConfigManagerInterface',
    'WebScraperInterface',
    'DatabaseManagerInterface',
    'NotificationServiceInterface',
    'PriceMonitorInterface'
]