# -*- coding: utf-8 -*-
"""
Plugin Security and Sandboxing System
Módulo responsável por segurança, isolamento e sandboxing de plugins
"""

import os
import sys
import subprocess
import tempfile
import shutil
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import time
from contextlib import contextmanager

try:
    from .plugin_base import PluginMetadata, Permission, PluginInterface
    from .security_manager import SecurityManager, SecurityLevel, ThreatType
except ImportError:
    from plugin_base import PluginMetadata, Permission, PluginInterface
    from security_manager import SecurityManager, SecurityLevel, ThreatType

logger = logging.getLogger(__name__)

class SandboxType(Enum):
    """Tipos de sandbox disponíveis"""
    NONE = "none"
    RESTRICTED_FILESYSTEM = "restricted_filesystem"
    ISOLATED_PROCESS = "isolated_process"
    CONTAINER = "container"
    VIRTUAL_MACHINE = "virtual_machine"

class PluginTrustLevel(Enum):
    """Níveis de confiança para plugins"""
    UNTRUSTED = "untrusted"
    BASIC = "basic"
    TRUSTED = "trusted"
    SYSTEM = "system"

@dataclass
class SandboxConfig:
    """Configuração do ambiente sandbox"""
    sandbox_type: SandboxType
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_network_hosts: List[str] = field(default_factory=list)
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_execution_time: int = 300  # seconds
    temp_directory: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    allowed_system_calls: List[str] = field(default_factory=list)

@dataclass
class PluginSecurityProfile:
    """Perfil de segurança do plugin"""
    plugin_name: str
    trust_level: PluginTrustLevel
    permissions: Set[Permission]
    sandbox_config: SandboxConfig
    signature_verified: bool = False
    hash_verified: bool = False
    last_security_check: Optional[datetime] = None
    security_violations: List[str] = field(default_factory=list)

@dataclass
class SecurityViolation:
    """Violação de segurança detectada"""
    plugin_name: str
    violation_type: str
    description: str
    severity: SecurityLevel
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

class PluginSecurityManager:
    """
    Gerenciador de segurança para plugins
    
    Implementa:
    - Sandboxing de plugins
    - Verificação de assinaturas digitais
    - Sistema de permissões
    - Monitoramento de segurança
    - Isolamento de execução
    """
    
    def __init__(self, security_manager: Optional[SecurityManager] = None):
        """Inicializar gerenciador de segurança de plugins"""
        self.logger = logging.getLogger(__name__)
        self.security_manager = security_manager or SecurityManager()
        
        # Armazenamento de perfis de segurança
        self.security_profiles: Dict[str, PluginSecurityProfile] = {}
        self.trusted_signatures: Set[str] = set()
        self.blocked_plugins: Set[str] = set()
        
        # Configurações de segurança
        self.default_sandbox_config = SandboxConfig(
            sandbox_type=SandboxType.RESTRICTED_FILESYSTEM,
            allowed_paths=[
                str(Path.cwd()),
                tempfile.gettempdir()
            ],
            blocked_paths=[
                os.path.expanduser("~"),
                "/etc",
                "/sys",
                "/proc",
                "C:\\Windows",
                "C:\\Program Files"
            ],
            max_memory_mb=256,
            max_cpu_percent=25,
            max_execution_time=60
        )
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Carregar configurações
        self._load_security_config()
        
        self.logger.info("Plugin security manager initialized")
    
    def validate_plugin_security(self, plugin_path: Path, metadata: PluginMetadata) -> Tuple[bool, List[str]]:
        """
        Validar segurança do plugin
        
        Args:
            plugin_path: Caminho do plugin
            metadata: Metadados do plugin
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, security_issues)
        """
        issues = []
        
        try:
            # Verificar assinatura digital
            if not self._verify_plugin_signature(plugin_path, metadata):
                issues.append("Plugin signature verification failed")
            
            # Verificar hash do plugin
            if not self._verify_plugin_hash(plugin_path, metadata):
                issues.append("Plugin hash verification failed")
            
            # Validar permissões solicitadas
            permission_issues = self._validate_permissions(metadata.permissions)
            issues.extend(permission_issues)
            
            # Escanear por código malicioso
            malware_issues = self._scan_for_malware(plugin_path)
            issues.extend(malware_issues)
            
            # Verificar dependências
            dependency_issues = self._validate_dependencies(metadata.dependencies)
            issues.extend(dependency_issues)
            
            is_valid = len(issues) == 0
            
            # Registrar resultado da validação
            self.security_manager.audit_critical_operation(
                operation="plugin_security_validation",
                component="plugin_security",
                details={
                    "plugin_name": metadata.name,
                    "plugin_version": metadata.version,
                    "is_valid": is_valid,
                    "issues_count": len(issues),
                    "issues": issues
                },
                success=is_valid,
                security_level=SecurityLevel.HIGH if not is_valid else SecurityLevel.MEDIUM
            )
            
            return is_valid, issues
            
        except Exception as e:
            self.logger.error(f"Error validating plugin security: {e}")
            issues.append(f"Security validation error: {str(e)}")
            return False, issues
    
    def create_security_profile(self, metadata: PluginMetadata, trust_level: PluginTrustLevel = PluginTrustLevel.UNTRUSTED) -> PluginSecurityProfile:
        """
        Criar perfil de segurança para plugin
        
        Args:
            metadata: Metadados do plugin
            trust_level: Nível de confiança
            
        Returns:
            PluginSecurityProfile: Perfil de segurança criado
        """
        # Determinar configuração de sandbox baseada no nível de confiança
        sandbox_config = self._create_sandbox_config(trust_level, metadata.permissions)
        
        profile = PluginSecurityProfile(
            plugin_name=metadata.name,
            trust_level=trust_level,
            permissions=set(metadata.permissions),
            sandbox_config=sandbox_config,
            last_security_check=datetime.now()
        )
        
        with self._lock:
            self.security_profiles[metadata.name] = profile
        
        self.logger.info(f"Created security profile for plugin {metadata.name} with trust level {trust_level.value}")
        return profile
    
    @contextmanager
    def create_sandbox_environment(self, plugin_name: str):
        """
        Criar ambiente sandbox para execução do plugin
        
        Args:
            plugin_name: Nome do plugin
            
        Yields:
            Dict[str, Any]: Contexto do ambiente sandbox
        """
        profile = self.security_profiles.get(plugin_name)
        if not profile:
            raise ValueError(f"No security profile found for plugin {plugin_name}")
        
        sandbox_context = None
        temp_dir = None
        
        try:
            # Criar diretório temporário isolado
            temp_dir = tempfile.mkdtemp(prefix=f"plugin_{plugin_name}_")
            
            # Configurar ambiente sandbox
            sandbox_context = {
                "temp_directory": temp_dir,
                "allowed_paths": profile.sandbox_config.allowed_paths + [temp_dir],
                "blocked_paths": profile.sandbox_config.blocked_paths,
                "permissions": profile.permissions,
                "max_memory_mb": profile.sandbox_config.max_memory_mb,
                "max_execution_time": profile.sandbox_config.max_execution_time,
                "environment_variables": profile.sandbox_config.environment_variables.copy()
            }
            
            # Configurar variáveis de ambiente restritas
            sandbox_context["environment_variables"].update({
                "PLUGIN_SANDBOX": "true",
                "PLUGIN_NAME": plugin_name,
                "PLUGIN_TEMP_DIR": temp_dir,
                "PYTHONPATH": temp_dir
            })
            
            self.logger.info(f"Created sandbox environment for plugin {plugin_name}")
            yield sandbox_context
            
        except Exception as e:
            self.logger.error(f"Error creating sandbox environment: {e}")
            raise
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.logger.debug(f"Cleaned up sandbox directory: {temp_dir}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup sandbox directory {temp_dir}: {e}")
    
    def check_permission(self, plugin_name: str, permission: Permission) -> bool:
        """
        Verificar se plugin tem permissão específica
        
        Args:
            plugin_name: Nome do plugin
            permission: Permissão a verificar
            
        Returns:
            bool: True se tem permissão
        """
        profile = self.security_profiles.get(plugin_name)
        if not profile:
            return False
        
        has_permission = permission in profile.permissions
        
        # Registrar tentativa de acesso
        self.security_manager.audit_critical_operation(
            operation="permission_check",
            component="plugin_security",
            details={
                "plugin_name": plugin_name,
                "permission": permission.value,
                "granted": has_permission
            },
            success=has_permission,
            security_level=SecurityLevel.MEDIUM
        )
        
        return has_permission
    
    def report_security_violation(self, plugin_name: str, violation_type: str, description: str, severity: SecurityLevel = SecurityLevel.MEDIUM):
        """
        Reportar violação de segurança
        
        Args:
            plugin_name: Nome do plugin
            violation_type: Tipo da violação
            description: Descrição da violação
            severity: Severidade da violação
        """
        violation = SecurityViolation(
            plugin_name=plugin_name,
            violation_type=violation_type,
            description=description,
            severity=severity,
            timestamp=datetime.now()
        )
        
        # Adicionar à lista de violações do perfil
        profile = self.security_profiles.get(plugin_name)
        if profile:
            profile.security_violations.append(f"{violation_type}: {description}")
        
        # Registrar no sistema de auditoria
        self.security_manager.audit_critical_operation(
            operation="security_violation",
            component="plugin_security",
            details={
                "plugin_name": plugin_name,
                "violation_type": violation_type,
                "description": description,
                "severity": severity.value
            },
            success=False,
            security_level=severity
        )
        
        # Tomar ações baseadas na severidade
        if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            self.blocked_plugins.add(plugin_name)
            self.logger.warning(f"Plugin {plugin_name} blocked due to {severity.value} security violation: {description}")
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Gerar relatório de segurança dos plugins
        
        Returns:
            Dict[str, Any]: Relatório de segurança
        """
        total_plugins = len(self.security_profiles)
        trusted_plugins = sum(1 for p in self.security_profiles.values() if p.trust_level in [PluginTrustLevel.TRUSTED, PluginTrustLevel.SYSTEM])
        blocked_plugins = len(self.blocked_plugins)
        
        violations_by_severity = {}
        for profile in self.security_profiles.values():
            for violation in profile.security_violations:
                severity = "medium"  # Default
                violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
        
        return {
            "summary": {
                "total_plugins": total_plugins,
                "trusted_plugins": trusted_plugins,
                "blocked_plugins": blocked_plugins,
                "security_violations": sum(violations_by_severity.values())
            },
            "trust_levels": {
                level.value: sum(1 for p in self.security_profiles.values() if p.trust_level == level)
                for level in PluginTrustLevel
            },
            "violations_by_severity": violations_by_severity,
            "blocked_plugins_list": list(self.blocked_plugins),
            "sandbox_types": {
                stype.value: sum(1 for p in self.security_profiles.values() if p.sandbox_config.sandbox_type == stype)
                for stype in SandboxType
            }
        }
    
    def _verify_plugin_signature(self, plugin_path: Path, metadata: PluginMetadata) -> bool:
        """
        Verificar assinatura digital do plugin
        
        Args:
            plugin_path: Caminho do plugin
            metadata: Metadados do plugin
            
        Returns:
            bool: True se assinatura é válida
        """
        if not metadata.signature:
            return False
        
        # TODO: Implementar verificação real de assinatura digital
        # Por enquanto, verificar se a assinatura está na lista de confiáveis
        return metadata.signature in self.trusted_signatures
    
    def _verify_plugin_hash(self, plugin_path: Path, metadata: PluginMetadata) -> bool:
        """
        Verificar hash do plugin
        
        Args:
            plugin_path: Caminho do plugin
            metadata: Metadados do plugin
            
        Returns:
            bool: True se hash é válido
        """
        try:
            # Calcular hash dos arquivos do plugin
            plugin_hash = self._calculate_plugin_hash(plugin_path)
            
            # TODO: Comparar com hash esperado (pode vir dos metadados ou de um registro)
            # Por enquanto, apenas verificar se o hash foi calculado com sucesso
            return plugin_hash is not None
            
        except Exception as e:
            self.logger.error(f"Error verifying plugin hash: {e}")
            return False
    
    def _calculate_plugin_hash(self, plugin_path: Path) -> Optional[str]:
        """
        Calcular hash SHA256 dos arquivos do plugin
        
        Args:
            plugin_path: Caminho do plugin
            
        Returns:
            Optional[str]: Hash SHA256 ou None se erro
        """
        try:
            hasher = hashlib.sha256()
            
            # Hash de todos os arquivos Python no plugin
            for py_file in plugin_path.rglob("*.py"):
                with open(py_file, 'rb') as f:
                    hasher.update(f.read())
            
            return hasher.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating plugin hash: {e}")
            return None
    
    def _validate_permissions(self, permissions: List[Permission]) -> List[str]:
        """
        Validar permissões solicitadas pelo plugin
        
        Args:
            permissions: Lista de permissões
            
        Returns:
            List[str]: Lista de problemas encontrados
        """
        issues = []
        
        # Verificar permissões perigosas
        dangerous_permissions = {
            Permission.SYSTEM_COMMANDS,
            Permission.PRIVILEGED_OPERATIONS,
            Permission.REGISTRY_WRITE
        }
        
        for permission in permissions:
            if permission in dangerous_permissions:
                issues.append(f"Dangerous permission requested: {permission.value}")
        
        # Verificar combinações suspeitas
        if Permission.NETWORK_ACCESS in permissions and Permission.WRITE_FILESYSTEM in permissions:
            issues.append("Suspicious permission combination: network access + file write")
        
        return issues
    
    def _scan_for_malware(self, plugin_path: Path) -> List[str]:
        """
        Escanear plugin por código malicioso
        
        Args:
            plugin_path: Caminho do plugin
            
        Returns:
            List[str]: Lista de problemas encontrados
        """
        issues = []
        
        try:
            # Padrões suspeitos para detectar
            suspicious_patterns = [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'subprocess\.',
                r'os\.system',
                r'os\.popen',
                r'socket\.',
                r'urllib',
                r'requests\.',
                r'base64\.decode',
                r'pickle\.loads'
            ]
            
            # Escanear arquivos Python
            for py_file in plugin_path.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in suspicious_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(f"Suspicious code pattern found in {py_file.name}: {pattern}")
                            
                except Exception as e:
                    self.logger.warning(f"Error scanning file {py_file}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error scanning plugin for malware: {e}")
            issues.append(f"Malware scan error: {str(e)}")
        
        return issues
    
    def _validate_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Validar dependências do plugin
        
        Args:
            dependencies: Lista de dependências
            
        Returns:
            List[str]: Lista de problemas encontrados
        """
        issues = []
        
        # Lista de dependências suspeitas
        suspicious_deps = {
            'keylogger', 'pynput', 'pyautogui', 'psutil',
            'scapy', 'nmap', 'paramiko', 'fabric'
        }
        
        for dep in dependencies:
            dep_name = dep.split('==')[0].split('>=')[0].split('<=')[0].strip()
            if dep_name.lower() in suspicious_deps:
                issues.append(f"Suspicious dependency: {dep_name}")
        
        return issues
    
    def _create_sandbox_config(self, trust_level: PluginTrustLevel, permissions: List[Permission]) -> SandboxConfig:
        """
        Criar configuração de sandbox baseada no nível de confiança
        
        Args:
            trust_level: Nível de confiança
            permissions: Permissões do plugin
            
        Returns:
            SandboxConfig: Configuração do sandbox
        """
        config = SandboxConfig(
            sandbox_type=SandboxType.RESTRICTED_FILESYSTEM,
            allowed_paths=self.default_sandbox_config.allowed_paths.copy(),
            blocked_paths=self.default_sandbox_config.blocked_paths.copy(),
            max_memory_mb=self.default_sandbox_config.max_memory_mb,
            max_cpu_percent=self.default_sandbox_config.max_cpu_percent,
            max_execution_time=self.default_sandbox_config.max_execution_time
        )
        
        # Ajustar configuração baseada no nível de confiança
        if trust_level == PluginTrustLevel.SYSTEM:
            config.sandbox_type = SandboxType.NONE
            config.max_memory_mb = 1024
            config.max_cpu_percent = 80
            config.max_execution_time = 600
        elif trust_level == PluginTrustLevel.TRUSTED:
            config.max_memory_mb = 512
            config.max_cpu_percent = 50
            config.max_execution_time = 300
        elif trust_level == PluginTrustLevel.BASIC:
            config.max_memory_mb = 256
            config.max_cpu_percent = 25
            config.max_execution_time = 120
        else:  # UNTRUSTED
            config.sandbox_type = SandboxType.ISOLATED_PROCESS
            config.max_memory_mb = 128
            config.max_cpu_percent = 15
            config.max_execution_time = 60
        
        # Ajustar baseado nas permissões
        if Permission.WRITE_FILESYSTEM in permissions:
            config.allowed_paths.append(str(Path.cwd() / "data"))
        
        if Permission.NETWORK_ACCESS in permissions:
            config.allowed_network_hosts = ["api.github.com", "pypi.org"]
        
        return config
    
    def _load_security_config(self):
        """
        Carregar configurações de segurança
        """
        try:
            config_path = Path("config/plugin_security.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Carregar assinaturas confiáveis
                self.trusted_signatures.update(config.get("trusted_signatures", []))
                
                # Carregar plugins bloqueados
                self.blocked_plugins.update(config.get("blocked_plugins", []))
                
                self.logger.info("Loaded plugin security configuration")
        except Exception as e:
            self.logger.warning(f"Could not load plugin security config: {e}")


# Instância global do gerenciador de segurança de plugins
plugin_security_manager = PluginSecurityManager()


if __name__ == "__main__":
    # Teste do sistema de segurança de plugins
    from .plugin_base import PluginMetadata, Permission
    
    # Criar metadados de teste
    test_metadata = PluginMetadata(
        name="test_plugin",
        version="1.0.0",
        author="Test Author",
        description="Test plugin for security validation",
        api_version="1.0",
        permissions=[Permission.READ_FILESYSTEM, Permission.NETWORK_ACCESS]
    )
    
    # Testar validação de segurança
    security_manager = PluginSecurityManager()
    
    # Criar perfil de segurança
    profile = security_manager.create_security_profile(test_metadata, PluginTrustLevel.BASIC)
    print(f"Created security profile: {profile.plugin_name}")
    
    # Testar verificação de permissões
    has_read = security_manager.check_permission("test_plugin", Permission.READ_FILESYSTEM)
    has_write = security_manager.check_permission("test_plugin", Permission.WRITE_FILESYSTEM)
    print(f"Read permission: {has_read}, Write permission: {has_write}")
    
    # Testar ambiente sandbox
    with security_manager.create_sandbox_environment("test_plugin") as sandbox:
        print(f"Sandbox created with temp dir: {sandbox['temp_directory']}")
    
    # Gerar relatório de segurança
    report = security_manager.get_security_report()
    print(f"Security report: {json.dumps(report, indent=2)}")