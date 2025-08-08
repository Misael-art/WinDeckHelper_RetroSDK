#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Anaconda Runtime Implementation
Handles Anaconda3 installation, configuration, and validation.
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


class AnacondaRuntime(Runtime):
    """Anaconda runtime implementation with conda environment management."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.conda_path = None
        self.python_path = None
        self.anaconda_path = None
        
    def install(self) -> bool:
        """Install Anaconda3 with automatic configuration."""
        try:
            self.logger.info(f"Starting Anaconda {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f"Anaconda {current_version} is already installed and compatible")
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
                self.logger.info("Anaconda installation completed successfully")
                return True
            else:
                self.logger.error("Anaconda installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Anaconda installation: {e}")
            return False
    
    def _download_installer(self) -> Optional[str]:
        """Download Anaconda installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading Anaconda installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"anaconda-{self.config.version}-installer.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f"Anaconda installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download Anaconda installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run Anaconda installer with silent installation parameters."""
        try:
            # Anaconda silent installation parameters
            install_args = [
                installer_path,
                "/InstallationType=AllUsers",
                "/RegisterPython=1",
                "/S",  # Silent installation
                "/AddToPath=1",
                "/D=C:\\ProgramData\\Anaconda3"  # Default installation directory
            ]
            
            self.logger.info("Running Anaconda installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout (Anaconda is large)
            )
            
            if result.returncode == 0:
                self.logger.info("Anaconda installer completed successfully")
                return True
            else:
                self.logger.error(f"Anaconda installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Anaconda installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running Anaconda installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure Anaconda environment variables and conda settings."""
        try:
            self.logger.info("Configuring Anaconda environment...")
            
            # Find Anaconda installation path
            anaconda_path = self._find_anaconda_installation()
            if not anaconda_path:
                self.logger.error("Anaconda installation not found after installation")
                return False
            
            self.anaconda_path = anaconda_path
            self.conda_path = os.path.join(anaconda_path, "Scripts", "conda.exe")
            self.python_path = os.path.join(anaconda_path, "python.exe")
            
            # Configure environment variables
            self._configure_environment_variables()
            
            # Add Anaconda to PATH if not already there
            self._ensure_anaconda_in_path()
            
            # Initialize conda
            self._initialize_conda()
            
            # Create default environment setup
            self._setup_default_environment()
            
            self.logger.info("Anaconda environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring Anaconda environment: {e}")
            return False
    
    def _find_anaconda_installation(self) -> Optional[str]:
        """Find Anaconda installation directory."""
        # Check common installation paths
        common_paths = [
            r"C:\ProgramData\Anaconda3",
            r"C:\Anaconda3",
            r"C:\Users\{}\Anaconda3".format(os.getenv('USERNAME', '')),
            r"C:\Users\{}\AppData\Local\Continuum\anaconda3".format(os.getenv('USERNAME', '')),
            os.path.expanduser(r"~\Anaconda3"),
            os.path.expanduser(r"~\anaconda3")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                # Check if this is a valid Anaconda installation
                conda_exe = os.path.join(path, "Scripts", "conda.exe")
                python_exe = os.path.join(path, "python.exe")
                if os.path.exists(conda_exe) and os.path.exists(python_exe):
                    return path
        
        # Check registry for Anaconda installation
        if winreg and platform.system() == "Windows":
            try:
                registry_paths = [
                    r"SOFTWARE\Python\ContinuumAnalytics",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                
                for reg_path in registry_paths:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                            if "Uninstall" in reg_path:
                                # Search through uninstall entries
                                i = 0
                                while True:
                                    try:
                                        subkey_name = winreg.EnumKey(key, i)
                                        with winreg.OpenKey(key, subkey_name) as subkey:
                                            try:
                                                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                                if "Anaconda" in display_name:
                                                    install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                                    if os.path.exists(install_location):
                                                        return install_location
                                            except FileNotFoundError:
                                                pass
                                        i += 1
                                    except OSError:
                                        break
                            else:
                                # Direct Anaconda registry check
                                anaconda_path, _ = winreg.QueryValueEx(key, "")
                                if os.path.exists(anaconda_path):
                                    return anaconda_path
                    except FileNotFoundError:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error checking registry for Anaconda: {e}")
        
        # Check PATH for conda
        try:
            result = subprocess.run(
                ["where", "conda"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                conda_path = result.stdout.strip().split('\n')[0]
                # Get parent directory (should be Scripts), then parent again (Anaconda root)
                anaconda_path = os.path.dirname(os.path.dirname(conda_path))
                if os.path.exists(anaconda_path):
                    return anaconda_path
        except:
            pass
        
        return None
    
    def _configure_environment_variables(self) -> None:
        """Configure Anaconda environment variables."""
        try:
            if not self.anaconda_path:
                return
            
            # Set CONDA_DEFAULT_ENV environment variable
            # Set for current session
            os.environ['CONDA_DEFAULT_ENV'] = 'base'
            
            # Try to set system environment variable (requires admin privileges)
            if winreg and platform.system() == "Windows":
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                        0,
                        winreg.KEY_ALL_ACCESS
                    ) as key:
                        winreg.SetValueEx(key, "CONDA_DEFAULT_ENV", 0, winreg.REG_SZ, "base")
                        self.logger.info("Set CONDA_DEFAULT_ENV system environment variable")
                except Exception as e:
                    self.logger.warning(f"Could not set system CONDA_DEFAULT_ENV (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error configuring environment variables: {e}")
    
    def _ensure_anaconda_in_path(self) -> None:
        """Ensure Anaconda is in system PATH."""
        try:
            if not self.anaconda_path:
                return
            
            # Anaconda paths to add
            paths_to_add = [
                self.anaconda_path,
                os.path.join(self.anaconda_path, "Scripts"),
                os.path.join(self.anaconda_path, "Library", "bin")
            ]
            
            current_path = os.environ.get('PATH', '')
            paths_added = []
            
            for path in paths_to_add:
                if path.lower() not in current_path.lower():
                    paths_added.append(path)
            
            if paths_added:
                # Add to PATH for current session
                new_paths = ";".join(paths_added)
                os.environ['PATH'] = f"{new_paths};{current_path}"
                
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
                            updated_path = f"{new_paths};{system_path}"
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, updated_path)
                            self.logger.info("Added Anaconda to system PATH")
                    except Exception as e:
                        self.logger.warning(f"Could not update system PATH (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error updating PATH: {e}")
    
    def _initialize_conda(self) -> None:
        """Initialize conda for shell integration."""
        try:
            if not self.conda_path or not os.path.exists(self.conda_path):
                return
            
            # Initialize conda for cmd and powershell
            init_commands = [
                [self.conda_path, "init", "cmd.exe"],
                [self.conda_path, "init", "powershell"]
            ]
            
            for cmd in init_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        self.logger.info(f"Successfully initialized conda for {cmd[-1]}")
                    else:
                        self.logger.warning(f"Failed to initialize conda for {cmd[-1]}")
                except Exception as e:
                    self.logger.warning(f"Error initializing conda for {cmd[-1]}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error initializing conda: {e}")
    
    def _setup_default_environment(self) -> None:
        """Set up default conda environment configuration."""
        try:
            if not self.conda_path or not os.path.exists(self.conda_path):
                return
            
            # Configure conda settings
            config_commands = [
                [self.conda_path, "config", "--set", "auto_activate_base", "true"],
                [self.conda_path, "config", "--set", "changeps1", "true"],
                [self.conda_path, "config", "--add", "channels", "conda-forge"]
            ]
            
            for cmd in config_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        self.logger.info(f"Successfully configured: {' '.join(cmd[2:])}")
                except Exception as e:
                    self.logger.warning(f"Error configuring conda: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error setting up default environment: {e}")
    
    def validate_installation(self) -> ValidationResult:
        """Validate Anaconda installation and configuration."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Check if Anaconda installation exists
            anaconda_path = self._find_anaconda_installation()
            if not anaconda_path:
                return ValidationResult(
                    is_valid=False,
                    issues=["Anaconda installation not found"],
                    recommendations=["Install Anaconda using the runtime manager"]
                )
            
            conda_exe = os.path.join(anaconda_path, "Scripts", "conda.exe")
            python_exe = os.path.join(anaconda_path, "python.exe")
            
            # Check conda version
            try:
                result = subprocess.run(
                    [conda_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    # Extract version from "conda 23.7.4"
                    if "conda" in version_output:
                        version_detected = version_output.split("conda ")[1].split()[0]
                        
                        if not self._is_version_compatible(version_detected):
                            issues.append(f"Anaconda version {version_detected} is outdated")
                            recommendations.append(f"Update to Anaconda {self.config.version} or later")
                else:
                    issues.append("Conda version check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append("Conda version check timed out")
            except Exception as e:
                issues.append(f"Error checking conda version: {e}")
            
            # Check Python version
            try:
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    issues.append("Anaconda Python is not working properly")
                    recommendations.append("Reinstall Anaconda")
            except Exception as e:
                issues.append(f"Error checking Anaconda Python: {e}")
            
            # Check if conda is in PATH
            try:
                result = subprocess.run(
                    ["conda", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    issues.append("Conda is not accessible from PATH")
                    recommendations.append("Add Anaconda to system PATH")
            except:
                issues.append("Conda is not accessible from PATH")
                recommendations.append("Add Anaconda to system PATH")
            
            # Check conda environments
            try:
                result = subprocess.run(
                    [conda_exe, "env", "list"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    if "base" not in result.stdout:
                        issues.append("Base conda environment not found")
                        recommendations.append("Reinstall Anaconda or repair base environment")
                else:
                    issues.append("Could not list conda environments")
            except Exception as e:
                issues.append(f"Error checking conda environments: {e}")
            
            # Check CONDA_DEFAULT_ENV
            conda_default_env = os.environ.get('CONDA_DEFAULT_ENV')
            if not conda_default_env:
                recommendations.append("Set CONDA_DEFAULT_ENV environment variable")
            
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
                recommendations=["Reinstall Anaconda using the runtime manager"]
            )
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed Anaconda version."""
        try:
            anaconda_path = self._find_anaconda_installation()
            if not anaconda_path:
                return None
            
            conda_exe = os.path.join(anaconda_path, "Scripts", "conda.exe")
            if not os.path.exists(conda_exe):
                return None
            
            result = subprocess.run(
                [conda_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                # Extract version from "conda 23.7.4"
                if "conda" in version_output:
                    return version_output.split("conda ")[1].split()[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Anaconda version: {e}")
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
        """Uninstall Anaconda (Windows-specific implementation)."""
        try:
            self.logger.info("Starting Anaconda uninstallation...")
            
            # Find Anaconda uninstaller
            anaconda_path = self._find_anaconda_installation()
            if not anaconda_path:
                self.logger.error("Anaconda installation not found")
                return False
            
            uninstaller_path = os.path.join(anaconda_path, "Uninstall-Anaconda3.exe")
            
            if os.path.exists(uninstaller_path):
                # Run uninstaller
                result = subprocess.run(
                    [uninstaller_path, "/S"],  # Silent uninstall
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes timeout
                )
                
                if result.returncode == 0:
                    self.logger.info("Anaconda uninstalled successfully")
                    return True
                else:
                    self.logger.error(f"Anaconda uninstaller failed with code {result.returncode}")
                    return False
            else:
                # Try registry-based uninstall
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
                                            if "Anaconda" in display_name:
                                                uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                                
                                                # Run uninstall command
                                                result = subprocess.run(
                                                    [uninstall_string, "/S"],
                                                    capture_output=True,
                                                    text=True,
                                                    timeout=600
                                                )
                                                
                                                if result.returncode == 0:
                                                    self.logger.info("Anaconda uninstalled successfully")
                                                    return True
                                                break
                                        except FileNotFoundError:
                                            pass
                                    i += 1
                                except OSError:
                                    break
                    except Exception as e:
                        self.logger.error(f"Error searching registry for Anaconda uninstaller: {e}")
                
                self.logger.error("Anaconda uninstaller not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Anaconda uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of Anaconda installation."""
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
            self.logger.error(f"Error getting Anaconda status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing AnacondaRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="anaconda",
        version="2024.10",
        download_url="https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Windows-x86_64.exe",
        mirrors=[
            "https://www.anaconda.com/download",
            "https://repo.anaconda.com/archive/"
        ],
        installation_type=InstallationType.EXE,
        environment_variables={
            "CONDA_DEFAULT_ENV": "base"
        },
        validation_commands=["conda --version", "python --version"],
        executable_paths=["conda.exe", "python.exe"],
        size_mb=500,
        description="Anaconda Python Distribution"
    )
    
    anaconda_runtime = AnacondaRuntime(config)
    
    # Test version detection
    version = anaconda_runtime.get_installed_version()
    print(f"Installed Anaconda version: {version}")
    
    # Test validation
    validation = anaconda_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = anaconda_runtime.get_status()
    print(f"Anaconda status: {status}")
    
    print("AnacondaRuntime test completed!")