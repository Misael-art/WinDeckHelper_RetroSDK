# -*- coding: utf-8 -*-
"""
Sistema de Tratamento de Erros
Gerencia erros e exceções do sistema de forma centralizada
"""

import logging
import traceback
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Níveis de severidade dos erros"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categorias de erros"""
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    PERMISSION = "permission"
    VALIDATION = "validation"
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    USER_INPUT = "user_input"

@dataclass
class ErrorContext:
    """Contexto adicional do erro"""
    component: str
    operation: str
    details: Dict[str, Any]
    timestamp: float
    user_action: Optional[str] = None

class EnvDevError(Exception):
    """Exceção base do sistema Environment Dev"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.category = category
        self.context = context
        self.original_error = original_error
        self.traceback_info = traceback.format_exc() if original_error else None
        
        # Log automaticamente o erro
        self._log_error()
    
    def _log_error(self):
        """Registra o erro no sistema de logging"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(self.severity, logging.ERROR)
        
        log_message = f"[{self.category.value.upper()}] {self.message}"
        
        if self.context:
            log_message += f" | Component: {self.context.component} | Operation: {self.context.operation}"
        
        logger.log(log_level, log_message)
        
        if self.original_error and self.traceback_info:
            logger.debug(f"Original error traceback: {self.traceback_info}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o erro para dicionário"""
        return {
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'context': self.context.__dict__ if self.context else None,
            'original_error': str(self.original_error) if self.original_error else None
        }

class NetworkError(EnvDevError):
    """Erro relacionado à rede"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)

class FileSystemError(EnvDevError):
    """Erro relacionado ao sistema de arquivos"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.FILE_SYSTEM, **kwargs)

class PermissionError(EnvDevError):
    """Erro relacionado a permissões"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.PERMISSION, **kwargs)

class ValidationError(EnvDevError):
    """Erro de validação"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)

class InstallationError(EnvDevError):
    """Erro de instalação"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.INSTALLATION, **kwargs)

class ConfigurationError(EnvDevError):
    """Erro de configuração"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)

def handle_error(
    error: Exception,
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    details: Optional[Dict[str, Any]] = None
) -> EnvDevError:
    """Manipula e converte erros genéricos em EnvDevError"""
    import time
    
    context = ErrorContext(
        component=component,
        operation=operation,
        details=details or {},
        timestamp=time.time()
    )
    
    if isinstance(error, EnvDevError):
        return error
    
    return EnvDevError(
        message=str(error),
        severity=severity,
        category=category,
        context=context,
        original_error=error
    )

def create_error_context(
    component: str,
    operation: str,
    **details
) -> ErrorContext:
    """Cria um contexto de erro"""
    import time
    
    return ErrorContext(
        component=component,
        operation=operation,
        details=details,
        timestamp=time.time()
    )