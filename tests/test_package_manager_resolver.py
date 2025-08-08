"""
Unit tests for Package Manager Resolver.
Tests integration with npm, pip, conda for dependency resolution.
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from core.package_manager_resolver import (
    PackageManagerResolver, PackageManagerType, PackageInfo, PackageManagerCache
)


class TestPackageManagerCache(unittest.TestCase):
    """Test PackageManagerCache functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = PackageManagerCache(cache_duration=1)  # 1 second for testing
    
    def test_cache_expiration(self):
        """Test cache expiration logic."""
        package_info = PackageInfo(name="test-package", version="1.0.0")
        
        # Initially expired (not in cache)
        self.assertTrue(self.cache.is_expired("test-package"))
        
        # Add to cache
        self.cache.update_package("test-package", package_info)
        self.assertFalse(self.cache.is_expired("test-package"))
        
        # Should be retrievable
        cached_info = self.cache.get_package("test-package")
        self.assertIsNotNone(cached_info)
        self.assertEqual(cached_info.name, "test-package")
        
        # Wait for expiration (in real test, you might mock time)
        import time
        time.sleep(1.1)
        self.assertTrue(self.cache.is_expired("test-package"))
        
        # Should return None when expired
        expired_info = self.cache.get_package("test-package")
        self.assertIsNone(expired_info)


class TestPackageManagerResolver(unittest.TestCase):
    """Test PackageManagerResolver functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resolver = PackageManagerResolver()
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_is_manager_available_npm(self, mock_run_command):
        """Test npm availability detection."""
        # Mock successful npm version check
        mock_run_command.return_value = "8.19.2"
        
        is_available = await self.resolver._is_manager_available(PackageManagerType.NPM)
        self.assertTrue(is_available)
        
        # Should cache the result
        mock_run_command.reset_mock()
        is_available_cached = await self.resolver._is_manager_available(PackageManagerType.NPM)
        self.assertTrue(is_available_cached)
        mock_run_command.assert_not_called()  # Should use cached result
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_is_manager_available_failure(self, mock_run_command):
        """Test package manager availability detection failure."""
        # Mock failed command
        mock_run_command.return_value = None
        
        is_available = await self.resolver._is_manager_available(PackageManagerType.PIP)
        self.assertFalse(is_available)
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_get_npm_package_info(self, mock_run_command):
        """Test getting npm package information."""
        # Mock npm view response
        mock_response = {
            "name": "express",
            "version": "4.18.2",
            "description": "Fast, unopinionated, minimalist web framework",
            "dependencies": {
                "accepts": "~1.3.8",
                "array-flatten": "1.1.1"
            },
            "devDependencies": {
                "mocha": "^10.0.0"
            },
            "versions": ["4.18.0", "4.18.1", "4.18.2"],
            "dist-tags": {"latest": "4.18.2"},
            "homepage": "http://expressjs.com/",
            "repository": {"url": "git+https://github.com/expressjs/express.git"},
            "license": "MIT"
        }
        mock_run_command.return_value = json.dumps(mock_response)
        
        package_info = await self.resolver._get_npm_package_info("express")
        
        self.assertIsNotNone(package_info)
        self.assertEqual(package_info.name, "express")
        self.assertEqual(package_info.version, "4.18.2")
        self.assertEqual(package_info.description, "Fast, unopinionated, minimalist web framework")
        self.assertIn("accepts", package_info.dependencies)
        self.assertIn("mocha", package_info.dev_dependencies)
        self.assertEqual(package_info.latest_version, "4.18.2")
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_get_pip_package_info(self, mock_run_command):
        """Test getting pip package information."""
        # Mock pip show response
        mock_response = """Name: requests
Version: 2.28.1
Summary: Python HTTP for Humans.
Home-page: https://requests.readthedocs.io
License: Apache 2.0"""
        
        mock_run_command.return_value = mock_response
        
        # Mock get_pip_versions to return empty list for simplicity
        with patch.object(self.resolver, '_get_pip_versions', return_value=[]):
            package_info = await self.resolver._get_pip_package_info("requests")
        
        self.assertIsNotNone(package_info)
        self.assertEqual(package_info.name, "requests")
        self.assertEqual(package_info.version, "2.28.1")
        self.assertEqual(package_info.description, "Python HTTP for Humans.")
        self.assertEqual(package_info.homepage, "https://requests.readthedocs.io")
        self.assertEqual(package_info.license, "Apache 2.0")
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_get_npm_versions(self, mock_run_command):
        """Test getting available versions from npm."""
        # Mock npm view versions response
        mock_versions = ["1.0.0", "1.0.1", "1.1.0", "2.0.0"]
        mock_run_command.return_value = json.dumps(mock_versions)
        
        versions = await self.resolver._get_npm_versions("test-package")
        
        self.assertEqual(versions, mock_versions)
        mock_run_command.assert_called_with(["npm", "view", "test-package", "versions", "--json"])
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    async def test_get_conda_versions(self, mock_run_command):
        """Test getting available versions from conda."""
        # Mock conda search response
        mock_response = {
            "numpy": [
                {"version": "1.21.0"},
                {"version": "1.21.1"},
                {"version": "1.22.0"}
            ]
        }
        mock_run_command.return_value = json.dumps(mock_response)
        
        versions = await self.resolver._get_conda_versions("numpy")
        
        expected_versions = ["1.21.0", "1.21.1", "1.22.0"]
        self.assertEqual(versions, expected_versions)
    
    @patch('core.package_manager_resolver.PackageManagerResolver._is_manager_available')
    @patch('core.package_manager_resolver.PackageManagerResolver._get_package_info')
    async def test_resolve_dependencies_success(self, mock_get_package_info, mock_is_available):
        """Test successful dependency resolution."""
        # Mock manager availability
        mock_is_available.return_value = True
        
        # Mock package info
        mock_package_info = PackageInfo(
            name="express",
            version="4.18.2",
            dependencies={"accepts": "~1.3.8", "body-parser": "1.20.1"}
        )
        mock_get_package_info.return_value = mock_package_info
        
        # Mock recursive resolution
        with patch.object(self.resolver, '_resolve_recursive_dependencies') as mock_recursive:
            mock_recursive.return_value = [
                {"name": "accepts", "constraint": "~1.3.8", "type": "runtime", "depth": 1},
                {"name": "body-parser", "constraint": "1.20.1", "type": "runtime", "depth": 1}
            ]
            
            result = await self.resolver.resolve_dependencies("express", PackageManagerType.NPM)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["package_info"], mock_package_info)
        self.assertEqual(len(result["dependencies"]), 2)
    
    @patch('core.package_manager_resolver.PackageManagerResolver._is_manager_available')
    async def test_resolve_dependencies_manager_unavailable(self, mock_is_available):
        """Test dependency resolution when manager is unavailable."""
        mock_is_available.return_value = False
        
        result = await self.resolver.resolve_dependencies("express", PackageManagerType.NPM)
        
        self.assertFalse(result["success"])
        self.assertIn("not available", result["error"])
    
    @patch('core.package_manager_resolver.PackageManagerResolver.get_available_versions')
    async def test_find_compatible_version(self, mock_get_versions):
        """Test finding compatible version with constraints."""
        # Mock available versions
        mock_get_versions.return_value = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
        
        # Test finding compatible version
        compatible_version = await self.resolver.find_compatible_version(
            "test-package", PackageManagerType.NPM, [">=1.1.0", "<2.0.0"]
        )
        
        # Should find a version between 1.1.0 and 2.0.0
        self.assertIsNotNone(compatible_version)
        self.assertIn(compatible_version, ["1.1.0", "1.2.0"])
    
    @patch('core.package_manager_resolver.PackageManagerResolver.get_available_versions')
    async def test_find_compatible_version_no_match(self, mock_get_versions):
        """Test finding compatible version when no match exists."""
        # Mock available versions that don't match constraints
        mock_get_versions.return_value = ["0.9.0", "0.9.1"]
        
        compatible_version = await self.resolver.find_compatible_version(
            "test-package", PackageManagerType.NPM, [">=1.0.0"]
        )
        
        self.assertIsNone(compatible_version)
    
    async def test_check_dependency_conflicts_no_conflicts(self):
        """Test dependency conflict checking with no conflicts."""
        dependencies = {
            "dep1": "package-a>=1.0.0",
            "dep2": "package-b>=2.0.0"
        }
        
        with patch.object(self.resolver, 'get_available_versions') as mock_get_versions:
            mock_get_versions.return_value = ["1.0.0", "1.1.0", "2.0.0"]
            
            conflicts = await self.resolver.check_dependency_conflicts(
                dependencies, PackageManagerType.NPM
            )
        
        self.assertEqual(len(conflicts), 0)
    
    async def test_check_dependency_conflicts_with_conflicts(self):
        """Test dependency conflict checking with actual conflicts."""
        dependencies = {
            "dep1": "shared-lib>=1.0.0",
            "dep2": "shared-lib<=0.9.0"  # Conflicting constraint
        }
        
        with patch.object(self.resolver, 'get_available_versions') as mock_get_versions:
            mock_get_versions.return_value = ["0.8.0", "0.9.0", "1.0.0", "1.1.0"]
            
            conflicts = await self.resolver.check_dependency_conflicts(
                dependencies, PackageManagerType.NPM
            )
        
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]["package"], "shared-lib")
        self.assertIn(">=1.0.0", conflicts[0]["conflicting_constraints"])
        self.assertIn("<=0.9.0", conflicts[0]["conflicting_constraints"])
    
    def test_parse_dependency_string(self):
        """Test parsing of dependency strings."""
        # Test various formats
        test_cases = [
            ("package>=1.0.0", ("package", ">=1.0.0")),
            ("package==2.1.0", ("package", "==2.1.0")),
            ("package", ("package", "*")),
            ("my-package<=3.0.0", ("my-package", "<=3.0.0")),
            ("package_name>1.0.0", ("package_name", ">1.0.0"))
        ]
        
        for dep_string, expected in test_cases:
            with self.subTest(dep_string=dep_string):
                result = self.resolver._parse_dependency_string(dep_string)
                self.assertEqual(result, expected)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_run_command_success(self, mock_subprocess):
        """Test successful command execution."""
        # Mock subprocess
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"output", b"")
        mock_subprocess.return_value = mock_process
        
        result = await self.resolver._run_command(["echo", "test"])
        
        self.assertEqual(result, "output")
    
    @patch('asyncio.create_subprocess_exec')
    async def test_run_command_failure(self, mock_subprocess):
        """Test command execution failure."""
        # Mock subprocess failure
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"error")
        mock_subprocess.return_value = mock_process
        
        result = await self.resolver._run_command(["false"])
        
        self.assertIsNone(result)
    
    @patch('asyncio.create_subprocess_exec')
    async def test_run_command_timeout(self, mock_subprocess):
        """Test command execution timeout."""
        # Mock subprocess that times out
        mock_process = Mock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process
        
        result = await self.resolver._run_command(["sleep", "10"], timeout=1)
        
        self.assertIsNone(result)
    
    def test_cache_integration(self):
        """Test cache integration with package info retrieval."""
        # Create a package info
        package_info = PackageInfo(name="test-package", version="1.0.0")
        
        # Update cache
        self.resolver.cache.update_package("npm:test-package", package_info)
        
        # Should retrieve from cache
        cached_info = self.resolver.cache.get_package("npm:test-package")
        self.assertEqual(cached_info, package_info)
        
        # Clear cache
        self.resolver.clear_cache()
        
        # Should not be in cache anymore
        cleared_info = self.resolver.cache.get_package("npm:test-package")
        self.assertIsNone(cleared_info)


class TestPackageManagerResolverIntegration(unittest.TestCase):
    """Integration tests for PackageManagerResolver."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.resolver = PackageManagerResolver()
    
    def test_async_context_manager(self):
        """Test that async operations work correctly in sync context."""
        async def async_test():
            # Test that we can create and use the resolver in async context
            result = await self.resolver._is_manager_available(PackageManagerType.NPM)
            return isinstance(result, bool)
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_test())
            self.assertTrue(result)
        finally:
            loop.close()
    
    @patch('core.package_manager_resolver.PackageManagerResolver._run_command')
    def test_multiple_manager_detection(self, mock_run_command):
        """Test detection of multiple package managers."""
        async def async_test():
            # Mock different responses for different managers
            def side_effect(command, **kwargs):
                if command[0] == "npm":
                    return "8.19.2"
                elif command[0] == "pip":
                    return "22.3.1"
                elif command[0] == "conda":
                    return "4.14.0"
                else:
                    return None
            
            mock_run_command.side_effect = side_effect
            
            # Test detection of multiple managers
            npm_available = await self.resolver._is_manager_available(PackageManagerType.NPM)
            pip_available = await self.resolver._is_manager_available(PackageManagerType.PIP)
            conda_available = await self.resolver._is_manager_available(PackageManagerType.CONDA)
            yarn_available = await self.resolver._is_manager_available(PackageManagerType.YARN)
            
            return npm_available, pip_available, conda_available, yarn_available
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            npm, pip, conda, yarn = loop.run_until_complete(async_test())
            self.assertTrue(npm)
            self.assertTrue(pip)
            self.assertTrue(conda)
            self.assertFalse(yarn)  # Should be False since we didn't mock yarn
        finally:
            loop.close()


# Import json for mocking
import json

if __name__ == '__main__':
    unittest.main()