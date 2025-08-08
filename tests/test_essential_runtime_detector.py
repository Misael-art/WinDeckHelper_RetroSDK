#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for EssentialRuntimeDetector.

Tests the detection of all 8 essential runtimes including:
- Git 2.47.1
- .NET SDK 8.0
- Java JDK 21
- Visual C++ Redistributables
- Anaconda3
- .NET Desktop Runtime 8.0/9.0
- PowerShell 7
- Node.js/Python updated
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import subprocess
import winreg
from pathlib import Path

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.essential_runtime_detector import EssentialRuntimeDetector, RuntimeDetectionResult, EnvironmentVariableInfo
from core.detection_base import DetectionMethod


class TestEssentialRuntimeDetector(unittest.TestCase):
    """Test cases for EssentialRuntimeDetector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = EssentialRuntimeDetector()
    
    def test_initialization(self):
        """Test detector initialization."""
        self.assertIsNotNone(self.detector)
        self.assertIsNotNone(self.detector._runtime_configs)
        self.assertEqual(len(self.detector._runtime_configs), 8)
        
        # Check that all 8 essential runtimes are configured
        expected_runtimes = [
            "git", "dotnet_sdk", "java_jdk", "vcpp_redistributables",
            "anaconda3", "dotnet_desktop_runtime", "powershell", "nodejs_python"
        ]
        
        for runtime in expected_runtimes:
            self.assertIn(runtime, self.detector._runtime_configs)
    
    @patch('subprocess.run')
    def test_detect_via_command_success(self, mock_subprocess):
        """Test successful command-based detection."""
        # Mock successful git version command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.47.1.windows.1"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        config = self.detector._runtime_configs["git"]
        result = self.detector._detect_via_command(config)
        
        self.assertTrue(result["detected"])
        self.assertEqual(result["version"], "2.47.1")
    
    @patch('subprocess.run')
    def test_detect_via_command_failure(self, mock_subprocess):
        """Test failed command-based detection."""
        # Mock failed command
        mock_subprocess.side_effect = FileNotFoundError("Command not found")
        
        config = self.detector._runtime_configs["git"]
        result = self.detector._detect_via_command(config)
        
        self.assertFalse(result["detected"])
    
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    @patch('os.path.exists')
    def test_detect_via_registry_success(self, mock_exists, mock_query_value, mock_open_key):
        """Test successful registry-based detection."""
        # Mock registry key
        mock_key = MagicMock()
        mock_open_key.return_value.__enter__.return_value = mock_key
        
        # Mock path exists check
        mock_exists.return_value = True
        
        # Mock registry values
        def mock_query_side_effect(key, value_name):
            values = {
                "Version": ("21.0.1", winreg.REG_SZ),
                "JavaHome": ("C:\\Program Files\\Java\\jdk-21", winreg.REG_SZ),
            }
            if value_name in values:
                return values[value_name]
            raise WindowsError()
        
        mock_query_value.side_effect = mock_query_side_effect
        
        config = self.detector._runtime_configs["java_jdk"]
        result = self.detector._detect_via_registry(config)
        
        self.assertTrue(result["detected"])
        self.assertEqual(result["version"], "21.0.1")
        self.assertEqual(result["install_path"], "C:\\Program Files\\Java\\jdk-21")
    
    @patch('os.walk')
    @patch('os.path.exists')
    def test_detect_via_filesystem_success(self, mock_exists, mock_walk):
        """Test successful filesystem-based detection."""
        # Mock filesystem structure
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("C:\\Program Files\\Git", ["bin"], []),
            ("C:\\Program Files\\Git\\bin", [], ["git.exe"])
        ]
        
        # Mock executable version detection
        with patch.object(self.detector, '_get_executable_version', return_value="2.47.1"):
            config = self.detector._runtime_configs["git"]
            result = self.detector._detect_via_filesystem(config)
            
            self.assertTrue(result["detected"])
            self.assertEqual(result["version"], "2.47.1")
            self.assertIn("git.exe", result["executable_path"])
    
    @patch.dict(os.environ, {"JAVA_HOME": "C:\\Java", "CONDA_PREFIX": "C:\\Anaconda3"})
    def test_detect_environment_variables(self):
        """Test environment variable detection."""
        config = self.detector._runtime_configs["java_jdk"]
        env_vars = self.detector._detect_environment_variables(config)
        
        self.assertIn("JAVA_HOME", env_vars)
        self.assertEqual(env_vars["JAVA_HOME"], "C:\\Java")
    
    @patch('subprocess.run')
    def test_validate_runtime_success(self, mock_subprocess):
        """Test successful runtime validation."""
        # Mock successful validation commands
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        config = self.detector._runtime_configs["git"]
        result = RuntimeDetectionResult(runtime_name="Git", detected=True)
        
        validation_results = self.detector._validate_runtime(config, result)
        
        # Should have validation results for each command
        self.assertEqual(len(validation_results), len(config["validation_commands"]))
        self.assertTrue(all(validation_results.values()))
    
    @patch('subprocess.run')
    def test_validate_runtime_failure(self, mock_subprocess):
        """Test failed runtime validation."""
        # Mock failed validation commands
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        config = self.detector._runtime_configs["git"]
        result = RuntimeDetectionResult(runtime_name="Git", detected=True)
        
        validation_results = self.detector._validate_runtime(config, result)
        
        # Should have validation results but all failed
        self.assertEqual(len(validation_results), len(config["validation_commands"]))
        self.assertTrue(all(not result for result in validation_results.values()))
    
    @patch('subprocess.run')
    def test_find_executable_path_windows(self, mock_subprocess):
        """Test finding executable path on Windows."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "C:\\Program Files\\Git\\bin\\git.exe\n"
        mock_subprocess.return_value = mock_result
        
        with patch('platform.system', return_value="Windows"):
            path = self.detector._find_executable_path("git")
            
            self.assertEqual(path, "C:\\Program Files\\Git\\bin\\git.exe")
            mock_subprocess.assert_called_with(
                ["where", "git"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
    
    def test_get_registry_version(self):
        """Test getting version from registry key."""
        mock_key = MagicMock()
        
        # Mock QueryValueEx to return version
        with patch('winreg.QueryValueEx') as mock_query:
            mock_query.return_value = ("21.0.1", winreg.REG_SZ)
            
            version = self.detector._get_registry_version(mock_key)
            
            self.assertEqual(version, "21.0.1")
    
    def test_get_registry_install_path(self):
        """Test getting install path from registry key."""
        mock_key = MagicMock()
        
        # Mock QueryValueEx to return install path
        with patch('winreg.QueryValueEx') as mock_query, \
             patch('os.path.exists', return_value=True):
            mock_query.return_value = ("C:\\Program Files\\Java", winreg.REG_SZ)
            
            path = self.detector._get_registry_install_path(mock_key)
            
            self.assertEqual(path, "C:\\Program Files\\Java")
    
    @patch('subprocess.run')
    def test_get_executable_version(self, mock_subprocess):
        """Test getting version from executable."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.47.1"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        config = self.detector._runtime_configs["git"]
        version = self.detector._get_executable_version("C:\\Git\\git.exe", config)
        
        self.assertEqual(version, "2.47.1")
    
    # Test individual runtime detection methods
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_git_2_47_1(self, mock_detect):
        """Test Git 2.47.1 detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="Git",
            detected=True,
            version="2.47.1"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_git_2_47_1()
        
        self.assertEqual(result.runtime_name, "Git")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "2.47.1")
        mock_detect.assert_called_once_with("git", self.detector._runtime_configs["git"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_dotnet_sdk_8_0(self, mock_detect):
        """Test .NET SDK 8.0 detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name=".NET SDK",
            detected=True,
            version="8.0.100"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_dotnet_sdk_8_0()
        
        self.assertEqual(result.runtime_name, ".NET SDK")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "8.0.100")
        mock_detect.assert_called_once_with("dotnet_sdk", self.detector._runtime_configs["dotnet_sdk"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_java_jdk_21(self, mock_detect):
        """Test Java JDK 21 detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="Java JDK",
            detected=True,
            version="21.0.1"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_java_jdk_21()
        
        self.assertEqual(result.runtime_name, "Java JDK")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "21.0.1")
        mock_detect.assert_called_once_with("java_jdk", self.detector._runtime_configs["java_jdk"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_vcpp_redistributables(self, mock_detect):
        """Test Visual C++ Redistributables detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="Visual C++ Redistributables",
            detected=True,
            version="14.0"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_vcpp_redistributables()
        
        self.assertEqual(result.runtime_name, "Visual C++ Redistributables")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "14.0")
        mock_detect.assert_called_once_with("vcpp_redistributables", self.detector._runtime_configs["vcpp_redistributables"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_anaconda3(self, mock_detect):
        """Test Anaconda3 detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="Anaconda3",
            detected=True,
            version="23.1.0"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_anaconda3()
        
        self.assertEqual(result.runtime_name, "Anaconda3")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "23.1.0")
        mock_detect.assert_called_once_with("anaconda3", self.detector._runtime_configs["anaconda3"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_dotnet_desktop_runtime(self, mock_detect):
        """Test .NET Desktop Runtime detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name=".NET Desktop Runtime",
            detected=True,
            version="8.0.1"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_dotnet_desktop_runtime()
        
        self.assertEqual(result.runtime_name, ".NET Desktop Runtime")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "8.0.1")
        mock_detect.assert_called_once_with("dotnet_desktop_runtime", self.detector._runtime_configs["dotnet_desktop_runtime"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_powershell_7(self, mock_detect):
        """Test PowerShell 7 detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="PowerShell",
            detected=True,
            version="7.4.0"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_powershell_7()
        
        self.assertEqual(result.runtime_name, "PowerShell")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "7.4.0")
        mock_detect.assert_called_once_with("powershell", self.detector._runtime_configs["powershell"])
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_updated_nodejs_python(self, mock_detect):
        """Test Node.js/Python updated detection."""
        expected_result = RuntimeDetectionResult(
            runtime_name="Node.js/Python Updated",
            detected=True,
            version="Node.js 20.10.0, Python 3.11.5"
        )
        mock_detect.return_value = expected_result
        
        result = self.detector.detect_updated_nodejs_python()
        
        self.assertEqual(result.runtime_name, "Node.js/Python Updated")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "Node.js 20.10.0, Python 3.11.5")
        mock_detect.assert_called_once_with("nodejs_python", self.detector._runtime_configs["nodejs_python"])
    
    # Test special detection logic
    
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_detect_vcpp_redistributables_special(self, mock_query_value, mock_open_key):
        """Test special Visual C++ Redistributables detection logic."""
        # Mock registry key
        mock_key = MagicMock()
        mock_open_key.return_value.__enter__.return_value = mock_key
        
        # Mock registry values for VC++ Redistributables
        def mock_query_side_effect(key, value_name):
            values = {
                "Version": ("14.38.33130", winreg.REG_SZ),
                "Installed": (1, winreg.REG_DWORD),
            }
            if value_name in values:
                return values[value_name]
            raise WindowsError()
        
        mock_query_value.side_effect = mock_query_side_effect
        
        result = RuntimeDetectionResult(runtime_name="Visual C++ Redistributables")
        result = self.detector._detect_vcpp_redistributables_special(result)
        
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "14.38.33130")
        self.assertEqual(result.detection_method, DetectionMethod.REGISTRY)
        self.assertEqual(result.confidence, 0.9)
    
    @patch('subprocess.run')
    def test_detect_dotnet_desktop_special(self, mock_subprocess):
        """Test special .NET Desktop Runtime detection logic."""
        # Mock dotnet --list-runtimes output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Microsoft.AspNetCore.App 8.0.1 [C:\\Program Files\\dotnet\\shared\\Microsoft.AspNetCore.App]
Microsoft.NETCore.App 8.0.1 [C:\\Program Files\\dotnet\\shared\\Microsoft.NETCore.App]
Microsoft.WindowsDesktop.App 8.0.1 [C:\\Program Files\\dotnet\\shared\\Microsoft.WindowsDesktop.App]
Microsoft.WindowsDesktop.App 9.0.0 [C:\\Program Files\\dotnet\\shared\\Microsoft.WindowsDesktop.App]"""
        mock_subprocess.return_value = mock_result
        
        result = RuntimeDetectionResult(runtime_name=".NET Desktop Runtime")
        result = self.detector._detect_dotnet_desktop_special(result)
        
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "9.0.0")  # Should pick highest version
        self.assertEqual(result.detection_method, DetectionMethod.PATH_BASED)
        self.assertEqual(result.confidence, 0.95)
        self.assertTrue(result.metadata["has_8_0"])
        self.assertTrue(result.metadata["has_9_0"])
    
    @patch('subprocess.run')
    def test_detect_nodejs_python_special(self, mock_subprocess):
        """Test special Node.js/Python detection logic."""
        # Mock both Node.js and Python commands
        def mock_subprocess_side_effect(cmd, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            
            if cmd[0] == "node":
                mock_result.stdout = "v20.10.0"
            elif cmd[0] == "python":
                mock_result.stdout = "Python 3.11.5"
            
            return mock_result
        
        mock_subprocess.side_effect = mock_subprocess_side_effect
        
        result = RuntimeDetectionResult(runtime_name="Node.js/Python Updated")
        result = self.detector._detect_nodejs_python_special(result)
        
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "Node.js 20.10.0, Python 3.11.5")
        self.assertEqual(result.detection_method, DetectionMethod.PATH_BASED)
        self.assertEqual(result.confidence, 0.9)
        self.assertTrue(result.metadata["node_detected"])
        self.assertTrue(result.metadata["python_detected"])
        self.assertEqual(result.metadata["node_version"], "20.10.0")
        self.assertEqual(result.metadata["python_version"], "3.11.5")
    
    @patch('subprocess.run')
    @patch.dict(os.environ, {"CONDA_PREFIX": "C:\\Anaconda3", "CONDA_DEFAULT_ENV": "base"})
    def test_detect_anaconda3_special(self, mock_subprocess):
        """Test special Anaconda3 detection logic."""
        # Mock conda and python commands
        def mock_subprocess_side_effect(cmd, **kwargs):
            mock_result = MagicMock()
            mock_result.returncode = 0
            
            if cmd[0] == "conda":
                mock_result.stdout = "conda 23.1.0"
            elif cmd[0] == "python":
                mock_result.stdout = "Python 3.11.5"
            
            return mock_result
        
        mock_subprocess.side_effect = mock_subprocess_side_effect
        
        result = RuntimeDetectionResult(runtime_name="Anaconda3")
        result = self.detector._detect_anaconda3_special(result)
        
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "23.1.0")
        self.assertEqual(result.detection_method, DetectionMethod.PATH_BASED)
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.metadata["conda_version"], "23.1.0")
        self.assertEqual(result.metadata["python_version"], "3.11.5")
        self.assertIn("CONDA_PREFIX", result.environment_variables)
        self.assertIn("CONDA_DEFAULT_ENV", result.environment_variables)
    
    # Integration tests
    
    @patch.object(EssentialRuntimeDetector, '_detect_single_runtime')
    def test_detect_all_essential_runtimes(self, mock_detect):
        """Test detection of all essential runtimes."""
        # Mock detection results for all runtimes
        def mock_detect_side_effect(runtime_key, config):
            return RuntimeDetectionResult(
                runtime_name=config["name"],
                detected=True,
                version="1.0.0"
            )
        
        mock_detect.side_effect = mock_detect_side_effect
        
        results = self.detector.detect_all_essential_runtimes()
        
        self.assertEqual(len(results), 8)
        self.assertTrue(all(result.detected for result in results))
        self.assertEqual(mock_detect.call_count, 8)
    
    @patch('subprocess.run')
    @patch('winreg.OpenKey')
    @patch('os.walk')
    def test_detect_single_runtime_integration(self, mock_walk, mock_open_key, mock_subprocess):
        """Test complete single runtime detection flow."""
        # Mock successful command detection
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.47.1"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        # Mock environment variables
        with patch.dict(os.environ, {"PATH": "C:\\Git\\bin"}):
            result = self.detector._detect_single_runtime("git", self.detector._runtime_configs["git"])
            
            self.assertTrue(result.detected)
            self.assertEqual(result.runtime_name, "Git")
            self.assertEqual(result.version, "2.47.1")
            self.assertEqual(result.detection_method, DetectionMethod.PATH_BASED)
            self.assertGreater(result.confidence, 0.0)
    
    def test_runtime_detection_result_dataclass(self):
        """Test RuntimeDetectionResult dataclass functionality."""
        result = RuntimeDetectionResult(
            runtime_name="Test Runtime",
            detected=True,
            version="1.0.0",
            confidence=0.9
        )
        
        self.assertEqual(result.runtime_name, "Test Runtime")
        self.assertTrue(result.detected)
        self.assertEqual(result.version, "1.0.0")
        self.assertEqual(result.confidence, 0.9)
        self.assertIsInstance(result.environment_variables, dict)
        self.assertIsInstance(result.validation_commands, list)
        self.assertIsInstance(result.validation_results, dict)
        self.assertIsInstance(result.metadata, dict)
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.warnings, list)
    
    def test_environment_variable_info_dataclass(self):
        """Test EnvironmentVariableInfo dataclass functionality."""
        env_info = EnvironmentVariableInfo(
            name="JAVA_HOME",
            expected_value="C:\\Java",
            current_value="C:\\Java",
            is_set=True,
            is_correct=True,
            description="Java installation directory"
        )
        
        self.assertEqual(env_info.name, "JAVA_HOME")
        self.assertEqual(env_info.expected_value, "C:\\Java")
        self.assertEqual(env_info.current_value, "C:\\Java")
        self.assertTrue(env_info.is_set)
        self.assertTrue(env_info.is_correct)
        self.assertEqual(env_info.description, "Java installation directory")


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    unittest.main()