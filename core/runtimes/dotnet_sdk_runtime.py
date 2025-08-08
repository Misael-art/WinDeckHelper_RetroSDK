#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.NET SDK Runtime Implementation
Handles .NET SDK 8.0 installation, configuration, and validation.
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
    from version_manager import version_manager
except ImportError:
    # Fallback import for when running from different contexts
    from ..runtime_catalog_manager import Runtime, RuntimeConfig, ValidationResult, RuntimeStatus
    from ..version_manager import version_manager

try:
    import winreg
except ImportError:
    winreg = None


class DotNetSDKRuntime(Runtime):
    """.NET SDK runtime implementation with automatic configuration."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.dotnet_path = None
        self.installation_path = None
        
    def install(self) -> bool:
        """Install .NET SDK 8.0 with automatic configuration."""
        try:
            self.logger.info(f"Starting .NET SDK {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f".NET SDK {current_version} is already installed and compatible")
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
                self.configure_environment()
                self.logger.info(".NET SDK installation completed successfully")
                return True
            else:
                self.logger.error(".NET SDK installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during .NET SDK installation: {e}")
            return False
    
    def _download_installer(self) -> Optional[str]:
        """.NET SDK installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading .NET SDK installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"dotnet-sdk-{self.config.version}-installer.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f".NET SDK installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download .NET SDK installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run .NET SDK installer with silent installation parameters."""
        try:
            # .NET SDK silent installation parameters
            install_args = [
                installer_path,
                "/quiet",
                "/norestart"
            ]
            
            self.logger.info("Running .NET SDK installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info(".NET SDK installer completed successfully")
                return True
            else:
                self.logger.error(f".NET SDK installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(".NET SDK installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running .NET SDK installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure .NET SDK environment variables and PATH."""
        try:
            self.logger.info("Configuring .NET SDK environment...")
            
            # Find .NET installation path
            dotnet_path = self._find_dotnet_executable()
            if not dotnet_path:
                self.logger.error(".NET executable not found after installation")
                return False
            
            self.dotnet_path = dotnet_path
            self.installation_path = os.path.dirname(dotnet_path)
            
            # Configure environment variables
            self._configure_environment_variables()
            
            # Add .NET to PATH if not already there
            self._ensure_dotnet_in_path()
            
            self.logger.info(".NET SDK environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring .NET SDK environment: {e}")
            return False
    
    def _find_dotnet_executable(self) -> Optional[str]:
        """Find .NET executable in common installation locations."""
        common_paths = [
            r"C:\Program Files\dotnet\dotnet.exe",
            r"C:\Program Files (x86)\dotnet\dotnet.exe",
            os.path.expanduser(r"~\.dotnet\dotnet.exe")
        ]
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check PATH
        try:
            result = subprocess.run(
                ["where", "dotnet"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def _configure_environment_variables(self) -> None:
        """Configure .NET SDK environment variables."""
        try:
            if not self.installation_path:
                return
            
            # Set DOTNET_ROOT environment variable
            dotnet_root = self.installation_path
            
            # Set for current session
            os.environ['DOTNET_ROOT'] = dotnet_root
            
            # Try to set system environment variable (requires admin privileges)
            if winreg and platform.system() == "Windows":
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                        0,
                        winreg.KEY_ALL_ACCESS
                    ) as key:
                        winreg.SetValueEx(key, "DOTNET_ROOT", 0, winreg.REG_SZ, dotnet_root)
                        self.logger.info(f"Set DOTNET_ROOT system environment variable: {dotnet_root}")
                except Exception as e:
                    self.logger.warning(f"Could not set system DOTNET_ROOT (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error configuring environment variables: {e}")
    
    def _ensure_dotnet_in_path(self) -> None:
        """Ensure .NET is in system PATH."""
        try:
            if not self.installation_path:
                return
            
            # Check if already in PATH
            current_path = os.environ.get('PATH', '')
            if self.installation_path.lower() in current_path.lower():
                return
            
            # Add to PATH for current session
            os.environ['PATH'] = f"{self.installation_path};{current_path}"
            
            # Try to add to system PATH (requires admin privileges)
            if winreg and platform.system() == "Windows":
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                        0,
                        winreg.KEY_ALL_ACCESS
                    ) as key:
                        system_path, _ = winreg.QueryValueEx(key, "PATH")
                        if self.installation_path.lower() not in system_path.lower():
                            new_path = f"{system_path};{self.installation_path}"
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            self.logger.info("Added .NET to system PATH")
                except Exception as e:
                    self.logger.warning(f"Could not update system PATH (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error updating PATH: {e}")
    
    def validate_installation(self) -> ValidationResult:
        """Validate .NET SDK installation and configuration."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Check if .NET executable exists
            dotnet_path = self._find_dotnet_executable()
            if not dotnet_path:
                return ValidationResult(
                    is_valid=False,
                    issues=[".NET executable not found"],
                    recommendations=["Install .NET SDK using the runtime manager"]
                )
            
            # Check .NET version
            try:
                result = subprocess.run(
                    [dotnet_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_detected = result.stdout.strip()
                    
                    if not self._is_version_compatible(version_detected):
                        issues.append(f".NET SDK version {version_detected} is outdated")
                        recommendations.append(f"Update to .NET SDK {self.config.version} or later")
                else:
                    issues.append(".NET version check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append(".NET version check timed out")
            except Exception as e:
                issues.append(f"Error checking .NET version: {e}")
            
            # Check if .NET is in PATH
            try:
                result = subprocess.run(
                    ["dotnet", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    issues.append(".NET is not accessible from PATH")
                    recommendations.append("Add .NET to system PATH")
            except:
                issues.append(".NET is not accessible from PATH")
                recommendations.append("Add .NET to system PATH")
            
            # Check DOTNET_ROOT environment variable
            dotnet_root = os.environ.get('DOTNET_ROOT')
            if not dotnet_root:
                recommendations.append("Set DOTNET_ROOT environment variable")
            
            # Check SDK installation
            try:
                result = subprocess.run(
                    [dotnet_path, "--list-sdks"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    sdks = result.stdout.strip()
                    if not sdks:
                        issues.append("No .NET SDKs found")
                        recommendations.append("Install .NET SDK")
                else:
                    issues.append("Could not list .NET SDKs")
            except Exception as e:
                issues.append(f"Error checking .NET SDKs: {e}")
            
            is_valid = len(issues) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                version_detected=version_detected,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                issues=[f"Validation error: {e}"],
                recommendations=["Reinstall .NET SDK using the runtime manager"]
            )
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed .NET SDK version."""
        try:
            dotnet_path = self._find_dotnet_executable()
            if not dotnet_path:
                return None
            
            result = subprocess.run(
                [dotnet_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting .NET version: {e}")
            return None
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if installed version is compatible with requirements."""
        try:
            # Use centralized version manager for compatibility checking
            requirement = f">={self.config.version}"
            return version_manager.is_compatible(version, requirement)
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall .NET SDK (Windows-specific implementation)."""
        try:
            self.logger.info("Starting .NET SDK uninstallation...")
            
            # .NET SDK uninstallation is complex as it may have multiple versions
            # We'll use the official uninstall tool if available
            
            # Try to find .NET uninstall tool
            uninstall_tool_paths = [
                r"C:\Program Files\dotnet\dotnet-core-uninstall.exe",
                r"C:\Program Files (x86)\dotnet\dotnet-core-uninstall.exe"
            ]
            
            uninstall_tool = None
            for path in uninstall_tool_paths:
                if os.path.exists(path):
                    uninstall_tool = path
                    break
            
            if uninstall_tool:
                # List and remove SDK versions
                try:
                    # List SDKs
                    result = subprocess.run(
                        [uninstall_tool, "list"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        # Remove all SDKs (user can be more selective if needed)
                        result = subprocess.run(
                            [uninstall_tool, "remove", "--all-previews-but-latest", "--sdk"],
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if result.returncode == 0:
                            self.logger.info(".NET SDK uninstalled successfully")
                            return True
                        else:
                            self.logger.error(f".NET uninstall tool failed with code {result.returncode}")
                            return False
                            
                except Exception as e:
                    self.logger.error(f"Error using .NET uninstall tool: {e}")
                    return False
            else:
                # Fallback: try to remove via Windows Programs and Features
                self.logger.warning(".NET uninstall tool not found, manual uninstallation may be required")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during .NET SDK uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of .NET SDK installation."""
        try:
            validation = self.validate_installation()
            
            if not validation.is_valid:
                if validation.version_detected:
                    return RuntimeStatus.CORRUPTED
                else:
                    return RuntimeStatus.NOT_INSTALLED
            
            if validation.version_detected:
                if self._is_version_compatible(validation.version_detected):
                    return RuntimeStatus.INSTALLED
                else:
                    return RuntimeStatus.OUTDATED
            
            return RuntimeStatus.NOT_INSTALLED
            
        except Exception as e:
            self.logger.error(f"Error getting .NET SDK status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing DotNetSDKRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="dotnet_sdk",
        version="8.0",
        download_url="https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/a7de3d8d6f4c8e9c6e8b8c8f8e8f8e8f/dotnet-sdk-8.0.404-win-x64.exe",
        mirrors=[
            "https://dotnet.microsoft.com/download/dotnet/8.0",
            "https://github.com/dotnet/core/releases"
        ],
        installation_type=InstallationType.EXE,
        environment_variables={
            "DOTNET_ROOT": "%ProgramFiles%\\dotnet"
        },
        validation_commands=["dotnet --version"],
        executable_paths=["dotnet.exe"],
        size_mb=200,
        description=".NET SDK 8.0"
    )
    
    dotnet_runtime = DotNetSDKRuntime(config)
    
    # Test version detection
    version = dotnet_runtime.get_installed_version()
    print(f"Installed .NET SDK version: {version}")
    
    # Test validation
    validation = dotnet_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = dotnet_runtime.get_status()
    print(f".NET SDK status: {status}")
    
    print("DotNetSDKRuntime test completed!")