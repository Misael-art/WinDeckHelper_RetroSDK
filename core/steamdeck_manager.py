#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Steam Deck Manager - Hardware Detection and Optimization System
Provides Steam Deck-specific optimizations and Steam ecosystem integration.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import winreg
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class SteamDeckModel(Enum):
    """Steam Deck hardware models."""
    UNKNOWN = "unknown"
    STEAM_DECK_64GB = "steam_deck_64gb"
    STEAM_DECK_256GB = "steam_deck_256gb"
    STEAM_DECK_512GB = "steam_deck_512gb"
    STEAM_DECK_OLED_512GB = "steam_deck_oled_512gb"
    STEAM_DECK_OLED_1TB = "steam_deck_oled_1tb"


class DetectionMethod(Enum):
    """Methods used for Steam Deck detection."""
    DMI_SMBIOS = "dmi_smbios"
    STEAM_CLIENT = "steam_client"
    MANUAL_OVERRIDE = "manual_override"
    HARDWARE_SIGNATURE = "hardware_signature"
    REGISTRY_CHECK = "registry_check"


@dataclass
class HardwareInfo:
    """Steam Deck hardware information."""
    model: SteamDeckModel = SteamDeckModel.UNKNOWN
    cpu_model: str = ""
    gpu_model: str = ""
    ram_gb: int = 0
    storage_type: str = ""
    storage_gb: int = 0
    screen_type: str = ""  # LCD or OLED
    bios_version: str = ""
    firmware_version: str = ""


@dataclass
class DetectionResult:
    """Result of Steam Deck detection."""
    is_steam_deck: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    detection_method: DetectionMethod = DetectionMethod.DMI_SMBIOS
    hardware_info: HardwareInfo = field(default_factory=HardwareInfo)
    detection_details: Dict[str, Any] = field(default_factory=dict)
    fallback_used: bool = False


@dataclass
class ControllerConfig:
    """Steam Deck controller configuration."""
    steam_input_enabled: bool = False
    controller_profiles: Dict[str, str] = field(default_factory=dict)
    haptic_feedback_enabled: bool = True
    gyro_enabled: bool = True
    trackpad_sensitivity: float = 1.0


@dataclass
class PowerProfile:
    """Steam Deck power profile configuration."""
    profile_name: str = "balanced"
    cpu_governor: str = "powersave"
    gpu_frequency_limit: int = 1600  # MHz
    tdp_limit: int = 15  # Watts
    battery_optimization: bool = True
    thermal_throttling: bool = True


@dataclass
class DisplaySettings:
    """Steam Deck display configuration."""
    resolution_x: int = 1280
    resolution_y: int = 800
    refresh_rate: int = 60
    scaling_factor: float = 1.25
    brightness: int = 50
    adaptive_brightness: bool = True
    touch_enabled: bool = True


@dataclass
class AudioSettings:
    """Steam Deck audio configuration."""
    output_device: str = "steam_deck_speakers"
    volume_level: int = 50
    audio_enhancement: bool = True
    microphone_enabled: bool = True
    noise_suppression: bool = False


@dataclass
class SteamIntegrationConfig:
    """Steam ecosystem integration configuration."""
    glossi_enabled: bool = False
    steam_input_mapping: bool = False
    overlay_support: bool = False
    cloud_sync: bool = False
    desktop_mode_steam: bool = True


@dataclass
class SteamDeckProfile:
    """Complete Steam Deck configuration profile."""
    hardware_detected: bool = False
    controller_config: ControllerConfig = field(default_factory=ControllerConfig)
    power_profile: PowerProfile = field(default_factory=PowerProfile)
    display_settings: DisplaySettings = field(default_factory=DisplaySettings)
    audio_settings: AudioSettings = field(default_factory=AudioSettings)
    steam_integration: SteamIntegrationConfig = field(default_factory=SteamIntegrationConfig)


class SteamDeckDetector:
    """Handles Steam Deck hardware detection using multiple methods."""
    
    def __init__(self):
        self.logger = logging.getLogger("steamdeck_detector")
        self.detection_cache: Optional[DetectionResult] = None
        
    def detect_steam_deck(self, force_refresh: bool = False) -> DetectionResult:
        """
        Detect if running on Steam Deck hardware using multiple methods.
        
        Args:
            force_refresh: Force re-detection even if cached result exists
            
        Returns:
            DetectionResult with detection information
        """
        if self.detection_cache and not force_refresh:
            return self.detection_cache
            
        self.logger.info("Starting Steam Deck hardware detection...")
        
        # Try multiple detection methods in order of reliability
        detection_methods = [
            self._detect_via_dmi_smbios,
            self._detect_via_hardware_signature,
            self._detect_via_registry,
            self._detect_via_steam_client
        ]
        
        best_result = DetectionResult()
        
        for method in detection_methods:
            try:
                result = method()
                if result.confidence > best_result.confidence:
                    best_result = result
                    
                # If we have high confidence, stop here
                if result.confidence >= 0.9:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Detection method {method.__name__} failed: {e}")
                continue
        
        # Cache the result
        self.detection_cache = best_result
        
        self.logger.info(f"Steam Deck detection completed. "
                        f"Detected: {best_result.is_steam_deck}, "
                        f"Confidence: {best_result.confidence:.2f}, "
                        f"Method: {best_result.detection_method.value}")
        
        return best_result
    
    def _detect_via_dmi_smbios(self) -> DetectionResult:
        """
        Detect Steam Deck via DMI/SMBIOS information.
        This is the most reliable method on Windows.
        """
        result = DetectionResult(detection_method=DetectionMethod.DMI_SMBIOS)
        
        try:
            # Use WMI to get system information
            import wmi
            c = wmi.WMI()
            
            # Get system information
            for system in c.Win32_ComputerSystem():
                manufacturer = system.Manufacturer.lower() if system.Manufacturer else ""
                model = system.Model.lower() if system.Model else ""
                
                result.detection_details["manufacturer"] = manufacturer
                result.detection_details["model"] = model
                
                # Check for Steam Deck identifiers
                if "valve" in manufacturer or "steam deck" in model:
                    result.is_steam_deck = True
                    result.confidence = 0.95
                    result.hardware_info.model = self._determine_steam_deck_model(model)
                    break
            
            # Get additional hardware info if Steam Deck detected
            if result.is_steam_deck:
                self._populate_hardware_info(result.hardware_info, c)
                
        except ImportError:
            self.logger.warning("WMI module not available, falling back to alternative methods")
            # Fallback to subprocess-based detection
            return self._detect_via_subprocess_wmic()
        except Exception as e:
            self.logger.error(f"DMI/SMBIOS detection failed: {e}")
            result.confidence = 0.0
            
        return result
    
    def _detect_via_subprocess_wmic(self) -> DetectionResult:
        """Fallback DMI detection using subprocess and wmic."""
        result = DetectionResult(detection_method=DetectionMethod.DMI_SMBIOS)
        
        try:
            # Get manufacturer
            manufacturer_cmd = ["wmic", "computersystem", "get", "manufacturer", "/value"]
            manufacturer_output = subprocess.check_output(manufacturer_cmd, 
                                                        universal_newlines=True, 
                                                        creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Get model
            model_cmd = ["wmic", "computersystem", "get", "model", "/value"]
            model_output = subprocess.check_output(model_cmd, 
                                                 universal_newlines=True,
                                                 creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Parse output
            manufacturer = ""
            model = ""
            
            for line in manufacturer_output.split('\n'):
                if 'Manufacturer=' in line:
                    manufacturer = line.split('=')[1].strip().lower()
                    
            for line in model_output.split('\n'):
                if 'Model=' in line:
                    model = line.split('=')[1].strip().lower()
            
            result.detection_details["manufacturer"] = manufacturer
            result.detection_details["model"] = model
            
            # Check for Steam Deck identifiers
            if "valve" in manufacturer or "steam deck" in model:
                result.is_steam_deck = True
                result.confidence = 0.9
                result.hardware_info.model = self._determine_steam_deck_model(model)
                
        except Exception as e:
            self.logger.error(f"Subprocess WMIC detection failed: {e}")
            result.confidence = 0.0
            
        return result
    
    def _detect_via_hardware_signature(self) -> DetectionResult:
        """Detect Steam Deck via hardware signature (CPU/GPU combination)."""
        result = DetectionResult(detection_method=DetectionMethod.HARDWARE_SIGNATURE)
        
        try:
            # Get CPU information
            cpu_info = self._get_cpu_info()
            gpu_info = self._get_gpu_info()
            
            result.detection_details["cpu_info"] = cpu_info
            result.detection_details["gpu_info"] = gpu_info
            
            # Steam Deck uses AMD Zen 2 APU (Van Gogh)
            steam_deck_signatures = [
                "amd custom apu 0405",  # Steam Deck APU
                "van gogh",
                "aerith",  # Steam Deck codename
            ]
            
            cpu_lower = cpu_info.lower()
            gpu_lower = gpu_info.lower()
            
            for signature in steam_deck_signatures:
                if signature in cpu_lower or signature in gpu_lower:
                    result.is_steam_deck = True
                    result.confidence = 0.8
                    result.hardware_info.cpu_model = cpu_info
                    result.hardware_info.gpu_model = gpu_info
                    break
                    
        except Exception as e:
            self.logger.error(f"Hardware signature detection failed: {e}")
            result.confidence = 0.0
            
        return result
    
    def _detect_via_registry(self) -> DetectionResult:
        """Detect Steam Deck via Windows registry entries."""
        result = DetectionResult(detection_method=DetectionMethod.REGISTRY_CHECK)
        
        try:
            # Check for Steam Deck specific registry entries
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SystemInformation"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            ]
            
            steam_deck_indicators = []
            
            for hkey, path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, path) as key:
                        # Get all values in the key
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                if isinstance(value, str):
                                    value_lower = value.lower()
                                    if any(indicator in value_lower for indicator in 
                                          ["valve", "steam deck", "jupiter", "van gogh"]):
                                        steam_deck_indicators.append(f"{path}\\{name}: {value}")
                                i += 1
                            except WindowsError:
                                break
                                
                except WindowsError:
                    continue
            
            result.detection_details["registry_indicators"] = steam_deck_indicators
            
            if steam_deck_indicators:
                result.is_steam_deck = True
                result.confidence = 0.7
                
        except Exception as e:
            self.logger.error(f"Registry detection failed: {e}")
            result.confidence = 0.0
            
        return result
    
    def _detect_via_steam_client(self) -> DetectionResult:
        """Detect Steam Deck via Steam client presence and configuration."""
        result = DetectionResult(detection_method=DetectionMethod.STEAM_CLIENT)
        
        try:
            # Common Steam installation paths
            steam_paths = [
                Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Steam",
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Steam",
                Path.home() / "AppData" / "Local" / "Steam",
            ]
            
            steam_found = False
            steam_deck_mode = False
            
            for steam_path in steam_paths:
                if steam_path.exists():
                    steam_found = True
                    
                    # Check for Steam Deck specific files/configs
                    steamdeck_indicators = [
                        steam_path / "config" / "steamdeck.cfg",
                        steam_path / "steamapps" / "steamdeck",
                        steam_path / "logs" / "steamdeck.log",
                    ]
                    
                    for indicator in steamdeck_indicators:
                        if indicator.exists():
                            steam_deck_mode = True
                            break
                    
                    # Check Steam config for Steam Deck mode
                    config_file = steam_path / "config" / "config.vdf"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().lower()
                                if "steamdeck" in content or "bigpicture" in content:
                                    steam_deck_mode = True
                        except Exception:
                            pass
                    
                    break
            
            result.detection_details["steam_found"] = steam_found
            result.detection_details["steam_deck_mode"] = steam_deck_mode
            
            if steam_found and steam_deck_mode:
                result.is_steam_deck = True
                result.confidence = 0.6
                result.fallback_used = True
                
        except Exception as e:
            self.logger.error(f"Steam client detection failed: {e}")
            result.confidence = 0.0
            
        return result
    
    def _determine_steam_deck_model(self, model_string: str) -> SteamDeckModel:
        """Determine specific Steam Deck model from model string."""
        model_lower = model_string.lower()
        
        if "oled" in model_lower:
            if "1tb" in model_lower or "1000" in model_lower:
                return SteamDeckModel.STEAM_DECK_OLED_1TB
            else:
                return SteamDeckModel.STEAM_DECK_OLED_512GB
        else:
            if "512" in model_lower:
                return SteamDeckModel.STEAM_DECK_512GB
            elif "256" in model_lower:
                return SteamDeckModel.STEAM_DECK_256GB
            elif "64" in model_lower:
                return SteamDeckModel.STEAM_DECK_64GB
        
        return SteamDeckModel.UNKNOWN
    
    def _populate_hardware_info(self, hardware_info: HardwareInfo, wmi_connection) -> None:
        """Populate detailed hardware information using WMI."""
        try:
            # Get CPU info
            for processor in wmi_connection.Win32_Processor():
                hardware_info.cpu_model = processor.Name or ""
                break
            
            # Get GPU info
            for video in wmi_connection.Win32_VideoController():
                if video.Name and "amd" in video.Name.lower():
                    hardware_info.gpu_model = video.Name
                    break
            
            # Get memory info
            total_memory = 0
            for memory in wmi_connection.Win32_PhysicalMemory():
                if memory.Capacity:
                    total_memory += int(memory.Capacity)
            hardware_info.ram_gb = total_memory // (1024**3)
            
            # Get BIOS info
            for bios in wmi_connection.Win32_BIOS():
                hardware_info.bios_version = bios.SMBIOSBIOSVersion or ""
                break
                
        except Exception as e:
            self.logger.warning(f"Failed to populate hardware info: {e}")
    
    def _get_cpu_info(self) -> str:
        """Get CPU information using subprocess."""
        try:
            cmd = ["wmic", "cpu", "get", "name", "/value"]
            output = subprocess.check_output(cmd, universal_newlines=True,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in output.split('\n'):
                if 'Name=' in line:
                    return line.split('=')[1].strip()
                    
        except Exception as e:
            self.logger.warning(f"Failed to get CPU info: {e}")
            
        return "Unknown CPU"
    
    def _get_gpu_info(self) -> str:
        """Get GPU information using subprocess."""
        try:
            cmd = ["wmic", "path", "win32_VideoController", "get", "name", "/value"]
            output = subprocess.check_output(cmd, universal_newlines=True,
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            for line in output.split('\n'):
                if 'Name=' in line and line.split('=')[1].strip():
                    gpu_name = line.split('=')[1].strip()
                    if "amd" in gpu_name.lower():
                        return gpu_name
                        
        except Exception as e:
            self.logger.warning(f"Failed to get GPU info: {e}")
            
        return "Unknown GPU"


class SteamDeckOptimizer:
    """Handles Steam Deck-specific hardware optimizations."""
    
    def __init__(self, profile: SteamDeckProfile):
        self.profile = profile
        self.logger = logging.getLogger("steamdeck_optimizer")
    
    def optimize_controller_configuration(self) -> bool:
        """
        Configure Steam Deck controller settings for optimal development experience.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info("Configuring Steam Deck controller settings...")
            
            # Enable Steam Input for better compatibility
            self.profile.controller_config.steam_input_enabled = True
            
            # Configure default controller profiles for development tools
            dev_profiles = {
                "vscode": "desktop_mouse_keyboard",
                "visual_studio": "desktop_mouse_keyboard", 
                "jetbrains": "desktop_mouse_keyboard",
                "terminal": "desktop_keyboard",
                "browser": "desktop_mouse_keyboard"
            }
            
            self.profile.controller_config.controller_profiles.update(dev_profiles)
            
            # Optimize trackpad sensitivity for precise cursor control
            self.profile.controller_config.trackpad_sensitivity = 1.2
            
            # Enable gyro for additional input options
            self.profile.controller_config.gyro_enabled = True
            
            # Enable haptic feedback for better user experience
            self.profile.controller_config.haptic_feedback_enabled = True
            
            self.logger.info("Controller configuration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure controller: {e}")
            return False
    
    def optimize_power_profile(self, profile_type: str = "development") -> bool:
        """
        Configure power profile optimized for development work.
        
        Args:
            profile_type: Type of power profile ("development", "gaming", "battery_saver")
            
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info(f"Configuring power profile: {profile_type}")
            
            if profile_type == "development":
                # Balanced profile for development work
                self.profile.power_profile.profile_name = "development"
                self.profile.power_profile.cpu_governor = "performance"
                self.profile.power_profile.gpu_frequency_limit = 1600  # MHz
                self.profile.power_profile.tdp_limit = 20  # Watts - higher for compilation
                self.profile.power_profile.battery_optimization = False
                self.profile.power_profile.thermal_throttling = True
                
            elif profile_type == "battery_saver":
                # Power-saving profile for extended battery life
                self.profile.power_profile.profile_name = "battery_saver"
                self.profile.power_profile.cpu_governor = "powersave"
                self.profile.power_profile.gpu_frequency_limit = 800  # MHz
                self.profile.power_profile.tdp_limit = 10  # Watts
                self.profile.power_profile.battery_optimization = True
                self.profile.power_profile.thermal_throttling = True
                
            elif profile_type == "gaming":
                # High-performance profile for gaming
                self.profile.power_profile.profile_name = "gaming"
                self.profile.power_profile.cpu_governor = "performance"
                self.profile.power_profile.gpu_frequency_limit = 1600  # MHz
                self.profile.power_profile.tdp_limit = 25  # Watts
                self.profile.power_profile.battery_optimization = False
                self.profile.power_profile.thermal_throttling = False
                
            else:
                self.logger.warning(f"Unknown profile type: {profile_type}, using development")
                return self.optimize_power_profile("development")
            
            self.logger.info(f"Power profile '{profile_type}' configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure power profile: {e}")
            return False
    
    def optimize_display_settings(self) -> bool:
        """
        Configure display settings optimized for development work.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info("Configuring display settings...")
            
            # Set optimal resolution for Steam Deck screen
            self.profile.display_settings.resolution_x = 1280
            self.profile.display_settings.resolution_y = 800
            
            # Set refresh rate for smooth experience
            self.profile.display_settings.refresh_rate = 60
            
            # Configure scaling for readable text in development tools
            self.profile.display_settings.scaling_factor = 1.25
            
            # Set comfortable brightness level
            self.profile.display_settings.brightness = 60
            
            # Enable adaptive brightness for battery savings
            self.profile.display_settings.adaptive_brightness = True
            
            # Enable touch for additional input method
            self.profile.display_settings.touch_enabled = True
            
            self.logger.info("Display settings configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure display settings: {e}")
            return False
    
    def optimize_audio_settings(self) -> bool:
        """
        Configure audio settings for Steam Deck.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info("Configuring audio settings...")
            
            # Set default output to Steam Deck speakers
            self.profile.audio_settings.output_device = "steam_deck_speakers"
            
            # Set comfortable volume level
            self.profile.audio_settings.volume_level = 50
            
            # Enable audio enhancement for better quality
            self.profile.audio_settings.audio_enhancement = True
            
            # Enable microphone for video calls/recording
            self.profile.audio_settings.microphone_enabled = True
            
            # Disable noise suppression by default (can be enabled if needed)
            self.profile.audio_settings.noise_suppression = False
            
            self.logger.info("Audio settings configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure audio settings: {e}")
            return False
    
    def apply_thermal_optimizations(self) -> bool:
        """
        Apply thermal management optimizations for sustained performance.
        
        Returns:
            True if optimizations were applied successfully, False otherwise
        """
        try:
            self.logger.info("Applying thermal optimizations...")
            
            # These would typically involve system-level changes
            # For now, we'll configure profile settings that influence thermal behavior
            
            optimizations = {
                "cpu_thermal_throttle_temp": 85,  # Celsius
                "gpu_thermal_throttle_temp": 90,  # Celsius
                "fan_curve_aggressive": False,    # Balanced fan curve
                "thermal_monitoring": True,       # Enable thermal monitoring
                "performance_scaling": True       # Enable dynamic performance scaling
            }
            
            # Store thermal optimizations in profile
            if not hasattr(self.profile, 'thermal_settings'):
                self.profile.thermal_settings = {}
            
            self.profile.thermal_settings.update(optimizations)
            
            self.logger.info("Thermal optimizations applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply thermal optimizations: {e}")
            return False
    
    def configure_development_environment(self) -> bool:
        """
        Apply comprehensive optimizations for development environment.
        
        Returns:
            True if all optimizations were successful, False otherwise
        """
        try:
            self.logger.info("Configuring comprehensive development environment...")
            
            success = True
            
            # Apply all optimizations
            success &= self.optimize_controller_configuration()
            success &= self.optimize_power_profile("development")
            success &= self.optimize_display_settings()
            success &= self.optimize_audio_settings()
            success &= self.apply_thermal_optimizations()
            
            if success:
                self.logger.info("Development environment configured successfully")
            else:
                self.logger.warning("Some optimizations failed during configuration")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to configure development environment: {e}")
            return False


class SteamEcosystemIntegrator:
    """Handles Steam ecosystem integration for development tools."""
    
    def __init__(self, profile: SteamDeckProfile):
        self.profile = profile
        self.logger = logging.getLogger("steam_ecosystem_integrator")
        self.steam_path = self._find_steam_installation()
    
    def _find_steam_installation(self) -> Optional[Path]:
        """Find Steam installation directory."""
        common_paths = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Steam",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Steam",
            Path.home() / "AppData" / "Local" / "Steam",
            Path("C:\\Steam"),
            Path("D:\\Steam"),
        ]
        
        for path in common_paths:
            if path.exists() and (path / "steam.exe").exists():
                self.logger.info(f"Found Steam installation at: {path}")
                return path
        
        self.logger.warning("Steam installation not found")
        return None
    
    def setup_glossi_integration(self) -> bool:
        """
        Set up GlosSI (Global Steam Input) integration for non-Steam applications.
        
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info("Setting up GlosSI integration...")
            
            if not self.steam_path:
                self.logger.error("Steam installation not found, cannot setup GlosSI")
                return False
            
            # GlosSI configuration for development tools
            glossi_configs = {
                "vscode": {
                    "name": "Visual Studio Code",
                    "executable": "code.exe",
                    "launch_options": "",
                    "controller_config": "desktop_mouse_keyboard",
                    "enable_overlay": True
                },
                "visual_studio": {
                    "name": "Visual Studio",
                    "executable": "devenv.exe",
                    "launch_options": "",
                    "controller_config": "desktop_mouse_keyboard",
                    "enable_overlay": True
                },
                "jetbrains_idea": {
                    "name": "IntelliJ IDEA",
                    "executable": "idea64.exe",
                    "launch_options": "",
                    "controller_config": "desktop_mouse_keyboard",
                    "enable_overlay": True
                },
                "terminal": {
                    "name": "Windows Terminal",
                    "executable": "wt.exe",
                    "launch_options": "",
                    "controller_config": "desktop_keyboard",
                    "enable_overlay": False
                },
                "powershell": {
                    "name": "PowerShell",
                    "executable": "pwsh.exe",
                    "launch_options": "",
                    "controller_config": "desktop_keyboard",
                    "enable_overlay": False
                }
            }
            
            # Store GlosSI configurations in profile
            if not hasattr(self.profile, 'glossi_configs'):
                self.profile.glossi_configs = {}
            
            self.profile.glossi_configs.update(glossi_configs)
            self.profile.steam_integration.glossi_enabled = True
            
            self.logger.info("GlosSI integration configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup GlosSI integration: {e}")
            return False
    
    def configure_steam_input_mapping(self) -> bool:
        """
        Configure Steam Input mappings for development tools.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info("Configuring Steam Input mappings...")
            
            # Steam Input configurations for different development scenarios
            input_mappings = {
                "code_editor": {
                    "left_trackpad": "mouse",
                    "right_trackpad": "scroll",
                    "left_trigger": "left_click",
                    "right_trigger": "right_click",
                    "a_button": "enter",
                    "b_button": "escape",
                    "x_button": "ctrl+c",
                    "y_button": "ctrl+v",
                    "left_bumper": "ctrl+z",
                    "right_bumper": "ctrl+y"
                },
                "terminal": {
                    "left_trackpad": "disabled",
                    "right_trackpad": "scroll",
                    "dpad": "arrow_keys",
                    "a_button": "enter",
                    "b_button": "escape",
                    "x_button": "ctrl+c",
                    "y_button": "ctrl+v",
                    "left_bumper": "tab",
                    "right_bumper": "shift+tab"
                },
                "browser": {
                    "left_trackpad": "mouse",
                    "right_trackpad": "scroll",
                    "left_trigger": "left_click",
                    "right_trigger": "right_click",
                    "a_button": "enter",
                    "b_button": "back",
                    "x_button": "refresh",
                    "y_button": "new_tab",
                    "left_bumper": "prev_tab",
                    "right_bumper": "next_tab"
                }
            }
            
            # Store input mappings in profile
            if not hasattr(self.profile, 'input_mappings'):
                self.profile.input_mappings = {}
            
            self.profile.input_mappings.update(input_mappings)
            self.profile.steam_integration.steam_input_mapping = True
            
            self.logger.info("Steam Input mappings configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure Steam Input mappings: {e}")
            return False
    
    def setup_overlay_support(self) -> bool:
        """
        Configure Steam overlay support for development tools.
        
        Returns:
            True if setup was successful, False otherwise
        """
        try:
            self.logger.info("Setting up Steam overlay support...")
            
            if not self.steam_path:
                self.logger.error("Steam installation not found, cannot setup overlay")
                return False
            
            # Overlay configurations for different tools
            overlay_configs = {
                "enable_for_dev_tools": True,
                "overlay_hotkey": "shift+tab",
                "screenshot_hotkey": "f12",
                "supported_applications": [
                    "code.exe",
                    "devenv.exe", 
                    "idea64.exe",
                    "chrome.exe",
                    "firefox.exe",
                    "msedge.exe"
                ],
                "overlay_features": {
                    "web_browser": True,
                    "screenshot": True,
                    "friends_list": True,
                    "achievement_notifications": False,
                    "fps_counter": True
                }
            }
            
            # Store overlay configurations
            if not hasattr(self.profile, 'overlay_configs'):
                self.profile.overlay_configs = {}
            
            self.profile.overlay_configs.update(overlay_configs)
            self.profile.steam_integration.overlay_support = True
            
            self.logger.info("Steam overlay support configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup overlay support: {e}")
            return False
    
    def configure_cloud_sync(self) -> bool:
        """
        Configure Steam Cloud synchronization for development configurations.
        
        Returns:
            True if configuration was successful, False otherwise
        """
        try:
            self.logger.info("Configuring Steam Cloud synchronization...")
            
            # Cloud sync configurations
            cloud_sync_configs = {
                "sync_enabled": True,
                "sync_directories": [
                    {
                        "name": "VSCode Settings",
                        "local_path": "%APPDATA%\\Code\\User",
                        "patterns": ["settings.json", "keybindings.json", "snippets\\*"]
                    },
                    {
                        "name": "PowerShell Profile",
                        "local_path": "%USERPROFILE%\\Documents\\PowerShell",
                        "patterns": ["Microsoft.PowerShell_profile.ps1"]
                    },
                    {
                        "name": "Git Config",
                        "local_path": "%USERPROFILE%",
                        "patterns": [".gitconfig", ".gitignore_global"]
                    },
                    {
                        "name": "SSH Keys",
                        "local_path": "%USERPROFILE%\\.ssh",
                        "patterns": ["config", "known_hosts"],
                        "exclude_private_keys": True
                    }
                ],
                "sync_frequency": "on_startup_and_shutdown",
                "conflict_resolution": "prompt_user",
                "backup_before_sync": True
            }
            
            # Store cloud sync configurations
            if not hasattr(self.profile, 'cloud_sync_configs'):
                self.profile.cloud_sync_configs = {}
            
            self.profile.cloud_sync_configs.update(cloud_sync_configs)
            self.profile.steam_integration.cloud_sync = True
            
            self.logger.info("Steam Cloud synchronization configured successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure cloud sync: {e}")
            return False
    
    def maintain_desktop_mode_steam(self) -> bool:
        """
        Ensure Steam functionality is maintained in desktop mode.
        
        Returns:
            True if maintenance was successful, False otherwise
        """
        try:
            self.logger.info("Maintaining desktop mode Steam functionality...")
            
            if not self.steam_path:
                self.logger.error("Steam installation not found")
                return False
            
            # Desktop mode configurations
            desktop_configs = {
                "auto_start_steam": True,
                "minimize_to_tray": True,
                "enable_big_picture_mode": False,  # Disabled for desktop development
                "controller_support": True,
                "overlay_in_desktop": True,
                "steam_input_desktop": True,
                "library_sharing": True,
                "remote_play": True,
                "steam_link": True
            }
            
            # Check if Steam is running
            steam_running = self._is_steam_running()
            
            # Store desktop mode configurations
            if not hasattr(self.profile, 'desktop_mode_configs'):
                self.profile.desktop_mode_configs = {}
            
            self.profile.desktop_mode_configs.update(desktop_configs)
            self.profile.desktop_mode_configs["steam_running"] = steam_running
            self.profile.steam_integration.desktop_mode_steam = True
            
            self.logger.info(f"Desktop mode Steam functionality maintained (Steam running: {steam_running})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to maintain desktop mode Steam: {e}")
            return False
    
    def _is_steam_running(self) -> bool:
        """Check if Steam is currently running."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                    return True
        except ImportError:
            # Fallback method using subprocess
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq steam.exe'], 
                                      capture_output=True, text=True, 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                return 'steam.exe' in result.stdout.lower()
            except Exception:
                pass
        
        return False
    
    def setup_complete_integration(self) -> bool:
        """
        Set up complete Steam ecosystem integration.
        
        Returns:
            True if all integrations were successful, False otherwise
        """
        try:
            self.logger.info("Setting up complete Steam ecosystem integration...")
            
            success = True
            
            # Apply all integrations
            success &= self.setup_glossi_integration()
            success &= self.configure_steam_input_mapping()
            success &= self.setup_overlay_support()
            success &= self.configure_cloud_sync()
            success &= self.maintain_desktop_mode_steam()
            
            if success:
                self.logger.info("Complete Steam ecosystem integration configured successfully")
            else:
                self.logger.warning("Some Steam integrations failed during setup")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to setup complete Steam integration: {e}")
            return False


class SteamDeckManager:
    """Main manager for Steam Deck detection and optimization."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config/steamdeck")
        self.detector = SteamDeckDetector()
        self.profile = SteamDeckProfile()
        self.optimizer = SteamDeckOptimizer(self.profile)
        self.steam_integrator = SteamEcosystemIntegrator(self.profile)
        self.logger = logging.getLogger("steamdeck_manager")
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing profile if available
        self._load_profile()
    
    def detect_steam_deck(self, force_refresh: bool = False) -> bool:
        """
        Detect if running on Steam Deck hardware.
        
        Args:
            force_refresh: Force re-detection even if cached
            
        Returns:
            True if Steam Deck detected, False otherwise
        """
        detection_result = self.detector.detect_steam_deck(force_refresh)
        
        # Update profile with detection result
        self.profile.hardware_detected = detection_result.is_steam_deck
        
        # Save detection result
        self._save_detection_result(detection_result)
        
        return detection_result.is_steam_deck
    
    def get_detection_details(self) -> Optional[DetectionResult]:
        """Get detailed detection information."""
        return self.detector.detection_cache
    
    def force_steam_deck_mode(self, enabled: bool = True) -> None:
        """
        Manually override Steam Deck detection.
        
        Args:
            enabled: Whether to enable Steam Deck mode
        """
        self.profile.hardware_detected = enabled
        
        # Create manual override detection result
        override_result = DetectionResult(
            is_steam_deck=enabled,
            confidence=1.0,
            detection_method=DetectionMethod.MANUAL_OVERRIDE,
            detection_details={"manual_override": enabled}
        )
        
        self.detector.detection_cache = override_result
        self._save_detection_result(override_result)
        
        self.logger.info(f"Steam Deck mode manually {'enabled' if enabled else 'disabled'}")
    
    def is_steam_deck(self) -> bool:
        """Check if Steam Deck mode is active."""
        return self.profile.hardware_detected
    
    def get_profile(self) -> SteamDeckProfile:
        """Get current Steam Deck profile."""
        return self.profile
    
    def apply_optimizations(self, optimization_type: str = "development") -> bool:
        """
        Apply Steam Deck optimizations.
        
        Args:
            optimization_type: Type of optimization ("development", "gaming", "battery_saver")
            
        Returns:
            True if optimizations were successful, False otherwise
        """
        if not self.is_steam_deck():
            self.logger.warning("Steam Deck optimizations requested but hardware not detected")
            return False
        
        try:
            self.logger.info(f"Applying Steam Deck optimizations: {optimization_type}")
            
            if optimization_type == "development":
                success = self.optimizer.configure_development_environment()
            else:
                # Apply individual optimizations
                success = True
                success &= self.optimizer.optimize_controller_configuration()
                success &= self.optimizer.optimize_power_profile(optimization_type)
                success &= self.optimizer.optimize_display_settings()
                success &= self.optimizer.optimize_audio_settings()
                success &= self.optimizer.apply_thermal_optimizations()
            
            if success:
                # Save the updated profile
                self._save_profile()
                self.logger.info(f"Steam Deck optimizations '{optimization_type}' applied successfully")
            else:
                self.logger.error(f"Some optimizations failed for '{optimization_type}'")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to apply optimizations: {e}")
            return False
    
    def get_optimization_status(self) -> Dict[str, bool]:
        """
        Get status of various optimization components.
        
        Returns:
            Dictionary with optimization status
        """
        status = {
            "steam_deck_detected": self.is_steam_deck(),
            "controller_configured": self.profile.controller_config.steam_input_enabled,
            "power_profile_set": self.profile.power_profile.profile_name != "balanced",
            "display_optimized": self.profile.display_settings.scaling_factor > 1.0,
            "audio_configured": self.profile.audio_settings.audio_enhancement,
            "thermal_optimized": hasattr(self.profile, 'thermal_settings')
        }
        
        return status
    
    def reset_optimizations(self) -> bool:
        """
        Reset all optimizations to default values.
        
        Returns:
            True if reset was successful, False otherwise
        """
        try:
            self.logger.info("Resetting Steam Deck optimizations to defaults")
            
            # Reset to default profile
            self.profile = SteamDeckProfile()
            self.profile.hardware_detected = self.is_steam_deck()
            
            # Update optimizer reference
            self.optimizer = SteamDeckOptimizer(self.profile)
            self.steam_integrator = SteamEcosystemIntegrator(self.profile)
            
            # Save the reset profile
            self._save_profile()
            
            self.logger.info("Steam Deck optimizations reset successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset optimizations: {e}")
            return False
    
    def setup_steam_integration(self, integration_type: str = "complete") -> bool:
        """
        Set up Steam ecosystem integration.
        
        Args:
            integration_type: Type of integration ("complete", "glossi", "input", "overlay", "cloud")
            
        Returns:
            True if integration was successful, False otherwise
        """
        if not self.is_steam_deck():
            self.logger.warning("Steam integration requested but Steam Deck not detected")
            return False
        
        try:
            self.logger.info(f"Setting up Steam integration: {integration_type}")
            
            success = True
            
            if integration_type == "complete":
                success = self.steam_integrator.setup_complete_integration()
            elif integration_type == "glossi":
                success = self.steam_integrator.setup_glossi_integration()
            elif integration_type == "input":
                success = self.steam_integrator.configure_steam_input_mapping()
            elif integration_type == "overlay":
                success = self.steam_integrator.setup_overlay_support()
            elif integration_type == "cloud":
                success = self.steam_integrator.configure_cloud_sync()
            else:
                self.logger.error(f"Unknown integration type: {integration_type}")
                return False
            
            if success:
                # Save the updated profile
                self._save_profile()
                self.logger.info(f"Steam integration '{integration_type}' completed successfully")
            else:
                self.logger.error(f"Steam integration '{integration_type}' failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to setup Steam integration: {e}")
            return False
    
    def get_steam_integration_status(self) -> Dict[str, bool]:
        """
        Get status of Steam ecosystem integrations.
        
        Returns:
            Dictionary with integration status
        """
        status = {
            "steam_found": self.steam_integrator.steam_path is not None,
            "glossi_enabled": self.profile.steam_integration.glossi_enabled,
            "steam_input_mapping": self.profile.steam_integration.steam_input_mapping,
            "overlay_support": self.profile.steam_integration.overlay_support,
            "cloud_sync": self.profile.steam_integration.cloud_sync,
            "desktop_mode_steam": self.profile.steam_integration.desktop_mode_steam
        }
        
        return status
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all Steam Deck features.
        
        Returns:
            Dictionary with complete status information
        """
        return {
            "detection": {
                "is_steam_deck": self.is_steam_deck(),
                "detection_details": self.get_detection_details()
            },
            "optimizations": self.get_optimization_status(),
            "steam_integration": self.get_steam_integration_status(),
            "profile_summary": {
                "power_profile": self.profile.power_profile.profile_name,
                "controller_enabled": self.profile.controller_config.steam_input_enabled,
                "display_scaling": self.profile.display_settings.scaling_factor,
                "audio_enhancement": self.profile.audio_settings.audio_enhancement
            }
        }
    
    def _load_profile(self) -> None:
        """Load Steam Deck profile from config file."""
        profile_file = self.config_dir / "profile.json"
        
        try:
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load basic settings
                self.profile.hardware_detected = data.get("hardware_detected", False)
                
                # Load controller config
                if "controller_config" in data:
                    cc_data = data["controller_config"]
                    self.profile.controller_config = ControllerConfig(
                        steam_input_enabled=cc_data.get("steam_input_enabled", False),
                        controller_profiles=cc_data.get("controller_profiles", {}),
                        haptic_feedback_enabled=cc_data.get("haptic_feedback_enabled", True),
                        gyro_enabled=cc_data.get("gyro_enabled", True),
                        trackpad_sensitivity=cc_data.get("trackpad_sensitivity", 1.0)
                    )
                
                self.logger.info("Steam Deck profile loaded successfully")
                
        except Exception as e:
            self.logger.warning(f"Failed to load Steam Deck profile: {e}")
            # Use default profile
            self.profile = SteamDeckProfile()
    
    def _save_profile(self) -> None:
        """Save Steam Deck profile to config file."""
        profile_file = self.config_dir / "profile.json"
        
        try:
            # Convert profile to dictionary
            profile_data = {
                "hardware_detected": self.profile.hardware_detected,
                "controller_config": {
                    "steam_input_enabled": self.profile.controller_config.steam_input_enabled,
                    "controller_profiles": self.profile.controller_config.controller_profiles,
                    "haptic_feedback_enabled": self.profile.controller_config.haptic_feedback_enabled,
                    "gyro_enabled": self.profile.controller_config.gyro_enabled,
                    "trackpad_sensitivity": self.profile.controller_config.trackpad_sensitivity
                },
                "power_profile": {
                    "profile_name": self.profile.power_profile.profile_name,
                    "cpu_governor": self.profile.power_profile.cpu_governor,
                    "gpu_frequency_limit": self.profile.power_profile.gpu_frequency_limit,
                    "tdp_limit": self.profile.power_profile.tdp_limit,
                    "battery_optimization": self.profile.power_profile.battery_optimization,
                    "thermal_throttling": self.profile.power_profile.thermal_throttling
                },
                "display_settings": {
                    "resolution_x": self.profile.display_settings.resolution_x,
                    "resolution_y": self.profile.display_settings.resolution_y,
                    "refresh_rate": self.profile.display_settings.refresh_rate,
                    "scaling_factor": self.profile.display_settings.scaling_factor,
                    "brightness": self.profile.display_settings.brightness,
                    "adaptive_brightness": self.profile.display_settings.adaptive_brightness,
                    "touch_enabled": self.profile.display_settings.touch_enabled
                },
                "audio_settings": {
                    "output_device": self.profile.audio_settings.output_device,
                    "volume_level": self.profile.audio_settings.volume_level,
                    "audio_enhancement": self.profile.audio_settings.audio_enhancement,
                    "microphone_enabled": self.profile.audio_settings.microphone_enabled,
                    "noise_suppression": self.profile.audio_settings.noise_suppression
                },
                "steam_integration": {
                    "glossi_enabled": self.profile.steam_integration.glossi_enabled,
                    "steam_input_mapping": self.profile.steam_integration.steam_input_mapping,
                    "overlay_support": self.profile.steam_integration.overlay_support,
                    "cloud_sync": self.profile.steam_integration.cloud_sync,
                    "desktop_mode_steam": self.profile.steam_integration.desktop_mode_steam
                }
            }
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
                
            self.logger.info("Steam Deck profile saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save Steam Deck profile: {e}")
    
    def _save_detection_result(self, result: DetectionResult) -> None:
        """Save detection result to file."""
        detection_file = self.config_dir / "detection_result.json"
        
        try:
            detection_data = {
                "is_steam_deck": result.is_steam_deck,
                "confidence": result.confidence,
                "detection_method": result.detection_method.value,
                "detection_details": result.detection_details,
                "fallback_used": result.fallback_used,
                "timestamp": datetime.now().isoformat(),
                "hardware_info": {
                    "model": result.hardware_info.model.value,
                    "cpu_model": result.hardware_info.cpu_model,
                    "gpu_model": result.hardware_info.gpu_model,
                    "ram_gb": result.hardware_info.ram_gb,
                    "storage_type": result.hardware_info.storage_type,
                    "storage_gb": result.hardware_info.storage_gb,
                    "screen_type": result.hardware_info.screen_type,
                    "bios_version": result.hardware_info.bios_version,
                    "firmware_version": result.hardware_info.firmware_version
                }
            }
            
            with open(detection_file, 'w', encoding='utf-8') as f:
                json.dump(detection_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save detection result: {e}")


# Test the module when run directly
if __name__ == "__main__":
    print("Testing SteamDeckManager...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test Steam Deck detection
    manager = SteamDeckManager()
    is_steam_deck = manager.detect_steam_deck()
    
    print(f"Steam Deck detected: {is_steam_deck}")
    
    # Get detection details
    details = manager.get_detection_details()
    if details:
        print(f"Detection method: {details.detection_method.value}")
        print(f"Confidence: {details.confidence:.2f}")
        print(f"Hardware model: {details.hardware_info.model.value}")
        
    print("SteamDeckManager test completed successfully!")