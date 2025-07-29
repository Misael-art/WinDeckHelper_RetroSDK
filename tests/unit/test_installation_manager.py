#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for InstallationManager
Tests robust installation with rollback, dependency resolution, and batch installation
"""

import unittest
import tempfile
import shutil
import os
import json
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from env_dev.core.installation_manager import (
    InstallationManager, InstallationType, InstallationStatus, 
    InstallationResult, BatchInstallationResult, VerificationResult,
    RollbackResult, DependencyResult, InstallationStep
)
from env_dev.core.error_handler import EnvDevError


class TestInstallationManager(unittest.TestCase):
    """Unit tests for InstallationManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_config_dir = self.temp_dir / "config"
        self.test_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock dependencies
        self.mock_download_manager = Mock()
        self.mock_preparation_manager = Mock()
        
        # Create installation manager
        self.manager = InstallationManager(
            config_dir=str(self.test_config_dir),
            download_manager=self.mock_download_manager,
            preparation_manager=self.mock_preparation_manager
        )
        
        # Test component data
        self.test_component = {
            'name': 'TestComponent',
            'version': '1.0.0',
            'install_type': 'executable',
            'install_args': ['/S'],
            'dependencies': [],
            'verify_actions': [
                {'type': 'file_exists', 'path': 'C:\\Program Files\\TestComponent\\test.exe'}
            ]
        }
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_install_component_success(self):
        """Test successful component installation (Requirement 4.1)"""
        # Mock successful preparation
        self.mock_preparation_manager.prepare_environment.return_value = Mock(success=True)
        
        # Mock successful download
        self.mock_download_manager.download_file.return_value = Mock(
            success=True,
            file_path=str(self.temp_dir / "test.exe")
        )
        
        # Create test installer file
        test_installer = self.temp_dir / "test.exe"
        test_installer.write_text("fake installer")
        
        # Mock subprocess for installation
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Mock verification
            with patch.object(self.manager, 'verify_installation') as mock_verify:
                mock_verify.return_value = VerificationResult(
                    success=True,
                    component='TestComponent',
                    message="Installation verified successfully"
                )
                
                # Execute installation
                result = self.manager.install_component(self.test_component)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.component, 'TestComponent')
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertIsNone(result.error_message)
        
        # Verify preparation was called
        self.mock_preparation_manager.prepare_environment.assert_called_once()
        
        # Verify download was called
        self.mock_download_manager.download_file.assert_called_once()
    
    def test_install_component_with_rollback(self):
        """Test installation failure with automatic rollback (Requirement 4.1)"""
        # Mock successful preparation
        self.mock_preparation_manager.prepare_environment.return_value = Mock(success=True)
        
        # Mock successful download
        self.mock_download_manager.download_file.return_value = Mock(
            success=True,
            file_path=str(self.temp_dir / "test.exe")
        )
        
        # Create test installer file
        test_installer = self.temp_dir / "test.exe"
        test_installer.write_text("fake installer")
        
        # Mock subprocess failure
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="Installation failed")
            
            # Mock rollback
            with patch.object(self.manager, 'rollback_installation') as mock_rollback:
                mock_rollback.return_value = RollbackResult(
                    success=True,
                    component='TestComponent',
                    message="Rollback completed successfully"
                )
                
                # Execute installation
                result = self.manager.install_component(self.test_component)
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.status, InstallationStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        
        # Verify rollback was called
        mock_rollback.assert_called_once_with('TestComponent')
    
    def test_detect_circular_dependencies(self):
        """Test circular dependency detection (Requirement 4.3)"""
        # Create components with circular dependencies
        components = {
            'ComponentA': {'dependencies': ['ComponentB']},
            'ComponentB': {'dependencies': ['ComponentC']},
            'ComponentC': {'dependencies': ['ComponentA']}  # Creates cycle
        }
        
        # Test detection
        has_cycles, cycles = self.manager.detect_circular_dependencies(components)
        
        # Verify cycle was detected
        self.assertTrue(has_cycles)
        self.assertGreater(len(cycles), 0)
        
        # Verify cycle contains expected components
        cycle = cycles[0]
        self.assertIn('ComponentA', cycle)
        self.assertIn('ComponentB', cycle)
        self.assertIn('ComponentC', cycle)
    
    def test_resolve_dependency_order(self):
        """Test dependency order resolution (Requirement 4.2)"""
        # Create components with dependencies
        components = {
            'ComponentA': {'dependencies': ['ComponentB', 'ComponentC']},
            'ComponentB': {'dependencies': ['ComponentC']},
            'ComponentC': {'dependencies': []},
            'ComponentD': {'dependencies': ['ComponentA']}
        }
        
        # Resolve order
        order = self.manager.resolve_dependency_order(components)
        
        # Verify order is correct
        self.assertEqual(len(order), 4)
        
        # ComponentC should be first (no dependencies)
        self.assertEqual(order[0], 'ComponentC')
        
        # ComponentB should come before ComponentA
        b_index = order.index('ComponentB')
        a_index = order.index('ComponentA')
        self.assertLess(b_index, a_index)
        
        # ComponentA should come before ComponentD
        d_index = order.index('ComponentD')
        self.assertLess(a_index, d_index)
    
    def test_install_multiple_components(self):
        """Test batch installation with dependency resolution (Requirement 4.2)"""
        # Create test components
        components = [
            {
                'name': 'ComponentC',
                'dependencies': [],
                'install_type': 'executable'
            },
            {
                'name': 'ComponentB', 
                'dependencies': ['ComponentC'],
                'install_type': 'executable'
            },
            {
                'name': 'ComponentA',
                'dependencies': ['ComponentB'],
                'install_type': 'executable'
            }
        ]
        
        # Mock successful installations
        def mock_install_component(component):
            return InstallationResult(
                success=True,
                component=component['name'],
                status=InstallationStatus.COMPLETED,
                message=f"{component['name']} installed successfully"
            )
        
        with patch.object(self.manager, 'install_component', side_effect=mock_install_component):
            # Execute batch installation
            result = self.manager.install_multiple(components)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.total_components, 3)
        self.assertEqual(result.successful_installations, 3)
        self.assertEqual(result.failed_installations, 0)
        
        # Verify installation order was correct
        self.assertEqual(len(result.installation_order), 3)
        self.assertEqual(result.installation_order[0], 'ComponentC')
        self.assertEqual(result.installation_order[1], 'ComponentB')
        self.assertEqual(result.installation_order[2], 'ComponentA')
    
    def test_install_multiple_with_failure_and_recovery(self):
        """Test batch installation with failure and recovery (Requirement 4.5)"""
        components = [
            {'name': 'ComponentA', 'dependencies': []},
            {'name': 'ComponentB', 'dependencies': []},
            {'name': 'ComponentC', 'dependencies': []}
        ]
        
        # Mock installation results - B fails, others succeed
        def mock_install_component(component):
            if component['name'] == 'ComponentB':
                return InstallationResult(
                    success=False,
                    component='ComponentB',
                    status=InstallationStatus.FAILED,
                    error_message="Installation failed"
                )
            else:
                return InstallationResult(
                    success=True,
                    component=component['name'],
                    status=InstallationStatus.COMPLETED
                )
        
        with patch.object(self.manager, 'install_component', side_effect=mock_install_component):
            # Execute batch installation
            result = self.manager.install_multiple(components)
        
        # Verify result
        self.assertFalse(result.success)  # Overall failure due to one component
        self.assertEqual(result.total_components, 3)
        self.assertEqual(result.successful_installations, 2)
        self.assertEqual(result.failed_installations, 1)
        
        # Verify failed component is recorded
        self.assertIn('ComponentB', result.failed_components)
    
    def test_verify_installation_success(self):
        """Test post-installation verification (Requirement 4.4)"""
        # Create test file for verification
        test_file = self.temp_dir / "test.exe"
        test_file.write_text("test executable")
        
        component = {
            'name': 'TestComponent',
            'verify_actions': [
                {
                    'type': 'file_exists',
                    'path': str(test_file)
                }
            ]
        }
        
        # Execute verification
        result = self.manager.verify_installation(component)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.component, 'TestComponent')
        self.assertIn("verified successfully", result.message.lower())
    
    def test_verify_installation_failure(self):
        """Test verification failure detection (Requirement 4.4)"""
        component = {
            'name': 'TestComponent',
            'verify_actions': [
                {
                    'type': 'file_exists',
                    'path': str(self.temp_dir / "nonexistent.exe")
                }
            ]
        }
        
        # Execute verification
        result = self.manager.verify_installation(component)
        
        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.component, 'TestComponent')
        self.assertIn("verification failed", result.message.lower())
    
    def test_rollback_installation(self):
        """Test installation rollback functionality (Requirement 4.1)"""
        component_name = 'TestComponent'
        
        # Create mock rollback data
        rollback_data = {
            'component': component_name,
            'installed_files': [str(self.temp_dir / "test.exe")],
            'created_directories': [str(self.temp_dir / "test_dir")],
            'registry_changes': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save rollback data
        rollback_file = self.temp_dir / f"{component_name}_rollback.json"
        with open(rollback_file, 'w') as f:
            json.dump(rollback_data, f)
        
        # Create files to be rolled back
        test_file = Path(rollback_data['installed_files'][0])
        test_file.write_text("test file")
        test_dir = Path(rollback_data['created_directories'][0])
        test_dir.mkdir()
        
        # Mock rollback data loading
        with patch.object(self.manager, '_load_rollback_data', return_value=rollback_data):
            # Execute rollback
            result = self.manager.rollback_installation(component_name)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.component, component_name)
        
        # Verify files were removed
        self.assertFalse(test_file.exists())
        self.assertFalse(test_dir.exists())
    
    def test_parallel_installation_when_possible(self):
        """Test parallel installation of independent components (Requirement 4.2)"""
        # Create independent components (no dependencies between them)
        components = [
            {'name': 'IndependentA', 'dependencies': []},
            {'name': 'IndependentB', 'dependencies': []},
            {'name': 'IndependentC', 'dependencies': []}
        ]
        
        # Track installation times to verify parallelism
        installation_times = {}
        
        def mock_install_component(component):
            start_time = time.time()
            time.sleep(0.1)  # Simulate installation time
            end_time = time.time()
            installation_times[component['name']] = (start_time, end_time)
            
            return InstallationResult(
                success=True,
                component=component['name'],
                status=InstallationStatus.COMPLETED
            )
        
        with patch.object(self.manager, 'install_component', side_effect=mock_install_component):
            # Enable parallel installation
            self.manager.enable_parallel_installation = True
            
            # Execute batch installation
            start_time = time.time()
            result = self.manager.install_multiple(components)
            total_time = time.time() - start_time
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.successful_installations, 3)
        
        # Verify installations ran in parallel (total time should be less than sum of individual times)
        # With 3 components taking 0.1s each, sequential would take ~0.3s, parallel should be ~0.1s
        self.assertLess(total_time, 0.25)  # Allow some overhead
    
    def test_installation_conflict_detection(self):
        """Test detection of conflicts between components (Requirement 4.5)"""
        components = [
            {
                'name': 'ComponentA',
                'conflicts': ['ComponentB'],
                'dependencies': []
            },
            {
                'name': 'ComponentB', 
                'conflicts': ['ComponentA'],
                'dependencies': []
            }
        ]
        
        # Test conflict detection
        conflicts = self.manager.detect_installation_conflicts(components)
        
        # Verify conflicts were detected
        self.assertGreater(len(conflicts), 0)
        
        # Verify specific conflict
        conflict = conflicts[0]
        self.assertIn('ComponentA', conflict['components'])
        self.assertIn('ComponentB', conflict['components'])
        self.assertIn('conflict', conflict['reason'].lower())
    
    def test_installation_state_tracking(self):
        """Test installation state tracking and persistence"""
        component_name = 'TestComponent'
        
        # Start installation tracking
        self.manager.start_installation_tracking(component_name)
        
        # Update progress
        self.manager.update_installation_progress(
            component_name,
            InstallationStep.DOWNLOADING,
            50.0,
            "Downloading component..."
        )
        
        # Get current state
        state = self.manager.get_installation_state(component_name)
        
        # Verify state
        self.assertEqual(state.component, component_name)
        self.assertEqual(state.current_step, InstallationStep.DOWNLOADING)
        self.assertEqual(state.progress, 50.0)
        self.assertEqual(state.status, InstallationStatus.IN_PROGRESS)
    
    def test_installation_cleanup_on_failure(self):
        """Test cleanup of partial installation on failure (Requirement 4.1)"""
        # Mock preparation that creates files
        def mock_prepare_environment(component):
            test_file = self.temp_dir / "partial_install.tmp"
            test_file.write_text("partial installation")
            return Mock(success=True, created_files=[str(test_file)])
        
        self.mock_preparation_manager.prepare_environment.side_effect = mock_prepare_environment
        
        # Mock download failure
        self.mock_download_manager.download_file.return_value = Mock(
            success=False,
            error_message="Download failed"
        )
        
        # Execute installation (should fail and cleanup)
        result = self.manager.install_component(self.test_component)
        
        # Verify installation failed
        self.assertFalse(result.success)
        
        # Verify cleanup occurred (partial files should be removed)
        partial_file = self.temp_dir / "partial_install.tmp"
        self.assertFalse(partial_file.exists())
    
    def test_installation_retry_mechanism(self):
        """Test retry mechanism for failed installations (Requirement 4.5)"""
        # Mock installation that fails twice then succeeds
        call_count = 0
        
        def mock_install_component_with_retry(component):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                return InstallationResult(
                    success=False,
                    component=component['name'],
                    status=InstallationStatus.FAILED,
                    error_message="Temporary failure"
                )
            else:
                return InstallationResult(
                    success=True,
                    component=component['name'],
                    status=InstallationStatus.COMPLETED
                )
        
        # Enable retry mechanism
        self.manager.max_retry_attempts = 3
        
        with patch.object(self.manager, '_execute_installation', side_effect=mock_install_component_with_retry):
            # Execute installation with retry
            result = self.manager.install_component_with_retry(self.test_component)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(call_count, 3)  # Should have retried twice
    
    def test_installation_progress_callbacks(self):
        """Test installation progress callback system"""
        progress_updates = []
        
        def progress_callback(component, step, progress, message):
            progress_updates.append({
                'component': component,
                'step': step,
                'progress': progress,
                'message': message
            })
        
        # Register callback
        self.manager.register_progress_callback(progress_callback)
        
        # Simulate installation with progress updates
        component_name = 'TestComponent'
        self.manager.start_installation_tracking(component_name)
        
        # Update progress multiple times
        steps = [
            (InstallationStep.PREPARING, 10.0, "Preparing environment"),
            (InstallationStep.DOWNLOADING, 50.0, "Downloading files"),
            (InstallationStep.INSTALLING, 80.0, "Installing component"),
            (InstallationStep.VERIFYING, 100.0, "Verifying installation")
        ]
        
        for step, progress, message in steps:
            self.manager.update_installation_progress(component_name, step, progress, message)
        
        # Verify callbacks were called
        self.assertEqual(len(progress_updates), 4)
        
        # Verify progress sequence
        for i, (expected_step, expected_progress, expected_message) in enumerate(steps):
            update = progress_updates[i]
            self.assertEqual(update['component'], component_name)
            self.assertEqual(update['step'], expected_step)
            self.assertEqual(update['progress'], expected_progress)
            self.assertEqual(update['message'], expected_message)


class TestInstallationManagerIntegration(unittest.TestCase):
    """Integration tests for InstallationManager with other components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.temp_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create real managers for integration testing
        self.download_manager = Mock()
        self.preparation_manager = Mock()
        
        self.manager = InstallationManager(
            config_dir=str(self.config_dir),
            download_manager=self.download_manager,
            preparation_manager=self.preparation_manager
        )
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_installation_workflow(self):
        """Test complete installation workflow with all components"""
        # Create realistic component
        component = {
            'name': 'TestSoftware',
            'version': '2.1.0',
            'install_type': 'executable',
            'install_args': ['/SILENT'],
            'dependencies': [],
            'verify_actions': [
                {'type': 'file_exists', 'path': str(self.temp_dir / "installed.exe")}
            ]
        }
        
        # Mock successful preparation
        self.preparation_manager.prepare_environment.return_value = Mock(
            success=True,
            created_directories=[str(self.temp_dir / "install_dir")],
            backup_info=[]
        )
        
        # Mock successful download
        installer_path = self.temp_dir / "installer.exe"
        installer_path.write_text("fake installer")
        
        self.download_manager.download_file.return_value = Mock(
            success=True,
            file_path=str(installer_path),
            verification_passed=True
        )
        
        # Create expected installation result
        installed_file = self.temp_dir / "installed.exe"
        
        # Mock subprocess for installation
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Create installed file to pass verification
            installed_file.write_text("installed software")
            
            # Execute installation
            result = self.manager.install_component(component)
        
        # Verify complete workflow
        self.assertTrue(result.success)
        self.assertEqual(result.component, 'TestSoftware')
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        
        # Verify all managers were called
        self.preparation_manager.prepare_environment.assert_called_once()
        self.download_manager.download_file.assert_called_once()
        
        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        self.assertIn('/SILENT', call_args)
    
    def test_complex_dependency_resolution(self):
        """Test complex dependency resolution scenario"""
        # Create complex dependency tree
        components = [
            {
                'name': 'Application',
                'dependencies': ['Runtime', 'Database'],
                'install_type': 'executable'
            },
            {
                'name': 'Runtime',
                'dependencies': ['BaseLibrary'],
                'install_type': 'msi'
            },
            {
                'name': 'Database',
                'dependencies': ['BaseLibrary', 'NetworkLibrary'],
                'install_type': 'executable'
            },
            {
                'name': 'BaseLibrary',
                'dependencies': [],
                'install_type': 'archive'
            },
            {
                'name': 'NetworkLibrary',
                'dependencies': ['BaseLibrary'],
                'install_type': 'archive'
            }
        ]
        
        # Mock successful installations
        def mock_install_component(component):
            return InstallationResult(
                success=True,
                component=component['name'],
                status=InstallationStatus.COMPLETED,
                message=f"{component['name']} installed successfully"
            )
        
        with patch.object(self.manager, 'install_component', side_effect=mock_install_component):
            # Execute batch installation
            result = self.manager.install_multiple(components)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.successful_installations, 5)
        
        # Verify installation order respects dependencies
        order = result.installation_order
        
        # BaseLibrary should be first
        self.assertEqual(order[0], 'BaseLibrary')
        
        # NetworkLibrary should come after BaseLibrary
        base_index = order.index('BaseLibrary')
        network_index = order.index('NetworkLibrary')
        self.assertLess(base_index, network_index)
        
        # Runtime should come after BaseLibrary
        runtime_index = order.index('Runtime')
        self.assertLess(base_index, runtime_index)
        
        # Database should come after BaseLibrary and NetworkLibrary
        database_index = order.index('Database')
        self.assertLess(base_index, database_index)
        self.assertLess(network_index, database_index)
        
        # Application should be last
        self.assertEqual(order[-1], 'Application')


if __name__ == '__main__':
    unittest.main(verbosity=2)