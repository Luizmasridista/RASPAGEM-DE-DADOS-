"""
Unit tests for the TaskScheduler class.
"""
import time
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.task_scheduler import TaskScheduler, ScheduledTask
from models.data_models import SystemConfig


class TestTaskScheduler:
    """Test cases for TaskScheduler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.system_config = SystemConfig()
        self.scheduler = TaskScheduler(self.system_config)
        self.test_task_called = False
        self.test_task_call_count = 0
    
    def teardown_method(self):
        """Cleanup after tests."""
        if self.scheduler.is_running():
            self.scheduler.stop()
    
    def test_task_func(self):
        """Test task function for unit tests."""
        self.test_task_called = True
        self.test_task_call_count += 1
        return True
    
    def failing_task_func(self):
        """Test task that always fails."""
        raise Exception("Test task failure")
    
    def test_false_returning_task(self):
        """Test task that returns False."""
        return False
    
    def test_init(self):
        """Test TaskScheduler initialization."""
        scheduler = TaskScheduler()
        assert not scheduler.is_running()
        assert len(scheduler._tasks) == 0
        assert scheduler._total_executions == 0
        
        # Test with system config
        config = SystemConfig(intervalo_execucao=300)
        scheduler_with_config = TaskScheduler(config)
        assert scheduler_with_config.system_config.intervalo_execucao == 300
    
    def test_add_task(self):
        """Test adding tasks to scheduler."""
        # Test adding a task
        result = self.scheduler.add_task("test_task", self.test_task_func, 10)
        assert result is True
        assert "test_task" in self.scheduler._tasks
        
        task = self.scheduler._tasks["test_task"]
        assert task.name == "test_task"
        assert task.interval == 10
        assert task.enabled is True
        assert task.run_count == 0
        
        # Test adding duplicate task (should update)
        result = self.scheduler.add_task("test_task", self.test_task_func, 20)
        assert result is True
        assert self.scheduler._tasks["test_task"].interval == 20
    
    def test_add_disabled_task(self):
        """Test adding a disabled task."""
        result = self.scheduler.add_task("disabled_task", self.test_task_func, 10, enabled=False)
        assert result is True
        
        task = self.scheduler._tasks["disabled_task"]
        assert task.enabled is False
        assert task.schedule_job is None
    
    def test_remove_task(self):
        """Test removing tasks from scheduler."""
        # Add a task first
        self.scheduler.add_task("test_task", self.test_task_func, 10)
        assert "test_task" in self.scheduler._tasks
        
        # Remove the task
        result = self.scheduler.remove_task("test_task")
        assert result is True
        assert "test_task" not in self.scheduler._tasks
        
        # Try to remove non-existent task
        result = self.scheduler.remove_task("non_existent")
        assert result is False
    
    def test_enable_disable_task(self):
        """Test enabling and disabling tasks."""
        # Add a disabled task
        self.scheduler.add_task("test_task", self.test_task_func, 10, enabled=False)
        task = self.scheduler._tasks["test_task"]
        assert task.enabled is False
        
        # Enable the task
        result = self.scheduler.enable_task("test_task")
        assert result is True
        assert task.enabled is True
        
        # Enable already enabled task
        result = self.scheduler.enable_task("test_task")
        assert result is True
        
        # Disable the task
        result = self.scheduler.disable_task("test_task")
        assert result is True
        assert task.enabled is False
        
        # Disable already disabled task
        result = self.scheduler.disable_task("test_task")
        assert result is True
        
        # Try to enable/disable non-existent task
        assert self.scheduler.enable_task("non_existent") is False
        assert self.scheduler.disable_task("non_existent") is False
    
    def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler."""
        # Test start
        result = self.scheduler.start()
        assert result is True
        assert self.scheduler.is_running()
        assert self.scheduler._scheduler_thread is not None
        assert self.scheduler._scheduler_thread.is_alive()
        
        # Test start when already running
        result = self.scheduler.start()
        assert result is True
        
        # Test stop
        result = self.scheduler.stop()
        assert result is True
        assert not self.scheduler.is_running()
        
        # Test stop when not running
        result = self.scheduler.stop()
        assert result is True
    
    def test_task_execution(self):
        """Test that tasks are executed correctly."""
        # Add a task
        self.scheduler.add_task("test_task", self.test_task_func, 1)  # 1 second interval
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait for task to execute
        time.sleep(2.5)  # Wait for at least 2 executions
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Check that task was executed
        assert self.test_task_called is True
        assert self.test_task_call_count >= 2
        
        # Check task statistics
        task = self.scheduler._tasks["test_task"]
        assert task.run_count >= 2
        assert task.last_run is not None
    
    def test_manual_task_execution(self):
        """Test manual task execution."""
        # Add a task
        self.scheduler.add_task("test_task", self.test_task_func, 60)  # Long interval
        
        # Run task manually
        result = self.scheduler.run_task_now("test_task")
        assert result is True
        assert self.test_task_called is True
        assert self.test_task_call_count == 1
        
        # Try to run non-existent task
        result = self.scheduler.run_task_now("non_existent")
        assert result is False
    
    def test_task_failure_handling(self):
        """Test handling of task failures."""
        # Add a failing task
        self.scheduler.add_task("failing_task", self.failing_task_func, 1)
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait for task to execute and fail
        time.sleep(2.5)
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Check statistics
        stats = self.scheduler.get_scheduler_statistics()
        assert stats['failed_executions'] > 0
        assert stats['success_rate'] < 100
    
    def test_task_returning_false(self):
        """Test handling of tasks that return False."""
        # Add a task that returns False
        self.scheduler.add_task("false_task", self.test_false_returning_task, 1)
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait for task to execute
        time.sleep(2.5)
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Check statistics
        stats = self.scheduler.get_scheduler_statistics()
        assert stats['failed_executions'] > 0
    
    def test_get_task_status(self):
        """Test getting task status."""
        # Test non-existent task
        status = self.scheduler.get_task_status("non_existent")
        assert status is None
        
        # Add a task
        self.scheduler.add_task("test_task", self.test_task_func, 30)
        
        # Get task status
        status = self.scheduler.get_task_status("test_task")
        assert status is not None
        assert status['name'] == "test_task"
        assert status['enabled'] is True
        assert status['interval'] == 30
        assert status['run_count'] == 0
        assert status['last_run'] is None
        
        # Run task manually and check status again
        self.scheduler.run_task_now("test_task")
        status = self.scheduler.get_task_status("test_task")
        assert status['run_count'] == 1
        assert status['last_run'] is not None
    
    def test_get_all_tasks_status(self):
        """Test getting status of all tasks."""
        # Initially no tasks
        all_status = self.scheduler.get_all_tasks_status()
        assert len(all_status) == 0
        
        # Add some tasks
        self.scheduler.add_task("task1", self.test_task_func, 10)
        self.scheduler.add_task("task2", self.test_task_func, 20, enabled=False)
        
        # Get all tasks status
        all_status = self.scheduler.get_all_tasks_status()
        assert len(all_status) == 2
        
        # Check task details
        task_names = [status['name'] for status in all_status]
        assert "task1" in task_names
        assert "task2" in task_names
        
        # Find specific tasks
        task1_status = next(s for s in all_status if s['name'] == 'task1')
        task2_status = next(s for s in all_status if s['name'] == 'task2')
        
        assert task1_status['enabled'] is True
        assert task2_status['enabled'] is False
    
    def test_get_scheduler_statistics(self):
        """Test getting scheduler statistics."""
        # Initial statistics
        stats = self.scheduler.get_scheduler_statistics()
        assert stats['running'] is False
        assert stats['total_tasks'] == 0
        assert stats['enabled_tasks'] == 0
        assert stats['total_executions'] == 0
        assert stats['start_time'] is None
        
        # Add tasks and start scheduler
        self.scheduler.add_task("task1", self.test_task_func, 10)
        self.scheduler.add_task("task2", self.test_task_func, 20, enabled=False)
        self.scheduler.start()
        
        # Check statistics after starting
        stats = self.scheduler.get_scheduler_statistics()
        assert stats['running'] is True
        assert stats['total_tasks'] == 2
        assert stats['enabled_tasks'] == 1
        assert stats['start_time'] is not None
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Check final statistics
        stats = self.scheduler.get_scheduler_statistics()
        assert stats['running'] is False
    
    def test_context_manager(self):
        """Test using scheduler as context manager."""
        self.scheduler.add_task("test_task", self.test_task_func, 1)
        
        with self.scheduler:
            assert self.scheduler.is_running()
            time.sleep(1.5)  # Let task execute once
        
        assert not self.scheduler.is_running()
        assert self.test_task_called is True
    
    @patch('signal.signal')
    def test_signal_handlers(self, mock_signal):
        """Test signal handler setup and restoration."""
        # Start scheduler (should setup signal handlers)
        self.scheduler.start()
        
        # Check that signal handlers were setup
        assert mock_signal.call_count >= 2  # SIGINT and SIGTERM
        
        # Stop scheduler (should restore signal handlers)
        self.scheduler.stop()
        
        # Signal should be called again to restore handlers
        assert mock_signal.call_count >= 4
    
    def test_graceful_shutdown_timeout(self):
        """Test graceful shutdown with timeout."""
        # Create a long-running task
        def long_task():
            time.sleep(5)  # Simulate long-running task
            return True
        
        self.scheduler.add_task("long_task", long_task, 1)
        self.scheduler.start()
        
        # Stop with short timeout
        start_time = time.time()
        result = self.scheduler.stop(timeout=2)
        stop_time = time.time()
        
        # Should timeout and return False
        assert result is False or (stop_time - start_time) < 3  # Allow some margin
    
    def test_disabled_task_not_scheduled(self):
        """Test that disabled tasks are not scheduled."""
        # Add disabled task
        self.scheduler.add_task("disabled_task", self.test_task_func, 1, enabled=False)
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait
        time.sleep(2.5)
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Task should not have been called
        assert self.test_task_called is False
        assert self.test_task_call_count == 0
    
    def test_task_enable_while_running(self):
        """Test enabling a task while scheduler is running."""
        # Add disabled task
        self.scheduler.add_task("test_task", self.test_task_func, 1, enabled=False)
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait a bit
        time.sleep(1.5)
        
        # Task should not have been called yet
        assert self.test_task_called is False
        
        # Enable the task
        self.scheduler.enable_task("test_task")
        
        # Wait for task to execute
        time.sleep(2.5)
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Task should have been called after enabling
        assert self.test_task_called is True
    
    def test_task_disable_while_running(self):
        """Test disabling a task while scheduler is running."""
        # Add enabled task
        self.scheduler.add_task("test_task", self.test_task_func, 1)
        
        # Start scheduler
        self.scheduler.start()
        
        # Wait for task to execute once
        time.sleep(1.5)
        
        # Reset counter
        initial_count = self.test_task_call_count
        
        # Disable the task
        self.scheduler.disable_task("test_task")
        
        # Wait more
        time.sleep(2.5)
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Task should not have been called after disabling
        assert self.test_task_call_count == initial_count


class TestScheduledTask:
    """Test cases for ScheduledTask dataclass."""
    
    def test_scheduled_task_creation(self):
        """Test creating a ScheduledTask."""
        def dummy_func():
            return True
        
        task = ScheduledTask(
            name="test_task",
            job_func=dummy_func,
            interval=60
        )
        
        assert task.name == "test_task"
        assert task.job_func == dummy_func
        assert task.interval == 60
        assert task.next_run is None
        assert task.last_run is None
        assert task.run_count == 0
        assert task.enabled is True
        assert task.schedule_job is None
    
    def test_scheduled_task_with_custom_values(self):
        """Test creating a ScheduledTask with custom values."""
        def dummy_func():
            return True
        
        now = datetime.now()
        
        task = ScheduledTask(
            name="custom_task",
            job_func=dummy_func,
            interval=30,
            next_run=now,
            last_run=now,
            run_count=5,
            enabled=False
        )
        
        assert task.name == "custom_task"
        assert task.interval == 30
        assert task.next_run == now
        assert task.last_run == now
        assert task.run_count == 5
        assert task.enabled is False


if __name__ == "__main__":
    pytest.main([__file__])