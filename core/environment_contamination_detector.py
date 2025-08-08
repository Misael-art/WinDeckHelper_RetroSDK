#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Contamination Detector - Sistema de Detecção de Ambiente Contaminado
Detecta problemas no ambiente de desenvolvimento que podem afetar instalações e funcionamento.
"""

import logging
import os
import sys
import json
import subprocess
import time
import winreg
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import psutil
import threading
from collections import defaultdict, Counter

class ContaminationType(Enum):
    """Tipos de contaminação"""
    MALICIOUS_PROCESS = "malicious_process"
    SUSPICIOUS_NETWORK = "suspicious_network"
    CORRUPTED_PATH = "corrupted_path"
    REGISTRY_POLLUTION = "registry_pollution"
    TEMP_POLLUTION = "temp_pollution"
    ENVIRONMENT_POLLUTION = "environment_pollution"
    PERMISSION_ISSUES = "permission_issues"
    DISK_CORRUPTION = "disk_corruption"
    MEMORY_ISSUES = "memory_issues"
    CONFLICTING_SOFTWARE = "conflicting_software"
    OUTDATED_DEPENDENCIES = "outdated_dependencies"
    BROKEN_SYMLINKS = "broken_symlinks"

class SeverityLevel(Enum):
    """Níveis de severidade"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DetectionMethod(Enum):
    """Métodos de detecção"""
    PROCESS_ANALYSIS = "process_analysis"
    NETWORK_MONITORING = "network_monitoring"
    FILE_SYSTEM_SCAN = "file_system_scan"
    REGISTRY_ANALYSIS = "registry_analysis"
    PERFORMANCE_MONITORING = "performance_monitoring"
    HEURISTIC_ANALYSIS = "heuristic_analysis"
    SIGNATURE_MATCHING = "signature_matching"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"

@dataclass
class ContaminationSignature:
    """Assinatura de contaminação"""
    name: str
    type: ContaminationType
    patterns: List[str] = field(default_factory=list)
    indicators: Dict[str, Any] = field(default_factory=dict)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    description: str = ""
    remediation: List[str] = field(default_factory=list)

@dataclass
class ContaminationDetection:
    """Detecção de contaminação"""
    detection_id: str
    type: ContaminationType
    severity: SeverityLevel
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    affected_components: List[str] = field(default_factory=list)
    detection_method: DetectionMethod = DetectionMethod.HEURISTIC_ANALYSIS
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.8
    remediation_steps: List[str] = field(default_factory=list)

@dataclass
class SystemSnapshot:
    """Snapshot do sistema"""
    timestamp: float
    processes: List[Dict[str, Any]] = field(default_factory=list)
    network_connections: List[Dict[str, Any]] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    registry_keys: Dict[str, Any] = field(default_factory=dict)
    file_system_state: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

class EnvironmentContaminationDetector:
    """Detector de contaminação do ambiente"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger("contamination_detector")
        self.config_dir = config_dir or Path.cwd() / "config"
        
        # Assinaturas de contaminação
        self.contamination_signatures: List[ContaminationSignature] = []
        self.load_contamination_signatures()
        
        # Baseline do sistema
        self.system_baseline: Optional[SystemSnapshot] = None
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Cache de detecções
        self.detection_cache: Dict[str, ContaminationDetection] = {}
        self.whitelist: Set[str] = set()
        
        # Métricas de performance
        self.performance_history: List[Dict[str, float]] = []
        self.max_history_size = 100
        
        # Carregar configurações
        self.load_configuration()
    
    def load_contamination_signatures(self):
        """Carrega assinaturas de contaminação"""
        # Assinaturas de processos maliciosos
        self.contamination_signatures.extend([
            ContaminationSignature(
                name="suspicious_miner",
                type=ContaminationType.MALICIOUS_PROCESS,
                patterns=["*miner*", "*crypto*", "*coin*"],
                indicators={"cpu_usage": ">80", "network_activity": "high"},
                severity=SeverityLevel.HIGH,
                description="Possível minerador de criptomoedas",
                remediation=["Terminar processo", "Verificar origem", "Executar antivírus"]
            ),
            ContaminationSignature(
                name="development_interference",
                type=ContaminationType.CONFLICTING_SOFTWARE,
                patterns=["*antivirus*", "*security*", "*protection*"],
                indicators={"file_access_blocks": ">5", "process_terminations": ">3"},
                severity=SeverityLevel.MEDIUM,
                description="Software de segurança interferindo no desenvolvimento",
                remediation=["Configurar exceções", "Ajustar políticas de segurança"]
            ),
            ContaminationSignature(
                name="registry_pollution",
                type=ContaminationType.REGISTRY_POLLUTION,
                patterns=["HKEY_LOCAL_MACHINE\\SOFTWARE\\*"],
                indicators={"orphaned_keys": ">50", "invalid_references": ">10"},
                severity=SeverityLevel.MEDIUM,
                description="Poluição do registro do Windows",
                remediation=["Limpeza do registro", "Verificar integridade"]
            ),
            ContaminationSignature(
                name="path_pollution",
                type=ContaminationType.CORRUPTED_PATH,
                patterns=["*;*;*;*;*"],  # PATH muito longo
                indicators={"path_length": ">2048", "duplicate_entries": ">5"},
                severity=SeverityLevel.MEDIUM,
                description="Variável PATH contaminada",
                remediation=["Limpar PATH", "Remover duplicatas", "Reorganizar prioridades"]
            ),
            ContaminationSignature(
                name="temp_pollution",
                type=ContaminationType.TEMP_POLLUTION,
                patterns=["*.tmp", "*.temp", "*~*"],
                indicators={"temp_files_count": ">1000", "temp_size_mb": ">500"},
                severity=SeverityLevel.LOW,
                description="Acúmulo excessivo de arquivos temporários",
                remediation=["Limpeza de arquivos temporários", "Configurar limpeza automática"]
            )
        ])
    
    def load_configuration(self):
        """Carrega configurações"""
        config_file = self.config_dir / "contamination_detection.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Carregar whitelist
                self.whitelist.update(config.get('whitelist', []))
                
                # Carregar assinaturas customizadas
                for sig_data in config.get('custom_signatures', []):
                    signature = ContaminationSignature(
                        name=sig_data['name'],
                        type=ContaminationType(sig_data['type']),
                        patterns=sig_data.get('patterns', []),
                        indicators=sig_data.get('indicators', {}),
                        severity=SeverityLevel(sig_data.get('severity', 'medium')),
                        description=sig_data.get('description', ''),
                        remediation=sig_data.get('remediation', [])
                    )
                    self.contamination_signatures.append(signature)
                
                self.logger.info(f"Configuração carregada: {len(self.whitelist)} itens na whitelist")
                
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configuração: {e}")
    
    def create_system_baseline(self) -> SystemSnapshot:
        """Cria baseline do sistema"""
        self.logger.info("Criando baseline do sistema...")
        
        snapshot = SystemSnapshot(
            timestamp=time.time(),
            processes=self._capture_processes(),
            network_connections=self._capture_network_connections(),
            environment_variables=dict(os.environ),
            registry_keys=self._capture_registry_keys(),
            file_system_state=self._capture_file_system_state(),
            performance_metrics=self._capture_performance_metrics()
        )
        
        self.system_baseline = snapshot
        self.logger.info("Baseline do sistema criado")
        
        return snapshot
    
    def _capture_processes(self) -> List[Dict[str, Any]]:
        """Captura informações de processos"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    proc_info['create_time'] = proc.create_time()
                    proc_info['status'] = proc.status()
                    
                    # Calcular hash do executável
                    if proc_info['exe']:
                        proc_info['exe_hash'] = self._calculate_file_hash(proc_info['exe'])
                    
                    processes.append(proc_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        
        except Exception as e:
            self.logger.warning(f"Erro ao capturar processos: {e}")
        
        return processes
    
    def _capture_network_connections(self) -> List[Dict[str, Any]]:
        """Captura conexões de rede"""
        connections = []
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                conn_info = {
                    'fd': conn.fd,
                    'family': conn.family.name if conn.family else None,
                    'type': conn.type.name if conn.type else None,
                    'laddr': conn.laddr._asdict() if conn.laddr else None,
                    'raddr': conn.raddr._asdict() if conn.raddr else None,
                    'status': conn.status,
                    'pid': conn.pid
                }
                connections.append(conn_info)
        
        except Exception as e:
            self.logger.warning(f"Erro ao capturar conexões de rede: {e}")
        
        return connections
    
    def _capture_registry_keys(self) -> Dict[str, Any]:
        """Captura chaves importantes do registro"""
        registry_data = {}
        
        important_keys = [
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services"
        ]
        
        for key_path in important_keys:
            try:
                registry_data[key_path] = self._read_registry_key(key_path)
            except Exception as e:
                self.logger.warning(f"Erro ao ler chave {key_path}: {e}")
        
        return registry_data
    
    def _read_registry_key(self, key_path: str) -> Dict[str, Any]:
        """Lê chave do registro"""
        parts = key_path.split('\\')
        root_key = parts[0]
        subkey = '\\'.join(parts[1:])
        
        root_map = {
            'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
            'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
            'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT
        }
        
        if root_key not in root_map:
            return {}
        
        try:
            with winreg.OpenKey(root_map[root_key], subkey) as key:
                values = {}
                i = 0
                while True:
                    try:
                        name, value, type_id = winreg.EnumValue(key, i)
                        values[name] = {'value': value, 'type': type_id}
                        i += 1
                    except WindowsError:
                        break
                
                return values
        
        except Exception:
            return {}
    
    def _capture_file_system_state(self) -> Dict[str, Any]:
        """Captura estado do sistema de arquivos"""
        fs_state = {}
        
        # Verificar diretórios importantes
        important_dirs = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            os.environ.get('APPDATA', ''),
            os.environ.get('LOCALAPPDATA', ''),
            'C:\\Windows\\System32',
            'C:\\Program Files',
            'C:\\Program Files (x86)'
        ]
        
        for dir_path in important_dirs:
            if dir_path and os.path.exists(dir_path):
                try:
                    fs_state[dir_path] = {
                        'file_count': self._count_files(dir_path),
                        'total_size': self._get_directory_size(dir_path),
                        'last_modified': os.path.getmtime(dir_path)
                    }
                except Exception as e:
                    self.logger.warning(f"Erro ao analisar diretório {dir_path}: {e}")
        
        return fs_state
    
    def _capture_performance_metrics(self) -> Dict[str, float]:
        """Captura métricas de performance"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                'network_bytes_sent': psutil.net_io_counters().bytes_sent,
                'network_bytes_recv': psutil.net_io_counters().bytes_recv,
                'boot_time': psutil.boot_time(),
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            self.logger.warning(f"Erro ao capturar métricas: {e}")
            return {}
    
    def detect_contamination(self, create_baseline: bool = False) -> List[ContaminationDetection]:
        """Detecta contaminação no ambiente"""
        if create_baseline or self.system_baseline is None:
            self.create_system_baseline()
        
        detections = []
        
        # Capturar estado atual
        current_snapshot = SystemSnapshot(
            timestamp=time.time(),
            processes=self._capture_processes(),
            network_connections=self._capture_network_connections(),
            environment_variables=dict(os.environ),
            registry_keys=self._capture_registry_keys(),
            file_system_state=self._capture_file_system_state(),
            performance_metrics=self._capture_performance_metrics()
        )
        
        # Análise de processos
        process_detections = self._analyze_processes(current_snapshot.processes)
        detections.extend(process_detections)
        
        # Análise de rede
        network_detections = self._analyze_network(current_snapshot.network_connections)
        detections.extend(network_detections)
        
        # Análise de variáveis de ambiente
        env_detections = self._analyze_environment_variables(current_snapshot.environment_variables)
        detections.extend(env_detections)
        
        # Análise do registro
        registry_detections = self._analyze_registry(current_snapshot.registry_keys)
        detections.extend(registry_detections)
        
        # Análise do sistema de arquivos
        fs_detections = self._analyze_file_system(current_snapshot.file_system_state)
        detections.extend(fs_detections)
        
        # Análise de performance
        perf_detections = self._analyze_performance(current_snapshot.performance_metrics)
        detections.extend(perf_detections)
        
        # Análise comparativa com baseline
        if self.system_baseline:
            baseline_detections = self._compare_with_baseline(current_snapshot, self.system_baseline)
            detections.extend(baseline_detections)
        
        # Filtrar duplicatas e aplicar whitelist
        detections = self._filter_detections(detections)
        
        # Salvar no cache
        for detection in detections:
            self.detection_cache[detection.detection_id] = detection
        
        self.logger.info(f"Detectadas {len(detections)} possíveis contaminações")
        
        return detections
    
    def _analyze_processes(self, processes: List[Dict[str, Any]]) -> List[ContaminationDetection]:
        """Analisa processos em busca de contaminação"""
        detections = []
        
        for proc in processes:
            proc_name = proc.get('name', '').lower()
            proc_exe = (proc.get('exe') or '').lower()
            
            # Verificar contra assinaturas
            for signature in self.contamination_signatures:
                if signature.type == ContaminationType.MALICIOUS_PROCESS:
                    for pattern in signature.patterns:
                        if self._match_pattern(pattern.lower(), proc_name) or self._match_pattern(pattern.lower(), proc_exe):
                            # Verificar indicadores adicionais
                            if self._check_process_indicators(proc, signature.indicators):
                                detection = ContaminationDetection(
                                    detection_id=f"proc_{proc.get('pid', 0)}_{signature.name}",
                                    type=signature.type,
                                    severity=signature.severity,
                                    description=f"Processo suspeito detectado: {proc_name} - {signature.description}",
                                    evidence={
                                        'process_name': proc_name,
                                        'process_exe': proc_exe,
                                        'pid': proc.get('pid'),
                                        'cpu_percent': proc.get('cpu_percent'),
                                        'memory_percent': proc.get('memory_percent'),
                                        'signature_matched': signature.name
                                    },
                                    detection_method=DetectionMethod.PROCESS_ANALYSIS,
                                    remediation_steps=signature.remediation
                                )
                                detections.append(detection)
            
            # Verificar processos com alto uso de recursos
            if proc.get('cpu_percent', 0) > 80 and proc.get('memory_percent', 0) > 50:
                detection = ContaminationDetection(
                    detection_id=f"high_resource_{proc.get('pid', 0)}",
                    type=ContaminationType.MALICIOUS_PROCESS,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Processo com alto uso de recursos: {proc_name}",
                    evidence={
                        'process_name': proc_name,
                        'cpu_percent': proc.get('cpu_percent'),
                        'memory_percent': proc.get('memory_percent')
                    },
                    detection_method=DetectionMethod.PERFORMANCE_MONITORING,
                    confidence=0.6
                )
                detections.append(detection)
        
        return detections
    
    def _analyze_network(self, connections: List[Dict[str, Any]]) -> List[ContaminationDetection]:
        """Analisa conexões de rede"""
        detections = []
        
        # Contar conexões por IP
        connection_counts = Counter()
        suspicious_ports = {22, 23, 135, 139, 445, 1433, 3389, 5900}  # Portas comumente atacadas
        
        for conn in connections:
            if conn.get('raddr'):
                remote_ip = conn['raddr'].get('ip')
                remote_port = conn['raddr'].get('port')
                
                if remote_ip:
                    connection_counts[remote_ip] += 1
                
                # Verificar portas suspeitas
                if remote_port in suspicious_ports:
                    detection = ContaminationDetection(
                        detection_id=f"suspicious_port_{remote_ip}_{remote_port}",
                        type=ContaminationType.SUSPICIOUS_NETWORK,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Conexão em porta suspeita: {remote_ip}:{remote_port}",
                        evidence={
                            'remote_ip': remote_ip,
                            'remote_port': remote_port,
                            'local_port': conn.get('laddr', {}).get('port'),
                            'status': conn.get('status'),
                            'pid': conn.get('pid')
                        },
                        detection_method=DetectionMethod.NETWORK_MONITORING
                    )
                    detections.append(detection)
        
        # Verificar IPs com muitas conexões
        for ip, count in connection_counts.items():
            if count > 10:  # Threshold configurável
                detection = ContaminationDetection(
                    detection_id=f"multiple_connections_{ip}",
                    type=ContaminationType.SUSPICIOUS_NETWORK,
                    severity=SeverityLevel.LOW,
                    description=f"Múltiplas conexões para o mesmo IP: {ip} ({count} conexões)",
                    evidence={
                        'remote_ip': ip,
                        'connection_count': count
                    },
                    detection_method=DetectionMethod.NETWORK_MONITORING,
                    confidence=0.5
                )
                detections.append(detection)
        
        return detections
    
    def _analyze_environment_variables(self, env_vars: Dict[str, str]) -> List[ContaminationDetection]:
        """Analisa variáveis de ambiente"""
        detections = []
        
        # Verificar PATH
        path_var = env_vars.get('PATH', '')
        if path_var:
            path_entries = path_var.split(os.pathsep)
            
            # PATH muito longo
            if len(path_var) > 2048:
                detection = ContaminationDetection(
                    detection_id="path_too_long",
                    type=ContaminationType.CORRUPTED_PATH,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Variável PATH muito longa ({len(path_var)} caracteres)",
                    evidence={
                        'path_length': len(path_var),
                        'path_entries_count': len(path_entries)
                    },
                    detection_method=DetectionMethod.HEURISTIC_ANALYSIS,
                    remediation_steps=["Limpar PATH", "Remover entradas desnecessárias"]
                )
                detections.append(detection)
            
            # Entradas duplicadas no PATH
            duplicates = [entry for entry in set(path_entries) if path_entries.count(entry) > 1]
            if len(duplicates) > 3:
                detection = ContaminationDetection(
                    detection_id="path_duplicates",
                    type=ContaminationType.CORRUPTED_PATH,
                    severity=SeverityLevel.LOW,
                    description=f"Entradas duplicadas no PATH: {len(duplicates)} duplicatas",
                    evidence={
                        'duplicate_entries': duplicates[:10],  # Limitar para não sobrecarregar
                        'duplicate_count': len(duplicates)
                    },
                    detection_method=DetectionMethod.HEURISTIC_ANALYSIS,
                    remediation_steps=["Remover duplicatas do PATH"]
                )
                detections.append(detection)
        
        # Verificar variáveis suspeitas
        suspicious_vars = ['MALWARE_CONFIG', 'BACKDOOR_PORT', 'CRYPTO_WALLET']
        for var_name in suspicious_vars:
            if var_name in env_vars:
                detection = ContaminationDetection(
                    detection_id=f"suspicious_env_var_{var_name}",
                    type=ContaminationType.ENVIRONMENT_POLLUTION,
                    severity=SeverityLevel.HIGH,
                    description=f"Variável de ambiente suspeita: {var_name}",
                    evidence={
                        'variable_name': var_name,
                        'variable_value': env_vars[var_name][:100]  # Limitar tamanho
                    },
                    detection_method=DetectionMethod.SIGNATURE_MATCHING
                )
                detections.append(detection)
        
        return detections
    
    def _analyze_registry(self, registry_data: Dict[str, Any]) -> List[ContaminationDetection]:
        """Analisa registro do Windows"""
        detections = []
        
        # Verificar chaves de inicialização
        run_keys = [
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        ]
        
        for key_path in run_keys:
            if key_path in registry_data:
                values = registry_data[key_path]
                
                # Verificar entradas suspeitas
                for name, data in values.items():
                    value = data.get('value', '').lower()
                    
                    # Verificar padrões suspeitos
                    suspicious_patterns = ['temp\\', 'appdata\\roaming\\', '.tmp', '.bat', 'powershell']
                    for pattern in suspicious_patterns:
                        if pattern in value:
                            detection = ContaminationDetection(
                                detection_id=f"suspicious_startup_{name}",
                                type=ContaminationType.REGISTRY_POLLUTION,
                                severity=SeverityLevel.HIGH,
                                description=f"Entrada suspeita na inicialização: {name}",
                                evidence={
                                    'registry_key': key_path,
                                    'entry_name': name,
                                    'entry_value': value[:200],
                                    'suspicious_pattern': pattern
                                },
                                detection_method=DetectionMethod.REGISTRY_ANALYSIS,
                                remediation_steps=["Verificar legitimidade", "Remover se malicioso"]
                            )
                            detections.append(detection)
                            break
        
        return detections
    
    def _analyze_file_system(self, fs_data: Dict[str, Any]) -> List[ContaminationDetection]:
        """Analisa sistema de arquivos"""
        detections = []
        
        # Verificar diretórios temporários
        temp_dirs = [os.environ.get('TEMP', ''), os.environ.get('TMP', '')]
        
        for temp_dir in temp_dirs:
            if temp_dir and temp_dir in fs_data:
                temp_info = fs_data[temp_dir]
                file_count = temp_info.get('file_count', 0)
                total_size = temp_info.get('total_size', 0)
                
                # Muitos arquivos temporários
                if file_count > 1000:
                    detection = ContaminationDetection(
                        detection_id=f"temp_pollution_{temp_dir.replace(':', '_').replace('\\', '_')}",
                        type=ContaminationType.TEMP_POLLUTION,
                        severity=SeverityLevel.LOW,
                        description=f"Acúmulo excessivo de arquivos temporários: {file_count} arquivos",
                        evidence={
                            'directory': temp_dir,
                            'file_count': file_count,
                            'total_size_mb': total_size / (1024 * 1024) if total_size else 0
                        },
                        detection_method=DetectionMethod.FILE_SYSTEM_SCAN,
                        remediation_steps=["Limpeza de arquivos temporários"]
                    )
                    detections.append(detection)
        
        return detections
    
    def _analyze_performance(self, perf_metrics: Dict[str, float]) -> List[ContaminationDetection]:
        """Analisa métricas de performance"""
        detections = []
        
        # Adicionar ao histórico
        self.performance_history.append(perf_metrics)
        if len(self.performance_history) > self.max_history_size:
            self.performance_history.pop(0)
        
        # Verificar uso excessivo de recursos
        cpu_percent = perf_metrics.get('cpu_percent', 0)
        memory_percent = perf_metrics.get('memory_percent', 0)
        
        if cpu_percent > 90:
            detection = ContaminationDetection(
                detection_id="high_cpu_usage",
                type=ContaminationType.MEMORY_ISSUES,
                severity=SeverityLevel.MEDIUM,
                description=f"Uso excessivo de CPU: {cpu_percent:.1f}%",
                evidence={
                    'cpu_percent': cpu_percent,
                    'process_count': perf_metrics.get('process_count', 0)
                },
                detection_method=DetectionMethod.PERFORMANCE_MONITORING,
                confidence=0.7
            )
            detections.append(detection)
        
        if memory_percent > 95:
            detection = ContaminationDetection(
                detection_id="high_memory_usage",
                type=ContaminationType.MEMORY_ISSUES,
                severity=SeverityLevel.HIGH,
                description=f"Uso excessivo de memória: {memory_percent:.1f}%",
                evidence={
                    'memory_percent': memory_percent
                },
                detection_method=DetectionMethod.PERFORMANCE_MONITORING
            )
            detections.append(detection)
        
        return detections
    
    def _compare_with_baseline(self, current: SystemSnapshot, baseline: SystemSnapshot) -> List[ContaminationDetection]:
        """Compara snapshot atual com baseline"""
        detections = []
        
        # Comparar processos
        baseline_processes = {proc.get('name', ''): proc for proc in baseline.processes}
        current_processes = {proc.get('name', ''): proc for proc in current.processes}
        
        # Novos processos
        new_processes = set(current_processes.keys()) - set(baseline_processes.keys())
        for proc_name in new_processes:
            if proc_name and not self._is_whitelisted(proc_name):
                detection = ContaminationDetection(
                    detection_id=f"new_process_{proc_name}",
                    type=ContaminationType.MALICIOUS_PROCESS,
                    severity=SeverityLevel.LOW,
                    description=f"Novo processo detectado: {proc_name}",
                    evidence={
                        'process_name': proc_name,
                        'process_info': current_processes[proc_name]
                    },
                    detection_method=DetectionMethod.BEHAVIORAL_ANALYSIS,
                    confidence=0.4
                )
                detections.append(detection)
        
        # Comparar variáveis de ambiente
        baseline_env = set(baseline.environment_variables.items())
        current_env = set(current.environment_variables.items())
        
        new_env_vars = current_env - baseline_env
        for var_name, var_value in new_env_vars:
            if not self._is_whitelisted(var_name):
                detection = ContaminationDetection(
                    detection_id=f"new_env_var_{var_name}",
                    type=ContaminationType.ENVIRONMENT_POLLUTION,
                    severity=SeverityLevel.LOW,
                    description=f"Nova variável de ambiente: {var_name}",
                    evidence={
                        'variable_name': var_name,
                        'variable_value': var_value[:100]
                    },
                    detection_method=DetectionMethod.BEHAVIORAL_ANALYSIS,
                    confidence=0.3
                )
                detections.append(detection)
        
        return detections
    
    def _check_process_indicators(self, process: Dict[str, Any], indicators: Dict[str, Any]) -> bool:
        """Verifica indicadores específicos de um processo"""
        for indicator, threshold in indicators.items():
            if indicator == "cpu_usage":
                cpu_percent = process.get('cpu_percent', 0)
                if threshold.startswith('>'):
                    if cpu_percent <= float(threshold[1:]):
                        return False
            elif indicator == "memory_usage":
                memory_percent = process.get('memory_percent', 0)
                if threshold.startswith('>'):
                    if memory_percent <= float(threshold[1:]):
                        return False
        
        return True
    
    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Verifica se texto corresponde ao padrão"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calcula hash de um arquivo"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None
    
    def _count_files(self, directory: str) -> int:
        """Conta arquivos em um diretório"""
        try:
            return sum(1 for _ in Path(directory).rglob('*') if _.is_file())
        except Exception:
            return 0
    
    def _get_directory_size(self, directory: str) -> int:
        """Obtém tamanho total de um diretório"""
        try:
            return sum(f.stat().st_size for f in Path(directory).rglob('*') if f.is_file())
        except Exception:
            return 0
    
    def _filter_detections(self, detections: List[ContaminationDetection]) -> List[ContaminationDetection]:
        """Filtra detecções duplicadas e aplica whitelist"""
        filtered = []
        seen_ids = set()
        
        for detection in detections:
            # Verificar duplicatas
            if detection.detection_id in seen_ids:
                continue
            
            # Verificar whitelist
            if self._is_detection_whitelisted(detection):
                continue
            
            filtered.append(detection)
            seen_ids.add(detection.detection_id)
        
        return filtered
    
    def _is_whitelisted(self, item: str) -> bool:
        """Verifica se item está na whitelist"""
        return item.lower() in self.whitelist
    
    def _is_detection_whitelisted(self, detection: ContaminationDetection) -> bool:
        """Verifica se detecção está na whitelist"""
        # Verificar por ID
        if detection.detection_id in self.whitelist:
            return True
        
        # Verificar por evidências
        for key, value in detection.evidence.items():
            if isinstance(value, str) and value.lower() in self.whitelist:
                return True
        
        return False
    
    def start_continuous_monitoring(self, interval: int = 300):
        """Inicia monitoramento contínuo"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info(f"Monitoramento contínuo iniciado (intervalo: {interval}s)")
    
    def stop_continuous_monitoring(self):
        """Para monitoramento contínuo"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Monitoramento contínuo parado")
    
    def _monitoring_loop(self, interval: int):
        """Loop de monitoramento contínuo"""
        while self.monitoring_active:
            try:
                detections = self.detect_contamination()
                if detections:
                    self.logger.warning(f"Detectadas {len(detections)} contaminações durante monitoramento")
                    # Aqui poderia enviar notificações ou tomar ações automáticas
                
                time.sleep(interval)
            
            except Exception as e:
                self.logger.error(f"Erro durante monitoramento: {e}")
                time.sleep(interval)
    
    def generate_contamination_report(self, detections: List[ContaminationDetection]) -> Dict[str, Any]:
        """Gera relatório de contaminação"""
        # Estatísticas por tipo
        type_counts = Counter(d.type.value for d in detections)
        severity_counts = Counter(d.severity.value for d in detections)
        
        # Componentes mais afetados
        affected_components = []
        for detection in detections:
            affected_components.extend(detection.affected_components)
        component_counts = Counter(affected_components)
        
        return {
            'summary': {
                'total_detections': len(detections),
                'critical_count': severity_counts.get('critical', 0),
                'high_count': severity_counts.get('high', 0),
                'medium_count': severity_counts.get('medium', 0),
                'low_count': severity_counts.get('low', 0),
                'contamination_score': self._calculate_contamination_score(detections)
            },
            'detections_by_type': dict(type_counts),
            'detections_by_severity': dict(severity_counts),
            'most_affected_components': dict(component_counts.most_common(10)),
            'detections': [
                {
                    'id': d.detection_id,
                    'type': d.type.value,
                    'severity': d.severity.value,
                    'description': d.description,
                    'confidence': d.confidence,
                    'timestamp': d.timestamp,
                    'evidence': d.evidence,
                    'remediation_steps': d.remediation_steps
                } for d in detections
            ],
            'recommendations': self._generate_cleanup_recommendations(detections)
        }
    
    def _calculate_contamination_score(self, detections: List[ContaminationDetection]) -> float:
        """Calcula score de contaminação (0-100)"""
        if not detections:
            return 0.0
        
        severity_weights = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 8,
            SeverityLevel.LOW: 3
        }
        
        total_score = sum(severity_weights.get(d.severity, 0) * d.confidence for d in detections)
        return min(100.0, total_score)
    
    def _generate_cleanup_recommendations(self, detections: List[ContaminationDetection]) -> List[str]:
        """Gera recomendações de limpeza"""
        recommendations = set()
        
        for detection in detections:
            recommendations.update(detection.remediation_steps)
        
        # Adicionar recomendações gerais
        if any(d.type == ContaminationType.TEMP_POLLUTION for d in detections):
            recommendations.add("Executar limpeza de arquivos temporários")
        
        if any(d.type == ContaminationType.REGISTRY_POLLUTION for d in detections):
            recommendations.add("Executar limpeza do registro")
        
        if any(d.severity == SeverityLevel.CRITICAL for d in detections):
            recommendations.add("Executar verificação completa de antivírus")
        
        return sorted(list(recommendations))

# Instância global
_contamination_detector: Optional[EnvironmentContaminationDetector] = None

def get_contamination_detector() -> EnvironmentContaminationDetector:
    """Obtém instância global do detector de contaminação"""
    global _contamination_detector
    if _contamination_detector is None:
        _contamination_detector = EnvironmentContaminationDetector()
    return _contamination_detector