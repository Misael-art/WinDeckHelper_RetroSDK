#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PowerShell 7 Runtime Implementation
Handles PowerShell 7 installation, configuration, and validation.
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
from ..version_manager import version_manager

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from runtime_catalog_manager import Runtime, RuntimeConfig, ValidationResult, RuntimeStatus
except ImportError:
    # Fallback import for when running from different contexts
    from ..runtime_catalog_manager import Runtime, RuntimeConfig, ValidationResult, RuntimeStatus

try:
    import winreg
except ImportError:
    winreg = None


class PowerShell7Runtime(Runtime):
    """PowerShell 7 runtime implementation with backward compatibility."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.pwsh_path = None
        self.installation_path = None
        
    def install(self) -> bool:
        """Install PowerShell 7 with automatic configuration."""
        try:
            self.logger.info(f"Starting PowerShell 7 {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f"PowerShell 7 {current_version} is already installed and compatible")
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
                self.logger.info("PowerShell 7 installation completed successfully")
                return True
            else:
                self.logger.error("PowerShell 7 installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during PowerShell 7 installation: {e}")
            return False
    
    def _download_installer(self) -> Optional[str]:
        """Download PowerShell 7 installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading PowerShell 7 installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"powershell-{self.config.version}-installer.msi")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f"PowerShell 7 installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download PowerShell 7 installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run PowerShell 7 installer with silent installation parameters."""
        try:
            # PowerShell 7 MSI silent installation parameters
            install_args = [
                "msiexec",
                "/i", installer_path,
                "/quiet",
                "/norestart",
                "ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1",
                "ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=1",
                "ENABLE_PSREMOTING=1",
                "REGISTER_MANIFEST=1",
                "USE_MU=1",
                "ENABLE_MU=1"
            ]
            
            self.logger.info("Running PowerShell 7 installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("PowerShell 7 installer completed successfully")
                return True
            else:
                self.logger.error(f"PowerShell 7 installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("PowerShell 7 installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running PowerShell 7 installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure PowerShell 7 environment and profiles."""
        try:
            self.logger.info("Configuring PowerShell 7 environment...")
            
            # Find PowerShell 7 installation path
            pwsh_path = self._find_pwsh_executable()
            if not pwsh_path:
                self.logger.error("PowerShell 7 executable not found after installation")
                return False
            
            self.pwsh_path = pwsh_path
            self.installation_path = os.path.dirname(pwsh_path)
            
            # Add PowerShell 7 to PATH if not already there
            self._ensure_pwsh_in_path()
            
            # Configure PowerShell profiles
            self._configure_powershell_profiles()
            
            # Set up execution policy
            self._configure_execution_policy()
            
            self.logger.info("PowerShell 7 environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring PowerShell 7 environment: {e}")
            return False
    
    def _find_pwsh_executable(self) -> Optional[str]:
        """Find PowerShell 7 executable in common installation locations."""
        common_paths = [
            r"C:\Program Files\PowerShell\7\pwsh.exe",
            r"C:\Program Files (x86)\PowerShell\7\pwsh.exe"
        ]
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check for any PowerShell 7 installation
        program_files_paths = [
            r"C:\Program Files\PowerShell",
            r"C:\Program Files (x86)\PowerShell"
        ]
        
        for base_path in program_files_paths:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        pwsh_exe = os.path.join(item_path, "pwsh.exe")
                        if os.path.exists(pwsh_exe):
                            return pwsh_exe
        
        # Check PATH
        try:
            result = subprocess.run(
                ["where", "pwsh"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def _ensure_pwsh_in_path(self) -> None:
        """Ensure PowerShell 7 is in system PATH."""
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
                            self.logger.info("Added PowerShell 7 to system PATH")
                except Exception as e:
                    self.logger.warning(f"Could not update system PATH (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error updating PATH: {e}")
    
    def _configure_powershell_profiles(self) -> None:
        """Configure PowerShell 7 profiles for better user experience."""
        try:
            if not self.pwsh_path:
                return
            
            # Get PowerShell profile paths
            result = subprocess.run(
                [self.pwsh_path, "-Command", "$PROFILE"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                profile_path = result.stdout.strip()
                
                # Create profile directory if it doesn't exist
                profile_dir = os.path.dirname(profile_path)
                os.makedirs(profile_dir, exist_ok=True)
                
                # Create basic profile if it doesn't exist
                if not os.path.exists(profile_path):
                    basic_profile = """# PowerShell 7 Profile
# Auto-generated by Environment Dev Runtime Manager

# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Enable tab completion
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView

# Set execution policy for current user (if not already set)
try {
    if ((Get-ExecutionPolicy -Scope CurrentUser) -eq 'Undefined') {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    }
} catch {
    # Ignore errors if we don't have permission
}

# Welcome message
Write-Host "PowerShell 7 - Environment Dev Runtime" -ForegroundColor Green
"""
                    
                    try:
                        with open(profile_path, 'w', encoding='utf-8') as f:
                            f.write(basic_profile)
                        self.logger.info(f"Created PowerShell 7 profile: {profile_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not create PowerShell profile: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Error configuring PowerShell profiles: {e}")
    
    def _configure_execution_policy(self) -> None:
        """Configure PowerShell execution policy for better usability."""
        try:
            if not self.pwsh_path:
                return
            
            # Set execution policy to RemoteSigned for CurrentUser scope
            # This allows local scripts to run while requiring remote scripts to be signed
            result = subprocess.run(
                [self.pwsh_path, "-Command", 
                 "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("Set PowerShell execution policy to RemoteSigned for CurrentUser")
            else:
                self.logger.warning("Could not set PowerShell execution policy")
                
        except Exception as e:
            self.logger.warning(f"Error configuring execution policy: {e}")
    
    def validate_installation(self) -> ValidationResult:
        """Validate PowerShell 7 installation and configuration."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Check if PowerShell 7 executable exists
            pwsh_path = self._find_pwsh_executable()
            if not pwsh_path:
                return ValidationResult(
                    is_valid=False,
                    issues=["PowerShell 7 executable not found"],
                    recommendations=["Install PowerShell 7 using the runtime manager"]
                )
            
            # Check PowerShell 7 version
            try:
                result = subprocess.run(
                    [pwsh_path, "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_detected = result.stdout.strip()
                    
                    if not self._is_version_compatible(version_detected):
                        issues.append(f"PowerShell 7 version {version_detected} is outdated")
                        recommendations.append(f"Update to PowerShell 7 {self.config.version} or later")
                else:
                    issues.append("PowerShell 7 version check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append("PowerShell 7 version check timed out")
            except Exception as e:
                issues.append(f"Error checking PowerShell 7 version: {e}")
            
            # Check if PowerShell 7 is in PATH
            try:
                result = subprocess.run(
                    ["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    issues.append("PowerShell 7 is not accessible from PATH")
                    recommendations.append("Add PowerShell 7 to system PATH")
            except:
                issues.append("PowerShell 7 is not accessible from PATH")
                recommendations.append("Add PowerShell 7 to system PATH")
            
            # Check execution policy
            try:
                result = subprocess.run(
                    [pwsh_path, "-Command", "Get-ExecutionPolicy -Scope CurrentUser"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    execution_policy = result.stdout.strip()
                    if execution_policy in ["Restricted", "Undefined"]:
                        recommendations.append("Set PowerShell execution policy to RemoteSigned or Unrestricted")
                else:
                    recommendations.append("Check PowerShell execution policy settings")
            except Exception as e:
                recommendations.append("Check PowerShell execution policy settings")
            
            # Check for profile
            try:
                result = subprocess.run(
                    [pwsh_path, "-Command", "Test-Path $PROFILE"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip().lower() == "false":
                    recommendations.append("Create PowerShell profile for better user experience")
            except:
                pass
            
            # Check backward compatibility with Windows PowerShell
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "$PSVersionTable.PSVersion.Major"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode == 0:
                    ps_version = result.stdout.strip()
                    if int(ps_version) < 5:
                        recommendations.append("Consider updating Windows PowerShell for better compatibility")
            except:
                recommendations.append("Windows PowerShell not found - PowerShell 7 provides backward compatibility")
            
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
                recommendations=["Reinstall PowerShell 7 using the runtime manager"]
            )
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed PowerShell 7 version."""
        try:
            pwsh_path = self._find_pwsh_executable()
            if not pwsh_path:
                return None
            
            result = subprocess.run(
                [pwsh_path, "-Command", "$PSVersionTable.PSVersion.ToString()"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting PowerShell 7 version: {e}")
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
        """Uninstall PowerShell 7 (Windows-specific implementation)."""
        try:
            self.logger.info("Starting PowerShell 7 uninstallation...")
            
            # PowerShell 7 uninstallation via Windows Programs and Features
            if winreg and platform.system() == "Windows":
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
                                        if "PowerShell" in display_name and "7" in display_name:
                                            uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                            
                                            # Run uninstall command
                                            if "msiexec" in uninstall_string.lower():
                                                # MSI uninstall
                                                cmd_parts = uninstall_string.split()
                                                cmd_parts.extend(["/quiet", "/norestart"])
                                            else:
                                                # EXE uninstall
                                                cmd_parts = [uninstall_string, "/S"]
                                            
                                            result = subprocess.run(
                                                cmd_parts,
                                                capture_output=True,
                                                text=True,
                                                timeout=300
                                            )
                                            
                                            if result.returncode == 0:
                                                self.logger.info("PowerShell 7 uninstalled successfully")
                                                return True
                                            else:
                                                self.logger.error(f"PowerShell 7 uninstaller failed with code {result.returncode}")
                                                return False
                                    except FileNotFoundError:
                                        pass
                                i += 1
                            except OSError:
                                break
                    
                    self.logger.error("PowerShell 7 uninstall entry not found in registry")
                    return False
                    
                except Exception as e:
                    self.logger.error(f"Error searching registry for PowerShell 7 uninstaller: {e}")
                    return False
            else:
                self.logger.error("PowerShell 7 uninstallation not supported on this platform")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during PowerShell 7 uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of PowerShell 7 installation."""
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
            self.logger.error(f"Error getting PowerShell 7 status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing PowerShell7Runtime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="powershell7",
        version="7.4.6",
        download_url="https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/PowerShell-7.4.6-win-x64.msi",
        mirrors=[
            "https://github.com/PowerShell/PowerShell/releases/latest"
        ],
        installation_type=InstallationType.MSI,
        validation_commands=["pwsh --version"],
        executable_paths=["pwsh.exe"],
        size_mb=100,
        description="PowerShell 7"
    )
    
    powershell7_runtime = PowerShell7Runtime(config)
    
    # Test version detection
    version = powershell7_runtime.get_installed_version()
    print(f"Installed PowerShell 7 version: {version}")
    
    # Test validation
    validation = powershell7_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = powershell7_runtime.get_status()
    print(f"PowerShell 7 status: {status}")
    
    print("PowerShell7Runtime test completed!")