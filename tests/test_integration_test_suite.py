# -*- coding: utf-8 -*-
"""
Tests for Integration Test Suite

This module contains comprehensive tests for the integration test suite,
including end-to-end workflow testing, Steam Deck simulation, and performance validation.
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.integration_test_suite import (
    IntegrationTestSuite,
    IntegrationTestScenario,
    IntegrationTestResult,
    IntegrationTestType,
    IntegrationTestStatus,
    SteamDeckSimulationConfig,
    IntegrationTestSuiteResult
)
from core.security_manager import SecurityManager, SecurityLevel


class TestIntegrationTestSuite(unittest.TestCase):
    """Test cases for IntegrationTestSuite"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "integration_artifacts"
        
        # Create mock security manager
        self.mock_security_manager = Mock(spec=SecurityManager)
        
        # Initialize integration test suite
        self.test_suite = IntegrationTestSuite(
            security_manager=self.mock_security_manager,
            test_artifacts_dir=str(self.artifacts_dir),
            enable_steam_deck_simulation=True,
            enable_performance_testing=True
        )
    
    def tearDown(self):
        """Clean up test environment"""
        self.test_suite.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_integration_test_suite_initialization(self):
        """Test integration test suite initialization"""
        self.assertIsNotNone(self.test_suite)
        self.assertEqual(str(self.test_suite.test_artifacts_dir), str(self.artifacts_dir))
        self.assertTrue(self.test_suite.enable_steam_deck_simulation)
        self.assertTrue(self.test_suite.enable_performance_testing)
        self.assertIsInstance(self.test_suite.test_scenarios, dict)
        self.assertIsInstance(self.test_suite.test_results, dict)
        self.assertIsInstance(self.test_suite.components, dict)
    
    def test_build_comprehensive_integration_test_suite(self):
        """Test building comprehensive integration test suite"""
        # Mock component initialization
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            # Build test suite
            result = self.test_suite.build_comprehensive_integration_test_suite()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertTrue(result.success)
        self.assertGreater(result.total_scenarios, 0)
        self.assertIsInstance(result.component_coverage, dict)
        
        # Verify security audit was called
        self.mock_security_manager.audit_critical_operation.assert_called()
        
        # Verify test scenarios were created
        self.assertGreater(len(self.test_suite.test_scenarios), 0)
    
    def test_end_to_end_workflow_tests(self):
        """Test end-to-end workflow test execution"""
        # Setup test suite
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            self.test_suite.build_comprehensive_integration_test_suite()
        
        # Mock scenario execution
        with patch.object(self.test_suite, '_execute_single_scenario') as mock_execute:
            mock_result = IntegrationTestResult(
                scenario_id="test_scenario",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=5.0
            )
            mock_execute.return_value = mock_result
            
            # Execute end-to-end tests
            result = self.test_suite.execute_end_to_end_workflow_tests()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertGreaterEqual(result.total_scenarios, 0)
    
    def test_steamdeck_simulation_tests(self):
        """Test Steam Deck simulation test execution"""
        # Setup test suite
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            self.test_suite.build_comprehensive_integration_test_suite()
        
        # Mock Steam Deck simulation setup
        with patch.object(self.test_suite, '_activate_steamdeck_simulation', return_value=True):
            with patch.object(self.test_suite, '_deactivate_steamdeck_simulation'):
                with patch.object(self.test_suite, '_execute_single_scenario') as mock_execute:
                    mock_result = IntegrationTestResult(
                        scenario_id="steamdeck_test",
                        status=IntegrationTestStatus.PASSED,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration_seconds=3.0
                    )
                    mock_execute.return_value = mock_result
                    
                    # Execute Steam Deck tests
                    result = self.test_suite.execute_steamdeck_simulation_tests()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertGreaterEqual(result.total_scenarios, 0)
    
    def test_plugin_integration_tests(self):
        """Test plugin integration test execution"""
        # Setup test suite
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            self.test_suite.build_comprehensive_integration_test_suite()
        
        # Mock plugin creation and cleanup
        with patch.object(self.test_suite, '_create_test_plugins', return_value=True):
            with patch.object(self.test_suite, '_cleanup_test_plugins'):
                with patch.object(self.test_suite, '_execute_single_scenario') as mock_execute:
                    mock_result = IntegrationTestResult(
                        scenario_id="plugin_test",
                        status=IntegrationTestStatus.PASSED,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        duration_seconds=4.0
                    )
                    mock_execute.return_value = mock_result
                    
                    # Execute plugin tests
                    result = self.test_suite.execute_plugin_integration_tests()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertGreaterEqual(result.total_scenarios, 0)
    
    def test_performance_integration_tests(self):
        """Test performance integration test execution"""
        # Setup test suite
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            self.test_suite.build_comprehensive_integration_test_suite()
        
        # Mock performance test execution
        with patch.object(self.test_suite, '_execute_performance_test_scenarios') as mock_execute:
            mock_result = IntegrationTestResult(
                scenario_id="performance_test",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=8.0,
                performance_metrics={
                    "execution_time": 8.0,
                    "memory_usage": 150.0,
                    "cpu_usage": 45.0
                }
            )
            mock_execute.return_value = [mock_result]
            
            with patch.object(self.test_suite, '_validate_performance_requirements', return_value={"diagnostic_time_met": True}):
                # Execute performance tests
                result = self.test_suite.execute_performance_integration_tests()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertIsInstance(result.performance_metrics, dict)
    
    def test_full_integration_test_suite_execution(self):
        """Test full integration test suite execution"""
        # Setup test suite
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            self.test_suite.build_comprehensive_integration_test_suite()
        
        # Mock all test type executions
        mock_suite_result = IntegrationTestSuiteResult(
            success=True,
            total_scenarios=5,
            passed_scenarios=4,
            failed_scenarios=1,
            total_duration=25.0
        )
        
        with patch.object(self.test_suite, 'execute_end_to_end_workflow_tests', return_value=mock_suite_result):
            with patch.object(self.test_suite, 'execute_steamdeck_simulation_tests', return_value=mock_suite_result):
                with patch.object(self.test_suite, 'execute_plugin_integration_tests', return_value=mock_suite_result):
                    with patch.object(self.test_suite, 'execute_performance_integration_tests', return_value=mock_suite_result):
                        with patch.object(self.test_suite, '_generate_integration_test_report'):
                            # Execute full test suite
                            result = self.test_suite.execute_full_integration_test_suite()
        
        # Verify result
        self.assertIsInstance(result, IntegrationTestSuiteResult)
        self.assertGreater(result.total_scenarios, 0)
        self.assertGreater(result.total_duration, 0)
    
    def test_sub_15_second_diagnostic_requirement_validation(self):
        """Test validation of sub-15 second diagnostic requirement"""
        # Create mock scenarios
        diagnostic_scenario = IntegrationTestScenario(
            scenario_id="complete_system_diagnostic",
            name="Complete System Diagnostic",
            description="Test diagnostic speed",
            test_type=IntegrationTestType.PERFORMANCE_INTEGRATION,
            components_involved=["architecture_analysis"],
            timeout_seconds=15
        )
        
        self.test_suite.test_scenarios["complete_system_diagnostic"] = diagnostic_scenario
        
        # Mock scenario execution with fast completion
        with patch.object(self.test_suite, '_execute_single_scenario') as mock_execute:
            mock_result = IntegrationTestResult(
                scenario_id="complete_system_diagnostic",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=12.0  # Within 15-second requirement
            )
            mock_execute.return_value = mock_result
            
            # Validate requirement
            requirement_met = self.test_suite.validate_sub_15_second_diagnostic_requirement()
        
        # Verify requirement is met
        self.assertTrue(requirement_met)
    
    def test_sub_15_second_diagnostic_requirement_violation(self):
        """Test detection of sub-15 second diagnostic requirement violation"""
        # Create mock scenarios
        diagnostic_scenario = IntegrationTestScenario(
            scenario_id="complete_system_diagnostic",
            name="Complete System Diagnostic",
            description="Test diagnostic speed",
            test_type=IntegrationTestType.PERFORMANCE_INTEGRATION,
            components_involved=["architecture_analysis"],
            timeout_seconds=15
        )
        
        self.test_suite.test_scenarios["complete_system_diagnostic"] = diagnostic_scenario
        
        # Mock scenario execution with slow completion
        with patch.object(self.test_suite, '_execute_single_scenario') as mock_execute:
            mock_result = IntegrationTestResult(
                scenario_id="complete_system_diagnostic",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=18.0  # Exceeds 15-second requirement
            )
            mock_execute.return_value = mock_result
            
            # Validate requirement
            requirement_met = self.test_suite.validate_sub_15_second_diagnostic_requirement()
        
        # Verify requirement is not met
        self.assertFalse(requirement_met)
    
    def test_steam_deck_simulation_configuration(self):
        """Test Steam Deck simulation configuration"""
        # Verify simulation config
        config = self.test_suite.steamdeck_simulation_config
        self.assertIsInstance(config, SteamDeckSimulationConfig)
        self.assertTrue(config.simulate_hardware)
        self.assertTrue(config.simulate_steam_client)
        self.assertTrue(config.simulate_controller)
        self.assertTrue(config.simulate_touchscreen)
        self.assertTrue(config.simulate_battery_constraints)
    
    def test_component_coverage_calculation(self):
        """Test component coverage calculation"""
        # Setup test suite with mock components
        self.test_suite.components = {
            'component1': Mock(),
            'component2': Mock(),
            'component3': Mock()
        }
        
        # Create test scenarios that cover some components
        scenario1 = IntegrationTestScenario(
            scenario_id="test1",
            name="Test 1",
            description="Test scenario 1",
            test_type=IntegrationTestType.COMPONENT_INTEGRATION,
            components_involved=["component1", "component2"]
        )
        
        scenario2 = IntegrationTestScenario(
            scenario_id="test2",
            name="Test 2",
            description="Test scenario 2",
            test_type=IntegrationTestType.COMPONENT_INTEGRATION,
            components_involved=["component2", "component3"]
        )
        
        self.test_suite.test_scenarios = {
            "test1": scenario1,
            "test2": scenario2
        }
        
        # Calculate coverage
        coverage = self.test_suite._calculate_component_coverage()
        
        # Verify coverage
        self.assertTrue(coverage["component1"])  # Covered by scenario1
        self.assertTrue(coverage["component2"])  # Covered by both scenarios
        self.assertTrue(coverage["component3"])  # Covered by scenario2
    
    def test_scenario_execution_with_error_handling(self):
        """Test scenario execution with error handling"""
        # Create test scenario
        scenario = IntegrationTestScenario(
            scenario_id="error_test",
            name="Error Test",
            description="Test error handling",
            test_type=IntegrationTestType.COMPONENT_INTEGRATION,
            components_involved=["test_component"],
            test_steps=["step1", "step2"],
            expected_outcomes=["outcome1"]
        )
        
        # Mock setup failure
        with patch.object(self.test_suite, '_setup_scenario_environment', return_value=False):
            result = self.test_suite._execute_single_scenario(scenario)
        
        # Verify error handling
        self.assertEqual(result.status, IntegrationTestStatus.ERROR)
        self.assertIsNotNone(result.error_message)
        self.assertIsNotNone(result.duration_seconds)
    
    def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        # Start performance monitoring
        monitor = self.test_suite._start_performance_monitoring()
        
        # Verify monitor structure
        self.assertIn("start_time", monitor)
        self.assertIn("start_memory", monitor)
        self.assertIn("start_cpu", monitor)
        
        # Simulate some work
        time.sleep(0.1)
        
        # Stop monitoring and get metrics
        metrics = self.test_suite._stop_performance_monitoring(monitor)
        
        # Verify metrics
        self.assertIn("execution_time", metrics)
        self.assertIn("memory_usage", metrics)
        self.assertIn("cpu_usage", metrics)
        self.assertIn("disk_io", metrics)
        self.assertIn("network_io", metrics)
        self.assertGreater(metrics["execution_time"], 0.05)  # Should be at least 0.05 seconds
    
    def test_test_plugin_creation_and_cleanup(self):
        """Test test plugin creation and cleanup"""
        # Create test plugins
        success = self.test_suite._create_test_plugins()
        self.assertTrue(success)
        
        # Verify plugin files exist
        plugin_dir = self.test_suite.test_artifacts_dir / "test_plugins"
        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / "test_plugin_manifest.json").exists())
        self.assertTrue((plugin_dir / "test_plugin.py").exists())
        
        # Cleanup test plugins
        self.test_suite._cleanup_test_plugins()
        
        # Verify cleanup
        self.assertFalse(plugin_dir.exists())
    
    def test_scenario_outcome_validation(self):
        """Test scenario outcome validation"""
        # Create test scenario
        scenario = IntegrationTestScenario(
            scenario_id="validation_test",
            name="Validation Test",
            description="Test outcome validation",
            test_type=IntegrationTestType.COMPONENT_INTEGRATION,
            components_involved=["test_component"],
            expected_outcomes=[
                "Operation completes successfully",
                "No errors occur",
                "System remains stable"
            ]
        )
        
        # Validate outcomes
        validation_results = self.test_suite._validate_scenario_outcomes(scenario)
        
        # Verify validation results
        self.assertIsInstance(validation_results, dict)
        self.assertEqual(len(validation_results), 3)
        
        # All outcomes should pass (mocked as successful)
        for outcome, result in validation_results.items():
            self.assertTrue(result)
    
    def test_performance_requirement_validation(self):
        """Test performance requirement validation"""
        # Create performance test results
        results = [
            IntegrationTestResult(
                scenario_id="complete_system_diagnostic",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=12.0,
                performance_metrics={"execution_time": 12.0}
            ),
            IntegrationTestResult(
                scenario_id="runtime_detection_full_scan",
                status=IntegrationTestStatus.PASSED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration_seconds=8.0,
                performance_metrics={"execution_time": 8.0}
            )
        ]
        
        # Validate performance requirements
        validation = self.test_suite._validate_performance_requirements(results)
        
        # Verify validation results
        self.assertIsInstance(validation, dict)
        self.assertTrue(validation.get("diagnostic_time_met", False))
        self.assertTrue(validation.get("detection_time_met", False))
    
    def test_integration_test_report_generation(self):
        """Test integration test report generation"""
        # Create mock suite result
        suite_result = IntegrationTestSuiteResult(
            success=True,
            total_scenarios=5,
            passed_scenarios=4,
            failed_scenarios=1,
            total_duration=30.0,
            performance_metrics={"avg_execution_time": 6.0},
            component_coverage={"component1": True, "component2": False}
        )
        
        # Add mock test results
        self.test_suite.test_results["test1"] = IntegrationTestResult(
            scenario_id="test1",
            status=IntegrationTestStatus.PASSED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=5.0,
            components_tested=["component1"],
            validation_results={"outcome1": True},
            performance_metrics={"execution_time": 5.0}
        )
        
        # Generate report
        self.test_suite._generate_integration_test_report(suite_result)
        
        # Verify report file exists
        report_file = self.test_suite.test_artifacts_dir / "integration_test_report.json"
        self.assertTrue(report_file.exists())
        
        # Verify report content
        with open(report_file, 'r') as f:
            report_data = json.load(f)
        
        self.assertIn("test_suite", report_data)
        self.assertIn("summary", report_data)
        self.assertIn("performance_metrics", report_data)
        self.assertIn("component_coverage", report_data)
        self.assertIn("detailed_results", report_data)
    
    def test_test_suite_shutdown(self):
        """Test test suite shutdown"""
        # Add mock components with shutdown methods
        mock_component = Mock()
        mock_component.shutdown = Mock()
        self.test_suite.components["test_component"] = mock_component
        
        # Shutdown test suite
        self.test_suite.shutdown()
        
        # Verify component shutdown was called
        mock_component.shutdown.assert_called_once()


class TestIntegrationTestScenarios(unittest.TestCase):
    """Test cases for integration test scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_suite = IntegrationTestSuite(
            test_artifacts_dir=str(Path(self.temp_dir) / "artifacts"),
            enable_steam_deck_simulation=True,
            enable_performance_testing=True
        )
    
    def tearDown(self):
        """Clean up test environment"""
        self.test_suite.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_scenario_creation(self):
        """Test creation of end-to-end test scenarios"""
        scenarios = self.test_suite._create_end_to_end_scenarios()
        
        # Verify scenarios were created
        self.assertGreater(len(scenarios), 0)
        
        # Verify scenario structure
        for scenario in scenarios:
            self.assertIsInstance(scenario, IntegrationTestScenario)
            self.assertEqual(scenario.test_type, IntegrationTestType.END_TO_END)
            self.assertGreater(len(scenario.components_involved), 0)
            self.assertGreater(len(scenario.test_steps), 0)
            self.assertGreater(len(scenario.expected_outcomes), 0)
    
    def test_component_integration_scenario_creation(self):
        """Test creation of component integration test scenarios"""
        scenarios = self.test_suite._create_component_integration_scenarios()
        
        # Verify scenarios were created
        self.assertGreater(len(scenarios), 0)
        
        # Verify scenario structure
        for scenario in scenarios:
            self.assertIsInstance(scenario, IntegrationTestScenario)
            self.assertEqual(scenario.test_type, IntegrationTestType.COMPONENT_INTEGRATION)
            self.assertGreaterEqual(len(scenario.components_involved), 2)  # Integration requires multiple components
    
    def test_steamdeck_simulation_scenario_creation(self):
        """Test creation of Steam Deck simulation test scenarios"""
        scenarios = self.test_suite._create_steamdeck_simulation_scenarios()
        
        # Verify scenarios were created
        self.assertGreater(len(scenarios), 0)
        
        # Verify scenario structure
        for scenario in scenarios:
            self.assertIsInstance(scenario, IntegrationTestScenario)
            self.assertEqual(scenario.test_type, IntegrationTestType.STEAM_DECK_SIMULATION)
            self.assertTrue(scenario.steam_deck_specific)
    
    def test_plugin_integration_scenario_creation(self):
        """Test creation of plugin integration test scenarios"""
        scenarios = self.test_suite._create_plugin_integration_scenarios()
        
        # Verify scenarios were created
        self.assertGreater(len(scenarios), 0)
        
        # Verify scenario structure
        for scenario in scenarios:
            self.assertIsInstance(scenario, IntegrationTestScenario)
            self.assertEqual(scenario.test_type, IntegrationTestType.PLUGIN_INTEGRATION)
            self.assertIn("plugin_manager", scenario.components_involved)
    
    def test_performance_integration_scenario_creation(self):
        """Test creation of performance integration test scenarios"""
        scenarios = self.test_suite._create_performance_integration_scenarios()
        
        # Verify scenarios were created
        self.assertGreater(len(scenarios), 0)
        
        # Verify scenario structure
        for scenario in scenarios:
            self.assertIsInstance(scenario, IntegrationTestScenario)
            self.assertEqual(scenario.test_type, IntegrationTestType.PERFORMANCE_INTEGRATION)
            self.assertTrue(scenario.performance_critical)
            
            # Performance scenarios should have strict timeouts
            if "diagnostic" in scenario.scenario_id:
                self.assertLessEqual(scenario.timeout_seconds, 15)
            elif "detection" in scenario.scenario_id:
                self.assertLessEqual(scenario.timeout_seconds, 10)


class TestIntegrationTestPerformance(unittest.TestCase):
    """Performance tests for integration test suite"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_suite = IntegrationTestSuite(
            test_artifacts_dir=str(Path(self.temp_dir) / "artifacts"),
            enable_steam_deck_simulation=False,  # Disable for performance testing
            enable_performance_testing=True
        )
    
    def tearDown(self):
        """Clean up performance test environment"""
        self.test_suite.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_test_suite_build_performance(self):
        """Test test suite building performance"""
        start_time = time.time()
        
        # Mock component initialization for speed
        with patch.object(self.test_suite, '_initialize_component_instances', return_value=True):
            result = self.test_suite.build_comprehensive_integration_test_suite()
        
        end_time = time.time()
        build_time = end_time - start_time
        
        # Should build quickly (under 2 seconds)
        self.assertLess(build_time, 2.0)
        self.assertTrue(result.success)
    
    def test_scenario_execution_performance(self):
        """Test individual scenario execution performance"""
        # Create a simple test scenario
        scenario = IntegrationTestScenario(
            scenario_id="performance_test",
            name="Performance Test",
            description="Test scenario execution performance",
            test_type=IntegrationTestType.COMPONENT_INTEGRATION,
            components_involved=["test_component"],
            test_steps=["step1", "step2", "step3"],
            expected_outcomes=["outcome1", "outcome2"]
        )
        
        # Mock environment setup for speed
        with patch.object(self.test_suite, '_setup_scenario_environment', return_value=True):
            with patch.object(self.test_suite, '_cleanup_scenario_environment', return_value=True):
                start_time = time.time()
                
                result = self.test_suite._execute_single_scenario(scenario)
                
                end_time = time.time()
                execution_time = end_time - start_time
        
        # Should execute quickly (under 1 second for mocked scenario)
        self.assertLess(execution_time, 1.0)
        self.assertEqual(result.status, IntegrationTestStatus.PASSED)
    
    def test_performance_monitoring_overhead(self):
        """Test performance monitoring overhead"""
        # Test without monitoring
        start_time = time.time()
        time.sleep(0.1)  # Simulate work
        end_time = time.time()
        baseline_time = end_time - start_time
        
        # Test with monitoring
        start_time = time.time()
        monitor = self.test_suite._start_performance_monitoring()
        time.sleep(0.1)  # Simulate work
        metrics = self.test_suite._stop_performance_monitoring(monitor)
        end_time = time.time()
        monitored_time = end_time - start_time
        
        # Monitoring overhead should be minimal (less than 10% overhead)
        overhead = (monitored_time - baseline_time) / baseline_time
        self.assertLess(overhead, 0.1)  # Less than 10% overhead
        
        # Verify metrics were collected
        self.assertIn("execution_time", metrics)
        self.assertGreater(metrics["execution_time"], 0.05)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)