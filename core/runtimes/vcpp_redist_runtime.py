#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual C++ Redistributables Runtime Implementation
Handles Visual C++ Redistributables 2015-2022 installation, configuration, and validation.
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


class VCppRedistRuntime(Runtime):
    """Visual C++ Redistributables runtime implementation with registry-based detection."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.installed_versions = {}
        
    def install(self) -> bool:
        """Install Visual C++ Redistributables with automatic configuration."""
        try:
            self.logger.info(f"Starting Visual C++ Redistributables {self.config.version} installation...")
            
            # Check if already installed and up to date
            if self._check_existing_installation():
                self.logger.info("Visual C++ Redistributables are already installed and up to date")
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
                self.logger.info("Visual C++ Redistributables installation completed successfully")
                return True
            else:
                self.logger.error("Visual C++ Redistributables installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Visual C++ Redistributables installation: {e}")
            return False
    
    def _check_existing_installation(self) -> bool:
        """Check if Visual C++ Redistributables are already installed."""
        try:
            installed_versions = self._get_installed_versions()
            
            # Check for required versions (2015-2022 are unified)
            required_versions = ["2015", "2017", "2019", "2022"]
            
            for version in required_versions:
                if not any(version in v for v in installed_versions):
                    # Check for unified 2015-2022 redistributable
                    if not any("14." in v for v in installed_versions):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking existing installation: {e}")
            return False
    
    def _get_installed_versions(self) -> List[str]:
        """Get list of installed Visual C++ Redistributable versions from registry."""
        installed_versions = []
        
        if not winreg or platform.system() != "Windows":
            return installed_versions
        
        # Registry paths to check for VC++ redistributables
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    if "Uninstall" in path:
                        # Search through uninstall entries
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                        if "Microsoft Visual C++" in display_name and "Redistributable" in display_name:
                                            installed_versions.append(display_name)
                                    except FileNotFoundError:
                                        pass
                                i += 1
                            except OSError:
                                break
                    else:
                        # Direct VC runtime registry check
                        try:
                            version, _ = winreg.QueryValueEx(key, "Version")
                            installed, _ = winreg.QueryValueEx(key, "Installed")
                            if installed:
                                installed_versions.append(f"VC++ Runtime {version}")
                        except FileNotFoundError:
                            pass
                            
            except FileNotFoundError:
                continue
            except Exception as e:
                self.logger.warning(f"Error checking registry path {path}: {e}")
                continue
        
        return installed_versions
    
    def _download_installer(self) -> Optional[str]:
        """Download Visual C++ Redistributables installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading Visual C++ Redistributables installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"vc_redist_{self.config.version}.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f"Visual C++ Redistributables installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download Visual C++ Redistributables installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run Visual C++ Redistributables installer with silent installation parameters."""
        try:
            # Visual C++ Redistributables silent installation parameters
            install_args = [
                installer_path,
                "/quiet",
                "/norestart"
            ]
            
            self.logger.info("Running Visual C++ Redistributables installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # VC++ redistributables return different codes
            # 0 = success, 1638 = already installed, 3010 = success but reboot required
            if result.returncode in [0, 1638, 3010]:
                if result.returncode == 1638:
                    self.logger.info("Visual C++ Redistributables already installed")
                elif result.returncode == 3010:
                    self.logger.info("Visual C++ Redistributables installed successfully (reboot recommended)")
                else:
                    self.logger.info("Visual C++ Redistributables installer completed successfully")
                return True
            else:
                self.logger.error(f"Visual C++ Redistributables installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Visual C++ Redistributables installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running Visual C++ Redistributables installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure Visual C++ Redistributables environment (minimal configuration needed)."""
        try:
            self.logger.info("Configuring Visual C++ Redistributables environment...")
            
            # Visual C++ Redistributables don't require special environment configuration
            # They install system-wide DLLs that are automatically found by applications
            
            # Verify installation by checking registry
            installed_versions = self._get_installed_versions()
            if installed_versions:
                self.logger.info(f"Found {len(installed_versions)} Visual C++ Redistributable installations")
                for version in installed_versions:
                    self.logger.info(f"  - {version}")
                return True
            else:
                self.logger.warning("No Visual C++ Redistributables found after installation")
                return False
            
        except Exception as e:
            self.logger.error(f"Error configuring Visual C++ Redistributables environment: {e}")
            return False
    
    def validate_installation(self) -> ValidationResult:
        """Validate Visual C++ Redistributables installation."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Get installed versions from registry
            installed_versions = self._get_installed_versions()
            
            if not installed_versions:
                return ValidationResult(
                    is_valid=False,
                    issues=["No Visual C++ Redistributables found"],
                    recommendations=["Install Visual C++ Redistributables using the runtime manager"]
                )
            
            # Check for essential versions
            essential_versions = ["2015", "2017", "2019", "2022"]
            found_versions = []
            
            for version in essential_versions:
                if any(version in v for v in installed_versions):
                    found_versions.append(version)
                elif any("14." in v for v in installed_versions):
                    # Unified 2015-2022 redistributable
                    found_versions.append(version)
            
            if found_versions:
                version_detected = ", ".join(found_versions)
            
            # Check for missing essential versions
            missing_versions = [v for v in essential_versions if v not in found_versions]
            if missing_versions:
                issues.append(f"Missing Visual C++ Redistributables: {', '.join(missing_versions)}")
                recommendations.append("Install missing Visual C++ Redistributable versions")
            
            # Check for both x64 and x86 versions
            x64_found = any("x64" in v.lower() for v in installed_versions)
            x86_found = any("x86" in v.lower() for v in installed_versions)
            
            if not x64_found:
                recommendations.append("Install x64 version of Visual C++ Redistributables")
            if not x86_found:
                recommendations.append("Install x86 version of Visual C++ Redistributables for 32-bit compatibility")
            
            # Check registry integrity
            try:
                self._check_registry_integrity()
            except Exception as e:
                issues.append(f"Registry integrity check failed: {e}")
                recommendations.append("Repair or reinstall Visual C++ Redistributables")
            
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
                recommendations=["Reinstall Visual C++ Redistributables using the runtime manager"]
            )
    
    def _check_registry_integrity(self) -> None:
        """Check registry integrity for Visual C++ Redistributables."""
        if not winreg or platform.system() != "Windows":
            return
        
        # Check key registry entries
        registry_checks = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86")
        ]
        
        for hkey, path in registry_checks:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    # Check for required values
                    version, _ = winreg.QueryValueEx(key, "Version")
                    installed, _ = winreg.QueryValueEx(key, "Installed")
                    
                    if not installed:
                        raise Exception(f"Registry indicates {path} is not installed")
                        
            except FileNotFoundError:
                # This is expected if the specific version is not installed
                pass
            except Exception as e:
                raise Exception(f"Registry check failed for {path}: {e}")
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed Visual C++ Redistributables versions."""
        try:
            installed_versions = self._get_installed_versions()
            
            if installed_versions:
                # Return a summary of installed versions
                version_summary = []
                for version in installed_versions:
                    # Extract version info
                    if "2015" in version or "2017" in version or "2019" in version or "2022" in version:
                        if "2015" in version:
                            version_summary.append("2015")
                        if "2017" in version:
                            version_summary.append("2017")
                        if "2019" in version:
                            version_summary.append("2019")
                        if "2022" in version:
                            version_summary.append("2022")
                    elif "14." in version:
                        version_summary.append("2015-2022")
                
                # Remove duplicates and return
                unique_versions = list(set(version_summary))
                return ", ".join(sorted(unique_versions))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Visual C++ Redistributables version: {e}")
            return None
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if installed version is compatible with requirements."""
        try:
            # For Visual C++ Redistributables, we need 2015-2022 versions
            required_versions = ["2015", "2017", "2019", "2022"]
            
            # Check if any required version is present
            for req_version in required_versions:
                if req_version in version:
                    return True
            
            # Also check for unified 2015-2022 version
            if "2015-2022" in version:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall Visual C++ Redistributables (Windows-specific implementation)."""
        try:
            self.logger.info("Starting Visual C++ Redistributables uninstallation...")
            
            # Visual C++ Redistributables uninstallation is complex
            # We'll search for uninstall entries in the registry
            
            if not winreg or platform.system() != "Windows":
                self.logger.error("Visual C++ Redistributables uninstallation not supported on this platform")
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
                                    if ("Microsoft Visual C++" in display_name and 
                                        "Redistributable" in display_name):
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
                    self.logger.info(f"Successfully uninstalled {success_count} Visual C++ Redistributable(s)")
                    return True
                else:
                    self.logger.error("Failed to uninstall any Visual C++ Redistributables")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error searching for Visual C++ Redistributables uninstall entries: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Visual C++ Redistributables uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of Visual C++ Redistributables installation."""
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
            self.logger.error(f"Error getting Visual C++ Redistributables status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing VCppRedistRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="vcpp_redist",
        version="2015-2022",
        download_url="https://aka.ms/vs/17/release/vc_redist.x64.exe",
        mirrors=[
            "https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist"
        ],
        installation_type=InstallationType.EXE,
        validation_commands=[],
        registry_keys=[
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64",
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64"
        ],
        size_mb=25,
        description="Visual C++ Redistributable 2015-2022"
    )
    
    vcpp_runtime = VCppRedistRuntime(config)
    
    # Test version detection
    version = vcpp_runtime.get_installed_version()
    print(f"Installed Visual C++ Redistributables versions: {version}")
    
    # Test validation
    validation = vcpp_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = vcpp_runtime.get_status()
    print(f"Visual C++ Redistributables status: {status}")
    
    print("VCppRedistRuntime test completed!")