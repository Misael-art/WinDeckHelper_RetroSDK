# -*- coding: utf-8 -*-
"""
Tests for Automated Testing Framework

This module contains comprehensive tests for the automated testing framework,
including unit tests, integration tests, and performance validation.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from core.automated_testing_framework import (
        AutomatedTestingFramework, TestCase, TestSuite, TestExecution,
        TestResult, TestType, TestStatus, TestPriority, TestFrameworkResult
    )
    from core.security_manager import SecurityManager, SecurityLevel
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class MockSecurityManager:
        def audit_critical_operation(self, **kwargs):
            pass
    
    class MockSecurityLevel:
        LOW = "low"


class TestAutomatedTestingFramework(unittest.TestCase):
    """Test cases for AutomatedTestingFramework"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = Path(self.temp_dir) / "tests"
        self.reports_dir = Path(self.temp_dir) / "reports"
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        
        # Create test directories
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock security manager
        self.mock_security_manager = Mock()
        
        # Initialize framework
        self.framework = AutomatedTestingFramework(
            security_manager=self.mock_security_manager,
            test_directory=str(self.test_dir),
            reports_directory=str(self.reports_dir),
            artifacts_directory=str(self.artifacts_dir)
        )
    
    def tearDown(self):
        """Clean up test environment"""
        self.framework.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_framework_initialization(self):
        """Test framework initialization"""
        self.assertIsNotNone(self.framework)
        self.assertEqual(str(self.framework.test_directory), str(self.test_dir))
        self.assertEqual(str(self.framework.reports_directory), str(self.reports_dir))
        self.assertEqual(str(self.framework.artifacts_directory), str(self.artifacts_dir))
        self.assertFalse(self.framework.framework_initialized)
        self.assertFalse(self.framework.continuous_testing_enabled)
        self.assertTrue(self.framework.coverage_enabled)
    
    def test_build_comprehensive_framework(self):
        """Test building comprehensive testing framework"""
        # Create sample test files
        self._create_sample_test_files()
        
        # Build framework
        result = self.framework.build_comprehensive_automated_testing_framework()
        
        # Verify result
        self.assertIsInstance(result, TestFrameworkResult)
        self.assertTrue(result.success)
        self.assertTrue(result.framework_initialized)
        self.assertGreater(result.tests_discovered, 0)
        self.assertGreater(result.suites_created, 0)
        self.assertIsInstance(result.configuration, dict)
        
        # Verify framework state
        self.assertTrue(self.framework.framework_initialized)
        self.assertGreater(len(self.framework.test_cases), 0)
        self.assertGreater(len(self.framework.test_suites), 0)
    
    def test_test_case_management(self):
        """Test adding and removing test cases"""
        # Create test case
        test_case = TestCase(
            test_id="test_example",
            name="test_example_function",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH,
            module_path="test_module.py",
            function_name="test_example_function",
            description="Example test case"
        )
        
        # Add test case
        result = self.framework.add_test_case(test_case)
        self.assertTrue(result)
        self.assertIn("test_example", self.framework.test_cases)
        
        # Try to add duplicate
        duplicate_result = self.framework.add_test_case(test_case)
        self.assertFalse(duplicate_result)
        
        # Remove test case
        remove_result = self.framework.remove_test_case("test_example")
        self.assertTrue(remove_result)
        self.assertNotIn("test_example", self.framework.test_cases)
        
        # Try to remove non-existent
        non_existent_result = self.framework.remove_test_case("non_existent")
        self.assertFalse(non_existent_result)
    
    def test_test_discovery(self):
        """Test test file discovery"""
        # Create sample test files
        self._create_sample_test_files()
        
        # Discover tests
        tests_discovered = self.framework._discover_test_files()
        
        # Verify discovery
        self.assertGreater(tests_discovered, 0)
        self.assertGreater(len(self.framework.test_cases), 0)
        
        # Check test case properties
        for test_case in self.framework.test_cases.values():
            self.assertIsInstance(test_case, TestCase)
            self.assertIn(test_case.test_type, TestType)
            self.assertIn(test_case.priority, TestPriority)
    
    def test_test_type_determination(self):
        """Test test type determination logic"""
        # Test unit test detection
        unit_type = self.framework._determine_test_type(
            Path("test_unit_example.py"), "test_basic_function"
        )
        self.assertEqual(unit_type, TestType.UNIT)
        
        # Test integration test detection
        integration_type = self.framework._determine_test_type(
            Path("test_integration_example.py"), "test_integration_flow"
        )
        self.assertEqual(integration_type, TestType.INTEGRATION)
        
        # Test performance test detection
        performance_type = self.framework._determine_test_type(
            Path("test_performance_example.py"), "test_performance_benchmark"
        )
        self.assertEqual(performance_type, TestType.PERFORMANCE)
    
    def test_test_suite_creation(self):
        """Test test suite creation"""
        # Add sample test cases
        self._add_sample_test_cases()
        
        # Create test suites
        suites_created = self.framework._create_test_suites()
        
        # Verify suite creation
        self.assertGreater(suites_created, 0)
        self.assertGreater(len(self.framework.test_suites), 0)
        
        # Check suite properties
        for suite in self.framework.test_suites.values():
            self.assertIsInstance(suite, TestSuite)
            self.assertGreater(len(suite.test_cases), 0)
    
    @patch('pytest.main')
    def test_unit_test_execution(self, mock_pytest):
        """Test unit test execution"""
        # Mock pytest to return success
        mock_pytest.return_value = 0
        
        # Add sample test cases
        self._add_sample_test_cases()
        
        # Execute unit tests
        execution = self.framework.execute_unit_tests()
        
        # Verify execution
        self.assertIsInstance(execution, TestExecution)
        self.assertIn(execution.status, [TestStatus.PASSED, TestStatus.FAILED, TestStatus.SKIPPED])
        self.assertIsNotNone(execution.start_time)
        self.assertIsNotNone(execution.end_time)
    
    @patch('pytest.main')
    def test_integration_test_execution(self, mock_pytest):
        """Test integration test execution"""
        # Mock pytest to return success
        mock_pytest.return_value = 0
        
        # Add sample test cases
        self._add_sample_test_cases()
        
        # Execute integration tests
        execution = self.framework.execute_integration_tests()
        
        # Verify execution
        self.assertIsInstance(execution, TestExecution)
        self.assertIn(execution.status, [TestStatus.PASSED, TestStatus.FAILED, TestStatus.SKIPPED])
    
    @patch('pytest.main')
    def test_performance_test_execution(self, mock_pytest):
        """Test performance test execution"""
        # Mock pytest to return success
        mock_pytest.return_value = 0
        
        # Add sample test cases
        self._add_sample_test_cases()
        
        # Execute performance tests
        execution = self.framework.execute_performance_tests()
        
        # Verify execution
        self.assertIsInstance(execution, TestExecution)
        self.assertIn(execution.status, [TestStatus.PASSED, TestStatus.FAILED, TestStatus.SKIPPED])
    
    @patch('pytest.main')
    def test_full_test_suite_execution(self, mock_pytest):
        """Test full test suite execution"""
        # Mock pytest to return success
        mock_pytest.return_value = 0
        
        # Add sample test cases
        self._add_sample_test_cases()
        
        # Execute full test suite
        execution = self.framework.run_full_test_suite()
        
        # Verify execution
        self.assertIsInstance(execution, TestExecution)
        self.assertEqual(execution.suite_id, "full_suite")
        self.assertIn(execution.status, [TestStatus.PASSED, TestStatus.FAILED])
        self.assertGreaterEqual(execution.total_tests, 0)
    
    def test_continuous_testing_enablement(self):
        """Test continuous testing enablement"""
        # Enable continuous testing
        result = self.framework.enable_continuous_testing(
            watch_directories=["core", "tests"],
            trigger_on_change=True
        )
        
        # Verify enablement
        self.assertTrue(result)
        self.assertTrue(self.framework.continuous_testing_enabled)
    
    def test_coverage_report_generation(self):
        """Test coverage report generation"""
        # Create mock execution
        execution = TestExecution(
            execution_id="test_execution",
            suite_id="test_suite",
            start_time=datetime.now(),
            end_time=datetime.now(),
            coverage_percentage=85.5
        )
        
        # Store execution
        self.framework.test_executions["test_execution"] = execution
        
        # Generate coverage report
        report_path = self.framework.generate_coverage_report("test_execution", "html")
        
        # Verify report generation
        self.assertIsInstance(report_path, str)
        if report_path:  # If report was generated
            self.assertTrue(Path(report_path).exists())
    
    def test_test_metrics_calculation(self):
        """Test test metrics calculation"""
        # Create sample executions
        executions = []
        for i in range(3):
            execution = TestExecution(
                execution_id=f"execution_{i}",
                suite_id=f"suite_{i}",
                start_time=datetime.now() - timedelta(days=i),
                end_time=datetime.now() - timedelta(days=i),
                total_tests=10,
                passed_tests=8,
                failed_tests=2,
                coverage_percentage=80.0 + i
            )
            executions.append(execution)
            self.framework.test_executions[execution.execution_id] = execution
        
        # Get metrics
        metrics = self.framework.get_test_metrics(timedelta(days=7))
        
        # Verify metrics
        self.assertIsInstance(metrics, dict)
        if metrics:  # If metrics were calculated
            self.assertIn('total_executions', metrics)
            self.assertIn('success_rate', metrics)
            self.assertIn('average_coverage', metrics)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid test directory
        with patch.object(Path, 'mkdir', side_effect=PermissionError("Access denied")):
            framework = AutomatedTestingFramework(
                test_directory="/invalid/path",
                reports_directory=str(self.reports_dir),
                artifacts_directory=str(self.artifacts_dir)
            )
            # Should handle error gracefully
            self.assertIsNotNone(framework)
        
        # Test execution with no tests
        execution = self.framework.execute_unit_tests()
        self.assertEqual(execution.status, TestStatus.SKIPPED)
        self.assertEqual(execution.total_tests, 0)
    
    def test_framework_configuration(self):
        """Test framework configuration retrieval"""
        config = self.framework._get_framework_configuration()
        
        # Verify configuration
        self.assertIsInstance(config, dict)
        self.assertIn('test_directory', config)
        self.assertIn('reports_directory', config)
        self.assertIn('artifacts_directory', config)
        self.assertIn('coverage_enabled', config)
        self.assertIn('parallel_execution', config)
        self.assertIn('total_test_cases', config)
        self.assertIn('total_test_suites', config)
    
    def test_framework_shutdown(self):
        """Test framework shutdown"""
        # Enable continuous testing first
        self.framework.enable_continuous_testing()
        
        # Shutdown framework
        self.framework.shutdown()
        
        # Verify shutdown
        self.assertFalse(self.framework.continuous_testing_enabled)
    
    # Helper methods
    
    def _create_sample_test_files(self):
        """Create sample test files for testing"""
        # Unit test file
        unit_test_content = '''
def test_basic_function():
    assert True

def test_another_function():
    assert 1 + 1 == 2
'''
        unit_test_file = self.test_dir / "test_unit_example.py"
        with open(unit_test_file, 'w') as f:
            f.write(unit_test_content)
        
        # Integration test file
        integration_test_content = '''
def test_integration_flow():
    # Integration test
    assert True

def test_integration_database():
    # Database integration test
    assert True
'''
        integration_test_file = self.test_dir / "test_integration_example.py"
        with open(integration_test_file, 'w') as f:
            f.write(integration_test_content)
        
        # Performance test file
        performance_test_content = '''
def test_performance_benchmark():
    # Performance test
    import time
    start = time.time()
    # Simulate work
    time.sleep(0.001)
    end = time.time()
    assert (end - start) < 1.0
'''
        performance_test_file = self.test_dir / "test_performance_example.py"
        with open(performance_test_file, 'w') as f:
            f.write(performance_test_content)
    
    def _add_sample_test_cases(self):
        """Add sample test cases to framework"""
        test_cases = [
            TestCase(
                test_id="unit_test_1",
                name="test_basic_function",
                test_type=TestType.UNIT,
                priority=TestPriority.HIGH,
                module_path="test_unit_example.py",
                function_name="test_basic_function"
            ),
            TestCase(
                test_id="integration_test_1",
                name="test_integration_flow",
                test_type=TestType.INTEGRATION,
                priority=TestPriority.MEDIUM,
                module_path="test_integration_example.py",
                function_name="test_integration_flow"
            ),
            TestCase(
                test_id="performance_test_1",
                name="test_performance_benchmark",
                test_type=TestType.PERFORMANCE,
                priority=TestPriority.LOW,
                module_path="test_performance_example.py",
                function_name="test_performance_benchmark"
            )
        ]
        
        for test_case in test_cases:
            self.framework.add_test_case(test_case)


class TestTestFrameworkIntegration(unittest.TestCase):
    """Integration tests for the testing framework"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.framework = AutomatedTestingFramework(
            test_directory=str(Path(self.temp_dir) / "tests"),
            reports_directory=str(Path(self.temp_dir) / "reports"),
            artifacts_directory=str(Path(self.temp_dir) / "artifacts")
        )
    
    def tearDown(self):
        """Clean up integration test environment"""
        self.framework.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_testing_workflow(self):
        """Test complete end-to-end testing workflow"""
        # Build framework
        build_result = self.framework.build_comprehensive_automated_testing_framework()
        
        # Should succeed even with no tests
        self.assertTrue(build_result.success)
        
        # Enable continuous testing
        continuous_result = self.framework.enable_continuous_testing()
        self.assertTrue(continuous_result)
        
        # Get metrics
        metrics = self.framework.get_test_metrics()
        self.assertIsInstance(metrics, dict)
        
        # Generate configuration
        config = self.framework._get_framework_configuration()
        self.assertIsInstance(config, dict)


class TestTestFrameworkPerformance(unittest.TestCase):
    """Performance tests for the testing framework"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.framework = AutomatedTestingFramework(
            test_directory=str(Path(self.temp_dir) / "tests"),
            reports_directory=str(Path(self.temp_dir) / "reports"),
            artifacts_directory=str(Path(self.temp_dir) / "artifacts")
        )
    
    def tearDown(self):
        """Clean up performance test environment"""
        self.framework.shutdown()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_framework_initialization_performance(self):
        """Test framework initialization performance"""
        start_time = datetime.now()
        
        # Initialize new framework
        framework = AutomatedTestingFramework(
            test_directory=str(Path(self.temp_dir) / "tests2"),
            reports_directory=str(Path(self.temp_dir) / "reports2"),
            artifacts_directory=str(Path(self.temp_dir) / "artifacts2")
        )
        
        end_time = datetime.now()
        initialization_time = (end_time - start_time).total_seconds()
        
        # Should initialize quickly (under 1 second)
        self.assertLess(initialization_time, 1.0)
        
        framework.shutdown()
    
    def test_large_test_suite_handling(self):
        """Test handling of large test suites"""
        # Add many test cases
        start_time = datetime.now()
        
        for i in range(100):
            test_case = TestCase(
                test_id=f"test_{i}",
                name=f"test_function_{i}",
                test_type=TestType.UNIT,
                priority=TestPriority.MEDIUM,
                module_path=f"test_module_{i}.py",
                function_name=f"test_function_{i}"
            )
            self.framework.add_test_case(test_case)
        
        end_time = datetime.now()
        addition_time = (end_time - start_time).total_seconds()
        
        # Should handle large number of test cases efficiently
        self.assertLess(addition_time, 5.0)
        self.assertEqual(len(self.framework.test_cases), 100)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)