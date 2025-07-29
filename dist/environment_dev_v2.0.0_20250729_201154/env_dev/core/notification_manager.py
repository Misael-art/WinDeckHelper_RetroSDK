#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Notification Manager for Environment Dev
Provides structured feedback system with categorization, progress tracking, and operation history
"""

import logging
import threading
import queue
import time
import json
import uuid
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import os

# Import existing notification system
try:
    from env_dev.gui.notification_system import (
        NotificationCenter, NotificationLevel, NotificationCategory,
        Notification, ProgressTracker
    )
except ImportError:
    # Fallback if GUI is not available
    NotificationCenter = None
    NotificationLevel = None
    NotificationCategory = None
    Notification = None
    ProgressTracker = None

# Import logging system
from env_dev.utils.log_manager import setup_logging

class NotificationSeverity(Enum):
    """Enhanced notification severity levels"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    PROGRESS = "progress"

class OperationCategory(Enum):
    """Operation categories for better organization"""
    SYSTEM = "system"
    DIAGNOSTIC = "diagnostic"
    DOWNLOAD = "download"
    INSTALLATION = "installation"
    PREPARATION = "preparation"
    ORGANIZATION = "organization"
    RECOVERY = "recovery"
    CLEANUP = "cleanup"
    USER_ACTION = "user_action"
    SECURITY = "security"
    CONFIGURATION = "configuration"

class OperationStatus(Enum):
    """Operation status tracking"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class StructuredNotification:
    """Enhanced notification with structured data"""
    id: str
    severity: NotificationSeverity
    category: OperationCategory
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    operation_id: Optional[str] = None
    component: Optional[str] = None
    progress: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    user_action_required: bool = False
    dismissible: bool = True
    persistent: bool = False
    auto_dismiss_after: int = 5000  # milliseconds
    related_notifications: List[str] = field(default_factory=list)

@dataclass
class OperationRecord:
    """Complete operation tracking record"""
    operation_id: str
    category: OperationCategory
    name: str
    description: str
    status: OperationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    progress: float = 0.0
    total_steps: int = 0
    current_step: int = 0
    step_descriptions: Dict[int, str] = field(default_factory=dict)
    notifications: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class NotificationManager:
    """
    Advanced notification manager providing structured feedback system
    with categorization, progress tracking, and comprehensive operation history
    """
    
    def __init__(self, 
                 gui_parent=None,
                 log_dir: Optional[str] = None,
                 enable_gui_notifications: bool = True,
                 enable_file_logging: bool = True,
                 max_history_size: int = 1000):
        """
        Initialize the notification manager
        
        Args:
            gui_parent: Parent window for GUI notifications
            log_dir: Directory for log files
            enable_gui_notifications: Enable GUI toast notifications
            enable_file_logging: Enable file-based logging
            max_history_size: Maximum number of notifications to keep in history
        """
        self.gui_parent = gui_parent
        self.enable_gui_notifications = enable_gui_notifications
        self.enable_file_logging = enable_file_logging
        self.max_history_size = max_history_size
        
        # Initialize logging
        self.logger, self.log_manager = setup_logging(
            log_dir=log_dir,
            log_file="notifications.log",
            console_level=logging.INFO,
            file_level=logging.DEBUG
        )
        
        # Initialize GUI notification center if available
        self.gui_notification_center = None
        if self.enable_gui_notifications and gui_parent and NotificationCenter:
            try:
                self.gui_notification_center = NotificationCenter(gui_parent)
            except Exception as e:
                self.logger.warning(f"Failed to initialize GUI notification center: {e}")
        
        # Internal storage
        self.notifications: Dict[str, StructuredNotification] = {}
        self.operations: Dict[str, OperationRecord] = {}
        self.notification_history: List[StructuredNotification] = []
        self.operation_history: List[OperationRecord] = []
        
        # Threading and queuing
        self.notification_queue = queue.Queue()
        self.processing_thread = None
        self.is_running = True
        
        # Statistics
        self.stats = {
            'total_notifications': 0,
            'notifications_by_severity': {},
            'notifications_by_category': {},
            'operations_completed': 0,
            'operations_failed': 0,
            'average_operation_duration': 0.0
        }
        
        # Start processing
        self.start_processing()
        
        self.logger.info("NotificationManager initialized successfully")
    
    def start_processing(self):
        """Start the notification processing thread"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_notifications,
                daemon=True
            )
            self.processing_thread.start()
    
    def stop_processing(self):
        """Stop the notification processing thread"""
        self.is_running = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
    
    def _process_notifications(self):
        """Process notifications from the queue"""
        while self.is_running:
            try:
                # Process all pending notifications
                while not self.notification_queue.empty():
                    notification = self.notification_queue.get_nowait()
                    self._handle_notification(notification)
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing notifications: {e}")
    
    def _handle_notification(self, notification: StructuredNotification):
        """Handle a single notification"""
        try:
            # Store notification
            self.notifications[notification.id] = notification
            self.notification_history.append(notification)
            
            # Maintain history size limit
            if len(self.notification_history) > self.max_history_size:
                old_notification = self.notification_history.pop(0)
                if old_notification.id in self.notifications:
                    del self.notifications[old_notification.id]
            
            # Update statistics
            self._update_stats(notification)
            
            # Log to file
            if self.enable_file_logging:
                self._log_notification(notification)
            
            # Show GUI notification
            if self.enable_gui_notifications and self.gui_notification_center:
                self._show_gui_notification(notification)
            
            # Update operation record if applicable
            if notification.operation_id and notification.operation_id in self.operations:
                operation = self.operations[notification.operation_id]
                operation.notifications.append(notification.id)
                
                # Update progress if provided
                if notification.progress is not None:
                    operation.progress = notification.progress
        
        except Exception as e:
            self.logger.error(f"Error handling notification {notification.id}: {e}")
    
    def _update_stats(self, notification: StructuredNotification):
        """Update notification statistics"""
        self.stats['total_notifications'] += 1
        
        # Update severity stats
        severity_key = notification.severity.value
        self.stats['notifications_by_severity'][severity_key] = \
            self.stats['notifications_by_severity'].get(severity_key, 0) + 1
        
        # Update category stats
        category_key = notification.category.value
        self.stats['notifications_by_category'][category_key] = \
            self.stats['notifications_by_category'].get(category_key, 0) + 1
    
    def _log_notification(self, notification: StructuredNotification):
        """Log notification to file"""
        try:
            # Map severity to logging level
            severity_mapping = {
                NotificationSeverity.TRACE: logging.DEBUG,
                NotificationSeverity.DEBUG: logging.DEBUG,
                NotificationSeverity.INFO: logging.INFO,
                NotificationSeverity.SUCCESS: 25,  # Custom SUCCESS level
                NotificationSeverity.WARNING: logging.WARNING,
                NotificationSeverity.ERROR: logging.ERROR,
                NotificationSeverity.CRITICAL: logging.CRITICAL,
                NotificationSeverity.PROGRESS: logging.INFO
            }
            
            log_level = severity_mapping.get(notification.severity, logging.INFO)
            
            # Create structured log message
            log_data = {
                'id': notification.id,
                'severity': notification.severity.value,
                'category': notification.category.value,
                'title': notification.title,
                'message': notification.message,
                'timestamp': notification.timestamp.isoformat(),
                'operation_id': notification.operation_id,
                'component': notification.component,
                'progress': notification.progress,
                'tags': notification.tags
            }
            
            if notification.details:
                log_data['details'] = notification.details
            
            if notification.context:
                log_data['context'] = notification.context
            
            # Log with appropriate level
            log_message = f"[{notification.category.value.upper()}] {notification.title}: {notification.message}"
            if notification.component:
                log_message = f"[{notification.component}] {log_message}"
            
            self.logger.log(log_level, log_message, extra={'structured_data': log_data})
            
        except Exception as e:
            self.logger.error(f"Error logging notification: {e}")
    
    def _show_gui_notification(self, notification: StructuredNotification):
        """Show GUI notification if available"""
        try:
            if not self.gui_notification_center:
                return
            
            # Map severity to GUI notification level
            severity_mapping = {
                NotificationSeverity.TRACE: NotificationLevel.INFO,
                NotificationSeverity.DEBUG: NotificationLevel.INFO,
                NotificationSeverity.INFO: NotificationLevel.INFO,
                NotificationSeverity.SUCCESS: NotificationLevel.SUCCESS,
                NotificationSeverity.WARNING: NotificationLevel.WARNING,
                NotificationSeverity.ERROR: NotificationLevel.ERROR,
                NotificationSeverity.CRITICAL: NotificationLevel.ERROR,
                NotificationSeverity.PROGRESS: NotificationLevel.PROGRESS
            }
            
            # Map category to GUI notification category
            category_mapping = {
                OperationCategory.SYSTEM: NotificationCategory.SYSTEM,
                OperationCategory.DIAGNOSTIC: NotificationCategory.DIAGNOSTIC,
                OperationCategory.DOWNLOAD: NotificationCategory.DOWNLOAD,
                OperationCategory.INSTALLATION: NotificationCategory.INSTALLATION,
                OperationCategory.PREPARATION: NotificationCategory.SYSTEM,
                OperationCategory.ORGANIZATION: NotificationCategory.CLEANUP,
                OperationCategory.RECOVERY: NotificationCategory.SYSTEM,
                OperationCategory.CLEANUP: NotificationCategory.CLEANUP,
                OperationCategory.USER_ACTION: NotificationCategory.USER_ACTION,
                OperationCategory.SECURITY: NotificationCategory.SYSTEM,
                OperationCategory.CONFIGURATION: NotificationCategory.SYSTEM
            }
            
            gui_level = severity_mapping.get(notification.severity, NotificationLevel.INFO)
            gui_category = category_mapping.get(notification.category, NotificationCategory.SYSTEM)
            
            # Create GUI notification
            gui_kwargs = {
                'progress': notification.progress,
                'details': json.dumps(notification.details) if notification.details else None,
                'persistent': notification.persistent,
                'auto_dismiss': notification.dismissible,
                'dismiss_after': notification.auto_dismiss_after
            }
            
            # Remove None values
            gui_kwargs = {k: v for k, v in gui_kwargs.items() if v is not None}
            
            self.gui_notification_center.notify(
                gui_level,
                gui_category,
                notification.title,
                notification.message,
                **gui_kwargs
            )
            
        except Exception as e:
            self.logger.error(f"Error showing GUI notification: {e}")
    
    def notify(self,
               severity: NotificationSeverity,
               category: OperationCategory,
               title: str,
               message: str,
               operation_id: Optional[str] = None,
               component: Optional[str] = None,
               progress: Optional[float] = None,
               details: Optional[Dict[str, Any]] = None,
               context: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None,
               **kwargs) -> str:
        """
        Create and queue a structured notification
        
        Args:
            severity: Notification severity level
            category: Operation category
            title: Notification title
            message: Notification message
            operation_id: Associated operation ID
            component: Component name
            progress: Progress percentage (0-100)
            details: Additional structured details
            context: Context information
            tags: Tags for categorization
            **kwargs: Additional notification parameters
            
        Returns:
            str: Notification ID
        """
        notification_id = str(uuid.uuid4())
        
        notification = StructuredNotification(
            id=notification_id,
            severity=severity,
            category=category,
            title=title,
            message=message,
            operation_id=operation_id,
            component=component,
            progress=progress,
            details=details or {},
            context=context or {},
            tags=tags or [],
            **kwargs
        )
        
        # Queue for processing
        self.notification_queue.put(notification)
        
        return notification_id
    
    def start_operation(self,
                       category: OperationCategory,
                       name: str,
                       description: str,
                       total_steps: int = 0,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a new operation
        
        Args:
            category: Operation category
            name: Operation name
            description: Operation description
            total_steps: Total number of steps (for progress tracking)
            metadata: Additional metadata
            
        Returns:
            str: Operation ID
        """
        operation_id = str(uuid.uuid4())
        
        operation = OperationRecord(
            operation_id=operation_id,
            category=category,
            name=name,
            description=description,
            status=OperationStatus.RUNNING,
            start_time=datetime.now(),
            total_steps=total_steps,
            metadata=metadata or {}
        )
        
        self.operations[operation_id] = operation
        
        # Send initial notification
        self.notify(
            NotificationSeverity.INFO,
            category,
            f"Started: {name}",
            description,
            operation_id=operation_id,
            progress=0.0 if total_steps > 0 else None
        )
        
        return operation_id
    
    def update_operation_progress(self,
                                 operation_id: str,
                                 current_step: int,
                                 step_description: Optional[str] = None,
                                 progress: Optional[float] = None):
        """
        Update operation progress
        
        Args:
            operation_id: Operation ID
            current_step: Current step number
            step_description: Description of current step
            progress: Manual progress override (0-100)
        """
        if operation_id not in self.operations:
            self.logger.warning(f"Operation {operation_id} not found for progress update")
            return
        
        operation = self.operations[operation_id]
        operation.current_step = current_step
        
        if step_description:
            operation.step_descriptions[current_step] = step_description
        
        # Calculate progress
        if progress is not None:
            operation.progress = progress
        elif operation.total_steps > 0:
            operation.progress = (current_step / operation.total_steps) * 100
        
        # Send progress notification
        current_description = operation.step_descriptions.get(current_step, "")
        progress_message = f"{current_description} ({operation.progress:.1f}%)"
        
        self.notify(
            NotificationSeverity.PROGRESS,
            operation.category,
            f"Progress: {operation.name}",
            progress_message,
            operation_id=operation_id,
            progress=operation.progress
        )
    
    def complete_operation(self,
                          operation_id: str,
                          success: bool = True,
                          result_message: Optional[str] = None,
                          result_data: Optional[Dict[str, Any]] = None,
                          error_message: Optional[str] = None):
        """
        Complete an operation
        
        Args:
            operation_id: Operation ID
            success: Whether operation was successful
            result_message: Result message
            result_data: Result data
            error_message: Error message if failed
        """
        if operation_id not in self.operations:
            self.logger.warning(f"Operation {operation_id} not found for completion")
            return
        
        operation = self.operations[operation_id]
        operation.end_time = datetime.now()
        operation.duration = operation.end_time - operation.start_time
        operation.result_data = result_data or {}
        
        if success:
            operation.status = OperationStatus.COMPLETED
            operation.progress = 100.0
            self.stats['operations_completed'] += 1
            
            self.notify(
                NotificationSeverity.SUCCESS,
                operation.category,
                f"Completed: {operation.name}",
                result_message or f"{operation.description} completed successfully",
                operation_id=operation_id,
                progress=100.0,
                details=result_data
            )
        else:
            operation.status = OperationStatus.FAILED
            operation.error_message = error_message
            self.stats['operations_failed'] += 1
            
            self.notify(
                NotificationSeverity.ERROR,
                operation.category,
                f"Failed: {operation.name}",
                error_message or f"{operation.description} failed",
                operation_id=operation_id,
                details={'error': error_message, 'result_data': result_data},
                persistent=True
            )
        
        # Move to history
        self.operation_history.append(operation)
        if len(self.operation_history) > self.max_history_size:
            self.operation_history.pop(0)
        
        # Remove from active operations
        del self.operations[operation_id]
        
        # Update average duration
        completed_ops = [op for op in self.operation_history if op.status == OperationStatus.COMPLETED]
        if completed_ops:
            total_duration = sum((op.duration.total_seconds() for op in completed_ops), 0.0)
            self.stats['average_operation_duration'] = total_duration / len(completed_ops)
    
    def cancel_operation(self, operation_id: str, reason: Optional[str] = None):
        """Cancel an operation"""
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        operation.status = OperationStatus.CANCELLED
        operation.end_time = datetime.now()
        operation.duration = operation.end_time - operation.start_time
        operation.error_message = reason
        
        self.notify(
            NotificationSeverity.WARNING,
            operation.category,
            f"Cancelled: {operation.name}",
            reason or f"{operation.description} was cancelled",
            operation_id=operation_id
        )
        
        # Move to history
        self.operation_history.append(operation)
        del self.operations[operation_id]
    
    # Convenience methods for common notification types
    def info(self, title: str, message: str, **kwargs) -> str:
        """Send info notification"""
        return self.notify(NotificationSeverity.INFO, OperationCategory.SYSTEM, title, message, **kwargs)
    
    def success(self, title: str, message: str, **kwargs) -> str:
        """Send success notification"""
        return self.notify(NotificationSeverity.SUCCESS, OperationCategory.SYSTEM, title, message, **kwargs)
    
    def warning(self, title: str, message: str, **kwargs) -> str:
        """Send warning notification"""
        return self.notify(NotificationSeverity.WARNING, OperationCategory.SYSTEM, title, message, **kwargs)
    
    def error(self, title: str, message: str, **kwargs) -> str:
        """Send error notification"""
        return self.notify(NotificationSeverity.ERROR, OperationCategory.SYSTEM, title, message, **kwargs)
    
    def critical(self, title: str, message: str, **kwargs) -> str:
        """Send critical notification"""
        return self.notify(NotificationSeverity.CRITICAL, OperationCategory.SYSTEM, title, message, **kwargs)
    
    # Query methods
    def get_notifications(self,
                         severity: Optional[NotificationSeverity] = None,
                         category: Optional[OperationCategory] = None,
                         operation_id: Optional[str] = None,
                         component: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         since: Optional[datetime] = None) -> List[StructuredNotification]:
        """Get notifications with filtering"""
        notifications = self.notification_history.copy()
        
        if severity:
            notifications = [n for n in notifications if n.severity == severity]
        
        if category:
            notifications = [n for n in notifications if n.category == category]
        
        if operation_id:
            notifications = [n for n in notifications if n.operation_id == operation_id]
        
        if component:
            notifications = [n for n in notifications if n.component == component]
        
        if tags:
            notifications = [n for n in notifications if any(tag in n.tags for tag in tags)]
        
        if since:
            notifications = [n for n in notifications if n.timestamp >= since]
        
        return notifications
    
    def get_operations(self,
                      category: Optional[OperationCategory] = None,
                      status: Optional[OperationStatus] = None,
                      since: Optional[datetime] = None) -> List[OperationRecord]:
        """Get operations with filtering"""
        # Combine active and historical operations
        all_operations = list(self.operations.values()) + self.operation_history
        
        if category:
            all_operations = [op for op in all_operations if op.category == category]
        
        if status:
            all_operations = [op for op in all_operations if op.status == status]
        
        if since:
            all_operations = [op for op in all_operations if op.start_time >= since]
        
        return all_operations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification and operation statistics"""
        return self.stats.copy()
    
    def export_history(self, 
                      file_path: str,
                      include_notifications: bool = True,
                      include_operations: bool = True,
                      since: Optional[datetime] = None):
        """Export notification and operation history to JSON file"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }
            
            if include_notifications:
                notifications = self.get_notifications(since=since)
                export_data['notifications'] = []
                for n in notifications:
                    n_data = {
                        'id': n.id,
                        'severity': n.severity.value,
                        'category': n.category.value,
                        'title': n.title,
                        'message': n.message,
                        'timestamp': n.timestamp.isoformat(),
                        'operation_id': n.operation_id,
                        'component': n.component,
                        'progress': n.progress,
                        'details': n.details,
                        'context': n.context,
                        'tags': n.tags,
                        'user_action_required': n.user_action_required,
                        'dismissible': n.dismissible,
                        'persistent': n.persistent,
                        'auto_dismiss_after': n.auto_dismiss_after,
                        'related_notifications': n.related_notifications
                    }
                    export_data['notifications'].append(n_data)
            
            if include_operations:
                operations = self.get_operations(since=since)
                export_data['operations'] = []
                for op in operations:
                    op_data = {
                        'operation_id': op.operation_id,
                        'category': op.category.value,
                        'name': op.name,
                        'description': op.description,
                        'status': op.status.value,
                        'start_time': op.start_time.isoformat(),
                        'end_time': op.end_time.isoformat() if op.end_time else None,
                        'duration_seconds': op.duration.total_seconds() if op.duration else None,
                        'progress': op.progress,
                        'total_steps': op.total_steps,
                        'current_step': op.current_step,
                        'step_descriptions': op.step_descriptions,
                        'notifications': op.notifications,
                        'error_message': op.error_message,
                        'result_data': op.result_data,
                        'metadata': op.metadata
                    }
                    export_data['operations'].append(op_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"History exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting history: {e}")
            raise
    
    def clear_history(self, 
                     older_than: Optional[datetime] = None,
                     categories: Optional[List[OperationCategory]] = None):
        """Clear notification and operation history"""
        if older_than:
            self.notification_history = [
                n for n in self.notification_history 
                if n.timestamp >= older_than
            ]
            self.operation_history = [
                op for op in self.operation_history 
                if op.start_time >= older_than
            ]
        elif categories:
            self.notification_history = [
                n for n in self.notification_history 
                if n.category not in categories
            ]
            self.operation_history = [
                op for op in self.operation_history 
                if op.category not in categories
            ]
        else:
            self.notification_history.clear()
            self.operation_history.clear()
            self.notifications.clear()  # Also clear the notifications dict
        
        # Reset statistics
        self.stats = {
            'total_notifications': 0,
            'notifications_by_severity': {},
            'notifications_by_category': {},
            'operations_completed': 0,
            'operations_failed': 0,
            'average_operation_duration': 0.0
        }
        
        # Recalculate statistics from remaining history
        for notification in self.notification_history:
            self._update_stats(notification)
        
        # Update operation statistics
        completed_ops = [op for op in self.operation_history if op.status == OperationStatus.COMPLETED]
        failed_ops = [op for op in self.operation_history if op.status == OperationStatus.FAILED]
        
        self.stats['operations_completed'] = len(completed_ops)
        self.stats['operations_failed'] = len(failed_ops)
        
        if completed_ops:
            total_duration = sum((op.duration.total_seconds() for op in completed_ops if op.duration), 0.0)
            self.stats['average_operation_duration'] = total_duration / len(completed_ops)
        
        self.logger.info("Notification history cleared")
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        self.stop_processing()

# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None

def get_notification_manager() -> Optional[NotificationManager]:
    """Get the global notification manager instance"""
    return _notification_manager

def initialize_notification_manager(gui_parent=None, **kwargs) -> NotificationManager:
    """Initialize the global notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(gui_parent=gui_parent, **kwargs)
    return _notification_manager

def shutdown_notification_manager():
    """Shutdown the global notification manager"""
    global _notification_manager
    if _notification_manager:
        _notification_manager.stop_processing()
        _notification_manager = None