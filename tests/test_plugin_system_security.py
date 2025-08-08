# -*- coding: utf-8 -*-
"""
Test Suite for Plugin System Security

Tests for plugin isolation, validation, and security features.
Addresses requirements 7.1, 7.2, and 7.5.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add core to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from plugin_system_manager import (
    PluginSystemManager, PluginStructureValidation, SecurePluginContext,
    PluginExecutionResult, PluginSystemError, PluginValidationError,
    PluginSecurityError, PluginLoadError
)
from plugin_base import PluginMetadata, Permission, PluginInterface, PluginStatus
from plugin_security import PluginTrustLevel


class TestPluginStructureValidation:
    """Test plugin structure validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = PluginSystemManager(
            plugin_directories=[str(self.temp_dir)],
            require_signatures=False  # Disable for testing
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_plugin(self, name: str, include_required_files: bool = True, 
                          metadata: dict = None) -> Path:
        """Create a test plugin directory"""
        plugin_dir = self.temp_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        if include_required_files:
            # Create plugin.json
            default_metadata = {
                "name": name,
                "version": "1.0.0",
                "author": "Test Author",
                "description": "Test plugin",
                "api_version": "1.0",
                "permissions": ["read_filesystem"],
                "entry_point": "TestPlugin"
            }
            if metadata:
                default_metadata.update(metadata)
            
            with open(plugin_dir / "plugin.json", "w") as f:
                json.dump(default_metadata, f, indent=2)
            
            # Create __init__.py
            plugin_code = '''
from core.plugin_base import PluginInterface

class TestPlugin(PluginInterface):
    def initialize(self, context):
        return True
    
    def execute(self, **kwargs):
        return "test_result"
    
    def cleanup(self):
        return True
'''
            with open(plugin_dir / "__init__.py", "w") as f:
                f.write(plugin_code)
            
            # Create README.md
            with open(plugin_dir / "README.md", "w") as f:
                f.write(f"# {name}\n\nTest plugin for validation")
        
        return plugin_dir
    
    def test_valid_plugin_structure(self):
        """Test validation of valid plugin structure"""
        plugin_dir = self.create_test_plugin("valid_plugin")
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        assert validation.is_valid
        assert len(validation.errors) == 0
        assert validation.required_files_present
        assert validation.metadata_valid
    
    def test_missing_required_files(self):
        """Test validation fails for missing required files"""
        plugin_dir = self.temp_dir / "incomplete_plugin"
        plugin_dir.mkdir()
        
        # Only create plugin.json, missing __init__.py
        metadata = {
            "name": "incomplete_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Incomplete plugin",
            "api_version": "1.0"
        }
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        assert not validation.is_valid
        assert not validation.required_files_present
        assert any("__init__.py" in error for error in validation.errors)
    
    def test_invalid_metadata_format(self):
        """Test validation fails for invalid metadata"""
        plugin_dir = self.create_test_plugin("invalid_metadata", metadata={
            "name": "",  # Invalid empty name
            "version": "invalid_version",  # Invalid version format
            "api_version": "999.0"  # Unsupported API version
        })
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        assert not validation.is_valid
        assert not validation.metadata_valid
        assert len(validation.errors) > 0
    
    def test_suspicious_files_detection(self):
        """Test detection of suspicious files"""
        plugin_dir = self.create_test_plugin("suspicious_plugin")
        
        # Add suspicious files
        (plugin_dir / "malware.exe").touch()
        (plugin_dir / "script.bat").touch()
        (plugin_dir / ".hidden_file").touch()
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        assert not validation.is_valid
        assert len(validation.security_issues) > 0
        assert any("malware.exe" in issue for issue in validation.security_issues)
        assert any("script.bat" in issue for issue in validation.security_issues)
        assert any(".hidden_file" in issue for issue in validation.security_issues)
    
    def test_dangerous_permissions_warning(self):
        """Test warning for dangerous permissions"""
        plugin_dir = self.create_test_plugin("dangerous_plugin", metadata={
            "permissions": ["system_commands", "privileged_operations", "registry_write"]
        })
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        # Should still be valid but with warnings
        assert validation.is_valid
        assert len(validation.warnings) > 0
    
    def test_code_syntax_validation(self):
        """Test Python code syntax validation"""
        plugin_dir = self.create_test_plugin("syntax_error_plugin", include_required_files=False)
        
        # Create plugin.json
        metadata = {
            "name": "syntax_error_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Plugin with syntax error",
            "api_version": "1.0"
        }
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        # Create __init__.py with syntax error
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write("def invalid_syntax(\n")  # Missing closing parenthesis
        
        validation = self.plugin_manager.validate_plugin_structure(plugin_dir)
        
        assert not validation.is_valid
        assert any("syntax error" in error.lower() for error in validation.errors)


class TestPluginSecurity:
    """Test plugin security and sandboxing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = PluginSystemManager(
            plugin_directories=[str(self.temp_dir)],
            enable_sandboxing=True,
            require_signatures=False
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.plugin_manager.shutdown()
    
    def create_secure_test_plugin(self, name: str, trust_level: PluginTrustLevel = PluginTrustLevel.UNTRUSTED) -> Path:
        """Create a secure test plugin"""
        plugin_dir = self.temp_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create plugin.json
        metadata = {
            "name": name,
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Secure test plugin",
            "api_version": "1.0",
            "permissions": ["read_filesystem"],
            "entry_point": "SecureTestPlugin"
        }
        
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Create secure plugin implementation
        plugin_code = '''
from core.plugin_base import PluginInterface

class SecureTestPlugin(PluginInterface):
    def initialize(self, context):
        self.context = context
        return True
    
    def execute(self, **kwargs):
        return {"status": "success", "data": kwargs}
    
    def cleanup(self):
        return True
    
    def get_info(self):
        return {"name": self.metadata.name, "version": self.metadata.version}
'''
        
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(plugin_code)
        
        return plugin_dir
    
    def test_secure_plugin_loading(self):
        """Test secure plugin loading with validation"""
        plugin_dir = self.create_secure_test_plugin("secure_plugin")
        
        success = self.plugin_manager.load_plugin_with_security(
            plugin_dir, PluginTrustLevel.BASIC
        )
        
        assert success
        assert "secure_plugin" in self.plugin_manager.loaded_plugins
        
        plugin_info = self.plugin_manager.loaded_plugins["secure_plugin"]
        assert plugin_info["status"] == PluginStatus.LOADED
        assert plugin_info["trust_level"] == PluginTrustLevel.BASIC
    
    def test_plugin_sandboxing(self):
        """Test plugin execution in sandbox environment"""
        plugin_dir = self.create_secure_test_plugin("sandboxed_plugin")
        
        # Load plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        assert success
        
        # Execute plugin in sandbox
        with self.plugin_manager.execute_plugin_secure("sandboxed_plugin", "execute", test_param="value") as result:
            assert result.success
            assert result.result["status"] == "success"
            assert result.result["data"]["test_param"] == "value"
            assert result.execution_time > 0
            assert len(result.security_violations) == 0
    
    def test_plugin_permission_checking(self):
        """Test plugin permission validation"""
        plugin_dir = self.create_secure_test_plugin("permission_plugin")
        
        # Load plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        assert success
        
        # Check permissions
        plugin_security = self.plugin_manager.plugin_security
        
        # Should have read_filesystem permission
        assert plugin_security.check_permission("permission_plugin", Permission.READ_FILESYSTEM)
        
        # Should not have write_filesystem permission
        assert not plugin_security.check_permission("permission_plugin", Permission.WRITE_FILESYSTEM)
    
    def test_blocked_plugin_loading(self):
        """Test that blocked plugins cannot be loaded"""
        plugin_dir = self.create_secure_test_plugin("blocked_plugin")
        
        # Add plugin to blocked list
        self.plugin_manager.blocked_plugins.add("blocked_plugin")
        
        # Attempt to load blocked plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        
        assert not success
        assert "blocked_plugin" not in self.plugin_manager.loaded_plugins
    
    def test_plugin_execution_timeout(self):
        """Test plugin execution timeout enforcement"""
        plugin_dir = self.temp_dir / "timeout_plugin"
        plugin_dir.mkdir()
        
        # Create plugin that takes too long
        metadata = {
            "name": "timeout_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Plugin that times out",
            "api_version": "1.0",
            "entry_point": "TimeoutPlugin"
        }
        
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        plugin_code = '''
import time
from core.plugin_base import PluginInterface

class TimeoutPlugin(PluginInterface):
    def initialize(self, context):
        return True
    
    def execute(self, **kwargs):
        time.sleep(10)  # Sleep longer than timeout
        return "should_not_reach_here"
    
    def cleanup(self):
        return True
'''
        
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(plugin_code)
        
        # Load plugin with short timeout
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        assert success
        
        # Execute with timeout (should fail)
        with pytest.raises(Exception):  # Should raise timeout exception
            with self.plugin_manager.execute_plugin_secure("timeout_plugin", "execute") as result:
                pass
    
    def test_restricted_api_access(self):
        """Test that plugins have restricted API access"""
        plugin_dir = self.temp_dir / "restricted_plugin"
        plugin_dir.mkdir()
        
        metadata = {
            "name": "restricted_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Plugin with restricted access",
            "api_version": "1.0",
            "entry_point": "RestrictedPlugin"
        }
        
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        # Plugin that tries to access restricted functionality
        plugin_code = '''
from core.plugin_base import PluginInterface

class RestrictedPlugin(PluginInterface):
    def initialize(self, context):
        return True
    
    def execute(self, **kwargs):
        try:
            # Try to import restricted module
            import subprocess
            return {"error": "Should not be able to import subprocess"}
        except ImportError:
            return {"success": "Correctly restricted"}
    
    def cleanup(self):
        return True
'''
        
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(plugin_code)
        
        # Load and execute plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        assert success
        
        with self.plugin_manager.execute_plugin_secure("restricted_plugin", "execute") as result:
            assert result.success
            assert "Correctly restricted" in result.result.get("success", "")


class TestPluginConflictDetection:
    """Test plugin conflict detection functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = PluginSystemManager(
            plugin_directories=[str(self.temp_dir)],
            require_signatures=False
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.plugin_manager.shutdown()
    
    def create_conflicting_plugins(self):
        """Create plugins that have conflicts"""
        # Plugin 1
        plugin1_dir = self.temp_dir / "plugin1"
        plugin1_dir.mkdir()
        
        metadata1 = {
            "name": "plugin1",
            "version": "1.0.0",
            "author": "Test",
            "description": "First plugin",
            "api_version": "1.0",
            "dependencies": ["plugin2>=2.0.0"],
            "entry_point": "Plugin1"
        }
        
        with open(plugin1_dir / "plugin.json", "w") as f:
            json.dump(metadata1, f)
        
        plugin1_code = '''
from core.plugin_base import PluginInterface

class Plugin1(PluginInterface):
    def initialize(self, context): return True
    def execute(self, **kwargs): return "plugin1"
    def cleanup(self): return True
'''
        
        with open(plugin1_dir / "__init__.py", "w") as f:
            f.write(plugin1_code)
        
        # Plugin 2 with incompatible version
        plugin2_dir = self.temp_dir / "plugin2"
        plugin2_dir.mkdir()
        
        metadata2 = {
            "name": "plugin2",
            "version": "1.5.0",  # Lower than required 2.0.0
            "author": "Test",
            "description": "Second plugin",
            "api_version": "1.0",
            "entry_point": "Plugin2"
        }
        
        with open(plugin2_dir / "plugin.json", "w") as f:
            json.dump(metadata2, f)
        
        plugin2_code = '''
from core.plugin_base import PluginInterface

class Plugin2(PluginInterface):
    def initialize(self, context): return True
    def execute(self, **kwargs): return "plugin2"
    def cleanup(self): return True
'''
        
        with open(plugin2_dir / "__init__.py", "w") as f:
            f.write(plugin2_code)
        
        return plugin1_dir, plugin2_dir
    
    def test_dependency_conflict_detection(self):
        """Test detection of dependency conflicts"""
        plugin1_dir, plugin2_dir = self.create_conflicting_plugins()
        
        # Load both plugins
        self.plugin_manager.load_plugin_with_security(plugin1_dir)
        self.plugin_manager.load_plugin_with_security(plugin2_dir)
        
        # Detect conflicts
        conflicts = self.plugin_manager.detect_plugin_conflicts()
        
        # Should detect version conflict
        assert len(conflicts) > 0
        version_conflicts = [c for c in conflicts if c.conflict_type.value == "version_conflict"]
        assert len(version_conflicts) > 0
    
    def test_name_conflict_detection(self):
        """Test detection of plugin name conflicts"""
        # Create two plugins with same name
        plugin_dir1 = self.temp_dir / "same_name_1"
        plugin_dir2 = self.temp_dir / "same_name_2"
        
        for i, plugin_dir in enumerate([plugin_dir1, plugin_dir2], 1):
            plugin_dir.mkdir()
            
            metadata = {
                "name": "duplicate_name",  # Same name
                "version": f"{i}.0.0",
                "author": "Test",
                "description": f"Plugin {i}",
                "api_version": "1.0",
                "entry_point": f"Plugin{i}"
            }
            
            with open(plugin_dir / "plugin.json", "w") as f:
                json.dump(metadata, f)
            
            plugin_code = f'''
from core.plugin_base import PluginInterface

class Plugin{i}(PluginInterface):
    def initialize(self, context): return True
    def execute(self, **kwargs): return "plugin{i}"
    def cleanup(self): return True
'''
            
            with open(plugin_dir / "__init__.py", "w") as f:
                f.write(plugin_code)
        
        # Load first plugin
        success1 = self.plugin_manager.load_plugin_with_security(plugin_dir1)
        assert success1
        
        # Loading second plugin with same name should fail
        success2 = self.plugin_manager.load_plugin_with_security(plugin_dir2)
        assert not success2  # Should fail due to name conflict


class TestPluginStatusReporting:
    """Test plugin status feedback and reporting"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_manager = PluginSystemManager(
            plugin_directories=[str(self.temp_dir)],
            require_signatures=False
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.plugin_manager.shutdown()
    
    def test_plugin_status_report_generation(self):
        """Test generation of comprehensive plugin status report"""
        # Create and load test plugin
        plugin_dir = self.temp_dir / "status_plugin"
        plugin_dir.mkdir()
        
        metadata = {
            "name": "status_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Plugin for status testing",
            "api_version": "1.0",
            "permissions": ["read_filesystem", "network_access"],
            "entry_point": "StatusPlugin"
        }
        
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        plugin_code = '''
from core.plugin_base import PluginInterface

class StatusPlugin(PluginInterface):
    def initialize(self, context): return True
    def execute(self, **kwargs): return "status_test"
    def cleanup(self): return True
'''
        
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(plugin_code)
        
        # Load plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir, PluginTrustLevel.TRUSTED)
        assert success
        
        # Execute plugin to generate execution history
        with self.plugin_manager.execute_plugin_secure("status_plugin", "execute") as result:
            assert result.success
        
        # Generate status report
        report = self.plugin_manager.get_plugin_status_report()
        
        # Verify report structure
        assert "summary" in report
        assert "trust_levels" in report
        assert "execution_statistics" in report
        assert "plugins" in report
        assert "security_report" in report
        
        # Verify summary data
        summary = report["summary"]
        assert summary["total_plugins"] == 1
        assert summary["sandboxing_enabled"] == True
        assert summary["signature_verification_required"] == False
        
        # Verify plugin data
        plugins = report["plugins"]
        assert "status_plugin" in plugins
        plugin_info = plugins["status_plugin"]
        assert plugin_info["name"] == "status_plugin"
        assert plugin_info["version"] == "1.0.0"
        assert plugin_info["trust_level"] == "trusted"
        assert "read_filesystem" in plugin_info["permissions"]
        assert "network_access" in plugin_info["permissions"]
        
        # Verify execution statistics
        exec_stats = report["execution_statistics"]
        assert exec_stats["recent_executions"] >= 1
        assert exec_stats["successful_executions"] >= 1
    
    def test_plugin_unload_status_update(self):
        """Test that plugin status is updated correctly on unload"""
        # Create and load plugin
        plugin_dir = self.temp_dir / "unload_plugin"
        plugin_dir.mkdir()
        
        metadata = {
            "name": "unload_plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "Plugin for unload testing",
            "api_version": "1.0",
            "entry_point": "UnloadPlugin"
        }
        
        with open(plugin_dir / "plugin.json", "w") as f:
            json.dump(metadata, f)
        
        plugin_code = '''
from core.plugin_base import PluginInterface

class UnloadPlugin(PluginInterface):
    def initialize(self, context): return True
    def execute(self, **kwargs): return "unload_test"
    def cleanup(self): return True
'''
        
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(plugin_code)
        
        # Load plugin
        success = self.plugin_manager.load_plugin_with_security(plugin_dir)
        assert success
        assert "unload_plugin" in self.plugin_manager.loaded_plugins
        
        # Unload plugin
        unload_success = self.plugin_manager.unload_plugin("unload_plugin")
        assert unload_success
        assert "unload_plugin" not in self.plugin_manager.loaded_plugins
        
        # Verify status report reflects unload
        report = self.plugin_manager.get_plugin_status_report()
        assert report["summary"]["total_plugins"] == 0
        assert "unload_plugin" not in report["plugins"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])