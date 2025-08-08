#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Configuration System - Sistema de Configuração Dinâmica
Centraliza e gerencia todas as configurações do sistema de forma dinâmica.
"""

import logging
import os
import json
import yaml
import time
import threading
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
from collections import defaultdict
import copy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigType(Enum):
    """Tipos de configuração"""
    DETECTION = "detection"
    INSTALLATION = "installation"
    COMPATIBILITY = "compatibility"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOGGING = "logging"
    CACHE = "cache"
    NETWORK = "network"
    SYSTEM = "system"
    USER = "user"

class ConfigScope(Enum):
    """Escopo da configuração"""
    GLOBAL = "global"
    USER = "user"
    SESSION = "session"
    COMPONENT = "component"
    TEMPORARY = "temporary"

class ConfigFormat(Enum):
    """Formato de configuração"""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"
    ENV = "env"

@dataclass
class ConfigSchema:
    """Schema de configuração"""
    name: str
    type: ConfigType
    scope: ConfigScope
    format: ConfigFormat
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    default_values: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: str = "1.0"

@dataclass
class ConfigEntry:
    """Entrada de configuração"""
    key: str
    value: Any
    type: ConfigType
    scope: ConfigScope
    source: str
    timestamp: float = field(default_factory=time.time)
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    encrypted: bool = False
    sensitive: bool = False

@dataclass
class ConfigChangeEvent:
    """Evento de mudança de configuração"""
    key: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    change_type: str = "update"  # create, update, delete

class ConfigValidator:
    """Validador de configurações"""
    
    @staticmethod
    def validate_value(value: Any, rules: Dict[str, Any]) -> tuple[bool, str]:
        """Valida um valor contra regras"""
        try:
            # Verificar tipo
            if 'type' in rules:
                expected_type = rules['type']
                if expected_type == 'string' and not isinstance(value, str):
                    return False, f"Esperado string, recebido {type(value).__name__}"
                elif expected_type == 'integer' and not isinstance(value, int):
                    return False, f"Esperado integer, recebido {type(value).__name__}"
                elif expected_type == 'float' and not isinstance(value, (int, float)):
                    return False, f"Esperado float, recebido {type(value).__name__}"
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    return False, f"Esperado boolean, recebido {type(value).__name__}"
                elif expected_type == 'list' and not isinstance(value, list):
                    return False, f"Esperado list, recebido {type(value).__name__}"
                elif expected_type == 'dict' and not isinstance(value, dict):
                    return False, f"Esperado dict, recebido {type(value).__name__}"
            
            # Verificar range para números
            if isinstance(value, (int, float)):
                if 'min' in rules and value < rules['min']:
                    return False, f"Valor {value} menor que mínimo {rules['min']}"
                if 'max' in rules and value > rules['max']:
                    return False, f"Valor {value} maior que máximo {rules['max']}"
            
            # Verificar comprimento para strings e listas
            if isinstance(value, (str, list)):
                if 'min_length' in rules and len(value) < rules['min_length']:
                    return False, f"Comprimento {len(value)} menor que mínimo {rules['min_length']}"
                if 'max_length' in rules and len(value) > rules['max_length']:
                    return False, f"Comprimento {len(value)} maior que máximo {rules['max_length']}"
            
            # Verificar valores permitidos
            if 'allowed_values' in rules:
                if value not in rules['allowed_values']:
                    return False, f"Valor {value} não está em {rules['allowed_values']}"
            
            # Verificar padrão regex para strings
            if isinstance(value, str) and 'pattern' in rules:
                import re
                if not re.match(rules['pattern'], value):
                    return False, f"Valor '{value}' não corresponde ao padrão {rules['pattern']}"
            
            # Validação customizada
            if 'custom_validator' in rules:
                validator_func = rules['custom_validator']
                if callable(validator_func):
                    is_valid, error_msg = validator_func(value)
                    if not is_valid:
                        return False, error_msg
            
            return True, ""
        
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"

class ConfigFileHandler(FileSystemEventHandler):
    """Handler para mudanças em arquivos de configuração"""
    
    def __init__(self, config_system):
        self.config_system = config_system
        self.logger = logging.getLogger("config_file_handler")
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix in ['.json', '.yaml', '.yml', '.ini', '.toml']:
                self.logger.info(f"Arquivo de configuração modificado: {file_path}")
                self.config_system.reload_config_file(file_path)
    
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix in ['.json', '.yaml', '.yml', '.ini', '.toml']:
                self.logger.info(f"Novo arquivo de configuração: {file_path}")
                self.config_system.load_config_file(file_path)

class DynamicConfigurationSystem:
    """Sistema de configuração dinâmica"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger("dynamic_config")
        if isinstance(config_dir, str):
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = config_dir or Path.cwd() / "config"
        
        # Armazenamento de configurações
        self.configurations: Dict[str, ConfigEntry] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        
        # Observadores de mudanças
        self.change_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.global_listeners: List[Callable] = []
        
        # Cache e otimização
        self.config_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 300  # 5 minutos
        
        # Monitoramento de arquivos
        self.file_observer: Optional[Observer] = None
        self.file_handler: Optional[ConfigFileHandler] = None
        self.monitored_files: Set[Path] = set()
        
        # Histórico de mudanças
        self.change_history: List[ConfigChangeEvent] = []
        self.max_history_size = 1000
        
        # Configurações de segurança
        self.encryption_key: Optional[bytes] = None
        self.sensitive_keys: Set[str] = set()
        
        # Lock para thread safety
        self.lock = threading.RLock()
        
        # Inicialização
        self.load_default_schemas()
        self.load_all_configurations()
        self.start_file_monitoring()
    
    def load_default_schemas(self):
        """Carrega schemas padrão"""
        default_schemas = [
            ConfigSchema(
                name="detection_engine",
                type=ConfigType.DETECTION,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "methods", "cache_enabled"],
                optional_fields=["timeout", "retry_count", "parallel_detection"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "timeout": {"type": "integer", "min": 1, "max": 3600},
                    "retry_count": {"type": "integer", "min": 0, "max": 10},
                    "methods": {"type": "list", "min_length": 1}
                },
                default_values={
                    "enabled": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "cache_enabled": True,
                    "parallel_detection": True
                },
                description="Configurações do motor de detecção"
            ),
            ConfigSchema(
                name="compatibility_matrix",
                type=ConfigType.COMPATIBILITY,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "auto_resolve"],
                optional_fields=["strict_mode", "conflict_threshold"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "auto_resolve": {"type": "boolean"},
                    "strict_mode": {"type": "boolean"},
                    "conflict_threshold": {"type": "float", "min": 0.0, "max": 1.0}
                },
                default_values={
                    "enabled": True,
                    "auto_resolve": False,
                    "strict_mode": False,
                    "conflict_threshold": 0.7
                },
                description="Configurações da matriz de compatibilidade"
            ),
            ConfigSchema(
                name="contamination_detector",
                type=ConfigType.SECURITY,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "monitoring_interval"],
                optional_fields=["auto_cleanup", "severity_threshold"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "monitoring_interval": {"type": "integer", "min": 60, "max": 3600},
                    "auto_cleanup": {"type": "boolean"},
                    "severity_threshold": {"type": "string", "allowed_values": ["low", "medium", "high", "critical"]}
                },
                default_values={
                    "enabled": True,
                    "monitoring_interval": 300,
                    "auto_cleanup": False,
                    "severity_threshold": "medium"
                },
                description="Configurações do detector de contaminação"
            ),
            ConfigSchema(
                name="integrity_checker",
                type=ConfigType.SECURITY,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "check_interval"],
                optional_fields=["auto_repair", "checksum_algorithm"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "check_interval": {"type": "integer", "min": 300, "max": 86400},
                    "auto_repair": {"type": "boolean"},
                    "checksum_algorithm": {"type": "string", "allowed_values": ["md5", "sha1", "sha256", "sha512"]}
                },
                default_values={
                    "enabled": True,
                    "check_interval": 3600,
                    "auto_repair": False,
                    "checksum_algorithm": "sha256"
                },
                description="Configurações do verificador de integridade"
            ),
            ConfigSchema(
                name="dependency_analyzer",
                type=ConfigType.DETECTION,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "max_depth"],
                optional_fields=["include_transitive", "conflict_detection"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "max_depth": {"type": "integer", "min": 1, "max": 10},
                    "include_transitive": {"type": "boolean"},
                    "conflict_detection": {"type": "boolean"}
                },
                default_values={
                    "enabled": True,
                    "max_depth": 5,
                    "include_transitive": True,
                    "conflict_detection": True
                },
                description="Configurações do analisador de dependências"
            ),
            ConfigSchema(
                name="auto_repair",
                type=ConfigType.SYSTEM,
                scope=ConfigScope.GLOBAL,
                format=ConfigFormat.YAML,
                required_fields=["enabled", "max_attempts"],
                optional_fields=["backup_before_repair", "repair_timeout"],
                validation_rules={
                    "enabled": {"type": "boolean"},
                    "max_attempts": {"type": "integer", "min": 1, "max": 5},
                    "backup_before_repair": {"type": "boolean"},
                    "repair_timeout": {"type": "integer", "min": 30, "max": 1800}
                },
                default_values={
                    "enabled": True,
                    "max_attempts": 3,
                    "backup_before_repair": True,
                    "repair_timeout": 300
                },
                description="Configurações do sistema de auto-reparo"
            )
        ]
        
        for schema in default_schemas:
            self.schemas[schema.name] = schema
    
    def load_all_configurations(self):
        """Carrega todas as configurações"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar arquivos de configuração
        config_files = list(self.config_dir.rglob('*.json')) + \
                      list(self.config_dir.rglob('*.yaml')) + \
                      list(self.config_dir.rglob('*.yml'))
        
        for config_file in config_files:
            self.load_config_file(config_file)
        
        # Carregar configurações padrão para schemas sem configuração
        for schema_name, schema in self.schemas.items():
            if not any(config.key.startswith(schema_name) for config in self.configurations.values()):
                self.load_default_configuration(schema)
    
    def load_config_file(self, file_path: Path):
        """Carrega arquivo de configuração"""
        try:
            with self.lock:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    self.logger.warning(f"Formato não suportado: {file_path}")
                    return
                
                if not isinstance(data, dict):
                    self.logger.warning(f"Arquivo de configuração inválido: {file_path}")
                    return
                
                # Determinar tipo e escopo baseado no nome do arquivo
                file_name = file_path.stem
                config_type = self._determine_config_type(file_name)
                config_scope = self._determine_config_scope(file_path)
                
                # Carregar configurações
                for key, value in data.items():
                    full_key = f"{file_name}.{key}" if '.' not in key else key
                    
                    config_entry = ConfigEntry(
                        key=full_key,
                        value=value,
                        type=config_type,
                        scope=config_scope,
                        source=str(file_path)
                    )
                    
                    # Validar se há schema
                    if file_name in self.schemas:
                        is_valid, error_msg = self.validate_configuration(config_entry, self.schemas[file_name])
                        if not is_valid:
                            self.logger.warning(f"Configuração inválida {full_key}: {error_msg}")
                            continue
                    
                    self.configurations[full_key] = config_entry
                
                self.monitored_files.add(file_path)
                self.logger.info(f"Configuração carregada: {file_path}")
        
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração {file_path}: {e}")
    
    def load_default_configuration(self, schema: ConfigSchema):
        """Carrega configuração padrão para um schema"""
        with self.lock:
            for key, value in schema.default_values.items():
                full_key = f"{schema.name}.{key}"
                
                if full_key not in self.configurations:
                    config_entry = ConfigEntry(
                        key=full_key,
                        value=value,
                        type=schema.type,
                        scope=schema.scope,
                        source="default"
                    )
                    
                    self.configurations[full_key] = config_entry
    
    def reload_config_file(self, file_path: Path):
        """Recarrega arquivo de configuração"""
        # Remover configurações antigas do arquivo
        old_configs = [key for key, config in self.configurations.items() 
                      if config.source == str(file_path)]
        
        for key in old_configs:
            old_value = self.configurations[key].value
            del self.configurations[key]
            
            # Notificar mudança
            self._notify_change(key, old_value, None, "delete", str(file_path))
        
        # Carregar nova configuração
        self.load_config_file(file_path)
    
    def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """Obtém valor de configuração"""
        # Verificar cache primeiro
        if use_cache and key in self.config_cache:
            cache_time = self.cache_timestamps.get(key, 0)
            if time.time() - cache_time < self.cache_ttl:
                return self.config_cache[key]
        
        with self.lock:
            if key in self.configurations:
                value = self.configurations[key].value
                
                # Descriptografar se necessário
                if self.configurations[key].encrypted:
                    value = self._decrypt_value(value)
                
                # Atualizar cache
                if use_cache:
                    self.config_cache[key] = value
                    self.cache_timestamps[key] = time.time()
                
                return value
            
            # Tentar buscar por padrão hierárquico
            parts = key.split('.')
            for i in range(len(parts) - 1, 0, -1):
                parent_key = '.'.join(parts[:i])
                if parent_key in self.configurations:
                    parent_value = self.configurations[parent_key].value
                    if isinstance(parent_value, dict):
                        nested_key = '.'.join(parts[i:])
                        nested_value = self._get_nested_value(parent_value, nested_key)
                        if nested_value is not None:
                            return nested_value
            
            return default
    
    def set(self, key: str, value: Any, config_type: ConfigType = ConfigType.USER, 
           config_scope: ConfigScope = ConfigScope.USER, source: str = "runtime",
           validate: bool = True, encrypt: bool = False) -> bool:
        """Define valor de configuração"""
        try:
            with self.lock:
                # Validar se necessário
                if validate:
                    schema_name = key.split('.')[0]
                    if schema_name in self.schemas:
                        config_entry = ConfigEntry(
                            key=key, value=value, type=config_type, 
                            scope=config_scope, source=source
                        )
                        is_valid, error_msg = self.validate_configuration(config_entry, self.schemas[schema_name])
                        if not is_valid:
                            self.logger.warning(f"Configuração inválida {key}: {error_msg}")
                            return False
                
                # Obter valor antigo
                old_value = self.configurations.get(key, ConfigEntry("", None, config_type, config_scope, "")).value
                
                # Criptografar se necessário
                stored_value = value
                if encrypt or key in self.sensitive_keys:
                    stored_value = self._encrypt_value(value)
                    encrypt = True
                
                # Criar entrada de configuração
                config_entry = ConfigEntry(
                    key=key,
                    value=stored_value,
                    type=config_type,
                    scope=config_scope,
                    source=source,
                    encrypted=encrypt,
                    sensitive=key in self.sensitive_keys
                )
                
                self.configurations[key] = config_entry
                
                # Limpar cache
                if key in self.config_cache:
                    del self.config_cache[key]
                    del self.cache_timestamps[key]
                
                # Notificar mudança
                change_type = "create" if old_value is None else "update"
                self._notify_change(key, old_value, value, change_type, source)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Erro ao definir configuração {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove configuração"""
        try:
            with self.lock:
                if key in self.configurations:
                    old_value = self.configurations[key].value
                    source = self.configurations[key].source
                    
                    del self.configurations[key]
                    
                    # Limpar cache
                    if key in self.config_cache:
                        del self.config_cache[key]
                        del self.cache_timestamps[key]
                    
                    # Notificar mudança
                    self._notify_change(key, old_value, None, "delete", source)
                    
                    return True
                
                return False
        
        except Exception as e:
            self.logger.error(f"Erro ao remover configuração {key}: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Obtém todas as configurações de uma seção"""
        result = {}
        prefix = f"{section}."
        
        with self.lock:
            for key, config in self.configurations.items():
                if key.startswith(prefix):
                    sub_key = key[len(prefix):]
                    value = config.value
                    
                    if config.encrypted:
                        value = self._decrypt_value(value)
                    
                    result[sub_key] = value
        
        return result
    
    def add_change_listener(self, key_pattern: str, callback: Callable[[ConfigChangeEvent], None]):
        """Adiciona listener para mudanças de configuração"""
        self.change_listeners[key_pattern].append(callback)
    
    def add_global_listener(self, callback: Callable[[ConfigChangeEvent], None]):
        """Adiciona listener global para mudanças"""
        self.global_listeners.append(callback)
    
    def validate_configuration(self, config: ConfigEntry, schema: ConfigSchema) -> tuple[bool, str]:
        """Valida configuração contra schema"""
        key_parts = config.key.split('.')
        if len(key_parts) < 2:
            return False, "Chave de configuração inválida"
        
        field_name = key_parts[1]
        
        # Verificar se campo é obrigatório
        if field_name in schema.required_fields:
            if config.value is None:
                return False, f"Campo obrigatório '{field_name}' não pode ser None"
        
        # Verificar se campo é conhecido
        all_fields = schema.required_fields + schema.optional_fields
        if field_name not in all_fields:
            return False, f"Campo desconhecido '{field_name}'"
        
        # Validar valor
        if field_name in schema.validation_rules:
            return ConfigValidator.validate_value(config.value, schema.validation_rules[field_name])
        
        return True, ""
    
    def export_configuration(self, format: ConfigFormat = ConfigFormat.YAML, 
                           include_sensitive: bool = False) -> str:
        """Exporta configuração"""
        export_data = {}
        
        with self.lock:
            for key, config in self.configurations.items():
                if config.sensitive and not include_sensitive:
                    continue
                
                value = config.value
                if config.encrypted:
                    if include_sensitive:
                        value = self._decrypt_value(value)
                    else:
                        value = "[ENCRYPTED]"
                
                # Organizar hierarquicamente
                parts = key.split('.')
                current = export_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
        
        if format == ConfigFormat.YAML:
            return yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
        elif format == ConfigFormat.JSON:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return str(export_data)
    
    def import_configuration(self, data: str, format: ConfigFormat = ConfigFormat.YAML,
                           source: str = "import", validate: bool = True) -> bool:
        """Importa configuração"""
        try:
            if format == ConfigFormat.YAML:
                config_data = yaml.safe_load(data)
            elif format == ConfigFormat.JSON:
                config_data = json.loads(data)
            else:
                return False
            
            if not isinstance(config_data, dict):
                return False
            
            # Importar configurações
            def import_nested(data: dict, prefix: str = ""):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        import_nested(value, full_key)
                    else:
                        self.set(full_key, value, source=source, validate=validate)
            
            import_nested(config_data)
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao importar configuração: {e}")
            return False
    
    def start_file_monitoring(self):
        """Inicia monitoramento de arquivos"""
        if self.file_observer is None:
            self.file_handler = ConfigFileHandler(self)
            self.file_observer = Observer()
            self.file_observer.schedule(self.file_handler, str(self.config_dir), recursive=True)
            self.file_observer.start()
            self.logger.info("Monitoramento de arquivos de configuração iniciado")
    
    def stop_file_monitoring(self):
        """Para monitoramento de arquivos"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
            self.file_handler = None
            self.logger.info("Monitoramento de arquivos de configuração parado")
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Obtém informações sobre configurações"""
        with self.lock:
            type_counts = defaultdict(int)
            scope_counts = defaultdict(int)
            source_counts = defaultdict(int)
            
            for config in self.configurations.values():
                type_counts[config.type.value] += 1
                scope_counts[config.scope.value] += 1
                source_counts[config.source] += 1
            
            return {
                'total_configurations': len(self.configurations),
                'schemas_loaded': len(self.schemas),
                'monitored_files': len(self.monitored_files),
                'cache_entries': len(self.config_cache),
                'change_listeners': sum(len(listeners) for listeners in self.change_listeners.values()),
                'global_listeners': len(self.global_listeners),
                'configurations_by_type': dict(type_counts),
                'configurations_by_scope': dict(scope_counts),
                'configurations_by_source': dict(source_counts),
                'change_history_size': len(self.change_history)
            }
    
    def _determine_config_type(self, file_name: str) -> ConfigType:
        """Determina tipo de configuração baseado no nome do arquivo"""
        type_mapping = {
            'detection': ConfigType.DETECTION,
            'installation': ConfigType.INSTALLATION,
            'compatibility': ConfigType.COMPATIBILITY,
            'performance': ConfigType.PERFORMANCE,
            'security': ConfigType.SECURITY,
            'logging': ConfigType.LOGGING,
            'cache': ConfigType.CACHE,
            'network': ConfigType.NETWORK,
            'system': ConfigType.SYSTEM
        }
        
        for keyword, config_type in type_mapping.items():
            if keyword in file_name.lower():
                return config_type
        
        return ConfigType.USER
    
    def _determine_config_scope(self, file_path: Path) -> ConfigScope:
        """Determina escopo baseado no caminho do arquivo"""
        path_str = str(file_path).lower()
        
        if 'global' in path_str:
            return ConfigScope.GLOBAL
        elif 'user' in path_str:
            return ConfigScope.USER
        elif 'session' in path_str:
            return ConfigScope.SESSION
        elif 'component' in path_str:
            return ConfigScope.COMPONENT
        else:
            return ConfigScope.GLOBAL
    
    def _get_nested_value(self, data: dict, key: str) -> Any:
        """Obtém valor aninhado usando notação de ponto"""
        parts = key.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _notify_change(self, key: str, old_value: Any, new_value: Any, 
                      change_type: str, source: str):
        """Notifica mudança de configuração"""
        event = ConfigChangeEvent(
            key=key,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            source=source
        )
        
        # Adicionar ao histórico
        self.change_history.append(event)
        if len(self.change_history) > self.max_history_size:
            self.change_history.pop(0)
        
        # Notificar listeners específicos
        for pattern, listeners in self.change_listeners.items():
            if self._match_pattern(pattern, key):
                for listener in listeners:
                    try:
                        listener(event)
                    except Exception as e:
                        self.logger.error(f"Erro em listener de configuração: {e}")
        
        # Notificar listeners globais
        for listener in self.global_listeners:
            try:
                listener(event)
            except Exception as e:
                self.logger.error(f"Erro em listener global de configuração: {e}")
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Verifica se texto corresponde ao padrão"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def _encrypt_value(self, value: Any) -> str:
        """Criptografa valor (implementação básica)"""
        if self.encryption_key is None:
            return str(value)  # Sem criptografia se não há chave
        
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key)
            return f.encrypt(str(value).encode()).decode()
        except ImportError:
            self.logger.warning("Biblioteca de criptografia não disponível")
            return str(value)
        except Exception as e:
            self.logger.error(f"Erro ao criptografar: {e}")
            return str(value)
    
    def _decrypt_value(self, encrypted_value: str) -> Any:
        """Descriptografa valor"""
        if self.encryption_key is None:
            return encrypted_value
        
        try:
            from cryptography.fernet import Fernet
            f = Fernet(self.encryption_key)
            return f.decrypt(encrypted_value.encode()).decode()
        except ImportError:
            return encrypted_value
        except Exception as e:
            self.logger.error(f"Erro ao descriptografar: {e}")
            return encrypted_value
    
    def __del__(self):
        """Destructor"""
        self.stop_file_monitoring()

# Instância global
_config_system: Optional[DynamicConfigurationSystem] = None

def get_config_system() -> DynamicConfigurationSystem:
    """Obtém instância global do sistema de configuração"""
    global _config_system
    if _config_system is None:
        _config_system = DynamicConfigurationSystem()
    return _config_system

def get_config(key: str, default: Any = None) -> Any:
    """Função de conveniência para obter configuração"""
    return get_config_system().get(key, default)

def set_config(key: str, value: Any, **kwargs) -> bool:
    """Função de conveniência para definir configuração"""
    return get_config_system().set(key, value, **kwargs)