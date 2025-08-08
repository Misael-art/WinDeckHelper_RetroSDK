#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Runtime Implementation
Handles Git 2.47.1 installation, configuration, and validation.
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
    # Fallback import for when running from different contexts
    from ..version_manager import version_manager

try:
    import winreg
except ImportError:
    winreg = None


class GitRuntime(Runtime):
    """Git runtime implementation with automatic configuration."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.git_path = None
        self.installation_path = None
        
    def install(self) -> bool:
        """Install Git 2.47.1 with automatic configuration."""
        try:
            self.logger.info(f"Starting Git {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f"Git {current_version} is already installed and compatible")
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
                # Configure Git after installation
                self.configure_environment()
                self.logger.info("Git installation completed successfully")
                return True
            else:
                self.logger.error("Git installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Git installation: {e}")
            return False
    
    def _download_installer(self) -> Optional[str]:
        """Download Git installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading Git installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"git-{self.config.version}-installer.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f"Git installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download Git installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run Git installer with silent installation parameters."""
        try:
            # Git for Windows silent installation parameters
            install_args = [
                installer_path,
                "/VERYSILENT",
                "/NORESTART",
                "/NOCANCEL",
                "/SP-",
                "/CLOSEAPPLICATIONS",
                "/RESTARTAPPLICATIONS",
                "/COMPONENTS=ext,ext\\shellhere,ext\\guihere,gitlfs,assoc,assoc_sh",
                "/TASKS=desktopicon,quicklaunchicon,addcontextmenufiles,addcontextmenufolders,associateshfiles"
            ]
            
            self.logger.info("Running Git installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Git installer completed successfully")
                return True
            else:
                self.logger.error(f"Git installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Git installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running Git installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure Git environment and initial settings."""
        try:
            self.logger.info("Configuring Git environment...")
            
            # Find Git installation path
            git_path = self._find_git_executable()
            if not git_path:
                self.logger.error("Git executable not found after installation")
                return False
            
            self.git_path = git_path
            
            # Configure basic Git settings
            self._configure_git_basics()
            
            # Add Git to PATH if not already there
            self._ensure_git_in_path()
            
            self.logger.info("Git environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring Git environment: {e}")
            return False
    
    def _find_git_executable(self) -> Optional[str]:
        """Find Git executable in common installation locations."""
        common_paths = [
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
            r"C:\Git\bin\git.exe"
        ]
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check PATH
        try:
            result = subprocess.run(
                ["where", "git"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def _configure_git_basics(self) -> None:
        """Configure basic Git settings."""
        try:
            if not self.git_path:
                return
            
            # Set basic configuration (user can override later)
            basic_configs = [
                ["config", "--global", "init.defaultBranch", "main"],
                ["config", "--global", "core.autocrlf", "true"],
                ["config", "--global", "core.editor", "notepad"],
                ["config", "--global", "pull.rebase", "false"],
                ["config", "--global", "credential.helper", "manager-core"]
            ]
            
            for config_cmd in basic_configs:
                try:
                    subprocess.run(
                        [self.git_path] + config_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                except:
                    # Continue if individual config fails
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Error configuring Git basics: {e}")
    
    def _ensure_git_in_path(self) -> None:
        """Ensure Git is in system PATH."""
        try:
            if not self.git_path:
                return
            
            git_dir = os.path.dirname(self.git_path)
            
            # Check if already in PATH
            current_path = os.environ.get('PATH', '')
            if git_dir.lower() in current_path.lower():
                return
            
            # Add to PATH for current session
            os.environ['PATH'] = f"{git_dir};{current_path}"
            
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
                        if git_dir.lower() not in system_path.lower():
                            new_path = f"{system_path};{git_dir}"
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                except:
                    # Silently fail if no admin privileges
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Error updating PATH: {e}")  
  
    def validate_installation(self) -> ValidationResult:
        """Validate Git installation and configuration."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Check if Git executable exists
            git_path = self._find_git_executable()
            if not git_path:
                return ValidationResult(
                    is_valid=False,
                    issues=["Git executable not found"],
                    recommendations=["Install Git using the runtime manager"]
                )
            
            # Check Git version
            try:
                result = subprocess.run(
                    [git_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    # Extract version from "git version 2.47.1.windows.1"
                    if "git version" in version_output:
                        version_detected = version_output.split("git version ")[1].split()[0]
                        
                        if not self._is_version_compatible(version_detected):
                            issues.append(f"Git version {version_detected} is outdated")
                            recommendations.append(f"Update to Git {self.config.version} or later")
                else:
                    issues.append("Git version check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append("Git version check timed out")
            except Exception as e:
                issues.append(f"Error checking Git version: {e}")
            
            # Check if Git is in PATH
            try:
                result = subprocess.run(
                    ["git", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    issues.append("Git is not accessible from PATH")
                    recommendations.append("Add Git to system PATH")
            except:
                issues.append("Git is not accessible from PATH")
                recommendations.append("Add Git to system PATH")
            
            # Check basic Git configuration
            config_checks = [
                ("user.name", "Configure Git user name with: git config --global user.name \"Your Name\""),
                ("user.email", "Configure Git user email with: git config --global user.email \"your.email@example.com\"")
            ]
            
            for config_key, recommendation in config_checks:
                try:
                    result = subprocess.run(
                        [git_path, "config", "--global", config_key],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0 or not result.stdout.strip():
                        recommendations.append(recommendation)
                except:
                    recommendations.append(recommendation)
            
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
                recommendations=["Reinstall Git using the runtime manager"]
            )
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed Git version."""
        try:
            git_path = self._find_git_executable()
            if not git_path:
                return None
            
            result = subprocess.run(
                [git_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                if "git version" in version_output:
                    return version_output.split("git version ")[1].split()[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Git version: {e}")
            return None
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if installed version is compatible with requirements."""
        try:
            # Use centralized VersionManager for compatibility check
            return version_manager.is_compatible(version, f">={self.config.version}")
            
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall Git (Windows-specific implementation)."""
        try:
            self.logger.info("Starting Git uninstallation...")
            
            # Find Git uninstaller
            uninstaller_paths = [
                r"C:\Program Files\Git\unins000.exe",
                r"C:\Program Files (x86)\Git\unins000.exe"
            ]
            
            uninstaller = None
            for path in uninstaller_paths:
                if os.path.exists(path):
                    uninstaller = path
                    break
            
            if not uninstaller:
                # Try to find via registry
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
                                            if "Git" in display_name:
                                                uninstaller, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                                break
                                        except FileNotFoundError:
                                            pass
                                    i += 1
                                except OSError:
                                    break
                    except Exception as e:
                        self.logger.warning(f"Error searching registry for Git uninstaller: {e}")
            
            if uninstaller:
                # Run uninstaller
                result = subprocess.run(
                    [uninstaller, "/VERYSILENT", "/NORESTART"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.logger.info("Git uninstalled successfully")
                    return True
                else:
                    self.logger.error(f"Git uninstaller failed with code {result.returncode}")
                    return False
            else:
                self.logger.error("Git uninstaller not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Git uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of Git installation."""
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
            self.logger.error(f"Error getting Git status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing GitRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="git",
        version="2.47.1",
        download_url="https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe",
        mirrors=[
            "https://git-scm.com/download/win",
            "https://github.com/git-for-windows/git/releases/latest"
        ],
        installation_type=InstallationType.EXE,
        validation_commands=["git --version"],
        executable_paths=["git.exe"],
        size_mb=50,
        description="Git version control system"
    )
    
    git_runtime = GitRuntime(config)
    
    # Test version detection
    version = git_runtime.get_installed_version()
    print(f"Installed Git version: {version}")
    
    # Test validation
    validation = git_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = git_runtime.get_status()
    print(f"Git status: {status}")
    
    print("GitRuntime test completed!")