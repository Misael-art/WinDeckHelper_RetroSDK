#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for AdvancedLogging
Tests organized logging, searchable logs, automatic report generation, and performance metrics
"""

import unittest
import tempfile
import shutil
import json
import sqlite3
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from env_dev.core.advanced_logging import (
    AdvancedLogger, LogLevel, LogCategory, LogEntry, PerformanceMetrics,
    LogSearchResult, LogReport, LogAnalytics
)


class TestAdvancedLogger(unittest.TestCase):
    """Unit tests for AdvancedLogger"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_dir = self.temp_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create advanced logger
        self.logger = AdvancedLogger(
            log_dir=str(self.log_dir),
            enable_database=True,
            enable_performance_tracking=True,
            max_log_size=1024 * 1024,  # 1MB
            max_log_files=5
        )
        
        # Give logger time to initialize
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'logger'):
            self.logger.shutdown()
        
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_logging(self):
        """Test basic logging functionality (Requirement 7.2)"""
        # Log messages at different levels
        self.logger.info("Test info message", category=LogCategory.APPLICATION)
        self.logger.warning("Test warning message", category=LogCategory.SYSTEM)
        self.logger.error("Test error message", category=LogCategory.INSTALLATION)
        self.logger.success("Test success message", category=LogCategory.APPLICATION)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify log files were created
        log_files = list(self.log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)
        
        # Verify database entries
        if self.logger.db_connection:
            cursor = self.logger.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM log_entries")
            count = cursor.fetchone()[0]
            self.assertGreaterEqual(count, 4)
    
    def test_structured_logging(self):
        """Test structured logging with metadata (Requirement 7.2)"""
        # Log with structured data
        metadata = {
            'component': 'TestComponent',
            'operation': 'installation',
            'duration': 2.5,
            'files_processed': 15
        }
        
        self.logger.log_structured(
            level=LogLevel.INFO,
            message="Component installation completed",
            category=LogCategory.INSTALLATION,
            metadata=metadata,
            tags=['installation', 'success']
        )
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify structured data was stored
        if self.logger.db_connection:
            cursor = self.logger.db_connection.cursor()
            cursor.execute("""
                SELECT message, metadata, tags FROM log_entries 
                WHERE message LIKE '%installation completed%'
            """)
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertIn('TestComponent', result[1])  # metadata
            self.assertIn('installation', result[2])   # tags
    
    def test_log_search_functionality(self):
        """Test searchable log functionality (Requirement 7.2)"""
        # Create test log entries
        test_entries = [
            ("Installation started for ComponentA", LogCategory.INSTALLATION, ['install', 'start']),
            ("Download completed for ComponentA", LogCategory.DOWNLOAD, ['download', 'complete']),
            ("Installation failed for ComponentB", LogCategory.INSTALLATION, ['install', 'error']),
            ("System diagnostic completed", LogCategory.DIAGNOSTIC, ['diagnostic', 'complete'])
        ]
        
        for message, category, tags in test_entries:
            self.logger.info(message, category=category, tags=tags)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Test text search
        search_result = self.logger.search_logs(query="ComponentA")
        self.assertGreaterEqual(len(search_result.entries), 2)
        
        # Test category filter
        install_result = self.logger.search_logs(category=LogCategory.INSTALLATION)
        self.assertGreaterEqual(len(install_result.entries), 2)
        
        # Test tag filter
        error_result = self.logger.search_logs(tags=['error'])
        self.assertGreaterEqual(len(error_result.entries), 1)
        
        # Test date range filter
        now = datetime.now()
        recent_result = self.logger.search_logs(
            start_date=now - timedelta(minutes=1),
            end_date=now + timedelta(minutes=1)
        )
        self.assertGreaterEqual(len(recent_result.entries), 4)
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics collection (Requirement 7.3)"""
        # Start performance tracking
        operation_id = self.logger.start_performance_tracking("test_operation")
        
        # Simulate some work
        time.sleep(0.1)
        
        # Add performance data
        self.logger.add_performance_data(operation_id, {
            'cpu_usage': 45.2,
            'memory_usage': 128 * 1024 * 1024,  # 128MB
            'disk_io': 1024 * 1024  # 1MB
        })
        
        # End performance tracking
        metrics = self.logger.end_performance_tracking(operation_id)
        
        # Verify metrics
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertEqual(metrics.operation_name, "test_operation")
        self.assertGreater(metrics.duration, 0.05)  # At least 50ms
        self.assertIn('cpu_usage', metrics.custom_metrics)
        self.assertEqual(metrics.custom_metrics['cpu_usage'], 45.2)
    
    def test_automatic_report_generation(self):
        """Test automatic report generation (Requirement 7.2)"""
        # Create diverse log entries for report
        self.logger.info("System started", category=LogCategory.SYSTEM)
        self.logger.success("Component installed", category=LogCategory.INSTALLATION)
        self.logger.warning("Low disk space", category=LogCategory.SYSTEM)
        self.logger.error("Installation failed", category=LogCategory.INSTALLATION)
        self.logger.critical("System crash", category=LogCategory.SYSTEM)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Generate report
        report = self.logger.generate_report(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )
        
        # Verify report
        self.assertIsInstance(report, LogReport)
        self.assertGreater(report.total_entries, 0)
        self.assertIn(LogLevel.INFO, report.level_distribution)
        self.assertIn(LogLevel.ERROR, report.level_distribution)
        self.assertIn(LogCategory.SYSTEM, report.category_distribution)
        self.assertIn(LogCategory.INSTALLATION, report.category_distribution)
        
        # Verify summary statistics
        self.assertGreater(report.error_count, 0)
        self.assertGreater(report.warning_count, 0)
    
    def test_log_rotation(self):
        """Test automatic log rotation"""
        # Configure small log size for testing
        self.logger.max_log_size = 1024  # 1KB
        
        # Generate enough logs to trigger rotation
        large_message = "x" * 200  # 200 character message
        for i in range(10):  # Should exceed 1KB
            self.logger.info(f"Large message {i}: {large_message}")
        
        # Wait for processing and rotation
        time.sleep(0.5)
        
        # Check for rotated log files
        log_files = list(self.log_dir.glob("*.log*"))
        self.assertGreater(len(log_files), 1)  # Should have main log + rotated logs
    
    def test_log_compression(self):
        """Test log compression for old files"""
        # Create old log file
        old_log = self.log_dir / "old_application.log"
        old_log.write_text("Old log content" * 100)
        
        # Set file modification time to be old
        old_time = datetime.now() - timedelta(days=8)
        os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))
        
        # Trigger compression
        self.logger.compress_old_logs(max_age_days=7)
        
        # Verify compression
        compressed_files = list(self.log_dir.glob("*.gz"))
        self.assertGreater(len(compressed_files), 0)
        
        # Verify original file was removed
        self.assertFalse(old_log.exists())
    
    def test_log_analytics(self):
        """Test log analytics functionality (Requirement 7.3)"""
        # Create pattern of log entries
        patterns = [
            ("User login successful", LogCategory.SYSTEM, LogLevel.INFO),
            ("User login failed", LogCategory.SYSTEM, LogLevel.WARNING),
            ("User login successful", LogCategory.SYSTEM, LogLevel.INFO),
            ("Installation started", LogCategory.INSTALLATION, LogLevel.INFO),
            ("Installation failed", LogCategory.INSTALLATION, LogLevel.ERROR),
            ("User login failed", LogCategory.SYSTEM, LogLevel.WARNING),
        ]
        
        for message, category, level in patterns:
            self.logger.log(level, message, category=category)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Generate analytics
        analytics = self.logger.generate_analytics(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )
        
        # Verify analytics
        self.assertIsInstance(analytics, LogAnalytics)
        self.assertGreater(len(analytics.common_patterns), 0)
        self.assertGreater(len(analytics.error_trends), 0)
        
        # Verify pattern detection
        login_patterns = [p for p in analytics.common_patterns if 'login' in p['pattern']]
        self.assertGreater(len(login_patterns), 0)
    
    def test_concurrent_logging(self):
        """Test thread-safe concurrent logging"""
        import threading
        
        def log_worker(worker_id, count):
            for i in range(count):
                self.logger.info(
                    f"Worker {worker_id} message {i}",
                    category=LogCategory.APPLICATION,
                    metadata={'worker_id': worker_id, 'message_num': i}
                )
        
        # Start multiple logging threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=log_worker, args=(worker_id, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify all messages were logged
        if self.logger.db_connection:
            cursor = self.logger.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM log_entries WHERE message LIKE 'Worker%'")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 50)  # 5 workers * 10 messages each
    
    def test_log_export_functionality(self):
        """Test log export to external formats (Requirement 7.4)"""
        # Create test log entries
        self.logger.info("Export test message 1", category=LogCategory.APPLICATION)
        self.logger.error("Export test error", category=LogCategory.SYSTEM)
        self.logger.success("Export test success", category=LogCategory.INSTALLATION)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Test JSON export
        json_file = self.temp_dir / "export.json"
        self.logger.export_logs(
            str(json_file),
            format='json',
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )
        
        # Verify JSON export
        self.assertTrue(json_file.exists())
        with open(json_file, 'r') as f:
            exported_data = json.load(f)
        
        self.assertIsInstance(exported_data, list)
        self.assertGreater(len(exported_data), 0)
        
        # Test CSV export
        csv_file = self.temp_dir / "export.csv"
        self.logger.export_logs(
            str(csv_file),
            format='csv',
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now() + timedelta(hours=1)
        )
        
        # Verify CSV export
        self.assertTrue(csv_file.exists())
        csv_content = csv_file.read_text()
        self.assertIn('timestamp', csv_content)
        self.assertIn('level', csv_content)
        self.assertIn('message', csv_content)
    
    def test_real_time_log_monitoring(self):
        """Test real-time log monitoring capabilities"""
        events_received = []
        
        def log_event_handler(log_entry):
            events_received.append(log_entry)
        
        # Register event handler
        self.logger.register_log_event_handler(log_event_handler)
        
        # Generate log events
        self.logger.info("Real-time test 1")
        self.logger.warning("Real-time test 2")
        self.logger.error("Real-time test 3")
        
        # Wait for event processing
        time.sleep(0.3)
        
        # Verify events were received
        self.assertGreaterEqual(len(events_received), 3)
        
        # Verify event content
        messages = [event.message for event in events_received]
        self.assertIn("Real-time test 1", messages)
        self.assertIn("Real-time test 2", messages)
        self.assertIn("Real-time test 3", messages)
    
    def test_log_filtering_and_masking(self):
        """Test log filtering and sensitive data masking"""
        # Configure sensitive data patterns
        self.logger.configure_data_masking([
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Credit card pattern
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email pattern
        ])
        
        # Log messages with sensitive data
        self.logger.info("User email: user@example.com registered")
        self.logger.info("Payment with card 1234-5678-9012-3456 processed")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify sensitive data was masked
        search_result = self.logger.search_logs(query="User email")
        self.assertGreater(len(search_result.entries), 0)
        
        entry = search_result.entries[0]
        self.assertNotIn("user@example.com", entry.message)
        self.assertIn("***", entry.message)  # Should be masked
    
    def test_log_database_operations(self):
        """Test database operations for log storage"""
        # Test database connection
        self.assertIsNotNone(self.logger.db_connection)
        
        # Test table creation
        cursor = self.logger.db_connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='log_entries'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        
        # Test log insertion
        self.logger.info("Database test message")
        time.sleep(0.2)
        
        # Verify insertion
        cursor.execute("SELECT message FROM log_entries WHERE message = ?", ("Database test message",))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Database test message")
    
    def test_performance_impact_measurement(self):
        """Test measurement of logging performance impact"""
        # Measure logging performance
        start_time = time.time()
        
        # Generate many log entries
        for i in range(1000):
            self.logger.info(f"Performance test message {i}")
        
        end_time = time.time()
        logging_duration = end_time - start_time
        
        # Wait for processing
        time.sleep(1.0)
        
        # Verify performance is acceptable (should be fast)
        self.assertLess(logging_duration, 1.0)  # Should take less than 1 second
        
        # Verify all messages were processed
        if self.logger.db_connection:
            cursor = self.logger.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM log_entries WHERE message LIKE 'Performance test%'")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1000)


class TestAdvancedLoggingIntegration(unittest.TestCase):
    """Integration tests for AdvancedLogging with other components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_dir = self.temp_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = AdvancedLogger(
            log_dir=str(self.log_dir),
            enable_database=True,
            enable_performance_tracking=True
        )
        
        time.sleep(0.1)
    
    def tearDown(self):
        """Clean up integration test environment"""
        if hasattr(self, 'logger'):
            self.logger.shutdown()
        
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_integration_with_notification_manager(self):
        """Test integration with notification manager"""
        # Mock notification manager
        mock_notification_manager = Mock()
        
        # Configure logger to send critical logs to notification manager
        self.logger.register_notification_handler(mock_notification_manager)
        
        # Log critical message
        self.logger.critical("Critical system failure", category=LogCategory.SYSTEM)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify notification was sent
        mock_notification_manager.critical.assert_called_once()
    
    def test_complete_logging_workflow(self):
        """Test complete logging workflow with all features"""
        # Start performance tracking
        perf_id = self.logger.start_performance_tracking("complete_workflow")
        
        # Log various types of messages
        self.logger.info("Workflow started", category=LogCategory.APPLICATION)
        self.logger.debug("Debug information", category=LogCategory.APPLICATION)
        
        # Log with metadata
        self.logger.log_structured(
            LogLevel.INFO,
            "Component processing",
            LogCategory.INSTALLATION,
            metadata={'component': 'TestComponent', 'files': 25},
            tags=['processing', 'installation']
        )
        
        # Simulate some work
        time.sleep(0.1)
        
        # Log success
        self.logger.success("Workflow completed", category=LogCategory.APPLICATION)
        
        # End performance tracking
        metrics = self.logger.end_performance_tracking(perf_id)
        
        # Wait for processing
        time.sleep(0.3)
        
        # Generate comprehensive report
        report = self.logger.generate_report(
            start_date=datetime.now() - timedelta(minutes=1),
            end_date=datetime.now() + timedelta(minutes=1)
        )
        
        # Verify complete workflow
        self.assertGreater(report.total_entries, 0)
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.duration, 0)
        
        # Test search functionality
        search_result = self.logger.search_logs(query="Workflow")
        self.assertGreaterEqual(len(search_result.entries), 2)
        
        # Test analytics
        analytics = self.logger.generate_analytics(
            start_date=datetime.now() - timedelta(minutes=1),
            end_date=datetime.now() + timedelta(minutes=1)
        )
        self.assertIsNotNone(analytics)
        
        # Export logs
        export_file = self.temp_dir / "workflow_export.json"
        self.logger.export_logs(str(export_file), format='json')
        self.assertTrue(export_file.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)