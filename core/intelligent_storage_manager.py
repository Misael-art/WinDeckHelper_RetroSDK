"""
Intelligent Storage Manager for Environment Dev Deep Evaluation

This module provides intelligent storage management capabilities including:
- Space requirement calculation before installation
- Available space analysis across multiple drives
- Selective installation recommendations based on available space
- Multi-drive distribution algorithms
- Automatic cleanup and compression management

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import os
import shutil
import psutil
import logging
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import json
import tempfile
from datetime import datetime, timedelta


class StoragePriority(Enum):
    """Priority levels for storage allocation"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class DriveType(Enum):
    """Types of storage drives"""
    SSD = "ssd"
    HDD = "hdd"
    NVME = "nvme"
    UNKNOWN = "unknown"


@dataclass
class SpaceRequirement:
    """Space requirement for a component"""
    component_name: str
    download_size: int  # bytes
    installation_size: int  # bytes
    temporary_size: int  # bytes
    total_required: int  # bytes
    priority: StoragePriority
    preferred_drive_type: Optional[DriveType] = None


@dataclass
class DriveInfo:
    """Information about a storage drive"""
    path: str
    total_space: int  # bytes
    available_space: int  # bytes
    used_space: int  # bytes
    drive_type: DriveType
    filesystem: str
    is_system_drive: bool
    performance_score: float  # 0-100, higher is better


@dataclass
class SelectiveInstallationResult:
    """Result of selective installation analysis"""
    recommended_components: List[str]
    skipped_components: List[str]
    total_space_required: int
    available_space_after: int
    warnings: List[str]


@dataclass
class DistributionPlan:
    """Plan for distributing installations across drives"""
    component_drive_mapping: Dict[str, str]
    drive_utilization: Dict[str, int]
    estimated_performance_impact: float
    warnings: List[str]


class IntelligentStorageManager:
    """
    Intelligent Storage Manager for Environment Dev Deep Evaluation
    
    Provides comprehensive storage management including space analysis,
    selective installation recommendations, and multi-drive distribution.
    """
    
    def __init__(self, security_manager=None, config_path: Optional[str] = None):
        """
        Initialize the Intelligent Storage Manager
        
        Args:
            security_manager: Security manager for auditing
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.security_manager = security_manager
        self.config_path = config_path
        self.drive_cache = {}
        self.space_requirements_cache = {}
        self.last_drive_scan = None
        self.cache_duration = timedelta(minutes=5)
        
        # Default space requirements for common components (in MB)
        self.default_requirements = {
            "git": {"download": 50, "install": 200, "temp": 100},
            "dotnet-sdk": {"download": 200, "install": 800, "temp": 300},
            "java-jdk": {"download": 180, "install": 600, "temp": 250},
            "vcpp-redist": {"download": 25, "install": 100, "temp": 50},
            "anaconda": {"download": 500, "install": 3000, "temp": 1000},
            "powershell": {"download": 100, "install": 300, "temp": 150},
            "nodejs": {"download": 30, "install": 150, "temp": 75},
            "python": {"download": 25, "install": 100, "temp": 50}
        }
    
    def calculate_space_requirements_before_installation(self, components: List[str]) -> Dict[str, SpaceRequirement]:
        """
        Calculate space requirements for components before installation
        
        Args:
            components: List of component names to analyze
            
        Returns:
            Dictionary mapping component names to their space requirements
            
        Requirements: 6.1
        """
        self.logger.info(f"Calculating space requirements for {len(components)} components")
        
        requirements = {}
        
        for component in components:
            try:
                req = self._calculate_component_space_requirement(component)
                requirements[component] = req
                self.logger.debug(f"Component {component}: {req.total_required / (1024*1024):.1f} MB required")
            except Exception as e:
                self.logger.error(f"Failed to calculate requirements for {component}: {e}")
                # Use default fallback
                req = self._get_default_space_requirement(component)
                requirements[component] = req
        
        return requirements
    
    def analyze_available_space_across_drives(self) -> Dict[str, DriveInfo]:
        """
        Analyze available space across multiple drives
        
        Returns:
            Dictionary mapping drive paths to their information
            
        Requirements: 6.1, 6.2
        """
        # Check cache first
        if (self.last_drive_scan and 
            datetime.now() - self.last_drive_scan < self.cache_duration and
            self.drive_cache):
            self.logger.debug("Using cached drive information")
            return self.drive_cache
        
        self.logger.info("Analyzing available space across all drives")
        drives = {}
        
        # Get all disk partitions
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                # Skip system partitions that shouldn't be used
                if self._should_skip_partition(partition):
                    continue
                
                usage = psutil.disk_usage(partition.mountpoint)
                drive_type = self._detect_drive_type(partition.device)
                
                drive_info = DriveInfo(
                    path=partition.mountpoint,
                    total_space=usage.total,
                    available_space=usage.free,
                    used_space=usage.used,
                    drive_type=drive_type,
                    filesystem=partition.fstype,
                    is_system_drive=self._is_system_drive(partition.mountpoint),
                    performance_score=self._calculate_performance_score(drive_type, usage)
                )
                
                drives[partition.mountpoint] = drive_info
                self.logger.debug(f"Drive {partition.mountpoint}: {usage.free / (1024**3):.1f} GB available")
                
            except (PermissionError, OSError) as e:
                self.logger.warning(f"Cannot access drive {partition.mountpoint}: {e}")
                continue
        
        # Update cache
        self.drive_cache = drives
        self.last_drive_scan = datetime.now()
        
        return drives
    
    def enable_selective_installation_based_on_available_space(self, 
                                                             components: List[str],
                                                             available_space: Optional[int] = None) -> SelectiveInstallationResult:
        """
        Enable selective installation based on available space
        
        Args:
            components: List of components to consider for installation
            available_space: Optional override for available space (bytes)
            
        Returns:
            SelectiveInstallationResult with recommendations
            
        Requirements: 6.2
        """
        self.logger.info(f"Analyzing selective installation for {len(components)} components")
        
        # Get space requirements
        requirements = self.calculate_space_requirements_before_installation(components)
        
        # Get available space
        if available_space is None:
            drives = self.analyze_available_space_across_drives()
            # Use the drive with most available space for this calculation
            available_space = max(drive.available_space for drive in drives.values()) if drives else 0
        
        # Sort components by priority (lower value = higher priority) and then by size (smaller first)
        sorted_components = sorted(
            components,
            key=lambda c: (requirements[c].priority.value, requirements[c].total_required)
        )
        
        recommended = []
        skipped = []
        total_required = 0
        warnings = []
        
        # Reserve 10% of available space as safety buffer
        safety_buffer = int(available_space * 0.1)
        usable_space = available_space - safety_buffer
        
        for component in sorted_components:
            req = requirements[component]
            
            if total_required + req.total_required <= usable_space:
                recommended.append(component)
                total_required += req.total_required
                self.logger.debug(f"Including {component} ({req.total_required / (1024*1024):.1f} MB)")
            else:
                skipped.append(component)
                self.logger.debug(f"Skipping {component} due to space constraints")
                
                if req.priority in [StoragePriority.CRITICAL, StoragePriority.HIGH]:
                    warnings.append(f"High priority component '{component}' skipped due to insufficient space")
        
        # Add warnings for low space
        remaining_space = available_space - total_required
        if remaining_space < 1024 * 1024 * 1024:  # Less than 1GB remaining
            warnings.append("Less than 1GB space will remain after installation")
        
        result = SelectiveInstallationResult(
            recommended_components=recommended,
            skipped_components=skipped,
            total_space_required=total_required,
            available_space_after=remaining_space,
            warnings=warnings
        )
        
        self.logger.info(f"Selective installation: {len(recommended)} recommended, {len(skipped)} skipped")
        return result
    
    def _calculate_component_space_requirement(self, component: str) -> SpaceRequirement:
        """Calculate space requirement for a specific component"""
        # Try to get from cache first
        if component in self.space_requirements_cache:
            return self.space_requirements_cache[component]
        
        # Try to get from component metadata if available
        req = self._get_component_metadata_requirement(component)
        if not req:
            req = self._get_default_space_requirement(component)
        
        # Cache the result
        self.space_requirements_cache[component] = req
        return req
    
    def _get_component_metadata_requirement(self, component: str) -> Optional[SpaceRequirement]:
        """Get space requirement from component metadata"""
        # This would integrate with the component metadata system
        # For now, return None to use defaults
        return None
    
    def _get_default_space_requirement(self, component: str) -> SpaceRequirement:
        """Get default space requirement for a component"""
        # Normalize component name
        normalized_name = component.lower().replace("-", "").replace("_", "")
        
        # Find matching default requirement
        for key, sizes in self.default_requirements.items():
            key_normalized = key.replace("-", "")
            if key_normalized in normalized_name or normalized_name in key_normalized:
                download_mb = sizes["download"]
                install_mb = sizes["install"]
                temp_mb = sizes["temp"]
                
                download_bytes = download_mb * 1024 * 1024
                install_bytes = install_mb * 1024 * 1024
                temp_bytes = temp_mb * 1024 * 1024
                total_bytes = download_bytes + install_bytes + temp_bytes
                
                return SpaceRequirement(
                    component_name=component,
                    download_size=download_bytes,
                    installation_size=install_bytes,
                    temporary_size=temp_bytes,
                    total_required=total_bytes,
                    priority=self._get_component_priority(component)
                )
        
        # Fallback for unknown components
        return SpaceRequirement(
            component_name=component,
            download_size=50 * 1024 * 1024,  # 50MB
            installation_size=200 * 1024 * 1024,  # 200MB
            temporary_size=100 * 1024 * 1024,  # 100MB
            total_required=350 * 1024 * 1024,  # 350MB
            priority=StoragePriority.MEDIUM
        )
    
    def _get_component_priority(self, component: str) -> StoragePriority:
        """Determine priority for a component"""
        critical_components = ["git", "dotnet-sdk", "java-jdk", "vcpp-redist"]
        high_components = ["powershell", "nodejs", "python"]
        
        normalized = component.lower()
        
        for critical in critical_components:
            if critical in normalized:
                return StoragePriority.CRITICAL
        
        for high in high_components:
            if high in normalized:
                return StoragePriority.HIGH
        
        return StoragePriority.MEDIUM
    
    def _should_skip_partition(self, partition) -> bool:
        """Determine if a partition should be skipped"""
        # Skip system partitions on Windows
        if os.name == 'nt':
            skip_paths = ['System Reserved', 'Recovery', 'EFI']
            for skip_path in skip_paths:
                if skip_path.lower() in partition.mountpoint.lower():
                    return True
        
        # Skip very small partitions (less than 100MB)
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            if usage.total < 100 * 1024 * 1024:
                return True
        except:
            return True
        
        return False
    
    def _detect_drive_type(self, device: str) -> DriveType:
        """Detect the type of storage drive"""
        # This is a simplified detection - in practice, you'd use more sophisticated methods
        device_lower = device.lower()
        
        if 'nvme' in device_lower:
            return DriveType.NVME
        elif 'ssd' in device_lower:
            return DriveType.SSD
        elif any(hdd_indicator in device_lower for hdd_indicator in ['hdd', 'hd', 'wd', 'seagate']):
            return DriveType.HDD
        
        return DriveType.UNKNOWN
    
    def _is_system_drive(self, mountpoint: str) -> bool:
        """Check if a drive is the system drive"""
        if os.name == 'nt':
            return mountpoint.upper() == 'C:\\'
        else:
            return mountpoint == '/'
    
    def _calculate_performance_score(self, drive_type: DriveType, usage) -> float:
        """Calculate a performance score for a drive"""
        # Base score by drive type
        type_scores = {
            DriveType.NVME: 100,
            DriveType.SSD: 80,
            DriveType.HDD: 40,
            DriveType.UNKNOWN: 50
        }
        
        base_score = type_scores[drive_type]
        
        # Adjust based on available space (more available space = better performance)
        space_ratio = usage.free / usage.total
        space_multiplier = 0.5 + (space_ratio * 0.5)  # 0.5 to 1.0
        
        return base_score * space_multiplier