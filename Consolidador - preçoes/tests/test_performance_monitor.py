"""
Unit tests for the PerformanceMonitor class.
"""
import unittest
from unittest.mock import Mock, patch
import time
from datetime import datetime, timedelta
from typing import List

from services.performance_monitor import (
    PerformanceMonitor, 
    ExecutionMetrics, 
    PerformanceStatistics
)


class TestExecutionMetrics(unittest.TestCase):
    """Test cases for ExecutionMetrics class."""
    
    def test_execution_metrics_creation(self):
        """Test ExecutionMetrics creation and properties."""
        timestamp = datetime.now()
        metrics = ExecutionMetrics(
            timestamp=timestamp,
            execution_time=5.0,
            products_processed=10,
            successful_scrapes=8,
            failed_scrapes=2,
            alerts_sent=3,
            errors=["Error 1", "Error 2"]
        )
        
        self.assertEqual(metrics.timestamp, timestamp)
        self.assertEqual(metrics.execution_time, 5.0)
        self.assertEqual(metrics.products_processed, 10)
        self.assertEqual(metrics.successful_scrapes, 8)
        self.assertEqual(metrics.failed_scrapes, 2)
        self.assertEqual(metrics.alerts_sent, 3)
        self.assertEqual(len(metrics.errors), 2)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ExecutionMetrics(
            timestamp=datetime.now(),
            execution_time=5.0,
            products_processed=10,
            successful_scrapes=8,
            failed_scrapes=2,
            alerts_sent=3
        )
        
        self.assertEqual(metrics.success_rate, 80.0)
        self.assertEqual(metrics.failure_rate, 20.0)
    
    def test_success_rate_zero_products(self):
        """Test success rate with zero products processed."""
        metrics = ExecutionMetrics(
            timestamp=datetime.now(),
            execution_time=5.0,
            products_processed=0,
            successful_scrapes=0,
            failed_scrapes=0,
            alerts_sent=0
        )
        
        self.assertEqual(metrics.success_rate, 0.0)
        self.assertEqual(metrics.failure_rate, 100.0)
    
    def test_alert_rate_calculation(self):
        """Test alert rate calculation."""
        metrics = ExecutionMetrics(
            timestamp=datetime.now(),
            execution_time=5.0,
            products_processed=10,
            successful_scrapes=8,
            failed_scrapes=2,
            alerts_sent=4
        )
        
        self.assertEqual(metrics.alert_rate, 50.0)  # 4 alerts out of 8 successful scrapes
    
    def test_alert_rate_zero_successful(self):
        """Test alert rate with zero successful scrapes."""
        metrics = ExecutionMetrics(
            timestamp=datetime.now(),
            execution_time=5.0,
            products_processed=10,
            successful_scrapes=0,
            failed_scrapes=10,
            alerts_sent=0
        )
        
        self.assertEqual(metrics.alert_rate, 0.0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor(max_history_size=100)
    
    def test_init(self):
        """Test PerformanceMonitor initialization."""
        self.assertEqual(self.performance_monitor.max_history_size, 100)
        self.assertEqual(len(self.performance_monitor._execution_history), 0)
        self.assertEqual(len(self.performance_monitor._error_counts), 0)
    
    def test_start_execution(self):
        """Test starting execution tracking."""
        self.performance_monitor.start_execution(5)
        
        self.assertIsNotNone(self.performance_monitor._current_execution_start)
        self.assertEqual(self.performance_monitor._current_products_count, 5)
    
    def test_end_execution_without_start(self):
        """Test ending execution without starting raises error."""
        with self.assertRaises(ValueError):
            self.performance_monitor.end_execution(3, 2, 1, [])
    
    def test_complete_execution_cycle(self):
        """Test complete execution cycle from start to end."""
        # Start execution
        self.performance_monitor.start_execution(10)
        
        # Simulate some processing time
        time.sleep(0.01)
        
        # End execution
        errors = ["Network error", "Parse error"]
        metrics = self.performance_monitor.end_execution(8, 2, 3, errors)
        
        # Verify metrics
        self.assertIsInstance(metrics, ExecutionMetrics)
        self.assertEqual(metrics.products_processed, 10)
        self.assertEqual(metrics.successful_scrapes, 8)
        self.assertEqual(metrics.failed_scrapes, 2)
        self.assertEqual(metrics.alerts_sent, 3)
        self.assertEqual(metrics.errors, errors)
        self.assertGreater(metrics.execution_time, 0)
        self.assertEqual(metrics.success_rate, 80.0)
        
        # Verify execution was stored
        self.assertEqual(len(self.performance_monitor._execution_history), 1)
        
        # Verify error counts were updated
        self.assertEqual(self.performance_monitor._error_counts["Network error"], 1)
        self.assertEqual(self.performance_monitor._error_counts["Parse error"], 1)
    
    def test_get_current_statistics_empty(self):
        """Test getting statistics with no executions."""
        stats = self.performance_monitor.get_current_statistics()
        
        self.assertIsInstance(stats, PerformanceStatistics)
        self.assertEqual(stats.total_executions, 0)
        self.assertEqual(stats.total_products_processed, 0)
        self.assertEqual(stats.overall_success_rate, 0.0)
        self.assertEqual(stats.average_execution_time, 0.0)
    
    def test_get_current_statistics_with_data(self):
        """Test getting statistics with execution data."""
        # Add multiple executions
        executions_data = [
            (10, 8, 2, 3, ["Error 1"]),
            (5, 5, 0, 2, []),
            (8, 6, 2, 1, ["Error 2", "Error 1"])
        ]
        
        for products, successful, failed, alerts, errors in executions_data:
            self.performance_monitor.start_execution(products)
            time.sleep(0.001)  # Small delay for execution time
            self.performance_monitor.end_execution(successful, failed, alerts, errors)
        
        stats = self.performance_monitor.get_current_statistics()
        
        # Verify aggregated statistics
        self.assertEqual(stats.total_executions, 3)
        self.assertEqual(stats.total_products_processed, 23)  # 10 + 5 + 8
        self.assertEqual(stats.total_successful_scrapes, 19)  # 8 + 5 + 6
        self.assertEqual(stats.total_failed_scrapes, 4)      # 2 + 0 + 2
        self.assertEqual(stats.total_alerts_sent, 6)         # 3 + 2 + 1
        self.assertEqual(stats.total_errors, 3)              # 1 + 0 + 2
        
        # Verify calculated rates
        expected_success_rate = (19 / 23) * 100  # ~82.6%
        self.assertAlmostEqual(stats.overall_success_rate, expected_success_rate, places=1)
        
        expected_alert_rate = (6 / 19) * 100  # ~31.6%
        self.assertAlmostEqual(stats.total_alert_rate, expected_alert_rate, places=1)
        
        # Verify time statistics
        self.assertGreater(stats.average_execution_time, 0)
        self.assertGreater(stats.min_execution_time, 0)
        self.assertGreater(stats.max_execution_time, 0)
        self.assertGreaterEqual(stats.max_execution_time, stats.min_execution_time)
        
        # Verify error statistics
        self.assertEqual(len(stats.most_common_errors), 2)
        self.assertEqual(stats.most_common_errors[0][0], "Error 1")  # Most common
        self.assertEqual(stats.most_common_errors[0][1], 2)          # Count
    
    def test_get_recent_executions(self):
        """Test getting recent executions."""
        # Add some executions
        for i in range(5):
            self.performance_monitor.start_execution(1)
            self.performance_monitor.end_execution(1, 0, 0, [])
        
        # Get recent executions
        recent = self.performance_monitor.get_recent_executions(3)
        
        self.assertEqual(len(recent), 3)
        self.assertIsInstance(recent[0], ExecutionMetrics)
        
        # Should be in reverse chronological order (most recent first)
        for i in range(len(recent) - 1):
            self.assertGreaterEqual(recent[i].timestamp, recent[i + 1].timestamp)
    
    def test_get_executions_by_time_range(self):
        """Test getting executions by time range."""
        now = datetime.now()
        
        # Add executions with different timestamps
        self.performance_monitor.start_execution(1)
        self.performance_monitor.end_execution(1, 0, 0, [])
        
        time.sleep(0.01)
        
        self.performance_monitor.start_execution(1)
        self.performance_monitor.end_execution(1, 0, 0, [])
        
        # Get executions in time range
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=1)
        
        executions = self.performance_monitor.get_executions_by_time_range(start_time, end_time)
        
        self.assertEqual(len(executions), 2)
        for execution in executions:
            self.assertGreaterEqual(execution.timestamp, start_time)
            self.assertLessEqual(execution.timestamp, end_time)
    
    def test_get_error_analysis_empty(self):
        """Test error analysis with no errors."""
        analysis = self.performance_monitor.get_error_analysis()
        
        self.assertEqual(analysis['total_errors'], 0)
        self.assertEqual(len(analysis['error_types']), 0)
        self.assertEqual(analysis['error_rate'], 0.0)
        self.assertIsNone(analysis['most_frequent_error'])
    
    def test_get_error_analysis_with_data(self):
        """Test error analysis with error data."""
        # Add executions with errors
        error_data = [
            ["Network error", "Parse error"],
            ["Network error"],
            ["Database error", "Network error"]
        ]
        
        for errors in error_data:
            self.performance_monitor.start_execution(1)
            self.performance_monitor.end_execution(1, 0, 0, errors)
        
        analysis = self.performance_monitor.get_error_analysis()
        
        self.assertEqual(analysis['total_errors'], 5)  # Total error count
        self.assertEqual(len(analysis['error_types']), 3)  # Unique error types
        
        # Check error types are sorted by frequency
        error_types = analysis['error_types']
        self.assertEqual(error_types[0]['type'], "Network error")
        self.assertEqual(error_types[0]['count'], 3)
        self.assertEqual(error_types[0]['percentage'], 60.0)  # 3/5 * 100
        
        # Check most frequent error
        self.assertEqual(analysis['most_frequent_error'][0], "Network error")
        self.assertEqual(analysis['most_frequent_error'][1], 3)
        
        # Check error rate (errors per execution)
        expected_error_rate = 5 / 3  # 5 errors in 3 executions
        self.assertAlmostEqual(analysis['error_rate'], expected_error_rate, places=2)
    
    def test_reset_metrics(self):
        """Test resetting all metrics."""
        # Add some data
        self.performance_monitor.start_execution(5)
        self.performance_monitor.end_execution(3, 2, 1, ["Error"])
        
        # Verify data exists
        self.assertEqual(len(self.performance_monitor._execution_history), 1)
        self.assertEqual(len(self.performance_monitor._error_counts), 1)
        
        # Reset metrics
        self.performance_monitor.reset_metrics()
        
        # Verify data is cleared
        self.assertEqual(len(self.performance_monitor._execution_history), 0)
        self.assertEqual(len(self.performance_monitor._error_counts), 0)
        self.assertIsNone(self.performance_monitor._current_execution_start)
        self.assertEqual(self.performance_monitor._current_products_count, 0)
    
    def test_export_metrics(self):
        """Test exporting all metrics data."""
        # Add some execution data
        self.performance_monitor.start_execution(5)
        self.performance_monitor.end_execution(4, 1, 2, ["Test error"])
        
        exported = self.performance_monitor.export_metrics()
        
        # Verify exported structure
        self.assertIn('statistics', exported)
        self.assertIn('recent_executions', exported)
        self.assertIn('error_analysis', exported)
        self.assertIn('hourly_stats', exported)
        self.assertIn('daily_stats', exported)
        
        # Verify recent executions format
        recent_executions = exported['recent_executions']
        self.assertEqual(len(recent_executions), 1)
        
        execution = recent_executions[0]
        self.assertIn('timestamp', execution)
        self.assertIn('execution_time', execution)
        self.assertIn('products_processed', execution)
        self.assertIn('successful_scrapes', execution)
        self.assertIn('failed_scrapes', execution)
        self.assertIn('alerts_sent', execution)
        self.assertIn('success_rate', execution)
        self.assertIn('errors', execution)
    
    def test_max_history_size_limit(self):
        """Test that history size is limited to max_history_size."""
        # Create monitor with small history size
        small_monitor = PerformanceMonitor(max_history_size=3)
        
        # Add more executions than the limit
        for i in range(5):
            small_monitor.start_execution(1)
            small_monitor.end_execution(1, 0, 0, [])
        
        # Verify only the last 3 executions are kept
        self.assertEqual(len(small_monitor._execution_history), 3)
        
        # Verify they are the most recent ones
        executions = list(small_monitor._execution_history)
        for i in range(len(executions) - 1):
            self.assertLessEqual(executions[i].timestamp, executions[i + 1].timestamp)
    
    def test_trend_calculation_stable(self):
        """Test trend calculation when performance is stable."""
        # Add executions with stable success rates
        for _ in range(10):
            self.performance_monitor.start_execution(10)
            self.performance_monitor.end_execution(8, 2, 1, [])  # 80% success rate
        
        stats = self.performance_monitor.get_current_statistics()
        self.assertEqual(stats.success_rate_trend, "stable")
    
    def test_trend_calculation_improving(self):
        """Test trend calculation when performance is improving."""
        # Add older executions with lower success rate
        for _ in range(5):
            self.performance_monitor.start_execution(10)
            self.performance_monitor.end_execution(6, 4, 1, [])  # 60% success rate
        
        # Add recent executions with higher success rate
        for _ in range(5):
            self.performance_monitor.start_execution(10)
            self.performance_monitor.end_execution(9, 1, 1, [])  # 90% success rate
        
        stats = self.performance_monitor.get_current_statistics()
        self.assertEqual(stats.success_rate_trend, "improving")
    
    def test_trend_calculation_declining(self):
        """Test trend calculation when performance is declining."""
        # Add older executions with higher success rate
        for _ in range(5):
            self.performance_monitor.start_execution(10)
            self.performance_monitor.end_execution(9, 1, 1, [])  # 90% success rate
        
        # Add recent executions with lower success rate
        for _ in range(5):
            self.performance_monitor.start_execution(10)
            self.performance_monitor.end_execution(6, 4, 1, [])  # 60% success rate
        
        stats = self.performance_monitor.get_current_statistics()
        self.assertEqual(stats.success_rate_trend, "declining")
    
    def test_thread_safety(self):
        """Test thread safety of performance monitor operations."""
        import threading
        import random
        
        def worker():
            for _ in range(10):
                products = random.randint(1, 10)
                successful = random.randint(0, products)
                failed = products - successful
                alerts = random.randint(0, successful)
                
                self.performance_monitor.start_execution(products)
                time.sleep(0.001)  # Simulate processing time
                self.performance_monitor.end_execution(successful, failed, alerts, [])
        
        # Run multiple threads concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all executions were recorded
        self.assertEqual(len(self.performance_monitor._execution_history), 50)  # 5 threads * 10 executions
        
        # Verify statistics can be calculated without errors
        stats = self.performance_monitor.get_current_statistics()
        self.assertEqual(stats.total_executions, 50)


if __name__ == '__main__':
    unittest.main()