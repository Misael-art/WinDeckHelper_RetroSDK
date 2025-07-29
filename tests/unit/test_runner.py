#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Runner for Environment Dev Unit Tests
Runs all unit tests for all managers and components
"""

import unittest
import sys
import os
from pathlib import Path
import time
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all test modules
try:
    from tests.unit.test_diagnostic_manager_enhanced import TestDiagnosticManager
    from tests.unit.test_installation_manager import TestInstallationManager, TestInstallationManagerIntegration
    from tests.unit.test_preparation_manager import TestPreparationManager, TestPreparationManagerIntegration
    from tests.unit.test_recovery_manager import TestRecoveryManager, TestRecoveryManagerIntegration
    from tests.unit.test_advanced_logging import TestAdvancedLogger, TestAdvancedLoggingIntegration
    
    # Import existing enhanced tests
    from test_download_manager import TestDownloadManager
    from test_notification_manager import TestNotificationManager, TestNotificationManagerIntegration
    from test_organization_manager import TestOrganizationManager, TestOrganizationManagerIntegration
    
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Warning: Some test modules could not be imported: {e}")
    IMPORTS_SUCCESSFUL = False


class TestResult:
    """Custom test result class for detailed reporting"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self.successes = []
        self.start_time = None
        self.end_time = None
    
    def start_test(self, test):
        """Called when a test starts"""
        self.start_time = time.time()
    
    def add_success(self, test):
        """Called when a test passes"""
        self.tests_run += 1
        self.successes.append(test)
    
    def add_failure(self, test, err):
        """Called when a test fails"""
        self.tests_run += 1
        self.failures.append((test, err))
    
    def add_error(self, test, err):
        """Called when a test has an error"""
        self.tests_run += 1
        self.errors.append((test, err))
    
    def add_skip(self, test, reason):
        """Called when a test is skipped"""
        self.tests_run += 1
        self.skipped.append((test, reason))
    
    def stop_test(self, test):
        """Called when a test ends"""
        self.end_time = time.time()
    
    @property
    def duration(self):
        """Get test duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def success_rate(self):
        """Calculate success rate"""
        if self.tests_run == 0:
            return 0
        return (len(self.successes) / self.tests_run) * 100


class ComprehensiveTestRunner:
    """Comprehensive test runner for all Environment Dev components"""
    
    def __init__(self):
        self.results = {}
        self.total_start_time = None
        self.total_end_time = None
    
    def run_all_tests(self, verbosity=2):
        """Run all unit tests for all components"""
        print("=" * 80)
        print("ENVIRONMENT DEV - COMPREHENSIVE UNIT TEST SUITE")
        print("=" * 80)
        print()
        
        self.total_start_time = time.time()
        
        # Define test suites
        test_suites = [
            ("DiagnosticManager", self._get_diagnostic_tests),
            ("DownloadManager", self._get_download_tests),
            ("InstallationManager", self._get_installation_tests),
            ("PreparationManager", self._get_preparation_tests),
            ("RecoveryManager", self._get_recovery_tests),
            ("NotificationManager", self._get_notification_tests),
            ("OrganizationManager", self._get_organization_tests),
            ("AdvancedLogging", self._get_logging_tests)
        ]
        
        # Run each test suite
        for suite_name, get_tests_func in test_suites:
            print(f"\n{'=' * 60}")
            print(f"TESTING: {suite_name}")
            print(f"{'=' * 60}")
            
            try:
                suite = get_tests_func()
                if suite:
                    result = self._run_test_suite(suite, verbosity)
                    self.results[suite_name] = result
                    self._print_suite_summary(suite_name, result)
                else:
                    print(f"⚠️  No tests found for {suite_name}")
                    
            except Exception as e:
                print(f"❌ Error running {suite_name} tests: {e}")
                import traceback
                traceback.print_exc()
        
        self.total_end_time = time.time()
        
        # Print comprehensive summary
        self._print_comprehensive_summary()
        
        return self._get_overall_success()
    
    def _get_diagnostic_tests(self):
        """Get diagnostic manager tests"""
        if not IMPORTS_SUCCESSFUL:
            return None
        
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestDiagnosticManager))
            return suite
        except NameError:
            print("⚠️  DiagnosticManager tests not available")
            return None
    
    def _get_download_tests(self):
        """Get download manager tests"""
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestDownloadManager))
            return suite
        except NameError:
            print("⚠️  DownloadManager tests not available")
            return None
    
    def _get_installation_tests(self):
        """Get installation manager tests"""
        if not IMPORTS_SUCCESSFUL:
            return None
        
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestInstallationManager))
            suite.addTest(unittest.makeSuite(TestInstallationManagerIntegration))
            return suite
        except NameError:
            print("⚠️  InstallationManager tests not available")
            return None
    
    def _get_preparation_tests(self):
        """Get preparation manager tests"""
        if not IMPORTS_SUCCESSFUL:
            return None
        
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestPreparationManager))
            suite.addTest(unittest.makeSuite(TestPreparationManagerIntegration))
            return suite
        except NameError:
            print("⚠️  PreparationManager tests not available")
            return None
    
    def _get_recovery_tests(self):
        """Get recovery manager tests"""
        if not IMPORTS_SUCCESSFUL:
            return None
        
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestRecoveryManager))
            suite.addTest(unittest.makeSuite(TestRecoveryManagerIntegration))
            return suite
        except NameError:
            print("⚠️  RecoveryManager tests not available")
            return None
    
    def _get_notification_tests(self):
        """Get notification manager tests"""
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestNotificationManager))
            suite.addTest(unittest.makeSuite(TestNotificationManagerIntegration))
            return suite
        except NameError:
            print("⚠️  NotificationManager tests not available")
            return None
    
    def _get_organization_tests(self):
        """Get organization manager tests"""
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestOrganizationManager))
            suite.addTest(unittest.makeSuite(TestOrganizationManagerIntegration))
            return suite
        except NameError:
            print("⚠️  OrganizationManager tests not available")
            return None
    
    def _get_logging_tests(self):
        """Get advanced logging tests"""
        if not IMPORTS_SUCCESSFUL:
            return None
        
        try:
            suite = unittest.TestSuite()
            suite.addTest(unittest.makeSuite(TestAdvancedLogger))
            suite.addTest(unittest.makeSuite(TestAdvancedLoggingIntegration))
            return suite
        except NameError:
            print("⚠️  AdvancedLogging tests not available")
            return None
    
    def _run_test_suite(self, suite, verbosity):
        """Run a test suite and capture results"""
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=verbosity,
            buffer=True
        )
        
        # Run tests
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Create custom result object
        custom_result = TestResult()
        custom_result.tests_run = result.testsRun
        custom_result.failures = result.failures
        custom_result.errors = result.errors
        custom_result.skipped = result.skipped
        custom_result.successes = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        custom_result.start_time = start_time
        custom_result.end_time = end_time
        
        # Print captured output
        output = stream.getvalue()
        if output.strip():
            print(output)
        
        return custom_result
    
    def _print_suite_summary(self, suite_name, result):
        """Print summary for a test suite"""
        print(f"\n📊 {suite_name} Test Summary:")
        print(f"   Tests Run: {result.tests_run}")
        print(f"   ✅ Passed: {result.successes}")
        print(f"   ❌ Failed: {len(result.failures)}")
        print(f"   🔥 Errors: {len(result.errors)}")
        print(f"   ⏭️  Skipped: {len(result.skipped)}")
        print(f"   ⏱️  Duration: {result.duration:.2f}s")
        print(f"   📈 Success Rate: {result.success_rate:.1f}%")
        
        # Print failures and errors
        if result.failures:
            print(f"\n❌ Failures in {suite_name}:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print(f"\n🔥 Errors in {suite_name}:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    def _print_comprehensive_summary(self):
        """Print comprehensive summary of all tests"""
        print(f"\n{'=' * 80}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'=' * 80}")
        
        total_tests = sum(r.tests_run for r in self.results.values())
        total_successes = sum(r.successes for r in self.results.values())
        total_failures = sum(len(r.failures) for r in self.results.values())
        total_errors = sum(len(r.errors) for r in self.results.values())
        total_skipped = sum(len(r.skipped) for r in self.results.values())
        total_duration = self.total_end_time - self.total_start_time if self.total_start_time else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Test Suites: {len(self.results)}")
        print(f"   Total Tests Run: {total_tests}")
        print(f"   ✅ Total Passed: {total_successes}")
        print(f"   ❌ Total Failed: {total_failures}")
        print(f"   🔥 Total Errors: {total_errors}")
        print(f"   ⏭️  Total Skipped: {total_skipped}")
        print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
        
        if total_tests > 0:
            overall_success_rate = (total_successes / total_tests) * 100
            print(f"   📊 Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Print per-component summary
        print(f"\n📋 Per-Component Results:")
        for component, result in self.results.items():
            status = "✅ PASS" if len(result.failures) == 0 and len(result.errors) == 0 else "❌ FAIL"
            print(f"   {component:20} {status:8} ({result.successes}/{result.tests_run} passed)")
        
        # Print requirements coverage
        self._print_requirements_coverage()
        
        # Final verdict
        overall_success = self._get_overall_success()
        if overall_success:
            print(f"\n🎉 ALL TESTS PASSED! Environment Dev is ready for production.")
        else:
            print(f"\n⚠️  SOME TESTS FAILED. Please review and fix issues before deployment.")
    
    def _print_requirements_coverage(self):
        """Print requirements coverage summary"""
        print(f"\n📋 Requirements Coverage:")
        
        # Map components to requirements (based on task requirements)
        requirements_coverage = {
            "Requirement 1 (Diagnostic System)": ["DiagnosticManager"],
            "Requirement 2 (Download Security)": ["DownloadManager"],
            "Requirement 3 (Environment Preparation)": ["PreparationManager"],
            "Requirement 4 (Robust Installation)": ["InstallationManager"],
            "Requirement 5 (Organization)": ["OrganizationManager"],
            "Requirement 6 (Interface)": ["NotificationManager"],
            "Requirement 7 (Feedback System)": ["NotificationManager", "AdvancedLogging"],
            "Requirement 8 (Recovery & Maintenance)": ["RecoveryManager"]
        }
        
        for requirement, components in requirements_coverage.items():
            covered_components = [c for c in components if c in self.results]
            if covered_components:
                all_passed = all(
                    len(self.results[c].failures) == 0 and len(self.results[c].errors) == 0
                    for c in covered_components
                )
                status = "✅ COVERED" if all_passed else "⚠️  ISSUES"
                print(f"   {requirement:35} {status}")
            else:
                print(f"   {requirement:35} ❌ NOT TESTED")
    
    def _get_overall_success(self):
        """Determine if all tests passed"""
        return all(
            len(result.failures) == 0 and len(result.errors) == 0
            for result in self.results.values()
        )


def run_specific_component_tests(component_name, verbosity=2):
    """Run tests for a specific component"""
    runner = ComprehensiveTestRunner()
    
    component_map = {
        'diagnostic': runner._get_diagnostic_tests,
        'download': runner._get_download_tests,
        'installation': runner._get_installation_tests,
        'preparation': runner._get_preparation_tests,
        'recovery': runner._get_recovery_tests,
        'notification': runner._get_notification_tests,
        'organization': runner._get_organization_tests,
        'logging': runner._get_logging_tests
    }
    
    if component_name.lower() not in component_map:
        print(f"❌ Unknown component: {component_name}")
        print(f"Available components: {', '.join(component_map.keys())}")
        return False
    
    print(f"Running tests for {component_name}...")
    suite = component_map[component_name.lower()]()
    
    if suite:
        result = runner._run_test_suite(suite, verbosity)
        runner._print_suite_summary(component_name, result)
        return len(result.failures) == 0 and len(result.errors) == 0
    else:
        print(f"❌ No tests available for {component_name}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Dev Unit Test Runner")
    parser.add_argument(
        '--component', '-c',
        help="Run tests for specific component only",
        choices=['diagnostic', 'download', 'installation', 'preparation', 
                'recovery', 'notification', 'organization', 'logging']
    )
    parser.add_argument(
        '--verbosity', '-v',
        type=int,
        default=2,
        help="Test verbosity level (0-2)"
    )
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help="Run quick tests only (skip integration tests)"
    )
    
    args = parser.parse_args()
    
    if args.component:
        success = run_specific_component_tests(args.component, args.verbosity)
        sys.exit(0 if success else 1)
    else:
        runner = ComprehensiveTestRunner()
        success = runner.run_all_tests(args.verbosity)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()