"""
Base classes for all system components.

This module provides abstract base classes that define common interfaces
and functionality for all major system components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .config import ConfigurationManager, SystemConfiguration
from .exceptions import EnvironmentDevDeepEvaluationError


class SystemComponentBase(ABC):
    """
    Abstract base class for all system components.
    
    Provides common functionality including configuration access,
    logging, error handling, and lifecycle management.
    """
    
    def __init__(
        self, 
        config_manager: ConfigurationManager,
        component_name: Optional[str] = None
    ):
        """
        Initialize system component.
        
        Args:
            config_manager: Configuration manager instance
            component_name: Optional component name for logging
        """
        self._config_manager = config_manager
        self._config = config_manager.get_config()
        self._component_name = component_name or self.__class__.__name__
        self._logger = self._setup_logger()
        self._initialized = False
        self._last_operation_time: Optional[datetime] = None
        self._operation_count = 0
        
    def _setup_logger(self) -> logging.Logger:
        """Setup component-specific logger."""
        logger = logging.getLogger(f"environment_dev_deep_evaluation.{self._component_name}")
        logger.setLevel(getattr(logging, self._config.log_level))
        return logger
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the component. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_configuration(self) -> None:
        """Validate component-specific configuration. Must be implemented by subclasses."""
        pass
    
    def ensure_initialized(self) -> None:
        """Ensure component is initialized before operations."""
        if not self._initialized:
            self.initialize()
            self.validate_configuration()
            self._initialized = True
            self._logger.info(f"{self._component_name} initialized successfully")
    
    def get_config(self) -> SystemConfiguration:
        """Get system configuration."""
        return self._config
    
    def get_component_info(self) -> Dict[str, Any]:
        """Get information about component state."""
        return {
            "component_name": self._component_name,
            "initialized": self._initialized,
            "last_operation_time": self._last_operation_time.isoformat() if self._last_operation_time else None,
            "operation_count": self._operation_count,
        }
    
    def _record_operation(self) -> None:
        """Record that an operation was performed."""
        self._last_operation_time = datetime.now()
        self._operation_count += 1
    
    def _handle_error(
        self, 
        error: Exception, 
        operation: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle errors with proper logging and context.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            context: Additional context information
        """
        error_context = {
            "component": self._component_name,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        }
        
        if context:
            error_context.update(context)
        
        self._logger.error(
            f"Error in {operation}: {str(error)}",
            extra={"context": error_context}
        )
        
        # Re-raise as system-specific error if not already
        if not isinstance(error, EnvironmentDevDeepEvaluationError):
            raise EnvironmentDevDeepEvaluationError(
                f"Error in {self._component_name}.{operation}: {str(error)}",
                context=error_context,
                cause=error
            ) from error
        else:
            raise error


class OperationResult:
    """
    Standard result object for component operations.
    
    Provides consistent structure for operation results across all components.
    """
    
    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        operation_time: Optional[datetime] = None
    ):
        """
        Initialize operation result.
        
        Args:
            success: Whether the operation was successful
            message: Human-readable message about the operation
            data: Optional data returned by the operation
            errors: List of error messages
            warnings: List of warning messages
            operation_time: When the operation was performed
        """
        self.success = success
        self.message = message
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []
        self.operation_time = operation_time or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "operation_time": self.operation_time.isoformat(),
        }
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def merge(self, other: 'OperationResult') -> None:
        """Merge another result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.data.update(other.data)
        
        if not other.success:
            self.success = False


class ComponentStatus:
    """
    Status tracking for system components.
    
    Provides standardized status information for monitoring and debugging.
    """
    
    def __init__(self, component_name: str):
        """Initialize component status."""
        self.component_name = component_name
        self.status = "not_initialized"
        self.last_update = datetime.now()
        self.health_score = 1.0
        self.metrics: Dict[str, Any] = {}
        self.issues: List[str] = []
    
    def update_status(self, status: str, message: Optional[str] = None) -> None:
        """Update component status."""
        self.status = status
        self.last_update = datetime.now()
        
        if message:
            self.metrics["last_status_message"] = message
    
    def add_metric(self, key: str, value: Any) -> None:
        """Add a metric value."""
        self.metrics[key] = value
        self.last_update = datetime.now()
    
    def add_issue(self, issue: str) -> None:
        """Add an issue to track."""
        self.issues.append(issue)
        self.health_score = max(0.0, self.health_score - 0.1)
        self.last_update = datetime.now()
    
    def clear_issues(self) -> None:
        """Clear all tracked issues."""
        self.issues.clear()
        self.health_score = 1.0
        self.last_update = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        return {
            "component_name": self.component_name,
            "status": self.status,
            "last_update": self.last_update.isoformat(),
            "health_score": self.health_score,
            "metrics": self.metrics,
            "issues": self.issues,
        }