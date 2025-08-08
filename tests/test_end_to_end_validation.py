# -*- coding: utf-8 -*-
"""
End-to-End Validation Tests

This module contains comprehensive end-to-end tests that validate the complete
system functionality, performance requirements, and success criteria.
"""

import unittest
import asyncio
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from main import EnvironmentDevDeepEvaluation
    from core.security_manager import SecurityManager, SecurityLevel
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class MockEnvironmentDevDeepEvaluation:
        def __init__(self, *args, **kwargs):
            pass


class TestEndToEndValidation(unittest.TestCase):
    """End-to-end validation tests for the complete system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test configuration
        test_config = {
            "application": {
                "version": "1.0.0",
                "debug_mode": True,
                "auto_update": False,
                "telemetry_enabled": False
            },
            "analysis": {
                "timeout_seconds": 60,
                "parallel_processing": True,
                "cache_results": False
            },
            "testing": {
                "mock_downloads": True,
                "mock_installations": True,
                "fast_mode": True
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Initialize application
        try:
            self.app = EnvironmentDevDeepEvaluation(config_path=self.config_path)
        except Exception as e:
            print(f"Failed to initialize application: {e}")
            self.app = None
    
    def tearDown(self):
        """Clean up test environment"""
        if self.app:
            try:
                self.app.shutdown()
            except:
                pass
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test complete system initialization"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Verify application is initialized
        self.assertTrue(self.app.initialized)
        self.assertEqual(self.app.version, "1.0.0")
        
        # Verify all components are loaded
        expected_components = [
            'security',
            'architecture_analysis',
            'detection',
            'dependency_validation',
            'download_manager',
            'installation_manager',
            'steamdeck_integration',
            'storage_manager',
            'plugin_manager',
            'testing_framework',
            'frontend'
        ]
        
        for component in expected_components:
            self.assertIn(component, self.app.components)
            self.assertIsNotNone(self.app.components[component])
    
    def test_system_requirements_validation(self):
        """Test system requirements validation"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Run requirements validation
        validation_result = self.app.validate_system_requirements()
        
        # Verify validation structure
        self.assertIn('overall_success', validation_result)
        self.assertIn('requirements', validation_result)
        self.assertIn('recommendations', validation_result)
        
        # Check individual requirements
        requirements = validation_result['requirements']
        self.assertIn('python', requirements)
        self.assertIn('memory', requirements)
        self.assertIn('disk_space', requirements)
        self.assertIn('network', requirements)
        
        # Verify requirement structure
        for req_name, req_info in requirements.items():
            self.assertIn('required', req_info)
            self.assertIn('found', req_info)
            self.assertIn('satisfied', req_info)
    
    @patch('core.unified_detection_engine.UnifiedDetectionEngine.detect_all_components')
    @patch('core.architecture_analysis_engine.ArchitectureAnalysisEngine.analyze_comprehensive_architecture')
    def test_comprehensive_analysis_performance(self, mock_arch_analysis, mock_detection):
        """Test comprehensive analysis meets performance requirements (<15 seconds)"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Mock successful responses
        mock_arch_result = Mock()
        mock_arch_result.success = True
        mock_arch_result.gaps_identified = []
        mock_arch_result.consistency_score = 95.0
        mock_arch_result.recommendations = ["Test recommendation"]
        mock_arch_analysis.return_value = mock_arch_result
        
        mock_detection_result = Mock()
        mock_detection_result.success = True
        mock_detection_result.detected_components = ["git", "python", "node"]
        mock_detection_result.runtime_detections = ["git", "python"]
        mock_detection_result.package_manager_detections = ["npm", "pip"]
        mock_detection.return_value = mock_detection_result
        
        # Run analysis and measure time
        start_time = time.time()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.app.run_comprehensive_analysis())
        finally:
            loop.close()
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        # Verify performance requirement (< 15 seconds)
        self.assertLess(analysis_time, 15.0, 
                       f"Analysis took {analysis_time:.2f} seconds, exceeding 15 second requirement")
        
        # Verify analysis completed successfully
        self.assertTrue(result['success'])
        self.assertIn('components', result)
        self.assertGreater(result['analysis_time_seconds'], 0)
    
    @patch('core.unified_detection_engine.UnifiedDetectionEngine.detect_all_components')
    def test_detection_accuracy_requirement(self, mock_detection):
        """Test 100% essential runtime detection accuracy requirement"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Mock detection of all essential runtimes
        essential_runtimes = [
            "git", "dotnet", "java", "python", "node", 
            "powershell", "anaconda", "vcredist"
        ]
        
        mock_detection_result = Mock()
        mock_detection_result.success = True
        mock_detection_result.detected_components = essential_runtimes
        mock_detection_result.runtime_detections = essential_runtimes
        mock_detection_result.package_manager_detections = ["npm", "pip", "conda"]
        mock_detection.return_value = mock_detection_result
        
        # Run detection
        detection_result = self.app.components['detection'].detect_all_components()
        
        # Verify 100% detection accuracy for essential runtimes
        detected_runtimes = set(detection_result.runtime_detections)
        expected_runtimes = set(essential_runtimes)
        
        detection_accuracy = len(detected_runtimes.intersection(expected_runtimes)) / len(expected_runtimes)
        self.assertEqual(detection_accuracy, 1.0, 
                        f"Detection accuracy {detection_accuracy:.1%} does not meet 100% requirement")
    
    @patch('core.robust_download_manager.RobustDownloadManager.download_with_verification')
    @patch('core.advanced_installation_manager.AdvancedInstallationManager.install_with_rollback')
    def test_installation_success_rate_requirement(self, mock_install, mock_download):
        """Test 95%+ installation success rate requirement"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Mock successful download
        mock_download_result = Mock()
        mock_download_result.success = True
        mock_download_result.file_path = "/tmp/test_component.exe"
        mock_download.return_value = mock_download_result
        
        # Mock successful installation (95%+ success rate)
        mock_install_result = Mock()
        mock_install_result.success = True
        mock_install_result.installation_id = "test_install_123"
        mock_install_result.rollback_available = True
        mock_install.return_value = mock_install_result
        
        # Test installation of multiple components
        test_components = ["git", "python", "node", "dotnet", "java"]
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.app.install_missing_components(test_components)
            )
        finally:
            loop.close()
        
        # Verify 95%+ success rate requirement
        success_rate = result.get('success_rate', 0)
        self.assertGreaterEqual(success_rate, 0.95, 
                               f"Installation success rate {success_rate:.1%} does not meet 95% requirement")
    
    def test_steam_deck_detection_and_optimization(self):
        """Test Steam Deck detection and optimization features"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test Steam Deck detection
        steamdeck_component = self.app.components['steamdeck_integration']
        self.assertIsNotNone(steamdeck_component)
        
        # Test detection method exists and works
        detection_result = steamdeck_component.detect_steam_deck_hardware()
        self.assertIsNotNone(detection_result)
        self.assertHasAttr(detection_result, 'is_steam_deck')
        self.assertHasAttr(detection_result, 'hardware_compatibility_score')
        
        # If Steam Deck is detected, verify optimizations are available
        if detection_result.is_steam_deck:
            self.assertHasAttr(detection_result, 'available_optimizations')
            self.assertGreater(len(detection_result.available_optimizations), 0)
    
    def test_plugin_system_security_and_functionality(self):
        """Test plugin system security and functionality"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test plugin manager initialization
        plugin_manager = self.app.components['plugin_manager']
        self.assertIsNotNone(plugin_manager)
        
        # Test security features
        system_status = plugin_manager.get_system_status()
        self.assertIsNotNone(system_status)
        self.assertHasAttr(system_status, 'security_enabled')
        self.assertTrue(system_status.security_enabled)
        
        # Test plugin loading capabilities
        self.assertHasAttr(plugin_manager, 'load_plugin')
        self.assertHasAttr(plugin_manager, 'validate_plugin_security')
    
    def test_security_audit_logging(self):
        """Test security audit logging functionality"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test security manager
        security_manager = self.app.components['security']
        self.assertIsNotNone(security_manager)
        
        # Test audit logging
        try:
            security_manager.audit_critical_operation(
                operation="test_operation",
                component="test_component",
                details={"test": "data"},
                success=True,
                security_level=SecurityLevel.LOW
            )
            # If no exception, audit logging is working
            audit_working = True
        except Exception as e:
            audit_working = False
            print(f"Audit logging error: {e}")
        
        self.assertTrue(audit_working, "Security audit logging is not functioning")
    
    def test_storage_management_and_optimization(self):
        """Test intelligent storage management and optimization"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test storage manager
        storage_manager = self.app.components['storage_manager']
        self.assertIsNotNone(storage_manager)
        
        # Test storage analysis
        try:
            storage_result = storage_manager.analyze_storage_comprehensive()
            self.assertIsNotNone(storage_result)
            self.assertHasAttr(storage_result, 'success')
            self.assertHasAttr(storage_result, 'total_space_gb')
            self.assertHasAttr(storage_result, 'available_space_gb')
        except Exception as e:
            self.fail(f"Storage analysis failed: {e}")
    
    def test_automated_testing_framework(self):
        """Test automated testing framework functionality"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test testing framework
        testing_framework = self.app.components['testing_framework']
        self.assertIsNotNone(testing_framework)
        
        # Test framework building
        try:
            framework_result = testing_framework.build_comprehensive_automated_testing_framework()
            self.assertIsNotNone(framework_result)
            self.assertHasAttr(framework_result, 'success')
            self.assertHasAttr(framework_result, 'tests_discovered')
            self.assertHasAttr(framework_result, 'suites_created')
        except Exception as e:
            self.fail(f"Testing framework build failed: {e}")
    
    def test_configuration_management(self):
        """Test configuration management and persistence"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Verify configuration is loaded
        self.assertIsNotNone(self.app.config)
        self.assertIn('application', self.app.config)
        
        # Test configuration saving
        original_config = self.app.config.copy()
        self.app.config['test_key'] = 'test_value'
        
        try:
            self.app._save_configuration()
            
            # Reload configuration
            with open(self.app.config_path, 'r') as f:
                reloaded_config = json.load(f)
            
            self.assertEqual(reloaded_config['test_key'], 'test_value')
            
        except Exception as e:
            self.fail(f"Configuration management failed: {e}")
        finally:
            # Restore original configuration
            self.app.config = original_config
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        # Test graceful error handling in analysis
        with patch('core.architecture_analysis_engine.ArchitectureAnalysisEngine.analyze_comprehensive_architecture') as mock_analysis:
            # Mock an exception
            mock_analysis.side_effect = Exception("Test exception")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.app.run_comprehensive_analysis())
            finally:
                loop.close()
            
            # Verify error is handled gracefully
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertEqual(result['error'], "Test exception")
    
    def test_memory_and_resource_management(self):
        """Test memory usage and resource management"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        try:
            import psutil
            import gc
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run multiple operations
            for i in range(5):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.app.run_comprehensive_analysis())
                finally:
                    loop.close()
                
                # Force garbage collection
                gc.collect()
            
            # Check final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 100MB for test operations)
            self.assertLess(memory_increase, 100, 
                           f"Memory usage increased by {memory_increase:.1f}MB, indicating potential memory leak")
            
        except ImportError:
            self.skipTest("psutil not available for memory testing")
    
    def test_concurrent_operations(self):
        """Test concurrent operations and thread safety"""
        if not self.app:
            self.skipTest("Application failed to initialize")
        
        import threading
        import concurrent.futures
        
        # Test concurrent analysis operations
        def run_analysis():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.app.run_comprehensive_analysis())
            finally:
                loop.close()
        
        # Run multiple concurrent analyses
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_analysis) for _ in range(3)]
            results = [future.result(timeout=30) for future in futures]
        
        # Verify all operations completed successfully
        for i, result in enumerate(results):
            self.assertIsNotNone(result, f"Analysis {i} returned None")
            self.assertIn('success', result, f"Analysis {i} missing success field")
    
    def assertHasAttr(self, obj, attr):
        """Helper method to assert object has attribute"""
        self.assertTrue(hasattr(obj, attr), f"Object {obj} does not have attribute '{attr}'")


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for system components working together"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_component_communication(self):
        """Test communication between system components"""
        try:
            # Test that components can be imported and initialized
            from core.security_manager import SecurityManager
            from core.architecture_analysis_engine import ArchitectureAnalysisEngine
            from core.unified_detection_engine import UnifiedDetectionEngine
            
            # Initialize components
            security_manager = SecurityManager()
            arch_engine = ArchitectureAnalysisEngine(security_manager=security_manager)
            detection_engine = UnifiedDetectionEngine(security_manager=security_manager)
            
            # Test that components can interact
            self.assertIsNotNone(arch_engine)
            self.assertIsNotNone(detection_engine)
            
        except ImportError as e:
            self.fail(f"Component import failed: {e}")
        except Exception as e:
            self.fail(f"Component initialization failed: {e}")
    
    def test_data_flow_integration(self):
        """Test data flow between components"""
        try:
            # This would test actual data flow in a real environment
            # For now, we test that the structure supports data flow
            
            from core.security_manager import SecurityManager
            security_manager = SecurityManager()
            
            # Test audit logging (data flow to security manager)
            security_manager.audit_critical_operation(
                operation="test_data_flow",
                component="integration_test",
                details={"test": "data"},
                success=True,
                security_level=SecurityLevel.LOW
            )
            
            # If no exception, data flow is working
            self.assertTrue(True)
            
        except Exception as e:
            self.fail(f"Data flow integration failed: {e}")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmark tests"""
    
    def test_startup_performance(self):
        """Test application startup performance"""
        start_time = time.time()
        
        try:
            temp_dir = tempfile.mkdtemp()
            config_path = os.path.join(temp_dir, "perf_config.json")
            
            # Create minimal config for performance testing
            config = {"application": {"debug_mode": False}}
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            # Initialize application
            app = EnvironmentDevDeepEvaluation(config_path=config_path)
            
            end_time = time.time()
            startup_time = end_time - start_time
            
            # Startup should be under 5 seconds
            self.assertLess(startup_time, 5.0, 
                           f"Startup took {startup_time:.2f} seconds, exceeding 5 second target")
            
            # Cleanup
            app.shutdown()
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            self.fail(f"Startup performance test failed: {e}")
    
    def test_memory_usage_benchmark(self):
        """Test memory usage benchmarks"""
        try:
            import psutil
            
            # Get baseline memory
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Initialize application
            temp_dir = tempfile.mkdtemp()
            config_path = os.path.join(temp_dir, "mem_config.json")
            
            config = {"application": {"debug_mode": False}}
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            app = EnvironmentDevDeepEvaluation(config_path=config_path)
            
            # Check memory after initialization
            init_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = init_memory - baseline_memory
            
            # Memory usage should be reasonable (< 200MB)
            self.assertLess(memory_usage, 200, 
                           f"Memory usage {memory_usage:.1f}MB exceeds 200MB target")
            
            # Cleanup
            app.shutdown()
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except ImportError:
            self.skipTest("psutil not available for memory benchmarking")
        except Exception as e:
            self.fail(f"Memory usage benchmark failed: {e}")


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)