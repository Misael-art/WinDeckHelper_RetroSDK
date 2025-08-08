# -*- coding: utf-8 -*-
"""
Modern Frontend Manager - Unified Interface Infrastructure

This module implements a comprehensive modern frontend manager with clear dashboard design,
real-time progress display system, and component organization by category and status.

Requirements addressed:
- 8.1: Unified interface with clear dashboard and real-time progress
- 8.2: Component organization by category and status
"""

import logging
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from .unified_detection_engine import UnifiedDetectionEngine
    from .dependency_validation_system import DependencyValidationSystem
    from .advanced_installation_manager import AdvancedInstallationManager
    from .plugin_system_manager import PluginSystemManager
    from .security_manager import SecurityManager, SecurityLevel
except ImportError:
    # Fallback for direct execution
    from unified_detection_engine import UnifiedDetectionEngine
    from dependency_validation_system import DependencyValidationSystem
    from advanced_installation_manager import AdvancedInstallationManager
    from plugin_system_manager import PluginSystemManager
    from security_manager import SecurityManager, SecurityLevel


class ComponentCategory(Enum):
    """Categories for component organization"""
    ESSENTIAL_RUNTIMES = "essential_runtimes"
    DEVELOPMENT_TOOLS = "development_tools"
    PACKAGE_MANAGERS = "package_managers"
    EDITORS_IDES = "editors_ides"
    RETRO_DEVKITS = "retro_devkits"
    UTILITIES = "utilities"
    PLUGINS = "plugins"
    CUSTOM = "custom"


class ComponentStatus(Enum):
    """Status of components"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    INSTALLING = "installing"
    UPDATING = "updating"
    FAILED = "failed"
    CONFLICT = "conflict"
    DISABLED = "disabled"


class OperationType(Enum):
    """Types of operations"""
    DETECTION = "detection"
    INSTALLATION = "installation"
    UPDATE = "update"
    VALIDATION = "validation"
    DOWNLOAD = "download"
    CONFIGURATION = "configuration"
    CLEANUP = "cleanup"


class ProgressLevel(Enum):
    """Progress detail levels"""
    SUMMARY = "summary"
    DETAILED = "detailed"
    VERBOSE = "verbose"


@dataclass
class ComponentInfo:
    """Information about a component"""
    name: str
    display_name: str
    category: ComponentCategory
    status: ComponentStatus
    version: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    priority: int = 50  # 0-100, higher = more important
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    size_mb: Optional[float] = None
    last_updated: Optional[datetime] = None
    installation_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationProgress:
    """Progress information for operations"""
    operation_id: str
    operation_type: OperationType
    component_name: Optional[str]
    title: str
    description: str
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 1
    current_step_number: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    speed: Optional[str] = None  # e.g., "1.2 MB/s"
    details: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    is_completed: bool = False
    is_cancelled: bool = False
    result: Optional[Any] = None


@dataclass
class DashboardState:
    """Current state of the dashboard"""
    components: Dict[str, ComponentInfo] = field(default_factory=dict)
    active_operations: Dict[str, OperationProgress] = field(default_factory=dict)
    completed_operations: List[OperationProgress] = field(default_factory=list)
    system_status: Dict[str, Any] = field(default_factory=dict)
    notifications: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    filter_category: Optional[ComponentCategory] = None
    filter_status: Optional[ComponentStatus] = None
    search_query: str = ""


@dataclass
class InterfaceDesignResult:
    """Result of interface design operations"""
    success: bool
    dashboard_created: bool = False
    components_organized: bool = False
    progress_system_ready: bool = False
    error_message: Optional[str] = None
    interface_elements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressDisplayResult:
    """Result of progress display operations"""
    success: bool
    operation_id: str
    display_updated: bool = False
    real_time_enabled: bool = False
    error_message: Optional[str] = None
    progress_data: Optional[OperationProgress] = None


@dataclass
class OrganizationResult:
    """Result of component organization operations"""
    success: bool
    categories_created: int = 0
    components_categorized: int = 0
    status_filters_applied: bool = False
    error_message: Optional[str] = None
    organization_data: Dict[str, Any] = field(default_factory=dict)


class ModernFrontendManager:
    """
    Comprehensive Modern Frontend Manager
    
    Provides:
    - Unified interface with clear dashboard design
    - Real-time progress display system for all operations
    - Component organization by category and status
    - Responsive UI component infrastructure
    - Event-driven updates and notifications
    """
    
    def __init__(self, 
                 detection_engine: Optional[UnifiedDetectionEngine] = None,
                 dependency_validator: Optional[DependencyValidationSystem] = None,
                 installation_manager: Optional[AdvancedInstallationManager] = None,
                 plugin_manager: Optional[PluginSystemManager] = None,
                 security_manager: Optional[SecurityManager] = None):
        """
        Initialize Modern Frontend Manager
        
        Args:
            detection_engine: Detection engine for component discovery
            dependency_validator: Dependency validation system
            installation_manager: Installation management system
            plugin_manager: Plugin system manager
            security_manager: Security manager for auditing
        """
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.detection_engine = detection_engine or UnifiedDetectionEngine()
        self.dependency_validator = dependency_validator or DependencyValidationSystem()
        self.installation_manager = installation_manager or AdvancedInstallationManager()
        self.plugin_manager = plugin_manager or PluginSystemManager()
        self.security_manager = security_manager or SecurityManager()
        
        # Dashboard state
        self.dashboard_state = DashboardState()
        self.progress_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.state_subscribers: List[Callable] = []
        
        # Configuration
        self.update_interval = 1.0  # seconds
        self.max_completed_operations = 100
        self.max_notifications = 50
        self.enable_real_time_updates = True
        
        # Threading
        self._lock = threading.RLock()
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Interface elements registry
        self.interface_elements: Dict[str, Any] = {}
        
        # Load configuration
        self._load_frontend_config()
        
        # Initialize dashboard
        self._initialize_dashboard()
        
        self.logger.info("Modern Frontend Manager initialized")
    
    def design_unified_interface_with_clear_dashboard(self) -> InterfaceDesignResult:
        """
        Design unified interface with clear dashboard
        
        Returns:
            InterfaceDesignResult: Result of interface design
        """
        try:
            result = InterfaceDesignResult(success=False)
            
            # Create main dashboard structure
            dashboard_created = self._create_main_dashboard()
            result.dashboard_created = dashboard_created
            
            # Organize components by category
            components_organized = self._organize_components_by_category()
            result.components_organized = components_organized
            
            # Setup progress display system
            progress_system_ready = self._setup_progress_display_system()
            result.progress_system_ready = progress_system_ready
            
            # Create interface elements
            interface_elements = self._create_interface_elements()
            result.interface_elements = interface_elements
            
            # Register interface elements
            self.interface_elements.update(interface_elements)
            
            # Validate interface design
            if dashboard_created and components_organized and progress_system_ready:
                result.success = True
                self.logger.info("Successfully designed unified interface with clear dashboard")
                
                # Audit interface creation
                self.security_manager.audit_critical_operation(
                    operation="interface_design",
                    component="modern_frontend_manager",
                    details={
                        "dashboard_created": dashboard_created,
                        "components_organized": components_organized,
                        "progress_system_ready": progress_system_ready,
                        "interface_elements_count": len(interface_elements)
                    },
                    success=True,
                    security_level=SecurityLevel.LOW
                )
            else:
                result.error_message = "Failed to create complete interface design"
                self.logger.error("Interface design incomplete")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error designing unified interface: {e}")
            return InterfaceDesignResult(
                success=False,
                error_message=str(e)
            )
    
    def show_detailed_real_time_progress(self, operation: str, 
                                       operation_type: OperationType = OperationType.INSTALLATION,
                                       component_name: Optional[str] = None) -> ProgressDisplayResult:
        """
        Show detailed real-time progress for operations
        
        Args:
            operation: Operation identifier
            operation_type: Type of operation
            component_name: Name of component being processed
            
        Returns:
            ProgressDisplayResult: Result of progress display setup
        """
        try:
            operation_id = f"{operation}_{datetime.now().timestamp()}"
            
            # Create progress tracking
            progress = OperationProgress(
                operation_id=operation_id,
                operation_type=operation_type,
                component_name=component_name,
                title=f"{operation_type.value.title()} Progress",
                description=f"Processing {operation}"
            )
            
            # Register progress tracking
            with self._lock:
                self.dashboard_state.active_operations[operation_id] = progress
            
            # Setup real-time updates
            real_time_enabled = self._enable_real_time_progress_updates(operation_id)
            
            # Notify subscribers
            self._notify_progress_subscribers(operation_id, progress)
            
            result = ProgressDisplayResult(
                success=True,
                operation_id=operation_id,
                display_updated=True,
                real_time_enabled=real_time_enabled,
                progress_data=progress
            )
            
            self.logger.info(f"Started real-time progress tracking for operation: {operation_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error setting up progress display: {e}")
            return ProgressDisplayResult(
                success=False,
                operation_id="",
                error_message=str(e)
            )
    
    def organize_components_by_category_and_status(self) -> OrganizationResult:
        """
        Organize components by category and status
        
        Returns:
            OrganizationResult: Result of organization operation
        """
        try:
            result = OrganizationResult(success=False)
            
            # Detect all components
            detection_result = self.detection_engine.detect_all_applications()
            
            # Categorize components
            categorized_components = self._categorize_components(detection_result)
            result.components_categorized = len(categorized_components)
            
            # Create category structure
            categories_created = self._create_category_structure(categorized_components)
            result.categories_created = categories_created
            
            # Apply status filters
            status_filters_applied = self._apply_status_filters()
            result.status_filters_applied = status_filters_applied
            
            # Update dashboard state
            with self._lock:
                self.dashboard_state.components.update(categorized_components)
                self.dashboard_state.last_updated = datetime.now()
            
            # Create organization data
            organization_data = self._create_organization_data()
            result.organization_data = organization_data
            
            result.success = True
            self.logger.info(f"Successfully organized {len(categorized_components)} components into {categories_created} categories")
            
            # Notify state subscribers
            self._notify_state_subscribers()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error organizing components: {e}")
            return OrganizationResult(
                success=False,
                error_message=str(e)
            )
    
    def update_progress(self, operation_id: str, 
                       progress_percentage: float,
                       current_step: str = "",
                       details: Optional[List[str]] = None,
                       warnings: Optional[List[str]] = None,
                       errors: Optional[List[str]] = None):
        """
        Update progress for an active operation
        
        Args:
            operation_id: ID of the operation
            progress_percentage: Progress percentage (0-100)
            current_step: Description of current step
            details: Additional details
            warnings: Warning messages
            errors: Error messages
        """
        try:
            with self._lock:
                if operation_id not in self.dashboard_state.active_operations:
                    self.logger.warning(f"Operation {operation_id} not found in active operations")
                    return
                
                progress = self.dashboard_state.active_operations[operation_id]
                
                # Update progress data
                progress.progress_percentage = min(100.0, max(0.0, progress_percentage))
                if current_step:
                    progress.current_step = current_step
                if details:
                    progress.details.extend(details)
                if warnings:
                    progress.warnings.extend(warnings)
                if errors:
                    progress.errors.extend(errors)
                
                # Calculate estimated completion
                if progress.progress_percentage > 0:
                    elapsed = datetime.now() - progress.start_time
                    total_estimated = elapsed.total_seconds() * (100.0 / progress.progress_percentage)
                    progress.estimated_completion = progress.start_time + timedelta(seconds=total_estimated)
                
                # Mark as completed if 100%
                if progress.progress_percentage >= 100.0:
                    progress.is_completed = True
                    self._complete_operation(operation_id)
            
            # Notify progress subscribers
            self._notify_progress_subscribers(operation_id, progress)
            
        except Exception as e:
            self.logger.error(f"Error updating progress for {operation_id}: {e}")
    
    def get_dashboard_state(self) -> DashboardState:
        """
        Get current dashboard state
        
        Returns:
            DashboardState: Current state of the dashboard
        """
        with self._lock:
            return self.dashboard_state
    
    def subscribe_to_progress_updates(self, operation_id: str, callback: Callable):
        """
        Subscribe to progress updates for a specific operation
        
        Args:
            operation_id: ID of operation to monitor
            callback: Callback function to receive updates
        """
        self.progress_subscribers[operation_id].append(callback)
    
    def subscribe_to_state_updates(self, callback: Callable):
        """
        Subscribe to dashboard state updates
        
        Args:
            callback: Callback function to receive state updates
        """
        self.state_subscribers.append(callback)
    
    def start_real_time_updates(self):
        """Start real-time update thread"""
        if self.enable_real_time_updates and not self._update_thread:
            self._stop_updates.clear()
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()
            self.logger.info("Started real-time updates")
    
    def stop_real_time_updates(self):
        """Stop real-time update thread"""
        if self._update_thread:
            self._stop_updates.set()
            self._update_thread.join(timeout=5.0)
            self._update_thread = None
            self.logger.info("Stopped real-time updates")
    
    def shutdown(self):
        """Shutdown frontend manager and cleanup resources"""
        self.logger.info("Shutting down Modern Frontend Manager")
        
        # Stop updates
        self.stop_real_time_updates()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        # Clear subscribers
        self.progress_subscribers.clear()
        self.state_subscribers.clear()
        
        self.logger.info("Modern Frontend Manager shutdown complete")
    
    # Private helper methods
    
    def _initialize_dashboard(self):
        """Initialize dashboard with initial data"""
        try:
            # Load initial component data
            self._refresh_component_data()
            
            # Start real-time updates if enabled
            if self.enable_real_time_updates:
                self.start_real_time_updates()
            
            self.logger.info("Dashboard initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing dashboard: {e}")
    
    def _create_main_dashboard(self) -> bool:
        """Create main dashboard structure"""
        try:
            # Define dashboard layout structure
            dashboard_layout = {
                "header": {
                    "title": "Environment Dev - Deep Evaluation",
                    "subtitle": "Advanced Development Environment Installer",
                    "status_indicators": ["system_health", "active_operations", "notifications"]
                },
                "sidebar": {
                    "categories": [cat.value for cat in ComponentCategory],
                    "filters": [status.value for status in ComponentStatus],
                    "search": True
                },
                "main_content": {
                    "component_grid": True,
                    "progress_panel": True,
                    "details_panel": True
                },
                "footer": {
                    "system_info": True,
                    "operation_history": True,
                    "help_links": True
                }
            }
            
            # Store dashboard layout
            self.interface_elements["dashboard_layout"] = dashboard_layout
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating main dashboard: {e}")
            return False
    
    def _organize_components_by_category(self) -> bool:
        """Organize components by category"""
        try:
            # Define category mappings
            category_mappings = {
                ComponentCategory.ESSENTIAL_RUNTIMES: [
                    "git", "dotnet", "java", "python", "nodejs", "powershell"
                ],
                ComponentCategory.DEVELOPMENT_TOOLS: [
                    "visual_studio", "vscode", "intellij", "eclipse"
                ],
                ComponentCategory.PACKAGE_MANAGERS: [
                    "npm", "pip", "conda", "yarn", "pipenv"
                ],
                ComponentCategory.RETRO_DEVKITS: [
                    "sgdk", "gbdk", "nesdev", "psxdev"
                ],
                ComponentCategory.UTILITIES: [
                    "7zip", "notepad++", "putty", "wireshark"
                ]
            }
            
            # Store category mappings
            self.interface_elements["category_mappings"] = category_mappings
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error organizing components by category: {e}")
            return False
    
    def _setup_progress_display_system(self) -> bool:
        """Setup progress display system"""
        try:
            # Define progress display configuration
            progress_config = {
                "update_interval": self.update_interval,
                "progress_levels": [level.value for level in ProgressLevel],
                "operation_types": [op.value for op in OperationType],
                "real_time_enabled": self.enable_real_time_updates,
                "max_concurrent_operations": 10,
                "progress_persistence": True
            }
            
            # Store progress configuration
            self.interface_elements["progress_config"] = progress_config
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up progress display system: {e}")
            return False
    
    def _create_interface_elements(self) -> Dict[str, Any]:
        """Create interface elements"""
        return {
            "theme": {
                "primary_color": "#2196F3",
                "secondary_color": "#FFC107",
                "success_color": "#4CAF50",
                "warning_color": "#FF9800",
                "error_color": "#F44336",
                "background_color": "#FAFAFA",
                "text_color": "#212121"
            },
            "icons": {
                "installed": "✓",
                "not_installed": "○",
                "installing": "⟳",
                "failed": "✗",
                "warning": "⚠",
                "info": "ℹ"
            },
            "responsive_breakpoints": {
                "mobile": 768,
                "tablet": 1024,
                "desktop": 1200
            }
        }
    
    def _categorize_components(self, detection_result) -> Dict[str, ComponentInfo]:
        """Categorize detected components"""
        categorized = {}
        
        try:
            # Get category mappings
            category_mappings = self.interface_elements.get("category_mappings", {})
            
            # Process detection results (assuming it has component data)
            if hasattr(detection_result, 'detected_components'):
                for component_name, component_data in detection_result.detected_components.items():
                    # Determine category
                    category = ComponentCategory.CUSTOM
                    for cat, names in category_mappings.items():
                        if any(name in component_name.lower() for name in names):
                            category = cat
                            break
                    
                    # Determine status
                    status = ComponentStatus.INSTALLED if component_data.get('installed', False) else ComponentStatus.NOT_INSTALLED
                    
                    # Create component info
                    component_info = ComponentInfo(
                        name=component_name,
                        display_name=component_data.get('display_name', component_name),
                        category=category,
                        status=status,
                        version=component_data.get('version'),
                        description=component_data.get('description'),
                        priority=component_data.get('priority', 50),
                        size_mb=component_data.get('size_mb'),
                        last_updated=component_data.get('last_updated')
                    )
                    
                    categorized[component_name] = component_info
            
            return categorized
            
        except Exception as e:
            self.logger.error(f"Error categorizing components: {e}")
            return {}
    
    def _create_category_structure(self, components: Dict[str, ComponentInfo]) -> int:
        """Create category structure from components"""
        try:
            categories = defaultdict(list)
            
            for component in components.values():
                categories[component.category].append(component)
            
            # Store category structure
            self.interface_elements["category_structure"] = dict(categories)
            
            return len(categories)
            
        except Exception as e:
            self.logger.error(f"Error creating category structure: {e}")
            return 0
    
    def _apply_status_filters(self) -> bool:
        """Apply status filters to components"""
        try:
            # Define status filter configuration
            status_filters = {
                "show_installed": True,
                "show_not_installed": True,
                "show_outdated": True,
                "show_failed": True,
                "show_installing": True,
                "show_disabled": False
            }
            
            # Store filter configuration
            self.interface_elements["status_filters"] = status_filters
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying status filters: {e}")
            return False
    
    def _create_organization_data(self) -> Dict[str, Any]:
        """Create organization data for components"""
        try:
            with self._lock:
                components = self.dashboard_state.components
            
            # Group by category
            by_category = defaultdict(list)
            for component in components.values():
                by_category[component.category.value].append(component.name)
            
            # Group by status
            by_status = defaultdict(list)
            for component in components.values():
                by_status[component.status.value].append(component.name)
            
            # Calculate statistics
            stats = {
                "total_components": len(components),
                "installed_count": len([c for c in components.values() if c.status == ComponentStatus.INSTALLED]),
                "not_installed_count": len([c for c in components.values() if c.status == ComponentStatus.NOT_INSTALLED]),
                "outdated_count": len([c for c in components.values() if c.status == ComponentStatus.OUTDATED]),
                "failed_count": len([c for c in components.values() if c.status == ComponentStatus.FAILED])
            }
            
            return {
                "by_category": dict(by_category),
                "by_status": dict(by_status),
                "statistics": stats,
                "last_organized": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating organization data: {e}")
            return {}
    
    def _enable_real_time_progress_updates(self, operation_id: str) -> bool:
        """Enable real-time progress updates for operation"""
        try:
            # Configure real-time updates for this operation
            update_config = {
                "operation_id": operation_id,
                "update_interval": self.update_interval,
                "enabled": True,
                "subscribers": len(self.progress_subscribers.get(operation_id, []))
            }
            
            # Store update configuration
            if "real_time_operations" not in self.interface_elements:
                self.interface_elements["real_time_operations"] = {}
            
            self.interface_elements["real_time_operations"][operation_id] = update_config
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling real-time updates for {operation_id}: {e}")
            return False
    
    def _complete_operation(self, operation_id: str):
        """Complete an operation and move to history"""
        try:
            with self._lock:
                if operation_id in self.dashboard_state.active_operations:
                    completed_operation = self.dashboard_state.active_operations.pop(operation_id)
                    completed_operation.is_completed = True
                    
                    # Add to completed operations (with limit)
                    self.dashboard_state.completed_operations.append(completed_operation)
                    if len(self.dashboard_state.completed_operations) > self.max_completed_operations:
                        self.dashboard_state.completed_operations.pop(0)
                    
                    # Clean up real-time configuration
                    if "real_time_operations" in self.interface_elements:
                        self.interface_elements["real_time_operations"].pop(operation_id, None)
                    
                    # Clean up subscribers
                    self.progress_subscribers.pop(operation_id, None)
                    
                    self.logger.info(f"Completed operation: {operation_id}")
            
        except Exception as e:
            self.logger.error(f"Error completing operation {operation_id}: {e}")
    
    def _notify_progress_subscribers(self, operation_id: str, progress: OperationProgress):
        """Notify progress subscribers of updates"""
        try:
            subscribers = self.progress_subscribers.get(operation_id, [])
            for callback in subscribers:
                try:
                    callback(progress)
                except Exception as e:
                    self.logger.warning(f"Error notifying progress subscriber: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying progress subscribers: {e}")
    
    def _notify_state_subscribers(self):
        """Notify state subscribers of dashboard updates"""
        try:
            for callback in self.state_subscribers:
                try:
                    callback(self.dashboard_state)
                except Exception as e:
                    self.logger.warning(f"Error notifying state subscriber: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying state subscribers: {e}")
    
    def _refresh_component_data(self):
        """Refresh component data from detection engine"""
        try:
            # Trigger component organization
            self.organize_components_by_category_and_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing component data: {e}")
    
    def _update_loop(self):
        """Main update loop for real-time updates"""
        while not self._stop_updates.is_set():
            try:
                # Update dashboard state
                self._refresh_component_data()
                
                # Update system status
                self._update_system_status()
                
                # Notify subscribers
                self._notify_state_subscribers()
                
                # Wait for next update
                self._stop_updates.wait(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                self._stop_updates.wait(self.update_interval)
    
    def _update_system_status(self):
        """Update system status information"""
        try:
            with self._lock:
                self.dashboard_state.system_status = {
                    "active_operations": len(self.dashboard_state.active_operations),
                    "completed_operations": len(self.dashboard_state.completed_operations),
                    "total_components": len(self.dashboard_state.components),
                    "installed_components": len([c for c in self.dashboard_state.components.values() 
                                               if c.status == ComponentStatus.INSTALLED]),
                    "failed_components": len([c for c in self.dashboard_state.components.values() 
                                            if c.status == ComponentStatus.FAILED]),
                    "last_updated": datetime.now(),
                    "uptime": datetime.now() - self.dashboard_state.last_updated
                }
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
    
    def _load_frontend_config(self):
        """Load frontend configuration"""
        try:
            config_path = Path("config/frontend.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.update_interval = config.get("update_interval", 1.0)
                self.max_completed_operations = config.get("max_completed_operations", 100)
                self.max_notifications = config.get("max_notifications", 50)
                self.enable_real_time_updates = config.get("enable_real_time_updates", True)
                
                self.logger.info("Loaded frontend configuration")
        except Exception as e:
            self.logger.warning(f"Could not load frontend config: {e}")


# Global instance
modern_frontend_manager = ModernFrontendManager()


if __name__ == "__main__":
    # Test the Modern Frontend Manager
    import time
    
    # Create manager
    manager = ModernFrontendManager()
    
    # Design interface
    design_result = manager.design_unified_interface_with_clear_dashboard()
    print(f"Interface design: {design_result.success}")
    
    # Show progress
    progress_result = manager.show_detailed_real_time_progress(
        "test_installation", 
        OperationType.INSTALLATION,
        "test_component"
    )
    print(f"Progress display: {progress_result.success}")
    
    # Organize components
    org_result = manager.organize_components_by_category_and_status()
    print(f"Component organization: {org_result.success}")
    
    # Simulate progress updates
    operation_id = progress_result.operation_id
    for i in range(0, 101, 10):
        manager.update_progress(
            operation_id, 
            i, 
            f"Step {i//10 + 1}",
            [f"Processing item {i//10 + 1}"]
        )
        time.sleep(0.1)
    
    # Get dashboard state
    state = manager.get_dashboard_state()
    print(f"Dashboard state: {len(state.components)} components, {len(state.active_operations)} active operations")
    
    # Shutdown
    manager.shutdown()