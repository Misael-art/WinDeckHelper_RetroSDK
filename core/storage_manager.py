#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Storage Manager - Intelligent Storage Management System
Provides storage analysis, calculation, and optimization for runtime installations.
"""

import os
import sys
import json
import logging
import platform
import shutil
import psutil
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union, NamedTuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Import winreg safely for Windows
try:
    import winreg
except ImportError:
    winreg = None


class StorageUnit(Enum):
    """Storage units for calculations."""
    BYTES = "bytes"
    KB = "kb"
    MB = "mb"
    GB = "gb"
    TB = "tb"


class DriveType(Enum):
    """Types of storage drives."""
    HDD = "hdd"
    SSD = "ssd"
    NVME = "nvme"
    USB = "usb"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ComponentPriority(Enum):
    """Priority levels for component installation."""
    CRITICAL = "critical"      # Essential system components
    HIGH = "high"             # Important development tools
    MEDIUM = "medium"         # Useful but optional components
    LOW = "low"              # Nice-to-have components
    OPTIONAL = "optional"     # Completely optional components


@dataclass
class StorageRequirement:
    """Storage requirement for a component or set of components."""
    component_name: str
    size_mb: int
    temporary_space_mb: int = 0  # Additional space needed during installation
    preferred_drive_types: List[DriveType] = field(default_factory=list)
    minimum_free_space_after_mb: int = 1024  # Minimum free space to maintain after installation
    description: str = ""


@dataclass
class DriveInfo:
    """Information about a storage drive."""
    path: str
    total_space_gb: float
    free_space_gb: float
    used_space_gb: float
    drive_type: DriveType
    file_system: str
    is_system_drive: bool = False
    is_removable: bool = False
    performance_score: int = 100  # 0-100, higher is better


@dataclass
class StorageAnalysis:
    """Result of storage analysis."""
    total_required_mb: int
    total_available_mb: int
    drives: List[DriveInfo]
    can_install_all: bool
    recommended_drives: Dict[str, str]  # component_name -> drive_path
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class InstallationPlan:
    """Plan for component installation across drives."""
    components: Dict[str, str]  # component_name -> drive_path
    total_size_mb: int
    estimated_duration_minutes: int
    space_after_installation: Dict[str, float]  # drive_path -> free_space_gb
    warnings: List[str] = field(default_factory=list)
    optimizations: List[str] = field(default_factory=list)


@dataclass
class ComponentSelection:
    """Result of component selection process."""
    selected_components: List[str]
    deselected_components: List[str]
    total_size_mb: int
    available_space_mb: int
    selection_reason: Dict[str, str]  # component_name -> reason for selection/deselection
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SelectionCriteria:
    """Criteria for component selection."""
    max_total_size_mb: Optional[int] = None
    required_components: List[str] = field(default_factory=list)
    excluded_components: List[str] = field(default_factory=list)
    priority_threshold: ComponentPriority = ComponentPriority.LOW
    prefer_essential_only: bool = False
    steamdeck_optimized: bool = False


class StorageManager:
    """Main storage management class for intelligent storage operations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config/storage")
        self.logger = logging.getLogger("storage_manager")
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for drive information
        self._drive_cache: Dict[str, DriveInfo] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration_seconds = 300  # 5 minutes
        
        # Storage thresholds
        self.minimum_free_space_gb = 2.0  # Minimum free space to maintain
        self.warning_threshold_percent = 10  # Warn if less than 10% free space
        self.critical_threshold_percent = 5  # Critical if less than 5% free space
        
        # Initialize selective installation manager
        self.selective_manager = None  # Will be initialized after class definition
    
    def get_drive_info(self, refresh_cache: bool = False) -> List[DriveInfo]:
        """Get information about all available drives."""
        try:
            # Check cache validity
            if (not refresh_cache and 
                self._cache_timestamp and 
                self._drive_cache and
                (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_duration_seconds):
                return list(self._drive_cache.values())
            
            drives = []
            
            if platform.system() == "Windows":
                drives = self._get_windows_drives()
            else:
                drives = self._get_unix_drives()
            
            # Update cache
            self._drive_cache = {drive.path: drive for drive in drives}
            self._cache_timestamp = datetime.now()
            
            self.logger.info(f"Detected {len(drives)} storage drives")
            return drives
            
        except Exception as e:
            self.logger.error(f"Error getting drive information: {e}")
            return []
    
    def _get_windows_drives(self) -> List[DriveInfo]:
        """Get drive information on Windows systems."""
        drives = []
        
        try:
            # Get all drive letters
            for drive_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = f"{drive_letter}:\\"
                
                if os.path.exists(drive_path):
                    try:
                        # Get disk usage
                        usage = shutil.disk_usage(drive_path)
                        total_gb = usage.total / (1024**3)
                        free_gb = usage.free / (1024**3)
                        used_gb = (usage.total - usage.free) / (1024**3)
                        
                        # Determine drive type
                        drive_type = self._detect_drive_type_windows(drive_path)
                        
                        # Get file system
                        file_system = self._get_file_system_windows(drive_path)
                        
                        # Check if system drive
                        is_system_drive = (drive_letter.upper() == os.environ.get('SystemDrive', 'C:')[0])
                        
                        # Check if removable
                        is_removable = self._is_removable_drive_windows(drive_path)
                        
                        drive_info = DriveInfo(
                            path=drive_path,
                            total_space_gb=round(total_gb, 2),
                            free_space_gb=round(free_gb, 2),
                            used_space_gb=round(used_gb, 2),
                            drive_type=drive_type,
                            file_system=file_system,
                            is_system_drive=is_system_drive,
                            is_removable=is_removable,
                            performance_score=self._calculate_performance_score(drive_type, is_system_drive)
                        )
                        
                        drives.append(drive_info)
                        
                    except (OSError, PermissionError) as e:
                        self.logger.debug(f"Cannot access drive {drive_path}: {e}")
                        continue
            
        except Exception as e:
            self.logger.error(f"Error getting Windows drives: {e}")
        
        return drives
    
    def _get_unix_drives(self) -> List[DriveInfo]:
        """Get drive information on Unix-like systems."""
        drives = []
        
        try:
            # Use psutil to get disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Skip special filesystems
                    if partition.fstype in ['tmpfs', 'devtmpfs', 'proc', 'sysfs']:
                        continue
                    
                    # Get disk usage
                    usage = shutil.disk_usage(partition.mountpoint)
                    total_gb = usage.total / (1024**3)
                    free_gb = usage.free / (1024**3)
                    used_gb = (usage.total - usage.free) / (1024**3)
                    
                    # Determine drive type
                    drive_type = self._detect_drive_type_unix(partition.device)
                    
                    # Check if system drive (root filesystem)
                    is_system_drive = (partition.mountpoint == '/')
                    
                    drive_info = DriveInfo(
                        path=partition.mountpoint,
                        total_space_gb=round(total_gb, 2),
                        free_space_gb=round(free_gb, 2),
                        used_space_gb=round(used_gb, 2),
                        drive_type=drive_type,
                        file_system=partition.fstype,
                        is_system_drive=is_system_drive,
                        is_removable=False,  # TODO: Implement removable detection for Unix
                        performance_score=self._calculate_performance_score(drive_type, is_system_drive)
                    )
                    
                    drives.append(drive_info)
                    
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Cannot access partition {partition.mountpoint}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error getting Unix drives: {e}")
        
        return drives
    
    def _detect_drive_type_windows(self, drive_path: str) -> DriveType:
        """Detect drive type on Windows."""
        try:
            import subprocess
            
            # Use wmic to get drive information
            cmd = f'wmic logicaldisk where "DeviceID=\\"{drive_path[0]}:\\"" get MediaType /value'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'removable' in output or 'usb' in output:
                    return DriveType.USB
                elif 'ssd' in output or 'solid state' in output:
                    return DriveType.SSD
                elif 'nvme' in output:
                    return DriveType.NVME
                elif 'network' in output:
                    return DriveType.NETWORK
                else:
                    return DriveType.HDD
            
        except Exception as e:
            self.logger.debug(f"Could not detect drive type for {drive_path}: {e}")
        
        return DriveType.UNKNOWN
    
    def _detect_drive_type_unix(self, device: str) -> DriveType:
        """Detect drive type on Unix-like systems."""
        try:
            # Check if it's an NVMe drive
            if 'nvme' in device.lower():
                return DriveType.NVME
            
            # Check if it's a USB drive
            if 'usb' in device.lower() or device.startswith('/dev/sd') and len(device) == 8:
                return DriveType.USB
            
            # Try to determine if it's SSD or HDD
            if device.startswith('/dev/'):
                device_name = device.split('/')[-1].rstrip('0123456789')
                rotational_file = f"/sys/block/{device_name}/queue/rotational"
                
                if os.path.exists(rotational_file):
                    with open(rotational_file, 'r') as f:
                        rotational = f.read().strip()
                        if rotational == '0':
                            return DriveType.SSD
                        else:
                            return DriveType.HDD
            
        except Exception as e:
            self.logger.debug(f"Could not detect drive type for {device}: {e}")
        
        return DriveType.UNKNOWN
    
    def _get_file_system_windows(self, drive_path: str) -> str:
        """Get file system type on Windows."""
        try:
            import subprocess
            
            cmd = f'fsutil fsinfo volumeinfo {drive_path}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'File System Name' in line:
                        return line.split(':')[-1].strip()
            
        except Exception as e:
            self.logger.debug(f"Could not get file system for {drive_path}: {e}")
        
        return "Unknown"
    
    def _is_removable_drive_windows(self, drive_path: str) -> bool:
        """Check if drive is removable on Windows."""
        try:
            import subprocess
            
            cmd = f'wmic logicaldisk where "DeviceID=\\"{drive_path[0]}:\\"" get DriveType /value'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # DriveType 2 = Removable disk
                return 'DriveType=2' in result.stdout
            
        except Exception as e:
            self.logger.debug(f"Could not check if drive {drive_path} is removable: {e}")
        
        return False
    
    def _calculate_performance_score(self, drive_type: DriveType, is_system_drive: bool) -> int:
        """Calculate performance score for a drive."""
        base_scores = {
            DriveType.NVME: 100,
            DriveType.SSD: 85,
            DriveType.HDD: 60,
            DriveType.USB: 40,
            DriveType.NETWORK: 30,
            DriveType.UNKNOWN: 50
        }
        
        score = base_scores.get(drive_type, 50)
        
        # Reduce score for system drive due to potential I/O contention
        if is_system_drive:
            score = max(score - 15, 10)
        
        return score
    
    def calculate_storage_requirements(self, components: List[Dict[str, Any]]) -> List[StorageRequirement]:
        """Calculate storage requirements for a list of components."""
        requirements = []
        
        try:
            for component in components:
                # Extract component information
                name = component.get('name', 'unknown')
                size_mb = component.get('size_mb', 0)
                
                # Calculate temporary space (typically 1.5x the component size for extraction/installation)
                temp_space_mb = int(size_mb * 1.5)
                
                # Determine preferred drive types based on component type
                preferred_drives = self._get_preferred_drive_types(component)
                
                requirement = StorageRequirement(
                    component_name=name,
                    size_mb=size_mb,
                    temporary_space_mb=temp_space_mb,
                    preferred_drive_types=preferred_drives,
                    minimum_free_space_after_mb=max(1024, size_mb // 10),  # At least 1GB or 10% of component size
                    description=component.get('description', '')
                )
                
                requirements.append(requirement)
                
        except Exception as e:
            self.logger.error(f"Error calculating storage requirements: {e}")
        
        return requirements
    
    def _get_preferred_drive_types(self, component: Dict[str, Any]) -> List[DriveType]:
        """Determine preferred drive types for a component."""
        component_type = component.get('type', '').lower()
        name = component.get('name', '').lower()
        
        # High-performance components prefer faster drives
        if any(keyword in name for keyword in ['ide', 'compiler', 'database', 'game']):
            return [DriveType.NVME, DriveType.SSD, DriveType.HDD]
        
        # Development tools prefer fast drives
        if any(keyword in name for keyword in ['sdk', 'jdk', 'visual', 'git']):
            return [DriveType.NVME, DriveType.SSD, DriveType.HDD]
        
        # General components can use any drive
        return [DriveType.NVME, DriveType.SSD, DriveType.HDD, DriveType.USB]
    
    def analyze_storage_capacity(self, requirements: List[StorageRequirement]) -> StorageAnalysis:
        """Analyze storage capacity and provide recommendations."""
        try:
            drives = self.get_drive_info()
            
            # Calculate total requirements
            total_required_mb = sum(req.size_mb + req.temporary_space_mb for req in requirements)
            total_available_mb = sum(int(drive.free_space_gb * 1024) for drive in drives)
            
            # Check if we can install everything
            can_install_all = total_available_mb >= total_required_mb
            
            # Generate drive recommendations
            recommended_drives = self._recommend_drive_assignments(requirements, drives)
            
            # Generate warnings and recommendations
            warnings = []
            recommendations = []
            
            # Check for low space warnings
            for drive in drives:
                free_percent = (drive.free_space_gb / drive.total_space_gb) * 100
                
                if free_percent < self.critical_threshold_percent:
                    warnings.append(f"Critical: Drive {drive.path} has only {drive.free_space_gb:.1f}GB free ({free_percent:.1f}%)")
                elif free_percent < self.warning_threshold_percent:
                    warnings.append(f"Warning: Drive {drive.path} has only {drive.free_space_gb:.1f}GB free ({free_percent:.1f}%)")
            
            # Generate recommendations
            if not can_install_all:
                recommendations.append(f"Insufficient space: Need {total_required_mb/1024:.1f}GB, have {total_available_mb/1024:.1f}GB available")
                recommendations.append("Consider selective installation or freeing up disk space")
            
            # Recommend drive optimization
            if len(drives) > 1:
                recommendations.append("Consider distributing installations across multiple drives for better performance")
            
            analysis = StorageAnalysis(
                total_required_mb=total_required_mb,
                total_available_mb=total_available_mb,
                drives=drives,
                can_install_all=can_install_all,
                recommended_drives=recommended_drives,
                warnings=warnings,
                recommendations=recommendations
            )
            
            self.logger.info(f"Storage analysis completed: {total_required_mb/1024:.1f}GB required, {total_available_mb/1024:.1f}GB available")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing storage capacity: {e}")
            return StorageAnalysis(
                total_required_mb=0,
                total_available_mb=0,
                drives=[],
                can_install_all=False,
                recommended_drives={},
                warnings=[f"Error analyzing storage: {e}"],
                recommendations=["Please check system storage manually"]
            )
    
    def _recommend_drive_assignments(self, requirements: List[StorageRequirement], drives: List[DriveInfo]) -> Dict[str, str]:
        """Recommend drive assignments for components."""
        recommendations = {}
        
        try:
            # Sort drives by performance score and available space
            sorted_drives = sorted(drives, key=lambda d: (d.performance_score, d.free_space_gb), reverse=True)
            
            # Sort requirements by size (largest first) for better packing
            sorted_requirements = sorted(requirements, key=lambda r: r.size_mb + r.temporary_space_mb, reverse=True)
            
            # Track remaining space on each drive
            drive_remaining_space = {drive.path: drive.free_space_gb * 1024 for drive in drives}  # Convert to MB
            
            for requirement in sorted_requirements:
                total_needed_mb = requirement.size_mb + requirement.temporary_space_mb + requirement.minimum_free_space_after_mb
                
                # Find the best drive for this component
                best_drive = None
                best_score = -1
                
                for drive in sorted_drives:
                    # Check if drive has enough space
                    if drive_remaining_space[drive.path] < total_needed_mb:
                        continue
                    
                    # Calculate score based on drive type preference and performance
                    score = 0
                    
                    # Prefer drives that match component preferences
                    if drive.drive_type in requirement.preferred_drive_types:
                        score += 50
                    
                    # Add performance score
                    score += drive.performance_score
                    
                    # Prefer non-system drives for large components
                    if not drive.is_system_drive and requirement.size_mb > 500:
                        score += 20
                    
                    # Prefer drives with more available space
                    space_score = min(drive_remaining_space[drive.path] / 10240, 20)  # Max 20 points for space
                    score += space_score
                    
                    if score > best_score:
                        best_score = score
                        best_drive = drive
                
                if best_drive:
                    recommendations[requirement.component_name] = best_drive.path
                    # Update remaining space
                    drive_remaining_space[best_drive.path] -= (requirement.size_mb + requirement.temporary_space_mb)
                else:
                    # No suitable drive found
                    self.logger.warning(f"No suitable drive found for component {requirement.component_name}")
            
        except Exception as e:
            self.logger.error(f"Error recommending drive assignments: {e}")
        
        return recommendations
    
    def check_available_space(self, drive_paths: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """Check available space on specified drives or all drives."""
        try:
            drives = self.get_drive_info()
            
            if drive_paths:
                # Filter to specified drives
                drives = [drive for drive in drives if drive.path in drive_paths]
            
            space_info = {}
            
            for drive in drives:
                space_info[drive.path] = {
                    'total_gb': drive.total_space_gb,
                    'free_gb': drive.free_space_gb,
                    'used_gb': drive.used_space_gb,
                    'free_percent': (drive.free_space_gb / drive.total_space_gb) * 100,
                    'drive_type': drive.drive_type.value,
                    'file_system': drive.file_system,
                    'is_system_drive': drive.is_system_drive,
                    'performance_score': drive.performance_score
                }
            
            return space_info
            
        except Exception as e:
            self.logger.error(f"Error checking available space: {e}")
            return {}
    
    def create_installation_plan(self, requirements: List[StorageRequirement], 
                               preferred_drives: Optional[Dict[str, str]] = None) -> InstallationPlan:
        """Create an optimized installation plan."""
        try:
            drives = self.get_drive_info()
            analysis = self.analyze_storage_capacity(requirements)
            
            # Use provided preferences or analysis recommendations
            drive_assignments = preferred_drives or analysis.recommended_drives
            
            # Calculate total size and estimated duration
            total_size_mb = sum(req.size_mb for req in requirements)
            
            # Estimate installation duration (rough estimate: 1MB per second for average drive)
            estimated_duration_minutes = max(total_size_mb // 60, 5)  # At least 5 minutes
            
            # Calculate space after installation
            space_after = {}
            drive_usage = {}
            
            for drive in drives:
                drive_usage[drive.path] = 0
                space_after[drive.path] = drive.free_space_gb
            
            # Calculate usage per drive
            for requirement in requirements:
                assigned_drive = drive_assignments.get(requirement.component_name)
                if assigned_drive and assigned_drive in drive_usage:
                    drive_usage[assigned_drive] += requirement.size_mb
            
            # Update space after installation
            for drive_path, usage_mb in drive_usage.items():
                space_after[drive_path] -= (usage_mb / 1024)  # Convert MB to GB
            
            # Generate warnings and optimizations
            warnings = []
            optimizations = []
            
            # Check for potential issues
            for drive_path, remaining_gb in space_after.items():
                if remaining_gb < self.minimum_free_space_gb:
                    warnings.append(f"Drive {drive_path} will have only {remaining_gb:.1f}GB free after installation")
            
            # Suggest optimizations
            if len(set(drive_assignments.values())) == 1 and len(drives) > 1:
                optimizations.append("Consider distributing components across multiple drives for better performance")
            
            if any(drive.drive_type == DriveType.USB for drive in drives if drive.path in drive_assignments.values()):
                optimizations.append("Some components will be installed on USB drives, which may affect performance")
            
            plan = InstallationPlan(
                components=drive_assignments,
                total_size_mb=total_size_mb,
                estimated_duration_minutes=estimated_duration_minutes,
                space_after_installation=space_after,
                warnings=warnings,
                optimizations=optimizations
            )
            
            self.logger.info(f"Created installation plan for {len(requirements)} components ({total_size_mb/1024:.1f}GB)")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating installation plan: {e}")
            return InstallationPlan(
                components={},
                total_size_mb=0,
                estimated_duration_minutes=0,
                space_after_installation={},
                warnings=[f"Error creating installation plan: {e}"],
                optimizations=[]
            )


class SelectiveInstallationManager:
    """Manager for selective component installation based on available space and priorities."""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.logger = logging.getLogger("selective_installation_manager")
        
        # Component priority mappings
        self.component_priorities = {
            # Critical system components
            'git': ComponentPriority.CRITICAL,
            'vcpp_redist': ComponentPriority.CRITICAL,
            
            # High priority development tools
            'dotnet_sdk': ComponentPriority.HIGH,
            'java_jdk': ComponentPriority.HIGH,
            'powershell7': ComponentPriority.HIGH,
            
            # Medium priority runtimes
            'dotnet_desktop': ComponentPriority.MEDIUM,
            'nodejs': ComponentPriority.MEDIUM,
            'python': ComponentPriority.MEDIUM,
            
            # Lower priority tools
            'anaconda': ComponentPriority.LOW,
            'visual_studio': ComponentPriority.LOW,
            
            # Optional components
            'docker': ComponentPriority.OPTIONAL,
            'unity': ComponentPriority.OPTIONAL,
        }
        
        # Steam Deck specific priorities (optimized for handheld development)
        self.steamdeck_priorities = {
            'git': ComponentPriority.CRITICAL,
            'dotnet_sdk': ComponentPriority.CRITICAL,  # Higher priority on Steam Deck
            'nodejs': ComponentPriority.HIGH,         # Higher priority for web dev
            'python': ComponentPriority.HIGH,         # Higher priority for scripting
            'powershell7': ComponentPriority.MEDIUM,  # Lower priority on Linux-based Steam Deck
            'java_jdk': ComponentPriority.MEDIUM,     # Lower priority on Steam Deck
            'vcpp_redist': ComponentPriority.LOW,     # Lower priority on Linux-based Steam Deck
            'anaconda': ComponentPriority.OPTIONAL,   # Too large for Steam Deck storage
            'visual_studio': ComponentPriority.OPTIONAL,  # Too large for Steam Deck
        }
    
    def get_component_priority(self, component_name: str, steamdeck_mode: bool = False) -> ComponentPriority:
        """Get priority for a component."""
        priorities = self.steamdeck_priorities if steamdeck_mode else self.component_priorities
        return priorities.get(component_name, ComponentPriority.MEDIUM)
    
    def calculate_component_scores(self, components: List[Dict[str, Any]], 
                                 criteria: SelectionCriteria) -> Dict[str, float]:
        """Calculate selection scores for components based on various factors."""
        scores = {}
        
        try:
            for component in components:
                name = component.get('name', 'unknown')
                size_mb = component.get('size_mb', 0)
                
                # Base score from priority
                priority = self.get_component_priority(name, criteria.steamdeck_optimized)
                priority_scores = {
                    ComponentPriority.CRITICAL: 100,
                    ComponentPriority.HIGH: 80,
                    ComponentPriority.MEDIUM: 60,
                    ComponentPriority.LOW: 40,
                    ComponentPriority.OPTIONAL: 20
                }
                score = priority_scores.get(priority, 50)
                
                # Adjust score based on size (smaller components get bonus)
                if size_mb > 0:
                    # Penalize very large components
                    if size_mb > 2000:  # > 2GB
                        score -= 20
                    elif size_mb > 1000:  # > 1GB
                        score -= 10
                    elif size_mb < 100:  # < 100MB
                        score += 10
                
                # Bonus for required components
                if name in criteria.required_components:
                    score += 50
                
                # Penalty for excluded components
                if name in criteria.excluded_components:
                    score = 0
                
                # Steam Deck specific adjustments
                if criteria.steamdeck_optimized:
                    # Prefer lightweight components
                    if size_mb < 200:
                        score += 15
                    elif size_mb > 1000:
                        score -= 25
                    
                    # Prefer cross-platform tools
                    cross_platform_tools = ['git', 'nodejs', 'python', 'dotnet_sdk']
                    if name in cross_platform_tools:
                        score += 10
                
                # Essential-only mode
                if criteria.prefer_essential_only:
                    if priority not in [ComponentPriority.CRITICAL, ComponentPriority.HIGH]:
                        score -= 30
                
                scores[name] = max(score, 0)  # Ensure non-negative scores
                
        except Exception as e:
            self.logger.error(f"Error calculating component scores: {e}")
        
        return scores
    
    def select_components_by_space(self, components: List[Dict[str, Any]], 
                                 available_space_mb: int,
                                 criteria: SelectionCriteria) -> ComponentSelection:
        """Select components that fit within available space using intelligent algorithms."""
        try:
            # Calculate component scores
            scores = self.calculate_component_scores(components, criteria)
            
            # Sort components by score (highest first)
            sorted_components = sorted(components, 
                                     key=lambda c: scores.get(c.get('name', ''), 0), 
                                     reverse=True)
            
            selected = []
            deselected = []
            total_size = 0
            selection_reasons = {}
            recommendations = []
            
            # Apply maximum size constraint if specified
            max_size = criteria.max_total_size_mb or available_space_mb
            effective_limit = min(max_size, available_space_mb)
            
            # First pass: Select required components
            for component in sorted_components:
                name = component.get('name', 'unknown')
                size_mb = component.get('size_mb', 0)
                
                if name in criteria.required_components:
                    if total_size + size_mb <= effective_limit:
                        selected.append(name)
                        total_size += size_mb
                        selection_reasons[name] = "Required component"
                    else:
                        deselected.append(name)
                        selection_reasons[name] = f"Required but insufficient space ({size_mb}MB needed)"
                        recommendations.append(f"Consider freeing space to install required component: {name}")
            
            # Second pass: Select components by priority and score
            for component in sorted_components:
                name = component.get('name', 'unknown')
                size_mb = component.get('size_mb', 0)
                score = scores.get(name, 0)
                priority = self.get_component_priority(name, criteria.steamdeck_optimized)
                
                # Skip if already processed or excluded
                if name in selected or name in deselected or name in criteria.excluded_components:
                    continue
                
                # Check priority threshold
                priority_values = {
                    ComponentPriority.CRITICAL: 5,
                    ComponentPriority.HIGH: 4,
                    ComponentPriority.MEDIUM: 3,
                    ComponentPriority.LOW: 2,
                    ComponentPriority.OPTIONAL: 1
                }
                
                if priority_values.get(priority, 0) < priority_values.get(criteria.priority_threshold, 0):
                    deselected.append(name)
                    selection_reasons[name] = f"Below priority threshold ({priority.value})"
                    continue
                
                # Check if component fits
                if total_size + size_mb <= effective_limit:
                    selected.append(name)
                    total_size += size_mb
                    selection_reasons[name] = f"Selected (priority: {priority.value}, score: {score:.1f})"
                else:
                    deselected.append(name)
                    selection_reasons[name] = f"Insufficient space ({size_mb}MB needed, {effective_limit - total_size}MB available)"
            
            # Generate recommendations
            if deselected:
                recommendations.append(f"Consider selective installation: {len(deselected)} components deselected due to space constraints")
            
            if total_size > available_space_mb * 0.9:  # Using > 90% of available space
                recommendations.append("Installation will use most available space. Consider cleanup after installation.")
            
            if criteria.steamdeck_optimized and any('visual_studio' in name or 'anaconda' in name for name in deselected):
                recommendations.append("Large development environments deselected for Steam Deck optimization")
            
            selection = ComponentSelection(
                selected_components=selected,
                deselected_components=deselected,
                total_size_mb=total_size,
                available_space_mb=available_space_mb,
                selection_reason=selection_reasons,
                recommendations=recommendations
            )
            
            self.logger.info(f"Component selection completed: {len(selected)} selected, {len(deselected)} deselected")
            return selection
            
        except Exception as e:
            self.logger.error(f"Error selecting components by space: {e}")
            return ComponentSelection(
                selected_components=[],
                deselected_components=[c.get('name', 'unknown') for c in components],
                total_size_mb=0,
                available_space_mb=available_space_mb,
                selection_reason={},
                recommendations=[f"Error during component selection: {e}"]
            )
    
    def optimize_selection_for_steamdeck(self, components: List[Dict[str, Any]], 
                                       available_space_mb: int) -> ComponentSelection:
        """Optimize component selection specifically for Steam Deck constraints."""
        criteria = SelectionCriteria(
            max_total_size_mb=min(available_space_mb, 8192),  # Limit to 8GB for Steam Deck
            required_components=['git', 'dotnet_sdk'],  # Essential for Steam Deck development
            excluded_components=['visual_studio', 'anaconda'],  # Too large for Steam Deck
            priority_threshold=ComponentPriority.LOW,
            prefer_essential_only=False,
            steamdeck_optimized=True
        )
        
        selection = self.select_components_by_space(components, available_space_mb, criteria)
        
        # Add Steam Deck specific recommendations
        selection.recommendations.extend([
            "Selection optimized for Steam Deck storage and performance constraints",
            "Large IDEs excluded in favor of lightweight development tools",
            "Consider using remote development for resource-intensive tasks"
        ])
        
        return selection
    
    def create_installation_profiles(self, components: List[Dict[str, Any]], 
                                   available_space_mb: int) -> Dict[str, ComponentSelection]:
        """Create multiple installation profiles for different use cases."""
        profiles = {}
        
        try:
            # Minimal profile - only critical components
            minimal_criteria = SelectionCriteria(
                priority_threshold=ComponentPriority.CRITICAL,
                prefer_essential_only=True
            )
            profiles['minimal'] = self.select_components_by_space(components, available_space_mb, minimal_criteria)
            
            # Standard profile - critical and high priority components
            standard_criteria = SelectionCriteria(
                priority_threshold=ComponentPriority.MEDIUM
            )
            profiles['standard'] = self.select_components_by_space(components, available_space_mb, standard_criteria)
            
            # Full profile - all components that fit
            full_criteria = SelectionCriteria(
                priority_threshold=ComponentPriority.OPTIONAL
            )
            profiles['full'] = self.select_components_by_space(components, available_space_mb, full_criteria)
            
            # Steam Deck profile - optimized for handheld
            profiles['steamdeck'] = self.optimize_selection_for_steamdeck(components, available_space_mb)
            
            # Developer profile - focused on development tools
            dev_criteria = SelectionCriteria(
                required_components=['git', 'dotnet_sdk', 'nodejs', 'python'],
                priority_threshold=ComponentPriority.LOW
            )
            profiles['developer'] = self.select_components_by_space(components, available_space_mb, dev_criteria)
            
            self.logger.info(f"Created {len(profiles)} installation profiles")
            
        except Exception as e:
            self.logger.error(f"Error creating installation profiles: {e}")
        
        return profiles
    
    def get_space_optimization_suggestions(self, components: List[Dict[str, Any]], 
                                         available_space_mb: int) -> List[str]:
        """Get suggestions for optimizing space usage."""
        suggestions = []
        
        try:
            total_required = sum(c.get('size_mb', 0) for c in components)
            
            if total_required > available_space_mb:
                shortage_mb = total_required - available_space_mb
                suggestions.append(f"Need {shortage_mb/1024:.1f}GB more space for full installation")
                
                # Suggest largest components to skip
                large_components = sorted(components, key=lambda c: c.get('size_mb', 0), reverse=True)[:3]
                suggestions.append("Consider skipping these large components:")
                for comp in large_components:
                    name = comp.get('name', 'unknown')
                    size_mb = comp.get('size_mb', 0)
                    priority = self.get_component_priority(name)
                    suggestions.append(f"  - {name}: {size_mb}MB ({priority.value} priority)")
            
            # Suggest cleanup if space is tight
            if available_space_mb < 5120:  # Less than 5GB available
                suggestions.append("Consider cleaning temporary files and downloads before installation")
                suggestions.append("Use disk cleanup tools to free additional space")
            
            # Suggest alternative installation locations
            drives = self.storage_manager.get_drive_info()
            if len(drives) > 1:
                other_drives = [d for d in drives if d.free_space_gb > 2.0]
                if other_drives:
                    suggestions.append("Consider installing some components on other drives:")
                    for drive in other_drives[:2]:  # Show top 2 alternatives
                        suggestions.append(f"  - {drive.path}: {drive.free_space_gb:.1f}GB available")
            
        except Exception as e:
            self.logger.error(f"Error generating space optimization suggestions: {e}")
            suggestions.append("Unable to generate optimization suggestions")
        
        return suggestions


# Initialize selective manager after StorageManager is defined
def _init_selective_manager(storage_manager):
    """Initialize selective installation manager."""
    if storage_manager.selective_manager is None:
        storage_manager.selective_manager = SelectiveInstallationManager(storage_manager)


# Extend StorageManager with selective installation methods
def create_selective_installation_plan(self, components: List[Dict[str, Any]], 
                                     criteria: Optional[SelectionCriteria] = None) -> Tuple[ComponentSelection, InstallationPlan]:
    """Create a selective installation plan based on available space and criteria."""
    _init_selective_manager(self)
    
    try:
        # Get available space
        drives = self.get_drive_info()
        total_available_mb = sum(int(drive.free_space_gb * 1024) for drive in drives)
        
        # Use default criteria if none provided
        if criteria is None:
            criteria = SelectionCriteria()
        
        # Select components
        selection = self.selective_manager.select_components_by_space(
            components, total_available_mb, criteria
        )
        
        # Create requirements for selected components
        selected_components = [c for c in components if c.get('name') in selection.selected_components]
        requirements = self.calculate_storage_requirements(selected_components)
        
        # Create installation plan
        plan = self.create_installation_plan(requirements)
        
        return selection, plan
        
    except Exception as e:
        self.logger.error(f"Error creating selective installation plan: {e}")
        empty_selection = ComponentSelection([], [], 0, 0, {})
        empty_plan = InstallationPlan({}, 0, 0, {})
        return empty_selection, empty_plan


def get_installation_profiles(self, components: List[Dict[str, Any]]) -> Dict[str, ComponentSelection]:
    """Get predefined installation profiles."""
    _init_selective_manager(self)
    
    drives = self.get_drive_info()
    total_available_mb = sum(int(drive.free_space_gb * 1024) for drive in drives)
    
    return self.selective_manager.create_installation_profiles(components, total_available_mb)


def get_optimization_suggestions(self, components: List[Dict[str, Any]]) -> List[str]:
    """Get space optimization suggestions."""
    _init_selective_manager(self)
    
    drives = self.get_drive_info()
    total_available_mb = sum(int(drive.free_space_gb * 1024) for drive in drives)
    
    return self.selective_manager.get_space_optimization_suggestions(components, total_available_mb)


# Add methods to StorageManager class
StorageManager.create_selective_installation_plan = create_selective_installation_plan
StorageManager.get_installation_profiles = get_installation_profiles
StorageManager.get_optimization_suggestions = get_optimization_suggestions


# Test the module when run directly
if __name__ == "__main__":
    print("Testing StorageManager...")
    
    manager = StorageManager()
    
    # Test drive detection
    drives = manager.get_drive_info()
    print(f"Detected {len(drives)} drives:")
    for drive in drives:
        print(f"  {drive.path}: {drive.free_space_gb:.1f}GB free / {drive.total_space_gb:.1f}GB total ({drive.drive_type.value})")
    
    # Test space checking
    space_info = manager.check_available_space()
    print(f"\nSpace information for {len(space_info)} drives:")
    for path, info in space_info.items():
        print(f"  {path}: {info['free_gb']:.1f}GB free ({info['free_percent']:.1f}%)")
    
    print("StorageManager test completed successfully!")


class CleanupType(Enum):
    """Types of cleanup operations."""
    TEMPORARY_FILES = "temporary_files"
    INSTALLATION_CACHE = "installation_cache"
    LOG_FILES = "log_files"
    BACKUP_FILES = "backup_files"
    DOWNLOAD_CACHE = "download_cache"
    SYSTEM_TEMP = "system_temp"


class OptimizationType(Enum):
    """Types of storage optimization."""
    DRIVE_DISTRIBUTION = "drive_distribution"
    CACHE_MANAGEMENT = "cache_management"
    COMPRESSION = "compression"
    DEDUPLICATION = "deduplication"
    CLEANUP = "cleanup"


@dataclass
class CleanupResult:
    """Result of cleanup operation."""
    cleanup_type: CleanupType
    files_removed: int
    directories_removed: int
    space_freed_mb: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Result of storage optimization."""
    optimization_type: OptimizationType
    space_saved_mb: int
    performance_improvement_percent: float
    operations_performed: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class CleanupPlan:
    """Plan for storage cleanup operations."""
    cleanup_operations: List[CleanupType]
    estimated_space_freed_mb: int
    estimated_duration_minutes: int
    safe_operations: List[CleanupType]
    risky_operations: List[CleanupType]
    warnings: List[str] = field(default_factory=list)


class StorageCleanupManager:
    """Manager for storage cleanup and optimization operations."""
    
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.logger = logging.getLogger("storage_cleanup_manager")
        
        # Cleanup configuration
        self.temp_directories = [
            os.path.expandvars("%TEMP%"),
            os.path.expandvars("%TMP%"),
            "C:\\Windows\\Temp",
            "temp",
            "cache",
            "downloads",
            "logs"
        ]
        
        # File patterns for cleanup
        self.temp_file_patterns = [
            "*.tmp", "*.temp", "*.cache", "*.log", "*.bak",
            "*.old", "*.~*", "*~", "*.swp", "*.swo"
        ]
        
        # Safe cleanup thresholds
        self.max_file_age_days = 7  # Only clean files older than 7 days
        self.max_log_size_mb = 100  # Clean log files larger than 100MB
        self.min_free_space_mb = 1024  # Maintain at least 1GB free space
    
    def analyze_cleanup_opportunities(self) -> CleanupPlan:
        """Analyze potential cleanup opportunities."""
        try:
            cleanup_operations = []
            estimated_space = 0
            estimated_duration = 0
            safe_operations = []
            risky_operations = []
            warnings = []
            
            # Check temporary files
            temp_analysis = self._analyze_temporary_files()
            if temp_analysis['size_mb'] > 10:  # Only if > 10MB
                cleanup_operations.append(CleanupType.TEMPORARY_FILES)
                safe_operations.append(CleanupType.TEMPORARY_FILES)
                estimated_space += temp_analysis['size_mb']
                estimated_duration += 2
            
            # Check installation cache
            cache_analysis = self._analyze_installation_cache()
            if cache_analysis['size_mb'] > 50:  # Only if > 50MB
                cleanup_operations.append(CleanupType.INSTALLATION_CACHE)
                safe_operations.append(CleanupType.INSTALLATION_CACHE)
                estimated_space += cache_analysis['size_mb']
                estimated_duration += 3
            
            # Check log files
            log_analysis = self._analyze_log_files()
            if log_analysis['size_mb'] > 20:  # Only if > 20MB
                cleanup_operations.append(CleanupType.LOG_FILES)
                safe_operations.append(CleanupType.LOG_FILES)
                estimated_space += log_analysis['size_mb']
                estimated_duration += 1
            
            # Check backup files
            backup_analysis = self._analyze_backup_files()
            if backup_analysis['size_mb'] > 100:  # Only if > 100MB
                cleanup_operations.append(CleanupType.BACKUP_FILES)
                risky_operations.append(CleanupType.BACKUP_FILES)  # Risky because backups might be needed
                estimated_space += backup_analysis['size_mb']
                estimated_duration += 5
                warnings.append("Backup file cleanup may remove important recovery files")
            
            # Check download cache
            download_analysis = self._analyze_download_cache()
            if download_analysis['size_mb'] > 200:  # Only if > 200MB
                cleanup_operations.append(CleanupType.DOWNLOAD_CACHE)
                safe_operations.append(CleanupType.DOWNLOAD_CACHE)
                estimated_space += download_analysis['size_mb']
                estimated_duration += 4
            
            # Check system temp (risky)
            system_temp_analysis = self._analyze_system_temp()
            if system_temp_analysis['size_mb'] > 500:  # Only if > 500MB
                cleanup_operations.append(CleanupType.SYSTEM_TEMP)
                risky_operations.append(CleanupType.SYSTEM_TEMP)
                estimated_space += min(system_temp_analysis['size_mb'], 1000)  # Cap at 1GB for safety
                estimated_duration += 10
                warnings.append("System temp cleanup may affect running applications")
            
            plan = CleanupPlan(
                cleanup_operations=cleanup_operations,
                estimated_space_freed_mb=estimated_space,
                estimated_duration_minutes=max(estimated_duration, 1),
                safe_operations=safe_operations,
                risky_operations=risky_operations,
                warnings=warnings
            )
            
            self.logger.info(f"Cleanup analysis completed: {len(cleanup_operations)} operations, {estimated_space}MB potential")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error analyzing cleanup opportunities: {e}")
            return CleanupPlan([], 0, 0, [], [], [f"Error analyzing cleanup: {e}"])
    
    def _analyze_temporary_files(self) -> Dict[str, Any]:
        """Analyze temporary files for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            for temp_dir in self.temp_directories:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_safe_to_clean(file_path):
                                    size = os.path.getsize(file_path)
                                    total_size_mb += size / (1024 * 1024)
                                    file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing temporary files: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _analyze_installation_cache(self) -> Dict[str, Any]:
        """Analyze installation cache for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            cache_dirs = ['cache', 'temp_download', 'downloads']
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    for root, dirs, files in os.walk(cache_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if file.endswith(('.exe', '.msi', '.zip', '.tar.gz')):
                                    # Only count installer files older than 1 day
                                    if self._is_file_old(file_path, days=1):
                                        size = os.path.getsize(file_path)
                                        total_size_mb += size / (1024 * 1024)
                                        file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing installation cache: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _analyze_log_files(self) -> Dict[str, Any]:
        """Analyze log files for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            log_dirs = ['logs', 'log']
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if file.endswith(('.log', '.txt')) and self._is_file_old(file_path, days=7):
                                    size = os.path.getsize(file_path)
                                    if size > self.max_log_size_mb * 1024 * 1024:  # Large log files
                                        total_size_mb += size / (1024 * 1024)
                                        file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing log files: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _analyze_backup_files(self) -> Dict[str, Any]:
        """Analyze backup files for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            backup_dirs = ['backups', 'backup', 'rollback']
            for backup_dir in backup_dirs:
                if os.path.exists(backup_dir):
                    for root, dirs, files in os.walk(backup_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_file_old(file_path, days=30):  # Old backups
                                    size = os.path.getsize(file_path)
                                    total_size_mb += size / (1024 * 1024)
                                    file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing backup files: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _analyze_download_cache(self) -> Dict[str, Any]:
        """Analyze download cache for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            download_dirs = ['downloads', 'temp_download']
            for download_dir in download_dirs:
                if os.path.exists(download_dir):
                    for root, dirs, files in os.walk(download_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_file_old(file_path, days=3):  # Downloads older than 3 days
                                    size = os.path.getsize(file_path)
                                    total_size_mb += size / (1024 * 1024)
                                    file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing download cache: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _analyze_system_temp(self) -> Dict[str, Any]:
        """Analyze system temporary files for cleanup."""
        total_size_mb = 0
        file_count = 0
        
        try:
            system_temp_dirs = [
                os.path.expandvars("%TEMP%"),
                os.path.expandvars("%TMP%"),
                "C:\\Windows\\Temp"
            ]
            
            for temp_dir in system_temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_safe_to_clean(file_path) and self._is_file_old(file_path, days=1):
                                    size = os.path.getsize(file_path)
                                    total_size_mb += size / (1024 * 1024)
                                    file_count += 1
                            except (OSError, PermissionError):
                                continue
        except Exception as e:
            self.logger.debug(f"Error analyzing system temp: {e}")
        
        return {'size_mb': int(total_size_mb), 'file_count': file_count}
    
    def _is_safe_to_clean(self, file_path: str) -> bool:
        """Check if a file is safe to clean."""
        try:
            # Don't clean files that are currently in use
            if self._is_file_in_use(file_path):
                return False
            
            # Don't clean very recent files (less than 1 hour old)
            if not self._is_file_old(file_path, hours=1):
                return False
            
            # Check file patterns
            filename = os.path.basename(file_path).lower()
            for pattern in self.temp_file_patterns:
                if filename.endswith(pattern.replace('*', '')):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_file_old(self, file_path: str, days: int = 0, hours: int = 0) -> bool:
        """Check if a file is older than specified time."""
        try:
            file_time = os.path.getmtime(file_path)
            current_time = datetime.now().timestamp()
            age_seconds = current_time - file_time
            
            threshold_seconds = (days * 24 * 3600) + (hours * 3600)
            return age_seconds > threshold_seconds
            
        except Exception:
            return False
    
    def _is_file_in_use(self, file_path: str) -> bool:
        """Check if a file is currently in use."""
        try:
            # Try to open the file exclusively
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (IOError, OSError, PermissionError):
            return True
    
    def perform_cleanup(self, cleanup_types: List[CleanupType], 
                       safe_only: bool = True) -> List[CleanupResult]:
        """Perform cleanup operations."""
        results = []
        
        try:
            for cleanup_type in cleanup_types:
                start_time = datetime.now()
                
                if cleanup_type == CleanupType.TEMPORARY_FILES:
                    result = self._cleanup_temporary_files()
                elif cleanup_type == CleanupType.INSTALLATION_CACHE:
                    result = self._cleanup_installation_cache()
                elif cleanup_type == CleanupType.LOG_FILES:
                    result = self._cleanup_log_files()
                elif cleanup_type == CleanupType.BACKUP_FILES:
                    if not safe_only:  # Only if not in safe mode
                        result = self._cleanup_backup_files()
                    else:
                        continue
                elif cleanup_type == CleanupType.DOWNLOAD_CACHE:
                    result = self._cleanup_download_cache()
                elif cleanup_type == CleanupType.SYSTEM_TEMP:
                    if not safe_only:  # Only if not in safe mode
                        result = self._cleanup_system_temp()
                    else:
                        continue
                else:
                    continue
                
                # Calculate duration
                end_time = datetime.now()
                result.duration_seconds = (end_time - start_time).total_seconds()
                
                results.append(result)
                self.logger.info(f"Cleanup {cleanup_type.value} completed: {result.space_freed_mb}MB freed")
                
        except Exception as e:
            self.logger.error(f"Error performing cleanup: {e}")
        
        return results
    
    def _cleanup_temporary_files(self) -> CleanupResult:
        """Clean up temporary files."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            for temp_dir in self.temp_directories:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir, topdown=False):
                        # Clean files
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_safe_to_clean(file_path):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    files_removed += 1
                                    space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
                        
                        # Clean empty directories
                        for dir_name in dirs:
                            try:
                                dir_path = os.path.join(root, dir_name)
                                if not os.listdir(dir_path):  # Empty directory
                                    os.rmdir(dir_path)
                                    dirs_removed += 1
                            except Exception as e:
                                errors.append(f"Failed to remove directory {dir_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during temporary file cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.TEMPORARY_FILES,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,  # Will be set by caller
            errors=errors,
            warnings=warnings
        )
    
    def _cleanup_installation_cache(self) -> CleanupResult:
        """Clean up installation cache files."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            cache_dirs = ['cache', 'temp_download', 'downloads']
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    for root, dirs, files in os.walk(cache_dir, topdown=False):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if (file.endswith(('.exe', '.msi', '.zip', '.tar.gz')) and 
                                    self._is_file_old(file_path, days=1)):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    files_removed += 1
                                    space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during installation cache cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.INSTALLATION_CACHE,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,
            errors=errors,
            warnings=warnings
        )
    
    def _cleanup_log_files(self) -> CleanupResult:
        """Clean up old log files."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            log_dirs = ['logs', 'log']
            for log_dir in log_dirs:
                if os.path.exists(log_dir):
                    for root, dirs, files in os.walk(log_dir, topdown=False):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if (file.endswith(('.log', '.txt')) and 
                                    self._is_file_old(file_path, days=7)):
                                    size = os.path.getsize(file_path)
                                    if size > self.max_log_size_mb * 1024 * 1024:
                                        os.remove(file_path)
                                        files_removed += 1
                                        space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during log file cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.LOG_FILES,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,
            errors=errors,
            warnings=warnings
        )
    
    def _cleanup_backup_files(self) -> CleanupResult:
        """Clean up old backup files."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = ["Backup files were removed - recovery may be limited"]
        
        try:
            backup_dirs = ['backups', 'backup', 'rollback']
            for backup_dir in backup_dirs:
                if os.path.exists(backup_dir):
                    for root, dirs, files in os.walk(backup_dir, topdown=False):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_file_old(file_path, days=30):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    files_removed += 1
                                    space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during backup file cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.BACKUP_FILES,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,
            errors=errors,
            warnings=warnings
        )
    
    def _cleanup_download_cache(self) -> CleanupResult:
        """Clean up download cache files."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            download_dirs = ['downloads', 'temp_download']
            for download_dir in download_dirs:
                if os.path.exists(download_dir):
                    for root, dirs, files in os.walk(download_dir, topdown=False):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if self._is_file_old(file_path, days=3):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    files_removed += 1
                                    space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during download cache cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.DOWNLOAD_CACHE,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,
            errors=errors,
            warnings=warnings
        )
    
    def _cleanup_system_temp(self) -> CleanupResult:
        """Clean up system temporary files (risky operation)."""
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        warnings = ["System temp cleanup may affect running applications"]
        
        try:
            system_temp_dirs = [
                os.path.expandvars("%TEMP%"),
                os.path.expandvars("%TMP%")
            ]
            
            for temp_dir in system_temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir, topdown=False):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if (self._is_safe_to_clean(file_path) and 
                                    self._is_file_old(file_path, days=1)):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    files_removed += 1
                                    space_freed += size
                            except Exception as e:
                                errors.append(f"Failed to remove {file_path}: {e}")
        
        except Exception as e:
            errors.append(f"Error during system temp cleanup: {e}")
        
        return CleanupResult(
            cleanup_type=CleanupType.SYSTEM_TEMP,
            files_removed=files_removed,
            directories_removed=dirs_removed,
            space_freed_mb=int(space_freed / (1024 * 1024)),
            duration_seconds=0,
            errors=errors,
            warnings=warnings
        )
    
    def optimize_drive_distribution(self, components: List[Dict[str, Any]]) -> OptimizationResult:
        """Optimize component distribution across multiple drives."""
        try:
            start_time = datetime.now()
            drives = self.storage_manager.get_drive_info()
            
            if len(drives) <= 1:
                return OptimizationResult(
                    optimization_type=OptimizationType.DRIVE_DISTRIBUTION,
                    space_saved_mb=0,
                    performance_improvement_percent=0,
                    operations_performed=[],
                    recommendations=["Only one drive available - no distribution optimization possible"],
                    duration_seconds=0
                )
            
            # Analyze current distribution
            operations = []
            recommendations = []
            space_saved = 0
            performance_improvement = 0
            
            # Sort drives by performance and available space
            sorted_drives = sorted(drives, key=lambda d: (d.performance_score, d.free_space_gb), reverse=True)
            
            # Recommend distribution strategy
            high_perf_drives = [d for d in drives if d.performance_score >= 80]
            medium_perf_drives = [d for d in drives if 50 <= d.performance_score < 80]
            low_perf_drives = [d for d in drives if d.performance_score < 50]
            
            if high_perf_drives:
                recommendations.append(f"Install development tools on high-performance drives: {', '.join([d.path for d in high_perf_drives[:2]])}")
                operations.append("Identified high-performance drives for development tools")
                performance_improvement += 15
            
            if medium_perf_drives:
                recommendations.append(f"Install runtimes on medium-performance drives: {', '.join([d.path for d in medium_perf_drives[:2]])}")
                operations.append("Identified medium-performance drives for runtimes")
                performance_improvement += 10
            
            if low_perf_drives:
                recommendations.append(f"Use low-performance drives for archives and backups: {', '.join([d.path for d in low_perf_drives[:2]])}")
                operations.append("Identified low-performance drives for archives")
            
            # Check for unbalanced distribution
            drive_usage = {}
            total_component_size = sum(c.get('size_mb', 0) for c in components)
            
            for drive in drives:
                drive_usage[drive.path] = 0
            
            # Simulate optimal distribution
            remaining_components = components.copy()
            for drive in sorted_drives:
                drive_capacity = drive.free_space_gb * 1024  # Convert to MB
                drive_allocation = min(drive_capacity * 0.8, total_component_size * 0.4)  # Max 80% of drive, 40% of total
                
                allocated_size = 0
                for component in remaining_components[:]:
                    comp_size = component.get('size_mb', 0)
                    if allocated_size + comp_size <= drive_allocation:
                        drive_usage[drive.path] += comp_size
                        allocated_size += comp_size
                        remaining_components.remove(component)
            
            # Calculate balance score
            usage_values = list(drive_usage.values())
            if usage_values:
                avg_usage = sum(usage_values) / len(usage_values)
                balance_score = 100 - (max(usage_values) - min(usage_values)) / avg_usage * 100
                
                if balance_score < 70:
                    recommendations.append("Consider redistributing components for better balance across drives")
                    operations.append("Analyzed drive balance and found optimization opportunities")
                    performance_improvement += 5
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return OptimizationResult(
                optimization_type=OptimizationType.DRIVE_DISTRIBUTION,
                space_saved_mb=space_saved,
                performance_improvement_percent=performance_improvement,
                operations_performed=operations,
                recommendations=recommendations,
                duration_seconds=duration
            )
            
        except Exception as e:
            self.logger.error(f"Error optimizing drive distribution: {e}")
            return OptimizationResult(
                optimization_type=OptimizationType.DRIVE_DISTRIBUTION,
                space_saved_mb=0,
                performance_improvement_percent=0,
                operations_performed=[],
                recommendations=[f"Error during optimization: {e}"],
                duration_seconds=0
            )
    
    def get_post_installation_cleanup_plan(self, installed_components: List[str]) -> CleanupPlan:
        """Get cleanup plan for after installation completion."""
        try:
            cleanup_operations = [
                CleanupType.TEMPORARY_FILES,
                CleanupType.INSTALLATION_CACHE,
                CleanupType.DOWNLOAD_CACHE
            ]
            
            # Estimate cleanup potential
            estimated_space = 0
            temp_analysis = self._analyze_temporary_files()
            cache_analysis = self._analyze_installation_cache()
            download_analysis = self._analyze_download_cache()
            
            estimated_space = temp_analysis['size_mb'] + cache_analysis['size_mb'] + download_analysis['size_mb']
            
            plan = CleanupPlan(
                cleanup_operations=cleanup_operations,
                estimated_space_freed_mb=estimated_space,
                estimated_duration_minutes=5,
                safe_operations=cleanup_operations,  # All are safe post-installation
                risky_operations=[],
                warnings=[]
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating post-installation cleanup plan: {e}")
            return CleanupPlan([], 0, 0, [], [], [f"Error creating cleanup plan: {e}"])


# Add cleanup manager to StorageManager
def get_cleanup_manager(self) -> StorageCleanupManager:
    """Get the cleanup manager instance."""
    if not hasattr(self, '_cleanup_manager'):
        self._cleanup_manager = StorageCleanupManager(self)
    return self._cleanup_manager


def perform_post_installation_cleanup(self, installed_components: List[str]) -> List[CleanupResult]:
    """Perform cleanup after installation completion."""
    cleanup_manager = self.get_cleanup_manager()
    plan = cleanup_manager.get_post_installation_cleanup_plan(installed_components)
    
    if plan.cleanup_operations:
        self.logger.info(f"Starting post-installation cleanup: {len(plan.cleanup_operations)} operations")
        results = cleanup_manager.perform_cleanup(plan.safe_operations, safe_only=True)
        
        total_space_freed = sum(r.space_freed_mb for r in results)
        self.logger.info(f"Post-installation cleanup completed: {total_space_freed}MB freed")
        
        return results
    else:
        return []


def get_storage_optimization_recommendations(self, components: List[Dict[str, Any]]) -> List[OptimizationResult]:
    """Get storage optimization recommendations."""
    cleanup_manager = self.get_cleanup_manager()
    results = []
    
    # Drive distribution optimization
    distribution_result = cleanup_manager.optimize_drive_distribution(components)
    results.append(distribution_result)
    
    return results


# Add methods to StorageManager class
StorageManager.get_cleanup_manager = get_cleanup_manager
StorageManager.perform_post_installation_cleanup = perform_post_installation_cleanup
StorageManager.get_storage_optimization_recommendations = get_storage_optimization_recommendations