# -*- coding: utf-8 -*-
"""
Unit tests for Advanced Installation Manager
Tests atomic operations, rollback capabilities, and installation state tracking
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.advanced_installation_manager import (
    AdvancedInstallationManager,
    AtomicTransaction,
    AtomicOperation,
    InstallationStatus,
    TransactionState,
    InstallationResult,
    RollbackInfo
)

class TestAtomicOperation(unittest.TestCase):
    """Test AtomicOperation data class"""
    
    def test_atomic_operation_creation(self):
        """Test creating atomic operation"""
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_file",
            target_path="/test/path",
            new_value="test content"
        )
        
        self.assertEqual(operation.operation_id, "test_op_001")
        self.assertEqual(operation.operation_type, "create_file")
        self.assertEqual(operation.target_path, "/test/path")
        self.assertEqual(operation.new_value, "test content")
        self.assertFalse(operation.completed)
        self.assertFalse(operation.rollback_completed)
        self.assertIsInstance(operation.timestamp, datetime)

class TestAtomicTransaction(unittest.TestCase):
    """Test AtomicTransaction class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.transaction_id = "test_transaction_001"
        self.component_name = "test_component"
        self.transaction = AtomicTransaction(
            self.transaction_id, 
            self.component_name, 
            self.test_dir
        )
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_transaction_initialization(self):
        """Test transaction initialization"""
        self.assertEqual(self.transaction.transaction_id, self.transaction_id)
        self.assertEqual(self.transaction.component_name, self.component_name)
        self.assertEqual(self.transaction.state, TransactionState.INACTIVE)
        self.assertEqual(len(self.transaction.operations), 0)
        
        # Check transaction directory was created
        expected_dir = os.path.join(self.test_dir, "transactions", self.transaction_id)
        self.assertTrue(os.path.exists(expected_dir))
    
    def test_begin_transaction(self):
        """Test beginning a transaction"""
        result = self.transaction.begin()
        
        self.assertTrue(result)
        self.assertEqual(self.transaction.state, TransactionState.ACTIVE)
        self.assertGreater(len(self.transaction.rollback_info.transaction_log), 0)
    
    def test_begin_transaction_already_active(self):
        """Test beginning transaction when already active"""
        self.transaction.begin()
        result = self.transaction.begin()  # Try to begin again
        
        self.assertFalse(result)
        self.assertEqual(self.transaction.state, TransactionState.ACTIVE)
    
    def test_add_operation(self):
        """Test adding operation to transaction"""
        self.transaction.begin()
        
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_file",
            target_path=os.path.join(self.test_dir, "test_file.txt")
        )
        
        result = self.transaction.add_operation(operation)
        
        self.assertTrue(result)
        self.assertEqual(len(self.transaction.operations), 1)
        self.assertEqual(self.transaction.operations[0], operation)
    
    def test_add_operation_inactive_transaction(self):
        """Test adding operation to inactive transaction"""
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_file"
        )
        
        result = self.transaction.add_operation(operation)
        
        self.assertFalse(result)
        self.assertEqual(len(self.transaction.operations), 0)
    
    def test_create_backup(self):
        """Test creating backup of existing file"""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("original content")
        
        backup_path = self.transaction.create_backup(test_file)
        
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup content
        with open(backup_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "original content")
    
    def test_create_backup_nonexistent_file(self):
        """Test creating backup of non-existent file"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")
        backup_path = self.transaction.create_backup(nonexistent_file)
        
        self.assertIsNone(backup_path)
    
    def test_execute_create_file_operation(self):
        """Test executing create file operation"""
        self.transaction.begin()
        
        target_path = os.path.join(self.test_dir, "new_file.txt")
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_file",
            target_path=target_path,
            new_value="test content"
        )
        
        result = self.transaction.execute_operation(operation)
        
        self.assertTrue(result)
        self.assertTrue(operation.completed)
        self.assertTrue(os.path.exists(target_path))
        
        # Verify file content
        with open(target_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "test content")
    
    def test_execute_create_directory_operation(self):
        """Test executing create directory operation"""
        self.transaction.begin()
        
        target_path = os.path.join(self.test_dir, "new_directory")
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_directory",
            target_path=target_path
        )
        
        result = self.transaction.execute_operation(operation)
        
        self.assertTrue(result)
        self.assertTrue(operation.completed)
        self.assertTrue(os.path.exists(target_path))
        self.assertTrue(os.path.isdir(target_path))
    
    @patch('utils.env_manager.set_env_var')
    def test_execute_set_env_var_operation(self, mock_set_env_var):
        """Test executing set environment variable operation"""
        mock_set_env_var.return_value = True
        
        self.transaction.begin()
        
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="set_env_var",
            new_value="test_value",
            metadata={'var_name': 'TEST_VAR', 'scope': 'user'}
        )
        
        result = self.transaction.execute_operation(operation)
        
        self.assertTrue(result)
        self.assertTrue(operation.completed)
        mock_set_env_var.assert_called_once_with('TEST_VAR', 'test_value', scope='user')
    
    def test_commit_transaction(self):
        """Test committing transaction"""
        self.transaction.begin()
        
        result = self.transaction.commit()
        
        self.assertTrue(result)
        self.assertEqual(self.transaction.state, TransactionState.COMMITTED)
    
    def test_commit_inactive_transaction(self):
        """Test committing inactive transaction"""
        result = self.transaction.commit()
        
        self.assertFalse(result)
        self.assertEqual(self.transaction.state, TransactionState.INACTIVE)
    
    def test_rollback_transaction(self):
        """Test rolling back transaction"""
        self.transaction.begin()
        
        # Create a file operation
        target_path = os.path.join(self.test_dir, "test_file.txt")
        operation = AtomicOperation(
            operation_id="test_op_001",
            operation_type="create_file",
            target_path=target_path,
            new_value="test content"
        )
        
        self.transaction.add_operation(operation)
        self.transaction.execute_operation(operation)
        
        # Verify file was created
        self.assertTrue(os.path.exists(target_path))
        
        # Rollback
        result = self.transaction.rollback()
        
        self.assertTrue(result)
        self.assertEqual(self.transaction.state, TransactionState.ROLLED_BACK)
        # File should be removed
        self.assertFalse(os.path.exists(target_path))

class TestAdvancedInstallationManager(unittest.TestCase):
    """Test AdvancedInstallationManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.manager = AdvancedInstallationManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.base_path, self.test_dir)
        self.assertTrue(os.path.exists(self.manager.transactions_dir))
        self.assertTrue(os.path.exists(self.manager.rollback_dir))
        self.assertEqual(len(self.manager.installation_states), 0)
        self.assertEqual(len(self.manager.active_transactions), 0)
    
    @patch('core.robust_download_manager.RobustDownloadManager')
    @patch('utils.extractor.extract_archive')
    def test_install_component_atomic_archive(self, mock_extract, mock_download_manager):
        """Test atomic installation of archive component"""
        # Mock download manager
        mock_download_result = Mock()
        mock_download_result.success = True
        mock_download_result.file_path = os.path.join(self.test_dir, "downloads", "test_component", "test.zip")
        
        mock_dm_instance = Mock()
        mock_dm_instance.download_with_mandatory_hash_verification.return_value = mock_download_result
        mock_download_manager.return_value = mock_dm_instance
        
        # Mock extract_archive
        mock_extract.return_value = True
        
        # Component data
        component_data = {
            'install_method': 'archive',
            'download_url': 'https://example.com/test.zip',
            'filename': 'test.zip',
            'sha256_hash': 'dummy_hash',
            'install_path': os.path.join(self.test_dir, 'test_component'),
            'verification_paths': [os.path.join(self.test_dir, 'test_component')],
            'verification_commands': []
        }
        
        # Create the verification path
        os.makedirs(component_data['verification_paths'][0], exist_ok=True)
        
        result = self.manager.install_component_atomic('test_component', component_data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertIsNotNone(result.transaction_id)
        self.assertTrue(result.rollback_available)
        
        # Verify state was tracked
        state = self.manager.get_installation_state('test_component')
        self.assertIsNotNone(state)
        self.assertEqual(state.status, InstallationStatus.COMPLETED)
    
    def test_install_component_atomic_failure_rollback(self):
        """Test atomic installation failure triggers rollback"""
        # Component data with invalid install method
        component_data = {
            'install_method': 'invalid_method',
            'verification_paths': [],
            'verification_commands': []
        }
        
        result = self.manager.install_component_atomic('test_component', component_data)
        
        self.assertFalse(result.success)
        self.assertEqual(result.status, InstallationStatus.FAILED)
        self.assertTrue(result.rollback_available)
        
        # Verify state was tracked
        state = self.manager.get_installation_state('test_component')
        self.assertIsNotNone(state)
        self.assertEqual(state.status, InstallationStatus.FAILED)
    
    def test_rollback_component(self):
        """Test rolling back a component"""
        # First install a component (mock successful installation)
        component_data = {
            'install_method': 'archive',
            'verification_paths': [],
            'verification_commands': []
        }
        
        # Create a mock transaction
        transaction_id = "test_component_12345678"
        transaction = AtomicTransaction(transaction_id, "test_component", self.test_dir)
        transaction.begin()
        
        # Add to active transactions
        self.manager.active_transactions[transaction_id] = transaction
        
        # Create installation state
        from core.advanced_installation_manager import InstallationState
        state = InstallationState(
            component="test_component",
            status=InstallationStatus.COMPLETED,
            transaction_id=transaction_id
        )
        self.manager.installation_states["test_component"] = state
        
        # Test rollback
        result = self.manager.rollback_component("test_component")
        
        self.assertTrue(result)
        
        # Verify state was updated
        updated_state = self.manager.get_installation_state("test_component")
        self.assertEqual(updated_state.status, InstallationStatus.ROLLED_BACK)
    
    def test_rollback_component_not_found(self):
        """Test rolling back non-existent component"""
        result = self.manager.rollback_component("nonexistent_component")
        
        self.assertFalse(result)
    
    def test_get_installation_state(self):
        """Test getting installation state"""
        # Create a state
        from core.advanced_installation_manager import InstallationState
        state = InstallationState(
            component="test_component",
            status=InstallationStatus.INSTALLING
        )
        self.manager.installation_states["test_component"] = state
        
        retrieved_state = self.manager.get_installation_state("test_component")
        
        self.assertIsNotNone(retrieved_state)
        self.assertEqual(retrieved_state.component, "test_component")
        self.assertEqual(retrieved_state.status, InstallationStatus.INSTALLING)
    
    def test_get_installation_state_not_found(self):
        """Test getting state for non-existent component"""
        state = self.manager.get_installation_state("nonexistent_component")
        
        self.assertIsNone(state)
    
    def test_list_rollback_available_components(self):
        """Test listing components with rollback available"""
        # Create some mock transactions
        transaction1 = AtomicTransaction("comp1_12345678", "comp1", self.test_dir)
        transaction2 = AtomicTransaction("comp2_87654321", "comp2", self.test_dir)
        
        self.manager.active_transactions["comp1_12345678"] = transaction1
        self.manager.active_transactions["comp2_87654321"] = transaction2
        
        components = self.manager.list_rollback_available_components()
        
        self.assertIn("comp1", components)
        self.assertIn("comp2", components)
        self.assertEqual(len(components), 2)
    
    def test_cleanup_old_transactions(self):
        """Test cleaning up old transactions"""
        # Create some old transaction directories
        old_transaction_dir = os.path.join(self.manager.transactions_dir, "old_component_12345678")
        os.makedirs(old_transaction_dir, exist_ok=True)
        
        # Create a file in the transaction directory
        with open(os.path.join(old_transaction_dir, "test.txt"), 'w') as f:
            f.write("test")
        
        # Set modification time to be old (simulate old transaction)
        old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
        os.utime(old_transaction_dir, (old_time, old_time))
        
        cleaned_count = self.manager.cleanup_old_transactions(days_old=30)
        
        self.assertEqual(cleaned_count, 1)
        self.assertFalse(os.path.exists(old_transaction_dir))

class TestInstallationResult(unittest.TestCase):
    """Test InstallationResult data class"""
    
    def test_installation_result_creation(self):
        """Test creating installation result"""
        result = InstallationResult(
            success=True,
            status=InstallationStatus.COMPLETED,
            message="Installation successful",
            details={'component': 'test'},
            installation_time=10.5,
            rollback_available=True
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertEqual(result.message, "Installation successful")
        self.assertEqual(result.details['component'], 'test')
        self.assertEqual(result.installation_time, 10.5)
        self.assertTrue(result.rollback_available)

class TestRollbackInfo(unittest.TestCase):
    """Test RollbackInfo data class"""
    
    def test_rollback_info_creation(self):
        """Test creating rollback info"""
        rollback_info = RollbackInfo(
            rollback_id="test_rollback_001",
            component_name="test_component",
            timestamp=datetime.now()
        )
        
        self.assertEqual(rollback_info.rollback_id, "test_rollback_001")
        self.assertEqual(rollback_info.component_name, "test_component")
        self.assertIsInstance(rollback_info.timestamp, datetime)
        self.assertEqual(len(rollback_info.operations), 0)
        self.assertEqual(len(rollback_info.backup_paths), 0)
        self.assertEqual(len(rollback_info.installed_files), 0)

if __name__ == '__main__':
    unittest.main()