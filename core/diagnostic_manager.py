# -*- coding: utf-8 -*-
"""
Diagnostic Manager para Environment Dev Script
Módulo responsável por diagnóstico completo do ambiente e detecção de problemas
"""

import os
import sys
import platform
import logging
import psutil
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from utils.os_detection import detect_operating_systems
from utils.disk_space import get_disk_space
from utils.permission_checker import is_admin, check_write_permission
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Status geral de saúde do sistema"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class CompatibilityStatus(Enum):
    """Status de compatibilidade do sistema"""
    FULLY_COMPATIBLE = "fully_compatible"
    MOSTLY_COMPATIBLE = "mostly_compatible"
    LIMITED_COMPATIBILITY = "limited_compatibility"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"

class IssueSeverity(Enum):
    """Severidade de problemas detectados"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class IssueCategory(Enum):
    """Categoria de problemas"""
    SYSTEM = "system"
    PERMISSIONS = "permissions"
    DISK_SPACE = "disk_space"
    DEPENDENCIES = "dependencies"
    CONFLICTS = "conflicts"
    NETWORK = "network"
    CONFIGURATION = "configuration"

@dataclass
class SystemInfo:
    """Informações detalhadas do sistema"""
    os_name: str
    os_version: str
    os_build: str
    architecture: str
    processor: str
    total_memory: int  # em bytes
    available_memory: int  # em bytes
    disk_space_total: int  # em bytes
    disk_space_free: int  # em bytes
    python_version: str
    python_executable: str
    is_admin: bool
    username: str
    hostname: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Issue:
    """Representa um problema detectado no sistema"""
    id: str
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_components: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Solution:
    """Representa uma solução sugerida para um problema"""
    issue_id: str
    title: str
    description: str
    steps: List[str]
    automatic: bool = False
    risk_level: str = "low"  # low, medium, high
    estimated_time: str = "unknown"

@dataclass
class CompatibilityResult:
    """Resultado da verificação de compatibilidade"""
    status: CompatibilityStatus
    supported_features: List[str]
    unsupported_features: List[str]
    warnings: List[str]
    recommendations: List[str]

@dataclass
class DiagnosticResult:
    """Resultado completo do diagnóstico do sistema"""
    system_info: SystemInfo
    compatibility: CompatibilityResult
    issues: List[Issue]
    suggestions: List[Solution]
    overall_health: HealthStatus
    timestamp: datetime = field(default_factory=datetime.now)
    diagnostic_duration: float = 0.0  # em segundos

class DiagnosticManager:
    """
    Gerenciador de diagnóstico do sistema
    
    Responsável por:
    - Diagnóstico completo do ambiente
    - Verificação de compatibilidade do sistema
    - Detecção de problemas e conflitos
    - Geração de sugestões de solução
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._supported_os = ["Windows"]
        self._min_python_version = (3, 8)
        self._min_disk_space_gb = 5
        self._min_memory_gb = 4
    
    def _get_os_info(self) -> Dict[str, str]:
        """
        Obtém informações básicas do sistema operacional
        
        Returns:
            Dict[str, str]: Informações do sistema operacional
        """
        try:
            # Usa platform para informações básicas
            return {
                'name': platform.system(),
                'version': platform.version(),
                'build': platform.release()
            }
        except Exception as e:
            self.logger.warning(f"Erro ao obter informações do OS: {e}")
            return {
                'name': 'Unknown',
                'version': 'Unknown',
                'build': 'Unknown'
            }
        
    def run_full_diagnostic(self) -> DiagnosticResult:
        """
        Executa diagnóstico completo do sistema
        
        Returns:
            DiagnosticResult: Resultado completo do diagnóstico
        """
        start_time = datetime.now()
        self.logger.info("Iniciando diagnóstico completo do sistema")
        
        try:
            # Coleta informações do sistema
            system_info = self._collect_system_info()
            
            # Verifica compatibilidade
            compatibility = self.check_system_compatibility()
            
            # Detecta problemas
            issues = self._detect_system_issues(system_info)
            
            # Gera sugestões
            suggestions = self._generate_suggestions(issues)
            
            # Calcula saúde geral
            overall_health = self._calculate_overall_health(issues, compatibility)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = DiagnosticResult(
                system_info=system_info,
                compatibility=compatibility,
                issues=issues,
                suggestions=suggestions,
                overall_health=overall_health,
                timestamp=end_time,
                diagnostic_duration=duration
            )
            
            self.logger.info(f"Diagnóstico concluído em {duration:.2f}s - Status: {overall_health.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Erro durante diagnóstico: {e}")
            raise EnvDevError(
                f"Falha no diagnóstico do sistema: {e}",
                ErrorSeverity.HIGH,
                ErrorCategory.SYSTEM
            )
    
    def check_system_compatibility(self) -> CompatibilityResult:
        """
        Verifica compatibilidade básica do sistema
        
        Returns:
            CompatibilityResult: Resultado da verificação de compatibilidade
        """
        self.logger.info("Verificando compatibilidade do sistema")
        
        supported_features = []
        unsupported_features = []
        warnings = []
        recommendations = []
        
        try:
            # Verifica sistema operacional
            os_info = self._get_os_info()
            if os_info.get('name', '').startswith('Windows'):
                supported_features.append("Windows OS")
                
                # Verifica versão do Windows
                version = os_info.get('version', '')
                if version and int(version.split('.')[0]) >= 10:
                    supported_features.append("Windows 10+")
                else:
                    warnings.append("Windows 10 ou superior recomendado")
                    
            else:
                unsupported_features.append("Sistema operacional não suportado")
                warnings.append(f"Sistema {os_info.get('name', 'desconhecido')} não é oficialmente suportado")
            
            # Verifica versão do Python
            python_version = sys.version_info
            if python_version >= self._min_python_version:
                supported_features.append(f"Python {python_version.major}.{python_version.minor}")
            else:
                unsupported_features.append("Versão do Python inadequada")
                recommendations.append(f"Atualize para Python {self._min_python_version[0]}.{self._min_python_version[1]} ou superior")
            
            # Verifica privilégios administrativos
            if is_admin():
                supported_features.append("Privilégios administrativos")
            else:
                warnings.append("Executando sem privilégios administrativos - algumas funcionalidades podem ser limitadas")
                recommendations.append("Execute o script como administrador para funcionalidade completa")
            
            # Verifica espaço em disco
            disk_space = get_disk_space(Path.cwd().drive)
            if disk_space.free / (1024**3) >= self._min_disk_space_gb:
                supported_features.append(f"Espaço em disco suficiente ({disk_space.free / (1024**3):.1f} GB livre)")
            else:
                unsupported_features.append("Espaço em disco insuficiente")
                recommendations.append(f"Libere pelo menos {self._min_disk_space_gb} GB de espaço em disco")
            
            # Verifica memória
            memory = psutil.virtual_memory()
            if memory.total / (1024**3) >= self._min_memory_gb:
                supported_features.append(f"Memória suficiente ({memory.total / (1024**3):.1f} GB)")
            else:
                warnings.append(f"Memória RAM baixa ({memory.total / (1024**3):.1f} GB) - pode afetar desempenho")
                recommendations.append("Considere adicionar mais memória RAM")
            
            # Determina status geral
            if unsupported_features:
                status = CompatibilityStatus.INCOMPATIBLE
            elif len(warnings) > 2:
                status = CompatibilityStatus.LIMITED_COMPATIBILITY
            elif warnings:
                status = CompatibilityStatus.MOSTLY_COMPATIBLE
            else:
                status = CompatibilityStatus.FULLY_COMPATIBLE
            
            return CompatibilityResult(
                status=status,
                supported_features=supported_features,
                unsupported_features=unsupported_features,
                warnings=warnings,
                recommendations=recommendations
            )
        
        except Exception as e:
            self.logger.error(f"Erro durante verificação de compatibilidade: {e}")
            return CompatibilityResult(
                status=CompatibilityStatus.UNKNOWN,
                supported_features=[],
                unsupported_features=[],
                warnings=[f"Erro na verificação: {str(e)}"],
                recommendations=[]
            )
    
    def check_system_health(self) -> Dict[str, Any]:
        """Verifica saúde geral do sistema"""
        try:
            health = {}
            # CPU
            health['cpu_usage'] = psutil.cpu_percent()
            # Memória
            mem = psutil.virtual_memory()
            health['memory_usage'] = mem.percent
            # Disco
            disk = psutil.disk_usage('/')
            health['disk_usage'] = disk.percent
            return health
        except Exception as e:
            self.logger.warning(f"Erro ao verificar saúde do sistema: {e}")
            return {}
    
    def check_network_connectivity(self) -> bool:
        """Verifica conectividade de rede"""
        try:
            import socket
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False
            if is_admin():
                supported_features.append("Privilégios administrativos")
            else:
                warnings.append("Privilégios administrativos não detectados")
                recommendations.append("Execute como administrador para funcionalidade completa")
            
            # Verifica espaço em disco
            disk_info = get_disk_space(".")
            disk_space_gb = disk_info['free'] / (1024**3)  # Converte para GB
            if disk_space_gb >= self._min_disk_space_gb:
                supported_features.append(f"Espaço em disco suficiente ({disk_space_gb:.1f}GB)")
            else:
                unsupported_features.append("Espaço em disco insuficiente")
                recommendations.append(f"Libere pelo menos {self._min_disk_space_gb}GB de espaço em disco")
            
            # Verifica memória RAM
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb >= self._min_memory_gb:
                supported_features.append(f"Memória RAM suficiente ({memory_gb:.1f}GB)")
            else:
                warnings.append(f"Memória RAM baixa ({memory_gb:.1f}GB)")
                recommendations.append(f"Recomendado pelo menos {self._min_memory_gb}GB de RAM")
            
            # Determina status de compatibilidade
            if unsupported_features:
                status = CompatibilityStatus.INCOMPATIBLE
            elif warnings:
                if len(warnings) > len(supported_features):
                    status = CompatibilityStatus.LIMITED_COMPATIBILITY
                else:
                    status = CompatibilityStatus.MOSTLY_COMPATIBLE
            else:
                status = CompatibilityStatus.FULLY_COMPATIBLE
            
            return CompatibilityResult(
                status=status,
                supported_features=supported_features,
                unsupported_features=unsupported_features,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de compatibilidade: {e}")
            return CompatibilityResult(
                status=CompatibilityStatus.UNKNOWN,
                supported_features=[],
                unsupported_features=[],
                warnings=[f"Erro na verificação: {e}"],
                recommendations=["Execute o diagnóstico novamente"]
            )
    
    def _collect_system_info(self) -> SystemInfo:
        """
        Coleta informações detalhadas do sistema
        
        Returns:
            SystemInfo: Informações do sistema
        """
        try:
            # Informações básicas do sistema
            os_info = self._get_os_info()
            memory = psutil.virtual_memory()
            disk_usage = psutil.disk_usage('/')
            
            return SystemInfo(
                os_name=os_info.get('name', platform.system()),
                os_version=os_info.get('version', platform.version()),
                os_build=os_info.get('build', platform.release()),
                architecture=platform.architecture()[0],
                processor=platform.processor() or "Unknown",
                total_memory=memory.total,
                available_memory=memory.available,
                disk_space_total=disk_usage.total,
                disk_space_free=disk_usage.free,
                python_version=platform.python_version(),
                python_executable=sys.executable,
                is_admin=is_admin(),
                username=os.getenv('USERNAME', os.getenv('USER', 'unknown')),
                hostname=platform.node()
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar informações do sistema: {e}")
            raise EnvDevError(
                f"Falha ao coletar informações do sistema: {e}",
                ErrorSeverity.HIGH,
                ErrorCategory.SYSTEM
            )
    
    def _detect_system_issues(self, system_info: SystemInfo) -> List[Issue]:
        """
        Detecta problemas no sistema
        
        Args:
            system_info: Informações do sistema
            
        Returns:
            List[Issue]: Lista de problemas detectados
        """
        issues = []
        
        # Verifica espaço em disco
        disk_free_gb = system_info.disk_space_free / (1024**3)
        if disk_free_gb < self._min_disk_space_gb:
            issues.append(Issue(
                id="disk_space_low",
                category=IssueCategory.DISK_SPACE,
                severity=IssueSeverity.ERROR if disk_free_gb < 2 else IssueSeverity.WARNING,
                title="Espaço em disco insuficiente",
                description=f"Apenas {disk_free_gb:.1f}GB disponível, mínimo recomendado: {self._min_disk_space_gb}GB",
                details={"free_space_gb": disk_free_gb, "required_gb": self._min_disk_space_gb}
            ))
        
        # Verifica memória RAM
        memory_gb = system_info.total_memory / (1024**3)
        if memory_gb < self._min_memory_gb:
            issues.append(Issue(
                id="memory_low",
                category=IssueCategory.SYSTEM,
                severity=IssueSeverity.WARNING,
                title="Memória RAM baixa",
                description=f"Sistema com {memory_gb:.1f}GB RAM, recomendado: {self._min_memory_gb}GB",
                details={"total_memory_gb": memory_gb, "recommended_gb": self._min_memory_gb}
            ))
        
        # Verifica privilégios administrativos
        if not system_info.is_admin:
            issues.append(Issue(
                id="no_admin_privileges",
                category=IssueCategory.PERMISSIONS,
                severity=IssueSeverity.WARNING,
                title="Sem privilégios administrativos",
                description="Algumas funcionalidades podem não estar disponíveis",
                details={"current_user": system_info.username}
            ))
        
        # Verifica versão do Python
        python_version = tuple(map(int, system_info.python_version.split('.')))
        if python_version < self._min_python_version:
            issues.append(Issue(
                id="python_version_old",
                category=IssueCategory.DEPENDENCIES,
                severity=IssueSeverity.ERROR,
                title="Versão do Python inadequada",
                description=f"Python {system_info.python_version} detectado, mínimo: {'.'.join(map(str, self._min_python_version))}",
                details={"current_version": system_info.python_version, "min_version": self._min_python_version}
            ))
        
        # Adiciona verificações de ambiente específicas
        issues.extend(self._check_os_version_compatibility(system_info))
        issues.extend(self._detect_conflicting_software())
        issues.extend(self._check_disk_space_detailed())
        issues.extend(self._check_user_permissions())
        
        return issues
    
    def _generate_suggestions(self, issues: List[Issue]) -> List[Solution]:
        """
        Gera sugestões de solução para os problemas detectados
        
        Args:
            issues: Lista de problemas detectados
            
        Returns:
            List[Solution]: Lista de soluções sugeridas
        """
        suggestions = []
        
        for issue in issues:
            if issue.id == "disk_space_low":
                suggestions.append(Solution(
                    issue_id=issue.id,
                    title="Liberar espaço em disco",
                    description="Remova arquivos desnecessários para liberar espaço",
                    steps=[
                        "Execute o Limpeza de Disco do Windows",
                        "Remova arquivos temporários",
                        "Desinstale programas não utilizados",
                        "Mova arquivos grandes para outro local"
                    ],
                    automatic=False,
                    risk_level="low",
                    estimated_time="10-30 minutos"
                ))
            
            elif issue.id == "memory_low":
                suggestions.append(Solution(
                    issue_id=issue.id,
                    title="Otimizar uso de memória",
                    description="Feche aplicações desnecessárias para liberar RAM",
                    steps=[
                        "Feche navegadores e aplicações não essenciais",
                        "Reinicie o sistema se necessário",
                        "Considere adicionar mais RAM ao sistema"
                    ],
                    automatic=False,
                    risk_level="low",
                    estimated_time="5-10 minutos"
                ))
            
            elif issue.id == "no_admin_privileges":
                suggestions.append(Solution(
                    issue_id=issue.id,
                    title="Executar como administrador",
                    description="Reinicie o aplicativo com privilégios administrativos",
                    steps=[
                        "Feche o aplicativo atual",
                        "Clique com botão direito no ícone do aplicativo",
                        "Selecione 'Executar como administrador'",
                        "Confirme a elevação de privilégios"
                    ],
                    automatic=True,
                    risk_level="low",
                    estimated_time="1-2 minutos"
                ))
            
            elif issue.id == "python_version_old":
                suggestions.append(Solution(
                    issue_id=issue.id,
                    title="Atualizar Python",
                    description="Instale uma versão mais recente do Python",
                    steps=[
                        "Acesse https://python.org/downloads",
                        "Baixe a versão mais recente do Python",
                        "Execute o instalador",
                        "Reinicie o sistema após a instalação"
                    ],
                    automatic=False,
                    risk_level="medium",
                    estimated_time="15-30 minutos"
                ))
        
        return suggestions
    
    def _calculate_overall_health(self, issues: List[Issue], compatibility: CompatibilityResult) -> HealthStatus:
        """
        Calcula o status geral de saúde do sistema
        
        Args:
            issues: Lista de problemas detectados
            compatibility: Resultado da verificação de compatibilidade
            
        Returns:
            HealthStatus: Status geral de saúde
        """
        # Conta problemas por severidade
        critical_count = sum(1 for issue in issues if issue.severity == IssueSeverity.CRITICAL)
        error_count = sum(1 for issue in issues if issue.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == IssueSeverity.WARNING)
        
        # Determina saúde baseada nos problemas e compatibilidade
        if critical_count > 0 or compatibility.status == CompatibilityStatus.INCOMPATIBLE:
            return HealthStatus.CRITICAL
        elif error_count > 0 or compatibility.status == CompatibilityStatus.LIMITED_COMPATIBILITY:
            return HealthStatus.WARNING
        elif warning_count > 2 or compatibility.status == CompatibilityStatus.MOSTLY_COMPATIBLE:
            return HealthStatus.GOOD
        elif warning_count == 0 and compatibility.status == CompatibilityStatus.FULLY_COMPATIBLE:
            return HealthStatus.EXCELLENT
        else:
            return HealthStatus.GOOD
    
    def _check_os_version_compatibility(self, system_info: SystemInfo) -> List[Issue]:
        """
        Verifica compatibilidade detalhada da versão do sistema operacional
        
        Args:
            system_info: Informações do sistema
            
        Returns:
            List[Issue]: Lista de problemas relacionados ao SO
        """
        issues = []
        
        try:
            if system_info.os_name.startswith('Windows'):
                # Extrai versão do Windows
                version_parts = system_info.os_version.split('.')
                if len(version_parts) >= 1:
                    major_version = int(version_parts[0])
                    
                    # Windows 7 ou anterior (não suportado)
                    if major_version < 10:
                        issues.append(Issue(
                            id="windows_version_unsupported",
                            category=IssueCategory.SYSTEM,
                            severity=IssueSeverity.ERROR,
                            title="Versão do Windows não suportada",
                            description=f"Windows {major_version} detectado. Mínimo: Windows 10",
                            details={"detected_version": major_version, "min_version": 10}
                        ))
                    
                    # Windows 10 versões antigas
                    elif major_version == 10 and len(version_parts) >= 3:
                        build_number = int(version_parts[2])
                        if build_number < 19041:  # Windows 10 2004
                            issues.append(Issue(
                                id="windows_build_old",
                                category=IssueCategory.SYSTEM,
                                severity=IssueSeverity.WARNING,
                                title="Build do Windows desatualizada",
                                description=f"Build {build_number} detectada. Recomendado: 19041+",
                                details={"detected_build": build_number, "recommended_build": 19041}
                            ))
            else:
                # Sistema operacional não Windows
                issues.append(Issue(
                    id="unsupported_os",
                    category=IssueCategory.SYSTEM,
                    severity=IssueSeverity.CRITICAL,
                    title="Sistema operacional não suportado",
                    description=f"Sistema {system_info.os_name} não é suportado",
                    details={"detected_os": system_info.os_name, "supported_os": self._supported_os}
                ))
                
        except Exception as e:
            self.logger.warning(f"Erro ao verificar compatibilidade do SO: {e}")
            issues.append(Issue(
                id="os_check_failed",
                category=IssueCategory.SYSTEM,
                severity=IssueSeverity.WARNING,
                title="Falha na verificação do sistema operacional",
                description=f"Não foi possível verificar a compatibilidade: {e}",
                details={"error": str(e)}
            ))
        
        return issues
    
    def _detect_conflicting_software(self) -> List[Issue]:
        """
        Detecta software que pode conflitar com o Environment Dev
        
        Returns:
            List[Issue]: Lista de problemas relacionados a software conflitante
        """
        issues = []
        
        try:
            # Lista de software conhecido por causar conflitos
            conflicting_software = {
                "VMware": ["vmware.exe", "vmware-vmx.exe"],
                "VirtualBox": ["VirtualBox.exe", "VBoxSVC.exe"],
                "Hyper-V": ["vmms.exe", "vmwp.exe"],
                "Docker Desktop": ["Docker Desktop.exe", "com.docker.backend.exe"],
                "Antivirus Agressivo": ["avp.exe", "mcshield.exe", "avgnt.exe"]
            }
            
            # Verifica processos em execução
            running_processes = [proc.name().lower() for proc in psutil.process_iter(['name'])]
            
            for software_name, process_names in conflicting_software.items():
                for process_name in process_names:
                    if process_name.lower() in running_processes:
                        issues.append(Issue(
                            id=f"conflicting_software_{software_name.lower().replace(' ', '_')}",
                            category=IssueCategory.CONFLICTS,
                            severity=IssueSeverity.WARNING,
                            title=f"Software conflitante detectado: {software_name}",
                            description=f"{software_name} pode interferir com instalações",
                            details={"software": software_name, "process": process_name},
                            affected_components=["installation", "virtualization"]
                        ))
                        break  # Evita múltiplos alertas para o mesmo software
            
            # Verifica serviços do Windows que podem causar conflitos
            if platform.system() == "Windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ['sc', 'query', 'type=', 'service', 'state=', 'running'],
                        capture_output=True, text=True, check=False
                    )
                    
                    if result.returncode == 0:
                        services_output = result.stdout.lower()
                        
                        # Verifica Hyper-V
                        if 'vmms' in services_output:
                            issues.append(Issue(
                                id="hyperv_service_running",
                                category=IssueCategory.CONFLICTS,
                                severity=IssueSeverity.WARNING,
                                title="Hyper-V ativo",
                                description="Serviço Hyper-V pode conflitar com outras virtualizações",
                                details={"service": "vmms"},
                                affected_components=["virtualization"]
                            ))
                        
                        # Verifica Windows Defender em modo restritivo
                        if 'windefend' in services_output:
                            issues.append(Issue(
                                id="windows_defender_active",
                                category=IssueCategory.CONFLICTS,
                                severity=IssueSeverity.INFO,
                                title="Windows Defender ativo",
                                description="Pode ser necessário adicionar exceções para downloads",
                                details={"service": "windefend"},
                                affected_components=["download", "installation"]
                            ))
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao verificar serviços: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Erro ao detectar software conflitante: {e}")
            issues.append(Issue(
                id="conflict_detection_failed",
                category=IssueCategory.CONFLICTS,
                severity=IssueSeverity.WARNING,
                title="Falha na detecção de conflitos",
                description=f"Não foi possível verificar software conflitante: {e}",
                details={"error": str(e)}
            ))
        
        return issues
    
    def _check_disk_space_detailed(self) -> List[Issue]:
        """
        Verifica espaço em disco de forma detalhada
        
        Returns:
            List[Issue]: Lista de problemas relacionados ao espaço em disco
        """
        issues = []
        
        try:
            # Verifica espaço no diretório atual
            current_disk = get_disk_space(".")
            current_free_gb = current_disk['free'] / (1024**3)
            
            # Verifica espaço crítico (menos de 1GB)
            if current_free_gb < 1:
                issues.append(Issue(
                    id="disk_space_critical",
                    category=IssueCategory.DISK_SPACE,
                    severity=IssueSeverity.CRITICAL,
                    title="Espaço em disco criticamente baixo",
                    description=f"Apenas {current_free_gb:.2f}GB disponível",
                    details={"free_space_gb": current_free_gb, "critical_threshold": 1}
                ))
            
            # Verifica diretório temporário
            temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
            if os.path.exists(temp_dir):
                temp_disk = get_disk_space(temp_dir)
                temp_free_gb = temp_disk['free'] / (1024**3)
                
                if temp_free_gb < 2:
                    issues.append(Issue(
                        id="temp_disk_space_low",
                        category=IssueCategory.DISK_SPACE,
                        severity=IssueSeverity.WARNING,
                        title="Espaço insuficiente no diretório temporário",
                        description=f"Apenas {temp_free_gb:.1f}GB no diretório temp",
                        details={"temp_dir": temp_dir, "free_space_gb": temp_free_gb}
                    ))
            
            # Verifica fragmentação (Windows)
            if platform.system() == "Windows":
                try:
                    # Verifica se o disco está muito fragmentado (estimativa simples)
                    disk_usage_percent = (current_disk['used'] / current_disk['total']) * 100
                    if disk_usage_percent > 90:
                        issues.append(Issue(
                            id="disk_nearly_full",
                            category=IssueCategory.DISK_SPACE,
                            severity=IssueSeverity.WARNING,
                            title="Disco quase cheio",
                            description=f"Disco {disk_usage_percent:.1f}% cheio",
                            details={"usage_percent": disk_usage_percent}
                        ))
                except Exception as e:
                    self.logger.debug(f"Erro ao verificar fragmentação: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Erro na verificação detalhada de disco: {e}")
            issues.append(Issue(
                id="disk_check_failed",
                category=IssueCategory.DISK_SPACE,
                severity=IssueSeverity.WARNING,
                title="Falha na verificação de disco",
                description=f"Não foi possível verificar espaço em disco: {e}",
                details={"error": str(e)}
            ))
        
        return issues
    
    def _check_user_permissions(self) -> List[Issue]:
        """
        Verifica permissões detalhadas do usuário
        
        Returns:
            List[Issue]: Lista de problemas relacionados a permissões
        """
        issues = []
        
        try:
            # Verifica permissões de escrita em diretórios importantes
            important_dirs = [
                ("Diretório atual", "."),
                ("Diretório temporário", os.environ.get('TEMP', 'C:\\temp')),
                ("Program Files", "C:\\Program Files"),
                ("Program Files (x86)", "C:\\Program Files (x86)")
            ]
            
            for dir_name, dir_path in important_dirs:
                if os.path.exists(dir_path):
                    try:
                        has_write = check_write_permission(dir_path)
                        if not has_write and dir_name in ["Diretório atual", "Diretório temporário"]:
                            issues.append(Issue(
                                id=f"no_write_permission_{dir_name.lower().replace(' ', '_')}",
                                category=IssueCategory.PERMISSIONS,
                                severity=IssueSeverity.ERROR,
                                title=f"Sem permissão de escrita: {dir_name}",
                                description=f"Não é possível escrever em {dir_path}",
                                details={"directory": dir_path, "permission": "write"}
                            ))
                        elif not has_write:
                            issues.append(Issue(
                                id=f"limited_write_permission_{dir_name.lower().replace(' ', '_')}",
                                category=IssueCategory.PERMISSIONS,
                                severity=IssueSeverity.INFO,
                                title=f"Permissão limitada: {dir_name}",
                                description=f"Sem permissão de escrita em {dir_path}",
                                details={"directory": dir_path, "permission": "write"}
                            ))
                    except Exception as e:
                        self.logger.debug(f"Erro ao verificar permissões em {dir_path}: {e}")
            
            # Verifica se está executando como usuário padrão vs administrador
            if not is_admin():
                # Verifica se UAC está habilitado
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
                    )
                    uac_enabled = winreg.QueryValueEx(key, "EnableLUA")[0]
                    winreg.CloseKey(key)
                    
                    if uac_enabled:
                        issues.append(Issue(
                            id="uac_enabled_no_admin",
                            category=IssueCategory.PERMISSIONS,
                            severity=IssueSeverity.INFO,
                            title="UAC habilitado sem privilégios admin",
                            description="Algumas operações podem solicitar elevação",
                            details={"uac_enabled": True, "is_admin": False}
                        ))
                except Exception as e:
                    self.logger.debug(f"Erro ao verificar UAC: {e}")
            
            # Verifica permissões de registro (Windows)
            if platform.system() == "Windows":
                try:
                    import winreg
                    # Tenta acessar uma chave de registro comum
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software")
                    winreg.CloseKey(key)
                except Exception as e:
                    issues.append(Issue(
                        id="registry_access_limited",
                        category=IssueCategory.PERMISSIONS,
                        severity=IssueSeverity.WARNING,
                        title="Acesso limitado ao registro",
                        description="Pode afetar algumas instalações",
                        details={"error": str(e)}
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Erro na verificação de permissões: {e}")
            issues.append(Issue(
                id="permission_check_failed",
                category=IssueCategory.PERMISSIONS,
                severity=IssueSeverity.WARNING,
                title="Falha na verificação de permissões",
                description=f"Não foi possível verificar permissões: {e}",
                details={"error": str(e)}
            ))
        
        return issues
    
    def detect_conflicts(self, components: List[str]) -> 'ConflictResult':
        """
        Detecta conflitos entre componentes especificados
        
        Args:
            components: Lista de nomes de componentes para verificar
            
        Returns:
            ConflictResult: Resultado da detecção de conflitos
        """
        self.logger.info(f"Detectando conflitos entre componentes: {components}")
        
        try:
            conflicts = []
            warnings = []
            
            # Simula detecção de conflitos baseada em componentes conhecidos
            # Em uma implementação real, isso consultaria o arquivo components.yaml
            known_conflicts = {
                ("CloverBootManager", "rEFInd"): "Ambos são boot managers e não podem coexistir",
                ("VMware", "VirtualBox"): "Hypervisors podem conflitar entre si",
                ("Docker", "Hyper-V"): "Docker Desktop pode ter problemas com Hyper-V",
                ("SteamDeckTools", "HandheldCompanion"): "Ferramentas de handheld podem conflitar"
            }
            
            # Verifica conflitos diretos
            for i, comp1 in enumerate(components):
                for comp2 in components[i+1:]:
                    conflict_key = (comp1, comp2)
                    reverse_key = (comp2, comp1)
                    
                    if conflict_key in known_conflicts:
                        conflicts.append({
                            "components": [comp1, comp2],
                            "reason": known_conflicts[conflict_key],
                            "severity": "high"
                        })
                    elif reverse_key in known_conflicts:
                        conflicts.append({
                            "components": [comp1, comp2],
                            "reason": known_conflicts[reverse_key],
                            "severity": "high"
                        })
            
            # Verifica conflitos com software já instalado
            installed_software = self._get_installed_software()
            for component in components:
                for software in installed_software:
                    if self._components_conflict(component, software):
                        warnings.append({
                            "component": component,
                            "conflicting_software": software,
                            "reason": f"{component} pode conflitar com {software} já instalado"
                        })
            
            return ConflictResult(
                has_conflicts=len(conflicts) > 0,
                conflicts=conflicts,
                warnings=warnings,
                checked_components=components
            )
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de conflitos: {e}")
            return ConflictResult(
                has_conflicts=False,
                conflicts=[],
                warnings=[f"Erro na detecção: {e}"],
                checked_components=components
            )
    
    def suggest_solutions(self, issues: List[Issue]) -> List[Solution]:
        """
        Gera sugestões de solução automáticas para problemas detectados
        
        Args:
            issues: Lista de problemas detectados
            
        Returns:
            List[Solution]: Lista de soluções sugeridas
        """
        self.logger.info(f"Gerando sugestões para {len(issues)} problemas")
        
        suggestions = []
        
        for issue in issues:
            # Gera sugestões baseadas no tipo e ID do problema
            if issue.category == IssueCategory.DISK_SPACE:
                suggestions.extend(self._generate_disk_space_solutions(issue))
            elif issue.category == IssueCategory.PERMISSIONS:
                suggestions.extend(self._generate_permission_solutions(issue))
            elif issue.category == IssueCategory.CONFLICTS:
                suggestions.extend(self._generate_conflict_solutions(issue))
            elif issue.category == IssueCategory.DEPENDENCIES:
                suggestions.extend(self._generate_dependency_solutions(issue))
            elif issue.category == IssueCategory.SYSTEM:
                suggestions.extend(self._generate_system_solutions(issue))
            else:
                # Solução genérica
                suggestions.append(Solution(
                    issue_id=issue.id,
                    title="Verificação manual necessária",
                    description=f"Problema detectado: {issue.title}",
                    steps=[
                        "Revise os detalhes do problema",
                        "Consulte a documentação",
                        "Entre em contato com o suporte se necessário"
                    ],
                    automatic=False,
                    risk_level="low",
                    estimated_time="5-15 minutos"
                ))
        
        return suggestions
    
    def verify_dependencies(self, component: str) -> 'DependencyResult':
        """
        Verifica dependências de um componente e detecta ciclos
        
        Args:
            component: Nome do componente para verificar
            
        Returns:
            DependencyResult: Resultado da verificação de dependências
        """
        self.logger.info(f"Verificando dependências para: {component}")
        
        try:
            # Simula estrutura de dependências
            # Em uma implementação real, isso consultaria o arquivo components.yaml
            dependencies_map = {
                "CloverBootManager": ["EFITools", "BootloaderUtils"],
                "SteamDeckTools": ["VisualCppRedist", "DotNetFramework"],
                "VMware": ["VirtualizationSupport"],
                "Docker": ["WSL2", "VirtualizationSupport"],
                "EFITools": [],
                "BootloaderUtils": ["EFITools"],
                "VisualCppRedist": [],
                "DotNetFramework": ["VisualCppRedist"],
                "VirtualizationSupport": [],
                "WSL2": ["VirtualizationSupport"]
            }
            
            # Detecta dependências e ciclos
            dependencies = dependencies_map.get(component, [])
            dependency_chain = self._build_dependency_chain(component, dependencies_map)
            has_cycles = self._detect_dependency_cycles(component, dependencies_map)
            
            missing_deps = []
            for dep in dependencies:
                if not self._is_component_available(dep):
                    missing_deps.append(dep)
            
            return DependencyResult(
                component=component,
                dependencies=dependencies,
                dependency_chain=dependency_chain,
                missing_dependencies=missing_deps,
                has_circular_dependencies=has_cycles,
                circular_path=has_cycles[1] if has_cycles[0] else []
            )
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de dependências: {e}")
            return DependencyResult(
                component=component,
                dependencies=[],
                dependency_chain=[],
                missing_dependencies=[],
                has_circular_dependencies=(False, []),
                circular_path=[]
            )
    
    def generate_diagnostic_report(self, result: DiagnosticResult) -> str:
        """
        Gera relatório de diagnóstico estruturado
        
        Args:
            result: Resultado do diagnóstico
            
        Returns:
            str: Relatório formatado
        """
        self.logger.info("Gerando relatório de diagnóstico estruturado")
        
        report_lines = []
        
        # Cabeçalho
        report_lines.append("=" * 60)
        report_lines.append("RELATÓRIO DE DIAGNÓSTICO - ENVIRONMENT DEV")
        report_lines.append("=" * 60)
        report_lines.append(f"Data/Hora: {result.timestamp.strftime('%d/%m/%Y %H:%M:%S')}")
        report_lines.append(f"Duração: {result.diagnostic_duration:.2f}s")
        report_lines.append(f"Status Geral: {result.overall_health.value.upper()}")
        report_lines.append("")
        
        # Informações do Sistema
        report_lines.append("INFORMAÇÕES DO SISTEMA")
        report_lines.append("-" * 30)
        report_lines.append(f"Sistema Operacional: {result.system_info.os_name} {result.system_info.os_version}")
        report_lines.append(f"Arquitetura: {result.system_info.architecture}")
        report_lines.append(f"Processador: {result.system_info.processor}")
        report_lines.append(f"Memória Total: {result.system_info.total_memory / (1024**3):.1f}GB")
        report_lines.append(f"Memória Disponível: {result.system_info.available_memory / (1024**3):.1f}GB")
        report_lines.append(f"Espaço em Disco: {result.system_info.disk_space_free / (1024**3):.1f}GB livres de {result.system_info.disk_space_total / (1024**3):.1f}GB")
        report_lines.append(f"Python: {result.system_info.python_version}")
        report_lines.append(f"Usuário: {result.system_info.username} ({'Admin' if result.system_info.is_admin else 'Padrão'})")
        report_lines.append("")
        
        # Compatibilidade
        report_lines.append("COMPATIBILIDADE")
        report_lines.append("-" * 20)
        report_lines.append(f"Status: {result.compatibility.status.value.upper()}")
        
        if result.compatibility.supported_features:
            report_lines.append("Recursos Suportados:")
            for feature in result.compatibility.supported_features:
                report_lines.append(f"  ✓ {feature}")
        
        if result.compatibility.unsupported_features:
            report_lines.append("Recursos Não Suportados:")
            for feature in result.compatibility.unsupported_features:
                report_lines.append(f"  ✗ {feature}")
        
        if result.compatibility.warnings:
            report_lines.append("Avisos:")
            for warning in result.compatibility.warnings:
                report_lines.append(f"  ⚠ {warning}")
        
        report_lines.append("")
        
        # Problemas Detectados
        if result.issues:
            report_lines.append("PROBLEMAS DETECTADOS")
            report_lines.append("-" * 25)
            
            # Agrupa por severidade
            critical_issues = [i for i in result.issues if i.severity == IssueSeverity.CRITICAL]
            error_issues = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
            warning_issues = [i for i in result.issues if i.severity == IssueSeverity.WARNING]
            info_issues = [i for i in result.issues if i.severity == IssueSeverity.INFO]
            
            for severity_name, issues_list, icon in [
                ("CRÍTICOS", critical_issues, "🔴"),
                ("ERROS", error_issues, "❌"),
                ("AVISOS", warning_issues, "⚠️"),
                ("INFORMAÇÕES", info_issues, "ℹ️")
            ]:
                if issues_list:
                    report_lines.append(f"{severity_name}:")
                    for issue in issues_list:
                        report_lines.append(f"  {icon} {issue.title}")
                        report_lines.append(f"     {issue.description}")
                        if issue.affected_components:
                            report_lines.append(f"     Componentes afetados: {', '.join(issue.affected_components)}")
                    report_lines.append("")
        else:
            report_lines.append("PROBLEMAS DETECTADOS")
            report_lines.append("-" * 25)
            report_lines.append("✅ Nenhum problema detectado!")
            report_lines.append("")
        
        # Sugestões
        if result.suggestions:
            report_lines.append("SUGESTÕES DE SOLUÇÃO")
            report_lines.append("-" * 25)
            for i, suggestion in enumerate(result.suggestions, 1):
                report_lines.append(f"{i}. {suggestion.title}")
                report_lines.append(f"   {suggestion.description}")
                report_lines.append(f"   Automática: {'Sim' if suggestion.automatic else 'Não'}")
                report_lines.append(f"   Risco: {suggestion.risk_level.upper()}")
                report_lines.append(f"   Tempo estimado: {suggestion.estimated_time}")
                if suggestion.steps:
                    report_lines.append("   Passos:")
                    for step in suggestion.steps:
                        report_lines.append(f"     - {step}")
                report_lines.append("")
        
        # Recomendações
        if result.compatibility.recommendations:
            report_lines.append("RECOMENDAÇÕES")
            report_lines.append("-" * 15)
            for rec in result.compatibility.recommendations:
                report_lines.append(f"• {rec}")
            report_lines.append("")
        
        # Rodapé
        report_lines.append("=" * 60)
        report_lines.append("Fim do Relatório")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    # Helper methods for the new functionality
    
    def _get_installed_software(self) -> List[str]:
        """
        Obtém lista de software instalado no sistema
        
        Returns:
            List[str]: Lista de software instalado
        """
        try:
            # Simula detecção de software instalado
            # Em uma implementação real, isso consultaria o registro do Windows
            return ["VMware", "VirtualBox", "Docker", "Hyper-V"]
        except Exception as e:
            self.logger.debug(f"Erro ao obter software instalado: {e}")
            return []
    
    def _components_conflict(self, component: str, software: str) -> bool:
        """
        Verifica se um componente conflita com software instalado
        
        Args:
            component: Nome do componente
            software: Nome do software instalado
            
        Returns:
            bool: True se há conflito
        """
        # Simula lógica de detecção de conflitos
        conflicts = {
            "CloverBootManager": ["rEFInd", "GRUB"],
            "VMware": ["VirtualBox", "Hyper-V"],
            "Docker": ["VMware", "VirtualBox"]
        }
        
        return software in conflicts.get(component, [])
    
    def _build_dependency_chain(self, component: str, dependencies_map: Dict[str, List[str]]) -> List[str]:
        """
        Constrói cadeia completa de dependências
        
        Args:
            component: Componente inicial
            dependencies_map: Mapa de dependências
            
        Returns:
            List[str]: Cadeia de dependências
        """
        chain = []
        visited = set()
        
        def build_chain(comp):
            if comp in visited:
                return
            visited.add(comp)
            chain.append(comp)
            
            for dep in dependencies_map.get(comp, []):
                build_chain(dep)
        
        build_chain(component)
        return chain
    
    def _detect_dependency_cycles(self, component: str, dependencies_map: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """
        Detecta ciclos nas dependências
        
        Args:
            component: Componente inicial
            dependencies_map: Mapa de dependências
            
        Returns:
            Tuple[bool, List[str]]: (tem_ciclo, caminho_do_ciclo)
        """
        visited = set()
        rec_stack = set()
        path = []
        
        def has_cycle(comp):
            if comp in rec_stack:
                # Encontrou ciclo, retorna o caminho
                cycle_start = path.index(comp)
                return True, path[cycle_start:] + [comp]
            
            if comp in visited:
                return False, []
            
            visited.add(comp)
            rec_stack.add(comp)
            path.append(comp)
            
            for dep in dependencies_map.get(comp, []):
                has_cycle_result, cycle_path = has_cycle(dep)
                if has_cycle_result:
                    return True, cycle_path
            
            rec_stack.remove(comp)
            path.pop()
            return False, []
        
        return has_cycle(component)
    
    def _is_component_available(self, component: str) -> bool:
        """
        Verifica se um componente está disponível
        
        Args:
            component: Nome do componente
            
        Returns:
            bool: True se disponível
        """
        # Simula verificação de disponibilidade
        # Em uma implementação real, isso verificaria se o componente existe no sistema
        available_components = [
            "EFITools", "BootloaderUtils", "VisualCppRedist", 
            "DotNetFramework", "VirtualizationSupport", "WSL2"
        ]
        return component in available_components
    
    def _generate_disk_space_solutions(self, issue: Issue) -> List[Solution]:
        """Gera soluções para problemas de espaço em disco"""
        solutions = []
        
        if issue.id == "disk_space_low" or issue.id == "disk_space_critical":
            solutions.append(Solution(
                issue_id=issue.id,
                title="Liberar espaço em disco",
                description="Execute limpeza de disco para liberar espaço",
                steps=[
                    "Execute o Limpeza de Disco do Windows (cleanmgr.exe)",
                    "Remova arquivos temporários",
                    "Esvazie a Lixeira",
                    "Desinstale programas não utilizados",
                    "Mova arquivos grandes para outro local"
                ],
                automatic=False,
                risk_level="low",
                estimated_time="15-30 minutos"
            ))
        
        return solutions
    
    def _generate_permission_solutions(self, issue: Issue) -> List[Solution]:
        """Gera soluções para problemas de permissões"""
        solutions = []
        
        if "admin" in issue.id:
            solutions.append(Solution(
                issue_id=issue.id,
                title="Executar como administrador",
                description="Reinicie o aplicativo com privilégios administrativos",
                steps=[
                    "Feche o aplicativo atual",
                    "Clique com botão direito no ícone do aplicativo",
                    "Selecione 'Executar como administrador'",
                    "Confirme a elevação de privilégios"
                ],
                automatic=True,
                risk_level="low",
                estimated_time="1-2 minutos"
            ))
        
        return solutions
    
    def _generate_conflict_solutions(self, issue: Issue) -> List[Solution]:
        """Gera soluções para problemas de conflitos"""
        solutions = []
        
        if "conflicting_software" in issue.id:
            solutions.append(Solution(
                issue_id=issue.id,
                title="Resolver conflito de software",
                description="Desative ou desinstale o software conflitante temporariamente",
                steps=[
                    "Identifique o software conflitante",
                    "Feche o software se estiver em execução",
                    "Considere desinstalar se não for necessário",
                    "Execute a instalação desejada",
                    "Reinstale o software se necessário"
                ],
                automatic=False,
                risk_level="medium",
                estimated_time="10-20 minutos"
            ))
        
        return solutions
    
    def _generate_dependency_solutions(self, issue: Issue) -> List[Solution]:
        """Gera soluções para problemas de dependências"""
        solutions = []
        
        if "python_version" in issue.id:
            solutions.append(Solution(
                issue_id=issue.id,
                title="Atualizar Python",
                description="Instale uma versão mais recente do Python",
                steps=[
                    "Acesse https://python.org/downloads",
                    "Baixe a versão mais recente do Python",
                    "Execute o instalador",
                    "Marque 'Add Python to PATH'",
                    "Reinicie o sistema após a instalação"
                ],
                automatic=False,
                risk_level="medium",
                estimated_time="15-30 minutos"
            ))
        
        return solutions
    
    def _generate_system_solutions(self, issue: Issue) -> List[Solution]:
        """Gera soluções para problemas de sistema"""
        solutions = []
        
        if "memory_low" in issue.id:
            solutions.append(Solution(
                issue_id=issue.id,
                title="Otimizar uso de memória",
                description="Libere memória RAM fechando aplicações desnecessárias",
                steps=[
                    "Feche navegadores e aplicações não essenciais",
                    "Use o Gerenciador de Tarefas para identificar processos que consomem muita RAM",
                    "Reinicie o sistema se necessário",
                    "Considere adicionar mais RAM ao sistema"
                ],
                automatic=False,
                risk_level="low",
                estimated_time="5-10 minutos"
            ))
        
        return solutions


# Additional data classes for the new functionality

@dataclass
class ConflictResult:
    """Resultado da detecção de conflitos entre componentes"""
    has_conflicts: bool
    conflicts: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    checked_components: List[str]

@dataclass
class DependencyResult:
    """Resultado da verificação de dependências"""
    component: str
    dependencies: List[str]
    dependency_chain: List[str]
    missing_dependencies: List[str]
    has_circular_dependencies: Tuple[bool, List[str]]
    circular_path: List[str]