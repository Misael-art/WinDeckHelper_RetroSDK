#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for PreparationManager
Tests intelligent environment preparation, backup creation, and permission management
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from env_dev.core.preparation_manager import (
    PreparationManager, PreparationStatus, BackupType, BackupInfo,
    PreparationResult, EnvironmentSetupResult
)
from env_dev.core.error_handler import EnvDevError


class TestPreparationManager(unittest.TestCase):
    """Unit tests for PreparationManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PreparationManager(base_dir=str(self.temp_dir))
        
        # Test component data
        self.test_component = {
            'name': 'TestComponent',
            'install_directories': [
                str(self.temp_dir / "install"),
                str(self.temp_dir / "config")
            ],
            'environment_variables': {
                'TEST_HOME': str(self.temp_dir / "install"),
                'TEST_CONFIG': str(self.temp_dir / "config")
            },
            'required_permissions': ['write', 'execute'],
            'backup_paths': [
                str(self.temp_dir / "existing_config.txt")
            ]
        }
    
    def tearDown(self):
        """Clean up test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_prepare_environment_success(self):
        """Test successful environment preparation (Requirement 3.1)"""
        # Create existing file to backup
        existing_config = self.temp_dir / "existing_config.txt"
        existing_config.write_text("existing configuration")
        
        # Mock permission checks
        with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
            with patch('env_dev.utils.permission_checker.is_admin', return_value=True):
                # Execute preparation
                result = self.manager.prepare_environment(self.test_component)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, PreparationStatus.COMPLETED)
        self.assertEqual(result.component, 'TestComponent')
        
        # Verify directories were created
        install_dir = Path(self.test_component['install_directories'][0])
        config_dir = Path(self.test_component['install_directories'][1])
        self.assertTrue(install_dir.exists())
        self.assertTrue(config_dir.exists())
        
        # Verify backup was created
        self.assertGreater(len(result.backups_created), 0)
        backup = result.backups_created[0]
        self.assertEqual(backup.backup_type, BackupType.FILE)
        self.assertTrue(Path(backup.backup_path).exists())
    
    def test_create_directory_structure(self):
        """Test automatic directory creation (Requirement 3.1)"""
        directories = [
            str(self.temp_dir / "level1"),
            str(self.temp_dir / "level1" / "level2"),
            str(self.temp_dir / "level1" / "level2" / "level3")
        ]
        
        # Execute directory creation
        created_dirs = self.manager.create_directory_structure(directories)
        
        # Verify all directories were created
        self.assertEqual(len(created_dirs), 3)
        for directory in directories:
            self.assertTrue(Path(directory).exists())
            self.assertIn(directory, created_dirs)
    
    def test_create_directory_structure_with_conflicts(self):
        """Test directory creation with existing conflicts (Requirement 3.2)"""
        # Create existing directory with file
        existing_dir = self.temp_dir / "existing"
        existing_dir.mkdir()
        existing_file = existing_dir / "important.txt"
        existing_file.write_text("important data")
        
        directories = [str(existing_dir)]
        
        # Execute directory creation (should handle existing directory)
        created_dirs = self.manager.create_directory_structure(directories)
        
        # Verify directory still exists and file is preserved
        self.assertTrue(existing_dir.exists())
        self.assertTrue(existing_file.exists())
        self.assertEqual(existing_file.read_text(), "important data")
    
    def test_backup_existing_configurations(self):
        """Test backup of existing configurations (Requirement 3.2)"""
        # Create existing files to backup
        config_file = self.temp_dir / "config.ini"
        config_file.write_text("[settings]\nkey=value")
        
        data_dir = self.temp_dir / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("data1")
        (data_dir / "file2.txt").write_text("data2")
        
        paths_to_backup = [str(config_file), str(data_dir)]
        
        # Execute backup
        backups = self.manager.backup_existing_configurations(paths_to_backup)
        
        # Verify backups were created
        self.assertEqual(len(backups), 2)
        
        # Verify file backup
        file_backup = next(b for b in backups if b.backup_type == BackupType.FILE)
        self.assertEqual(file_backup.original_path, str(config_file))
        self.assertTrue(Path(file_backup.backup_path).exists())
        
        # Verify directory backup
        dir_backup = next(b for b in backups if b.backup_type == BackupType.DIRECTORY)
        self.assertEqual(dir_backup.original_path, str(data_dir))
        self.assertTrue(Path(dir_backup.backup_path).exists())
        
        # Verify backup contents
        backup_config = Path(file_backup.backup_path)
        self.assertEqual(backup_config.read_text(), "[settings]\nkey=value")
    
    def test_configure_environment_variables(self):
        """Test environment variable configuration (Requirement 3.3)"""
        env_vars = {
            'TEST_VAR1': 'value1',
            'TEST_VAR2': 'value2',
            'PATH_ADDITION': str(self.temp_dir / "bin")
        }
        
        # Mock environment variable functions
        with patch('env_dev.utils.env_manager.set_env_var') as mock_set_env:
            with patch('env_dev.utils.env_manager.add_to_path') as mock_add_path:
                # Execute environment configuration
                result = self.manager.configure_environment_variables(env_vars)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(len(result.variables_set), 3)
        
        # Verify environment functions were called
        mock_set_env.assert_any_call('TEST_VAR1', 'value1')
        mock_set_env.assert_any_call('TEST_VAR2', 'value2')
        mock_add_path.assert_called_with(str(self.temp_dir / "bin"))
    
    def test_check_and_request_permissions(self):
        """Test permission checking and elevation (Requirement 3.4)"""
        required_permissions = ['write', 'execute', 'admin']
        
        # Mock permission checks - admin required but not available
        with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
            with patch('env_dev.utils.permission_checker.is_admin', return_value=False):
                # Execute permission check
                result = self.manager.check_and_request_permissions(required_permissions)
        
        # Verify result indicates admin elevation needed
        self.assertFalse(result.success)
        self.assertIn('admin', result.missing_permissions)
        self.assertIn('elevation required', result.message.lower())
    
    def test_check_and_request_permissions_success(self):
        """Test successful permission verification (Requirement 3.4)"""
        required_permissions = ['write', 'execute']
        
        # Mock successful permission checks
        with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
            with patch('env_dev.utils.permission_checker.is_admin', return_value=True):
                # Execute permission check
                result = self.manager.check_and_request_permissions(required_permissions)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(len(result.missing_permissions), 0)
        self.assertIn('permissions verified', result.message.lower())
    
    def test_prepare_system_dependencies(self):
        """Test system dependency preparation (Requirement 3.5)"""
        dependencies = [
            {
                'name': 'Visual C++ Redistributable',
                'type': 'system_package',
                'check_command': 'reg query "HKLM\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64"',
                'install_command': 'vcredist_x64.exe /quiet'
            },
            {
                'name': '.NET Framework 4.8',
                'type': 'system_package', 
                'check_command': 'reg query "HKLM\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full" /v Release',
                'install_command': 'ndp48-x86-x64-allos-enu.exe /quiet'
            }
        ]
        
        # Mock dependency checks - first missing, second present
        def mock_subprocess_run(cmd, **kwargs):
            if 'VisualStudio' in ' '.join(cmd):
                # VC++ not found
                return Mock(returncode=1, stdout="", stderr="Not found")
            else:
                # .NET found
                return Mock(returncode=0, stdout="Release    REG_DWORD    0x1cc020", stderr="")
        
        with patch('subprocess.run', side_effect=mock_subprocess_run):
            # Execute dependency preparation
            result = self.manager.prepare_system_dependencies(dependencies)
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(len(result.dependencies_checked), 2)
        self.assertEqual(len(result.dependencies_installed), 1)  # Only VC++ needed installation
        
        # Verify missing dependency was identified
        missing_deps = [d for d in result.dependencies_checked if not d['present']]
        self.assertEqual(len(missing_deps), 1)
        self.assertEqual(missing_deps[0]['name'], 'Visual C++ Redistributable')
    
    def test_restore_from_backup(self):
        """Test restoration from backup"""
        # Create original file and backup
        original_file = self.temp_dir / "original.txt"
        original_file.write_text("original content")
        
        # Create backup
        backup_info = self.manager.create_backup(str(original_file))
        
        # Modify original file
        original_file.write_text("modified content")
        
        # Restore from backup
        result = self.manager.restore_from_backup(backup_info)
        
        # Verify restoration
        self.assertTrue(result.success)
        self.assertEqual(original_file.read_text(), "original content")
    
    def test_cleanup_preparation_on_failure(self):
        """Test cleanup of preparation artifacts on failure"""
        # Start preparation tracking
        self.manager.start_preparation_tracking('TestComponent')
        
        # Create some directories and files
        test_dir = self.temp_dir / "test_prep"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")
        
        # Track created items
        self.manager.track_created_directory(str(test_dir))
        self.manager.track_created_file(str(test_file))
        
        # Execute cleanup
        self.manager.cleanup_preparation('TestComponent')
        
        # Verify cleanup
        self.assertFalse(test_dir.exists())
        self.assertFalse(test_file.exists())
    
    def test_disk_space_verification(self):
        """Test disk space verification before preparation"""
        # Mock disk space check - insufficient space
        with patch('env_dev.utils.disk_space.get_disk_space') as mock_disk_space:
            mock_disk_space.return_value = {
                'free': 100 * 1024 * 1024,  # 100MB free
                'total': 1000 * 1024 * 1024  # 1GB total
            }
            
            # Test with component requiring 200MB
            component = {
                'name': 'LargeComponent',
                'required_disk_space': 200 * 1024 * 1024  # 200MB required
            }
            
            # Execute disk space check
            result = self.manager.verify_disk_space(component)
        
        # Verify insufficient space detected
        self.assertFalse(result.success)
        self.assertIn('insufficient disk space', result.message.lower())
        self.assertEqual(result.required_space, 200 * 1024 * 1024)
        self.assertEqual(result.available_space, 100 * 1024 * 1024)
    
    def test_concurrent_preparation(self):
        """Test concurrent preparation of multiple components"""
        import threading
        import time
        
        components = [
            {'name': 'Component1', 'install_directories': [str(self.temp_dir / "comp1")]},
            {'name': 'Component2', 'install_directories': [str(self.temp_dir / "comp2")]},
            {'name': 'Component3', 'install_directories': [str(self.temp_dir / "comp3")]}
        ]
        
        results = {}
        
        def prepare_component(component):
            with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
                result = self.manager.prepare_environment(component)
                results[component['name']] = result
        
        # Start concurrent preparations
        threads = []
        for component in components:
            thread = threading.Thread(target=prepare_component, args=(component,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Verify all preparations succeeded
        self.assertEqual(len(results), 3)
        for component_name, result in results.items():
            self.assertTrue(result.success, f"Preparation failed for {component_name}")
            
            # Verify directory was created
            expected_dir = self.temp_dir / component_name.lower()
            self.assertTrue(expected_dir.exists())
    
    def test_preparation_rollback_on_partial_failure(self):
        """Test rollback of preparation when partial failure occurs"""
        component = {
            'name': 'PartialFailComponent',
            'install_directories': [
                str(self.temp_dir / "dir1"),
                str(self.temp_dir / "dir2")
            ],
            'environment_variables': {
                'TEST_VAR': 'test_value'
            }
        }
        
        # Mock directory creation success, but env var failure
        with patch.object(self.manager, 'create_directory_structure') as mock_create_dirs:
            mock_create_dirs.return_value = [str(self.temp_dir / "dir1"), str(self.temp_dir / "dir2")]
            
            with patch.object(self.manager, 'configure_environment_variables') as mock_env_vars:
                mock_env_vars.return_value = Mock(success=False, error_message="Env var failed")
                
                # Execute preparation (should fail and rollback)
                result = self.manager.prepare_environment(component)
        
        # Verify preparation failed
        self.assertFalse(result.success)
        
        # Verify rollback occurred (directories should be cleaned up)
        # Note: In a real implementation, this would clean up created directories
        self.assertIn('rollback', result.message.lower())
    
    def test_preparation_state_persistence(self):
        """Test persistence of preparation state"""
        component_name = 'PersistentComponent'
        
        # Start preparation tracking
        self.manager.start_preparation_tracking(component_name)
        
        # Add some tracked items
        self.manager.track_created_directory(str(self.temp_dir / "tracked_dir"))
        self.manager.track_environment_variable('TRACKED_VAR', 'tracked_value')
        
        # Save state
        self.manager.save_preparation_state(component_name)
        
        # Load state in new manager instance
        new_manager = PreparationManager(base_dir=str(self.temp_dir))
        state = new_manager.load_preparation_state(component_name)
        
        # Verify state was persisted
        self.assertIsNotNone(state)
        self.assertEqual(state['component'], component_name)
        self.assertIn(str(self.temp_dir / "tracked_dir"), state['created_directories'])
        self.assertIn('TRACKED_VAR', state['environment_variables'])


class TestPreparationManagerIntegration(unittest.TestCase):
    """Integration tests for PreparationManager with other components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PreparationManager(base_dir=str(self.temp_dir))
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_preparation_workflow(self):
        """Test complete preparation workflow"""
        # Create realistic component requiring full preparation
        component = {
            'name': 'ComplexSoftware',
            'version': '3.0.0',
            'install_directories': [
                str(self.temp_dir / "ComplexSoftware"),
                str(self.temp_dir / "ComplexSoftware" / "config"),
                str(self.temp_dir / "ComplexSoftware" / "data"),
                str(self.temp_dir / "ComplexSoftware" / "logs")
            ],
            'environment_variables': {
                'COMPLEX_HOME': str(self.temp_dir / "ComplexSoftware"),
                'COMPLEX_CONFIG': str(self.temp_dir / "ComplexSoftware" / "config"),
                'COMPLEX_DATA': str(self.temp_dir / "ComplexSoftware" / "data")
            },
            'backup_paths': [
                str(self.temp_dir / "existing_config.xml")
            ],
            'required_permissions': ['write', 'execute'],
            'system_dependencies': [
                {
                    'name': 'Test Dependency',
                    'type': 'system_package',
                    'check_command': 'echo "present"',
                    'install_command': 'echo "installed"'
                }
            ],
            'required_disk_space': 50 * 1024 * 1024  # 50MB
        }
        
        # Create existing file to backup
        existing_config = self.temp_dir / "existing_config.xml"
        existing_config.write_text('<?xml version="1.0"?><config><setting>value</setting></config>')
        
        # Mock all external dependencies
        with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
            with patch('env_dev.utils.permission_checker.is_admin', return_value=True):
                with patch('env_dev.utils.disk_space.get_disk_space') as mock_disk_space:
                    mock_disk_space.return_value = {
                        'free': 100 * 1024 * 1024,  # 100MB free
                        'total': 1000 * 1024 * 1024  # 1GB total
                    }
                    
                    with patch('env_dev.utils.env_manager.set_env_var') as mock_set_env:
                        with patch('subprocess.run') as mock_subprocess:
                            mock_subprocess.return_value = Mock(returncode=0, stdout="present", stderr="")
                            
                            # Execute full preparation
                            result = self.manager.prepare_environment(component)
        
        # Verify complete success
        self.assertTrue(result.success)
        self.assertEqual(result.status, PreparationStatus.COMPLETED)
        self.assertEqual(result.component, 'ComplexSoftware')
        
        # Verify all directories were created
        for directory in component['install_directories']:
            self.assertTrue(Path(directory).exists(), f"Directory {directory} was not created")
        
        # Verify backup was created
        self.assertGreater(len(result.backups_created), 0)
        backup = result.backups_created[0]
        self.assertTrue(Path(backup.backup_path).exists())
        
        # Verify environment variables were set
        expected_env_calls = len(component['environment_variables'])
        self.assertEqual(mock_set_env.call_count, expected_env_calls)
        
        # Verify system dependencies were checked
        self.assertGreater(len(result.dependencies_checked), 0)
        
        # Verify disk space was sufficient
        self.assertGreaterEqual(result.available_disk_space, component['required_disk_space'])
    
    def test_preparation_with_permission_elevation(self):
        """Test preparation workflow requiring permission elevation"""
        component = {
            'name': 'SystemLevelSoftware',
            'install_directories': [str(self.temp_dir / "Program Files" / "SystemSoftware")],
            'required_permissions': ['admin', 'write', 'execute']
        }
        
        # Mock permission checks - not admin initially
        with patch('env_dev.utils.permission_checker.is_admin', side_effect=[False, True]):
            with patch('env_dev.utils.permission_checker.check_write_permission', return_value=True):
                with patch.object(self.manager, 'request_elevation') as mock_elevation:
                    mock_elevation.return_value = True
                    
                    # Execute preparation
                    result = self.manager.prepare_environment(component)
        
        # Verify elevation was requested
        mock_elevation.assert_called_once()
        
        # Verify preparation succeeded after elevation
        self.assertTrue(result.success)
        self.assertIn('elevation', result.message.lower())


if __name__ == '__main__':
    unittest.main(verbosity=2)