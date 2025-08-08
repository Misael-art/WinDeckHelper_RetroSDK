# -*- coding: utf-8 -*-
"""
Tests for Operation History and Reporting System
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the dependencies before importing
with patch.dict('sys.modules', {
    'core.modern_frontend_manager': Mock(),
    'core.security_manager': Mock(),
    'modern_frontend_manager': Mock(),
    'security_manager': Mock()
}):
    from core.operation_history_reporting_system import (
        OperationHistoryReportingSystem, OperationStatus, ReportFormat,
        TimelineGranularity, OperationRecord, OperationSummary, TimelineEvent,
        ReportExportResult, HistoryTrackingResult
    )


class TestOperationHistoryReportingSystem(unittest.TestCase):
    """Test cases for Operation History and Reporting System"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock dependencies
        self.mock_security_manager = Mock()
        
        # Create system with temporary database
        self.system = OperationHistoryReportingSystem(
            security_manager=self.mock_security_manager,
            database_path=self.temp_db.name,
            max_history_records=100
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.system.shutdown()
        
        # Clean up temporary database
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system.operation_records)
        self.assertIsNotNone(self.system.timeline_events)
        self.assertIsNotNone(self.system.active_operations)
        self.assertEqual(len(self.system.operation_records), 0)
        self.assertEqual(len(self.system.timeline_events), 0)
    
    def test_build_detailed_operation_history_tracking_and_display(self):
        """Test history tracking system setup"""
        result = self.system.build_detailed_operation_history_tracking_and_display()
        
        self.assertIsInstance(result, HistoryTrackingResult)
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.records_tracked, 0)
        self.assertGreaterEqual(result.records_stored, 0)
        self.assertIsNotNone(result.storage_size)
    
    def test_track_operation(self):
        """Test operation tracking"""
        # Create mock operation progress
        mock_progress = Mock()
        mock_progress.operation_id = "test_op_123"
        mock_progress.operation_type = Mock()
        mock_progress.operation_type.value = "installation"
        mock_progress.component_name = "git"
        mock_progress.title = "Installing Git"
        mock_progress.description = "Installing Git version control"
        mock_progress.start_time = datetime.now()
        mock_progress.progress_percentage = 50.0
        mock_progress.current_step = "Downloading"
        mock_progress.total_steps = 3
        mock_progress.current_step_number = 1
        mock_progress.details = ["Starting download"]
        mock_progress.warnings = []
        mock_progress.errors = []
        mock_progress.result = None
        mock_progress.is_completed = False
        mock_progress.is_cancelled = False
        mock_progress.speed = "1.2 MB/s"
        mock_progress.estimated_completion = None
        
        # Track operation
        success = self.system.track_operation(mock_progress)
        
        self.assertTrue(success)
        self.assertIn("test_op_123", self.system.operation_records)
        self.assertIn("test_op_123", self.system.active_operations)
        
        # Check record details
        record = self.system.operation_records["test_op_123"]
        self.assertEqual(record.operation_id, "test_op_123")
        self.assertEqual(record.component_name, "git")
        self.assertEqual(record.title, "Installing Git")
        self.assertEqual(record.progress_percentage, 50.0)
        self.assertEqual(record.status, OperationStatus.RUNNING)
    
    def test_get_operation_history(self):
        """Test operation history retrieval"""
        # Add some test records
        for i in range(5):
            mock_progress = self._create_mock_progress(f"test_op_{i}", f"component_{i}")
            self.system.track_operation(mock_progress)
        
        # Get history
        history = self.system.get_operation_history(limit=3, offset=0)
        
        self.assertEqual(len(history), 3)
        self.assertIsInstance(history[0], OperationRecord)
        
        # Test pagination
        history_page2 = self.system.get_operation_history(limit=3, offset=3)
        self.assertEqual(len(history_page2), 2)
        
        # Test with filters
        filters = {"status": ["running"]}
        filtered_history = self.system.get_operation_history(filters=filters)
        self.assertGreaterEqual(len(filtered_history), 0)
    
    def test_get_operation_summary(self):
        """Test operation summary generation"""
        # Add test records with different statuses
        completed_progress = self._create_mock_progress("completed_op", "git")
        completed_progress.is_completed = True
        completed_progress.progress_percentage = 100.0
        self.system.track_operation(completed_progress)
        
        failed_progress = self._create_mock_progress("failed_op", "python")
        failed_progress.errors = ["Installation failed"]
        failed_progress.progress_percentage = 30.0
        self.system.track_operation(failed_progress)
        
        # Get summary
        summary = self.system.get_operation_summary("24h")
        
        self.assertIsInstance(summary, OperationSummary)
        self.assertGreaterEqual(summary.total_operations, 2)
        self.assertGreaterEqual(summary.completed_operations, 1)
        self.assertGreaterEqual(summary.failed_operations, 1)
        self.assertIsInstance(summary.operations_by_type, dict)
        self.assertIsInstance(summary.operations_by_component, dict)
        self.assertEqual(summary.time_period, "24h")
    
    def test_search_operations(self):
        """Test operation search functionality"""
        # Add test records
        git_progress = self._create_mock_progress("git_op", "git")
        git_progress.title = "Installing Git"
        git_progress.description = "Installing Git version control system"
        self.system.track_operation(git_progress)
        
        python_progress = self._create_mock_progress("python_op", "python")
        python_progress.title = "Installing Python"
        python_progress.description = "Installing Python interpreter"
        self.system.track_operation(python_progress)
        
        # Search by title
        results = self.system.search_operations("Git")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].operation_id, "git_op")
        
        # Search by component
        results = self.system.search_operations("python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].operation_id, "python_op")
        
        # Search by description
        results = self.system.search_operations("version control")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].operation_id, "git_op")
        
        # Search with no results
        results = self.system.search_operations("nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_create_report_export_functionality_json(self):
        """Test JSON report export"""
        # Add test records
        for i in range(3):
            progress = self._create_mock_progress(f"export_test_{i}", f"component_{i}")
            self.system.track_operation(progress)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            output_path = temp_file.name
        
        try:
            # Export to JSON
            result = self.system.create_report_export_functionality_for_troubleshooting(
                ReportFormat.JSON,
                filters={},
                output_path=output_path
            )
            
            self.assertIsInstance(result, ReportExportResult)
            self.assertTrue(result.success)
            self.assertEqual(result.format, ReportFormat.JSON)
            self.assertEqual(result.records_exported, 3)
            self.assertEqual(result.file_path, output_path)
            self.assertGreater(result.file_size, 0)
            
            # Verify file exists and has content
            self.assertTrue(Path(output_path).exists())
            self.assertGreater(Path(output_path).stat().st_size, 0)
            
        finally:
            # Clean up
            try:
                os.unlink(output_path)
            except:
                pass
    
    def test_create_report_export_functionality_csv(self):
        """Test CSV report export"""
        # Add test records
        for i in range(2):
            progress = self._create_mock_progress(f"csv_test_{i}", f"component_{i}")
            self.system.track_operation(progress)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            output_path = temp_file.name
        
        try:
            # Export to CSV
            result = self.system.create_report_export_functionality_for_troubleshooting(
                ReportFormat.CSV,
                output_path=output_path
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.format, ReportFormat.CSV)
            self.assertEqual(result.records_exported, 2)
            
            # Verify file exists
            self.assertTrue(Path(output_path).exists())
            
        finally:
            # Clean up
            try:
                os.unlink(output_path)
            except:
                pass
    
    def test_create_report_export_functionality_html(self):
        """Test HTML report export"""
        # Add test record
        progress = self._create_mock_progress("html_test", "git")
        self.system.track_operation(progress)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
            output_path = temp_file.name
        
        try:
            # Export to HTML
            result = self.system.create_report_export_functionality_for_troubleshooting(
                ReportFormat.HTML,
                output_path=output_path
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.format, ReportFormat.HTML)
            self.assertEqual(result.records_exported, 1)
            
            # Verify file exists and contains HTML
            self.assertTrue(Path(output_path).exists())
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('<html>', content)
                self.assertIn('<table>', content)
            
        finally:
            # Clean up
            try:
                os.unlink(output_path)
            except:
                pass
    
    def test_implement_operation_timeline_visualization(self):
        """Test timeline visualization"""
        # Add test records with different timestamps
        now = datetime.now()
        
        for i in range(3):
            progress = self._create_mock_progress(f"timeline_test_{i}", f"component_{i}")
            progress.start_time = now - timedelta(hours=i)
            self.system.track_operation(progress)
        
        # Generate timeline
        timeline_data = self.system.implement_operation_timeline_visualization(
            time_range=(now - timedelta(days=1), now),
            granularity=TimelineGranularity.HOUR
        )
        
        self.assertIn('timeline', timeline_data)
        self.assertIn('statistics', timeline_data)
        self.assertIn('events', timeline_data)
        self.assertIn('filters', timeline_data)
        
        # Check timeline structure
        timeline = timeline_data['timeline']
        self.assertIn('start_time', timeline)
        self.assertIn('end_time', timeline)
        self.assertIn('granularity', timeline)
        self.assertIn('buckets', timeline)
        self.assertEqual(timeline['granularity'], 'hour')
        
        # Check events
        events = timeline_data['events']
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 0)
        
        # Check statistics
        statistics = timeline_data['statistics']
        self.assertIn('total_operations', statistics)
        self.assertIn('success_rate', statistics)
    
    def test_get_system_report(self):
        """Test system report generation"""
        # Add some test data
        for i in range(3):
            progress = self._create_mock_progress(f"system_test_{i}", f"component_{i % 2}")
            if i == 0:
                progress.is_completed = True
                progress.progress_percentage = 100.0
            elif i == 1:
                progress.errors = ["Test error"]
            self.system.track_operation(progress)
        
        # Generate report
        report = self.system.get_system_report()
        
        self.assertIn('system_overview', report)
        self.assertIn('recent_activity', report)
        self.assertIn('top_components', report)
        self.assertIn('error_analysis', report)
        self.assertIn('performance_metrics', report)
        self.assertIn('generated_at', report)
        
        # Check system overview
        overview = report['system_overview']
        self.assertGreaterEqual(overview['total_records'], 3)
        self.assertGreaterEqual(overview['active_operations'], 0)
        self.assertIsInstance(overview['database_size_bytes'], int)
        
        # Check top components
        top_components = report['top_components']
        self.assertIsInstance(top_components, list)
        if top_components:
            self.assertIn('component', top_components[0])
            self.assertIn('operations', top_components[0])
    
    def test_cleanup_old_records(self):
        """Test cleanup of old records"""
        # Add old records
        old_time = datetime.now() - timedelta(days=100)
        for i in range(3):
            progress = self._create_mock_progress(f"old_test_{i}", f"component_{i}")
            progress.start_time = old_time
            self.system.track_operation(progress)
        
        # Add recent records
        for i in range(2):
            progress = self._create_mock_progress(f"recent_test_{i}", f"component_{i}")
            self.system.track_operation(progress)
        
        # Verify we have 5 records
        self.assertEqual(len(self.system.operation_records), 5)
        
        # Cleanup old records (keep 90 days)
        cleaned_count = self.system.cleanup_old_records(days_to_keep=90)
        
        # Should have cleaned up 3 old records
        self.assertEqual(cleaned_count, 3)
        self.assertEqual(len(self.system.operation_records), 2)
        
        # Verify only recent records remain
        for record in self.system.operation_records.values():
            self.assertIn('recent_test', record.operation_id)
    
    def test_export_filters(self):
        """Test export filtering functionality"""
        # Add records with different statuses and components
        completed_progress = self._create_mock_progress("completed_op", "git")
        completed_progress.is_completed = True
        completed_progress.progress_percentage = 100.0
        self.system.track_operation(completed_progress)
        
        running_progress = self._create_mock_progress("running_op", "python")
        running_progress.progress_percentage = 50.0
        self.system.track_operation(running_progress)
        
        failed_progress = self._create_mock_progress("failed_op", "nodejs")
        failed_progress.errors = ["Installation failed"]
        self.system.track_operation(failed_progress)
        
        # Test status filter
        filters = {"status": ["completed"]}
        filtered_records = self.system._apply_export_filters(filters)
        self.assertEqual(len(filtered_records), 1)
        self.assertEqual(filtered_records[0].operation_id, "completed_op")
        
        # Test component filter
        filters = {"component": "python"}
        filtered_records = self.system._apply_export_filters(filters)
        self.assertEqual(len(filtered_records), 1)
        self.assertEqual(filtered_records[0].operation_id, "running_op")
        
        # Test multiple filters
        filters = {"status": ["running", "failed"], "component": "nodejs"}
        filtered_records = self.system._apply_export_filters(filters)
        self.assertEqual(len(filtered_records), 1)
        self.assertEqual(filtered_records[0].operation_id, "failed_op")
    
    def test_timeline_granularity(self):
        """Test different timeline granularities"""
        # Add test records
        now = datetime.now()
        for i in range(3):
            progress = self._create_mock_progress(f"granularity_test_{i}", "git")
            progress.start_time = now - timedelta(minutes=i * 30)
            self.system.track_operation(progress)
        
        # Test different granularities
        for granularity in [TimelineGranularity.MINUTE, TimelineGranularity.HOUR, TimelineGranularity.DAY]:
            timeline_data = self.system.implement_operation_timeline_visualization(
                time_range=(now - timedelta(hours=2), now),
                granularity=granularity
            )
            
            self.assertIn('timeline', timeline_data)
            self.assertEqual(timeline_data['timeline']['granularity'], granularity.value)
            self.assertIn('buckets', timeline_data['timeline'])
            self.assertIsInstance(timeline_data['timeline']['buckets'], list)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test tracking invalid operation
        invalid_progress = Mock()
        invalid_progress.operation_id = None  # Invalid
        
        success = self.system.track_operation(invalid_progress)
        self.assertFalse(success)
        
        # Test export with invalid format
        with self.assertRaises(ValueError):
            self.system.create_report_export_functionality_for_troubleshooting(
                "invalid_format",  # Invalid format
                output_path="test.txt"
            )
        
        # Test search with empty query
        results = self.system.search_operations("")
        self.assertEqual(len(results), 0)
        
        results = self.system.search_operations("   ")  # Whitespace only
        self.assertEqual(len(results), 0)
    
    def _create_mock_progress(self, operation_id: str, component_name: str):
        """Helper method to create mock operation progress"""
        mock_progress = Mock()
        mock_progress.operation_id = operation_id
        mock_progress.operation_type = Mock()
        mock_progress.operation_type.value = "installation"
        mock_progress.component_name = component_name
        mock_progress.title = f"Installing {component_name}"
        mock_progress.description = f"Installing {component_name} component"
        mock_progress.start_time = datetime.now()
        mock_progress.progress_percentage = 25.0
        mock_progress.current_step = "Processing"
        mock_progress.total_steps = 4
        mock_progress.current_step_number = 1
        mock_progress.details = [f"Processing {component_name}"]
        mock_progress.warnings = []
        mock_progress.errors = []
        mock_progress.result = None
        mock_progress.is_completed = False
        mock_progress.is_cancelled = False
        mock_progress.speed = None
        mock_progress.estimated_completion = None
        
        return mock_progress


class TestDataClasses(unittest.TestCase):
    """Test cases for data classes"""
    
    def test_operation_record_creation(self):
        """Test OperationRecord creation"""
        from core.operation_history_reporting_system import OperationType
        
        record = OperationRecord(
            operation_id="test_123",
            operation_type=OperationType.INSTALLATION,
            status=OperationStatus.RUNNING,
            component_name="git",
            title="Installing Git",
            description="Installing Git version control system",
            progress_percentage=75.0
        )
        
        self.assertEqual(record.operation_id, "test_123")
        self.assertEqual(record.operation_type, OperationType.INSTALLATION)
        self.assertEqual(record.status, OperationStatus.RUNNING)
        self.assertEqual(record.component_name, "git")
        self.assertEqual(record.progress_percentage, 75.0)
        self.assertEqual(len(record.details), 0)
        self.assertEqual(len(record.warnings), 0)
        self.assertEqual(len(record.errors), 0)
    
    def test_timeline_event_creation(self):
        """Test TimelineEvent creation"""
        event = TimelineEvent(
            timestamp=datetime.now(),
            operation_id="test_op",
            event_type="start",
            title="Operation Started",
            description="Test operation has started",
            component="test_component",
            progress=0.0
        )
        
        self.assertEqual(event.operation_id, "test_op")
        self.assertEqual(event.event_type, "start")
        self.assertEqual(event.title, "Operation Started")
        self.assertEqual(event.component, "test_component")
        self.assertEqual(event.progress, 0.0)
        self.assertEqual(len(event.metadata), 0)


if __name__ == '__main__':
    unittest.main()