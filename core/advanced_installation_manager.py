# -*- coding: utf-8 -*-
"""
Advanced Installation Manager for Environment Dev Deep Evaluation
Implements robust installation infrastructure with automatic rollback capabilities
"""

import os
import sys
import logging
import subprocess
import shutil
import tempfile
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Set, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class InstallationStatus(Enum):
    """Status of installation operations"""
    PENDING = "pending"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"

class TransactionState(Enum):
    """State of atomic transaction"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMMITTING = "committing"
    COMMITTED = "committed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

@dataclass
class AtomicOperation:
    """Represents an atomic operation that can be rolled back"""
    operation_id: str
    operation_type: str  # "create_file", "create_dir", "modify_file", "set_env_var", etc.
    target_path: Optional[str] = None
    backup_path: Optional[str] = None
    original_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    completed: bool = False
    rollback_completed: bool = False

@dataclass
class RollbackInfo:
    """Information for rolling back an installation"""
    rollback_id: str
    component_name: str
    timestamp: datetime
    operations: List[AtomicOperation] = field(default_factory=list)
    backup_paths: List[str] = field(default_factory=list)
    registry_backups: List[str] = field(default_factory=list)
    env_vars_backup: Dict[str, str] = field(default_factory=dict)
    installed_files: List[str] = field(default_factory=list)
    created_directories: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    rollback_script: Optional[str] = None
    transaction_log: List[str] = field(default_factory=list)

@dataclass
class InstallationState:
    """Current state of an installation"""
    component: str
    status: InstallationStatus
    progress: float = 0.0
    current_step: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_info: Optional[RollbackInfo] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    transaction_id: Optional[str] = None
    atomic_operations: List[AtomicOperation] = field(default_factory=list)

@dataclass
class InstallationResult:
    """Result of an installation operation"""
    success: bool
    status: InstallationStatus
    message: str
    details: Dict[str, Any]
    installed_path: Optional[str] = None
    version: Optional[str] = None
    rollback_info: Optional[RollbackInfo] = None
    installation_time: float = 0.0
    verification_result: Optional[Dict] = None
    transaction_id: Optional[str] = None
    operations_count: int = 0
    rollback_available: bool = False

class AtomicTransaction:
    """Manages atomic installation transactions with rollback capability"""
    
    def __init__(self, transaction_id: str, component_name: str, base_path: str):
        self.transaction_id = transaction_id
        self.component_name = component_name
        self.base_path = base_path
        self.state = TransactionState.INACTIVE
        self.operations: List[AtomicOperation] = []
        self.rollback_info = RollbackInfo(
            rollback_id=transaction_id,
            component_name=component_name,
            timestamp=datetime.now()
        )
        self.logger = logging.getLogger(f"{__name__}.AtomicTransaction")
        self._lock = threading.Lock()
        
        # Create transaction directory
        self.transaction_dir = os.path.join(base_path, "transactions", transaction_id)
        os.makedirs(self.transaction_dir, exist_ok=True)
    
    def begin(self) -> bool:
        """Begin atomic transaction"""
        with self._lock:
            if self.state != TransactionState.INACTIVE:
                self.logger.error(f"Cannot begin transaction {self.transaction_id}: already {self.state.value}")
                return False
            
            self.state = TransactionState.ACTIVE
            self.rollback_info.transaction_log.append(f"Transaction {self.transaction_id} began at {datetime.now()}")
            self.logger.info(f"Atomic transaction {self.transaction_id} began for {self.component_name}")
            return True
    
    def add_operation(self, operation: AtomicOperation) -> bool:
        """Add operation to transaction"""
        with self._lock:
            if self.state != TransactionState.ACTIVE:
                self.logger.error(f"Cannot add operation: transaction {self.transaction_id} is {self.state.value}")
                return False
            
            self.operations.append(operation)
            self.rollback_info.operations.append(operation)
            self.rollback_info.transaction_log.append(
                f"Added operation {operation.operation_type} for {operation.target_path}"
            )
            return True
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of file/directory before modification"""
        try:
            if not os.path.exists(file_path):
                return None
            
            backup_name = f"backup_{uuid.uuid4().hex[:8]}_{os.path.basename(file_path)}"
            backup_path = os.path.join(self.transaction_dir, backup_name)
            
            if os.path.isdir(file_path):
                shutil.copytree(file_path, backup_path)
            else:
                shutil.copy2(file_path, backup_path)
            
            self.rollback_info.backup_paths.append(backup_path)
            self.logger.debug(f"Created backup: {file_path} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def execute_operation(self, operation: AtomicOperation) -> bool:
        """Execute a single atomic operation"""
        try:
            if operation.operation_type == "create_file":
                return self._execute_create_file(operation)
            elif operation.operation_type == "create_directory":
                return self._execute_create_directory(operation)
            elif operation.operation_type == "modify_file":
                return self._execute_modify_file(operation)
            elif operation.operation_type == "set_env_var":
                return self._execute_set_env_var(operation)
            elif operation.operation_type == "run_command":
                return self._execute_run_command(operation)
            elif operation.operation_type == "extract_archive":
                return self._execute_extract_archive(operation)
            else:
                self.logger.error(f"Unknown operation type: {operation.operation_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to execute operation {operation.operation_id}: {e}")
            return False
    
    def _execute_create_file(self, operation: AtomicOperation) -> bool:
        """Execute create file operation"""
        try:
            target_path = operation.target_path
            content = operation.new_value or ""
            
            # Create backup if file exists
            if os.path.exists(target_path):
                operation.backup_path = self.create_backup(target_path)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Write file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            operation.completed = True
            self.rollback_info.installed_files.append(target_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create file {operation.target_path}: {e}")
            return False
    
    def _execute_create_directory(self, operation: AtomicOperation) -> bool:
        """Execute create directory operation"""
        try:
            target_path = operation.target_path
            
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)
                operation.completed = True
                self.rollback_info.created_directories.append(target_path)
                return True
            else:
                # Directory already exists
                operation.completed = True
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create directory {operation.target_path}: {e}")
            return False
    
    def _execute_modify_file(self, operation: AtomicOperation) -> bool:
        """Execute modify file operation"""
        try:
            target_path = operation.target_path
            new_content = operation.new_value
            
            # Create backup
            operation.backup_path = self.create_backup(target_path)
            
            # Read original content
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    operation.original_value = f.read()
            
            # Write new content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            operation.completed = True
            self.rollback_info.modified_files.append(target_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to modify file {operation.target_path}: {e}")
            return False
    
    def _execute_set_env_var(self, operation: AtomicOperation) -> bool:
        """Execute set environment variable operation"""
        try:
            var_name = operation.metadata.get('var_name')
            var_value = operation.new_value
            scope = operation.metadata.get('scope', 'user')
            
            # Backup original value
            operation.original_value = os.environ.get(var_name)
            if operation.original_value:
                self.rollback_info.env_vars_backup[var_name] = operation.original_value
            
            # Set environment variable
            from utils.env_manager import set_env_var
            if set_env_var(var_name, var_value, scope=scope):
                operation.completed = True
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set environment variable: {e}")
            return False
    
    def _execute_run_command(self, operation: AtomicOperation) -> bool:
        """Execute run command operation"""
        try:
            command = operation.metadata.get('command', [])
            cwd = operation.metadata.get('cwd')
            timeout = operation.metadata.get('timeout', 300)
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            operation.metadata['return_code'] = result.returncode
            operation.metadata['stdout'] = result.stdout
            operation.metadata['stderr'] = result.stderr
            
            if result.returncode == 0:
                operation.completed = True
                return True
            else:
                self.logger.error(f"Command failed with code {result.returncode}: {' '.join(command)}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {operation.metadata.get('command')}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to run command: {e}")
            return False
    
    def _execute_extract_archive(self, operation: AtomicOperation) -> bool:
        """Execute extract archive operation"""
        try:
            archive_path = operation.metadata.get('archive_path')
            extract_path = operation.target_path
            
            # Create backup if directory exists and is not empty
            if os.path.exists(extract_path) and os.listdir(extract_path):
                operation.backup_path = self.create_backup(extract_path)
            
            # Extract archive
            from utils.extractor import extract_archive
            if extract_archive(archive_path, extract_path):
                operation.completed = True
                self.rollback_info.created_directories.append(extract_path)
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to extract archive: {e}")
            return False
    
    def commit(self) -> bool:
        """Commit transaction"""
        with self._lock:
            if self.state != TransactionState.ACTIVE:
                self.logger.error(f"Cannot commit transaction {self.transaction_id}: state is {self.state.value}")
                return False
            
            self.state = TransactionState.COMMITTING
            
            try:
                # Save transaction info for future reference
                self._save_transaction_info()
                
                self.state = TransactionState.COMMITTED
                self.rollback_info.transaction_log.append(f"Transaction {self.transaction_id} committed at {datetime.now()}")
                self.logger.info(f"Transaction {self.transaction_id} committed successfully")
                return True
                
            except Exception as e:
                self.state = TransactionState.FAILED
                self.logger.error(f"Failed to commit transaction {self.transaction_id}: {e}")
                return False
    
    def rollback(self) -> bool:
        """Rollback transaction"""
        with self._lock:
            if self.state not in [TransactionState.ACTIVE, TransactionState.FAILED, TransactionState.COMMITTED]:
                self.logger.error(f"Cannot rollback transaction {self.transaction_id}: state is {self.state.value}")
                return False
            
            self.state = TransactionState.ROLLING_BACK
            self.logger.info(f"Rolling back transaction {self.transaction_id}")
            
            success = True
            
            # Rollback operations in reverse order
            for operation in reversed(self.operations):
                if operation.completed and not operation.rollback_completed:
                    if not self._rollback_operation(operation):
                        success = False
                        self.logger.error(f"Failed to rollback operation {operation.operation_id}")
                    else:
                        operation.rollback_completed = True
            
            # Clean up created directories (in reverse order)
            for directory in reversed(self.rollback_info.created_directories):
                try:
                    if os.path.exists(directory) and os.path.isdir(directory):
                        shutil.rmtree(directory)
                        self.logger.debug(f"Removed directory: {directory}")
                except Exception as e:
                    self.logger.error(f"Failed to remove directory {directory}: {e}")
                    success = False
            
            # Remove installed files
            for file_path in reversed(self.rollback_info.installed_files):
                try:
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        os.remove(file_path)
                        self.logger.debug(f"Removed file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to remove file {file_path}: {e}")
                    success = False
            
            # Restore environment variables
            for var_name, original_value in self.rollback_info.env_vars_backup.items():
                try:
                    from utils.env_manager import set_env_var, unset_env_var
                    if original_value is None:
                        unset_env_var(var_name)
                    else:
                        set_env_var(var_name, original_value)
                    self.logger.debug(f"Restored environment variable: {var_name}")
                except Exception as e:
                    self.logger.error(f"Failed to restore environment variable {var_name}: {e}")
                    success = False
            
            self.state = TransactionState.ROLLED_BACK if success else TransactionState.FAILED
            self.rollback_info.transaction_log.append(
                f"Transaction {self.transaction_id} rollback {'completed' if success else 'failed'} at {datetime.now()}"
            )
            
            return success
    
    def _rollback_operation(self, operation: AtomicOperation) -> bool:
        """Rollback a single operation"""
        try:
            if operation.operation_type == "create_file":
                return self._rollback_create_file(operation)
            elif operation.operation_type == "create_directory":
                return self._rollback_create_directory(operation)
            elif operation.operation_type == "modify_file":
                return self._rollback_modify_file(operation)
            elif operation.operation_type == "set_env_var":
                return self._rollback_set_env_var(operation)
            elif operation.operation_type == "run_command":
                return self._rollback_run_command(operation)
            elif operation.operation_type == "extract_archive":
                return self._rollback_extract_archive(operation)
            else:
                self.logger.warning(f"No rollback handler for operation type: {operation.operation_type}")
                return True  # Assume success for unknown operations
                
        except Exception as e:
            self.logger.error(f"Failed to rollback operation {operation.operation_id}: {e}")
            return False
    
    def _rollback_create_file(self, operation: AtomicOperation) -> bool:
        """Rollback create file operation"""
        try:
            target_path = operation.target_path
            
            if operation.backup_path and os.path.exists(operation.backup_path):
                # Restore from backup
                shutil.copy2(operation.backup_path, target_path)
                self.logger.debug(f"Restored file from backup: {target_path}")
            else:
                # Remove created file
                if os.path.exists(target_path):
                    os.remove(target_path)
                    self.logger.debug(f"Removed created file: {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback create file {operation.target_path}: {e}")
            return False
    
    def _rollback_create_directory(self, operation: AtomicOperation) -> bool:
        """Rollback create directory operation"""
        try:
            target_path = operation.target_path
            
            if os.path.exists(target_path) and os.path.isdir(target_path):
                # Only remove if directory is empty or was created by us
                try:
                    os.rmdir(target_path)  # Only removes empty directories
                    self.logger.debug(f"Removed created directory: {target_path}")
                except OSError:
                    # Directory not empty, leave it
                    self.logger.debug(f"Directory not empty, leaving: {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback create directory {operation.target_path}: {e}")
            return False
    
    def _rollback_modify_file(self, operation: AtomicOperation) -> bool:
        """Rollback modify file operation"""
        try:
            target_path = operation.target_path
            
            if operation.backup_path and os.path.exists(operation.backup_path):
                # Restore from backup
                shutil.copy2(operation.backup_path, target_path)
                self.logger.debug(f"Restored modified file from backup: {target_path}")
            elif operation.original_value is not None:
                # Restore original content
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(operation.original_value)
                self.logger.debug(f"Restored original content: {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback modify file {operation.target_path}: {e}")
            return False
    
    def _rollback_set_env_var(self, operation: AtomicOperation) -> bool:
        """Rollback set environment variable operation"""
        try:
            var_name = operation.metadata.get('var_name')
            
            from utils.env_manager import set_env_var, unset_env_var
            
            if operation.original_value is not None:
                set_env_var(var_name, operation.original_value)
                self.logger.debug(f"Restored environment variable: {var_name}")
            else:
                unset_env_var(var_name)
                self.logger.debug(f"Removed environment variable: {var_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback environment variable: {e}")
            return False
    
    def _rollback_run_command(self, operation: AtomicOperation) -> bool:
        """Rollback run command operation"""
        try:
            # Check if there's a rollback command
            rollback_command = operation.metadata.get('rollback_command')
            
            if rollback_command:
                result = subprocess.run(
                    rollback_command,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False
                )
                
                if result.returncode == 0:
                    self.logger.debug(f"Executed rollback command successfully")
                    return True
                else:
                    self.logger.error(f"Rollback command failed with code {result.returncode}")
                    return False
            else:
                # No rollback command specified, assume success
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to rollback command: {e}")
            return False
    
    def _rollback_extract_archive(self, operation: AtomicOperation) -> bool:
        """Rollback extract archive operation"""
        try:
            target_path = operation.target_path
            
            if operation.backup_path and os.path.exists(operation.backup_path):
                # Restore from backup
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(operation.backup_path, target_path)
                self.logger.debug(f"Restored extracted directory from backup: {target_path}")
            else:
                # Remove extracted directory
                if os.path.exists(target_path) and os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                    self.logger.debug(f"Removed extracted directory: {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback extract archive {operation.target_path}: {e}")
            return False
    
    def _save_transaction_info(self) -> None:
        """Save transaction information to disk"""
        try:
            transaction_file = os.path.join(self.transaction_dir, "transaction.json")
            
            transaction_data = {
                'transaction_id': self.transaction_id,
                'component_name': self.component_name,
                'state': self.state.value,
                'timestamp': self.rollback_info.timestamp.isoformat(),
                'operations_count': len(self.operations),
                'rollback_info': {
                    'backup_paths': self.rollback_info.backup_paths,
                    'installed_files': self.rollback_info.installed_files,
                    'created_directories': self.rollback_info.created_directories,
                    'modified_files': self.rollback_info.modified_files,
                    'env_vars_backup': self.rollback_info.env_vars_backup,
                    'transaction_log': self.rollback_info.transaction_log
                }
            }
            
            with open(transaction_file, 'w', encoding='utf-8') as f:
                json.dump(transaction_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved transaction info to {transaction_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save transaction info: {e}")

class AdvancedInstallationManager:
    """
    Advanced Installation Manager with atomic operations and automatic rollback
    
    Features:
    - Atomic installation operations with transaction-like behavior
    - Automatic rollback capabilities on failure
    - Installation state tracking and progress reporting
    - Thread-safe operations
    - Comprehensive error handling
    """
    
    def __init__(self, security_manager=None, base_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.security_manager = security_manager
        self.base_path = base_path or os.getcwd()
        
        # Initialize directories
        self.transactions_dir = os.path.join(self.base_path, "transactions")
        self.rollback_dir = os.path.join(self.base_path, "rollback")
        os.makedirs(self.transactions_dir, exist_ok=True)
        os.makedirs(self.rollback_dir, exist_ok=True)
        
        # State management
        self.installation_states: Dict[str, InstallationState] = {}
        self.active_transactions: Dict[str, AtomicTransaction] = {}
        self._lock = threading.Lock()
        
        self.logger.info("Advanced Installation Manager initialized")
    
    def install_component_atomic(self, component: str, component_data: Dict[str, Any], 
                                progress_callback: Optional[callable] = None) -> InstallationResult:
        """
        Install component using atomic operations with automatic rollback
        
        Args:
            component: Name of the component to install
            component_data: Component configuration data
            progress_callback: Optional callback for progress updates
            
        Returns:
            InstallationResult: Result of the installation
        """
        start_time = datetime.now()
        transaction_id = f"{component}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"Starting atomic installation of {component} (transaction: {transaction_id})")
        
        # Create installation state
        state = InstallationState(
            component=component,
            status=InstallationStatus.PREPARING,
            transaction_id=transaction_id
        )
        
        with self._lock:
            self.installation_states[component] = state
        
        # Create atomic transaction
        transaction = AtomicTransaction(transaction_id, component, self.base_path)
        
        with self._lock:
            self.active_transactions[transaction_id] = transaction
        
        try:
            # Begin transaction
            if not transaction.begin():
                return self._create_failure_result(
                    component, "Failed to begin atomic transaction", 
                    start_time, transaction_id
                )
            
            # Update progress
            if progress_callback:
                progress_callback("Beginning atomic installation transaction...")
            
            # Phase 1: Preparation
            state.status = InstallationStatus.PREPARING
            state.current_step = "Preparing installation environment"
            state.progress = 10.0
            
            if not self._prepare_installation_atomic(component, component_data, transaction, progress_callback):
                transaction.rollback()
                return self._create_failure_result(
                    component, "Failed during preparation phase", 
                    start_time, transaction_id
                )
            
            # Phase 2: Download (if needed)
            if component_data.get('download_url'):
                state.status = InstallationStatus.DOWNLOADING
                state.current_step = "Downloading component files"
                state.progress = 30.0
                
                if progress_callback:
                    progress_callback("Downloading component files...")
                
                if not self._download_component_atomic(component, component_data, transaction):
                    transaction.rollback()
                    return self._create_failure_result(
                        component, "Failed during download phase", 
                        start_time, transaction_id
                    )
            
            # Phase 3: Installation
            state.status = InstallationStatus.INSTALLING
            state.current_step = "Installing component"
            state.progress = 60.0
            
            if progress_callback:
                progress_callback("Installing component...")
            
            if not self._install_component_atomic(component, component_data, transaction):
                transaction.rollback()
                return self._create_failure_result(
                    component, "Failed during installation phase", 
                    start_time, transaction_id
                )
            
            # Phase 4: Verification
            state.status = InstallationStatus.VERIFYING
            state.current_step = "Verifying installation"
            state.progress = 90.0
            
            if progress_callback:
                progress_callback("Verifying installation...")
            
            verification_result = self._verify_installation_atomic(component, component_data)
            if not verification_result['success']:
                transaction.rollback()
                return self._create_failure_result(
                    component, f"Installation verification failed: {verification_result['message']}", 
                    start_time, transaction_id
                )
            
            # Commit transaction
            if not transaction.commit():
                transaction.rollback()
                return self._create_failure_result(
                    component, "Failed to commit transaction", 
                    start_time, transaction_id
                )
            
            # Success
            state.status = InstallationStatus.COMPLETED
            state.current_step = "Installation completed successfully"
            state.progress = 100.0
            state.end_time = datetime.now()
            
            installation_time = (state.end_time - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("Installation completed successfully!")
            
            self.logger.info(f"Atomic installation of {component} completed successfully in {installation_time:.2f}s")
            
            return InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message=f"Component {component} installed successfully",
                details={
                    'component': component,
                    'installation_time': installation_time,
                    'verification': verification_result,
                    'transaction_id': transaction_id,
                    'operations_count': len(transaction.operations)
                },
                installed_path=verification_result.get('installed_path'),
                version=verification_result.get('version'),
                rollback_info=transaction.rollback_info,
                installation_time=installation_time,
                verification_result=verification_result,
                transaction_id=transaction_id,
                operations_count=len(transaction.operations),
                rollback_available=True
            )
            
        except Exception as e:
            self.logger.error(f"Critical error during atomic installation of {component}: {e}")
            
            # Attempt rollback
            try:
                transaction.rollback()
                self.logger.info(f"Rollback completed for {component}")
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed for {component}: {rollback_error}")
            
            return self._create_failure_result(
                component, f"Critical installation error: {e}", 
                start_time, transaction_id
            )
        
        finally:
            # Clean up
            with self._lock:
                if transaction_id in self.active_transactions:
                    del self.active_transactions[transaction_id]
    
    def _prepare_installation_atomic(self, component: str, component_data: Dict[str, Any], 
                                   transaction: AtomicTransaction, progress_callback: Optional[callable] = None) -> bool:
        """Prepare installation environment atomically"""
        try:
            # Create necessary directories
            directories_to_create = [
                os.path.join(self.base_path, "downloads", component),
                os.path.join(self.base_path, "temp", component),
                os.path.join(self.base_path, "logs", component),
                os.path.join(self.base_path, "config", component)
            ]
            
            for directory in directories_to_create:
                if not os.path.exists(directory):
                    operation = AtomicOperation(
                        operation_id=f"create_dir_{uuid.uuid4().hex[:8]}",
                        operation_type="create_directory",
                        target_path=directory
                    )
                    
                    if not transaction.add_operation(operation):
                        return False
                    
                    if not transaction.execute_operation(operation):
                        return False
            
            # Set up environment variables if specified
            env_vars = component_data.get('environment_variables', {})
            for var_name, var_value in env_vars.items():
                operation = AtomicOperation(
                    operation_id=f"set_env_{uuid.uuid4().hex[:8]}",
                    operation_type="set_env_var",
                    new_value=var_value,
                    metadata={'var_name': var_name, 'scope': 'user'}
                )
                
                if not transaction.add_operation(operation):
                    return False
                
                if not transaction.execute_operation(operation):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to prepare installation for {component}: {e}")
            return False
    
    def _download_component_atomic(self, component: str, component_data: Dict[str, Any], 
                                 transaction: AtomicTransaction) -> bool:
        """Download component files atomically"""
        try:
            download_url = component_data.get('download_url')
            if not download_url:
                return True  # No download needed
            
            download_path = os.path.join(self.base_path, "downloads", component)
            filename = component_data.get('filename') or f"{component}.zip"
            file_path = os.path.join(download_path, filename)
            
            # Use robust download manager
            from core.robust_download_manager import RobustDownloadManager
            download_manager = RobustDownloadManager()
            
            expected_hash = component_data.get('sha256_hash')
            download_result = download_manager.download_with_mandatory_hash_verification(
                download_url, expected_hash
            )
            
            if not download_result.success:
                self.logger.error(f"Download failed for {component}: {download_result.message}")
                return False
            
            # Move downloaded file to correct location
            if download_result.file_path != file_path:
                operation = AtomicOperation(
                    operation_id=f"move_file_{uuid.uuid4().hex[:8]}",
                    operation_type="create_file",
                    target_path=file_path
                )
                
                if not transaction.add_operation(operation):
                    return False
                
                # Copy file content
                with open(download_result.file_path, 'rb') as src, open(file_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                
                operation.completed = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download component {component}: {e}")
            return False
    
    def _install_component_atomic(self, component: str, component_data: Dict[str, Any], 
                                transaction: AtomicTransaction) -> bool:
        """Install component atomically"""
        try:
            install_method = component_data.get('install_method', 'archive')
            
            if install_method == 'archive':
                return self._install_archive_atomic(component, component_data, transaction)
            elif install_method == 'executable':
                return self._install_executable_atomic(component, component_data, transaction)
            elif install_method == 'msi':
                return self._install_msi_atomic(component, component_data, transaction)
            elif install_method == 'script':
                return self._install_script_atomic(component, component_data, transaction)
            else:
                self.logger.error(f"Unsupported install method: {install_method}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to install component {component}: {e}")
            return False
    
    def _install_archive_atomic(self, component: str, component_data: Dict[str, Any], 
                              transaction: AtomicTransaction) -> bool:
        """Install archive atomically"""
        try:
            download_path = os.path.join(self.base_path, "downloads", component)
            filename = component_data.get('filename') or f"{component}.zip"
            archive_path = os.path.join(download_path, filename)
            
            install_path = component_data.get('install_path') or os.path.join(self.base_path, component)
            
            # Extract archive
            operation = AtomicOperation(
                operation_id=f"extract_{uuid.uuid4().hex[:8]}",
                operation_type="extract_archive",
                target_path=install_path,
                metadata={'archive_path': archive_path}
            )
            
            if not transaction.add_operation(operation):
                return False
            
            return transaction.execute_operation(operation)
            
        except Exception as e:
            self.logger.error(f"Failed to install archive for {component}: {e}")
            return False
    
    def _install_executable_atomic(self, component: str, component_data: Dict[str, Any], 
                                 transaction: AtomicTransaction) -> bool:
        """Install executable atomically"""
        try:
            download_path = os.path.join(self.base_path, "downloads", component)
            filename = component_data.get('filename') or f"{component}.exe"
            exe_path = os.path.join(download_path, filename)
            
            install_args = component_data.get('install_args', ['/S'])
            command = [exe_path] + install_args
            
            # Run installer
            operation = AtomicOperation(
                operation_id=f"run_installer_{uuid.uuid4().hex[:8]}",
                operation_type="run_command",
                metadata={
                    'command': command,
                    'timeout': component_data.get('install_timeout', 300),
                    'rollback_command': component_data.get('uninstall_command')
                }
            )
            
            if not transaction.add_operation(operation):
                return False
            
            return transaction.execute_operation(operation)
            
        except Exception as e:
            self.logger.error(f"Failed to install executable for {component}: {e}")
            return False
    
    def _install_msi_atomic(self, component: str, component_data: Dict[str, Any], 
                          transaction: AtomicTransaction) -> bool:
        """Install MSI package atomically"""
        try:
            download_path = os.path.join(self.base_path, "downloads", component)
            filename = component_data.get('filename') or f"{component}.msi"
            msi_path = os.path.join(download_path, filename)
            
            install_args = component_data.get('install_args', ['/quiet'])
            command = ['msiexec', '/i', msi_path] + install_args
            
            # Run MSI installer
            operation = AtomicOperation(
                operation_id=f"run_msi_{uuid.uuid4().hex[:8]}",
                operation_type="run_command",
                metadata={
                    'command': command,
                    'timeout': component_data.get('install_timeout', 300),
                    'rollback_command': ['msiexec', '/x', msi_path, '/quiet']
                }
            )
            
            if not transaction.add_operation(operation):
                return False
            
            return transaction.execute_operation(operation)
            
        except Exception as e:
            self.logger.error(f"Failed to install MSI for {component}: {e}")
            return False
    
    def _install_script_atomic(self, component: str, component_data: Dict[str, Any], 
                             transaction: AtomicTransaction) -> bool:
        """Install using script atomically"""
        try:
            script_path = component_data.get('script_path')
            if not script_path:
                self.logger.error(f"No script path specified for {component}")
                return False
            
            script_args = component_data.get('script_args', [])
            
            # Determine script type and command
            if script_path.lower().endswith('.ps1'):
                command = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path] + script_args
            elif script_path.lower().endswith(('.bat', '.cmd')):
                command = [script_path] + script_args
            else:
                command = [script_path] + script_args
            
            # Run script
            operation = AtomicOperation(
                operation_id=f"run_script_{uuid.uuid4().hex[:8]}",
                operation_type="run_command",
                metadata={
                    'command': command,
                    'cwd': component_data.get('script_cwd'),
                    'timeout': component_data.get('script_timeout', 300),
                    'rollback_command': component_data.get('rollback_script')
                }
            )
            
            if not transaction.add_operation(operation):
                return False
            
            return transaction.execute_operation(operation)
            
        except Exception as e:
            self.logger.error(f"Failed to install script for {component}: {e}")
            return False
    
    def _verify_installation_atomic(self, component: str, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify installation atomically"""
        try:
            verification_commands = component_data.get('verification_commands', [])
            verification_paths = component_data.get('verification_paths', [])
            
            result = {
                'success': True,
                'message': 'Installation verified successfully',
                'details': {}
            }
            
            # Check verification paths
            for path in verification_paths:
                if not os.path.exists(path):
                    result['success'] = False
                    result['message'] = f'Verification failed: path not found: {path}'
                    return result
                else:
                    result['details'][f'path_{path}'] = 'exists'
            
            # Run verification commands
            for i, command in enumerate(verification_commands):
                try:
                    cmd_result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if cmd_result.returncode != 0:
                        result['success'] = False
                        result['message'] = f'Verification command failed: {" ".join(command)}'
                        result['details'][f'command_{i}'] = {
                            'return_code': cmd_result.returncode,
                            'stderr': cmd_result.stderr
                        }
                        return result
                    else:
                        result['details'][f'command_{i}'] = {
                            'return_code': cmd_result.returncode,
                            'stdout': cmd_result.stdout
                        }
                        
                except subprocess.TimeoutExpired:
                    result['success'] = False
                    result['message'] = f'Verification command timed out: {" ".join(command)}'
                    return result
            
            # Try to detect installed path and version
            install_path = component_data.get('install_path')
            if install_path and os.path.exists(install_path):
                result['installed_path'] = install_path
            
            version_command = component_data.get('version_command')
            if version_command:
                try:
                    version_result = subprocess.run(
                        version_command,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False
                    )
                    
                    if version_result.returncode == 0:
                        result['version'] = version_result.stdout.strip()
                        
                except Exception:
                    pass  # Version detection is optional
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to verify installation for {component}: {e}")
            return {
                'success': False,
                'message': f'Verification error: {e}',
                'details': {}
            }
    
    def _create_failure_result(self, component: str, message: str, start_time: datetime, 
                             transaction_id: str) -> InstallationResult:
        """Create failure result"""
        end_time = datetime.now()
        installation_time = (end_time - start_time).total_seconds()
        
        # Update state
        if component in self.installation_states:
            state = self.installation_states[component]
            state.status = InstallationStatus.FAILED
            state.error_message = message
            state.end_time = end_time
        
        self.logger.error(f"Installation failed for {component}: {message}")
        
        return InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message=message,
            details={
                'component': component,
                'error': message,
                'installation_time': installation_time,
                'transaction_id': transaction_id
            },
            installation_time=installation_time,
            transaction_id=transaction_id,
            rollback_available=True
        )
    
    def rollback_component(self, component: str) -> bool:
        """
        Rollback a component installation
        
        Args:
            component: Name of the component to rollback
            
        Returns:
            bool: True if rollback was successful
        """
        try:
            # Find the most recent transaction for this component
            transaction_id = None
            
            if component in self.installation_states:
                state = self.installation_states[component]
                transaction_id = state.transaction_id
            
            if not transaction_id:
                # Look for saved transaction info
                component_transactions = []
                for filename in os.listdir(self.transactions_dir):
                    if filename.startswith(component) and os.path.isdir(os.path.join(self.transactions_dir, filename)):
                        component_transactions.append(filename)
                
                if component_transactions:
                    # Use the most recent transaction
                    transaction_id = sorted(component_transactions)[-1]
            
            if not transaction_id:
                self.logger.error(f"No transaction found for component {component}")
                return False
            
            # Load or get transaction
            transaction = None
            if transaction_id in self.active_transactions:
                transaction = self.active_transactions[transaction_id]
            else:
                # Try to load from disk
                transaction_dir = os.path.join(self.transactions_dir, transaction_id)
                if os.path.exists(transaction_dir):
                    transaction = AtomicTransaction(transaction_id, component, self.base_path)
                    # Load transaction state from disk if needed
            
            if not transaction:
                self.logger.error(f"Could not load transaction {transaction_id} for component {component}")
                return False
            
            # Perform rollback
            self.logger.info(f"Rolling back component {component} (transaction: {transaction_id})")
            
            success = transaction.rollback()
            
            if success:
                self.logger.info(f"Rollback completed successfully for {component}")
                
                # Update state
                if component in self.installation_states:
                    state = self.installation_states[component]
                    state.status = InstallationStatus.ROLLED_BACK
                    state.current_step = "Rollback completed"
                    state.end_time = datetime.now()
            else:
                self.logger.error(f"Rollback failed for {component}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during rollback of {component}: {e}")
            return False
    
    def get_installation_state(self, component: str) -> Optional[InstallationState]:
        """Get current installation state for a component"""
        return self.installation_states.get(component)
    
    def list_rollback_available_components(self) -> List[str]:
        """List components that have rollback information available"""
        components = []
        
        try:
            # Check active transactions
            for transaction_id, transaction in self.active_transactions.items():
                if transaction.component_name not in components:
                    components.append(transaction.component_name)
            
            # Check saved transactions
            if os.path.exists(self.transactions_dir):
                for item in os.listdir(self.transactions_dir):
                    item_path = os.path.join(self.transactions_dir, item)
                    if os.path.isdir(item_path):
                        # Extract component name from transaction ID
                        component_name = item.split('_')[0]
                        if component_name not in components:
                            components.append(component_name)
            
        except Exception as e:
            self.logger.error(f"Error listing rollback available components: {e}")
        
        return sorted(components)
    
    def cleanup_old_transactions(self, days_old: int = 30) -> int:
        """
        Clean up old transaction data
        
        Args:
            days_old: Remove transactions older than this many days
            
        Returns:
            int: Number of transactions cleaned up
        """
        cleaned_count = 0
        
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            
            if os.path.exists(self.transactions_dir):
                for item in os.listdir(self.transactions_dir):
                    item_path = os.path.join(self.transactions_dir, item)
                    
                    if os.path.isdir(item_path):
                        # Check modification time
                        mod_time = datetime.fromtimestamp(os.path.getmtime(item_path))
                        
                        if mod_time < cutoff_time:
                            try:
                                shutil.rmtree(item_path)
                                cleaned_count += 1
                                self.logger.debug(f"Cleaned up old transaction: {item}")
                            except Exception as e:
                                self.logger.warning(f"Failed to clean up transaction {item}: {e}")
            
            self.logger.info(f"Cleaned up {cleaned_count} old transactions")
            
        except Exception as e:
            self.logger.error(f"Error during transaction cleanup: {e}")
        
        return cleaned_count