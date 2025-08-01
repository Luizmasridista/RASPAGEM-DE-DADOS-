"""
Performance monitoring and metrics collection for the price monitoring system.
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import threading


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution."""
    timestamp: datetime
    execution_time: float
    products_processed: int
    successful_scrapes: int
    failed_scrapes: int
    alerts_sent: int
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.products_processed == 0:
            return 0.0
        return (self.successful_scrapes / self.products_processed) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        return 100.0 - self.success_rate
    
    @property
    def alert_rate(self) -> float:
        """Calculate alert rate as percentage of successful scrapes."""
        if self.successful_scrapes == 0:
            return 0.0
        return (self.alerts_sent / self.successful_scrapes) * 100


@dataclass
class PerformanceStatistics:
    """Aggregated performance statistics."""
    total_executions: int
    total_execution_time: float
    total_products_processed: int
    total_successful_scrapes: int
    total_failed_scrapes: int
    total_alerts_sent: int
    
    # Time-based statistics
    average_execution_time: float
    min_execution_time: float
    max_execution_time: float
    median_execution_time: float
    
    # Success rate statistics
    overall_success_rate: float
    average_success_rate: float
    min_success_rate: float
    max_success_rate: float
    
    # Alert statistics
    total_alert_rate: float
    average_alert_rate: float
    
    # Error statistics
    total_errors: int
    most_common_errors: List[tuple] = field(default_factory=list)
    
    # Trend analysis
    success_rate_trend: str = "stable"  # "improving", "declining", "stable"
    performance_trend: str = "stable"   # "improving", "declining", "stable"


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection system.
    Tracks execution statistics, trends, and provides analytics.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_history_size: Maximum number of execution records to keep in memory
        """
        self.max_history_size = max_history_size
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread-safe storage
        self._lock = threading.Lock()
        
        # Execution history (using deque for efficient operations)
        self._execution_history: deque = deque(maxlen=max_history_size)
        
        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        # Performance tracking by time periods
        self._hourly_stats: Dict[str, List[ExecutionMetrics]] = defaultdict(list)
        self._daily_stats: Dict[str, List[ExecutionMetrics]] = defaultdict(list)
        
        # Real-time metrics
        self._current_execution_start: Optional[float] = None
        self._current_products_count: int = 0
        
        self.logger.info(f"PerformanceMonitor initialized with max_history_size={max_history_size}")
    
    def start_execution(self, products_count: int) -> None:
        """
        Mark the start of a monitoring execution.
        
        Args:
            products_count: Number of products to be processed
        """
        with self._lock:
            self._current_execution_start = time.time()
            self._current_products_count = products_count
            
        self.logger.debug(f"Started execution tracking for {products_count} products")
    
    def end_execution(self, successful_scrapes: int, failed_scrapes: int, 
                     alerts_sent: int, errors: List[str]) -> ExecutionMetrics:
        """
        Mark the end of a monitoring execution and record metrics.
        
        Args:
            successful_scrapes: Number of successful scrapes
            failed_scrapes: Number of failed scrapes
            alerts_sent: Number of alerts sent
            errors: List of error messages
            
        Returns:
            ExecutionMetrics object with recorded data
        """
        with self._lock:
            if self._current_execution_start is None:
                raise ValueError("No execution started - call start_execution() first")
            
            execution_time = time.time() - self._current_execution_start
            timestamp = datetime.now()
            
            # Create execution metrics
            metrics = ExecutionMetrics(
                timestamp=timestamp,
                execution_time=execution_time,
                products_processed=self._current_products_count,
                successful_scrapes=successful_scrapes,
                failed_scrapes=failed_scrapes,
                alerts_sent=alerts_sent,
                errors=errors.copy()
            )
            
            # Store in history
            self._execution_history.append(metrics)
            
            # Update error counts
            for error in errors:
                # Extract error type (first part before colon)
                error_type = error.split(':')[0].strip()
                self._error_counts[error_type] += 1
            
            # Store in time-based buckets
            hour_key = timestamp.strftime("%Y-%m-%d-%H")
            day_key = timestamp.strftime("%Y-%m-%d")
            
            self._hourly_stats[hour_key].append(metrics)
            self._daily_stats[day_key].append(metrics)
            
            # Clean up old time-based data (keep last 7 days)
            self._cleanup_old_time_data()
            
            # Reset current execution tracking
            self._current_execution_start = None
            self._current_products_count = 0
            
        self.logger.debug(f"Recorded execution metrics: {metrics.success_rate:.1f}% success rate, {execution_time:.2f}s")
        return metrics
    
    def get_current_statistics(self) -> PerformanceStatistics:
        """
        Get current aggregated performance statistics.
        
        Returns:
            PerformanceStatistics object with current data
        """
        with self._lock:
            if not self._execution_history:
                return self._empty_statistics()
            
            executions = list(self._execution_history)
            
            # Basic aggregations
            total_executions = len(executions)
            total_execution_time = sum(e.execution_time for e in executions)
            total_products_processed = sum(e.products_processed for e in executions)
            total_successful_scrapes = sum(e.successful_scrapes for e in executions)
            total_failed_scrapes = sum(e.failed_scrapes for e in executions)
            total_alerts_sent = sum(e.alerts_sent for e in executions)
            
            # Time statistics
            execution_times = [e.execution_time for e in executions]
            average_execution_time = statistics.mean(execution_times)
            min_execution_time = min(execution_times)
            max_execution_time = max(execution_times)
            median_execution_time = statistics.median(execution_times)
            
            # Success rate statistics
            success_rates = [e.success_rate for e in executions]
            overall_success_rate = (total_successful_scrapes / total_products_processed * 100) if total_products_processed > 0 else 0.0
            average_success_rate = statistics.mean(success_rates)
            min_success_rate = min(success_rates)
            max_success_rate = max(success_rates)
            
            # Alert statistics
            total_alert_rate = (total_alerts_sent / total_successful_scrapes * 100) if total_successful_scrapes > 0 else 0.0
            alert_rates = [e.alert_rate for e in executions if e.successful_scrapes > 0]
            average_alert_rate = statistics.mean(alert_rates) if alert_rates else 0.0
            
            # Error statistics
            total_errors = sum(len(e.errors) for e in executions)
            most_common_errors = sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Trend analysis
            success_rate_trend = self._calculate_success_rate_trend(executions)
            performance_trend = self._calculate_performance_trend(executions)
            
            return PerformanceStatistics(
                total_executions=total_executions,
                total_execution_time=total_execution_time,
                total_products_processed=total_products_processed,
                total_successful_scrapes=total_successful_scrapes,
                total_failed_scrapes=total_failed_scrapes,
                total_alerts_sent=total_alerts_sent,
                average_execution_time=average_execution_time,
                min_execution_time=min_execution_time,
                max_execution_time=max_execution_time,
                median_execution_time=median_execution_time,
                overall_success_rate=overall_success_rate,
                average_success_rate=average_success_rate,
                min_success_rate=min_success_rate,
                max_success_rate=max_success_rate,
                total_alert_rate=total_alert_rate,
                average_alert_rate=average_alert_rate,
                total_errors=total_errors,
                most_common_errors=most_common_errors,
                success_rate_trend=success_rate_trend,
                performance_trend=performance_trend
            )
    
    def get_recent_executions(self, count: int = 10) -> List[ExecutionMetrics]:
        """
        Get the most recent execution metrics.
        
        Args:
            count: Number of recent executions to return
            
        Returns:
            List of ExecutionMetrics objects
        """
        with self._lock:
            return list(self._execution_history)[-count:]
    
    def get_executions_by_time_range(self, start_time: datetime, end_time: datetime) -> List[ExecutionMetrics]:
        """
        Get executions within a specific time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of ExecutionMetrics objects within the time range
        """
        with self._lock:
            return [
                execution for execution in self._execution_history
                if start_time <= execution.timestamp <= end_time
            ]
    
    def get_hourly_statistics(self, hours_back: int = 24) -> Dict[str, Dict[str, float]]:
        """
        Get hourly performance statistics.
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary with hourly statistics
        """
        with self._lock:
            now = datetime.now()
            hourly_stats = {}
            
            for i in range(hours_back):
                hour_time = now - timedelta(hours=i)
                hour_key = hour_time.strftime("%Y-%m-%d-%H")
                
                if hour_key in self._hourly_stats:
                    executions = self._hourly_stats[hour_key]
                    hourly_stats[hour_key] = self._calculate_period_stats(executions)
                else:
                    hourly_stats[hour_key] = {
                        'executions': 0,
                        'success_rate': 0.0,
                        'average_execution_time': 0.0,
                        'alerts_sent': 0
                    }
            
            return hourly_stats
    
    def get_daily_statistics(self, days_back: int = 7) -> Dict[str, Dict[str, float]]:
        """
        Get daily performance statistics.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Dictionary with daily statistics
        """
        with self._lock:
            now = datetime.now()
            daily_stats = {}
            
            for i in range(days_back):
                day_time = now - timedelta(days=i)
                day_key = day_time.strftime("%Y-%m-%d")
                
                if day_key in self._daily_stats:
                    executions = self._daily_stats[day_key]
                    daily_stats[day_key] = self._calculate_period_stats(executions)
                else:
                    daily_stats[day_key] = {
                        'executions': 0,
                        'success_rate': 0.0,
                        'average_execution_time': 0.0,
                        'alerts_sent': 0
                    }
            
            return daily_stats
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """
        Get detailed error analysis.
        
        Returns:
            Dictionary with error analysis data
        """
        with self._lock:
            total_errors = sum(self._error_counts.values())
            
            if total_errors == 0:
                return {
                    'total_errors': 0,
                    'error_types': [],
                    'error_rate': 0.0,
                    'most_frequent_error': None
                }
            
            # Sort errors by frequency
            sorted_errors = sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate error rates
            error_types = [
                {
                    'type': error_type,
                    'count': count,
                    'percentage': (count / total_errors) * 100
                }
                for error_type, count in sorted_errors
            ]
            
            # Calculate overall error rate
            total_executions = len(self._execution_history)
            error_rate = (total_errors / total_executions) if total_executions > 0 else 0.0
            
            return {
                'total_errors': total_errors,
                'error_types': error_types,
                'error_rate': error_rate,
                'most_frequent_error': sorted_errors[0] if sorted_errors else None
            }
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics and history."""
        with self._lock:
            self._execution_history.clear()
            self._error_counts.clear()
            self._hourly_stats.clear()
            self._daily_stats.clear()
            self._current_execution_start = None
            self._current_products_count = 0
            
        self.logger.info("Performance metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics data for external analysis.
        
        Returns:
            Dictionary with all metrics data
        """
        with self._lock:
            return {
                'statistics': self.get_current_statistics().__dict__,
                'recent_executions': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'execution_time': e.execution_time,
                        'products_processed': e.products_processed,
                        'successful_scrapes': e.successful_scrapes,
                        'failed_scrapes': e.failed_scrapes,
                        'alerts_sent': e.alerts_sent,
                        'success_rate': e.success_rate,
                        'errors': e.errors
                    }
                    for e in self._execution_history
                ],
                'error_analysis': self.get_error_analysis(),
                'hourly_stats': self.get_hourly_statistics(),
                'daily_stats': self.get_daily_statistics()
            }
    
    def _empty_statistics(self) -> PerformanceStatistics:
        """Return empty statistics object."""
        return PerformanceStatistics(
            total_executions=0,
            total_execution_time=0.0,
            total_products_processed=0,
            total_successful_scrapes=0,
            total_failed_scrapes=0,
            total_alerts_sent=0,
            average_execution_time=0.0,
            min_execution_time=0.0,
            max_execution_time=0.0,
            median_execution_time=0.0,
            overall_success_rate=0.0,
            average_success_rate=0.0,
            min_success_rate=0.0,
            max_success_rate=0.0,
            total_alert_rate=0.0,
            average_alert_rate=0.0,
            total_errors=0,
            most_common_errors=[],
            success_rate_trend="stable",
            performance_trend="stable"
        )
    
    def _calculate_period_stats(self, executions: List[ExecutionMetrics]) -> Dict[str, float]:
        """Calculate statistics for a period."""
        if not executions:
            return {
                'executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'alerts_sent': 0
            }
        
        total_products = sum(e.products_processed for e in executions)
        total_successful = sum(e.successful_scrapes for e in executions)
        success_rate = (total_successful / total_products * 100) if total_products > 0 else 0.0
        
        return {
            'executions': len(executions),
            'success_rate': success_rate,
            'average_execution_time': statistics.mean([e.execution_time for e in executions]),
            'alerts_sent': sum(e.alerts_sent for e in executions)
        }
    
    def _calculate_success_rate_trend(self, executions: List[ExecutionMetrics]) -> str:
        """Calculate success rate trend."""
        if len(executions) < 5:
            return "stable"
        
        # Compare recent vs older executions
        recent = executions[-5:]
        older = executions[-10:-5] if len(executions) >= 10 else executions[:-5]
        
        if not older:
            return "stable"
        
        recent_avg = statistics.mean([e.success_rate for e in recent])
        older_avg = statistics.mean([e.success_rate for e in older])
        
        diff = recent_avg - older_avg
        
        if diff > 5.0:
            return "improving"
        elif diff < -5.0:
            return "declining"
        else:
            return "stable"
    
    def _calculate_performance_trend(self, executions: List[ExecutionMetrics]) -> str:
        """Calculate performance (execution time) trend."""
        if len(executions) < 5:
            return "stable"
        
        # Compare recent vs older executions (lower execution time is better)
        recent = executions[-5:]
        older = executions[-10:-5] if len(executions) >= 10 else executions[:-5]
        
        if not older:
            return "stable"
        
        recent_avg = statistics.mean([e.execution_time for e in recent])
        older_avg = statistics.mean([e.execution_time for e in older])
        
        # Performance improves when execution time decreases
        diff = older_avg - recent_avg
        
        if diff > 1.0:  # 1 second improvement
            return "improving"
        elif diff < -1.0:  # 1 second degradation
            return "declining"
        else:
            return "stable"
    
    def _cleanup_old_time_data(self) -> None:
        """Clean up old time-based data to prevent memory leaks."""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Clean hourly stats
        old_hour_keys = [
            key for key in self._hourly_stats.keys()
            if datetime.strptime(key, "%Y-%m-%d-%H") < cutoff_date
        ]
        for key in old_hour_keys:
            del self._hourly_stats[key]
        
        # Clean daily stats
        old_day_keys = [
            key for key in self._daily_stats.keys()
            if datetime.strptime(key, "%Y-%m-%d") < cutoff_date
        ]
        for key in old_day_keys:
            del self._daily_stats[key]


if __name__ == "__main__":
    print("PerformanceMonitor module loaded successfully")
    print(f"PerformanceMonitor class: {PerformanceMonitor}")
    print(f"ExecutionMetrics class: {ExecutionMetrics}")
    print(f"PerformanceStatistics class: {PerformanceStatistics}")