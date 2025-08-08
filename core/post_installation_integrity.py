#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Installation Integrity Checker - Sistema de Verificação de Integridade Pós-Instalação
Verifica a integridade de componentes após a instalação usando checksums e validações.
"""

import logging
import hashlib
import os
import json
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import winreg
import psutil

class IntegrityStatus(Enum):
    """Status de integridade"""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    UNKNOWN = "unknown"
    PARTIAL = "partial"

class CheckType(Enum):
    """Tipos de verificação"""
    FILE_CHECKSUM = "file_checksum"
    FILE_SIZE = "file_size"
    FILE_EXISTS = "file_exists"
    REGISTRY_KEY = "registry_key"
    COMMAND_OUTPUT = "command_output"
    SERVICE_STATUS = "service_status"
    PROCESS_RUNNING = "process_running"
    DIRECTORY_STRUCTURE = "directory_structure"
    PERMISSIONS = "permissions"
    DIGITAL_SIGNATURE = "digital_signature"

@dataclass
class IntegrityCheck:
    """Definição de uma verificação de integridade"""
    name: str
    type: CheckType
    target: str  # Arquivo, chave de registro, comando, etc.
    expected_value: Optional[str] = None
    critical: bool = True
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IntegrityResult:
    """Resultado de uma verificação de integridade"""
    check_name: str
    status: IntegrityStatus
    expected: Optional[str] = None
    actual: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComponentIntegrityReport:
    """Relatório de integridade de um componente"""
    component_name: str
    overall_status: IntegrityStatus
    checks_passed: int
    checks_failed: int
    checks_total: int
    critical_failures: int
    results: List[IntegrityResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    repair_actions: List[str] = field(default_factory=list)

class PostInstallationIntegrityChecker:
    """Verificador de integridade pós-instalação"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.logger = logging.getLogger("integrity_checker")
        self.cache_dir = cache_dir or Path.home() / ".env_dev" / "integrity_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache de checksums conhecidos
        self.checksum_cache: Dict[str, str] = {}
        self.load_checksum_cache()
        
        # Verificações padrão por tipo de componente
        self.default_checks = {
            'executable': self._get_executable_checks,
            'archive': self._get_archive_checks,
            'msi': self._get_msi_checks,
            'pip': self._get_pip_checks,
            'npm': self._get_npm_checks,
            'chocolatey': self._get_chocolatey_checks
        }
    
    def verify_component_integrity(self, component_name: str, 
                                 component_data: Dict[str, Any],
                                 installation_path: Optional[str] = None) -> ComponentIntegrityReport:
        """Verifica a integridade de um componente instalado"""
        self.logger.info(f"Verificando integridade de {component_name}")
        
        # Gerar verificações baseadas no componente
        checks = self._generate_integrity_checks(component_name, component_data, installation_path)
        
        # Executar verificações
        results = []
        for check in checks:
            result = self._execute_integrity_check(check)
            results.append(result)
        
        # Analisar resultados
        report = self._analyze_integrity_results(component_name, results)
        
        # Salvar no cache
        self._save_integrity_report(component_name, report)
        
        return report
    
    def _generate_integrity_checks(self, component_name: str, 
                                 component_data: Dict[str, Any],
                                 installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Gera verificações de integridade baseadas no componente"""
        checks = []
        
        # Verificações baseadas no método de instalação
        install_method = component_data.get('install_method', '').lower()
        if install_method in self.default_checks:
            checks.extend(self.default_checks[install_method](component_name, component_data, installation_path))
        
        # Verificações customizadas definidas no YAML
        if 'integrity_checks' in component_data:
            for check_data in component_data['integrity_checks']:
                check = IntegrityCheck(
                    name=check_data.get('name', f"{component_name}_custom"),
                    type=CheckType(check_data.get('type', 'file_exists')),
                    target=check_data.get('target', ''),
                    expected_value=check_data.get('expected'),
                    critical=check_data.get('critical', True),
                    timeout=check_data.get('timeout', 30),
                    metadata=check_data.get('metadata', {})
                )
                checks.append(check)
        
        # Verificações baseadas em verify_actions existentes
        if 'verify_actions' in component_data:
            for action in component_data['verify_actions']:
                checks.extend(self._convert_verify_action_to_checks(component_name, action))
        
        return checks
    
    def _get_executable_checks(self, component_name: str, component_data: Dict[str, Any], 
                             installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para executáveis"""
        checks = []
        
        # Verificar arquivo principal
        download_url = component_data.get('download_url', '')
        if download_url:
            filename = os.path.basename(download_url)
            if installation_path:
                target_path = os.path.join(installation_path, filename)
            else:
                target_path = filename
            
            # Verificação de existência
            checks.append(IntegrityCheck(
                name=f"{component_name}_file_exists",
                type=CheckType.FILE_EXISTS,
                target=target_path,
                critical=True
            ))
            
            # Verificação de checksum se disponível
            if 'hash' in component_data and component_data['hash'] != 'HASH_PENDENTE_VERIFICACAO':
                checks.append(IntegrityCheck(
                    name=f"{component_name}_checksum",
                    type=CheckType.FILE_CHECKSUM,
                    target=target_path,
                    expected_value=component_data['hash'],
                    critical=True,
                    metadata={'algorithm': component_data.get('hash_algorithm', 'sha256')}
                ))
            
            # Verificação de assinatura digital
            checks.append(IntegrityCheck(
                name=f"{component_name}_signature",
                type=CheckType.DIGITAL_SIGNATURE,
                target=target_path,
                critical=False
            ))
        
        return checks
    
    def _get_archive_checks(self, component_name: str, component_data: Dict[str, Any], 
                          installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para arquivos compactados"""
        checks = []
        
        extract_path = component_data.get('extract_path', installation_path)
        if extract_path:
            # Verificar se o diretório de extração existe
            checks.append(IntegrityCheck(
                name=f"{component_name}_extract_dir",
                type=CheckType.FILE_EXISTS,
                target=extract_path,
                critical=True
            ))
            
            # Verificar estrutura de diretórios
            checks.append(IntegrityCheck(
                name=f"{component_name}_directory_structure",
                type=CheckType.DIRECTORY_STRUCTURE,
                target=extract_path,
                critical=False,
                metadata={'min_files': 1}
            ))
        
        return checks
    
    def _get_msi_checks(self, component_name: str, component_data: Dict[str, Any], 
                       installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para instaladores MSI"""
        checks = []
        
        # Verificar entrada no registro
        checks.append(IntegrityCheck(
            name=f"{component_name}_registry",
            type=CheckType.REGISTRY_KEY,
            target=f"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
            critical=True,
            metadata={'search_pattern': component_name}
        ))
        
        return checks
    
    def _get_pip_checks(self, component_name: str, component_data: Dict[str, Any], 
                       installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para pacotes pip"""
        checks = []
        
        package_name = component_data.get('package_name', component_name)
        
        # Verificar se o pacote está instalado
        checks.append(IntegrityCheck(
            name=f"{component_name}_pip_installed",
            type=CheckType.COMMAND_OUTPUT,
            target="pip show " + package_name,
            expected_value="Name: " + package_name,
            critical=True
        ))
        
        return checks
    
    def _get_npm_checks(self, component_name: str, component_data: Dict[str, Any], 
                       installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para pacotes npm"""
        checks = []
        
        package_name = component_data.get('package_name', component_name)
        
        # Verificar se o pacote está instalado
        checks.append(IntegrityCheck(
            name=f"{component_name}_npm_installed",
            type=CheckType.COMMAND_OUTPUT,
            target="npm list -g " + package_name,
            critical=True
        ))
        
        return checks
    
    def _get_chocolatey_checks(self, component_name: str, component_data: Dict[str, Any], 
                             installation_path: Optional[str] = None) -> List[IntegrityCheck]:
        """Verificações para pacotes chocolatey"""
        checks = []
        
        package_name = component_data.get('package_name', component_name)
        
        # Verificar se o pacote está instalado
        checks.append(IntegrityCheck(
            name=f"{component_name}_choco_installed",
            type=CheckType.COMMAND_OUTPUT,
            target="choco list --local-only " + package_name,
            expected_value=package_name,
            critical=True
        ))
        
        return checks
    
    def _convert_verify_action_to_checks(self, component_name: str, action: Dict[str, Any]) -> List[IntegrityCheck]:
        """Converte verify_actions em IntegrityChecks"""
        checks = []
        
        action_type = action.get('type', '')
        
        if action_type == 'file_exists':
            checks.append(IntegrityCheck(
                name=f"{component_name}_{action_type}",
                type=CheckType.FILE_EXISTS,
                target=action.get('path', ''),
                critical=True
            ))
        
        elif action_type == 'command_exists':
            checks.append(IntegrityCheck(
                name=f"{component_name}_{action_type}",
                type=CheckType.COMMAND_OUTPUT,
                target=action.get('name', '') + " --version",
                critical=True
            ))
        
        elif action_type == 'registry_key':
            checks.append(IntegrityCheck(
                name=f"{component_name}_{action_type}",
                type=CheckType.REGISTRY_KEY,
                target=action.get('key', ''),
                critical=True
            ))
        
        return checks
    
    def _execute_integrity_check(self, check: IntegrityCheck) -> IntegrityResult:
        """Executa uma verificação de integridade"""
        start_time = time.time()
        
        try:
            if check.type == CheckType.FILE_EXISTS:
                status, actual, error = self._check_file_exists(check)
            elif check.type == CheckType.FILE_CHECKSUM:
                status, actual, error = self._check_file_checksum(check)
            elif check.type == CheckType.FILE_SIZE:
                status, actual, error = self._check_file_size(check)
            elif check.type == CheckType.REGISTRY_KEY:
                status, actual, error = self._check_registry_key(check)
            elif check.type == CheckType.COMMAND_OUTPUT:
                status, actual, error = self._check_command_output(check)
            elif check.type == CheckType.SERVICE_STATUS:
                status, actual, error = self._check_service_status(check)
            elif check.type == CheckType.PROCESS_RUNNING:
                status, actual, error = self._check_process_running(check)
            elif check.type == CheckType.DIRECTORY_STRUCTURE:
                status, actual, error = self._check_directory_structure(check)
            elif check.type == CheckType.PERMISSIONS:
                status, actual, error = self._check_permissions(check)
            elif check.type == CheckType.DIGITAL_SIGNATURE:
                status, actual, error = self._check_digital_signature(check)
            else:
                status, actual, error = IntegrityStatus.UNKNOWN, None, f"Tipo de verificação não suportado: {check.type}"
        
        except Exception as e:
            status, actual, error = IntegrityStatus.UNKNOWN, None, str(e)
        
        execution_time = time.time() - start_time
        
        return IntegrityResult(
            check_name=check.name,
            status=status,
            expected=check.expected_value,
            actual=actual,
            error_message=error,
            execution_time=execution_time,
            metadata=check.metadata
        )
    
    def _check_file_exists(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica se um arquivo existe"""
        try:
            if os.path.exists(check.target):
                return IntegrityStatus.VALID, "exists", None
            else:
                return IntegrityStatus.MISSING, "not_found", f"Arquivo não encontrado: {check.target}"
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_file_checksum(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica checksum de um arquivo"""
        try:
            if not os.path.exists(check.target):
                return IntegrityStatus.MISSING, None, f"Arquivo não encontrado: {check.target}"
            
            algorithm = check.metadata.get('algorithm', 'sha256')
            actual_hash = self._calculate_file_hash(check.target, algorithm)
            
            if actual_hash == check.expected_value:
                return IntegrityStatus.VALID, actual_hash, None
            else:
                return IntegrityStatus.CORRUPTED, actual_hash, f"Checksum não confere. Esperado: {check.expected_value}, Atual: {actual_hash}"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_file_size(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica tamanho de um arquivo"""
        try:
            if not os.path.exists(check.target):
                return IntegrityStatus.MISSING, None, f"Arquivo não encontrado: {check.target}"
            
            actual_size = os.path.getsize(check.target)
            expected_size = int(check.expected_value) if check.expected_value else None
            
            if expected_size is None:
                return IntegrityStatus.VALID, str(actual_size), None
            
            if actual_size == expected_size:
                return IntegrityStatus.VALID, str(actual_size), None
            else:
                return IntegrityStatus.INVALID, str(actual_size), f"Tamanho incorreto. Esperado: {expected_size}, Atual: {actual_size}"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_registry_key(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica chave do registro"""
        try:
            # Parsear a chave do registro
            parts = check.target.split('\\')
            if len(parts) < 2:
                return IntegrityStatus.INVALID, None, "Formato de chave de registro inválido"
            
            root_key = parts[0]
            subkey = '\\'.join(parts[1:])
            
            # Mapear root keys
            root_map = {
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT
            }
            
            if root_key not in root_map:
                return IntegrityStatus.INVALID, None, f"Root key não suportada: {root_key}"
            
            # Tentar abrir a chave
            try:
                with winreg.OpenKey(root_map[root_key], subkey):
                    return IntegrityStatus.VALID, "exists", None
            except FileNotFoundError:
                return IntegrityStatus.MISSING, "not_found", f"Chave de registro não encontrada: {check.target}"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_command_output(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica saída de comando"""
        try:
            result = subprocess.run(
                check.target.split(),
                capture_output=True,
                text=True,
                timeout=check.timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                if check.expected_value:
                    if check.expected_value in output:
                        return IntegrityStatus.VALID, output, None
                    else:
                        return IntegrityStatus.INVALID, output, f"Saída não contém valor esperado: {check.expected_value}"
                else:
                    return IntegrityStatus.VALID, output, None
            else:
                return IntegrityStatus.INVALID, result.stderr, f"Comando falhou com código {result.returncode}"
        
        except subprocess.TimeoutExpired:
            return IntegrityStatus.UNKNOWN, None, f"Comando expirou após {check.timeout} segundos"
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_service_status(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica status de serviço"""
        try:
            # Usar sc query para verificar serviço
            result = subprocess.run(
                ['sc', 'query', check.target],
                capture_output=True,
                text=True,
                timeout=check.timeout
            )
            
            if result.returncode == 0:
                if "RUNNING" in result.stdout:
                    return IntegrityStatus.VALID, "running", None
                else:
                    return IntegrityStatus.INVALID, "not_running", f"Serviço {check.target} não está rodando"
            else:
                return IntegrityStatus.MISSING, "not_found", f"Serviço {check.target} não encontrado"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_process_running(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica se processo está rodando"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and check.target.lower() in proc.info['name'].lower():
                    return IntegrityStatus.VALID, "running", None
            
            return IntegrityStatus.INVALID, "not_running", f"Processo {check.target} não está rodando"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_directory_structure(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica estrutura de diretório"""
        try:
            if not os.path.exists(check.target):
                return IntegrityStatus.MISSING, None, f"Diretório não encontrado: {check.target}"
            
            if not os.path.isdir(check.target):
                return IntegrityStatus.INVALID, "not_directory", f"Caminho não é um diretório: {check.target}"
            
            # Contar arquivos
            file_count = sum(1 for _ in Path(check.target).rglob('*') if _.is_file())
            min_files = check.metadata.get('min_files', 0)
            
            if file_count >= min_files:
                return IntegrityStatus.VALID, str(file_count), None
            else:
                return IntegrityStatus.PARTIAL, str(file_count), f"Poucos arquivos encontrados. Mínimo: {min_files}, Atual: {file_count}"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_permissions(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica permissões de arquivo"""
        try:
            if not os.path.exists(check.target):
                return IntegrityStatus.MISSING, None, f"Arquivo não encontrado: {check.target}"
            
            # Verificar se é legível
            if os.access(check.target, os.R_OK):
                permissions = "readable"
                if os.access(check.target, os.W_OK):
                    permissions += ",writable"
                if os.access(check.target, os.X_OK):
                    permissions += ",executable"
                
                return IntegrityStatus.VALID, permissions, None
            else:
                return IntegrityStatus.INVALID, "no_access", f"Sem permissão de leitura: {check.target}"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _check_digital_signature(self, check: IntegrityCheck) -> Tuple[IntegrityStatus, Optional[str], Optional[str]]:
        """Verifica assinatura digital"""
        try:
            if not os.path.exists(check.target):
                return IntegrityStatus.MISSING, None, f"Arquivo não encontrado: {check.target}"
            
            # Usar PowerShell para verificar assinatura
            ps_command = f"Get-AuthenticodeSignature '{check.target}' | Select-Object Status"
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=check.timeout
            )
            
            if result.returncode == 0:
                if "Valid" in result.stdout:
                    return IntegrityStatus.VALID, "signed", None
                elif "NotSigned" in result.stdout:
                    return IntegrityStatus.INVALID, "not_signed", "Arquivo não possui assinatura digital"
                else:
                    return IntegrityStatus.INVALID, "invalid_signature", "Assinatura digital inválida"
            else:
                return IntegrityStatus.UNKNOWN, None, "Erro ao verificar assinatura"
        
        except Exception as e:
            return IntegrityStatus.UNKNOWN, None, str(e)
    
    def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calcula hash de um arquivo"""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def _analyze_integrity_results(self, component_name: str, 
                                 results: List[IntegrityResult]) -> ComponentIntegrityReport:
        """Analisa resultados e gera relatório"""
        passed = sum(1 for r in results if r.status == IntegrityStatus.VALID)
        failed = sum(1 for r in results if r.status in [IntegrityStatus.INVALID, IntegrityStatus.CORRUPTED, IntegrityStatus.MISSING])
        total = len(results)
        
        # Contar falhas críticas
        critical_failures = 0
        for result in results:
            # Assumir que verificações com erro são críticas
            if result.status in [IntegrityStatus.INVALID, IntegrityStatus.CORRUPTED, IntegrityStatus.MISSING]:
                critical_failures += 1
        
        # Determinar status geral
        if failed == 0:
            overall_status = IntegrityStatus.VALID
        elif critical_failures > 0:
            overall_status = IntegrityStatus.CORRUPTED
        elif passed > failed:
            overall_status = IntegrityStatus.PARTIAL
        else:
            overall_status = IntegrityStatus.INVALID
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(results)
        repair_actions = self._generate_repair_actions(component_name, results)
        
        return ComponentIntegrityReport(
            component_name=component_name,
            overall_status=overall_status,
            checks_passed=passed,
            checks_failed=failed,
            checks_total=total,
            critical_failures=critical_failures,
            results=results,
            recommendations=recommendations,
            repair_actions=repair_actions
        )
    
    def _generate_recommendations(self, results: List[IntegrityResult]) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        for result in results:
            if result.status == IntegrityStatus.MISSING:
                recommendations.append(f"Reinstalar componente - arquivo ausente: {result.check_name}")
            elif result.status == IntegrityStatus.CORRUPTED:
                recommendations.append(f"Verificar integridade e reinstalar - arquivo corrompido: {result.check_name}")
            elif result.status == IntegrityStatus.INVALID:
                recommendations.append(f"Verificar configuração - validação falhou: {result.check_name}")
        
        return list(set(recommendations))  # Remover duplicatas
    
    def _generate_repair_actions(self, component_name: str, results: List[IntegrityResult]) -> List[str]:
        """Gera ações de reparo automático"""
        repair_actions = []
        
        has_missing = any(r.status == IntegrityStatus.MISSING for r in results)
        has_corrupted = any(r.status == IntegrityStatus.CORRUPTED for r in results)
        
        if has_missing or has_corrupted:
            repair_actions.append(f"reinstall:{component_name}")
        
        # Ações específicas por tipo de problema
        for result in results:
            if "registry" in result.check_name and result.status == IntegrityStatus.MISSING:
                repair_actions.append(f"repair_registry:{component_name}")
            elif "service" in result.check_name and result.status == IntegrityStatus.INVALID:
                repair_actions.append(f"restart_service:{result.check_name}")
        
        return repair_actions
    
    def load_checksum_cache(self):
        """Carrega cache de checksums"""
        cache_file = self.cache_dir / "checksums.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.checksum_cache = json.load(f)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar cache de checksums: {e}")
    
    def save_checksum_cache(self):
        """Salva cache de checksums"""
        cache_file = self.cache_dir / "checksums.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.checksum_cache, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Erro ao salvar cache de checksums: {e}")
    
    def _save_integrity_report(self, component_name: str, report: ComponentIntegrityReport):
        """Salva relatório de integridade"""
        report_file = self.cache_dir / f"{component_name}_integrity.json"
        try:
            # Converter para dict para serialização
            report_dict = {
                'component_name': report.component_name,
                'overall_status': report.overall_status.value,
                'checks_passed': report.checks_passed,
                'checks_failed': report.checks_failed,
                'checks_total': report.checks_total,
                'critical_failures': report.critical_failures,
                'timestamp': time.time(),
                'results': [
                    {
                        'check_name': r.check_name,
                        'status': r.status.value,
                        'expected': r.expected,
                        'actual': r.actual,
                        'error_message': r.error_message,
                        'execution_time': r.execution_time
                    } for r in report.results
                ],
                'recommendations': report.recommendations,
                'repair_actions': report.repair_actions
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_dict, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Erro ao salvar relatório de integridade: {e}")
    
    def get_component_integrity_history(self, component_name: str) -> List[Dict[str, Any]]:
        """Obtém histórico de integridade de um componente"""
        report_file = self.cache_dir / f"{component_name}_integrity.json"
        if report_file.exists():
            try:
                with open(report_file, 'r') as f:
                    return [json.load(f)]
            except Exception as e:
                self.logger.warning(f"Erro ao carregar histórico de integridade: {e}")
        return []
    
    def generate_integrity_summary(self, reports: List[ComponentIntegrityReport]) -> Dict[str, Any]:
        """Gera resumo de integridade do sistema"""
        total_components = len(reports)
        valid_components = sum(1 for r in reports if r.overall_status == IntegrityStatus.VALID)
        corrupted_components = sum(1 for r in reports if r.overall_status == IntegrityStatus.CORRUPTED)
        partial_components = sum(1 for r in reports if r.overall_status == IntegrityStatus.PARTIAL)
        
        return {
            'total_components': total_components,
            'valid_components': valid_components,
            'corrupted_components': corrupted_components,
            'partial_components': partial_components,
            'integrity_score': (valid_components / total_components * 100) if total_components > 0 else 0,
            'critical_issues': sum(r.critical_failures for r in reports),
            'total_checks': sum(r.checks_total for r in reports),
            'passed_checks': sum(r.checks_passed for r in reports),
            'failed_checks': sum(r.checks_failed for r in reports)
        }

# Instância global
_integrity_checker: Optional[PostInstallationIntegrityChecker] = None

def get_integrity_checker() -> PostInstallationIntegrityChecker:
    """Obtém instância global do verificador de integridade"""
    global _integrity_checker
    if _integrity_checker is None:
        _integrity_checker = PostInstallationIntegrityChecker()
    return _integrity_checker