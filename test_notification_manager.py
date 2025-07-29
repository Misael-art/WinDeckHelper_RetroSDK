#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for the NotificationManager
Tests structured notifications, progress tracking, and operation history
"""

import unittest
import tempfile
import shutil
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Import the notification manager
from env_dev.core.notification_manager import (
    NotificationManager, NotificationSeverity, OperationCategory, OperationStatus,
    StructuredNotification, OperationRecord,
    initialize_notification_manager, get_notification_manager, shutdown_notification_manager
)

class TestNotificationManager(unittest.TestCase):
    """Test cases for NotificationManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Create notification manager without GUI
        self.manager = NotificationManager(
            gui_parent=None,
            log_dir=str(self.log_dir),
            enable_gui_notifications=False,
            enable_file_logging=True,
            max_history_size=100
        )
        
        # Give processing thread time to start
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'manager'):
            self.manager.stop_processing()
        
        # Clean up temp directory
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_notification(self):
        """Test basic notification creation and storage"""
        # Send a basic notification
        notification_id = self.manager.notify(
            NotificationSeverity.INFO,
            OperationCategory.SYSTEM,
            "Test Notification",
            "This is a test message"
        )
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify notification was stored
        self.assertIn(notification_id, self.manager.notifications)
        notification = self.manager.notifications[notification_id]
        
        self.assertEqual(notification.severity, NotificationSeverity.INFO)
        self.assertEqual(notification.category, OperationCategory.SYSTEM)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test message")
        self.assertIsInstance(notification.timestamp, datetime)
    
    def test_notification_with_details(self):
        """Test notification with additional details and context"""
        details = {"component": "test_component", "version": "1.0.0"}
        context = {"user": "test_user", "session": "test_session"}
        tags = ["test", "unit_test"]
        
        notification_id = self.manager.notify(
            NotificationSeverity.SUCCESS,
            OperationCategory.INSTALLATION,
            "Installation Complete",
            "Component installed successfully",
            component="test_component",
            details=details,
            context=context,
            tags=tags
        )
        
        time.sleep(0.2)
        
        notification = self.manager.notifications[notification_id]
        self.assertEqual(notification.component, "test_component")
        self.assertEqual(notification.details, details)
        self.assertEqual(notification.context, context)
        self.assertEqual(notification.tags, tags)
    
    def test_operation_tracking(self):
        """Test complete operation tracking lifecycle"""
        # Start operation
        operation_id = self.manager.start_operation(
            OperationCategory.DOWNLOAD,
            "Download Test File",
            "Downloading test file for unit test",
            total_steps=5
        )
        
        time.sleep(0.1)
        
        # Verify operation was created
        self.assertIn(operation_id, self.manager.operations)
        operation = self.manager.operations[operation_id]
        
        self.assertEqual(operation.category, OperationCategory.DOWNLOAD)
        self.assertEqual(operation.name, "Download Test File")
        self.assertEqual(operation.status, OperationStatus.RUNNING)
        self.assertEqual(operation.total_steps, 5)
        
        # Update progress
        self.manager.update_operation_progress(
            operation_id, 
            2, 
            "Downloading chunk 2 of 5"
        )
        
        time.sleep(0.1)
        
        operation = self.manager.operations[operation_id]
        self.assertEqual(operation.current_step, 2)
        self.assertEqual(operation.progress, 40.0)  # 2/5 * 100
        self.assertIn(2, operation.step_descriptions)
        
        # Complete operation successfully
        self.manager.complete_operation(
            operation_id,
            success=True,
            result_message="File downloaded successfully",
            result_data={"file_size": 1024, "checksum": "abc123"}
        )
        
        time.sleep(0.1)
        
        # Verify operation was moved to history
        self.assertNotIn(operation_id, self.manager.operations)
        
        # Find in history
        completed_ops = [op for op in self.manager.operation_history if op.operation_id == operation_id]
        self.assertEqual(len(completed_ops), 1)
        
        completed_op = completed_ops[0]
        self.assertEqual(completed_op.status, OperationStatus.COMPLETED)
        self.assertEqual(completed_op.progress, 100.0)
        self.assertIsNotNone(completed_op.end_time)
        self.assertIsNotNone(completed_op.duration)
        self.assertEqual(completed_op.result_data["file_size"], 1024)
    
    def test_operation_failure(self):
        """Test operation failure handling"""
        operation_id = self.manager.start_operation(
            OperationCategory.INSTALLATION,
            "Install Failed Component",
            "Installing component that will fail",
            total_steps=3
        )
        
        time.sleep(0.1)
        
        # Fail the operation
        self.manager.complete_operation(
            operation_id,
            success=False,
            error_message="Installation failed due to missing dependencies"
        )
        
        time.sleep(0.1)
        
        # Verify operation was marked as failed
        failed_ops = [op for op in self.manager.operation_history if op.operation_id == operation_id]
        self.assertEqual(len(failed_ops), 1)
        
        failed_op = failed_ops[0]
        self.assertEqual(failed_op.status, OperationStatus.FAILED)
        self.assertEqual(failed_op.error_message, "Installation failed due to missing dependencies")
    
    def test_operation_cancellation(self):
        """Test operation cancellation"""
        operation_id = self.manager.start_operation(
            OperationCategory.CLEANUP,
            "Cleanup Operation",
            "Cleaning up temporary files"
        )
        
        time.sleep(0.1)
        
        # Cancel the operation
        self.manager.cancel_operation(operation_id, "User requested cancellation")
        
        time.sleep(0.1)
        
        # Verify operation was cancelled
        cancelled_ops = [op for op in self.manager.operation_history if op.operation_id == operation_id]
        self.assertEqual(len(cancelled_ops), 1)
        
        cancelled_op = cancelled_ops[0]
        self.assertEqual(cancelled_op.status, OperationStatus.CANCELLED)
        self.assertEqual(cancelled_op.error_message, "User requested cancellation")
    
    def test_convenience_methods(self):
        """Test convenience methods for common notification types"""
        # Test info
        info_id = self.manager.info("Info Title", "Info message")
        time.sleep(0.1)
        info_notification = self.manager.notifications[info_id]
        self.assertEqual(info_notification.severity, NotificationSeverity.INFO)
        
        # Test success
        success_id = self.manager.success("Success Title", "Success message")
        time.sleep(0.1)
        success_notification = self.manager.notifications[success_id]
        self.assertEqual(success_notification.severity, NotificationSeverity.SUCCESS)
        
        # Test warning
        warning_id = self.manager.warning("Warning Title", "Warning message")
        time.sleep(0.1)
        warning_notification = self.manager.notifications[warning_id]
        self.assertEqual(warning_notification.severity, NotificationSeverity.WARNING)
        
        # Test error
        error_id = self.manager.error("Error Title", "Error message")
        time.sleep(0.1)
        error_notification = self.manager.notifications[error_id]
        self.assertEqual(error_notification.severity, NotificationSeverity.ERROR)
        
        # Test critical
        critical_id = self.manager.critical("Critical Title", "Critical message")
        time.sleep(0.1)
        critical_notification = self.manager.notifications[critical_id]
        self.assertEqual(critical_notification.severity, NotificationSeverity.CRITICAL)
    
    def test_notification_filtering(self):
        """Test notification filtering and querying"""
        # Create notifications with different properties
        self.manager.notify(
            NotificationSeverity.INFO,
            OperationCategory.SYSTEM,
            "System Info",
            "System message",
            component="system_component",
            tags=["system", "info"]
        )
        
        self.manager.notify(
            NotificationSeverity.ERROR,
            OperationCategory.INSTALLATION,
            "Install Error",
            "Installation failed",
            component="install_component",
            tags=["installation", "error"]
        )
        
        self.manager.notify(
            NotificationSeverity.SUCCESS,
            OperationCategory.SYSTEM,
            "System Success",
            "System operation completed",
            component="system_component",
            tags=["system", "success"]
        )
        
        time.sleep(0.2)
        
        # Test filtering by severity
        error_notifications = self.manager.get_notifications(severity=NotificationSeverity.ERROR)
        self.assertEqual(len(error_notifications), 1)
        self.assertEqual(error_notifications[0].title, "Install Error")
        
        # Test filtering by category
        system_notifications = self.manager.get_notifications(category=OperationCategory.SYSTEM)
        self.assertEqual(len(system_notifications), 2)
        
        # Test filtering by component
        system_component_notifications = self.manager.get_notifications(component="system_component")
        self.assertEqual(len(system_component_notifications), 2)
        
        # Test filtering by tags
        system_tag_notifications = self.manager.get_notifications(tags=["system"])
        self.assertEqual(len(system_tag_notifications), 2)
    
    def test_statistics(self):
        """Test statistics tracking"""
        # Create various notifications
        self.manager.info("Info 1", "Message 1")
        self.manager.info("Info 2", "Message 2")
        self.manager.error("Error 1", "Error message")
        self.manager.success("Success 1", "Success message")
        
        # Create and complete operations
        op1_id = self.manager.start_operation(
            OperationCategory.DOWNLOAD,
            "Download 1",
            "First download"
        )
        
        op2_id = self.manager.start_operation(
            OperationCategory.INSTALLATION,
            "Install 1",
            "First installation"
        )
        
        time.sleep(0.1)
        
        self.manager.complete_operation(op1_id, success=True)
        self.manager.complete_operation(op2_id, success=False, error_message="Failed")
        
        time.sleep(0.1)
        
        # Check statistics
        stats = self.manager.get_statistics()
        
        self.assertGreaterEqual(stats['total_notifications'], 4)
        self.assertGreaterEqual(stats['notifications_by_severity']['info'], 2)
        self.assertGreaterEqual(stats['notifications_by_severity']['error'], 1)
        self.assertGreaterEqual(stats['notifications_by_severity']['success'], 1)
        self.assertEqual(stats['operations_completed'], 1)
        self.assertEqual(stats['operations_failed'], 1)
    
    def test_history_export(self):
        """Test history export functionality"""
        # Create some notifications and operations
        self.manager.info("Export Test", "Test notification for export")
        
        op_id = self.manager.start_operation(
            OperationCategory.SYSTEM,
            "Export Test Operation",
            "Test operation for export"
        )
        
        time.sleep(0.1)
        self.manager.complete_operation(op_id, success=True)
        time.sleep(0.1)
        
        # Export history
        export_file = Path(self.temp_dir) / "export_test.json"
        self.manager.export_history(str(export_file))
        
        # Verify export file was created
        self.assertTrue(export_file.exists())
        
        # Load and verify export data
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        self.assertIn('export_timestamp', export_data)
        self.assertIn('statistics', export_data)
        self.assertIn('notifications', export_data)
        self.assertIn('operations', export_data)
        
        # Verify data content
        self.assertGreater(len(export_data['notifications']), 0)
        self.assertGreater(len(export_data['operations']), 0)
    
    def test_history_clearing(self):
        """Test history clearing functionality"""
        # Create some notifications
        self.manager.info("Clear Test 1", "Message 1")
        self.manager.info("Clear Test 2", "Message 2")
        
        time.sleep(0.1)
        
        initial_count = len(self.manager.notification_history)
        self.assertGreater(initial_count, 0)
        
        # Clear history
        self.manager.clear_history()
        
        # Verify history was cleared
        self.assertEqual(len(self.manager.notification_history), 0)
        self.assertEqual(len(self.manager.operation_history), 0)
    
    def test_concurrent_notifications(self):
        """Test handling of concurrent notifications"""
        def send_notifications(thread_id, count):
            for i in range(count):
                self.manager.notify(
                    NotificationSeverity.INFO,
                    OperationCategory.SYSTEM,
                    f"Thread {thread_id} Notification {i}",
                    f"Message from thread {thread_id}, notification {i}"
                )
        
        # Create multiple threads sending notifications
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=send_notifications, args=(thread_id, 5))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify all notifications were processed
        self.assertGreaterEqual(len(self.manager.notification_history), 15)
    
    def test_global_manager_functions(self):
        """Test global notification manager functions"""
        # Initialize global manager
        global_manager = initialize_notification_manager(
            gui_parent=None,
            enable_gui_notifications=False,
            log_dir=str(self.log_dir)
        )
        
        # Verify it's the same instance when called again
        same_manager = initialize_notification_manager()
        self.assertIs(global_manager, same_manager)
        
        # Test get function
        retrieved_manager = get_notification_manager()
        self.assertIs(global_manager, retrieved_manager)
        
        # Test functionality
        retrieved_manager.info("Global Test", "Testing global manager")
        time.sleep(0.1)
        
        self.assertGreater(len(retrieved_manager.notification_history), 0)
        
        # Shutdown
        shutdown_notification_manager()
        
        # Verify manager was cleared
        self.assertIsNone(get_notification_manager())

class TestNotificationManagerIntegration(unittest.TestCase):
    """Integration tests for NotificationManager with other components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.manager = NotificationManager(
            gui_parent=None,
            log_dir=str(self.log_dir),
            enable_gui_notifications=False,
            enable_file_logging=True
        )
        
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up integration test environment"""
        if hasattr(self, 'manager'):
            self.manager.stop_processing()
        
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_file_creation(self):
        """Test that log files are created and contain notifications"""
        # Send a notification
        self.manager.error("Log Test", "This should appear in the log file")
        
        time.sleep(0.2)
        
        # Check if log file was created
        log_files = list(self.log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)
        
        # Check if notification appears in log
        log_content = ""
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content += f.read()
        
        self.assertIn("Log Test", log_content)
        self.assertIn("This should appear in the log file", log_content)
    
    def test_complex_operation_workflow(self):
        """Test a complex operation workflow with multiple steps"""
        # Simulate a complex installation process
        operation_id = self.manager.start_operation(
            OperationCategory.INSTALLATION,
            "Complex Installation",
            "Installing complex software package",
            total_steps=10
        )
        
        time.sleep(0.1)
        
        # Simulate installation steps
        steps = [
            "Checking system requirements",
            "Downloading package",
            "Verifying checksums",
            "Extracting files",
            "Installing dependencies",
            "Configuring application",
            "Creating shortcuts",
            "Registering services",
            "Running post-install scripts",
            "Finalizing installation"
        ]
        
        for i, step_desc in enumerate(steps, 1):
            self.manager.update_operation_progress(
                operation_id,
                i,
                step_desc
            )
            time.sleep(0.05)  # Simulate work
        
        # Complete the operation
        self.manager.complete_operation(
            operation_id,
            success=True,
            result_message="Complex installation completed successfully",
            result_data={
                "installed_files": 150,
                "installation_size": "45.2 MB",
                "installation_time": "2.5 minutes"
            }
        )
        
        time.sleep(0.1)
        
        # Verify the operation was completed properly
        completed_ops = [op for op in self.manager.operation_history 
                        if op.operation_id == operation_id]
        self.assertEqual(len(completed_ops), 1)
        
        completed_op = completed_ops[0]
        self.assertEqual(completed_op.status, OperationStatus.COMPLETED)
        self.assertEqual(completed_op.progress, 100.0)
        self.assertEqual(completed_op.current_step, 10)
        self.assertEqual(len(completed_op.step_descriptions), 10)
        self.assertIn("installed_files", completed_op.result_data)
        
        # Verify notifications were created for each step
        operation_notifications = self.manager.get_notifications(operation_id=operation_id)
        self.assertGreaterEqual(len(operation_notifications), 10)  # At least one per step

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)