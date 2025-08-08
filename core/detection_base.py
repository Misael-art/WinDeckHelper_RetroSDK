#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detection Base Classes
Classes base para o sistema de detecção de aplicações.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum


class DetectionMethod(Enum):
    """Methods used for application detection."""
    REGISTRY = "registry"
    EXECUTABLE_SCAN = "executable_scan"
    PATH_BASED = "path_based"
    PACKAGE_MANAGER = "package_manager"
    MANUAL_OVERRIDE = "manual_override"


class ApplicationStatus(Enum):
    """Status of detected applications."""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"
    CORRUPTED = "corrupted"


@dataclass
class DetectedApplication:
    """Represents a detected application with all relevant information."""
    name: str
    version: str = "Unknown"
    install_path: str = ""
    executable_path: str = ""
    detection_method: DetectionMethod = DetectionMethod.MANUAL_OVERRIDE
    status: ApplicationStatus = ApplicationStatus.UNKNOWN
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.confidence < 0.0:
            self.confidence = 0.0
        elif self.confidence > 1.0:
            self.confidence = 1.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'version': self.version,
            'install_path': self.install_path,
            'executable_path': self.executable_path,
            'detection_method': self.detection_method.value,
            'status': self.status.value,
            'confidence': self.confidence,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DetectedApplication':
        """Create instance from dictionary."""
        return cls(
            name=data.get('name', ''),
            version=data.get('version', 'Unknown'),
            install_path=data.get('install_path', ''),
            executable_path=data.get('executable_path', ''),
            detection_method=DetectionMethod(data.get('detection_method', 'manual_override')),
            status=ApplicationStatus(data.get('status', 'unknown')),
            confidence=data.get('confidence', 0.0),
            metadata=data.get('metadata', {})
        )


class DetectionStrategy(ABC):
    """Abstract base class for application detection strategies."""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(f"detection_{self.__class__.__name__.lower()}")
    
    @abstractmethod
    def get_method_name(self) -> DetectionMethod:
        """Return the detection method used by this strategy."""
        pass
    
    @abstractmethod
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detect applications using this strategy."""
        pass