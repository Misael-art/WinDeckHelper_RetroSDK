# -*- coding: utf-8 -*-
"""
Unit tests for Runtime-Specific Installation Handler
Tests runtime-specific installation logic for essential runtimes
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.runtime_specific_installer import (
    RuntimeSpecificInstallationManager,
    JavaInstaller,
    PythonInstaller,
    NodeJSInstaller,
    DotNetInstaller,
    RuntimeType,
    RuntimeInstallationMethod,
    RuntimeConfiguration,
    RuntimeInstallationResult
)

class TestRuntimeConfiguration(unittest.TestCase):
    """Test RuntimeConfiguration data class"""
    
    def test_runtime_configuration_creation(self):
        """Test creating runtime configuration"""
        config = RuntimeConfiguration(
            name="Test Runtime",
            runtime_type=RuntimeType.JAVA,
            version="17",
            download_url="https://example.com/java.zip",
            installation_method=RuntimeInstallationMethod.ARCHIVE,
            install_path="/test/java"
        )
        
        self.assertEqual(config.name, "Test Runtime")
        self.assertEqual(config.runtime_type, RuntimeType.JAVA)
        self.assertEqual(config.version, "17")
        self.assertEqual(config.download_url, "https://example.com/java.zip")
        self.assertEqual(config.installation_method, RuntimeInstallationMethod.ARCHIVE)
        self.assertEqual(config.install_path, "/test/java")
        self.assertEqual(len(config.environment_variables), 0)
        self.assertEqual(len(config.path_entries), 0)

class TestRuntimeInstallationResult(unittest.TestCase):
    """Test RuntimeInstallationResult data class"""
    
    def test_runtime_installation_result_creation(self):
        """Test creating runtime installation result"""
        result = RuntimeInstallationResult(
            success=True,
            runtime_type=RuntimeType.PYTHON,
            version="3.11",
            installed_path="/test/python",
            installation_time=45.5,
            message="Installation successful"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.runtime_type, RuntimeType.PYTHON)
        self.assertEqual(result.version, "3.11")
        self.assertEqual(result.installed_path, "/test/python")
        self.assertEqual(result.installation_time, 45.5)
        self.assertEqual(result.message, "Installation successful")
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)

class TestJavaInstaller(unittest.TestCase):
    """Test JavaInstaller class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.installer = JavaInstaller(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_runtime_type(self):
        """Test getting runtime type"""
        runtime_type = self.installer.get_runtime_type()
        self.assertEqual(runtime_type, RuntimeType.JAVA)
    
    def test_get_default_configuration(self):
        """Test getting default Java configuration"""
        config = self.installer.get_default_configuration("17")
        
        self.assertEqual(config.runtime_type, RuntimeType.JAVA)
        self.assertEqual(config.version, "17")
        self.assertEqual(config.installation_method, RuntimeInstallationMethod.ARCHIVE)
        self.assertIn("JAVA_HOME", config.environment_variables)
        self.assertIn("JDK_HOME", config.environment_variables)
        self.assertGreater(len(config.path_entries), 0)
        self.assertGreater(len(config.verification_commands), 0)
    
    @patch('utils.env_manager.set_env_var')
    @patch('utils.env_manager.add_to_path')
    def test_configure_environment(self, mock_add_to_path, mock_set_env_var):
        """Test configuring environment for Java"""
        mock_set_env_var.return_value = True
        mock_add_to_path.return_value = True
        
        config = self.installer.get_default_configuration("17")
        result = self.installer.configure_environment(config)
        
        self.assertTrue(result)
        self.assertEqual(mock_set_env_var.call_count, len(config.environment_variables))
        self.assertEqual(mock_add_to_path.call_count, len(config.path_entries))
    
    @patch('subprocess.run')
    def test_run_post_install_commands(self, mock_run):
        """Test running post-install commands"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        config = RuntimeConfiguration(
            name="Test Java",
            runtime_type=RuntimeType.JAVA,
            version="17",
            download_url="https://example.com/java.zip",
            installation_method=RuntimeInstallationMethod.ARCHIVE,
            install_path="/test/java",
            post_install_commands=[["java", "-version"]]
        )
        
        results = self.installer.run_post_install_commands(config)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['success'])
        self.assertEqual(results[0]['return_code'], 0)
    
    @patch('subprocess.run')
    @patch('utils.env_manager.get_env_var')
    def test_verify_installation_success(self, mock_get_env_var, mock_run):
        """Test successful Java installation verification"""
        mock_get_env_var.return_value = "/test/java"
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = 'openjdk version "17.0.1" 2021-10-19'
        mock_run.return_value = mock_result
        
        # Mock os.path.exists
        with patch('os.path.exists', return_value=True):
            config = self.installer.get_default_configuration("17")
            verification_result = self.installer.verify_installation(config)
        
        self.assertTrue(verification_result['success'])
        self.assertTrue(verification_result['java_home_valid'])
        self.assertIsNotNone(verification_result['version_detected'])
        self.assertGreater(len(verification_result['commands_working']), 0)
    
    @patch('subprocess.run')
    @patch('utils.env_manager.get_env_var')
    def test_verify_installation_failure(self, mock_get_env_var, mock_run):
        """Test failed Java installation verification"""
        mock_get_env_var.return_value = None
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command not found"
        mock_run.return_value = mock_result
        
        config = self.installer.get_default_configuration("17")
        verification_result = self.installer.verify_installation(config)
        
        self.assertFalse(verification_result['success'])
        self.assertFalse(verification_result['java_home_valid'])
        self.assertGreater(len(verification_result['errors']), 0)

class TestPythonInstaller(unittest.TestCase):
    """Test PythonInstaller class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.installer = PythonInstaller(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_runtime_type(self):
        """Test getting runtime type"""
        runtime_type = self.installer.get_runtime_type()
        self.assertEqual(runtime_type, RuntimeType.PYTHON)
    
    def test_get_default_configuration(self):
        """Test getting default Python configuration"""
        config = self.installer.get_default_configuration("3.11")
        
        self.assertEqual(config.runtime_type, RuntimeType.PYTHON)
        self.assertEqual(config.version, "3.11")
        self.assertIn("PYTHON_HOME", config.environment_variables)
        self.assertIn("PYTHONPATH", config.environment_variables)
        self.assertGreater(len(config.path_entries), 0)
        self.assertGreater(len(config.verification_commands), 0)
    
    def test_create_python_build_script(self):
        """Test creating Python build script"""
        config = self.installer.get_default_configuration("3.11")
        script_path = self.installer._create_python_build_script(config)
        
        self.assertTrue(os.path.exists(script_path))
        self.assertTrue(script_path.endswith('.sh'))
        
        # Check script content
        with open(script_path, 'r') as f:
            content = f.read()
        
        self.assertIn("#!/bin/bash", content)
        self.assertIn("./configure", content)
        self.assertIn("make install", content)
    
    @patch('subprocess.run')
    @patch('utils.env_manager.get_env_var')
    def test_verify_installation_success(self, mock_get_env_var, mock_run):
        """Test successful Python installation verification"""
        mock_get_env_var.return_value = "/test/python"
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.11.0"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock os.path.exists
        with patch('os.path.exists', return_value=True):
            config = self.installer.get_default_configuration("3.11")
            verification_result = self.installer.verify_installation(config)
        
        self.assertTrue(verification_result['success'])
        self.assertTrue(verification_result['python_home_valid'])
        self.assertIsNotNone(verification_result['version_detected'])

class TestNodeJSInstaller(unittest.TestCase):
    """Test NodeJSInstaller class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.installer = NodeJSInstaller(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_runtime_type(self):
        """Test getting runtime type"""
        runtime_type = self.installer.get_runtime_type()
        self.assertEqual(runtime_type, RuntimeType.NODEJS)
    
    def test_get_default_configuration(self):
        """Test getting default Node.js configuration"""
        config = self.installer.get_default_configuration("18")
        
        self.assertEqual(config.runtime_type, RuntimeType.NODEJS)
        self.assertEqual(config.version, "18")
        self.assertEqual(config.installation_method, RuntimeInstallationMethod.ARCHIVE)
        self.assertIn("NODE_HOME", config.environment_variables)
        self.assertIn("NPM_CONFIG_PREFIX", config.environment_variables)
        self.assertGreater(len(config.path_entries), 0)
        self.assertGreater(len(config.verification_commands), 0)
    
    @patch('subprocess.run')
    @patch('utils.env_manager.get_env_var')
    def test_verify_installation_success(self, mock_get_env_var, mock_run):
        """Test successful Node.js installation verification"""
        mock_get_env_var.return_value = "/test/nodejs"
        
        # Mock different responses for node and npm commands
        def mock_run_side_effect(command, **kwargs):
            mock_result = Mock()
            mock_result.returncode = 0
            if command[0] == "node":
                mock_result.stdout = "v18.0.0"
            elif command[0] == "npm":
                mock_result.stdout = "8.0.0"
            mock_result.stderr = ""
            return mock_result
        
        mock_run.side_effect = mock_run_side_effect
        
        # Mock os.path.exists
        with patch('os.path.exists', return_value=True):
            config = self.installer.get_default_configuration("18")
            verification_result = self.installer.verify_installation(config)
        
        self.assertTrue(verification_result['success'])
        self.assertTrue(verification_result['node_home_valid'])
        self.assertIsNotNone(verification_result['node_version'])
        self.assertIsNotNone(verification_result['npm_version'])

class TestDotNetInstaller(unittest.TestCase):
    """Test DotNetInstaller class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.installer = DotNetInstaller(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_runtime_type(self):
        """Test getting runtime type"""
        runtime_type = self.installer.get_runtime_type()
        self.assertEqual(runtime_type, RuntimeType.DOTNET)
    
    def test_get_default_configuration(self):
        """Test getting default .NET configuration"""
        config = self.installer.get_default_configuration("6.0")
        
        self.assertEqual(config.runtime_type, RuntimeType.DOTNET)
        self.assertEqual(config.version, "6.0")
        self.assertEqual(config.installation_method, RuntimeInstallationMethod.ARCHIVE)
        self.assertIn("DOTNET_ROOT", config.environment_variables)
        self.assertIn("DOTNET_CLI_TELEMETRY_OPTOUT", config.environment_variables)
        self.assertGreater(len(config.path_entries), 0)
        self.assertGreater(len(config.verification_commands), 0)

class TestRuntimeSpecificInstallationManager(unittest.TestCase):
    """Test RuntimeSpecificInstallationManager class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.manager = RuntimeSpecificInstallationManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.base_path, self.test_dir)
        self.assertGreater(len(self.manager.installers), 0)
        self.assertIn(RuntimeType.JAVA, self.manager.installers)
        self.assertIn(RuntimeType.PYTHON, self.manager.installers)
        self.assertIn(RuntimeType.NODEJS, self.manager.installers)
        self.assertIn(RuntimeType.DOTNET, self.manager.installers)
    
    def test_get_supported_runtimes(self):
        """Test getting supported runtimes"""
        supported = self.manager.get_supported_runtimes()
        
        self.assertIsInstance(supported, list)
        self.assertGreater(len(supported), 0)
        self.assertIn(RuntimeType.JAVA, supported)
        self.assertIn(RuntimeType.PYTHON, supported)
    
    def test_get_runtime_configuration(self):
        """Test getting runtime configuration"""
        config = self.manager.get_runtime_configuration(RuntimeType.JAVA, "17")
        
        self.assertIsNotNone(config)
        self.assertEqual(config.runtime_type, RuntimeType.JAVA)
        self.assertEqual(config.version, "17")
    
    def test_get_runtime_configuration_unsupported(self):
        """Test getting configuration for unsupported runtime"""
        config = self.manager.get_runtime_configuration(RuntimeType.GO, "1.19")
        
        # GO is not implemented yet, should return None
        self.assertIsNone(config)
    
    @patch('core.intelligent_preparation_manager.IntelligentPreparationManager.prepare_intelligent_environment')
    def test_install_runtime_preparation_failure(self, mock_prepare):
        """Test runtime installation when preparation fails"""
        # Mock preparation failure
        mock_prep_result = Mock()
        mock_prep_result.status.value = "failed"
        mock_prep_result.message = "Preparation failed"
        mock_prepare.return_value = mock_prep_result
        
        result = self.manager.install_runtime(RuntimeType.JAVA, "17")
        
        self.assertFalse(result.success)
        self.assertIn("Preparation failed", result.message)
        self.assertGreater(len(result.errors), 0)
    
    def test_install_runtime_unsupported(self):
        """Test installing unsupported runtime"""
        result = self.manager.install_runtime(RuntimeType.GO, "1.19")
        
        self.assertFalse(result.success)
        self.assertIn("No installer available", result.message)
        self.assertGreater(len(result.errors), 0)
    
    def test_verify_runtime_unsupported(self):
        """Test verifying unsupported runtime"""
        verification_result = self.manager.verify_runtime(RuntimeType.GO)
        
        self.assertFalse(verification_result['success'])
        self.assertIn("No installer available", verification_result['errors'][0])
    
    def test_install_multiple_runtimes(self):
        """Test installing multiple runtimes"""
        runtime_specs = [
            (RuntimeType.JAVA, "17"),
            (RuntimeType.PYTHON, "3.11")
        ]
        
        # Mock preparation
        with patch('core.intelligent_preparation_manager.IntelligentPreparationManager.prepare_intelligent_environment') as mock_prepare:
            mock_prep_result = Mock()
            mock_prep_result.status.value = "completed"
            mock_prep_result.message = "Preparation successful"
            mock_prepare.return_value = mock_prep_result
            
            # Mock individual installations
            with patch.object(self.manager, 'install_runtime') as mock_install:
                mock_install.return_value = RuntimeInstallationResult(
                    success=True,
                    runtime_type=RuntimeType.JAVA,
                    version="17",
                    installed_path="/test/java",
                    message="Installation successful"
                )
                
                results = self.manager.install_multiple_runtimes(runtime_specs, parallel=False)
        
        self.assertEqual(len(results), 2)
        self.assertIn(RuntimeType.JAVA, results)
        self.assertIn(RuntimeType.PYTHON, results)
    
    def test_generate_installation_report(self):
        """Test generating installation report"""
        # Create mock results
        results = {
            RuntimeType.JAVA: RuntimeInstallationResult(
                success=True,
                runtime_type=RuntimeType.JAVA,
                version="17",
                installed_path="/test/java",
                installation_time=30.5,
                message="Java installed successfully",
                environment_variables={"JAVA_HOME": "/test/java"},
                path_entries=["/test/java/bin"]
            ),
            RuntimeType.PYTHON: RuntimeInstallationResult(
                success=False,
                runtime_type=RuntimeType.PYTHON,
                version="3.11",
                installed_path="",
                installation_time=15.2,
                message="Python installation failed",
                errors=["Download failed"]
            )
        }
        
        report = self.manager.generate_installation_report(results)
        
        self.assertEqual(report['total_runtimes'], 2)
        self.assertEqual(report['successful_installations'], 1)
        self.assertEqual(report['failed_installations'], 1)
        self.assertEqual(report['summary']['success_rate'], 50.0)
        self.assertGreater(report['summary']['average_installation_time'], 0)
        self.assertEqual(report['summary']['environment_variables_set'], 1)
        self.assertEqual(report['summary']['path_entries_added'], 1)
        
        # Check runtime details
        self.assertIn('java', report['runtime_details'])
        self.assertIn('python', report['runtime_details'])
        self.assertTrue(report['runtime_details']['java']['success'])
        self.assertFalse(report['runtime_details']['python']['success'])

if __name__ == '__main__':
    unittest.main()