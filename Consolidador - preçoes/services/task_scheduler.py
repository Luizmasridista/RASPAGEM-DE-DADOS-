"""
Task scheduler for the price monitoring system.
Handles periodic execution with configurable intervals and graceful shutdown.
"""
import time
import signal
import threading
import logging
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import schedule

from models.data_models import SystemConfig


@dataclass
class ScheduledTask:
    """Represents a scheduled task with its configuration."""
    name: str
    job_func: Callable
    interval: int  # seconds
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    enabled: bool = True
    schedule_job: Optional[schedule.Job] = None


class TaskScheduler:
    """
    Task scheduler with configurable intervals and graceful shutdown handling.
    Uses the schedule library for periodic execution.
    """
    
    def __init__(self, system_config: Optional[SystemConfig] = None):
        """
        Initialize the task scheduler.
        
        Args:
            system_config: System configuration object
        """
        self.system_config = system_config or SystemConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Scheduler state
        self._running = False
        self._shutdown_requested = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Task management
        self._tasks: Dict[str, ScheduledTask] = {}
        self._task_lock = threading.Lock()
        
        # Statistics
        self._start_time: Optional[datetime] = None
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        
        # Signal handlers for graceful shutdown
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
        
        self.logger.info("TaskScheduler initialized")
    
    def add_task(self, name: str, job_func: Callable, interval: int, enabled: bool = True) -> bool:
        """
        Add a new scheduled task.
        
        Args:
            name: Unique name for the task
            job_func: Function to execute
            interval: Execution interval in seconds
            enabled: Whether the task is enabled
            
        Returns:
            True if task was added successfully, False otherwise
        """
        try:
            with self._task_lock:
                if name in self._tasks:
                    self.logger.warning(f"Task '{name}' already exists, updating configuration")
                    # Remove existing task from schedule
                    existing_task = self._tasks[name]
                    if existing_task.schedule_job:
                        schedule.cancel_job(existing_task.schedule_job)
                
                # Create new task
                task = ScheduledTask(
                    name=name,
                    job_func=job_func,
                    interval=interval,
                    enabled=enabled
                )
                
                # Add to schedule if enabled and scheduler is running
                if enabled and self._running:
                    task.schedule_job = schedule.every(interval).seconds.do(
                        self._execute_task_wrapper, task
                    )
                    task.next_run = datetime.now() + timedelta(seconds=interval)
                
                self._tasks[name] = task
                
                self.logger.info(f"Added task '{name}' with {interval}s interval (enabled: {enabled})")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add task '{name}': {str(e)}")
            return False
    
    def remove_task(self, name: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            name: Name of the task to remove
            
        Returns:
            True if task was removed successfully, False otherwise
        """
        try:
            with self._task_lock:
                if name not in self._tasks:
                    self.logger.warning(f"Task '{name}' not found")
                    return False
                
                task = self._tasks[name]
                
                # Cancel scheduled job
                if task.schedule_job:
                    schedule.cancel_job(task.schedule_job)
                
                # Remove from tasks
                del self._tasks[name]
                
                self.logger.info(f"Removed task '{name}'")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to remove task '{name}': {str(e)}")
            return False
    
    def enable_task(self, name: str) -> bool:
        """
        Enable a scheduled task.
        
        Args:
            name: Name of the task to enable
            
        Returns:
            True if task was enabled successfully, False otherwise
        """
        try:
            with self._task_lock:
                if name not in self._tasks:
                    self.logger.warning(f"Task '{name}' not found")
                    return False
                
                task = self._tasks[name]
                
                if task.enabled:
                    self.logger.info(f"Task '{name}' is already enabled")
                    return True
                
                task.enabled = True
                
                # Add to schedule if scheduler is running
                if self._running:
                    task.schedule_job = schedule.every(task.interval).seconds.do(
                        self._execute_task_wrapper, task
                    )
                    task.next_run = datetime.now() + timedelta(seconds=task.interval)
                
                self.logger.info(f"Enabled task '{name}'")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to enable task '{name}': {str(e)}")
            return False
    
    def disable_task(self, name: str) -> bool:
        """
        Disable a scheduled task.
        
        Args:
            name: Name of the task to disable
            
        Returns:
            True if task was disabled successfully, False otherwise
        """
        try:
            with self._task_lock:
                if name not in self._tasks:
                    self.logger.warning(f"Task '{name}' not found")
                    return False
                
                task = self._tasks[name]
                
                if not task.enabled:
                    self.logger.info(f"Task '{name}' is already disabled")
                    return True
                
                task.enabled = False
                
                # Cancel scheduled job
                if task.schedule_job:
                    schedule.cancel_job(task.schedule_job)
                    task.schedule_job = None
                
                task.next_run = None
                
                self.logger.info(f"Disabled task '{name}'")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to disable task '{name}': {str(e)}")
            return False
    
    def start(self) -> bool:
        """
        Start the task scheduler.
        
        Returns:
            True if scheduler started successfully, False otherwise
        """
        try:
            if self._running:
                self.logger.warning("Scheduler is already running")
                return True
            
            self.logger.info("Starting task scheduler...")
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Schedule all enabled tasks
            with self._task_lock:
                for task in self._tasks.values():
                    if task.enabled:
                        task.schedule_job = schedule.every(task.interval).seconds.do(
                            self._execute_task_wrapper, task
                        )
                        task.next_run = datetime.now() + timedelta(seconds=task.interval)
            
            # Start scheduler thread
            self._running = True
            self._shutdown_requested = False
            self._shutdown_event.clear()
            self._start_time = datetime.now()
            
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="TaskScheduler",
                daemon=False
            )
            self._scheduler_thread.start()
            
            self.logger.info(f"Task scheduler started with {len([t for t in self._tasks.values() if t.enabled])} enabled tasks")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {str(e)}")
            self._running = False
            return False
    
    def stop(self, timeout: int = 30) -> bool:
        """
        Stop the task scheduler gracefully.
        
        Args:
            timeout: Maximum time to wait for shutdown in seconds
            
        Returns:
            True if scheduler stopped successfully, False otherwise
        """
        try:
            if not self._running:
                self.logger.info("Scheduler is not running")
                return True
            
            self.logger.info("Stopping task scheduler...")
            
            # Request shutdown
            self._shutdown_requested = True
            self._shutdown_event.set()
            
            # Wait for scheduler thread to finish
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=timeout)
                
                if self._scheduler_thread.is_alive():
                    self.logger.warning(f"Scheduler thread did not stop within {timeout}s timeout")
                    return False
            
            # Clear all scheduled jobs
            schedule.clear()
            
            # Reset task schedule jobs
            with self._task_lock:
                for task in self._tasks.values():
                    task.schedule_job = None
                    task.next_run = None
            
            # Restore signal handlers
            self._restore_signal_handlers()
            
            self._running = False
            
            # Log final statistics
            uptime = datetime.now() - self._start_time if self._start_time else timedelta(0)
            self.logger.info(
                f"Task scheduler stopped. Uptime: {uptime}, "
                f"Total executions: {self._total_executions}, "
                f"Success rate: {self._successful_executions / max(1, self._total_executions) * 100:.1f}%"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {str(e)}")
            return False
    
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running and not self._shutdown_requested
    
    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific task.
        
        Args:
            name: Name of the task
            
        Returns:
            Dictionary with task status or None if task not found
        """
        with self._task_lock:
            if name not in self._tasks:
                return None
            
            task = self._tasks[name]
            return {
                'name': task.name,
                'enabled': task.enabled,
                'interval': task.interval,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'run_count': task.run_count
            }
    
    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """
        Get status information for all tasks.
        
        Returns:
            List of dictionaries with task status information
        """
        with self._task_lock:
            return [
                {
                    'name': task.name,
                    'enabled': task.enabled,
                    'interval': task.interval,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'run_count': task.run_count
                }
                for task in self._tasks.values()
            ]
    
    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """
        Get scheduler statistics.
        
        Returns:
            Dictionary with scheduler statistics
        """
        uptime = datetime.now() - self._start_time if self._start_time else timedelta(0)
        
        return {
            'running': self._running,
            'uptime_seconds': uptime.total_seconds(),
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'total_tasks': len(self._tasks),
            'enabled_tasks': len([t for t in self._tasks.values() if t.enabled]),
            'total_executions': self._total_executions,
            'successful_executions': self._successful_executions,
            'failed_executions': self._failed_executions,
            'success_rate': self._successful_executions / max(1, self._total_executions) * 100
        }
    
    def run_task_now(self, name: str) -> bool:
        """
        Execute a task immediately (outside of its schedule).
        
        Args:
            name: Name of the task to run
            
        Returns:
            True if task executed successfully, False otherwise
        """
        try:
            with self._task_lock:
                if name not in self._tasks:
                    self.logger.warning(f"Task '{name}' not found")
                    return False
                
                task = self._tasks[name]
            
            self.logger.info(f"Running task '{name}' manually")
            return self._execute_task_wrapper(task, manual=True)
            
        except Exception as e:
            self.logger.error(f"Failed to run task '{name}' manually: {str(e)}")
            return False
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop that runs in a separate thread."""
        self.logger.info("Scheduler loop started")
        
        try:
            while not self._shutdown_requested:
                try:
                    # Run pending scheduled jobs
                    schedule.run_pending()
                    
                    # Sleep for a short interval to avoid busy waiting
                    # Use shutdown event for interruptible sleep
                    if self._shutdown_event.wait(timeout=1.0):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {str(e)}")
                    # Continue running even if there's an error
                    time.sleep(1.0)
            
        except Exception as e:
            self.logger.error(f"Critical error in scheduler loop: {str(e)}")
        finally:
            self.logger.info("Scheduler loop ended")
    
    def _execute_task_wrapper(self, task: ScheduledTask, manual: bool = False) -> bool:
        """
        Wrapper for task execution with error handling and statistics.
        
        Args:
            task: Task to execute
            manual: Whether this is a manual execution
            
        Returns:
            True if task executed successfully, False otherwise
        """
        start_time = datetime.now()
        
        try:
            if not manual and not task.enabled:
                self.logger.debug(f"Skipping disabled task '{task.name}'")
                return False
            
            self.logger.info(f"Executing task '{task.name}' (manual: {manual})")
            
            # Update statistics
            self._total_executions += 1
            task.run_count += 1
            task.last_run = start_time
            
            # Execute the task function
            result = task.job_func()
            
            # Update next run time for scheduled tasks
            if not manual and task.enabled:
                task.next_run = datetime.now() + timedelta(seconds=task.interval)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Consider task successful if it doesn't raise an exception
            # and returns a truthy value (or None)
            success = result is not False
            
            if success:
                self._successful_executions += 1
                self.logger.info(f"Task '{task.name}' completed successfully in {execution_time:.2f}s")
            else:
                self._failed_executions += 1
                self.logger.warning(f"Task '{task.name}' returned failure in {execution_time:.2f}s")
            
            return success
            
        except Exception as e:
            self._failed_executions += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.error(
                f"Task '{task.name}' failed after {execution_time:.2f}s: {str(e)}",
                exc_info=True
            )
            return False
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            # Store original handlers
            self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
            self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.debug("Signal handlers setup for graceful shutdown")
            
        except Exception as e:
            self.logger.warning(f"Failed to setup signal handlers: {str(e)}")
    
    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        try:
            if self._original_sigint_handler:
                signal.signal(signal.SIGINT, self._original_sigint_handler)
            
            if self._original_sigterm_handler:
                signal.signal(signal.SIGTERM, self._original_sigterm_handler)
            
            self.logger.debug("Original signal handlers restored")
            
        except Exception as e:
            self.logger.warning(f"Failed to restore signal handlers: {str(e)}")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        
        # Request shutdown
        self._shutdown_requested = True
        self._shutdown_event.set()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


if __name__ == "__main__":
    # Simple test
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    def test_task():
        print(f"Test task executed at {datetime.now()}")
        return True
    
    scheduler = TaskScheduler()
    scheduler.add_task("test", test_task, 5)
    
    print("Starting scheduler for 15 seconds...")
    scheduler.start()
    time.sleep(15)
    scheduler.stop()
    
    print("Scheduler statistics:", scheduler.get_scheduler_statistics())