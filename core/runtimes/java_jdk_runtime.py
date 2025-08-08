#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Java JDK Runtime Implementation
Handles Java JDK 21 installation, configuration, and validation.
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


class JavaJDKRuntime(Runtime):
    """Java JDK runtime implementation with automatic configuration."""
    
    def __init__(self, config: RuntimeConfig):
        super().__init__(config)
        self.java_path = None
        self.javac_path = None
        self.java_home = None
        
    def install(self) -> bool:
        """Install Java JDK 21 with automatic configuration."""
        try:
            self.logger.info(f"Starting Java JDK {self.config.version} installation...")
            
            # Check if already installed and up to date
            current_version = self.get_installed_version()
            if current_version and self._is_version_compatible(current_version):
                self.logger.info(f"Java JDK {current_version} is already installed and compatible")
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
                self.logger.info("Java JDK installation completed successfully")
                return True
            else:
                self.logger.error("Java JDK installation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Java JDK installation: {e}")
            return False
    
    def _download_installer(self) -> Optional[str]:
        """Download Java JDK installer from primary URL or mirrors."""
        urls_to_try = [self.config.download_url] + self.config.mirrors
        
        for url in urls_to_try:
            try:
                self.logger.info(f"Downloading Java JDK installer from: {url}")
                
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"jdk-{self.config.version}-installer.exe")
                
                # Download with progress (simplified)
                urlretrieve(url, installer_path)
                
                if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1024:
                    self.logger.info(f"Java JDK installer downloaded successfully: {installer_path}")
                    return installer_path
                    
            except URLError as e:
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error downloading from {url}: {e}")
                continue
        
        self.logger.error("Failed to download Java JDK installer from all sources")
        return None
    
    def _run_installation(self, installer_path: str) -> bool:
        """Run Java JDK installer with silent installation parameters."""
        try:
            # Java JDK silent installation parameters
            install_args = [
                installer_path,
                "/s",  # Silent installation
                "INSTALL_SILENT=1",
                "STATIC=0",
                "AUTO_UPDATE=0",
                "WEB_JAVA=1",
                "WEB_JAVA_SECURITY_LEVEL=H",
                "WEB_ANALYTICS=0",
                "EULA=0",
                "REBOOT=0"
            ]
            
            self.logger.info("Running Java JDK installer...")
            result = subprocess.run(
                install_args,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Java JDK installer completed successfully")
                return True
            else:
                self.logger.error(f"Java JDK installer failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Installer error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Java JDK installation timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error running Java JDK installer: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """Configure Java JDK environment variables and PATH."""
        try:
            self.logger.info("Configuring Java JDK environment...")
            
            # Find Java installation path
            java_home = self._find_java_home()
            if not java_home:
                self.logger.error("Java installation not found after installation")
                return False
            
            self.java_home = java_home
            self.java_path = os.path.join(java_home, "bin", "java.exe")
            self.javac_path = os.path.join(java_home, "bin", "javac.exe")
            
            # Configure environment variables
            self._configure_environment_variables()
            
            # Add Java to PATH if not already there
            self._ensure_java_in_path()
            
            self.logger.info("Java JDK environment configuration completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring Java JDK environment: {e}")
            return False
    
    def _find_java_home(self) -> Optional[str]:
        """Find Java installation directory."""
        # Check common installation paths
        common_paths = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
            r"C:\Java"
        ]
        
        for base_path in common_paths:
            if os.path.exists(base_path):
                # Look for JDK directories
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path) and "jdk" in item.lower():
                        # Check if this is a valid JDK installation
                        java_exe = os.path.join(item_path, "bin", "java.exe")
                        javac_exe = os.path.join(item_path, "bin", "javac.exe")
                        if os.path.exists(java_exe) and os.path.exists(javac_exe):
                            return item_path
        
        # Check registry for Java installation
        if winreg and platform.system() == "Windows":
            try:
                # Check for JDK in registry
                registry_paths = [
                    r"SOFTWARE\JavaSoft\JDK",
                    r"SOFTWARE\JavaSoft\Java Development Kit"
                ]
                
                for reg_path in registry_paths:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                            # Get the current version
                            current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
                            
                            # Get the Java home for this version
                            with winreg.OpenKey(key, current_version) as version_key:
                                java_home, _ = winreg.QueryValueEx(version_key, "JavaHome")
                                if os.path.exists(java_home):
                                    return java_home
                    except FileNotFoundError:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error checking registry for Java: {e}")
        
        # Check JAVA_HOME environment variable
        java_home_env = os.environ.get('JAVA_HOME')
        if java_home_env and os.path.exists(java_home_env):
            java_exe = os.path.join(java_home_env, "bin", "java.exe")
            javac_exe = os.path.join(java_home_env, "bin", "javac.exe")
            if os.path.exists(java_exe) and os.path.exists(javac_exe):
                return java_home_env
        
        return None
    
    def _configure_environment_variables(self) -> None:
        """Configure Java JDK environment variables."""
        try:
            if not self.java_home:
                return
            
            # Set JAVA_HOME environment variable
            # Set for current session
            os.environ['JAVA_HOME'] = self.java_home
            
            # Try to set system environment variable (requires admin privileges)
            if winreg and platform.system() == "Windows":
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                        0,
                        winreg.KEY_ALL_ACCESS
                    ) as key:
                        winreg.SetValueEx(key, "JAVA_HOME", 0, winreg.REG_SZ, self.java_home)
                        self.logger.info(f"Set JAVA_HOME system environment variable: {self.java_home}")
                except Exception as e:
                    self.logger.warning(f"Could not set system JAVA_HOME (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error configuring environment variables: {e}")
    
    def _ensure_java_in_path(self) -> None:
        """Ensure Java bin directory is in system PATH."""
        try:
            if not self.java_home:
                return
            
            java_bin_path = os.path.join(self.java_home, "bin")
            
            # Check if already in PATH
            current_path = os.environ.get('PATH', '')
            if java_bin_path.lower() in current_path.lower():
                return
            
            # Add to PATH for current session
            os.environ['PATH'] = f"{java_bin_path};{current_path}"
            
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
                        if java_bin_path.lower() not in system_path.lower():
                            new_path = f"{system_path};{java_bin_path}"
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            self.logger.info("Added Java to system PATH")
                except Exception as e:
                    self.logger.warning(f"Could not update system PATH (may need admin privileges): {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error updating PATH: {e}")
    
    def validate_installation(self) -> ValidationResult:
        """Validate Java JDK installation and configuration."""
        try:
            issues = []
            recommendations = []
            version_detected = None
            
            # Check if Java executable exists
            java_home = self._find_java_home()
            if not java_home:
                return ValidationResult(
                    is_valid=False,
                    issues=["Java JDK installation not found"],
                    recommendations=["Install Java JDK using the runtime manager"]
                )
            
            java_exe = os.path.join(java_home, "bin", "java.exe")
            javac_exe = os.path.join(java_home, "bin", "javac.exe")
            
            # Check Java version
            try:
                result = subprocess.run(
                    [java_exe, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    # Java version output goes to stderr
                    version_output = result.stderr.strip()
                    # Extract version from output like 'openjdk version "21.0.1" 2023-10-17'
                    if "version" in version_output:
                        import re
                        version_match = re.search(r'version "([^"]+)"', version_output)
                        if version_match:
                            version_detected = version_match.group(1)
                            
                            if not self._is_version_compatible(version_detected):
                                issues.append(f"Java version {version_detected} is outdated")
                                recommendations.append(f"Update to Java JDK {self.config.version} or later")
                else:
                    issues.append("Java version check failed")
                    
            except subprocess.TimeoutExpired:
                issues.append("Java version check timed out")
            except Exception as e:
                issues.append(f"Error checking Java version: {e}")
            
            # Check javac (compiler)
            if not os.path.exists(javac_exe):
                issues.append("Java compiler (javac) not found")
                recommendations.append("Install full Java JDK (not just JRE)")
            else:
                try:
                    result = subprocess.run(
                        [javac_exe, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        issues.append("Java compiler (javac) not working properly")
                except Exception as e:
                    issues.append(f"Error checking javac: {e}")
            
            # Check if Java is in PATH
            try:
                result = subprocess.run(
                    ["java", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    issues.append("Java is not accessible from PATH")
                    recommendations.append("Add Java to system PATH")
            except:
                issues.append("Java is not accessible from PATH")
                recommendations.append("Add Java to system PATH")
            
            # Check JAVA_HOME environment variable
            java_home_env = os.environ.get('JAVA_HOME')
            if not java_home_env:
                recommendations.append("Set JAVA_HOME environment variable")
            elif java_home_env != java_home:
                recommendations.append("Update JAVA_HOME to point to correct Java installation")
            
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
                recommendations=["Reinstall Java JDK using the runtime manager"]
            )
    
    def get_installed_version(self) -> Optional[str]:
        """Get currently installed Java JDK version."""
        try:
            java_home = self._find_java_home()
            if not java_home:
                return None
            
            java_exe = os.path.join(java_home, "bin", "java.exe")
            if not os.path.exists(java_exe):
                return None
            
            result = subprocess.run(
                [java_exe, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Java version output goes to stderr
                version_output = result.stderr.strip()
                # Extract version from output like 'openjdk version "21.0.1" 2023-10-17'
                if "version" in version_output:
                    import re
                    version_match = re.search(r'version "([^"]+)"', version_output)
                    if version_match:
                        return version_match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Java version: {e}")
            return None
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if installed version is compatible with requirements."""
        try:
            # Normalize Java version format for comparison
            normalized_version = self._normalize_java_version(version)
            normalized_required = self._normalize_java_version(self.config.version)
            
            # Use centralized version manager for compatibility checking
            requirement = f">={normalized_required}"
            return version_manager.is_compatible(normalized_version, requirement)
        except Exception as e:
            self.logger.error(f"Error comparing versions: {e}")
            return False
    
    def _normalize_java_version(self, version: str) -> str:
        """Normalize Java version format for consistent comparison."""
        try:
            parts = version.split('.')
            if len(parts) >= 2 and parts[0] == "1":
                # Handle old Java versioning (1.8.x -> 8.0.0)
                major = int(parts[1])
                return f"{major}.0.0"
            else:
                # Handle new Java versioning (21.x.x -> 21.x.x)
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                patch = int(parts[2].split('_')[0]) if len(parts) > 2 else 0
                return f"{major}.{minor}.{patch}"
        except (ValueError, IndexError):
            return "0.0.0"
    
    def uninstall(self) -> bool:
        """Uninstall Java JDK (Windows-specific implementation)."""
        try:
            self.logger.info("Starting Java JDK uninstallation...")
            
            # Java uninstallation via Windows Programs and Features
            # This is complex as Java may have multiple versions installed
            
            if winreg and platform.system() == "Windows":
                try:
                    uninstall_commands = []
                    
                    # Search for Java in uninstall registry
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
                                        if "Java" in display_name and "JDK" in display_name:
                                            uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                            uninstall_commands.append(uninstall_string)
                                    except FileNotFoundError:
                                        pass
                                i += 1
                            except OSError:
                                break
                    
                    # Execute uninstall commands
                    for uninstall_cmd in uninstall_commands:
                        try:
                            # Parse uninstall command and add silent flags
                            if "msiexec" in uninstall_cmd.lower():
                                # MSI uninstall
                                cmd_parts = uninstall_cmd.split()
                                cmd_parts.extend(["/quiet", "/norestart"])
                            else:
                                # EXE uninstall
                                cmd_parts = [uninstall_cmd, "/s"]
                            
                            result = subprocess.run(
                                cmd_parts,
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                            
                            if result.returncode == 0:
                                self.logger.info("Java JDK uninstalled successfully")
                                return True
                                
                        except Exception as e:
                            self.logger.warning(f"Error running uninstall command {uninstall_cmd}: {e}")
                            continue
                    
                    if not uninstall_commands:
                        self.logger.warning("No Java JDK uninstall entries found in registry")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"Error searching for Java uninstall entries: {e}")
                    return False
            else:
                self.logger.error("Java uninstallation not supported on this platform")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Java JDK uninstallation: {e}")
            return False
    
    def get_status(self) -> RuntimeStatus:
        """Get current status of Java JDK installation."""
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
            self.logger.error(f"Error getting Java JDK status: {e}")
            return RuntimeStatus.FAILED


# Test the module when run directly
if __name__ == "__main__":
    print("Testing JavaJDKRuntime...")
    
    # Create test configuration
    from runtime_catalog_manager import RuntimeConfig, InstallationType
    
    config = RuntimeConfig(
        name="java_jdk",
        version="21",
        download_url="https://download.oracle.com/java/21/latest/jdk-21_windows-x64_bin.exe",
        mirrors=[
            "https://adoptium.net/temurin/releases/",
            "https://www.oracle.com/java/technologies/downloads/"
        ],
        installation_type=InstallationType.EXE,
        environment_variables={
            "JAVA_HOME": "%ProgramFiles%\\Java\\jdk-21"
        },
        validation_commands=["java -version", "javac -version"],
        executable_paths=["java.exe", "javac.exe"],
        registry_keys=["HKEY_LOCAL_MACHINE\\SOFTWARE\\JavaSoft\\JDK"],
        size_mb=300,
        description="Java JDK 21"
    )
    
    java_runtime = JavaJDKRuntime(config)
    
    # Test version detection
    version = java_runtime.get_installed_version()
    print(f"Installed Java JDK version: {version}")
    
    # Test validation
    validation = java_runtime.validate_installation()
    print(f"Validation result: {validation}")
    
    # Test status
    status = java_runtime.get_status()
    print(f"Java JDK status: {status}")
    
    print("JavaJDKRuntime test completed!")