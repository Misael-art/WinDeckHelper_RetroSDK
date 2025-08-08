#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.NET Desktop Runtime Implementation
Handles .NET Desktop Runtime 8.0 and 9.0 installation, configuration, and validation.
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


class DotNetDesktopRuntime(Runtime):
    """.NET Desktop Runtime implementation with multiple version support."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.dotnet_path = None
        self.installation_path = None
        self.supported_versions = ["8.0", "9.0"]
        
    def install(self) -> bool:
        """Install .NET Desktop Runtime with automatic configuration."""
        try:
            self.logger.info(f"Starting .NET Desktop Runtime {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_versions = self.get_installed_versions()
            if current_versions and self._is_version_compatible(current_versions):
                self.logger.info(f".NET Desktop Runtime versions {current_versions} are already installed and compatible")
                return True
            
            # Install multiple versions if needed
            success = True
            for version in self.supported_versions:
                if not self._install_version(version):
                    success = False
            
            if success:
                # Configure environment after installation
                self.configure_environment()
                self.logger.info(".NET Desktop Runtime installation completed successfully")
                return True
            else:
                self.logger.error(".NET Desktop Runtime installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during .NET Desktop Runtime installation: {e}")
            return False
    
    def _install_version(self, version: str) -> bool:
        """Install a specific version of .NET Desktop Runtime."""
        try:
            self.logger.info(f"Installing .NET Desktop Runtime {version}...")
            
            # Get download URL for specific version
            download_url = self._get_version_download_url(version)
            if not download_url:
                self.logger.error(f"No download URL found for .NET Desktop Runtime {version}")
                return False
            
            # Download installer
            installer_path = self._download_installer(download_url, version)
            if not installer_path:
                return False
            
            # Run installation
            success = self._run_installation(installer_path, version)
            
            # Cleanup
            try:
                os.unlink(installer_path)
            except:
                pass
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error installing .NET Desktop Runtime {version}: {e}")
            return False
    
    def _get_version_download_url(self, version: str) -> Optional[str]:
        """Get download URL for specific .NET Desktop Runtime version."""
        version_urls = {
            "8.0": "https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/windowsdesktop-runtime-8.0.11-win-x64.exe",
            "9.0": "https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/windowsdesktop-runtime-9.0.0-win-x64.exe"
        }
        
        return version_urls.get(version, self.config.download_url)
    
    def _download_installer(self, download_url: str, version: str) -> Optional[str]:
        """Download .NET Desktop Runtime installer for specific version."""
        urls_to_try = [download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading .NET Desktop Runtime {version} installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"dotnet-desktop-runtime-{version}-installer.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f".NET Desktop Runtime {version} installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error(f"Failed to download .NET Desktop Runtime {version} installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str, version: str) -> bool:
        """Run .NET Desktop Runtime installer with silent installation parameters."""
        try:
            # .NET Desktop Runtime silent installation parameters
            install_args = [
                installer_path,
                "/quiet",
                "/norestart"
            ]
            
            self.logger.info(f"Running .NET Desktop Runtime {version} installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f".NET Desktop Runtime {version} installer completed successfully")
                return True
            else:
                self.logger.error(f".NET Desktop Runtime {version} installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f".NET Desktop Runtime {version} installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running .NET Desktop Runtime {version} installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure .NET Desktop Runtime environment."""
        try:
            self.logger.info("Configuring .NET Desktop Runtime environment...")
            
            # Find .NET installation path
            dotnet_path = self._find_dotnet_executable()
            if not dotnet_path:
                self.logger.error(".NET executable not found after installation")
                return False
            
            self.dotnet_path = dotnet_path
            self.installation_path = os.path.dirname(dotnet_path)
            
            # .NET Desktop Runtime doesn't require special environment configuration
            # It integrates with the existing .NET installation
            
            self.logger.info(".NET Desktop Runtime environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring .NET Desktop Runtime environment: {e}")
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
    
    def validate_installation(self) -> ValidationResult:
        """Validate .NET Desktop Runtime installation and configuration."""
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
                    recommendations=["Install .NET Desktop Runtime using the runtime manager"]
                )
            
            # Check installed runtimes
            try:
                result = subprocess.run(
                    [dotnet_path, "--list-runtimes"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    runtimes_output = result.stdout.strip()
                    
                    # Parse runtime information
                    desktop_runtimes = []
                    for line in runtimes_output.split('\n'):
                        if "Microsoft.WindowsDesktop.App" in line:
                            # Extract version from line like "Microsoft.WindowsDesktop.App 8.0.11 [C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App]"
                            parts = line.split()
                            if len(parts) >= 2:
                                desktop_runtimes.append(parts[1])
                    
                    if desktop_runtimes:
                        version_detected = ", ".join(desktop_runtimes)
                        
                        # Check if required versions are installed
                        missing_versions = []
                        for required_version in self.supported_versions:
                            if not any(runtime.startswith(required_version) for runtime in desktop_runtimes):
                                missing_versions.append(required_version)
                        
                        if missing_versions:
                            issues.append(f"Missing .NET Desktop Runtime versions: {', '.join(missing_versions)}")
                            recommendations.append(f"Install missing .NET Desktop Runtime versions: {', '.join(missing_versions)}")
                    else:
                        issues.append("No .NET Desktop Runtime found")
                        recommendations.append("Install .NET Desktop Runtime")
                else:
                    issues.append(".NET runtime list check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append(".NET runtime list check timed out")
            except Exception as e:
                issues.append(f"Error checking .NET runtimes: {e}")
            
            # Check if .NET is in PATH
            try:
                result = subprocess.run(
                    ["dotnet", "--list-runtimes"],
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
            
            # Check registry entries
            try:
                self._check_registry_entries()
            except Exception as e:
                issues.append(f"Registry check failed: {e}")
                recommendations.append("Repair .NET Desktop Runtime installation")
            
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
                recommendations=["Reinstall .NET Desktop Runtime using the runtime manager"]
            )
    
    def _check_registry_entries(self) -> None:
        """Check registry entries for .NET Desktop Runtime."""
        if not winreg or platform.system() != "Windows":
            return
        
        # Check key registry entries for .NET Desktop Runtime
        registry_paths = [
            r"SOFTWARE\WOW6432Node\dotnet\Setup\InstalledVersions\x64\sharedhost",
            r"SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost"
        ]
        
        for path in registry_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    # Check if key exists and has values
                    try:
                        version, _ = winreg.QueryValueEx(key, "Version")
                        if version:
                            return  # Found valid registry entry
                    except FileNotFoundError:
                        pass
            except FileNotFoundError:
                continue
        
        # If we get here, no valid registry entries were found
        raise Exception("No valid .NET Desktop Runtime registry entries found")
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed .NET Desktop Runtime version."""
        return self.get_installed_versions()
    
    def get_installed_versions(self) -> Optional[str]:
        """Get all currently installed .NET Desktop Runtime versions."""
        try:
            dotnet_path = self._find_dotnet_executable()
            if not dotnet_path:
                return None
            
            result = subprocess.run(
                [dotnet_path, "--list-runtimes"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                runtimes_output = result.stdout.strip()
                
                # Parse runtime information
                desktop_runtimes = []
                for line in runtimes_output.split('\n'):
                    if "Microsoft.WindowsDesktop.App" in line:
                        # Extract version from line like "Microsoft.WindowsDesktop.App 8.0.11 [C:\Program Files\dotnet\shared\Microsoft.WindowsDesktop.App]"
                        parts = line.split()
                        if len(parts) >= 2:
                            desktop_runtimes.append(parts[1])
                
                if desktop_runtimes:
                    return ", ".join(desktop_runtimes)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting .NET Desktop Runtime versions: {e}")
            return None
    
    def _is_version_compatible(self, versions: str) -> bool:
        """Check if installed versions are compatible with requirements."""
        try:
            if not versions:
                return False
            
            # For .NET Desktop Runtime, we check if any installed version meets requirements
            # versions is a comma-separated string like "6.0.25, 8.0.1"
            installed_versions = [v.strip() for v in versions.split(", ")]
            requirement = f">={self.config.version}"
            
            for version in installed_versions:
                # Use centralized version manager for compatibility checking
                if version_manager.is_compatible(version, requirement):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall .NET Desktop Runtime (Windows-specific implementation)."""
        try:
            self.logger.info("Starting .NET Desktop Runtime uninstallation...")
            
            # .NET Desktop Runtime uninstallation is complex as it's part of the .NET ecosystem
            # We'll search for uninstall entries in the registry
            
            if not winreg or platform.system() != "Windows":
                self.logger.error(".NET Desktop Runtime uninstallation not supported on this platform")
                return False
            
            uninstall_commands = []
            
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                ) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                    if ("Microsoft .NET" in display_name and 
                                        "Desktop Runtime" in display_name):
                                        uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                        uninstall_commands.append((display_name, uninstall_string))
                                except FileNotFoundError:
                                    pass
                            i += 1
                        except OSError:
                            break
                
                # Execute uninstall commands
                success_count = 0
                for display_name, uninstall_cmd in uninstall_commands:
                    try:
                        self.logger.info(f"Uninstalling: {display_name}")
                        
                        # Parse uninstall command and add silent flags
                        if "msiexec" in uninstall_cmd.lower():
                            # MSI uninstall
                            cmd_parts = uninstall_cmd.split()
                            cmd_parts.extend(["/quiet", "/norestart"])
                        else:
                            # EXE uninstall
                            cmd_parts = [uninstall_cmd, "/quiet"]
                        
                        result = subprocess.run(
                            cmd_parts,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        if result.returncode in [0, 1605, 3010]:  # Success codes
                            success_count += 1
                            self.logger.info(f"Successfully uninstalled: {display_name}")
                        else:
                            self.logger.warning(f"Failed to uninstall {display_name}: code {result.returncode}")
                            
                    except Exception as e:
                        self.logger.warning(f"Error uninstalling {display_name}: {e}")
                        continue
                
                if success_count > 0:
                    self.logger.info(f"Successfully uninstalled {success_count} .NET Desktop Runtime(s)")
                    return True
                else:
                    self.logger.error("Failed to uninstall any .NET Desktop Runtimes")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error searching for .NET Desktop Runtime uninstall entries: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during .NET Desktop Runtime uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of .NET Desktop Runtime installation."""
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
            self.logger.error(f"Error getting .NET Desktop Runtime status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing DotNetDesktopRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="dotnet_desktop",
        version="8.0",
        download_url="https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/windowsdesktop-runtime-8.0.11-win-x64.exe",
        mirrors=[
            "https://dotnet.microsoft.com/download/dotnet/8.0"
        ],
        installation_type=InstallationType.EXE,
        validation_commands=["dotnet --list-runtimes"],
        registry_keys=["HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\dotnet\\Setup\\InstalledVersions\\x64\\sharedhost"],
        size_mb=50,
        description=".NET Desktop Runtime 8.0"
    )
    
    dotnet_desktop_runtime = DotNetDesktopRuntime(config)
    
    # Test version detection
    versions = dotnet_desktop_runtime.get_installed_versions()
    print(f"Installed .NET Desktop Runtime versions: {versions}")
    
    # Test validation
    validation = dotnet_desktop_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = dotnet_desktop_runtime.get_status()
    print(f".NET Desktop Runtime status: {status}")
    
    print("DotNetDesktopRuntime test completed!")