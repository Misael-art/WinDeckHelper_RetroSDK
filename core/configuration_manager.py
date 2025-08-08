#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Manager - Advanced Configuration Management System
Provides centralized configuration management with validation, profiles, and environment-specific settings.
"""

import os
import sys
import json
import yaml
import logging
import platform
import tempfile
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Type
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
import time
from datetime import datetime
import hashlib
import copy


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"
    ENV = "env"


class ConfigScope(Enum):
    """Configuration scope levels."""
    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    RUNTIME = "runtime"
    TEMPORARY = "temporary"


class ValidationLevel(Enum):
    """Configuration validation levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"
    DISABLED = "disabled"


@dataclass
class ConfigValidationRule:
    """Configuration validation rule."""
    field_path: str
    rule_type: str  # required, type, range, regex, custom
    rule_value: Any = None
    error_message: str = ""
    warning_message: str = ""
    is_critical: bool = True


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_errors: Dict[str, List[str]] = field(default_factory=dict)
    validation_time: float = 0.0


@dataclass
class ConfigProfile:
    """Configuration profile for different environments."""
    name: str
    description: str = ""
    base_profile: Optional[str] = None
    config_data: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    validation_rules: List[ConfigValidationRule] = field(default_factory=list)
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConfigBackup:
    """Configuration backup information."""
    backup_id: str
    profile_name: str
    backup_path: str
    created_at: datetime
    description: str = ""
    config_hash: str = ""


class ConfigValidator:
    """Configuration validator with rule-based validation."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self.logger = logging.getLogger("config_validator")
    
    def validate_config(self, config_data: Dict[str, Any], 
                       rules: List[ConfigValidationRule]) -> ConfigValidationResult:
        """Validate configuration data against rules."""
        start_time = time.time()
        result = ConfigValidationResult()
        
        if self.validation_level == ValidationLevel.DISABLED:
            result.validation_time = time.time() - start_time
            return result
        
        for rule in rules:
            try:
                self._validate_rule(config_data, rule, result)
            except Exception as e:
                error_msg = f"Validation error for rule {rule.field_path}: {e}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
        
        result.is_valid = len(result.errors) == 0
        result.validation_time = time.time() - start_time
        
        return result
    
    def _validate_rule(self, config_data: Dict[str, Any], 
                      rule: ConfigValidationRule, result: ConfigValidationResult):
        """Validate a single rule."""
        field_value = self._get_nested_value(config_data, rule.field_path)
        
        if rule.rule_type == "required":
            if field_value is None:
                self._add_validation_error(result, rule, f"Required field '{rule.field_path}' is missing")
        
        elif rule.rule_type == "type":
            if field_value is not None and rule.rule_value:
                expected_type = rule.rule_value
                if not isinstance(field_value, expected_type):
                    self._add_validation_error(result, rule, 
                        f"Field '{rule.field_path}' must be of type {expected_type.__name__}")
        
        elif rule.rule_type == "range":
            if field_value is not None and rule.rule_value:
                min_val, max_val = rule.rule_value
                if not (min_val <= field_value <= max_val):
                    self._add_validation_error(result, rule, 
                        f"Field '{rule.field_path}' must be between {min_val} and {max_val}")
        
        elif rule.rule_type == "regex":
            if field_value is not None and rule.rule_value:
                pattern = rule.rule_value
                if not re.match(pattern, str(field_value)):
                    self._add_validation_error(result, rule, 
                        f"Field '{rule.field_path}' does not match required pattern")
        
        elif rule.rule_type == "enum":
            if field_value is not None and rule.rule_value:
                allowed_values = rule.rule_value
                if field_value not in allowed_values:
                    self._add_validation_error(result, rule, 
                        f"Field '{rule.field_path}' must be one of: {allowed_values}")
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _add_validation_error(self, result: ConfigValidationResult, 
                             rule: ConfigValidationRule, message: str):
        """Add validation error to result."""
        error_msg = rule.error_message or message
        
        if rule.is_critical or self.validation_level == ValidationLevel.STRICT:
            result.errors.append(error_msg)
            
            if rule.field_path not in result.field_errors:
                result.field_errors[rule.field_path] = []
            result.field_errors[rule.field_path].append(error_msg)
        else:
            warning_msg = rule.warning_message or error_msg
            result.warnings.append(warning_msg)


class ConfigurationManager:
    """Advanced configuration management system."""
    
    def __init__(self, config_dir: Optional[str] = None, 
                 validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.logger = logging.getLogger("configuration_manager")
        
        # Configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".env_dev" / "config"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Profiles and settings
        self.profiles: Dict[str, ConfigProfile] = {}
        self.active_profile: Optional[str] = None
        self.global_config: Dict[str, Any] = {}
        
        # Validation and backup
        self.validator = ConfigValidator(validation_level)
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load existing configuration
        self._load_configuration()
    
    def create_profile(self, name: str, description: str = "", 
                      base_profile: Optional[str] = None) -> bool:
        """Create a new configuration profile."""
        try:
            if name in self.profiles:
                self.logger.warning(f"Profile '{name}' already exists")
                return False
            
            # Create new profile
            profile = ConfigProfile(
                name=name,
                description=description,
                base_profile=base_profile
            )
            
            # Inherit from base profile if specified
            if base_profile and base_profile in self.profiles:
                base = self.profiles[base_profile]
                profile.config_data = copy.deepcopy(base.config_data)
                profile.environment_variables = copy.deepcopy(base.environment_variables)
                profile.validation_rules = copy.deepcopy(base.validation_rules)
            
            self.profiles[name] = profile
            self._save_profile(profile)
            
            self.logger.info(f"Created configuration profile: {name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to create profile {name}: {e}")
            return False
    
    def activate_profile(self, name: str) -> bool:
        """Activate a configuration profile."""
        try:
            if name not in self.profiles:
                self.logger.error(f"Profile '{name}' not found")
                return False
            
            # Deactivate current profile
            if self.active_profile:
                self.profiles[self.active_profile].is_active = False
            
            # Activate new profile
            self.profiles[name].is_active = True
            self.active_profile = name
            
            # Apply environment variables
            profile = self.profiles[name]
            for key, value in profile.environment_variables.items():
                os.environ[key] = value
            
            self._save_global_config()
            self.logger.info(f"Activated configuration profile: {name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to activate profile {name}: {e}")
            return False
    
    def set_config_value(self, key: str, value: Any, 
                        profile_name: Optional[str] = None) -> bool:
        """Set a configuration value."""
        try:
            target_profile = profile_name or self.active_profile
            
            if target_profile:
                if target_profile not in self.profiles:
                    self.logger.error(f"Profile '{target_profile}' not found")
                    return False
                
                profile = self.profiles[target_profile]
                self._set_nested_value(profile.config_data, key, value)
                profile.modified_at = datetime.now()
                
                # Validate configuration
                validation_result = self.validator.validate_config(
                    profile.config_data, profile.validation_rules
                )
                
                if not validation_result.is_valid:
                    self.logger.warning(f"Configuration validation warnings for {key}: {validation_result.warnings}")
                
                self._save_profile(profile)
            else:
                # Set in global config
                self._set_nested_value(self.global_config, key, value)
                self._save_global_config()
            
            self.logger.debug(f"Set config value: {key} = {value}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to set config value {key}: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None, 
                        profile_name: Optional[str] = None) -> Any:
        """Get a configuration value."""
        try:
            target_profile = profile_name or self.active_profile
            
            if target_profile and target_profile in self.profiles:
                profile = self.profiles[target_profile]
                value = self._get_nested_value(profile.config_data, key)
                if value is not None:
                    return value
            
            # Fallback to global config
            value = self._get_nested_value(self.global_config, key)
            return value if value is not None else default
        
        except Exception as e:
            self.logger.error(f"Failed to get config value {key}: {e}")
            return default
    
    def add_validation_rule(self, profile_name: str, rule: ConfigValidationRule) -> bool:
        """Add a validation rule to a profile."""
        try:
            if profile_name not in self.profiles:
                self.logger.error(f"Profile '{profile_name}' not found")
                return False
            
            profile = self.profiles[profile_name]
            profile.validation_rules.append(rule)
            profile.modified_at = datetime.now()
            
            self._save_profile(profile)
            self.logger.info(f"Added validation rule for {rule.field_path} to profile {profile_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to add validation rule: {e}")
            return False
    
    def validate_profile(self, profile_name: str) -> ConfigValidationResult:
        """Validate a configuration profile."""
        if profile_name not in self.profiles:
            result = ConfigValidationResult(is_valid=False)
            result.errors.append(f"Profile '{profile_name}' not found")
            return result
        
        profile = self.profiles[profile_name]
        return self.validator.validate_config(profile.config_data, profile.validation_rules)
    
    def create_backup(self, profile_name: str, description: str = "") -> Optional[str]:
        """Create a backup of a configuration profile."""
        try:
            if profile_name not in self.profiles:
                self.logger.error(f"Profile '{profile_name}' not found")
                return None
            
            profile = self.profiles[profile_name]
            
            # Generate backup ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{profile_name}_{timestamp}"
            
            # Create backup file
            backup_path = self.backup_dir / f"{backup_id}.json"
            backup_data = {
                "profile": asdict(profile),
                "backup_info": {
                    "backup_id": backup_id,
                    "created_at": datetime.now().isoformat(),
                    "description": description
                }
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate config hash
            config_str = json.dumps(profile.config_data, sort_keys=True)
            config_hash = hashlib.md5(config_str.encode()).hexdigest()
            
            # Create backup record
            backup = ConfigBackup(
                backup_id=backup_id,
                profile_name=profile_name,
                backup_path=str(backup_path),
                created_at=datetime.now(),
                description=description,
                config_hash=config_hash
            )
            
            self.logger.info(f"Created backup {backup_id} for profile {profile_name}")
            return backup_id
        
        except Exception as e:
            self.logger.error(f"Failed to create backup for {profile_name}: {e}")
            return None
    
    def restore_backup(self, backup_id: str) -> bool:
        """Restore a configuration from backup."""
        try:
            backup_path = self.backup_dir / f"{backup_id}.json"
            
            if not backup_path.exists():
                self.logger.error(f"Backup {backup_id} not found")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            profile_data = backup_data["profile"]
            profile_name = profile_data["name"]
            
            # Restore profile
            profile = ConfigProfile(**profile_data)
            profile.modified_at = datetime.now()
            
            self.profiles[profile_name] = profile
            self._save_profile(profile)
            
            self.logger.info(f"Restored profile {profile_name} from backup {backup_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def export_profile(self, profile_name: str, export_path: str, 
                      format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Export a configuration profile to file."""
        try:
            if profile_name not in self.profiles:
                self.logger.error(f"Profile '{profile_name}' not found")
                return False
            
            profile = self.profiles[profile_name]
            export_data = asdict(profile)
            
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == ConfigFormat.JSON:
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif format == ConfigFormat.YAML:
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, default_flow_style=False)
            
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
            
            self.logger.info(f"Exported profile {profile_name} to {export_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to export profile {profile_name}: {e}")
            return False
    
    def import_profile(self, import_path: str, profile_name: Optional[str] = None) -> bool:
        """Import a configuration profile from file."""
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            # Determine format from extension
            if import_file.suffix.lower() == '.json':
                with open(import_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            elif import_file.suffix.lower() in ['.yml', '.yaml']:
                with open(import_file, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
            else:
                self.logger.error(f"Unsupported import format: {import_file.suffix}")
                return False
            
            # Create profile
            if profile_name:
                profile_data["name"] = profile_name
            
            profile = ConfigProfile(**profile_data)
            profile.modified_at = datetime.now()
            
            self.profiles[profile.name] = profile
            self._save_profile(profile)
            
            self.logger.info(f"Imported profile {profile.name} from {import_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to import profile from {import_path}: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """List all available configuration profiles."""
        return list(self.profiles.keys())
    
    def get_profile_info(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a profile."""
        if profile_name not in self.profiles:
            return None
        
        profile = self.profiles[profile_name]
        validation_result = self.validate_profile(profile_name)
        
        return {
            "name": profile.name,
            "description": profile.description,
            "base_profile": profile.base_profile,
            "is_active": profile.is_active,
            "created_at": profile.created_at.isoformat(),
            "modified_at": profile.modified_at.isoformat(),
            "config_keys": list(profile.config_data.keys()),
            "environment_variables": list(profile.environment_variables.keys()),
            "validation_rules_count": len(profile.validation_rules),
            "validation_status": {
                "is_valid": validation_result.is_valid,
                "errors_count": len(validation_result.errors),
                "warnings_count": len(validation_result.warnings)
            }
        }
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """Set value in nested dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _load_configuration(self):
        """Load existing configuration from disk."""
        try:
            # Load global config
            global_config_path = self.config_dir / "global.json"
            if global_config_path.exists():
                with open(global_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.global_config = config_data.get("config", {})
                    self.active_profile = config_data.get("active_profile")
            
            # Load profiles
            profiles_dir = self.config_dir / "profiles"
            if profiles_dir.exists():
                for profile_file in profiles_dir.glob("*.json"):
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile_data = json.load(f)
                            profile = ConfigProfile(**profile_data)
                            self.profiles[profile.name] = profile
                    except Exception as e:
                        self.logger.error(f"Failed to load profile {profile_file}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    def _save_profile(self, profile: ConfigProfile):
        """Save a profile to disk."""
        try:
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            profile_path = profiles_dir / f"{profile.name}.json"
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(profile), f, indent=2, default=str)
        
        except Exception as e:
            self.logger.error(f"Failed to save profile {profile.name}: {e}")
    
    def _save_global_config(self):
        """Save global configuration to disk."""
        try:
            global_config_path = self.config_dir / "global.json"
            
            config_data = {
                "config": self.global_config,
                "active_profile": self.active_profile,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(global_config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
        
        except Exception as e:
            self.logger.error(f"Failed to save global config: {e}")


# Test the module when run directly
if __name__ == "__main__":
    print("Testing ConfigurationManager...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test configuration manager
    config_manager = ConfigurationManager()
    
    # Create test profile
    config_manager.create_profile("development", "Development environment configuration")
    config_manager.activate_profile("development")
    
    # Set some configuration values
    config_manager.set_config_value("database.host", "localhost")
    config_manager.set_config_value("database.port", 5432)
    config_manager.set_config_value("debug.enabled", True)
    
    # Add validation rules
    rule = ConfigValidationRule(
        field_path="database.port",
        rule_type="range",
        rule_value=(1, 65535),
        error_message="Port must be between 1 and 65535"
    )
    config_manager.add_validation_rule("development", rule)
    
    # Test validation
    validation_result = config_manager.validate_profile("development")
    print(f"Validation result: {validation_result.is_valid}")
    
    # Get configuration values
    host = config_manager.get_config_value("database.host")
    port = config_manager.get_config_value("database.port")
    print(f"Database config: {host}:{port}")
    
    # List profiles
    profiles = config_manager.list_profiles()
    print(f"Available profiles: {profiles}")
    
    print("\nConfigurationManager test completed!")