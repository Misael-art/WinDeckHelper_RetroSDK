#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for RecoveryManager
Tests automatic recovery, backup restoration, and system maintenance
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from env_dev.core.recovery_manager import (
    RecoveryManager, RecoveryStatus, RepairType, BackupType,
    RepairResult, RestoreResult, UpdateResult, HealthReport
)
from env_dev.core.diagnostic_manager import Issue, DiagnosticResult, HealthStatus, IssueSeverity
from env_dev.core.error_handler import EnvDevError


class TestRecoveryManager(unittest.TestCase):
    """Unit tests for RecoveryManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock diagnostic manager
        self.mock_diagnostic_manager = Mock()
        
        # Create recovery manager
        self.manager = RecoveryManager(
            backup_dir=str(self.backup_dir),
            diagnostic_manager=self.mock_diagnostic_manager
        )
        
        # Test issue data
        self.test_issue = Issue(
            id="test_issue_1",
            title="Test Configuration Issue",
            description="Configuration file is corrupted",
            severity=IssueSeverity.ERROR,
            category="configuration",
            affected_components=["TestComponent"],
            suggested_solutions=["Restore from backup", "Recreate configuration"]
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_auto_repair_issues_success(self):
        """Test automatic repair of detected issues (Requirement 8.1)"""
        issues = [self.test_issue]
        
        # Mock successful repair
        with patch.object(self.manager, '_repair_configuration_issue') as mock_repair:
            mock_repair.return_value = True
            
            # Execute auto repair
            result = self.manager.auto_repair_issues(issues)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, RecoveryStatus.COMPLETED)
        self.assertEqual(result.issues_repaired, 1)
        self.assertEqual(result.issues_failed, 0)
        
        # Verify repair method was called
        mock_repair.assert_called_once_with(self.test_issue)
    
    def test_auto_repair_issues_partial_failure(self):
        """Test auto repair with some failures (Requirement 8.1)"""
        issues = [
            self.test_issue,
            Issue(
                id="test_issue_2",
                title="Unfixable Issue",
                description="Cannot be automatically repaired",
                severity=IssueSeverity.CRITICAL,
                category="system",
                affected_components=["SystemComponent"]
            )
        ]
        
        # Mock repair results - first succeeds, second fails
        def mock_repair_issue(issue):
            if issue.id == "test_issue_1":
                return True
            else:
                return False
        
        with patch.object(self.manager, '_repair_issue') as mock_repair:
            mock_repair.side_effect = mock_repair_issue
            
            # Execute auto repair
            result = self.manager.auto_repair_issues(issues)
        
        # Verify result
        self.assertFalse(result.success)  # Overall failure due to partial success
        self.assertEqual(result.status, RecoveryStatus.PARTIAL)
        self.assertEqual(result.issues_repaired, 1)
        self.assertEqual(result.issues_failed, 1)
    
    def test_restore_from_backup_success(self):
        """Test successful backup restoration (Requirement 8.3)"""
        # Create test backup
        backup_id = "backup_20250128_120000_test"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir()
        
        # Create backup metadata
        metadata = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'backup_type': BackupType.CONFIGURATION.value,
            'component': 'TestComponent',
            'files': [
                {
                    'original_path': str(self.temp_dir / "config.ini"),
                    'backup_path': str(backup_path / "config.ini")
                }
            ]
        }
        
        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Create backup file
        backup_config = backup_path / "config.ini"
        backup_config.write_text("[settings]\nkey=backup_value")
        
        # Execute restoration
        result = self.manager.restore_from_backup(backup_id)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, RecoveryStatus.COMPLETED)
        self.assertEqual(result.backup_id, backup_id)
        self.assertEqual(result.files_restored, 1)
        
        # Verify file was restored
        restored_file = self.temp_dir / "config.ini"
        self.assertTrue(restored_file.exists())
        self.assertEqual(restored_file.read_text(), "[settings]\nkey=backup_value")
    
    def test_restore_from_backup_not_found(self):
        """Test restoration with non-existent backup (Requirement 8.3)"""
        # Execute restoration with non-existent backup
        result = self.manager.restore_from_backup("nonexistent_backup")
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.status, RecoveryStatus.FAILED)
        self.assertIn("not found", result.error_message.lower())
    
    def test_update_components_success(self):
        """Test component update functionality (Requirement 8.2)"""
        components = [
            {
                'name': 'TestComponent',
                'current_version': '1.0.0',
                'latest_version': '1.1.0',
                'update_url': 'https://example.com/update.exe'
            }
        ]
        
        # Mock successful update
        with patch.object(self.manager, '_download_and_install_update') as mock_update:
            mock_update.return_value = True
            
            # Execute update
            result = self.manager.update_components(components)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, RecoveryStatus.COMPLETED)
        self.assertEqual(result.components_updated, 1)
        self.assertEqual(result.components_failed, 0)
        
        # Verify update method was called
        mock_update.assert_called_once_with(components[0])
    
    def test_update_components_with_outdated_detection(self):
        """Test automatic detection of outdated components (Requirement 8.2)"""
        # Mock component version checking
        with patch.object(self.manager, 'check_component_versions') as mock_check:
            mock_check.return_value = [
                {
                    'name': 'OutdatedComponent',
                    'current_version': '1.0.0',
                    'latest_version': '2.0.0',
                    'needs_update': True
                }
            ]
            
            # Execute update check
            outdated_components = self.manager.find_outdated_components()
        
        # Verify outdated components were found
        self.assertEqual(len(outdated_components), 1)
        self.assertEqual(outdated_components[0]['name'], 'OutdatedComponent')
        self.assertTrue(outdated_components[0]['needs_update'])
    
    def test_fix_inconsistencies(self):
        """Test detection and correction of inconsistencies (Requirement 8.5)"""
        # Create inconsistent state
        inconsistencies = [
            {
                'type': 'missing_file',
                'component': 'TestComponent',
                'expected_path': str(self.temp_dir / "required.dll"),
                'fix_action': 'restore_from_backup'
            },
            {
                'type': 'corrupted_config',
                'component': 'TestComponent',
                'config_path': str(self.temp_dir / "config.ini"),
                'fix_action': 'regenerate_config'
            }
        ]
        
        # Mock inconsistency detection
        with patch.object(self.manager, 'detect_inconsistencies') as mock_detect:
            mock_detect.return_value = inconsistencies
            
            # Mock fix methods
            with patch.object(self.manager, '_fix_missing_file') as mock_fix_file:
                with patch.object(self.manager, '_fix_corrupted_config') as mock_fix_config:
                    mock_fix_file.return_value = True
                    mock_fix_config.return_value = True
                    
                    # Execute fix
                    result = self.manager.fix_inconsistencies()
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, RecoveryStatus.COMPLETED)
        self.assertEqual(result.inconsistencies_fixed, 2)
        
        # Verify fix methods were called
        mock_fix_file.assert_called_once()
        mock_fix_config.assert_called_once()
    
    def test_generate_health_report(self):
        """Test system health report generation (Requirement 8.4)"""
        # Mock diagnostic result
        mock_diagnostic_result = DiagnosticResult(
            system_info=Mock(),
            compatibility=Mock(),
            issues=[self.test_issue],
            suggestions=[],
            overall_health=HealthStatus.WARNING,
            timestamp=datetime.now(),
            diagnostic_duration=1.5
        )
        
        self.mock_diagnostic_manager.run_full_diagnostic.return_value = mock_diagnostic_result
        
        # Mock component status
        with patch.object(self.manager, 'get_component_status') as mock_status:
            mock_status.return_value = {
                'TestComponent': {
                    'status': 'installed',
                    'version': '1.0.0',
                    'health': 'good'
                }
            }
            
            # Generate health report
            report = self.manager.generate_health_report()
        
        # Verify report
        self.assertIsInstance(report, HealthReport)
        self.assertEqual(report.overall_health, HealthStatus.WARNING)
        self.assertEqual(len(report.issues_found), 1)
        self.assertIn('TestComponent', report.component_status)
        self.assertIsNotNone(report.recommendations)
    
    def test_create_system_backup(self):
        """Test system backup creation"""
        components_to_backup = ['TestComponent', 'AnotherComponent']
        
        # Mock backup creation
        with patch.object(self.manager, '_backup_component') as mock_backup:
            mock_backup.return_value = {
                'success': True,
                'backup_path': str(self.backup_dir / "component_backup"),
                'files_backed_up': 5
            }
            
            # Create system backup
            result = self.manager.create_system_backup(components_to_backup)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.components_backed_up, 2)
        self.assertGreater(result.total_files_backed_up, 0)
        
        # Verify backup method was called for each component
        self.assertEqual(mock_backup.call_count, 2)
    
    def test_schedule_maintenance_tasks(self):
        """Test scheduling of maintenance tasks (Requirement 8.4)"""
        maintenance_tasks = [
            {
                'name': 'cleanup_temp_files',
                'frequency': 'daily',
                'last_run': datetime.now() - timedelta(days=2)
            },
            {
                'name': 'update_check',
                'frequency': 'weekly', 
                'last_run': datetime.now() - timedelta(days=8)
            }
        ]
        
        # Execute maintenance scheduling
        scheduled_tasks = self.manager.schedule_maintenance_tasks(maintenance_tasks)
        
        # Verify tasks were scheduled
        self.assertEqual(len(scheduled_tasks), 2)
        
        # Verify overdue tasks are identified
        overdue_tasks = [t for t in scheduled_tasks if t['overdue']]
        self.assertEqual(len(overdue_tasks), 2)  # Both tasks are overdue
    
    def test_repair_specific_issue_types(self):
        """Test repair of specific issue types"""
        # Test configuration issue repair
        config_issue = Issue(
            id="config_issue",
            title="Configuration Corrupted",
            description="Config file is corrupted",
            severity=IssueSeverity.ERROR,
            category="configuration",
            affected_components=["TestComponent"]
        )
        
        # Mock configuration repair
        with patch.object(self.manager, '_restore_configuration_from_backup') as mock_restore:
            mock_restore.return_value = True
            
            # Execute repair
            success = self.manager._repair_configuration_issue(config_issue)
        
        # Verify repair
        self.assertTrue(success)
        mock_restore.assert_called_once()
    
    def test_emergency_recovery_mode(self):
        """Test emergency recovery mode for critical issues"""
        critical_issues = [
            Issue(
                id="critical_issue",
                title="System Boot Failure",
                description="System cannot boot properly",
                severity=IssueSeverity.CRITICAL,
                category="system",
                affected_components=["BootManager"]
            )
        ]
        
        # Mock emergency recovery procedures
        with patch.object(self.manager, '_emergency_boot_repair') as mock_emergency:
            mock_emergency.return_value = True
            
            # Execute emergency recovery
            result = self.manager.emergency_recovery(critical_issues)
        
        # Verify emergency recovery
        self.assertTrue(result.success)
        self.assertEqual(result.status, RecoveryStatus.COMPLETED)
        self.assertTrue(result.emergency_mode_used)
        
        # Verify emergency procedure was called
        mock_emergency.assert_called_once()
    
    def test_recovery_progress_tracking(self):
        """Test recovery progress tracking"""
        # Start recovery operation
        operation_id = self.manager.start_recovery_operation("System Recovery", 5)
        
        # Update progress
        self.manager.update_recovery_progress(operation_id, 1, "Analyzing issues")
        self.manager.update_recovery_progress(operation_id, 3, "Applying repairs")
        
        # Get progress
        progress = self.manager.get_recovery_progress(operation_id)
        
        # Verify progress tracking
        self.assertEqual(progress.current_step, 3)
        self.assertEqual(progress.total_steps, 5)
        self.assertEqual(progress.percentage, 60.0)  # 3/5 * 100
        self.assertEqual(progress.current_message, "Applying repairs")
    
    def test_recovery_rollback_on_failure(self):
        """Test rollback of recovery operations on failure"""
        # Mock recovery operation that fails midway
        with patch.object(self.manager, '_apply_repair') as mock_repair:
            mock_repair.side_effect = [True, True, Exception("Repair failed")]
            
            # Mock rollback
            with patch.object(self.manager, '_rollback_recovery_changes') as mock_rollback:
                mock_rollback.return_value = True
                
                # Execute recovery (should fail and rollback)
                issues = [self.test_issue] * 3  # 3 issues to repair
                result = self.manager.auto_repair_issues(issues)
        
        # Verify recovery failed and rollback occurred
        self.assertFalse(result.success)
        self.assertTrue(result.rollback_performed)
        mock_rollback.assert_called_once()


class TestRecoveryManagerIntegration(unittest.TestCase):
    """Integration tests for RecoveryManager with other components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create real diagnostic manager mock
        self.diagnostic_manager = Mock()
        
        self.manager = RecoveryManager(
            backup_dir=str(self.backup_dir),
            diagnostic_manager=self.diagnostic_manager
        )
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_recovery_workflow(self):
        """Test complete recovery workflow with real scenarios"""
        # Create realistic system issues
        issues = [
            Issue(
                id="missing_config",
                title="Missing Configuration File",
                description="Critical configuration file is missing",
                severity=IssueSeverity.ERROR,
                category="configuration",
                affected_components=["MainApplication"],
                suggested_solutions=["Restore from backup", "Regenerate configuration"]
            ),
            Issue(
                id="outdated_component",
                title="Outdated Component",
                description="Component version is outdated",
                severity=IssueSeverity.WARNING,
                category="version",
                affected_components=["ComponentX"],
                suggested_solutions=["Update component"]
            )
        ]
        
        # Create backup for restoration
        backup_id = "backup_20250128_120000_config"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir()
        
        # Create backup metadata and files
        metadata = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'backup_type': BackupType.CONFIGURATION.value,
            'component': 'MainApplication',
            'files': [
                {
                    'original_path': str(self.temp_dir / "app_config.ini"),
                    'backup_path': str(backup_path / "app_config.ini")
                }
            ]
        }
        
        with open(backup_path / "metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        (backup_path / "app_config.ini").write_text("[app]\nversion=1.0\nmode=production")
        
        # Mock repair methods
        def mock_repair_issue(issue):
            if issue.category == "configuration":
                # Simulate configuration restoration
                return self.manager.restore_from_backup(backup_id).success
            elif issue.category == "version":
                # Simulate component update
                return True
            return False
        
        with patch.object(self.manager, '_repair_issue', side_effect=mock_repair_issue):
            # Execute complete recovery
            result = self.manager.auto_repair_issues(issues)
        
        # Verify complete recovery
        self.assertTrue(result.success)
        self.assertEqual(result.issues_repaired, 2)
        self.assertEqual(result.issues_failed, 0)
        
        # Verify configuration was restored
        restored_config = self.temp_dir / "app_config.ini"
        self.assertTrue(restored_config.exists())
        self.assertIn("version=1.0", restored_config.read_text())
    
    def test_health_monitoring_and_recovery_cycle(self):
        """Test continuous health monitoring and recovery cycle"""
        # Mock diagnostic results over time
        diagnostic_results = [
            # Initial state - healthy
            DiagnosticResult(
                system_info=Mock(),
                compatibility=Mock(),
                issues=[],
                suggestions=[],
                overall_health=HealthStatus.GOOD,
                timestamp=datetime.now(),
                diagnostic_duration=1.0
            ),
            # Later state - issues detected
            DiagnosticResult(
                system_info=Mock(),
                compatibility=Mock(),
                issues=[self.create_test_issue()],
                suggestions=[],
                overall_health=HealthStatus.WARNING,
                timestamp=datetime.now(),
                diagnostic_duration=1.2
            ),
            # After recovery - healthy again
            DiagnosticResult(
                system_info=Mock(),
                compatibility=Mock(),
                issues=[],
                suggestions=[],
                overall_health=HealthStatus.GOOD,
                timestamp=datetime.now(),
                diagnostic_duration=1.1
            )
        ]
        
        self.diagnostic_manager.run_full_diagnostic.side_effect = diagnostic_results
        
        # Mock successful repair
        with patch.object(self.manager, 'auto_repair_issues') as mock_repair:
            mock_repair.return_value = Mock(success=True, issues_repaired=1)
            
            # Simulate monitoring cycle
            reports = []
            for i in range(3):
                report = self.manager.generate_health_report()
                reports.append(report)
                
                # Trigger recovery if issues found
                if report.issues_found:
                    self.manager.auto_repair_issues(report.issues_found)
        
        # Verify monitoring cycle
        self.assertEqual(len(reports), 3)
        self.assertEqual(reports[0].overall_health, HealthStatus.GOOD)
        self.assertEqual(reports[1].overall_health, HealthStatus.WARNING)
        self.assertEqual(reports[2].overall_health, HealthStatus.GOOD)
        
        # Verify repair was triggered
        mock_repair.assert_called_once()
    
    def create_test_issue(self):
        """Helper method to create test issue"""
        return Issue(
            id="test_issue",
            title="Test Issue",
            description="Test issue for monitoring",
            severity=IssueSeverity.WARNING,
            category="test",
            affected_components=["TestComponent"]
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)