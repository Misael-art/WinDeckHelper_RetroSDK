"""
Core exception hierarchy for Environment Dev Deep Evaluation system.

This module defines all exceptions used throughout the system, organized
in a hierarchical structure for proper error handling and categorization.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class EnvironmentDevDeepEvaluationError(Exception):
    """
    Base exception for Environment Dev Deep Evaluation system.
    
    All other exceptions in the system inherit from this base class,
    providing a common interface for error handling and logging.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }


class ArchitectureAnalysisError(EnvironmentDevDeepEvaluationError):
    """
    Errors during architecture analysis operations.
    
    Raised when issues occur during:
    - Architecture mapping and comparison
    - Gap analysis and documentation
    - Requirements consistency validation
    """
    pass


class UnifiedDetectionError(EnvironmentDevDeepEvaluationError):
    """
    Errors during unified detection operations.
    
    Raised when issues occur during:
    - Application and runtime detection
    - Registry scanning
    - Portable application detection
    - Hierarchical detection prioritization
    """
    pass


class DependencyValidationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during dependency validation operations.
    
    Raised when issues occur during:
    - Dependency graph creation and analysis
    - Conflict detection and resolution
    - Contextual compatibility validation
    """
    pass


class RobustDownloadError(EnvironmentDevDeepEvaluationError):
    """
    Errors during robust download operations.
    
    Raised when issues occur during:
    - Secure download with hash verification
    - Mirror fallback and retry mechanisms
    - Parallel download coordination
    """
    pass


class AdvancedInstallationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during advanced installation operations.
    
    Raised when issues occur during:
    - Installation with automatic rollback
    - Environment variable configuration
    - Runtime-specific installation handling
    """
    pass


class SteamDeckIntegrationError(EnvironmentDevDeepEvaluationError):
    """
    Errors during Steam Deck integration operations.
    
    Raised when issues occur during:
    - Steam Deck hardware detection
    - Controller and power optimizations
    - Steam ecosystem integration
    """
    pass


class IntelligentStorageError(EnvironmentDevDeepEvaluationError):
    """
    Errors during intelligent storage management operations.
    
    Raised when issues occur during:
    - Storage analysis and planning
    - Intelligent distribution and cleanup
    - Compression system operations
    """
    pass


class PluginSystemError(EnvironmentDevDeepEvaluationError):
    """
    Errors during plugin system operations.
    
    Raised when issues occur during:
    - Plugin loading and validation
    - Plugin conflict detection
    - Plugin integration mechanisms
    """
    pass


# Specific sub-exceptions for more granular error handling

class ConfigurationError(EnvironmentDevDeepEvaluationError):
    """Errors related to system configuration management."""
    pass


class ValidationError(EnvironmentDevDeepEvaluationError):
    """Errors related to data validation and verification."""
    pass


class SecurityError(EnvironmentDevDeepEvaluationError):
    """Errors related to security validation and verification."""
    pass


class PermissionError(EnvironmentDevDeepEvaluationError):
    """Errors related to insufficient permissions or privilege escalation."""
    pass


class NetworkError(EnvironmentDevDeepEvaluationError):
    """Errors related to network operations and connectivity."""
    pass


class FileSystemError(EnvironmentDevDeepEvaluationError):
    """Errors related to file system operations."""
    pass


class IntegrityError(EnvironmentDevDeepEvaluationError):
    """Errors related to data integrity and verification."""
    pass