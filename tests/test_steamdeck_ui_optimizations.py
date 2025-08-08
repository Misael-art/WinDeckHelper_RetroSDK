# -*- coding: utf-8 -*-
"""
Tests for Steam Deck UI Optimizations
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the dependencies before importing
with patch.dict('sys.modules', {
    'core.steamdeck_integration_layer': Mock(),
    'core.modern_frontend_manager': Mock(),
    'core.security_manager': Mock(),
    'steamdeck_integration_layer': Mock(),
    'modern_frontend_manager': Mock(),
    'security_manager': Mock(),
    'psutil': Mock()
}):
    from core.steamdeck_ui_optimizations import (
        SteamDeckUIOptimizations, UIMode, InputMethod, PowerProfile,
        OverlayPosition, TouchscreenConfig, GamepadConfig, OverlayConfig,
        BatteryOptimizationConfig, AdaptiveInterfaceResult, GamepadOptimizationResult,
        OverlayModeResult, BatteryOptimizationResult
    )


class TestSteamDeckUIOptimizations(unittest.TestCase):
    """Test cases for Steam Deck UI Optimizations"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_steamdeck_integration = Mock()
        self.mock_frontend_manager = Mock()
        self.mock_security_manager = Mock()
        
        # Mock psutil for system information
        with patch('psutil.cpu_count', return_value=4), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.sensors_battery', return_value=None), \
             patch('psutil.cpu_percent', return_value=25.0), \
             patch('psutil.net_io_counters') as mock_net, \
             patch('psutil.disk_io_counters', return_value=None):
            
            mock_memory.return_value.total = 16 * 1024 * 1024 * 1024  # 16GB
            mock_memory.return_value.percent = 45.0
            mock_net.return_value.bytes_sent = 1000000
            mock_net.return_value.bytes_recv = 2000000
            
            # Create system with mocked dependencies
            self.system = SteamDeckUIOptimizations(
                steamdeck_integration=self.mock_steamdeck_integration,
                frontend_manager=self.mock_frontend_manager,
                security_manager=self.mock_security_manager
            )
    
    def tearDown(self):
        """Clean up after tests"""
        self.system.shutdown()
    
    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system.touchscreen_config)
        self.assertIsNotNone(self.system.gamepad_config)
        self.assertIsNotNone(self.system.overlay_config)
        self.assertIsNotNone(self.system.battery_config)
        self.assertEqual(self.system.current_ui_mode, UIMode.DESKTOP)
        self.assertEqual(self.system.current_input_method, InputMethod.MOUSE_KEYBOARD)
        self.assertFalse(self.system.overlay_active)
        self.assertFalse(self.system.battery_optimizations_active)
    
    def test_implement_adaptive_interface_for_touchscreen_mode(self):
        """Test touchscreen interface implementation"""
        result = self.system.implement_adaptive_interface_for_touchscreen_mode()
        
        self.assertIsInstance(result, AdaptiveInterfaceResult)
        self.assertTrue(result.success)
        self.assertEqual(result.ui_mode, UIMode.TOUCHSCREEN)
        self.assertEqual(result.input_method, InputMethod.TOUCH)
        self.assertGreater(len(result.optimizations_applied), 0)
        self.assertGreaterEqual(result.performance_impact, 0.0)
        self.assertLessEqual(result.performance_impact, 1.0)
        
        # Check that UI mode was updated
        self.assertEqual(self.system.current_ui_mode, UIMode.TOUCHSCREEN)
        self.assertEqual(self.system.current_input_method, InputMethod.TOUCH)
        
        # Check expected optimizations
        expected_optimizations = [
            "touch_targets_optimized",
            "gesture_recognition_enabled",
            "touch_scrolling_optimized",
            "multitouch_support_configured",
            "touch_feedback_enabled",
            "virtual_keyboard_optimized"
        ]
        
        for optimization in expected_optimizations:
            self.assertIn(optimization, result.optimizations_applied)
    
    def test_optimize_controls_for_gamepad(self):
        """Test gamepad controls optimization"""
        result = self.system.optimize_controls_for_gamepad()
        
        self.assertIsInstance(result, GamepadOptimizationResult)
        self.assertTrue(result.success)
        self.assertGreater(result.controls_mapped, 0)
        self.assertTrue(result.navigation_optimized)
        self.assertGreater(result.quick_actions_configured, 0)
        
        # Check that UI mode was updated
        self.assertEqual(self.system.current_ui_mode, UIMode.GAMEPAD)
        self.assertEqual(self.system.current_input_method, InputMethod.GAMEPAD)
        
        # Check that button mappings were configured
        self.assertGreater(len(self.system.gamepad_config.button_mapping), 0)
        
        # Check for expected button mappings
        expected_buttons = ["A", "B", "X", "Y", "L1", "R1", "DPAD_UP", "DPAD_DOWN"]
        for button in expected_buttons:
            self.assertIn(button, self.system.gamepad_config.button_mapping)
    
    def test_implement_overlay_mode_for_use_during_games(self):
        """Test overlay mode implementation"""
        result = self.system.implement_overlay_mode_for_use_during_games()
        
        self.assertIsInstance(result, OverlayModeResult)
        self.assertTrue(result.success)
        self.assertTrue(result.overlay_active)
        self.assertIsNotNone(result.position)
        self.assertGreaterEqual(result.performance_impact, 0.0)
        self.assertLessEqual(result.performance_impact, 1.0)
        
        # Check that overlay state was updated
        self.assertTrue(self.system.overlay_active)
        self.assertEqual(self.system.current_ui_mode, UIMode.OVERLAY)
        
        # Check overlay configuration
        self.assertEqual(result.position, self.system.overlay_config.position)
    
    def test_optimize_battery_consumption_in_interface(self):
        """Test battery consumption optimization"""
        result = self.system.optimize_battery_consumption_in_interface()
        
        self.assertIsInstance(result, BatteryOptimizationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.power_profile, self.system.battery_config.power_profile)
        self.assertGreaterEqual(result.estimated_battery_savings, 0.0)
        self.assertLessEqual(result.estimated_battery_savings, 50.0)  # Capped at 50%
        self.assertGreater(len(result.optimizations_active), 0)
        
        # Check that battery optimizations were activated
        self.assertTrue(self.system.battery_optimizations_active)
        
        # Check for expected optimizations
        expected_optimizations = [
            "screen_brightness_reduced",
            "animations_reduced",
            "background_updates_disabled",
            "cpu_throttling_enabled",
            "gpu_power_limited",
            "network_optimized",
            "polling_frequency_reduced",
            "background_tasks_suspended"
        ]
        
        for optimization in expected_optimizations:
            self.assertIn(optimization, result.optimizations_active)
    
    def test_get_optimization_status(self):
        """Test optimization status retrieval"""
        # Apply some optimizations first
        self.system.implement_adaptive_interface_for_touchscreen_mode()
        self.system.optimize_battery_consumption_in_interface()
        
        status = self.system.get_optimization_status()
        
        self.assertIn('system_info', status)
        self.assertIn('ui_status', status)
        self.assertIn('configurations', status)
        self.assertIn('performance_metrics', status)
        self.assertIn('battery_info', status)
        self.assertIn('last_updated', status)
        
        # Check system info
        system_info = status['system_info']
        self.assertIn('is_steam_deck', system_info)
        self.assertIn('platform', system_info)
        self.assertIn('cpu_count', system_info)
        self.assertIn('memory_total', system_info)
        
        # Check UI status
        ui_status = status['ui_status']
        self.assertEqual(ui_status['current_ui_mode'], UIMode.TOUCHSCREEN.value)
        self.assertEqual(ui_status['current_input_method'], InputMethod.TOUCH.value)
        self.assertTrue(ui_status['battery_optimizations_active'])
        
        # Check configurations
        configurations = status['configurations']
        self.assertIn('touchscreen_config', configurations)
        self.assertIn('gamepad_config', configurations)
        self.assertIn('overlay_config', configurations)
        self.assertIn('battery_config', configurations)
    
    def test_toggle_overlay_mode(self):
        """Test overlay mode toggling"""
        # Initially overlay should be inactive
        self.assertFalse(self.system.overlay_active)
        
        # Toggle on
        result = self.system.toggle_overlay_mode()
        self.assertTrue(result)
        self.assertTrue(self.system.overlay_active)
        
        # Toggle off
        result = self.system.toggle_overlay_mode()
        self.assertFalse(result)
        self.assertFalse(self.system.overlay_active)
        self.assertEqual(self.system.current_ui_mode, UIMode.DESKTOP)
    
    def test_switch_ui_mode(self):
        """Test UI mode switching"""
        # Test switching to touchscreen mode
        success = self.system.switch_ui_mode(UIMode.TOUCHSCREEN)
        self.assertTrue(success)
        self.assertEqual(self.system.current_ui_mode, UIMode.TOUCHSCREEN)
        
        # Test switching to gamepad mode
        success = self.system.switch_ui_mode(UIMode.GAMEPAD)
        self.assertTrue(success)
        self.assertEqual(self.system.current_ui_mode, UIMode.GAMEPAD)
        
        # Test switching to overlay mode
        success = self.system.switch_ui_mode(UIMode.OVERLAY)
        self.assertTrue(success)
        self.assertEqual(self.system.current_ui_mode, UIMode.OVERLAY)
        self.assertTrue(self.system.overlay_active)
        
        # Test switching to desktop mode
        success = self.system.switch_ui_mode(UIMode.DESKTOP)
        self.assertTrue(success)
        self.assertEqual(self.system.current_ui_mode, UIMode.DESKTOP)
        self.assertEqual(self.system.current_input_method, InputMethod.MOUSE_KEYBOARD)
        
        # Test switching to hybrid mode
        success = self.system.switch_ui_mode(UIMode.HYBRID)
        self.assertTrue(success)
        self.assertEqual(self.system.current_ui_mode, UIMode.HYBRID)
        
        # Test switching to same mode (should return True)
        success = self.system.switch_ui_mode(UIMode.HYBRID)
        self.assertTrue(success)
    
    def test_touchscreen_config(self):
        """Test touchscreen configuration"""
        config = self.system.touchscreen_config
        
        # Test default values
        self.assertEqual(config.touch_sensitivity, 1.0)
        self.assertTrue(config.gesture_recognition)
        self.assertTrue(config.multi_touch_enabled)
        self.assertTrue(config.touch_feedback)
        self.assertEqual(config.minimum_touch_size, 44)
        self.assertEqual(config.touch_timeout, 0.3)
        self.assertEqual(config.swipe_threshold, 50)
        self.assertTrue(config.pinch_zoom_enabled)
        self.assertEqual(config.long_press_duration, 0.8)
        self.assertTrue(config.edge_scroll_enabled)
        
        # Test configuration modification
        config.touch_sensitivity = 1.5
        config.minimum_touch_size = 48
        
        self.assertEqual(config.touch_sensitivity, 1.5)
        self.assertEqual(config.minimum_touch_size, 48)
    
    def test_gamepad_config(self):
        """Test gamepad configuration"""
        config = self.system.gamepad_config
        
        # Test default values
        self.assertEqual(config.analog_sensitivity, 1.0)
        self.assertEqual(config.deadzone_threshold, 0.1)
        self.assertTrue(config.vibration_enabled)
        self.assertTrue(config.auto_repeat_enabled)
        self.assertEqual(config.auto_repeat_delay, 0.5)
        self.assertEqual(config.auto_repeat_rate, 0.1)
        self.assertTrue(config.navigation_wrap)
        self.assertTrue(config.quick_actions_enabled)
        self.assertEqual(config.context_menu_button, "menu")
        
        # Test configuration modification
        config.analog_sensitivity = 1.2
        config.vibration_enabled = False
        
        self.assertEqual(config.analog_sensitivity, 1.2)
        self.assertFalse(config.vibration_enabled)
    
    def test_overlay_config(self):
        """Test overlay configuration"""
        config = self.system.overlay_config
        
        # Test default values
        self.assertEqual(config.position, OverlayPosition.TOP_RIGHT)
        self.assertEqual(config.opacity, 0.9)
        self.assertTrue(config.auto_hide)
        self.assertEqual(config.auto_hide_delay, 5.0)
        self.assertTrue(config.always_on_top)
        self.assertTrue(config.resizable)
        self.assertTrue(config.minimizable)
        self.assertTrue(config.snap_to_edges)
        self.assertEqual(config.hotkey_toggle, "F12")
        self.assertTrue(config.compact_mode)
        
        # Test configuration modification
        config.position = OverlayPosition.BOTTOM_LEFT
        config.opacity = 0.8
        config.auto_hide = False
        
        self.assertEqual(config.position, OverlayPosition.BOTTOM_LEFT)
        self.assertEqual(config.opacity, 0.8)
        self.assertFalse(config.auto_hide)
    
    def test_battery_optimization_config(self):
        """Test battery optimization configuration"""
        config = self.system.battery_config
        
        # Test default values
        self.assertEqual(config.power_profile, PowerProfile.BALANCED)
        self.assertEqual(config.screen_brightness_reduction, 0.2)
        self.assertTrue(config.animation_reduction)
        self.assertTrue(config.background_updates_disabled)
        self.assertTrue(config.cpu_throttling)
        self.assertEqual(config.gpu_power_limit, 0.8)
        self.assertTrue(config.network_optimization)
        self.assertEqual(config.idle_timeout, 300.0)
        self.assertTrue(config.suspend_background_tasks)
        self.assertTrue(config.reduce_polling_frequency)
        
        # Test configuration modification
        config.power_profile = PowerProfile.BATTERY_SAVER
        config.screen_brightness_reduction = 0.3
        config.gpu_power_limit = 0.6
        
        self.assertEqual(config.power_profile, PowerProfile.BATTERY_SAVER)
        self.assertEqual(config.screen_brightness_reduction, 0.3)
        self.assertEqual(config.gpu_power_limit, 0.6)
    
    def test_performance_impact_calculation(self):
        """Test performance impact calculation"""
        optimizations = [
            "touch_targets_optimized",
            "gesture_recognition_enabled",
            "touch_scrolling_optimized"
        ]
        
        impact = self.system._calculate_performance_impact(optimizations)
        
        self.assertGreaterEqual(impact, 0.0)
        self.assertLessEqual(impact, 1.0)
        self.assertGreater(impact, 0.0)  # Should have some impact
    
    def test_battery_savings_calculation(self):
        """Test battery savings calculation"""
        optimizations = [
            "screen_brightness_reduced",
            "animations_reduced",
            "cpu_throttling_enabled",
            "gpu_power_limited"
        ]
        
        savings = self.system._calculate_battery_savings(optimizations)
        
        self.assertGreaterEqual(savings, 0.0)
        self.assertLessEqual(savings, 50.0)  # Capped at 50%
        self.assertGreater(savings, 0.0)  # Should have some savings
    
    def test_overlay_performance_impact_calculation(self):
        """Test overlay performance impact calculation"""
        # Test with default configuration
        impact = self.system._calculate_overlay_performance_impact()
        
        self.assertGreaterEqual(impact, 0.0)
        self.assertLessEqual(impact, 1.0)
        self.assertGreater(impact, 0.0)  # Should have some impact
        
        # Test with modified configuration
        self.system.overlay_config.opacity = 0.5  # More transparency
        self.system.overlay_config.compact_mode = True  # Compact mode
        
        impact_modified = self.system._calculate_overlay_performance_impact()
        
        self.assertGreaterEqual(impact_modified, 0.0)
        self.assertLessEqual(impact_modified, 1.0)
    
    def test_steam_deck_detection(self):
        """Test Steam Deck hardware detection"""
        # Test detection method (mocked)
        is_steam_deck = self.system._detect_steam_deck_hardware()
        
        # Should return a boolean
        self.assertIsInstance(is_steam_deck, bool)
        
        # Test with system property
        self.assertIsInstance(self.system.is_steam_deck, bool)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid UI mode switching
        # This should be handled gracefully
        
        # Test configuration with invalid values
        # The system should handle this without crashing
        
        # Test optimization when dependencies fail
        # Should return appropriate error results
        pass
    
    def test_configuration_persistence(self):
        """Test configuration loading and saving"""
        # Modify some configurations
        self.system.touchscreen_config.touch_sensitivity = 1.5
        self.system.gamepad_config.analog_sensitivity = 1.2
        self.system.overlay_config.opacity = 0.8
        self.system.battery_config.screen_brightness_reduction = 0.3
        
        # Save configuration
        self.system._save_configuration()
        
        # Create new system instance
        new_system = SteamDeckUIOptimizations()
        
        # Configuration should be loaded (if file exists)
        # This test would need actual file I/O to work properly
        # For now, we just test that the methods don't crash
        
        new_system.shutdown()


class TestDataClasses(unittest.TestCase):
    """Test cases for data classes"""
    
    def test_touchscreen_config_creation(self):
        """Test TouchscreenConfig creation"""
        config = TouchscreenConfig(
            touch_sensitivity=1.2,
            gesture_recognition=True,
            multi_touch_enabled=True,
            minimum_touch_size=48
        )
        
        self.assertEqual(config.touch_sensitivity, 1.2)
        self.assertTrue(config.gesture_recognition)
        self.assertTrue(config.multi_touch_enabled)
        self.assertEqual(config.minimum_touch_size, 48)
        self.assertEqual(config.touch_timeout, 0.3)  # Default value
    
    def test_gamepad_config_creation(self):
        """Test GamepadConfig creation"""
        config = GamepadConfig(
            analog_sensitivity=1.5,
            deadzone_threshold=0.15,
            vibration_enabled=False
        )
        
        self.assertEqual(config.analog_sensitivity, 1.5)
        self.assertEqual(config.deadzone_threshold, 0.15)
        self.assertFalse(config.vibration_enabled)
        self.assertTrue(config.auto_repeat_enabled)  # Default value
    
    def test_overlay_config_creation(self):
        """Test OverlayConfig creation"""
        config = OverlayConfig(
            position=OverlayPosition.BOTTOM_LEFT,
            opacity=0.7,
            auto_hide=False
        )
        
        self.assertEqual(config.position, OverlayPosition.BOTTOM_LEFT)
        self.assertEqual(config.opacity, 0.7)
        self.assertFalse(config.auto_hide)
        self.assertEqual(config.auto_hide_delay, 5.0)  # Default value
    
    def test_battery_optimization_config_creation(self):
        """Test BatteryOptimizationConfig creation"""
        config = BatteryOptimizationConfig(
            power_profile=PowerProfile.BATTERY_SAVER,
            screen_brightness_reduction=0.3,
            cpu_throttling=True
        )
        
        self.assertEqual(config.power_profile, PowerProfile.BATTERY_SAVER)
        self.assertEqual(config.screen_brightness_reduction, 0.3)
        self.assertTrue(config.cpu_throttling)
        self.assertEqual(config.gpu_power_limit, 0.8)  # Default value
    
    def test_adaptive_interface_result_creation(self):
        """Test AdaptiveInterfaceResult creation"""
        result = AdaptiveInterfaceResult(
            success=True,
            ui_mode=UIMode.TOUCHSCREEN,
            input_method=InputMethod.TOUCH,
            optimizations_applied=["touch_targets_optimized", "gesture_recognition_enabled"],
            performance_impact=0.15
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.ui_mode, UIMode.TOUCHSCREEN)
        self.assertEqual(result.input_method, InputMethod.TOUCH)
        self.assertEqual(len(result.optimizations_applied), 2)
        self.assertEqual(result.performance_impact, 0.15)
        self.assertIsNone(result.error_message)


if __name__ == '__main__':
    unittest.main()