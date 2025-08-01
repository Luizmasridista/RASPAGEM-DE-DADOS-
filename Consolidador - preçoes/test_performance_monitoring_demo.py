#!/usr/bin/env python3
"""
Performance Monitoring Demo Script

This script demonstrates the comprehensive performance monitoring and metrics
capabilities of the price monitoring system.
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from models.data_models import ProductConfig, SystemConfig
from services.performance_monitor import PerformanceMonitor, ExecutionMetrics, PerformanceStatistics
from services.web_scraper import WebScraper
from services.database_manager import DatabaseManager
from services.notification_service import NotificationService
from services.price_monitor import PriceMonitor
from services.http_client import HTTPClient
from services.html_parser import HTMLParser
from components.config_manager import ConfigManager


def create_test_products() -> List[ProductConfig]:
    """Create test product configurations."""
    return [
        ProductConfig(
            nome="Produto Teste 1",
            url="https://httpbin.org/json",
            preco_alvo=100.0,
            ativo=True
        ),
        ProductConfig(
            nome="Produto Teste 2", 
            url="https://httpbin.org/delay/1",
            preco_alvo=50.0,
            ativo=True
        ),
        ProductConfig(
            nome="Produto Teste 3",
            url="https://httpbin.org/status/404",  # This will fail
            preco_alvo=75.0,
            ativo=True
        ),
        ProductConfig(
            nome="Produto Inativo",
            url="https://httpbin.org/json",
            preco_alvo=200.0,
            ativo=False  # This won't be processed
        )
    ]


def demonstrate_performance_monitor():
    """Demonstrate PerformanceMonitor capabilities."""
    print("\n" + "="*60)
    print("PERFORMANCE MONITOR DEMONSTRATION")
    print("="*60)
    
    # Create performance monitor
    perf_monitor = PerformanceMonitor(max_history_size=100)
    
    print("\n1. Simulating multiple monitoring executions...")
    
    # Simulate multiple executions with varying performance
    execution_scenarios = [
        (10, 8, 2, 3, ["Network timeout", "Parse error"]),
        (5, 5, 0, 2, []),
        (8, 6, 2, 1, ["Connection refused"]),
        (12, 10, 2, 4, ["Invalid price format", "Network timeout"]),
        (6, 4, 2, 1, ["Parse error"]),
        (15, 13, 2, 5, ["Network timeout"]),
        (7, 7, 0, 3, []),
        (9, 7, 2, 2, ["Connection refused", "Invalid price format"])
    ]
    
    for i, (products, successful, failed, alerts, errors) in enumerate(execution_scenarios):
        print(f"   Execution {i+1}: {products} products, {successful} successful, {failed} failed")
        
        perf_monitor.start_execution(products)
        time.sleep(0.1 + (i * 0.05))  # Simulate varying execution times
        metrics = perf_monitor.end_execution(successful, failed, alerts, errors)
        
        print(f"      → Success rate: {metrics.success_rate:.1f}%, "
              f"Execution time: {metrics.execution_time:.3f}s")
    
    print("\n2. Current Performance Statistics:")
    stats = perf_monitor.get_current_statistics()
    
    print(f"   Total Executions: {stats.total_executions}")
    print(f"   Total Products Processed: {stats.total_products_processed}")
    print(f"   Overall Success Rate: {stats.overall_success_rate:.1f}%")
    print(f"   Average Execution Time: {stats.average_execution_time:.3f}s")
    print(f"   Min/Max Execution Time: {stats.min_execution_time:.3f}s / {stats.max_execution_time:.3f}s")
    print(f"   Total Alerts Sent: {stats.total_alerts_sent}")
    print(f"   Total Alert Rate: {stats.total_alert_rate:.1f}%")
    print(f"   Total Errors: {stats.total_errors}")
    print(f"   Success Rate Trend: {stats.success_rate_trend}")
    print(f"   Performance Trend: {stats.performance_trend}")
    
    print("\n3. Most Common Errors:")
    for error_type, count in stats.most_common_errors:
        print(f"   - {error_type}: {count} occurrences")
    
    print("\n4. Recent Executions (last 3):")
    recent = perf_monitor.get_recent_executions(3)
    for i, execution in enumerate(recent):
        print(f"   Execution {len(recent)-i}: {execution.timestamp.strftime('%H:%M:%S')} - "
              f"{execution.success_rate:.1f}% success, {execution.execution_time:.3f}s")
    
    print("\n5. Error Analysis:")
    error_analysis = perf_monitor.get_error_analysis()
    print(f"   Total Errors: {error_analysis['total_errors']}")
    print(f"   Error Rate: {error_analysis['error_rate']:.2f} errors per execution")
    if error_analysis['most_frequent_error']:
        error_type, count = error_analysis['most_frequent_error']
        print(f"   Most Frequent Error: {error_type} ({count} times)")
    
    print("\n6. Hourly Statistics (last 2 hours):")
    hourly_stats = perf_monitor.get_hourly_statistics(2)
    for hour, stats_data in sorted(hourly_stats.items()):
        if stats_data['executions'] > 0:
            print(f"   {hour}: {stats_data['executions']} executions, "
                  f"{stats_data['success_rate']:.1f}% success rate")
    
    return perf_monitor


def demonstrate_integrated_monitoring():
    """Demonstrate integrated performance monitoring with PriceMonitor."""
    print("\n" + "="*60)
    print("INTEGRATED MONITORING DEMONSTRATION")
    print("="*60)
    
    # Create system configuration
    system_config = SystemConfig(
        timeout_requisicao=5,
        max_retries=2,
        log_level="INFO"
    )
    
    # Initialize components
    from services.web_scraper import ScrapingConfig
    scraping_config = ScrapingConfig(
        timeout=system_config.timeout_requisicao,
        max_retries=system_config.max_retries
    )
    web_scraper = WebScraper(scraping_config)
    
    database_manager = DatabaseManager(":memory:")  # Use in-memory database
    
    from services.notification_service import ConsoleNotifier
    notification_service = NotificationService()
    notification_service.add_notifier('console', ConsoleNotifier())
    
    # Create performance monitor
    performance_monitor = PerformanceMonitor()
    
    # Create price monitor with performance monitoring
    price_monitor = PriceMonitor(
        scraper=web_scraper,
        database=database_manager,
        notifier=notification_service,
        max_workers=3,
        performance_monitor=performance_monitor
    )
    
    print("\n1. Running monitoring with performance tracking...")
    
    # Create test products
    products = create_test_products()
    
    # Run monitoring
    result = price_monitor.monitor_all_products(products)
    
    print(f"\n2. Monitoring Results:")
    print(f"   Total Products: {result.total_products}")
    print(f"   Successful Scrapes: {result.successful_scrapes}")
    print(f"   Failed Scrapes: {result.failed_scrapes}")
    print(f"   Alerts Sent: {result.alerts_sent}")
    print(f"   Execution Time: {result.execution_time:.3f}s")
    
    if result.errors:
        print(f"   Errors:")
        for error in result.errors:
            print(f"     - {error}")
    
    print(f"\n3. Enhanced Performance Metrics:")
    enhanced_metrics = price_monitor.get_performance_metrics()
    
    # Display enhanced statistics
    enhanced_stats = enhanced_metrics['enhanced_statistics']
    print(f"   Total Executions: {enhanced_stats['total_executions']}")
    print(f"   Products Processed: {enhanced_stats['total_products_processed']}")
    print(f"   Overall Success Rate: {enhanced_stats['overall_success_rate']:.1f}%")
    print(f"   Average Execution Time: {enhanced_stats['average_execution_time']:.3f}s")
    print(f"   Total Alerts Sent: {enhanced_stats['total_alerts_sent']}")
    print(f"   Success Rate Trend: {enhanced_stats['success_rate_trend']}")
    
    print(f"\n4. Legacy Metrics (for backward compatibility):")
    legacy_metrics = enhanced_metrics['legacy_metrics']
    print(f"   Total Executions: {legacy_metrics['total_executions']}")
    print(f"   Successful Executions: {legacy_metrics['successful_executions']}")
    print(f"   Success Rate: {legacy_metrics['success_rate']:.1f}%")
    print(f"   Average Execution Time: {legacy_metrics['average_execution_time']:.3f}s")
    
    print(f"\n5. Health Check:")
    health_status = price_monitor.health_check()
    print(f"   Overall Status: {health_status['overall_status']}")
    print(f"   Components:")
    for component, status in health_status['components'].items():
        print(f"     - {component}: {status['status']}")
    
    # Run a few more monitoring cycles to show trend analysis
    print(f"\n6. Running additional monitoring cycles for trend analysis...")
    for i in range(3):
        print(f"   Cycle {i+2}...")
        result = price_monitor.monitor_all_products(products[:2])  # Use fewer products for speed
        time.sleep(0.5)
    
    # Show updated statistics
    final_stats = price_monitor.get_detailed_performance_statistics()
    print(f"\n7. Final Performance Statistics:")
    print(f"   Total Executions: {final_stats.total_executions}")
    print(f"   Overall Success Rate: {final_stats.overall_success_rate:.1f}%")
    print(f"   Success Rate Trend: {final_stats.success_rate_trend}")
    print(f"   Performance Trend: {final_stats.performance_trend}")
    
    # Export metrics for analysis
    print(f"\n8. Exporting performance data...")
    exported_data = price_monitor.export_performance_data()
    
    # Save to file for inspection
    with open('performance_metrics_export.json', 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        json.dump(exported_data, f, indent=2, default=serialize_datetime)
    
    print(f"   Performance data exported to 'performance_metrics_export.json'")
    
    # Cleanup
    price_monitor.close()
    
    return price_monitor


def demonstrate_metrics_analysis():
    """Demonstrate advanced metrics analysis capabilities."""
    print("\n" + "="*60)
    print("ADVANCED METRICS ANALYSIS")
    print("="*60)
    
    perf_monitor = PerformanceMonitor()
    
    # Simulate a week of monitoring data
    print("\n1. Simulating a week of monitoring data...")
    
    base_time = datetime.now() - timedelta(days=7)
    
    # Simulate different performance patterns throughout the week
    for day in range(7):
        day_time = base_time + timedelta(days=day)
        
        # Simulate different performance on different days
        if day < 2:  # First 2 days - poor performance
            scenarios = [(10, 6, 4, 2, ["Network issues", "Server errors"])] * 3
        elif day < 4:  # Next 2 days - improving performance  
            scenarios = [(10, 8, 2, 3, ["Minor errors"])] * 4
        else:  # Last 3 days - good performance
            scenarios = [(10, 9, 1, 4, [])] * 5
        
        for scenario in scenarios:
            products, successful, failed, alerts, errors = scenario
            perf_monitor.start_execution(products)
            time.sleep(0.01)  # Small delay
            perf_monitor.end_execution(successful, failed, alerts, errors)
    
    print(f"   Generated {len(perf_monitor._execution_history)} execution records")
    
    print("\n2. Weekly Performance Analysis:")
    stats = perf_monitor.get_current_statistics()
    print(f"   Overall Success Rate: {stats.overall_success_rate:.1f}%")
    print(f"   Success Rate Trend: {stats.success_rate_trend}")
    print(f"   Performance Trend: {stats.performance_trend}")
    
    print("\n3. Daily Statistics (last 7 days):")
    daily_stats = perf_monitor.get_daily_statistics(7)
    for day, day_stats in sorted(daily_stats.items()):
        if day_stats['executions'] > 0:
            print(f"   {day}: {day_stats['executions']} executions, "
                  f"{day_stats['success_rate']:.1f}% success, "
                  f"{day_stats['average_execution_time']:.3f}s avg time")
    
    print("\n4. Error Trend Analysis:")
    error_analysis = perf_monitor.get_error_analysis()
    print(f"   Total Errors: {error_analysis['total_errors']}")
    print(f"   Error Rate: {error_analysis['error_rate']:.2f} errors per execution")
    
    print("\n   Error Types by Frequency:")
    for error_info in error_analysis['error_types']:
        print(f"     - {error_info['type']}: {error_info['count']} times "
              f"({error_info['percentage']:.1f}%)")
    
    return perf_monitor


def main():
    """Main demonstration function."""
    print("PRICE MONITORING SYSTEM - PERFORMANCE MONITORING DEMO")
    print("=" * 60)
    print("This demo showcases the comprehensive performance monitoring")
    print("and metrics collection capabilities of the system.")
    
    try:
        # Demonstrate standalone performance monitor
        perf_monitor1 = demonstrate_performance_monitor()
        
        # Demonstrate integrated monitoring
        price_monitor = demonstrate_integrated_monitoring()
        
        # Demonstrate advanced metrics analysis
        perf_monitor2 = demonstrate_metrics_analysis()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nKey Performance Monitoring Features Demonstrated:")
        print("✓ Real-time execution metrics tracking")
        print("✓ Success/failure rate monitoring")
        print("✓ Execution time statistics (min, max, average, median)")
        print("✓ Alert rate tracking")
        print("✓ Error analysis and categorization")
        print("✓ Trend analysis (improving/declining/stable)")
        print("✓ Time-based statistics (hourly, daily)")
        print("✓ Thread-safe metrics collection")
        print("✓ Comprehensive data export capabilities")
        print("✓ Integration with PriceMonitor")
        print("✓ Health check functionality")
        print("✓ Legacy metrics compatibility")
        
        print("\nFiles generated:")
        print("- performance_metrics_export.json (detailed metrics data)")
        
        print("\nThe performance monitoring system is fully operational!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())