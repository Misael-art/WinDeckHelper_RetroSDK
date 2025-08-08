# -*- coding: utf-8 -*-
"""
Tests for Modern Frontend Manager
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the dependencies before importing
with patch.dict('sys.modules', {
    'core.unified_detection_engine': Mock(),
    'core.dependency_validation_system': Mock(),
    'core.advanced_installation_manager': Mock(),
    'core.plugin_system_manager': Mock(),
    'core.security_manager': Mock(),
    'unified_detection_engine': Mock(),
    'dependency_validation_system': Mock(),
    'advanced_installation_manager': Mock(),
    'plugin_system_manager': Mock(),
    'security_manager': Mock()
}):
    from core.modern_frontend_manager import (
        ModernFrontendManager, ComponentCategory, ComponentStatus, OperationType,
        ComponentInfo, OperationProgress, DashboardState, InterfaceDesignResult,
        ProgressDisplayResult, OrganizationResult
    )


class TestModernFrontendManager(unittest.TestCase):
    """Test cases for Modern Frontend Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_detection_engine = Mock()
        self.mock_dependency_validator = Mock()
        self.mock_installation_manager = Mock()
        self.mock_plugin_manager = Mock()
        self.mock_security_manager = Mock()
        
        # Create manager with mocked dependencies
        self.manager = ModernFrontendManager(
            detection_engine=self.mock_detection_engine,
            dependency_validator=self.mock_dependency_validator,
            installation_manager=self.mock_installation_manager,
            plugin_manager=self.mock_plugin_manager,
            security_manager=self.mock_security_manager
        )
        
        # Disable real-time updates for testing
        self.manager.enable_real_time_updates = False
    
    def tearDown(self):
        """Clean up after tests"""
        self.manager.shutdown()
    
    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager.dashboard_state)
        self.assertIsInstance(self.manager.dashboard_state, DashboardState)
        self.assertEqual(len(self.manager.dashboard_state.components), 0)
        self.assertEqual(len(self.manager.dashboard_state.active_operations), 0)
    
    def test_design_unified_interface(self):
        """Test unified interface design"""
        result = self.manager.design_unified_interface_with_clear_dashboard()
        
        self.assertIsInstance(result, InterfaceDesignResult)
        self.assertTrue(result.success)
        self.assertTrue(result.dashboard_created)
        self.assertTrue(result.components_organized)
        self.assertTrue(result.progress_system_ready)
        self.assertIsNotNone(result.interface_elements)
        
        # Check interface elements were created
        self.assertIn("dashboard_layout", self.manager.interface_elements)
        self.assertIn("category_mappings", self.manager.interface_elements)
        self.assertIn("progress_config", self.manager.interface_elements)
    
    def test_show_detailed_real_time_progress(self):
        """Test real-time progress display"""
        operation = "test_installation"
        operation_type = OperationType.INSTALLATION
        component_name = "test_component"
        
        result = self.manager.show_detailed_real_time_progress(
            operation, operation_type, component_name
        )
        
        self.assertIsInstance(result, ProgressDisplayResult)
        self.assertTrue(result.success)
        self.assertTrue(result.display_updated)
        self.assertIsNotNone(result.operation_id)
        self.assertIsNotNone(result.progress_data)
        
        # Check operation was registered
        self.assertIn(result.operation_id, self.manager.dashboard_state.active_operations)
        
        # Check progress data
        progress = result.progress_data
        self.assertEqual(progress.operation_type, operation_type)
        self.assertEqual(progress.component_name, component_name)
        self.assertEqual(progress.progress_percentage, 0.0)
        self.assertFalse(progress.is_completed)
    
    def test_organize_components_by_category_and_status(self):
        """Test component organization"""
        # Mock detection result
        mock_detection_result = Mock()
        mock_detection_result.detected_components = {
            "git": {
                "display_name": "Git",
                "installed": True,
                "version": "2.47.1",
                "description": "Version control system",
                "priority": 90
            },
            "vscode": {
                "display_name": "Visual Studio Code",
                "installed": False,
                "description": "Code editor",
                "priority": 80
            }
        }
        
        self.mock_detection_engine.detect_all_applications.return_value = mock_detection_result
        
        result = self.manager.organize_components_by_category_and_status()
        
        self.assertIsInstance(result, OrganizationResult)
        self.assertTrue(result.success)
        self.assertGreater(result.components_categorized, 0)
        self.assertGreater(result.categories_created, 0)
        self.assertTrue(result.status_filters_applied)
        
        # Check components were added to dashboard
        self.assertGreater(len(self.manager.dashboard_state.components), 0)
        
        # Check specific components
        self.assertIn("git", self.manager.dashboard_state.components)
        self.assertIn("vscode", self.manager.dashboard_state.components)
        
        git_component = self.manager.dashboard_state.components["git"]
        self.assertEqual(git_component.status, ComponentStatus.INSTALLED)
        self.assertEqual(git_component.category, ComponentCategory.ESSENTIAL_RUNTIMES)
        
        vscode_component = self.manager.dashboard_state.components["vscode"]
        self.assertEqual(vscode_component.status, ComponentStatus.NOT_INSTALLED)
        self.assertEqual(vscode_component.category, ComponentCategory.DEVELOPMENT_TOOLS)
    
    def test_update_progress(self):
        """Test progress updates"""
        # Create an operation first
        progress_result = self.manager.show_detailed_real_time_progress(
            "test_operation", OperationType.INSTALLATION
        )
        operation_id = progress_result.operation_id
        
        # Update progress
        self.manager.update_progress(
            operation_id,
            50.0,
            "Installing component",
            ["Downloaded files", "Extracting archive"],
            ["Minor warning"],
            []
        )
        
        # Check progress was updated
        progress = self.manager.dashboard_state.active_operations[operation_id]
        self.assertEqual(progress.progress_percentage, 50.0)
        self.assertEqual(progress.current_step, "Installing component")
        self.assertEqual(len(progress.details), 2)
        self.assertEqual(len(progress.warnings), 1)
        self.assertIsNotNone(progress.estimated_completion)
        
        # Complete the operation
        self.manager.update_progress(operation_id, 100.0, "Completed")
        
        # Check operation was moved to completed
        self.assertNotIn(operation_id, self.manager.dashboard_state.active_operations)
        self.assertEqual(len(self.manager.dashboard_state.completed_operations), 1)
        
        completed_operation = self.manager.dashboard_state.completed_operations[0]
        self.assertTrue(completed_operation.is_completed)
        self.assertEqual(completed_operation.progress_percentage, 100.0)
    
    def test_progress_subscribers(self):
        """Test progress subscription system"""
        # Create operation
        progress_result = self.manager.show_detailed_real_time_progress(
            "test_operation", OperationType.INSTALLATION
        )
        operation_id = progress_result.operation_id
        
        # Create mock subscriber
        subscriber_callback = Mock()
        self.manager.subscribe_to_progress_updates(operation_id, subscriber_callback)
        
        # Update progress
        self.manager.update_progress(operation_id, 25.0, "Step 1")
        
        # Check subscriber was called
        subscriber_callback.assert_called_once()
        
        # Check callback received correct progress data
        called_progress = subscriber_callback.call_args[0][0]
        self.assertEqual(called_progress.progress_percentage, 25.0)
        self.assertEqual(called_progress.current_step, "Step 1")
    
    def test_state_subscribers(self):
        """Test state subscription system"""
        # Create mock subscriber
        state_subscriber = Mock()
        self.manager.subscribe_to_state_updates(state_subscriber)
        
        # Trigger state update
        self.manager._notify_state_subscribers()
        
        # Check subscriber was called
        state_subscriber.assert_called_once()
        
        # Check callback received dashboard state
        called_state = state_subscriber.call_args[0][0]
        self.assertIsInstance(called_state, DashboardState)
    
    def test_dashboard_state_access(self):
        """Test dashboard state access"""
        state = self.manager.get_dashboard_state()
        
        self.assertIsInstance(state, DashboardState)
        self.assertIsInstance(state.components, dict)
        self.assertIsInstance(state.active_operations, dict)
        self.assertIsInstance(state.completed_operations, list)
        self.assertIsInstance(state.system_status, dict)
        self.assertIsInstance(state.notifications, list)
    
    def test_component_categorization(self):
        """Test component categorization logic"""
        # Create mock detection result
        mock_detection_result = Mock()
        mock_detection_result.detected_components = {
            "git": {"display_name": "Git", "installed": True},
            "python": {"display_name": "Python", "installed": True},
            "npm": {"display_name": "NPM", "installed": False},
            "sgdk": {"display_name": "SGDK", "installed": False},
            "unknown_tool": {"display_name": "Unknown Tool", "installed": False}
        }
        
        categorized = self.manager._categorize_components(mock_detection_result)
        
        # Check categorization
        self.assertEqual(categorized["git"].category, ComponentCategory.ESSENTIAL_RUNTIMES)
        self.assertEqual(categorized["python"].category, ComponentCategory.ESSENTIAL_RUNTIMES)
        self.assertEqual(categorized["npm"].category, ComponentCategory.PACKAGE_MANAGERS)
        self.assertEqual(categorized["sgdk"].category, ComponentCategory.RETRO_DEVKITS)
        self.assertEqual(categorized["unknown_tool"].category, ComponentCategory.CUSTOM)
    
    def test_interface_elements_creation(self):
        """Test interface elements creation"""
        elements = self.manager._create_interface_elements()
        
        self.assertIn("theme", elements)
        self.assertIn("icons", elements)
        self.assertIn("responsive_breakpoints", elements)
        
        # Check theme colors
        theme = elements["theme"]
        self.assertIn("primary_color", theme)
        self.assertIn("success_color", theme)
        self.assertIn("error_color", theme)
        
        # Check icons
        icons = elements["icons"]
        self.assertIn("installed", icons)
        self.assertIn("not_installed", icons)
        self.assertIn("failed", icons)
    
    def test_operation_completion(self):
        """Test operation completion handling"""
        # Create operation
        progress_result = self.manager.show_detailed_real_time_progress(
            "test_operation", OperationType.INSTALLATION
        )
        operation_id = progress_result.operation_id
        
        # Verify operation is active
        self.assertIn(operation_id, self.manager.dashboard_state.active_operations)
        
        # Complete operation
        self.manager._complete_operation(operation_id)
        
        # Verify operation moved to completed
        self.assertNotIn(operation_id, self.manager.dashboard_state.active_operations)
        self.assertEqual(len(self.manager.dashboard_state.completed_operations), 1)
        
        completed = self.manager.dashboard_state.completed_operations[0]
        self.assertTrue(completed.is_completed)
        self.assertEqual(completed.operation_id, operation_id)
    
    def test_max_completed_operations_limit(self):
        """Test maximum completed operations limit"""
        # Set low limit for testing
        self.manager.max_completed_operations = 2
        
        # Create and complete multiple operations
        for i in range(5):
            progress_result = self.manager.show_detailed_real_time_progress(
                f"test_operation_{i}", OperationType.INSTALLATION
            )
            self.manager._complete_operation(progress_result.operation_id)
        
        # Check limit is enforced
        self.assertEqual(len(self.manager.dashboard_state.completed_operations), 2)
        
        # Check most recent operations are kept
        completed_ids = [op.operation_id for op in self.manager.dashboard_state.completed_operations]
        self.assertIn("test_operation_3", completed_ids[0])
        self.assertIn("test_operation_4", completed_ids[1])
    
    def test_error_handling_in_progress_update(self):
        """Test error handling in progress updates"""
        # Try to update non-existent operation
        self.manager.update_progress("non_existent_id", 50.0)
        
        # Should not raise exception and should log warning
        # (We can't easily test logging in unit tests without additional setup)
        
        # Dashboard state should remain unchanged
        self.assertEqual(len(self.manager.dashboard_state.active_operations), 0)
    
    def test_real_time_updates_configuration(self):
        """Test real-time updates configuration"""
        operation_id = "test_operation"
        
        result = self.manager._enable_real_time_progress_updates(operation_id)
        self.assertTrue(result)
        
        # Check configuration was stored
        self.assertIn("real_time_operations", self.manager.interface_elements)
        self.assertIn(operation_id, self.manager.interface_elements["real_time_operations"])
        
        config = self.manager.interface_elements["real_time_operations"][operation_id]
        self.assertEqual(config["operation_id"], operation_id)
        self.assertTrue(config["enabled"])


class TestComponentInfo(unittest.TestCase):
    """Test cases for ComponentInfo data class"""
    
    def test_component_info_creation(self):
        """Test ComponentInfo creation"""
        component = ComponentInfo(
            name="test_component",
            display_name="Test Component",
            category=ComponentCategory.DEVELOPMENT_TOOLS,
            status=ComponentStatus.INSTALLED,
            version="1.0.0",
            description="Test component description",
            priority=75
        )
        
        self.assertEqual(component.name, "test_component")
        self.assertEqual(component.display_name, "Test Component")
        self.assertEqual(component.category, ComponentCategory.DEVELOPMENT_TOOLS)
        self.assertEqual(component.status, ComponentStatus.INSTALLED)
        self.assertEqual(component.version, "1.0.0")
        self.assertEqual(component.priority, 75)


class TestOperationProgress(unittest.TestCase):
    """Test cases for OperationProgress data class"""
    
    def test_operation_progress_creation(self):
        """Test OperationProgress creation"""
        progress = OperationProgress(
            operation_id="test_op_123",
            operation_type=OperationType.INSTALLATION,
            component_name="test_component",
            title="Installing Test Component",
            description="Installing test component for development"
        )
        
        self.assertEqual(progress.operation_id, "test_op_123")
        self.assertEqual(progress.operation_type, OperationType.INSTALLATION)
        self.assertEqual(progress.component_name, "test_component")
        self.assertEqual(progress.progress_percentage, 0.0)
        self.assertFalse(progress.is_completed)
        self.assertFalse(progress.is_cancelled)
        self.assertEqual(len(progress.details), 0)
        self.assertEqual(len(progress.warnings), 0)
        self.assertEqual(len(progress.errors), 0)


if __name__ == '__main__':
    unittest.main()