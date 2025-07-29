# -*- coding: utf-8 -*-
"""
Security Manager para Environment Dev Script
Módulo responsável por validações de segurança, proteção contra ataques
e auditoria de operações críticas
"""

import os
import logging
import hashlib
import re
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Níveis de segurança"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    """Tipos de ameaças"""
    PATH_TRAVERSAL = "path_traversal"
    CODE_INJECTION = "code_injection"
    MALICIOUS_URL = "malicious_url"
    SUSPICIOUS_FILE = "suspicious_file"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    NETWORK_ATTACK = "network_attack"

class ValidationResult(Enum):
    """Resultado da validação"""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"

@dataclass
class SecurityThreat:
    """Representa uma ameaça de segurança detectada"""
    id: str
    threat_type: ThreatType
    severity: SecurityLevel
    description: str
    source: str
    detected_at: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    mitigation_applied: bool = False
    false_positive: bool = False

@dataclass
class ValidationReport:
    """Relatório de validação de segurança"""
    input_data: str
    validation_result: ValidationResult
    threats_detected: List[SecurityThreat] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    safe_alternative: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AuditEntry:
    """Entrada de auditoria"""
    id: str
    timestamp: datetime
    operation: str
    user: str
    component: str
    details: Dict[str, Any]
    security_level: SecurityLevel
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecurityManager:
    """
    Gerenciador de segurança completo para validação rigorosa de inputs,
    proteção contra ataques e auditoria de operações críticas.
    
    Implementa os requisitos:
    - 2.1: Validação rigorosa de todos os inputs
    - 2.4: Proteção contra path traversal e injection
    - Auditoria para operações críticas
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.security_config = self._load_security_config()
        self.audit_log: List[AuditEntry] = []
        self.threat_database: List[SecurityThreat] = []
        self.blocked_patterns = self._load_blocked_patterns()
        self.trusted_domains = self._load_trusted_domains()
        self.audit_file = self.base_path / "logs" / "security_audit.json"
        
        # Cria diretório de logs se não existir
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Carrega auditoria existente
        self._load_audit_log()
        
        logger.info("Security Manager inicializado")
    
    def validate_input(self, input_data: str, input_type: str = "general", 
                      context: Optional[Dict] = None) -> ValidationReport:
        """
        Validação rigorosa de todos os inputs (Requisito 2.1)
        
        Args:
            input_data: Dados de entrada para validar
            input_type: Tipo do input (path, url, command, etc.)
            context: Contexto adicional para validação
            
        Returns:
            ValidationReport: Relatório detalhado da validação
        """
        logger.debug(f"Validando input tipo '{input_type}': {input_data[:100]}...")
        
        report = ValidationReport(
            input_data=input_data,
            validation_result=ValidationResult.SAFE
        )
        
        try:
            # Validações específicas por tipo
            if input_type == "path":
                self._validate_path_input(input_data, report)
            elif input_type == "url":
                self._validate_url_input(input_data, report)
            elif input_type == "command":
                self._validate_command_input(input_data, report)
            elif input_type == "filename":
                self._validate_filename_input(input_data, report)
            elif input_type == "json":
                self._validate_json_input(input_data, report)
            else:
                self._validate_general_input(input_data, report)
            
            # Validações gerais aplicadas a todos os tipos
            self._check_malicious_patterns(input_data, report)
            self._check_encoding_attacks(input_data, report)
            self._check_length_limits(input_data, report, input_type)
            
            # Determina resultado final
            if report.threats_detected:
                critical_threats = [t for t in report.threats_detected if t.severity == SecurityLevel.CRITICAL]
                high_threats = [t for t in report.threats_detected if t.severity == SecurityLevel.HIGH]
                
                if critical_threats:
                    report.validation_result = ValidationResult.BLOCKED
                elif high_threats:
                    report.validation_result = ValidationResult.DANGEROUS
                else:
                    report.validation_result = ValidationResult.SUSPICIOUS
            
            # Gera recomendações
            self._generate_security_recommendations(report)
            
            # Registra auditoria para inputs suspeitos ou perigosos
            if report.validation_result in [ValidationResult.SUSPICIOUS, ValidationResult.DANGEROUS, ValidationResult.BLOCKED]:
                self._audit_security_event(
                    operation="input_validation",
                    details={
                        "input_type": input_type,
                        "validation_result": report.validation_result.value,
                        "threats_count": len(report.threats_detected),
                        "input_preview": input_data[:100]
                    },
                    security_level=SecurityLevel.HIGH if report.validation_result == ValidationResult.BLOCKED else SecurityLevel.MEDIUM
                )
            
            logger.debug(f"Validação concluída: {report.validation_result.value}")
            return report
            
        except Exception as e:
            logger.error(f"Erro na validação de input: {e}")
            
            # Em caso de erro, assume o pior cenário
            report.validation_result = ValidationResult.BLOCKED
            report.threats_detected.append(SecurityThreat(
                id=f"validation_error_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.CRITICAL,
                description=f"Erro na validação: {e}",
                source="security_manager",
                detected_at=datetime.now()
            ))
            
            return report
    
    def protect_against_path_traversal(self, file_path: str, 
                                     allowed_base_paths: Optional[List[str]] = None) -> ValidationReport:
        """
        Proteção contra ataques de path traversal (Requisito 2.4)
        
        Args:
            file_path: Caminho do arquivo a ser validado
            allowed_base_paths: Lista de caminhos base permitidos
            
        Returns:
            ValidationReport: Resultado da validação
        """
        logger.debug(f"Verificando path traversal: {file_path}")
        
        report = ValidationReport(
            input_data=file_path,
            validation_result=ValidationResult.SAFE
        )
        
        try:
            # Normaliza o caminho
            normalized_path = os.path.normpath(file_path)
            resolved_path = os.path.abspath(normalized_path)
            
            # Verifica padrões suspeitos
            suspicious_patterns = [
                r'\.\.[\\/]',  # ../ ou ..\
                r'[\\/]\.\.[\\/]',  # /../ ou \..\
                r'^\.\.[\\/]',  # Inicia com ../
                r'[\\/]\.\.?$',  # Termina com /.. ou /.
                r'%2e%2e',  # URL encoded ..
                r'%252e%252e',  # Double URL encoded ..
                r'\.\.%2f',  # Mixed encoding
                r'%c0%ae',  # UTF-8 overlong encoding
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, file_path, re.IGNORECASE):
                    threat = SecurityThreat(
                        id=f"path_traversal_{int(time.time())}",
                        threat_type=ThreatType.PATH_TRAVERSAL,
                        severity=SecurityLevel.HIGH,
                        description=f"Padrão de path traversal detectado: {pattern}",
                        source=file_path,
                        detected_at=datetime.now(),
                        details={"pattern": pattern, "normalized_path": normalized_path}
                    )
                    report.threats_detected.append(threat)
            
            # Verifica se o caminho resolvido está dentro dos caminhos permitidos
            if allowed_base_paths:
                is_allowed = False
                for base_path in allowed_base_paths:
                    abs_base_path = os.path.abspath(base_path)
                    if resolved_path.startswith(abs_base_path):
                        is_allowed = True
                        break
                
                if not is_allowed:
                    threat = SecurityThreat(
                        id=f"path_outside_allowed_{int(time.time())}",
                        threat_type=ThreatType.PATH_TRAVERSAL,
                        severity=SecurityLevel.CRITICAL,
                        description="Caminho fora dos diretórios permitidos",
                        source=file_path,
                        detected_at=datetime.now(),
                        details={
                            "resolved_path": resolved_path,
                            "allowed_paths": allowed_base_paths
                        }
                    )
                    report.threats_detected.append(threat)
            
            # Verifica caracteres perigosos
            dangerous_chars = ['<', '>', '|', '&', ';', '`', '$', '(', ')']
            found_dangerous = [char for char in dangerous_chars if char in file_path]
            
            if found_dangerous:
                threat = SecurityThreat(
                    id=f"dangerous_chars_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Caracteres perigosos encontrados: {found_dangerous}",
                    source=file_path,
                    detected_at=datetime.now(),
                    details={"dangerous_chars": found_dangerous}
                )
                report.threats_detected.append(threat)
            
            # Determina resultado
            if report.threats_detected:
                critical_threats = [t for t in report.threats_detected if t.severity == SecurityLevel.CRITICAL]
                if critical_threats:
                    report.validation_result = ValidationResult.BLOCKED
                else:
                    report.validation_result = ValidationResult.SUSPICIOUS
                
                # Sugere alternativa segura
                safe_path = self._sanitize_path(file_path)
                if safe_path != file_path:
                    report.safe_alternative = safe_path
            
            return report
            
        except Exception as e:
            logger.error(f"Erro na proteção contra path traversal: {e}")
            report.validation_result = ValidationResult.BLOCKED
            return report
    
    def protect_against_injection(self, input_data: str, 
                                injection_types: Optional[List[str]] = None) -> ValidationReport:
        """
        Proteção contra ataques de injeção (Requisito 2.4)
        
        Args:
            input_data: Dados a serem verificados
            injection_types: Tipos de injeção a verificar (sql, command, script, etc.)
            
        Returns:
            ValidationReport: Resultado da validação
        """
        logger.debug(f"Verificando injeção: {input_data[:50]}...")
        
        report = ValidationReport(
            input_data=input_data,
            validation_result=ValidationResult.SAFE
        )
        
        if not injection_types:
            injection_types = ['sql', 'command', 'script', 'ldap', 'xpath']
        
        try:
            for injection_type in injection_types:
                if injection_type == 'sql':
                    self._check_sql_injection(input_data, report)
                elif injection_type == 'command':
                    self._check_command_injection(input_data, report)
                elif injection_type == 'script':
                    self._check_script_injection(input_data, report)
                elif injection_type == 'ldap':
                    self._check_ldap_injection(input_data, report)
                elif injection_type == 'xpath':
                    self._check_xpath_injection(input_data, report)
            
            # Determina resultado final
            if report.threats_detected:
                critical_threats = [t for t in report.threats_detected if t.severity == SecurityLevel.CRITICAL]
                high_threats = [t for t in report.threats_detected if t.severity == SecurityLevel.HIGH]
                
                if critical_threats:
                    report.validation_result = ValidationResult.BLOCKED
                elif high_threats:
                    report.validation_result = ValidationResult.DANGEROUS
                else:
                    report.validation_result = ValidationResult.SUSPICIOUS
            
            return report
            
        except Exception as e:
            logger.error(f"Erro na proteção contra injeção: {e}")
            report.validation_result = ValidationResult.BLOCKED
            return report
    
    def audit_critical_operation(self, operation: str, component: str, 
                               details: Dict[str, Any], success: bool = True,
                               security_level: SecurityLevel = SecurityLevel.MEDIUM) -> str:
        """
        Auditoria para operações críticas (Requisito de auditoria)
        
        Args:
            operation: Nome da operação
            component: Componente que executou a operação
            details: Detalhes da operação
            success: Se a operação foi bem-sucedida
            security_level: Nível de segurança da operação
            
        Returns:
            str: ID da entrada de auditoria
        """
        audit_id = f"audit_{int(time.time())}_{hash(operation) % 10000}"
        
        audit_entry = AuditEntry(
            id=audit_id,
            timestamp=datetime.now(),
            operation=operation,
            user=self._get_current_user(),
            component=component,
            details=details,
            security_level=security_level,
            success=success,
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent()
        )
        
        self.audit_log.append(audit_entry)
        
        # Salva auditoria imediatamente para operações críticas
        if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            self._save_audit_log()
        
        logger.info(f"Operação auditada: {operation} ({audit_id})")
        return audit_id
    
    def get_security_report(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Gera relatório de segurança
        
        Args:
            days_back: Número de dias para incluir no relatório
            
        Returns:
            Dict: Relatório de segurança detalhado
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Filtra eventos recentes
        recent_threats = [t for t in self.threat_database if t.detected_at >= cutoff_date]
        recent_audits = [a for a in self.audit_log if a.timestamp >= cutoff_date]
        
        # Estatísticas de ameaças
        threat_stats = {}
        for threat_type in ThreatType:
            threat_stats[threat_type.value] = len([t for t in recent_threats if t.threat_type == threat_type])
        
        # Estatísticas de auditoria
        audit_stats = {
            'total_operations': len(recent_audits),
            'successful_operations': len([a for a in recent_audits if a.success]),
            'failed_operations': len([a for a in recent_audits if not a.success]),
            'critical_operations': len([a for a in recent_audits if a.security_level == SecurityLevel.CRITICAL]),
            'high_security_operations': len([a for a in recent_audits if a.security_level == SecurityLevel.HIGH])
        }
        
        # Top operações por componente
        component_operations = {}
        for audit in recent_audits:
            if audit.component not in component_operations:
                component_operations[audit.component] = 0
            component_operations[audit.component] += 1
        
        # Ameaças por severidade
        severity_stats = {}
        for severity in SecurityLevel:
            severity_stats[severity.value] = len([t for t in recent_threats if t.severity == severity])
        
        report = {
            'report_period': {
                'start_date': cutoff_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'days_included': days_back
            },
            'threat_summary': {
                'total_threats': len(recent_threats),
                'threats_by_type': threat_stats,
                'threats_by_severity': severity_stats,
                'mitigated_threats': len([t for t in recent_threats if t.mitigation_applied]),
                'false_positives': len([t for t in recent_threats if t.false_positive])
            },
            'audit_summary': audit_stats,
            'top_components': dict(sorted(component_operations.items(), key=lambda x: x[1], reverse=True)[:10]),
            'security_recommendations': self._generate_security_recommendations_report(recent_threats, recent_audits),
            'generated_at': datetime.now().isoformat()
        }
        
        return report    

    # Métodos privados de validação específica
    def _validate_path_input(self, path: str, report: ValidationReport):
        """Valida input de caminho de arquivo"""
        # Verifica comprimento excessivo
        if len(path) > 260:  # Limite do Windows
            threat = SecurityThreat(
                id=f"path_too_long_{int(time.time())}",
                threat_type=ThreatType.PATH_TRAVERSAL,
                severity=SecurityLevel.MEDIUM,
                description="Caminho muito longo",
                source=path,
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
        
        # Verifica caracteres inválidos
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        found_invalid = [char for char in invalid_chars if char in path]
        
        if found_invalid:
            threat = SecurityThreat(
                id=f"invalid_path_chars_{int(time.time())}",
                threat_type=ThreatType.PATH_TRAVERSAL,
                severity=SecurityLevel.MEDIUM,
                description=f"Caracteres inválidos no caminho: {found_invalid}",
                source=path,
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _validate_url_input(self, url: str, report: ValidationReport):
        """Valida input de URL"""
        try:
            parsed = urlparse(url)
            
            # Verifica esquema
            if parsed.scheme not in ['http', 'https', 'ftp', 'ftps']:
                threat = SecurityThreat(
                    id=f"invalid_url_scheme_{int(time.time())}",
                    threat_type=ThreatType.MALICIOUS_URL,
                    severity=SecurityLevel.HIGH,
                    description=f"Esquema de URL não permitido: {parsed.scheme}",
                    source=url,
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
            
            # Verifica domínio suspeito
            if parsed.hostname:
                if self._is_suspicious_domain(parsed.hostname):
                    threat = SecurityThreat(
                        id=f"suspicious_domain_{int(time.time())}",
                        threat_type=ThreatType.MALICIOUS_URL,
                        severity=SecurityLevel.HIGH,
                        description=f"Domínio suspeito: {parsed.hostname}",
                        source=url,
                        detected_at=datetime.now()
                    )
                    report.threats_detected.append(threat)
                
                # Verifica IP privado ou localhost
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                    if ip.is_private or ip.is_loopback:
                        threat = SecurityThreat(
                            id=f"private_ip_url_{int(time.time())}",
                            threat_type=ThreatType.NETWORK_ATTACK,
                            severity=SecurityLevel.MEDIUM,
                            description=f"URL aponta para IP privado/localhost: {parsed.hostname}",
                            source=url,
                            detected_at=datetime.now()
                        )
                        report.threats_detected.append(threat)
                except ValueError:
                    pass  # Não é um IP, continua
            
        except Exception as e:
            threat = SecurityThreat(
                id=f"malformed_url_{int(time.time())}",
                threat_type=ThreatType.MALICIOUS_URL,
                severity=SecurityLevel.MEDIUM,
                description=f"URL malformada: {e}",
                source=url,
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _validate_command_input(self, command: str, report: ValidationReport):
        """Valida input de comando"""
        # Comandos perigosos
        dangerous_commands = [
            'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd',
            'shutdown', 'reboot', 'halt', 'poweroff',
            'su', 'sudo', 'runas', 'net user', 'net localgroup',
            'reg add', 'reg delete', 'regedit',
            'powershell', 'cmd', 'bash', 'sh',
            'wget', 'curl', 'nc', 'netcat', 'telnet'
        ]
        
        command_lower = command.lower()
        for dangerous_cmd in dangerous_commands:
            if dangerous_cmd in command_lower:
                threat = SecurityThreat(
                    id=f"dangerous_command_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description=f"Comando perigoso detectado: {dangerous_cmd}",
                    source=command,
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
        
        # Verifica redirecionamentos e pipes suspeitos
        suspicious_operators = ['>', '>>', '<', '|', '&', '&&', '||', ';', '`', '$']
        found_operators = [op for op in suspicious_operators if op in command]
        
        if found_operators:
            threat = SecurityThreat(
                id=f"suspicious_operators_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.MEDIUM,
                description=f"Operadores suspeitos: {found_operators}",
                source=command,
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _validate_filename_input(self, filename: str, report: ValidationReport):
        """Valida nome de arquivo"""
        # Nomes reservados no Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        filename_upper = filename.upper()
        for reserved in reserved_names:
            if filename_upper == reserved or filename_upper.startswith(reserved + '.'):
                threat = SecurityThreat(
                    id=f"reserved_filename_{int(time.time())}",
                    threat_type=ThreatType.SUSPICIOUS_FILE,
                    severity=SecurityLevel.MEDIUM,
                    description=f"Nome de arquivo reservado: {reserved}",
                    source=filename,
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
        
        # Extensões perigosas
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.ps1', '.msi', '.reg', '.inf', '.sys', '.dll'
        ]
        
        file_ext = Path(filename).suffix.lower()
        if file_ext in dangerous_extensions:
            threat = SecurityThreat(
                id=f"dangerous_extension_{int(time.time())}",
                threat_type=ThreatType.SUSPICIOUS_FILE,
                severity=SecurityLevel.HIGH,
                description=f"Extensão perigosa: {file_ext}",
                source=filename,
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _validate_json_input(self, json_data: str, report: ValidationReport):
        """Valida input JSON"""
        try:
            parsed_json = json.loads(json_data)
            
            # Verifica profundidade excessiva (ataque de DoS)
            max_depth = 10
            if self._get_json_depth(parsed_json) > max_depth:
                threat = SecurityThreat(
                    id=f"json_too_deep_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description=f"JSON muito profundo (>{max_depth} níveis)",
                    source=json_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
            
            # Verifica tamanho excessivo
            if len(json_data) > 1024 * 1024:  # 1MB
                threat = SecurityThreat(
                    id=f"json_too_large_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description="JSON muito grande (>1MB)",
                    source=json_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                
        except json.JSONDecodeError as e:
            threat = SecurityThreat(
                id=f"invalid_json_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.LOW,
                description=f"JSON inválido: {e}",
                source=json_data[:100],
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _validate_general_input(self, input_data: str, report: ValidationReport):
        """Validação geral para qualquer input"""
        # Verifica caracteres de controle
        control_chars = [char for char in input_data if ord(char) < 32 and char not in ['\t', '\n', '\r']]
        if control_chars:
            threat = SecurityThreat(
                id=f"control_chars_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.LOW,
                description=f"Caracteres de controle encontrados: {len(control_chars)}",
                source=input_data[:100],
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _check_malicious_patterns(self, input_data: str, report: ValidationReport):
        """Verifica padrões maliciosos conhecidos"""
        for pattern_name, pattern_regex in self.blocked_patterns.items():
            if re.search(pattern_regex, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    id=f"malicious_pattern_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description=f"Padrão malicioso detectado: {pattern_name}",
                    source=input_data[:100],
                    detected_at=datetime.now(),
                    details={"pattern": pattern_name}
                )
                report.threats_detected.append(threat)
    
    def _check_encoding_attacks(self, input_data: str, report: ValidationReport):
        """Verifica ataques de codificação"""
        # URL encoding duplo
        if '%25' in input_data:
            threat = SecurityThreat(
                id=f"double_encoding_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.MEDIUM,
                description="Possível double URL encoding detectado",
                source=input_data[:100],
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
        
        # Unicode overlong encoding
        overlong_patterns = [r'%c0%ae', r'%e0%80%ae', r'%c1%9c']
        for pattern in overlong_patterns:
            if pattern in input_data.lower():
                threat = SecurityThreat(
                    id=f"overlong_encoding_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description="Unicode overlong encoding detectado",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
    
    def _check_length_limits(self, input_data: str, report: ValidationReport, input_type: str):
        """Verifica limites de comprimento"""
        limits = {
            'path': 260,
            'url': 2048,
            'command': 8192,
            'filename': 255,
            'general': 65536
        }
        
        max_length = limits.get(input_type, limits['general'])
        
        if len(input_data) > max_length:
            threat = SecurityThreat(
                id=f"length_exceeded_{int(time.time())}",
                threat_type=ThreatType.CODE_INJECTION,
                severity=SecurityLevel.MEDIUM,
                description=f"Comprimento excede limite ({len(input_data)} > {max_length})",
                source=input_data[:100],
                detected_at=datetime.now()
            )
            report.threats_detected.append(threat)
    
    def _check_sql_injection(self, input_data: str, report: ValidationReport):
        """Verifica injeção SQL"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    id=f"sql_injection_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description="Possível injeção SQL detectada",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                break
    
    def _check_command_injection(self, input_data: str, report: ValidationReport):
        """Verifica injeção de comando"""
        command_patterns = [
            r"[;&|`$(){}[\]<>]",
            r"\b(eval|exec|system|shell_exec|passthru)\b",
            r"(\$\(|\`)",
            r"(&&|\|\|)"
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    id=f"command_injection_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description="Possível injeção de comando detectada",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                break
    
    def _check_script_injection(self, input_data: str, report: ValidationReport):
        """Verifica injeção de script"""
        script_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"document\.(write|cookie)",
            r"window\.(location|open)"
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    id=f"script_injection_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.HIGH,
                    description="Possível injeção de script detectada",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                break
    
    def _check_ldap_injection(self, input_data: str, report: ValidationReport):
        """Verifica injeção LDAP"""
        ldap_patterns = [
            r"[()&|!*]",
            r"\\[0-9a-fA-F]{2}",
            r"\*\)",
            r"\(\|"
        ]
        
        for pattern in ldap_patterns:
            if re.search(pattern, input_data):
                threat = SecurityThreat(
                    id=f"ldap_injection_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description="Possível injeção LDAP detectada",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                break
    
    def _check_xpath_injection(self, input_data: str, report: ValidationReport):
        """Verifica injeção XPath"""
        xpath_patterns = [
            r"(\b(and|or)\b\s+\d+\s*=\s*\d+)",
            r"(\b(and|or)\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(//|\[|\]|@|\*)",
            r"(\btext\(\)|\bnode\(\))"
        ]
        
        for pattern in xpath_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threat = SecurityThreat(
                    id=f"xpath_injection_{int(time.time())}",
                    threat_type=ThreatType.CODE_INJECTION,
                    severity=SecurityLevel.MEDIUM,
                    description="Possível injeção XPath detectada",
                    source=input_data[:100],
                    detected_at=datetime.now()
                )
                report.threats_detected.append(threat)
                break
    
    def _generate_security_recommendations(self, report: ValidationReport):
        """Gera recomendações de segurança"""
        if not report.threats_detected:
            return
        
        threat_types = set(t.threat_type for t in report.threats_detected)
        
        if ThreatType.PATH_TRAVERSAL in threat_types:
            report.recommendations.append("Use caminhos absolutos e valide contra diretórios permitidos")
            report.recommendations.append("Implemente whitelist de diretórios acessíveis")
        
        if ThreatType.CODE_INJECTION in threat_types:
            report.recommendations.append("Sanitize todos os inputs antes do processamento")
            report.recommendations.append("Use prepared statements para consultas")
            report.recommendations.append("Implemente validação rigorosa de tipos de dados")
        
        if ThreatType.MALICIOUS_URL in threat_types:
            report.recommendations.append("Valide URLs contra whitelist de domínios confiáveis")
            report.recommendations.append("Implemente verificação de certificados SSL")
        
        if ThreatType.SUSPICIOUS_FILE in threat_types:
            report.recommendations.append("Escaneie arquivos com antivírus antes do processamento")
            report.recommendations.append("Restrinja tipos de arquivo permitidos")
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitiza um caminho removendo elementos perigosos"""
        # Remove sequências de path traversal
        sanitized = re.sub(r'\.\.[\\/]', '', path)
        sanitized = re.sub(r'[\\/]\.\.[\\/]', '/', sanitized)
        sanitized = re.sub(r'^\.\.[\\/]', '', sanitized)
        
        # Remove caracteres perigosos
        dangerous_chars = ['<', '>', '|', '&', ';', '`', '$', '(', ')']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        return sanitized
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """Verifica se um domínio é suspeito"""
        # Lista de domínios conhecidamente maliciosos (exemplo)
        malicious_domains = [
            'malware.com', 'phishing.net', 'suspicious.org'
        ]
        
        # Verifica contra lista de domínios maliciosos
        if domain.lower() in malicious_domains:
            return True
        
        # Verifica padrões suspeitos
        suspicious_patterns = [
            r'\d+\.\d+\.\d+\.\d+',  # IP direto
            r'[a-z0-9]{20,}',  # String muito longa
            r'.*\.tk$|.*\.ml$|.*\.ga$',  # TLDs suspeitos
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, domain.lower()):
                return True
        
        return False
    
    def _get_json_depth(self, obj, depth=0):
        """Calcula profundidade de um objeto JSON"""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()] + [depth])
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj] + [depth])
        else:
            return depth
    
    def _audit_security_event(self, operation: str, details: Dict[str, Any], 
                            security_level: SecurityLevel):
        """Registra evento de segurança na auditoria"""
        self.audit_critical_operation(
            operation=f"security_{operation}",
            component="security_manager",
            details=details,
            success=True,
            security_level=security_level
        )
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Carrega configuração de segurança"""
        config_file = self.base_path / "config" / "security.json"
        
        default_config = {
            "max_input_length": 65536,
            "allowed_file_extensions": [".txt", ".json", ".yaml", ".yml"],
            "blocked_file_extensions": [".exe", ".bat", ".cmd", ".ps1"],
            "trusted_domains": ["github.com", "microsoft.com", "python.org"],
            "audit_retention_days": 90,
            "threat_detection_enabled": True
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Erro ao carregar configuração de segurança: {e}")
        
        return default_config
    
    def _load_blocked_patterns(self) -> Dict[str, str]:
        """Carrega padrões bloqueados"""
        return {
            "sql_injection": r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            "command_injection": r"[;&|`$(){}[\]<>]",
            "script_injection": r"<script[^>]*>|javascript:|vbscript:",
            "path_traversal": r"\.\.[\\/]",
            "null_byte": r"\x00",
            "format_string": r"%[sdxp]",
            "buffer_overflow": r"A{100,}",  # Muitos A's consecutivos
        }
    
    def _load_trusted_domains(self) -> Set[str]:
        """Carrega lista de domínios confiáveis"""
        return set(self.security_config.get("trusted_domains", []))
    
    def _load_audit_log(self):
        """Carrega log de auditoria existente"""
        try:
            if self.audit_file.exists():
                with open(self.audit_file, 'r', encoding='utf-8') as f:
                    audit_data = json.load(f)
                    
                    for entry_data in audit_data:
                        audit_entry = AuditEntry(
                            id=entry_data['id'],
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            operation=entry_data['operation'],
                            user=entry_data['user'],
                            component=entry_data['component'],
                            details=entry_data['details'],
                            security_level=SecurityLevel(entry_data['security_level']),
                            success=entry_data['success'],
                            ip_address=entry_data.get('ip_address'),
                            user_agent=entry_data.get('user_agent')
                        )
                        self.audit_log.append(audit_entry)
                        
        except Exception as e:
            logger.warning(f"Erro ao carregar log de auditoria: {e}")
    
    def _save_audit_log(self):
        """Salva log de auditoria"""
        try:
            audit_data = []
            for entry in self.audit_log:
                audit_data.append({
                    'id': entry.id,
                    'timestamp': entry.timestamp.isoformat(),
                    'operation': entry.operation,
                    'user': entry.user,
                    'component': entry.component,
                    'details': entry.details,
                    'security_level': entry.security_level.value,
                    'success': entry.success,
                    'ip_address': entry.ip_address,
                    'user_agent': entry.user_agent
                })
            
            with open(self.audit_file, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar log de auditoria: {e}")
    
    def _get_current_user(self) -> str:
        """Obtém usuário atual"""
        try:
            import getpass
            return getpass.getuser()
        except:
            return "unknown"
    
    def _get_client_ip(self) -> Optional[str]:
        """Obtém IP do cliente (placeholder)"""
        # Em uma aplicação web, isso viria do request
        return None
    
    def _get_user_agent(self) -> Optional[str]:
        """Obtém user agent (placeholder)"""
        # Em uma aplicação web, isso viria do request
        return None
    
    def _generate_security_recommendations_report(self, threats: List[SecurityThreat], 
                                                audits: List[AuditEntry]) -> List[str]:
        """Gera recomendações para o relatório de segurança"""
        recommendations = []
        
        # Análise de ameaças
        if threats:
            threat_types = set(t.threat_type for t in threats)
            
            if ThreatType.PATH_TRAVERSAL in threat_types:
                recommendations.append("Implementar validação rigorosa de caminhos de arquivo")
            
            if ThreatType.CODE_INJECTION in threat_types:
                recommendations.append("Revisar e fortalecer validação de inputs")
            
            if ThreatType.MALICIOUS_URL in threat_types:
                recommendations.append("Implementar whitelist de domínios confiáveis")
        
        # Análise de auditoria
        failed_operations = [a for a in audits if not a.success]
        if len(failed_operations) > len(audits) * 0.1:  # Mais de 10% de falhas
            recommendations.append("Investigar alta taxa de falhas em operações")
        
        critical_operations = [a for a in audits if a.security_level == SecurityLevel.CRITICAL]
        if critical_operations:
            recommendations.append("Revisar operações críticas para possível otimização")
        
        if not recommendations:
            recommendations.append("Sistema apresenta boa postura de segurança")
        
        return recommendations


# Instância global do gerenciador de segurança
security_manager = SecurityManager()