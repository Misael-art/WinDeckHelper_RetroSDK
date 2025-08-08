#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Node.js Runtime Implementation
Handles Node.js LTS installation, configuration, and validation with npm support.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.request import urlretrieve
from urllib.error import URLError

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from runtime_catalog_manager import Runtime, RuntimeConfig, ValidationResult, RuntimeStatus
except ImportError:
    # Fallback import for when running from different contexts
    from ..runtime_catalog_manager import Runtime, RuntimeConfig, ValidationResult, RuntimeStatus

try:
    from version_manager import version_manager
except ImportError:
    from ..version_manager import version_manager

try:
    import winreg
except ImportError:
    winreg = None


class NodeJSRuntime(Runtime):
    """Node.js runtime implementation with npm package management."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.node_path = None
        self.npm_path = None
        self.installation_path = None
        
    def install(self) -> bool:
        """Install Node.js LTS with automatic configuration."""
        try:
            self.logger.info(f"Starting Node.js {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f"Node.js {current_version} is already installed and compatible")
                return True
            
            # Download installer
            installer_path = self._download_installer()
            if not installer_path:
                return False
            
            # Run installation
            success = self._run_installation(installer_path)
            
            # Cleanup
            try:
                os.unlink(installer_path)
            except:
                pass
            
            if success:
                # Configure environment after installation
                self._configure_environment()
                self.logger.info("Node.js installation completed successfully")
                return True
            else:
                self.logger.error("Node.js installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Node.js installation: {e}")
            return False
    
    def configure(self) -> bool:
        """Configure Node.js environment and npm settings."""
        try:
            self.logger.info("Configuring Node.js environment...")
            
            # Find Node.js installation
            if not self._find_node_installation():
                self.logger.error("Node.js installation not found")
                return False
            
            # Configure npm settings
            self._configure_npm()
            
            # Update PATH if needed
            self._update_system_path()
            
            # Verify configuration
            if self.validate().is_valid:
                self.logger.info("Node.js configuration completed successfully")
                return True
            else:
                self.logger.error("Node.js configuration validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Node.js configuration: {e}")
            return False
    
    def validate(self) -> ValidationResult:
        """Validate Node.js installation and configuration."""
        try:
            issues = []
            
            # Check Node.js executable
            node_version = self._check_command_version("node", "--version")
            if not node_version:
                issues.append("Node.js executable not found or not working")
            else:
                self.logger.info(f"Found Node.js version: {node_version}")
            
            # Check npm executable
            npm_version = self._check_command_version("npm", "--version")
            if not npm_version:
                issues.append("npm executable not found or not working")
            else:
                self.logger.info(f"Found npm version: {npm_version}")
            
            # Check if versions are compatible
            if node_version and not self._is_version_compatible(node_version):
                issues.append(f"Node.js version {node_version} is not compatible with required version {self.config.version}")
            
            # Check PATH configuration
            if not self._is_in_path("node"):
                issues.append("Node.js is not properly configured in system PATH")
            
            # Check npm global directory
            if not self._check_npm_global_config():
                issues.append("npm global configuration needs attention")
            
            return ValidationResult(
                is_valid=len(issues) == 0,
                issues=issues,
                version=node_version
            )
            
        except Exception as e:
            self.logger.error(f"Error during Node.js validation: {e}")
            return ValidationResult(
                is_valid=False,
                issues=[f"Validation error: {e}"],
                version=None
            )
    
    def uninstall(self) -> bool:
        """Uninstall Node.js and clean up configuration."""
        try:
            self.logger.info("Starting Node.js uninstallation...")
            
            # Find installation path
            if not self._find_node_installation():
                self.logger.warning("Node.js installation not found, nothing to uninstall")
                return True
            
            # Remove from PATH
            self._remove_from_system_path()
            
            # Clean up npm cache and global packages
            self._cleanup_npm_data()
            
            # Remove installation directory (if we installed it)
            if self.installation_path and os.path.exists(self.installation_path):
                try:
                    shutil.rmtree(self.installation_path)
                    self.logger.info(f"Removed Node.js installation directory: {self.installation_path}")
                except Exception as e:
                    self.logger.warning(f"Could not remove installation directory: {e}")
            
            self.logger.info("Node.js uninstallation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during Node.js uninstallation: {e}")
            return False
    
    def get_installed_version(self) -> Optional[str]:
        """Get the currently installed Node.js version."""
        return self._check_command_version("node", "--version")
    
    def get_status(self) -> RuntimeStatus:
        """Get current Node.js runtime status."""
        validation = self.validate()
        
        return RuntimeStatus(
            name=self.config.name,
            is_installed=validation.is_valid,
            version=validation.version,
            issues=validation.issues,
            installation_path=self.installation_path
        )
    
    # Private helper methods
    
    def _download_installer(self) -> Optional[str]:
        """Download Node.js installer."""
        try:
            # Determine architecture and installer type
            arch = "x64" if platform.machine().lower() in ["amd64", "x86_64"] else "x86"
            installer_name = f"node-v{self.config.version}-x{arch}.msi"
            
            # Build download URL
            base_url = self.config.download_url or f"https://nodejs.org/dist/v{self.config.version}/"
            download_url = f"{base_url}{installer_name}"
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, installer_name)
            
            self.logger.info(f"Downloading Node.js installer from: {download_url}")
            
            # Download with progress
            urlretrieve(download_url, installer_path)
            
            if os.path.exists(installer_path):
                self.logger.info(f"Node.js installer downloaded to: {installer_path}")
                return installer_path
            else:
                self.logger.error("Failed to download Node.js installer")
                return None
                
        except URLError as e:
            self.logger.error(f"Network error downloading Node.js installer: {e}")
            # Try mirrors if available
            return self._try_mirror_download()
        except Exception as e:
            self.logger.error(f"Error downloading Node.js installer: {e}")
            return None
    
    def _try_mirror_download(self) -> Optional[str]:
        """Try downloading from mirror URLs."""
        mirrors = getattr(self.config, 'mirrors', [])
        
        for mirror_url in mirrors:
            try:
                arch = "x64" if platform.machine().lower() in ["amd64", "x86_64"] else "x86"
                installer_name = f"node-v{self.config.version}-x{arch}.msi"
                download_url = f"{mirror_url}{installer_name}"
                
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, installer_name)
                
                self.logger.info(f"Trying mirror: {download_url}")
                urlretrieve(download_url, installer_path)
                
                if os.path.exists(installer_path):
                    self.logger.info(f"Successfully downloaded from mirror: {mirror_url}")
                    return installer_path
                    
            except Exception as e:
                self.logger.warning(f"Mirror {mirror_url} failed: {e}")
                continue
        
        self.logger.error("All download mirrors failed")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run the Node.js installer."""
        try:
            # Prepare installation command
            cmd = [
                "msiexec",
                "/i", installer_path,
                "/quiet",
                "/norestart",
                "ADDLOCAL=ALL"
            ]
            
            # Add custom installation path if specified
            if hasattr(self.config, 'installation_path') and self.config.installation_path:
                cmd.extend([f"INSTALLDIR={self.config.installation_path}"])
            
            self.logger.info(f"Running Node.js installer: {' '.join(cmd)}")
            
            # Run installer
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("Node.js installer completed successfully")
                return True
            else:
                self.logger.error(f"Node.js installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Node.js installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running Node.js installer: {e}")
            return False
    
    def _configure_environment(self) -> bool:
        """Configure Node.js environment variables and settings."""
        try:
            # Find Node.js installation
            if not self._find_node_installation():
                return False
            
            # Configure npm settings
            self._configure_npm()
            
            # Update system PATH
            self._update_system_path()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring Node.js environment: {e}")
            return False
    
    def _find_node_installation(self) -> bool:
        """Find Node.js installation paths."""
        try:
            # Common installation paths
            common_paths = [
                os.path.join(os.environ.get("ProgramFiles", ""), "nodejs"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "nodejs"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs"),
            ]
            
            # Check if node is in PATH
            node_path = shutil.which("node")
            if node_path:
                self.node_path = node_path
                self.installation_path = os.path.dirname(node_path)
                self.npm_path = shutil.which("npm")
                return True
            
            # Check common installation paths
            for path in common_paths:
                node_exe = os.path.join(path, "node.exe")
                npm_exe = os.path.join(path, "npm.cmd")
                
                if os.path.exists(node_exe):
                    self.node_path = node_exe
                    self.installation_path = path
                    if os.path.exists(npm_exe):
                        self.npm_path = npm_exe
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Node.js installation: {e}")
            return False
    
    def _configure_npm(self) -> bool:
        """Configure npm settings."""
        try:
            if not self.npm_path:
                return False
            
            # Set npm global directory to avoid permission issues
            npm_global_dir = os.path.join(os.environ.get("APPDATA", ""), "npm")
            
            # Configure npm settings
            npm_configs = [
                ("prefix", npm_global_dir),
                ("cache", os.path.join(npm_global_dir, "cache")),
                ("registry", "https://registry.npmjs.org/"),
            ]
            
            for key, value in npm_configs:
                try:
                    cmd = [self.npm_path, "config", "set", key, value]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        self.logger.warning(f"Failed to set npm config {key}: {result.stderr}")
                except Exception as e:
                    self.logger.warning(f"Error setting npm config {key}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring npm: {e}")
            return False
    
    def _update_system_path(self) -> bool:
        """Update system PATH to include Node.js."""
        try:
            if not self.installation_path:
                return False
            
            # Check if already in PATH
            if self._is_in_path("node"):
                return True
            
            # Add to PATH using Windows registry
            if winreg:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                        try:
                            current_path, _ = winreg.QueryValueEx(key, "PATH")
                        except FileNotFoundError:
                            current_path = ""
                        
                        if self.installation_path not in current_path:
                            new_path = f"{current_path};{self.installation_path}" if current_path else self.installation_path
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            self.logger.info(f"Added Node.js to PATH: {self.installation_path}")
                        
                        # Also add npm global directory
                        npm_global_dir = os.path.join(os.environ.get("APPDATA", ""), "npm")
                        if npm_global_dir not in current_path:
                            new_path = f"{new_path};{npm_global_dir}"
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            self.logger.info(f"Added npm global directory to PATH: {npm_global_dir}")
                        
                        return True
                        
                except Exception as e:
                    self.logger.warning(f"Could not update PATH via registry: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating system PATH: {e}")
            return False
    
    def _remove_from_system_path(self) -> bool:
        """Remove Node.js from system PATH."""
        try:
            if not winreg:
                return False
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                try:
                    current_path, _ = winreg.QueryValueEx(key, "PATH")
                    
                    # Remove Node.js paths
                    paths_to_remove = [
                        self.installation_path,
                        os.path.join(os.environ.get("APPDATA", ""), "npm")
                    ]
                    
                    path_parts = current_path.split(";")
                    new_path_parts = [p for p in path_parts if not any(remove_path in p for remove_path in paths_to_remove)]
                    new_path = ";".join(new_path_parts)
                    
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    self.logger.info("Removed Node.js from PATH")
                    return True
                    
                except FileNotFoundError:
                    return True  # PATH doesn't exist, nothing to remove
                    
        except Exception as e:
            self.logger.error(f"Error removing Node.js from PATH: {e}")
            return False
    
    def _cleanup_npm_data(self) -> bool:
        """Clean up npm cache and global packages."""
        try:
            if self.npm_path:
                # Clear npm cache
                try:
                    cmd = [self.npm_path, "cache", "clean", "--force"]
                    subprocess.run(cmd, capture_output=True, timeout=60)
                    self.logger.info("Cleared npm cache")
                except Exception as e:
                    self.logger.warning(f"Could not clear npm cache: {e}")
            
            # Remove npm global directory
            npm_global_dir = os.path.join(os.environ.get("APPDATA", ""), "npm")
            if os.path.exists(npm_global_dir):
                try:
                    shutil.rmtree(npm_global_dir)
                    self.logger.info("Removed npm global directory")
                except Exception as e:
                    self.logger.warning(f"Could not remove npm global directory: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up npm data: {e}")
            return False
    
    def _check_command_version(self, command: str, version_arg: str) -> Optional[str]:
        """Check if a command exists and get its version."""
        try:
            result = subprocess.run([command, version_arg], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output (remove 'v' prefix if present)
                version = result.stdout.strip()
                if version.startswith('v'):
                    version = version[1:]
                return version
            return None
        except Exception:
            return None
    
    def _is_version_compatible(self, installed_version: str) -> bool:
        """Check if installed version is compatible with required version."""
        try:
            # Remove 'v' prefix if present
            clean_installed = installed_version[1:] if installed_version.startswith('v') else installed_version
            clean_required = self.config.version[1:] if self.config.version.startswith('v') else self.config.version
            
            # Use centralized version manager for compatibility checking
            requirement = f">={clean_required}"
            return version_manager.is_compatible(clean_installed, requirement)
        except Exception as e:
            self.logger.warning(f"Error comparing versions: {e}")
            return False
    
    def _is_in_path(self, command: str) -> bool:
        """Check if a command is available in PATH."""
        return shutil.which(command) is not None
    
    def _check_npm_global_config(self) -> bool:
        """Check if npm global configuration is correct."""
        try:
            if not self.npm_path:
                return False
            
            # Check npm prefix
            result = subprocess.run([self.npm_path, "config", "get", "prefix"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                prefix = result.stdout.strip()
                expected_prefix = os.path.join(os.environ.get("APPDATA", ""), "npm")
                return os.path.normpath(prefix) == os.path.normpath(expected_prefix)
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking npm global config: {e}")
            return False


# Factory function for creating Node.js runtime instances
def create_nodejs_runtime(version: str = "20.11.0") -> NodeJSRuntime:
    """Create a Node.js runtime instance with default configuration."""
    config = RuntimeConfig(
        name="nodejs",
        version=version,
        download_url=f"https://nodejs.org/dist/v{version}/",
        mirrors=[
            "https://npm.taobao.org/mirrors/node/",
            "https://nodejs.org/download/release/",
        ],
        installation_type="msi",
        environment_variables={
            "NODE_ENV": "development"
        },
        dependencies=[],
        post_install_scripts=[],
        validation_commands=["node --version", "npm --version"]
    )
    
    return NodeJSRuntime(config)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create Node.js runtime
    nodejs = create_nodejs_runtime()
    
    # Install Node.js
    if nodejs.install():
        print("Node.js installation successful")
        
        # Validate installation
        validation = nodejs.validate()
        if validation.is_valid:
            print(f"Node.js validation successful - Version: {validation.version}")
        else:
            print(f"Node.js validation failed: {validation.issues}")
    else:
        print("Node.js installation failed")