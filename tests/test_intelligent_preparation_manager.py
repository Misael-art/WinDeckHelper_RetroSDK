# -*- coding: utf-8 -*-
"""
Unit tests for Intelligent Preparation Manager
Tests intelligent preparation system with directory structure creation,
configuration backup, privilege escalation, and environment variable configuration
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intelligent_preparation_manager import (
    IntelligentPreparationManager,
    DirectoryStructure,
    EnvironmentConfiguration,
    PathConfiguration,
    BackupInfo,
    PreparationResult,
    PreparationStatus,
    BackupType,
    PrivilegeLevel
)

class TestDirectoryStructure(unittest.TestCase):
    """Test DirectoryStructure data class"""
    
    def test_directory_structure_creation(self):
        """Test creating directory structure"""
        structure = DirectoryStructure(
            path="/test/path",
            permissions="755",
            owner="user:group",
            required_privilege=PrivilegeLevel.USER
        )
        
        self.assertEqual(structure.path, "/test/path")
        self.assertEqual(structure.permissions, "755")
        self.assertEqual(structure.owner, "user:group")
        self.assertEqual(structure.required_privilege, PrivilegeLevel.USER)
        self.assertTrue(structure.recursive)
        self.assertTrue(structure.backup_existing)

class TestEnvironmentConfiguration(unittest.TestCase):
    """Test EnvironmentConfiguration data class"""
    
    def test_environment_configuration_creation(self):
        """Test creating environment configuration"""
        env_config = EnvironmentConfiguration(
            name="TEST_VAR",
            value="test_value",
            scope="user",
            operation="set",
            backup_existing=True
        )
        
        self.assertEqual(env_config.name, "TEST_VAR")
        self.assertEqual(env_config.value, "test_value")
        self.assertEqual(env_config.scope, "user")
        self.assertEqual(env_config.operation, "set")
        self.assertTrue(env_config.backup_existing)
        self.assertEqual(env_config.separator, ";")

class TestPathConfiguration(unittest.TestCase):
    """Test PathConfiguration data class"""
    
    def test_path_configuration_creation(self):
        """Test creating path configuration"""
        path_config = PathConfiguration(
            path="/test/bin",
            operation="add",
            scope="user",
            position="end"
        )
        
        self.assertEqual(path_config.path, "/test/bin")
        self.assertEqual(path_config.operation, "add")
        self.assertEqual(path_config.scope, "user")
        self.assertEqual(path_config.position, "end")
        self.assertTrue(path_config.backup_existing)

class TestBackupInfo(unittest.TestCase):
    """Test BackupInfo data class"""
    
    def test_backup_info_creation(self):
        """Test creating backup info"""
        backup_info = BackupInfo(
            backup_id="test_backup_001",
            original_path="/original/path",
            backup_path="/backup/path",
            backup_type=BackupType.FILE,
            size_bytes=1024
        )
        
        self.assertEqual(backup_info.backup_id, "test_backup_001")
        self.assertEqual(backup_info.original_path, "/original/path")
        self.assertEqual(backup_info.backup_path, "/backup/path")
        self.assertEqual(backup_info.backup_type, BackupType.FILE)
        self.assertEqual(backup_info.size_bytes, 1024)
        self.assertIsInstance(backup_info.timestamp, datetime)

class TestIntelligentPreparationManager(unittest.TestCase):
    """Test IntelligentPreparationManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.manager = IntelligentPreparationManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.base_path, self.test_dir)
        self.assertTrue(os.path.exists(self.manager.backup_base_dir))
        self.assertTrue(os.path.exists(self.manager.temp_dir))
        self.assertTrue(os.path.exists(self.manager.config_dir))
        self.assertEqual(len(self.manager.backup_registry), 0)
        self.assertEqual(len(self.manager.preparation_history), 0)
    
    def test_analyze_privilege_requirements_user_only(self):
        """Test privilege analysis for user-only operations"""
        components = ["test_component"]
        
        analysis = self.manager._analyze_privilege_requirements(components)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('requires_elevation', analysis)
        self.assertIn('required_operations', analysis)
        self.assertIn('user_operations', analysis)
        self.assertIn('admin_operations', analysis)
        self.assertIn('system_operations', analysis)
    
    def test_analyze_privilege_requirements_with_admin_structures(self):
        """Test privilege analysis with admin-required structures"""
        components = ["test_component"]
        custom_structures = [
            DirectoryStructure(
                path="/system/path",
                required_privilege=PrivilegeLevel.ADMIN
            )
        ]
        
        analysis = self.manager._analyze_privilege_requirements(
            components, custom_structures=custom_structures
        )
        
        self.assertTrue(analysis['requires_elevation'])
        self.assertGreater(len(analysis['admin_operations']), 0)
    
    def test_analyze_privilege_requirements_with_system_env_vars(self):
        """Test privilege analysis with system environment variables"""
        components = ["test_component"]
        custom_env_vars = [
            EnvironmentConfiguration(
                name="SYSTEM_VAR",
                value="test_value",
                scope="system"
            )
        ]
        
        analysis = self.manager._analyze_privilege_requirements(
            components, custom_env_vars=custom_env_vars
        )
        
        self.assertTrue(analysis['requires_elevation'])
        self.assertGreater(len(analysis['admin_operations']), 0)
    
    @patch('core.intelligent_preparation_manager.is_admin')
    def test_request_privilege_elevation_already_admin(self, mock_is_admin):
        """Test privilege elevation when already admin"""
        mock_is_admin.return_value = True
        
        result = self.manager._request_privilege_elevation(["test operation"])
        
        self.assertTrue(result)
    
    @patch('core.intelligent_preparation_manager.is_admin')
    def test_request_privilege_elevation_not_admin(self, mock_is_admin):
        """Test privilege elevation when not admin"""
        mock_is_admin.return_value = False
        
        result = self.manager._request_privilege_elevation(["test operation"])
        
        # Should return False since we can't actually elevate in tests
        self.assertFalse(result)
    
    def test_create_backup_file(self):
        """Test creating backup of a file"""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        backup_info = self.manager._create_backup(test_file)
        
        self.assertIsNotNone(backup_info)
        self.assertEqual(backup_info.original_path, test_file)
        self.assertEqual(backup_info.backup_type, BackupType.FILE)
        self.assertTrue(os.path.exists(backup_info.backup_path))
        self.assertGreater(backup_info.size_bytes, 0)
        
        # Verify backup content
        with open(backup_info.backup_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test content")
    
    def test_create_backup_directory(self):
        """Test creating backup of a directory"""
        # Create a test directory with files
        test_dir = os.path.join(self.test_dir, "test_directory")
        os.makedirs(test_dir)
        
        test_file = os.path.join(test_dir, "file.txt")
        with open(test_file, 'w') as f:
            f.write("directory content")
        
        backup_info = self.manager._create_backup(test_dir)
        
        self.assertIsNotNone(backup_info)
        self.assertEqual(backup_info.original_path, test_dir)
        self.assertEqual(backup_info.backup_type, BackupType.DIRECTORY)
        self.assertTrue(os.path.exists(backup_info.backup_path))
        self.assertTrue(os.path.isdir(backup_info.backup_path))
        self.assertGreater(backup_info.size_bytes, 0)
        
        # Verify backup content
        backup_file = os.path.join(backup_info.backup_path, "file.txt")
        self.assertTrue(os.path.exists(backup_file))
        with open(backup_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "directory content")
    
    def test_create_backup_nonexistent_file(self):
        """Test creating backup of non-existent file"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")
        
        backup_info = self.manager._create_backup(nonexistent_file)
        
        self.assertIsNone(backup_info)
    
    def test_create_directory_structure_new_directory(self):
        """Test creating new directory structure"""
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        structure = DirectoryStructure(
            path=os.path.join(self.test_dir, "new_directory"),
            permissions="755"
        )
        
        success = self.manager._create_directory_structure(structure, result)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(structure.path))
        self.assertTrue(os.path.isdir(structure.path))
    
    def test_create_directory_structure_existing_directory(self):
        """Test creating directory structure when directory already exists"""
        # Create existing directory
        existing_dir = os.path.join(self.test_dir, "existing_directory")
        os.makedirs(existing_dir)
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        structure = DirectoryStructure(
            path=existing_dir,
            backup_existing=False
        )
        
        success = self.manager._create_directory_structure(structure, result)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(structure.path))
    
    def test_create_directory_structure_with_backup(self):
        """Test creating directory structure with backup of existing content"""
        # Create existing directory with content
        existing_dir = os.path.join(self.test_dir, "existing_with_content")
        os.makedirs(existing_dir)
        
        test_file = os.path.join(existing_dir, "existing_file.txt")
        with open(test_file, 'w') as f:
            f.write("existing content")
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        structure = DirectoryStructure(
            path=existing_dir,
            backup_existing=True
        )
        
        success = self.manager._create_directory_structure(structure, result)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(structure.path))
        self.assertGreater(len(result.backups_created), 0)
    
    @patch('utils.env_manager.set_env_var')
    @patch('utils.env_manager.get_env_var')
    def test_configure_environment_variable_set(self, mock_get_env_var, mock_set_env_var):
        """Test configuring environment variable with set operation"""
        mock_get_env_var.return_value = None
        mock_set_env_var.return_value = True
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        env_var = EnvironmentConfiguration(
            name="TEST_VAR",
            value="test_value",
            operation="set"
        )
        
        success = self.manager._configure_environment_variable(env_var, result)
        
        self.assertTrue(success)
        mock_set_env_var.assert_called_once_with("TEST_VAR", "test_value", scope="user")
    
    @patch('utils.env_manager.set_env_var')
    @patch('utils.env_manager.get_env_var')
    def test_configure_environment_variable_append(self, mock_get_env_var, mock_set_env_var):
        """Test configuring environment variable with append operation"""
        mock_get_env_var.return_value = "existing_value"
        mock_set_env_var.return_value = True
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        env_var = EnvironmentConfiguration(
            name="TEST_VAR",
            value="new_value",
            operation="append",
            separator=":"
        )
        
        success = self.manager._configure_environment_variable(env_var, result)
        
        self.assertTrue(success)
        mock_set_env_var.assert_called_once_with("TEST_VAR", "existing_value:new_value", scope="user")
    
    @patch('utils.env_manager.set_env_var')
    @patch('utils.env_manager.get_env_var')
    def test_configure_environment_variable_prepend(self, mock_get_env_var, mock_set_env_var):
        """Test configuring environment variable with prepend operation"""
        mock_get_env_var.return_value = "existing_value"
        mock_set_env_var.return_value = True
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        env_var = EnvironmentConfiguration(
            name="TEST_VAR",
            value="new_value",
            operation="prepend",
            separator=":"
        )
        
        success = self.manager._configure_environment_variable(env_var, result)
        
        self.assertTrue(success)
        mock_set_env_var.assert_called_once_with("TEST_VAR", "new_value:existing_value", scope="user")
    
    @patch('utils.env_manager.add_to_path')
    def test_configure_path_variable_add(self, mock_add_to_path):
        """Test configuring PATH variable with add operation"""
        mock_add_to_path.return_value = True
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        path_var = PathConfiguration(
            path="/test/bin",
            operation="add",
            scope="user"
        )
        
        success = self.manager._configure_path_variable(path_var, result)
        
        self.assertTrue(success)
        mock_add_to_path.assert_called_once_with("/test/bin", scope="user")
    
    @patch('utils.env_manager.remove_from_path')
    def test_configure_path_variable_remove(self, mock_remove_from_path):
        """Test configuring PATH variable with remove operation"""
        mock_remove_from_path.return_value = True
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        path_var = PathConfiguration(
            path="/test/bin",
            operation="remove",
            scope="user"
        )
        
        success = self.manager._configure_path_variable(path_var, result)
        
        self.assertTrue(success)
        mock_remove_from_path.assert_called_once_with("/test/bin", scope="user")
    
    def test_get_component_directory_structures(self):
        """Test getting directory structures for components"""
        components = ["java", "python", "nodejs"]
        
        structures = self.manager._get_component_directory_structures(components)
        
        self.assertGreater(len(structures), 0)
        
        # Check that base directories are included for all components
        base_dirs = ["downloads", "temp", "logs", "config"]
        for component in components:
            for base_dir in base_dirs:
                expected_path = os.path.join(self.test_dir, base_dir, component)
                self.assertTrue(any(s.path == expected_path for s in structures))
        
        # Check component-specific directories
        java_dir = os.path.join(self.test_dir, "java")
        self.assertTrue(any(s.path == java_dir for s in structures))
        
        python_dir = os.path.join(self.test_dir, "python")
        self.assertTrue(any(s.path == python_dir for s in structures))
        
        nodejs_dir = os.path.join(self.test_dir, "nodejs")
        self.assertTrue(any(s.path == nodejs_dir for s in structures))
    
    def test_get_component_environment_variables(self):
        """Test getting environment variables for components"""
        components = ["java", "python", "nodejs"]
        
        env_vars = self.manager._get_component_environment_variables(components)
        
        self.assertGreater(len(env_vars), 0)
        
        # Check for global variables
        env_var_names = [var.name for var in env_vars]
        self.assertIn("ENVIRONMENT_DEV_HOME", env_var_names)
        self.assertIn("ENVIRONMENT_DEV_VERSION", env_var_names)
        
        # Check for component-specific variables
        self.assertIn("JAVA_HOME", env_var_names)
        self.assertIn("PYTHON_HOME", env_var_names)
        self.assertIn("NODE_HOME", env_var_names)
    
    def test_get_component_path_variables(self):
        """Test getting PATH variables for components"""
        components = ["java", "python", "nodejs"]
        
        path_vars = self.manager._get_component_path_variables(components)
        
        self.assertGreater(len(path_vars), 0)
        
        # Check for component-specific PATH entries
        path_values = [var.path for var in path_vars]
        
        java_bin = os.path.join(self.test_dir, "java", "bin")
        self.assertIn(java_bin, path_values)
        
        python_path = os.path.join(self.test_dir, "python")
        self.assertIn(python_path, path_values)
        
        nodejs_path = os.path.join(self.test_dir, "nodejs")
        self.assertIn(nodejs_path, path_values)
    
    def test_sort_directory_structures(self):
        """Test sorting directory structures"""
        structures = [
            DirectoryStructure(
                path=os.path.join(self.test_dir, "deep", "nested", "path"),
                required_privilege=PrivilegeLevel.USER
            ),
            DirectoryStructure(
                path=os.path.join(self.test_dir, "shallow"),
                required_privilege=PrivilegeLevel.ADMIN
            ),
            DirectoryStructure(
                path=os.path.join(self.test_dir, "deep", "nested"),
                required_privilege=PrivilegeLevel.USER
            )
        ]
        
        sorted_structures = self.manager._sort_directory_structures(structures)
        
        # Should be sorted by path depth (parents first)
        self.assertEqual(len(sorted_structures), 3)
        self.assertTrue(len(sorted_structures[0].path.split(os.sep)) <= len(sorted_structures[1].path.split(os.sep)))
        self.assertTrue(len(sorted_structures[1].path.split(os.sep)) <= len(sorted_structures[2].path.split(os.sep)))
    
    def test_deduplicate_environment_variables(self):
        """Test deduplicating environment variables"""
        env_vars = [
            EnvironmentConfiguration(name="TEST_VAR", value="value1", scope="user"),
            EnvironmentConfiguration(name="TEST_VAR", value="value2", scope="user"),
            EnvironmentConfiguration(name="TEST_VAR", value="value3", scope="system"),
            EnvironmentConfiguration(name="OTHER_VAR", value="other_value", scope="user")
        ]
        
        unique_vars = self.manager._deduplicate_environment_variables(env_vars)
        
        # Should have 3 unique variables (TEST_VAR for user, TEST_VAR for system, OTHER_VAR for user)
        self.assertEqual(len(unique_vars), 3)
        
        # Check that the last value for each (name, scope) combination is kept
        test_var_user = next(var for var in unique_vars if var.name == "TEST_VAR" and var.scope == "user")
        self.assertEqual(test_var_user.value, "value2")
        
        test_var_system = next(var for var in unique_vars if var.name == "TEST_VAR" and var.scope == "system")
        self.assertEqual(test_var_system.value, "value3")
    
    @patch('utils.env_manager.set_env_var')
    def test_restore_from_backup_environment_var(self, mock_set_env_var):
        """Test restoring environment variable from backup"""
        mock_set_env_var.return_value = True
        
        # Create a backup
        backup_info = BackupInfo(
            backup_id="env_backup_001",
            original_path="ENV:TEST_VAR",
            backup_path="",
            backup_type=BackupType.ENVIRONMENT_VAR,
            metadata={
                'variable_name': 'TEST_VAR',
                'original_value': 'original_value',
                'scope': 'user'
            }
        )
        
        # Register backup
        with self.manager._lock:
            self.manager.backup_registry[backup_info.backup_id] = backup_info
        
        # Restore
        success = self.manager.restore_from_backup(backup_info.backup_id)
        
        self.assertTrue(success)
        mock_set_env_var.assert_called_once_with('TEST_VAR', 'original_value', scope='user')
    
    def test_restore_from_backup_file(self):
        """Test restoring file from backup"""
        # Create original file
        original_file = os.path.join(self.test_dir, "original.txt")
        with open(original_file, 'w') as f:
            f.write("original content")
        
        # Create backup
        backup_info = self.manager._create_backup(original_file)
        self.assertIsNotNone(backup_info)
        
        # Modify original file
        with open(original_file, 'w') as f:
            f.write("modified content")
        
        # Restore from backup
        success = self.manager.restore_from_backup(backup_info.backup_id)
        
        self.assertTrue(success)
        
        # Verify restoration
        with open(original_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "original content")
    
    def test_list_backups(self):
        """Test listing backups"""
        # Create some backups
        test_file1 = os.path.join(self.test_dir, "test1.txt")
        with open(test_file1, 'w') as f:
            f.write("test1")
        
        test_file2 = os.path.join(self.test_dir, "test2.txt")
        with open(test_file2, 'w') as f:
            f.write("test2")
        
        backup1 = self.manager._create_backup(test_file1)
        backup2 = self.manager._create_backup(test_file2)
        
        # List backups
        backups = self.manager.list_backups()
        
        self.assertEqual(len(backups), 2)
        backup_ids = [b.backup_id for b in backups]
        self.assertIn(backup1.backup_id, backup_ids)
        self.assertIn(backup2.backup_id, backup_ids)
    
    def test_cleanup_old_backups(self):
        """Test cleaning up old backups"""
        # Create a backup
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        backup_info = self.manager._create_backup(test_file)
        self.assertIsNotNone(backup_info)
        
        # Manually set old timestamp
        old_time = datetime.now() - timedelta(days=31)
        backup_info.timestamp = old_time
        
        # Update registry
        with self.manager._lock:
            self.manager.backup_registry[backup_info.backup_id] = backup_info
        
        # Clean up old backups
        cleaned_count = self.manager.cleanup_old_backups(days_old=30)
        
        self.assertEqual(cleaned_count, 1)
        self.assertFalse(os.path.exists(backup_info.backup_path))
        
        # Check that backup was removed from registry
        backups = self.manager.list_backups()
        self.assertEqual(len(backups), 0)
    
    def test_get_preparation_statistics_empty(self):
        """Test getting preparation statistics when no preparations have been done"""
        stats = self.manager.get_preparation_statistics()
        
        self.assertEqual(stats['total_preparations'], 0)
        self.assertEqual(stats['successful_preparations'], 0)
        self.assertEqual(stats['failed_preparations'], 0)
        self.assertEqual(stats['total_backups'], 0)
        self.assertEqual(stats['average_preparation_time'], 0.0)
    
    def test_get_preparation_statistics_with_history(self):
        """Test getting preparation statistics with history"""
        # Add some mock preparation results
        result1 = PreparationResult(
            status=PreparationStatus.COMPLETED,
            preparation_time=10.5,
            directories_created=["/test/dir1"],
            env_vars_configured=[EnvironmentConfiguration("VAR1", "value1")],
            path_vars_configured=[PathConfiguration("/test/bin")]
        )
        
        result2 = PreparationResult(
            status=PreparationStatus.FAILED,
            preparation_time=5.2,
            directories_created=[],
            env_vars_configured=[],
            path_vars_configured=[]
        )
        
        with self.manager._lock:
            self.manager.preparation_history.extend([result1, result2])
        
        stats = self.manager.get_preparation_statistics()
        
        self.assertEqual(stats['total_preparations'], 2)
        self.assertEqual(stats['successful_preparations'], 1)
        self.assertEqual(stats['failed_preparations'], 1)
        self.assertEqual(stats['success_rate'], 50.0)
        self.assertEqual(stats['average_preparation_time'], 7.85)
        self.assertEqual(stats['total_directories_created'], 1)
        self.assertEqual(stats['total_env_vars_configured'], 1)
        self.assertEqual(stats['total_path_vars_configured'], 1)

if __name__ == '__main__':
    unittest.main()