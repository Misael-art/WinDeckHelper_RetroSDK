#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Repair System - Sistema de Auto-Reparo
Detecta e corrige automaticamente problemas comuns no ambiente de desenvolvimento.
"""

import logging
import os
import sys
import json
import subprocess
import time
import shutil
import winreg
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
from collections import defaultdict
import tempfile
import zipfile
import requests

class RepairType(Enum):
    """Tipos de reparo"""
    FILE_REPAIR = "file_repair"
    REGISTRY_REPAIR = "registry_repair"
    PERMISSION_REPAIR = "permission_repair"
    DEPENDENCY_REPAIR = "dependency_repair"
    CONFIGURATION_REPAIR = "configuration_repair"
    CACHE_REPAIR = "cache_repair"
    NETWORK_REPAIR = "network_repair"
    SERVICE_REPAIR = "service_repair"
    ENVIRONMENT_REPAIR = "environment_repair"
    INSTALLATION_REPAIR = "installation_repair"

class RepairSeverity(Enum):
    """Severidade do reparo"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RepairStatus(Enum):
    """Status do reparo"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    REQUIRES_MANUAL = "requires_manual"

@dataclass
class RepairAction:
    """Ação de reparo"""
    action_id: str
    name: str
    description: str
    repair_type: RepairType
    severity: RepairSeverity
    auto_executable: bool = True
    requires_admin: bool = False
    backup_required: bool = True
    estimated_time: int = 30  # segundos
    dependencies: List[str] = field(default_factory=list)
    repair_function: Optional[Callable] = None
    validation_function: Optional[Callable] = None
    rollback_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RepairResult:
    """Resultado de reparo"""
    action_id: str
    status: RepairStatus
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    backup_path: Optional[str] = None
    rollback_available: bool = False

@dataclass
class RepairSession:
    """Sessão de reparo"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    skipped_actions: int = 0
    results: List[RepairResult] = field(default_factory=list)
    backup_directory: Optional[str] = None

class AutoRepairSystem:
    """Sistema de auto-reparo"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger("auto_repair")
        self.config_dir = config_dir or Path.cwd() / "config"
        
        # Ações de reparo registradas
        self.repair_actions: Dict[str, RepairAction] = {}
        self.repair_categories: Dict[RepairType, List[str]] = defaultdict(list)
        
        # Histórico de reparos
        self.repair_history: List[RepairSession] = []
        self.max_history_size = 100
        
        # Configurações
        self.max_repair_attempts = 3
        self.backup_before_repair = True
        self.auto_repair_enabled = True
        self.require_confirmation = False
        self.repair_timeout = 300  # 5 minutos
        
        # Diretórios
        self.backup_dir = Path.cwd() / "backups" / "auto_repair"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Lock para thread safety
        self.lock = threading.RLock()
        
        # Registrar ações padrão
        self.register_default_repair_actions()
        
        # Carregar configurações
        self.load_configuration()
    
    def register_default_repair_actions(self):
        """Registra ações de reparo padrão"""
        # Reparo de arquivos corrompidos
        self.register_repair_action(RepairAction(
            action_id="fix_corrupted_files",
            name="Reparar Arquivos Corrompidos",
            description="Detecta e repara arquivos corrompidos ou com checksums inválidos",
            repair_type=RepairType.FILE_REPAIR,
            severity=RepairSeverity.HIGH,
            repair_function=self._repair_corrupted_files,
            validation_function=self._validate_file_integrity
        ))
        
        # Limpeza de cache
        self.register_repair_action(RepairAction(
            action_id="clear_corrupted_cache",
            name="Limpar Cache Corrompido",
            description="Remove arquivos de cache corrompidos ou expirados",
            repair_type=RepairType.CACHE_REPAIR,
            severity=RepairSeverity.MEDIUM,
            backup_required=False,
            repair_function=self._clear_corrupted_cache
        ))
        
        # Reparo de permissões
        self.register_repair_action(RepairAction(
            action_id="fix_file_permissions",
            name="Corrigir Permissões de Arquivos",
            description="Corrige permissões de arquivos e diretórios importantes",
            repair_type=RepairType.PERMISSION_REPAIR,
            severity=RepairSeverity.MEDIUM,
            requires_admin=True,
            repair_function=self._fix_file_permissions
        ))
        
        # Reparo de variáveis de ambiente
        self.register_repair_action(RepairAction(
            action_id="fix_environment_variables",
            name="Corrigir Variáveis de Ambiente",
            description="Corrige variáveis de ambiente corrompidas ou ausentes",
            repair_type=RepairType.ENVIRONMENT_REPAIR,
            severity=RepairSeverity.MEDIUM,
            repair_function=self._fix_environment_variables
        ))
        
        # Reparo de dependências
        self.register_repair_action(RepairAction(
            action_id="reinstall_missing_dependencies",
            name="Reinstalar Dependências Ausentes",
            description="Detecta e reinstala dependências ausentes ou corrompidas",
            repair_type=RepairType.DEPENDENCY_REPAIR,
            severity=RepairSeverity.HIGH,
            estimated_time=120,
            repair_function=self._reinstall_missing_dependencies
        ))
        
        # Limpeza de arquivos temporários
        self.register_repair_action(RepairAction(
            action_id="cleanup_temp_files",
            name="Limpeza de Arquivos Temporários",
            description="Remove arquivos temporários acumulados",
            repair_type=RepairType.FILE_REPAIR,
            severity=RepairSeverity.LOW,
            backup_required=False,
            repair_function=self._cleanup_temp_files
        ))
        
        # Reparo de registro
        self.register_repair_action(RepairAction(
            action_id="fix_registry_entries",
            name="Corrigir Entradas do Registro",
            description="Corrige entradas corrompidas ou ausentes no registro",
            repair_type=RepairType.REGISTRY_REPAIR,
            severity=RepairSeverity.HIGH,
            requires_admin=True,
            repair_function=self._fix_registry_entries
        ))
        
        # Reparo de configurações
        self.register_repair_action(RepairAction(
            action_id="restore_default_configs",
            name="Restaurar Configurações Padrão",
            description="Restaura configurações padrão para componentes com configuração corrompida",
            repair_type=RepairType.CONFIGURATION_REPAIR,
            severity=RepairSeverity.MEDIUM,
            repair_function=self._restore_default_configs
        ))
        
        # Reparo de conectividade
        self.register_repair_action(RepairAction(
            action_id="fix_network_connectivity",
            name="Corrigir Conectividade de Rede",
            description="Diagnostica e corrige problemas de conectividade de rede",
            repair_type=RepairType.NETWORK_REPAIR,
            severity=RepairSeverity.MEDIUM,
            repair_function=self._fix_network_connectivity
        ))
        
        # Reparo de instalações
        self.register_repair_action(RepairAction(
            action_id="repair_broken_installations",
            name="Reparar Instalações Quebradas",
            description="Detecta e repara instalações de software quebradas",
            repair_type=RepairType.INSTALLATION_REPAIR,
            severity=RepairSeverity.HIGH,
            estimated_time=180,
            repair_function=self._repair_broken_installations
        ))
    
    def register_repair_action(self, action: RepairAction):
        """Registra uma ação de reparo"""
        with self.lock:
            self.repair_actions[action.action_id] = action
            self.repair_categories[action.repair_type].append(action.action_id)
            self.logger.info(f"Ação de reparo registrada: {action.name}")
    
    def unregister_repair_action(self, action_id: str):
        """Remove uma ação de reparo"""
        with self.lock:
            if action_id in self.repair_actions:
                action = self.repair_actions[action_id]
                del self.repair_actions[action_id]
                self.repair_categories[action.repair_type].remove(action_id)
                self.logger.info(f"Ação de reparo removida: {action.name}")
    
    def diagnose_problems(self) -> List[str]:
        """Diagnostica problemas que podem ser reparados"""
        problems = []
        
        for action_id, action in self.repair_actions.items():
            if action.validation_function:
                try:
                    if not action.validation_function():
                        problems.append(action_id)
                except Exception as e:
                    self.logger.warning(f"Erro na validação de {action_id}: {e}")
        
        return problems
    
    def auto_repair(self, problem_types: Optional[List[RepairType]] = None,
                   max_severity: RepairSeverity = RepairSeverity.HIGH) -> RepairSession:
        """Executa reparo automático"""
        session_id = f"repair_{int(time.time())}"
        session = RepairSession(
            session_id=session_id,
            start_time=time.time(),
            backup_directory=str(self.backup_dir / session_id) if self.backup_before_repair else None
        )
        
        if session.backup_directory:
            Path(session.backup_directory).mkdir(parents=True, exist_ok=True)
        
        try:
            # Diagnosticar problemas
            problems = self.diagnose_problems()
            
            # Filtrar por tipo se especificado
            if problem_types:
                problems = [p for p in problems if self.repair_actions[p].repair_type in problem_types]
            
            # Filtrar por severidade
            severity_order = [RepairSeverity.LOW, RepairSeverity.MEDIUM, RepairSeverity.HIGH, RepairSeverity.CRITICAL]
            max_severity_index = severity_order.index(max_severity)
            problems = [p for p in problems if severity_order.index(self.repair_actions[p].severity) <= max_severity_index]
            
            # Ordenar por severidade (crítico primeiro)
            problems.sort(key=lambda p: severity_order.index(self.repair_actions[p].severity), reverse=True)
            
            session.total_actions = len(problems)
            
            self.logger.info(f"Iniciando reparo automático: {len(problems)} problemas detectados")
            
            # Executar reparos
            for problem_id in problems:
                result = self.execute_repair(problem_id, session)
                session.results.append(result)
                
                if result.success:
                    session.successful_actions += 1
                elif result.status == RepairStatus.SKIPPED:
                    session.skipped_actions += 1
                else:
                    session.failed_actions += 1
        
        except Exception as e:
            self.logger.error(f"Erro durante reparo automático: {e}")
        
        finally:
            session.end_time = time.time()
            self.repair_history.append(session)
            
            # Limitar histórico
            if len(self.repair_history) > self.max_history_size:
                self.repair_history.pop(0)
        
        self.logger.info(f"Reparo automático concluído: {session.successful_actions}/{session.total_actions} sucessos")
        
        return session
    
    def execute_repair(self, action_id: str, session: Optional[RepairSession] = None) -> RepairResult:
        """Executa uma ação de reparo específica"""
        if action_id not in self.repair_actions:
            return RepairResult(
                action_id=action_id,
                status=RepairStatus.FAILED,
                success=False,
                message="Ação de reparo não encontrada"
            )
        
        action = self.repair_actions[action_id]
        start_time = time.time()
        
        result = RepairResult(
            action_id=action_id,
            status=RepairStatus.IN_PROGRESS,
            success=False,
            message="Executando reparo..."
        )
        
        try:
            self.logger.info(f"Executando reparo: {action.name}")
            
            # Verificar se requer confirmação
            if self.require_confirmation and not self._get_user_confirmation(action):
                result.status = RepairStatus.SKIPPED
                result.message = "Reparo cancelado pelo usuário"
                return result
            
            # Verificar se requer privilégios administrativos
            if action.requires_admin and not self._is_admin():
                result.status = RepairStatus.REQUIRES_MANUAL
                result.message = "Requer privilégios administrativos"
                return result
            
            # Criar backup se necessário
            if action.backup_required and self.backup_before_repair and session:
                backup_path = self._create_backup(action, session.backup_directory)
                result.backup_path = backup_path
                result.rollback_available = backup_path is not None
            
            # Executar função de reparo
            if action.repair_function:
                repair_success, repair_message, repair_details = action.repair_function()
                
                if repair_success:
                    result.status = RepairStatus.SUCCESS
                    result.success = True
                    result.message = repair_message or "Reparo executado com sucesso"
                    result.details = repair_details or {}
                else:
                    result.status = RepairStatus.FAILED
                    result.message = repair_message or "Falha na execução do reparo"
                    result.details = repair_details or {}
            else:
                result.status = RepairStatus.FAILED
                result.message = "Função de reparo não definida"
        
        except Exception as e:
            result.status = RepairStatus.FAILED
            result.message = f"Erro durante execução: {str(e)}"
            self.logger.error(f"Erro ao executar reparo {action_id}: {e}")
        
        finally:
            result.execution_time = time.time() - start_time
        
        return result
    
    def rollback_repair(self, session_id: str, action_id: str) -> bool:
        """Desfaz um reparo específico"""
        # Encontrar sessão
        session = None
        for s in self.repair_history:
            if s.session_id == session_id:
                session = s
                break
        
        if not session:
            self.logger.error(f"Sessão não encontrada: {session_id}")
            return False
        
        # Encontrar resultado do reparo
        repair_result = None
        for result in session.results:
            if result.action_id == action_id:
                repair_result = result
                break
        
        if not repair_result or not repair_result.rollback_available:
            self.logger.error(f"Rollback não disponível para {action_id}")
            return False
        
        try:
            action = self.repair_actions.get(action_id)
            if action and action.rollback_function:
                return action.rollback_function(repair_result.backup_path)
            else:
                # Rollback padrão: restaurar backup
                return self._restore_backup(repair_result.backup_path)
        
        except Exception as e:
            self.logger.error(f"Erro durante rollback: {e}")
            return False
    
    def get_repair_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de reparo"""
        problems = self.diagnose_problems()
        recommendations = []
        
        for problem_id in problems:
            action = self.repair_actions[problem_id]
            recommendations.append({
                'action_id': problem_id,
                'name': action.name,
                'description': action.description,
                'severity': action.severity.value,
                'auto_executable': action.auto_executable,
                'requires_admin': action.requires_admin,
                'estimated_time': action.estimated_time
            })
        
        # Ordenar por severidade
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
        
        return recommendations
    
    def generate_repair_report(self, session: RepairSession) -> Dict[str, Any]:
        """Gera relatório de reparo"""
        total_time = (session.end_time or time.time()) - session.start_time
        
        return {
            'session_id': session.session_id,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'total_time': total_time,
            'summary': {
                'total_actions': session.total_actions,
                'successful_actions': session.successful_actions,
                'failed_actions': session.failed_actions,
                'skipped_actions': session.skipped_actions,
                'success_rate': session.successful_actions / session.total_actions if session.total_actions > 0 else 0
            },
            'results': [
                {
                    'action_id': result.action_id,
                    'action_name': self.repair_actions.get(result.action_id, RepairAction("", "", "", RepairType.FILE_REPAIR, RepairSeverity.LOW)).name,
                    'status': result.status.value,
                    'success': result.success,
                    'message': result.message,
                    'execution_time': result.execution_time,
                    'rollback_available': result.rollback_available
                } for result in session.results
            ],
            'backup_directory': session.backup_directory
        }
    
    # Funções de reparo específicas
    
    def _repair_corrupted_files(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Repara arquivos corrompidos"""
        try:
            repaired_files = []
            
            # Verificar arquivos importantes
            important_files = [
                Path.cwd() / "components.yaml",
                Path.cwd() / "config" / "constants.py"
            ]
            
            for file_path in important_files:
                if file_path.exists():
                    # Verificar integridade (implementação básica)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Se conseguiu ler, arquivo provavelmente está OK
                        # Aqui poderia ter verificações mais sofisticadas
                        
                    except Exception:
                        # Tentar reparar ou restaurar backup
                        backup_file = file_path.with_suffix(file_path.suffix + '.backup')
                        if backup_file.exists():
                            shutil.copy2(backup_file, file_path)
                            repaired_files.append(str(file_path))
            
            return True, f"Reparados {len(repaired_files)} arquivos", {'repaired_files': repaired_files}
        
        except Exception as e:
            return False, f"Erro ao reparar arquivos: {e}", {}
    
    def _validate_file_integrity(self) -> bool:
        """Valida integridade de arquivos importantes"""
        try:
            important_files = [
                Path.cwd() / "components.yaml",
                Path.cwd() / "config" / "constants.py"
            ]
            
            for file_path in important_files:
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            f.read()
                    except Exception:
                        return False
            
            return True
        
        except Exception:
            return False
    
    def _clear_corrupted_cache(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Limpa cache corrompido"""
        try:
            cache_dirs = [
                Path.cwd() / "cache",
                Path.cwd() / ".cache",
                Path(os.environ.get('TEMP', '')) / "env_dev_cache"
            ]
            
            cleared_size = 0
            cleared_files = 0
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    for file_path in cache_dir.rglob('*'):
                        if file_path.is_file():
                            try:
                                size = file_path.stat().st_size
                                file_path.unlink()
                                cleared_size += size
                                cleared_files += 1
                            except Exception:
                                continue
            
            return True, f"Cache limpo: {cleared_files} arquivos, {cleared_size / 1024 / 1024:.1f} MB", {
                'cleared_files': cleared_files,
                'cleared_size_mb': cleared_size / 1024 / 1024
            }
        
        except Exception as e:
            return False, f"Erro ao limpar cache: {e}", {}
    
    def _fix_file_permissions(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Corrige permissões de arquivos"""
        try:
            if os.name != 'nt':
                return False, "Reparo de permissões não implementado para este SO", {}
            
            # No Windows, verificar se temos acesso de escrita aos diretórios importantes
            important_dirs = [
                Path.cwd(),
                Path.cwd() / "config",
                Path.cwd() / "logs"
            ]
            
            fixed_dirs = []
            
            for dir_path in important_dirs:
                if dir_path.exists():
                    # Tentar criar arquivo de teste
                    test_file = dir_path / "test_permissions.tmp"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                    except Exception:
                        # Tentar corrigir permissões (implementação básica)
                        try:
                            os.chmod(dir_path, 0o755)
                            fixed_dirs.append(str(dir_path))
                        except Exception:
                            continue
            
            return True, f"Permissões corrigidas para {len(fixed_dirs)} diretórios", {
                'fixed_directories': fixed_dirs
            }
        
        except Exception as e:
            return False, f"Erro ao corrigir permissões: {e}", {}
    
    def _fix_environment_variables(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Corrige variáveis de ambiente"""
        try:
            fixed_vars = []
            
            # Verificar PATH
            path_var = os.environ.get('PATH', '')
            if path_var:
                # Remover duplicatas
                path_entries = path_var.split(os.pathsep)
                unique_entries = []
                seen = set()
                
                for entry in path_entries:
                    if entry and entry not in seen:
                        unique_entries.append(entry)
                        seen.add(entry)
                
                if len(unique_entries) < len(path_entries):
                    new_path = os.pathsep.join(unique_entries)
                    os.environ['PATH'] = new_path
                    fixed_vars.append('PATH')
            
            # Verificar outras variáveis importantes
            required_vars = {
                'TEMP': tempfile.gettempdir(),
                'TMP': tempfile.gettempdir()
            }
            
            for var_name, default_value in required_vars.items():
                if not os.environ.get(var_name):
                    os.environ[var_name] = default_value
                    fixed_vars.append(var_name)
            
            return True, f"Variáveis de ambiente corrigidas: {', '.join(fixed_vars)}", {
                'fixed_variables': fixed_vars
            }
        
        except Exception as e:
            return False, f"Erro ao corrigir variáveis de ambiente: {e}", {}
    
    def _reinstall_missing_dependencies(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Reinstala dependências ausentes"""
        try:
            # Verificar dependências Python
            missing_deps = []
            required_deps = ['pyyaml', 'requests', 'psutil']
            
            for dep in required_deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)
            
            installed_deps = []
            
            if missing_deps:
                for dep in missing_deps:
                    try:
                        result = subprocess.run(
                            [sys.executable, '-m', 'pip', 'install', dep],
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if result.returncode == 0:
                            installed_deps.append(dep)
                    
                    except Exception:
                        continue
            
            return True, f"Dependências reinstaladas: {', '.join(installed_deps)}", {
                'installed_dependencies': installed_deps,
                'missing_dependencies': [d for d in missing_deps if d not in installed_deps]
            }
        
        except Exception as e:
            return False, f"Erro ao reinstalar dependências: {e}", {}
    
    def _cleanup_temp_files(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Limpa arquivos temporários"""
        try:
            temp_dirs = [
                Path(tempfile.gettempdir()),
                Path.cwd() / "temp",
                Path.cwd() / "tmp"
            ]
            
            cleaned_size = 0
            cleaned_files = 0
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    # Limpar apenas arquivos antigos (mais de 1 dia)
                    cutoff_time = time.time() - 86400  # 24 horas
                    
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            try:
                                if file_path.stat().st_mtime < cutoff_time:
                                    size = file_path.stat().st_size
                                    file_path.unlink()
                                    cleaned_size += size
                                    cleaned_files += 1
                            except Exception:
                                continue
            
            return True, f"Arquivos temporários limpos: {cleaned_files} arquivos, {cleaned_size / 1024 / 1024:.1f} MB", {
                'cleaned_files': cleaned_files,
                'cleaned_size_mb': cleaned_size / 1024 / 1024
            }
        
        except Exception as e:
            return False, f"Erro ao limpar arquivos temporários: {e}", {}
    
    def _fix_registry_entries(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Corrige entradas do registro"""
        try:
            if os.name != 'nt':
                return False, "Reparo de registro não aplicável neste SO", {}
            
            fixed_entries = []
            
            # Verificar entradas importantes (implementação básica)
            # Aqui seria implementada a lógica específica de reparo do registro
            
            return True, f"Entradas do registro corrigidas: {len(fixed_entries)}", {
                'fixed_entries': fixed_entries
            }
        
        except Exception as e:
            return False, f"Erro ao corrigir registro: {e}", {}
    
    def _restore_default_configs(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Restaura configurações padrão"""
        try:
            restored_configs = []
            
            # Verificar arquivos de configuração importantes
            config_files = [
                Path.cwd() / "config" / "detection_engine.yaml",
                Path.cwd() / "config" / "compatibility_matrix.yaml"
            ]
            
            for config_file in config_files:
                if not config_file.exists() or config_file.stat().st_size == 0:
                    # Criar configuração padrão
                    config_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    default_config = {
                        'enabled': True,
                        'version': '1.0',
                        'created_by': 'auto_repair_system'
                    }
                    
                    with open(config_file, 'w') as f:
                        import yaml
                        yaml.dump(default_config, f)
                    
                    restored_configs.append(str(config_file))
            
            return True, f"Configurações restauradas: {len(restored_configs)}", {
                'restored_configs': restored_configs
            }
        
        except Exception as e:
            return False, f"Erro ao restaurar configurações: {e}", {}
    
    def _fix_network_connectivity(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Corrige problemas de conectividade"""
        try:
            # Testar conectividade básica
            test_urls = ['https://www.google.com', 'https://github.com']
            connectivity_issues = []
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        connectivity_issues.append(url)
                except Exception:
                    connectivity_issues.append(url)
            
            if connectivity_issues:
                # Tentar flush DNS
                try:
                    subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
                except Exception:
                    pass
            
            return True, f"Verificação de conectividade concluída", {
                'connectivity_issues': connectivity_issues
            }
        
        except Exception as e:
            return False, f"Erro ao verificar conectividade: {e}", {}
    
    def _repair_broken_installations(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Repara instalações quebradas"""
        try:
            from .main_controller import verify_component, install_component
            repaired_installations = []
            
            # Lista de componentes críticos para verificar
            critical_components = [
                "Visual Studio Code",
                "SGDK (Sega Genesis Development Kit)",
                "Java Runtime Environment",
                "Make"
            ]
            
            for component in critical_components:
                try:
                    # Verifica se o componente está instalado
                    if not verify_component(component):
                        self.logger.info(f"Tentando reparar instalação de: {component}")
                        
                        # Tenta reinstalar o componente
                        install_result = install_component(component)
                        if install_result:
                            repaired_installations.append(component)
                            self.logger.info(f"Componente {component} reparado com sucesso")
                        else:
                            self.logger.warning(f"Falha ao reparar {component}")
                            
                except Exception as e:
                    self.logger.error(f"Erro ao verificar/reparar {component}: {e}")
            
            return True, f"Instalações reparadas: {len(repaired_installations)}", {
                'repaired_installations': repaired_installations
            }
        
        except Exception as e:
            return False, f"Erro ao reparar instalações: {e}", {}
    
    # Funções auxiliares
    
    def _create_backup(self, action: RepairAction, backup_dir: str) -> Optional[str]:
        """Cria backup antes do reparo"""
        try:
            backup_path = Path(backup_dir) / f"{action.action_id}_{int(time.time())}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Implementar lógica de backup específica baseada no tipo de reparo
            # Por enquanto, apenas criar o diretório
            
            return str(backup_path)
        
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def _restore_backup(self, backup_path: str) -> bool:
        """Restaura backup"""
        try:
            # Implementar lógica de restauração
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            return False
    
    def _get_user_confirmation(self, action: RepairAction) -> bool:
        """Obtém confirmação do usuário"""
        # Por enquanto, sempre retorna True
        # Em uma implementação real, mostraria dialog ou prompt
        return True
    
    def _is_admin(self) -> bool:
        """Verifica se tem privilégios administrativos"""
        try:
            if os.name == 'nt':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    def load_configuration(self):
        """Carrega configurações do sistema"""
        config_file = self.config_dir / "auto_repair.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.max_repair_attempts = config.get('max_repair_attempts', self.max_repair_attempts)
                self.backup_before_repair = config.get('backup_before_repair', self.backup_before_repair)
                self.auto_repair_enabled = config.get('auto_repair_enabled', self.auto_repair_enabled)
                self.require_confirmation = config.get('require_confirmation', self.require_confirmation)
                self.repair_timeout = config.get('repair_timeout', self.repair_timeout)
                
                self.logger.info("Configuração do auto-reparo carregada")
            
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configuração: {e}")

# Instância global
_auto_repair_system: Optional[AutoRepairSystem] = None

def get_auto_repair_system() -> AutoRepairSystem:
    """Obtém instância global do sistema de auto-reparo"""
    global _auto_repair_system
    if _auto_repair_system is None:
        _auto_repair_system = AutoRepairSystem()
    return _auto_repair_system