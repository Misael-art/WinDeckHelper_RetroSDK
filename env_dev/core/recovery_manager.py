# -*- coding: utf-8 -*-
"""
Recovery Manager para Environment Dev Script
Módulo responsável por recuperação automática e manutenção do sistema
"""

import os
import sys
import shutil
import logging
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from env_dev.core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory, handle_error, create_error_context
from env_dev.core.diagnostic_manager import DiagnosticManager, Issue, DiagnosticResult, HealthStatus
from env_dev.utils.efi_backup import create_efi_backup, restore_efi_backup, list_efi_backups
from env_dev.utils.disk_space import get_disk_space, format_size
from env_dev.utils.permission_checker import is_admin, check_write_permission

logger = logging.getLogger(__name__)

class RecoveryStatus(Enum):
    """Status das operações de recuperação"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"

class RepairType(Enum):
    """Tipos de reparo disponíveis"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    INTERACTIVE = "interactive"

class BackupType(Enum):
    """Tipos de backup"""
    CONFIGURATION = "configuration"
    EFI_PARTITION = "efi_partition"
    COMPONENT_STATE = "component_state"
    SYSTEM_STATE = "system_state"
    FULL_SYSTEM = "full_system"

@dataclass
class RepairAction:
    """Representa uma ação de reparo"""
    id: str
    title: str
    description: str
    repair_type: RepairType
    target_issue: str
    command: Optional[str] = None
    script_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high
    estimated_time: str = "unknown"
    requires_admin: bool = False
    backup_required: bool = True

@dataclass
class RepairResult:
    """Resultado de uma operação de reparo"""
    action_id: str
    status: RecoveryStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    backup_created: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0

@dataclass
class BackupInfo:
    """Informações sobre um backup"""
    id: str
    name: str
    backup_type: BackupType
    path: str
    size: int
    created_at: datetime
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True

@dataclass
class RestoreResult:
    """Resultado de uma operação de restauração"""
    backup_id: str
    status: RecoveryStatus
    message: str
    restored_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0

@dataclass
class InconsistencyResult:
    """Resultado da detecção de inconsistências"""
    inconsistencies_found: int
    inconsistencies_fixed: int
    issues: List[Dict[str, Any]] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class RecoveryManager:
    """
    Gerenciador de recuperação automática do sistema.
    
    Responsável por:
    - Reparo automático de problemas detectados
    - Restauração confiável de backups
    - Detecção e correção de inconsistências
    - Manutenção preventiva do sistema
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa o RecoveryManager.
        
        Args:
            base_path: Caminho base do projeto (padrão: diretório atual)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.backups_dir = self.base_path / "backups"
        self.recovery_logs_dir = self.base_path / "logs" / "recovery"
        self.temp_dir = self.base_path / "temp" / "recovery"
        
        # Inicializar diretórios
        self._ensure_directories()
        
        # Componentes auxiliares
        self.diagnostic_manager = DiagnosticManager()
        
        # Configurações
        self.max_backup_age_days = 30
        self.max_repair_attempts = 3
        self.backup_retention_count = 10
        
        logger.info(f"RecoveryManager inicializado com base_path: {self.base_path}")
    
    def _ensure_directories(self):
        """Garante que os diretórios necessários existam"""
        directories = [
            self.backups_dir,
            self.recovery_logs_dir,
            self.temp_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Erro ao criar diretório {directory}: {e}")
    
    def auto_repair_issues(self, issues: List[Issue]) -> List[RepairResult]:
        """
        Executa reparo automático dos problemas detectados.
        
        Args:
            issues: Lista de problemas para reparar
            
        Returns:
            List[RepairResult]: Lista de resultados dos reparos
        """
        logger.info(f"Iniciando reparo automático de {len(issues)} problemas")
        results = []
        
        try:
            # Agrupar problemas por prioridade
            critical_issues = [i for i in issues if i.severity.value == "critical"]
            error_issues = [i for i in issues if i.severity.value == "error"]
            warning_issues = [i for i in issues if i.severity.value == "warning"]
            
            # Processar problemas por ordem de prioridade
            all_issues = critical_issues + error_issues + warning_issues
            
            for issue in all_issues:
                try:
                    repair_actions = self._get_repair_actions_for_issue(issue)
                    
                    for action in repair_actions:
                        if action.repair_type == RepairType.AUTOMATIC:
                            result = self._execute_repair_action(action, issue)
                            results.append(result)
                            
                            # Se o reparo foi bem-sucedido, não tentar outras ações para este problema
                            if result.status == RecoveryStatus.COMPLETED:
                                break
                                
                except Exception as e:
                    error_result = RepairResult(
                        action_id=f"repair_{issue.id}",
                        status=RecoveryStatus.FAILED,
                        message=f"Erro ao reparar problema {issue.id}: {str(e)}",
                        errors=[str(e)]
                    )
                    results.append(error_result)
                    logger.error(f"Erro ao reparar problema {issue.id}: {e}")
            
            # Log do resumo
            successful_repairs = len([r for r in results if r.status == RecoveryStatus.COMPLETED])
            failed_repairs = len([r for r in results if r.status == RecoveryStatus.FAILED])
            
            logger.info(f"Reparo automático concluído: {successful_repairs} sucessos, {failed_repairs} falhas")
            
        except Exception as e:
            logger.error(f"Erro durante reparo automático: {e}")
            error_result = RepairResult(
                action_id="auto_repair_general",
                status=RecoveryStatus.FAILED,
                message=f"Erro geral durante reparo automático: {str(e)}",
                errors=[str(e)]
            )
            results.append(error_result)
        
        return results    
    
    def restore_from_backup(self, backup_id: str) -> RestoreResult:
        """
        Restaura o sistema a partir de um backup específico.
        
        Args:
            backup_id: ID do backup para restaurar
            
        Returns:
            RestoreResult: Resultado da operação de restauração
        """
        logger.info(f"Iniciando restauração do backup: {backup_id}")
        start_time = time.time()
        
        try:
            # Buscar informações do backup
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return RestoreResult(
                    backup_id=backup_id,
                    status=RecoveryStatus.FAILED,
                    message=f"Backup {backup_id} não encontrado",
                    errors=[f"Backup {backup_id} não encontrado"]
                )
            
            # Verificar se o backup é válido
            if not backup_info.is_valid:
                return RestoreResult(
                    backup_id=backup_id,
                    status=RecoveryStatus.FAILED,
                    message=f"Backup {backup_id} está corrompido ou inválido",
                    errors=[f"Backup {backup_id} está corrompido ou inválido"]
                )
            
            # Criar backup do estado atual antes da restauração
            current_backup_id = self._create_pre_restore_backup()
            
            result = RestoreResult(
                backup_id=backup_id,
                status=RecoveryStatus.IN_PROGRESS,
                message=f"Restaurando backup {backup_info.name}..."
            )
            
            # Executar restauração baseada no tipo de backup
            if backup_info.backup_type == BackupType.EFI_PARTITION:
                success = self._restore_efi_backup(backup_info, result)
            elif backup_info.backup_type == BackupType.CONFIGURATION:
                success = self._restore_configuration_backup(backup_info, result)
            elif backup_info.backup_type == BackupType.COMPONENT_STATE:
                success = self._restore_component_state_backup(backup_info, result)
            elif backup_info.backup_type == BackupType.SYSTEM_STATE:
                success = self._restore_system_state_backup(backup_info, result)
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Tipo de backup não suportado: {backup_info.backup_type.value}"
                result.errors.append(f"Tipo de backup não suportado: {backup_info.backup_type.value}")
                success = False
            
            # Atualizar resultado final
            if success:
                result.status = RecoveryStatus.COMPLETED
                result.message = f"Backup {backup_info.name} restaurado com sucesso"
                logger.info(f"Backup {backup_id} restaurado com sucesso")
            else:
                result.status = RecoveryStatus.FAILED
                if not result.message.startswith("Falha"):
                    result.message = f"Falha ao restaurar backup {backup_info.name}"
                logger.error(f"Falha ao restaurar backup {backup_id}")
            
            result.duration = time.time() - start_time
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Erro durante restauração do backup {backup_id}: {str(e)}"
            logger.error(error_msg)
            
            return RestoreResult(
                backup_id=backup_id,
                status=RecoveryStatus.FAILED,
                message=error_msg,
                errors=[str(e)],
                duration=duration
            )
    
    def detect_and_fix_inconsistencies(self) -> InconsistencyResult:
        """
        Detecta e corrige inconsistências no sistema.
        
        Returns:
            InconsistencyResult: Resultado da detecção e correção
        """
        logger.info("Iniciando detecção de inconsistências do sistema")
        
        result = InconsistencyResult(
            inconsistencies_found=0,
            inconsistencies_fixed=0
        )
        
        try:
            # Verificar inconsistências em diferentes áreas
            checks = [
                ("Arquivos de configuração", self._check_configuration_consistency),
                ("Estado dos componentes", self._check_component_state_consistency),
                ("Integridade de backups", self._check_backup_integrity),
                ("Estrutura de diretórios", self._check_directory_structure),
                ("Permissões de arquivos", self._check_file_permissions),
                ("Variáveis de ambiente", self._check_environment_variables)
            ]
            
            for check_name, check_function in checks:
                try:
                    logger.debug(f"Executando verificação: {check_name}")
                    inconsistencies = check_function()
                    
                    for inconsistency in inconsistencies:
                        result.inconsistencies_found += 1
                        result.issues.append({
                            'category': check_name,
                            'issue': inconsistency['issue'],
                            'severity': inconsistency.get('severity', 'warning'),
                            'fix_attempted': False,
                            'fix_successful': False
                        })
                        
                        # Tentar corrigir automaticamente se possível
                        if inconsistency.get('auto_fix'):
                            try:
                                fix_result = inconsistency['auto_fix']()
                                if fix_result:
                                    result.inconsistencies_fixed += 1
                                    result.fixes_applied.append(f"{check_name}: {inconsistency['issue']}")
                                    result.issues[-1]['fix_attempted'] = True
                                    result.issues[-1]['fix_successful'] = True
                                    logger.info(f"Inconsistência corrigida: {inconsistency['issue']}")
                                else:
                                    result.issues[-1]['fix_attempted'] = True
                                    result.warnings.append(f"Falha ao corrigir: {inconsistency['issue']}")
                            except Exception as fix_error:
                                result.issues[-1]['fix_attempted'] = True
                                result.errors.append(f"Erro ao corrigir {inconsistency['issue']}: {str(fix_error)}")
                                logger.error(f"Erro ao corrigir inconsistência: {fix_error}")
                
                except Exception as e:
                    result.errors.append(f"Erro na verificação {check_name}: {str(e)}")
                    logger.error(f"Erro na verificação {check_name}: {e}")
            
            # Log do resumo
            logger.info(f"Detecção de inconsistências concluída: "
                       f"{result.inconsistencies_found} encontradas, "
                       f"{result.inconsistencies_fixed} corrigidas")
            
        except Exception as e:
            result.errors.append(f"Erro geral na detecção de inconsistências: {str(e)}")
            logger.error(f"Erro geral na detecção de inconsistências: {e}")
        
        return result
    
    def create_system_backup(self, backup_type: BackupType, name: Optional[str] = None) -> Optional[BackupInfo]:
        """
        Cria um backup do sistema.
        
        Args:
            backup_type: Tipo de backup a ser criado
            name: Nome opcional para o backup
            
        Returns:
            BackupInfo: Informações do backup criado ou None se falhar
        """
        logger.info(f"Criando backup do tipo: {backup_type.value}")
        
        try:
            # Gerar nome do backup se não fornecido
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"{backup_type.value}_{timestamp}"
            
            backup_id = f"backup_{int(time.time())}"
            backup_path = self.backups_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Executar backup baseado no tipo
            success = False
            metadata = {
                'created_at': datetime.now().isoformat(),
                'backup_type': backup_type.value,
                'name': name,
                'version': '1.0'
            }
            
            if backup_type == BackupType.EFI_PARTITION:
                success = self._create_efi_backup(backup_path, metadata)
            elif backup_type == BackupType.CONFIGURATION:
                success = self._create_configuration_backup(backup_path, metadata)
            elif backup_type == BackupType.COMPONENT_STATE:
                success = self._create_component_state_backup(backup_path, metadata)
            elif backup_type == BackupType.SYSTEM_STATE:
                success = self._create_system_state_backup(backup_path, metadata)
            else:
                logger.error(f"Tipo de backup não suportado: {backup_type.value}")
                return None
            
            if success:
                # Salvar metadados
                metadata_file = backup_path / "backup_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Calcular tamanho do backup
                backup_size = self._calculate_directory_size(backup_path)
                
                backup_info = BackupInfo(
                    id=backup_id,
                    name=name,
                    backup_type=backup_type,
                    path=str(backup_path),
                    size=backup_size,
                    created_at=datetime.now(),
                    description=f"Backup {backup_type.value} criado automaticamente",
                    metadata=metadata
                )
                
                logger.info(f"Backup criado com sucesso: {backup_id} ({format_size(backup_size)})")
                return backup_info
            else:
                # Limpar diretório de backup em caso de falha
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                logger.error(f"Falha ao criar backup {backup_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar backup {backup_type.value}: {e}")
            return None    
    
    def list_available_backups(self) -> List[BackupInfo]:
        """
        Lista todos os backups disponíveis.
        
        Returns:
            List[BackupInfo]: Lista de informações dos backups
        """
        backups = []
        
        try:
            if not self.backups_dir.exists():
                logger.warning("Diretório de backups não existe")
                return backups
            
            for backup_dir in self.backups_dir.iterdir():
                if backup_dir.is_dir():
                    try:
                        backup_info = self._get_backup_info(backup_dir.name)
                        if backup_info:
                            backups.append(backup_info)
                    except Exception as e:
                        logger.warning(f"Erro ao processar backup {backup_dir.name}: {e}")
            
            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao listar backups: {e}")
        
        return backups
    
    def validate_backup(self, backup_id: str) -> bool:
        """
        Valida a integridade de um backup.
        
        Args:
            backup_id: ID do backup para validar
            
        Returns:
            bool: True se o backup é válido
        """
        try:
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return False
            
            backup_path = Path(backup_info.path)
            
            # Verificar se o diretório existe
            if not backup_path.exists():
                logger.error(f"Diretório de backup não existe: {backup_path}")
                return False
            
            # Verificar arquivo de metadados
            metadata_file = backup_path / "backup_metadata.json"
            if not metadata_file.exists():
                logger.error(f"Arquivo de metadados não encontrado: {metadata_file}")
                return False
            
            # Validar conteúdo baseado no tipo de backup
            if backup_info.backup_type == BackupType.EFI_PARTITION:
                return self._validate_efi_backup(backup_path)
            elif backup_info.backup_type == BackupType.CONFIGURATION:
                return self._validate_configuration_backup(backup_path)
            elif backup_info.backup_type == BackupType.COMPONENT_STATE:
                return self._validate_component_state_backup(backup_path)
            elif backup_info.backup_type == BackupType.SYSTEM_STATE:
                return self._validate_system_state_backup(backup_path)
            else:
                logger.warning(f"Tipo de backup desconhecido: {backup_info.backup_type}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao validar backup {backup_id}: {e}")
            return False
    
    # Métodos privados auxiliares
    
    def _get_repair_actions_for_issue(self, issue: Issue) -> List[RepairAction]:
        """
        Obtém ações de reparo disponíveis para um problema específico.
        
        Args:
            issue: Problema para obter ações de reparo
            
        Returns:
            List[RepairAction]: Lista de ações de reparo disponíveis
        """
        actions = []
        
        # Mapeamento de problemas para ações de reparo
        repair_mappings = {
            "disk_space_low": [
                RepairAction(
                    id="cleanup_temp_files",
                    title="Limpar arquivos temporários",
                    description="Remove arquivos temporários para liberar espaço",
                    repair_type=RepairType.AUTOMATIC,
                    target_issue=issue.id,
                    risk_level="low",
                    estimated_time="2-5 minutos"
                )
            ],
            "no_admin_privileges": [
                RepairAction(
                    id="request_admin_elevation",
                    title="Solicitar privilégios administrativos",
                    description="Solicita elevação de privilégios para o usuário",
                    repair_type=RepairType.INTERACTIVE,
                    target_issue=issue.id,
                    requires_admin=True,
                    risk_level="low",
                    estimated_time="1 minuto"
                )
            ],
            "python_version_old": [
                RepairAction(
                    id="suggest_python_update",
                    title="Sugerir atualização do Python",
                    description="Fornece instruções para atualizar o Python",
                    repair_type=RepairType.MANUAL,
                    target_issue=issue.id,
                    risk_level="medium",
                    estimated_time="15-30 minutos"
                )
            ],
            "conflicting_software": [
                RepairAction(
                    id="disable_conflicting_service",
                    title="Desabilitar serviço conflitante",
                    description="Desabilita temporariamente serviços que podem causar conflito",
                    repair_type=RepairType.AUTOMATIC,
                    target_issue=issue.id,
                    requires_admin=True,
                    risk_level="medium",
                    estimated_time="1-2 minutos",
                    backup_required=True
                )
            ]
        }
        
        # Buscar ações específicas para o problema
        if issue.id in repair_mappings:
            actions.extend(repair_mappings[issue.id])
        
        # Ações genéricas baseadas na categoria
        if issue.category.value == "disk_space" and not actions:
            actions.append(RepairAction(
                id="generic_disk_cleanup",
                title="Limpeza genérica de disco",
                description="Executa limpeza geral de arquivos desnecessários",
                repair_type=RepairType.AUTOMATIC,
                target_issue=issue.id,
                risk_level="low",
                estimated_time="5-10 minutos"
            ))
        
        return actions
    
    def _execute_repair_action(self, action: RepairAction, issue: Issue) -> RepairResult:
        """
        Executa uma ação de reparo específica.
        
        Args:
            action: Ação de reparo a ser executada
            issue: Problema sendo reparado
            
        Returns:
            RepairResult: Resultado da execução do reparo
        """
        logger.info(f"Executando ação de reparo: {action.title}")
        start_time = time.time()
        
        result = RepairResult(
            action_id=action.id,
            status=RecoveryStatus.IN_PROGRESS,
            message=f"Executando: {action.title}"
        )
        
        try:
            # Verificar pré-requisitos
            if action.requires_admin and not is_admin():
                result.status = RecoveryStatus.FAILED
                result.message = "Privilégios administrativos necessários"
                result.errors.append("Privilégios administrativos necessários")
                return result
            
            # Criar backup se necessário
            if action.backup_required:
                backup_id = self._create_repair_backup(action.id)
                if backup_id:
                    result.backup_created = backup_id
                else:
                    result.warnings.append("Não foi possível criar backup antes do reparo")
            
            # Executar ação específica
            success = False
            
            if action.id == "cleanup_temp_files":
                success = self._repair_cleanup_temp_files(result)
            elif action.id == "request_admin_elevation":
                success = self._repair_request_admin_elevation(result)
            elif action.id == "suggest_python_update":
                success = self._repair_suggest_python_update(result)
            elif action.id == "disable_conflicting_service":
                success = self._repair_disable_conflicting_service(result, issue)
            elif action.id == "generic_disk_cleanup":
                success = self._repair_generic_disk_cleanup(result)
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Ação de reparo não implementada: {action.id}"
                result.errors.append(f"Ação de reparo não implementada: {action.id}")
                success = False
            
            # Atualizar resultado final
            if success:
                result.status = RecoveryStatus.COMPLETED
                if not result.message.startswith("Sucesso"):
                    result.message = f"Reparo concluído com sucesso: {action.title}"
            else:
                result.status = RecoveryStatus.FAILED
                if not result.message.startswith("Falha"):
                    result.message = f"Falha no reparo: {action.title}"
            
        except Exception as e:
            result.status = RecoveryStatus.FAILED
            result.message = f"Erro durante reparo {action.title}: {str(e)}"
            result.errors.append(str(e))
            logger.error(f"Erro durante reparo {action.id}: {e}")
        
        result.duration = time.time() - start_time
        return result
    
    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """
        Obtém informações de um backup específico.
        
        Args:
            backup_id: ID do backup
            
        Returns:
            BackupInfo: Informações do backup ou None se não encontrado
        """
        try:
            backup_path = self.backups_dir / backup_id
            if not backup_path.exists():
                return None
            
            metadata_file = backup_path / "backup_metadata.json"
            if not metadata_file.exists():
                # Tentar inferir informações do diretório
                return self._infer_backup_info(backup_id, backup_path)
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            backup_type_str = metadata.get('backup_type', 'system_state')
            backup_type = BackupType(backup_type_str)
            
            created_at_str = metadata.get('created_at')
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
            
            backup_size = self._calculate_directory_size(backup_path)
            
            return BackupInfo(
                id=backup_id,
                name=metadata.get('name', backup_id),
                backup_type=backup_type,
                path=str(backup_path),
                size=backup_size,
                created_at=created_at,
                description=metadata.get('description', 'Backup sem descrição'),
                metadata=metadata,
                is_valid=self._validate_backup_structure(backup_path, backup_type)
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do backup {backup_id}: {e}")
            return None 
   
    def _infer_backup_info(self, backup_id: str, backup_path: Path) -> Optional[BackupInfo]:
        """
        Infere informações de um backup sem metadados.
        
        Args:
            backup_id: ID do backup
            backup_path: Caminho do backup
            
        Returns:
            BackupInfo: Informações inferidas do backup
        """
        try:
            # Determinar tipo de backup baseado no conteúdo
            backup_type = BackupType.SYSTEM_STATE  # padrão
            
            if (backup_path / "EFI").exists():
                backup_type = BackupType.EFI_PARTITION
            elif (backup_path / "config").exists():
                backup_type = BackupType.CONFIGURATION
            elif (backup_path / "components").exists():
                backup_type = BackupType.COMPONENT_STATE
            
            # Usar timestamp de criação do diretório
            created_at = datetime.fromtimestamp(backup_path.stat().st_ctime)
            backup_size = self._calculate_directory_size(backup_path)
            
            return BackupInfo(
                id=backup_id,
                name=f"Backup {backup_type.value} {created_at.strftime('%Y-%m-%d %H:%M')}",
                backup_type=backup_type,
                path=str(backup_path),
                size=backup_size,
                created_at=created_at,
                description="Backup sem metadados (inferido)",
                metadata={},
                is_valid=self._validate_backup_structure(backup_path, backup_type)
            )
            
        except Exception as e:
            logger.error(f"Erro ao inferir informações do backup {backup_id}: {e}")
            return None
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """
        Calcula o tamanho total de um diretório.
        
        Args:
            directory: Diretório para calcular
            
        Returns:
            int: Tamanho em bytes
        """
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.warning(f"Erro ao calcular tamanho de {directory}: {e}")
        
        return total_size
    
    def _validate_backup_structure(self, backup_path: Path, backup_type: BackupType) -> bool:
        """
        Valida a estrutura básica de um backup.
        
        Args:
            backup_path: Caminho do backup
            backup_type: Tipo do backup
            
        Returns:
            bool: True se a estrutura é válida
        """
        try:
            if backup_type == BackupType.EFI_PARTITION:
                return (backup_path / "EFI").exists()
            elif backup_type == BackupType.CONFIGURATION:
                return (backup_path / "config").exists() or len(list(backup_path.glob("*.yaml"))) > 0
            elif backup_type == BackupType.COMPONENT_STATE:
                return (backup_path / "components").exists() or (backup_path / "component_state.json").exists()
            else:
                return backup_path.exists() and any(backup_path.iterdir())
                
        except Exception:
            return False
    
    def _create_pre_restore_backup(self) -> Optional[str]:
        """
        Cria um backup do estado atual antes de uma restauração.
        
        Returns:
            str: ID do backup criado ou None se falhar
        """
        try:
            backup_info = self.create_system_backup(
                BackupType.SYSTEM_STATE,
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            return backup_info.id if backup_info else None
        except Exception as e:
            logger.error(f"Erro ao criar backup pré-restauração: {e}")
            return None
    
    def _create_repair_backup(self, action_id: str) -> Optional[str]:
        """
        Cria um backup antes de executar um reparo.
        
        Args:
            action_id: ID da ação de reparo
            
        Returns:
            str: ID do backup criado ou None se falhar
        """
        try:
            backup_info = self.create_system_backup(
                BackupType.SYSTEM_STATE,
                f"pre_repair_{action_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            return backup_info.id if backup_info else None
        except Exception as e:
            logger.error(f"Erro ao criar backup pré-reparo: {e}")
            return None
    
    # Métodos de verificação de inconsistências
    
    def _check_configuration_consistency(self) -> List[Dict[str, Any]]:
        """Verifica inconsistências nos arquivos de configuração"""
        inconsistencies = []
        
        try:
            config_files = [
                self.base_path / "env_dev" / "components.yaml",
                self.base_path / "config" / "settings.yaml"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    try:
                        import yaml
                        with open(config_file, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        inconsistencies.append({
                            'issue': f"Arquivo YAML inválido: {config_file}",
                            'severity': 'error',
                            'details': str(e),
                            'auto_fix': lambda: self._fix_yaml_file(config_file)
                        })
                    except Exception as e:
                        inconsistencies.append({
                            'issue': f"Erro ao ler configuração: {config_file}",
                            'severity': 'warning',
                            'details': str(e)
                        })
                else:
                    inconsistencies.append({
                        'issue': f"Arquivo de configuração ausente: {config_file}",
                        'severity': 'warning',
                        'auto_fix': lambda: self._create_default_config(config_file)
                    })
        
        except Exception as e:
            logger.error(f"Erro na verificação de configuração: {e}")
        
        return inconsistencies
    
    def _check_component_state_consistency(self) -> List[Dict[str, Any]]:
        """Verifica inconsistências no estado dos componentes"""
        inconsistencies = []
        
        try:
            # Verificar se existe arquivo de estado dos componentes
            state_file = self.base_path / "component_state.json"
            
            if state_file.exists():
                try:
                    with open(state_file, 'r', encoding='utf-8') as f:
                        state_data = json.load(f)
                    
                    # Verificar se os componentes instalados ainda existem
                    for component, info in state_data.items():
                        if info.get('status') == 'installed':
                            install_path = info.get('install_path')
                            if install_path and not Path(install_path).exists():
                                inconsistencies.append({
                                    'issue': f"Componente {component} marcado como instalado mas não encontrado em {install_path}",
                                    'severity': 'warning',
                                    'auto_fix': lambda c=component: self._fix_component_state(c, 'not_installed')
                                })
                
                except json.JSONDecodeError as e:
                    inconsistencies.append({
                        'issue': f"Arquivo de estado dos componentes corrompido: {state_file}",
                        'severity': 'error',
                        'details': str(e),
                        'auto_fix': lambda: self._recreate_component_state()
                    })
            else:
                inconsistencies.append({
                    'issue': "Arquivo de estado dos componentes não encontrado",
                    'severity': 'info',
                    'auto_fix': lambda: self._create_component_state_file()
                })
        
        except Exception as e:
            logger.error(f"Erro na verificação de estado dos componentes: {e}")
        
        return inconsistencies
    
    def _check_backup_integrity(self) -> List[Dict[str, Any]]:
        """Verifica integridade dos backups"""
        inconsistencies = []
        
        try:
            backups = self.list_available_backups()
            
            for backup in backups:
                if not self.validate_backup(backup.id):
                    inconsistencies.append({
                        'issue': f"Backup corrompido ou inválido: {backup.name}",
                        'severity': 'warning',
                        'auto_fix': lambda b=backup: self._remove_invalid_backup(b.id)
                    })
                
                # Verificar backups muito antigos
                age_days = (datetime.now() - backup.created_at).days
                if age_days > self.max_backup_age_days:
                    inconsistencies.append({
                        'issue': f"Backup antigo ({age_days} dias): {backup.name}",
                        'severity': 'info',
                        'auto_fix': lambda b=backup: self._archive_old_backup(b.id)
                    })
        
        except Exception as e:
            logger.error(f"Erro na verificação de integridade de backups: {e}")
        
        return inconsistencies
    
    def _check_directory_structure(self) -> List[Dict[str, Any]]:
        """Verifica estrutura de diretórios"""
        inconsistencies = []
        
        try:
            required_dirs = [
                self.base_path / "downloads",
                self.base_path / "temp",
                self.base_path / "logs",
                self.base_path / "backups",
                self.base_path / "cache"
            ]
            
            for directory in required_dirs:
                if not directory.exists():
                    inconsistencies.append({
                        'issue': f"Diretório necessário ausente: {directory}",
                        'severity': 'warning',
                        'auto_fix': lambda d=directory: self._create_directory(d)
                    })
                elif not check_write_permission(str(directory)):
                    inconsistencies.append({
                        'issue': f"Sem permissão de escrita no diretório: {directory}",
                        'severity': 'error'
                    })
        
        except Exception as e:
            logger.error(f"Erro na verificação de estrutura de diretórios: {e}")
        
        return inconsistencies
    
    def _check_file_permissions(self) -> List[Dict[str, Any]]:
        """Verifica permissões de arquivos críticos"""
        inconsistencies = []
        
        try:
            critical_files = [
                self.base_path / "env_dev" / "main.py",
                self.base_path / "env_dev" / "components.yaml"
            ]
            
            for file_path in critical_files:
                if file_path.exists():
                    if not check_write_permission(str(file_path.parent)):
                        inconsistencies.append({
                            'issue': f"Sem permissão de escrita para arquivo crítico: {file_path}",
                            'severity': 'error'
                        })
        
        except Exception as e:
            logger.error(f"Erro na verificação de permissões: {e}")
        
        return inconsistencies
    
    def _check_environment_variables(self) -> List[Dict[str, Any]]:
        """Verifica variáveis de ambiente"""
        inconsistencies = []
        
        try:
            # Verificar PATH
            path_env = os.environ.get('PATH', '')
            if not path_env:
                inconsistencies.append({
                    'issue': "Variável PATH não definida",
                    'severity': 'critical'
                })
            
            # Verificar TEMP
            temp_env = os.environ.get('TEMP', os.environ.get('TMP', ''))
            if temp_env and not Path(temp_env).exists():
                inconsistencies.append({
                    'issue': f"Diretório temporário não existe: {temp_env}",
                    'severity': 'warning',
                    'auto_fix': lambda: self._create_directory(Path(temp_env))
                })
        
        except Exception as e:
            logger.error(f"Erro na verificação de variáveis de ambiente: {e}")
        
        return inconsistencies    

    # Métodos de reparo específicos
    
    def _repair_cleanup_temp_files(self, result: RepairResult) -> bool:
        """Executa limpeza de arquivos temporários"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            cleanup_result = org_manager.cleanup_temporary_files()
            
            if cleanup_result.status.value == "completed":
                result.details['files_removed'] = cleanup_result.files_removed
                result.details['space_freed'] = cleanup_result.space_freed
                result.message = f"Limpeza concluída: {cleanup_result.files_removed} arquivos removidos, {format_size(cleanup_result.space_freed)} liberados"
                return True
            else:
                result.errors.extend(cleanup_result.errors)
                return False
                
        except Exception as e:
            result.errors.append(f"Erro na limpeza de temporários: {str(e)}")
            return False
    
    def _repair_request_admin_elevation(self, result: RepairResult) -> bool:
        """Solicita elevação de privilégios administrativos"""
        try:
            if is_admin():
                result.message = "Privilégios administrativos já disponíveis"
                return True
            
            # Informar ao usuário sobre a necessidade de privilégios
            result.message = "Privilégios administrativos necessários. Reinicie o aplicativo como administrador."
            result.warnings.append("Reinicie o aplicativo como administrador para funcionalidade completa")
            return False
            
        except Exception as e:
            result.errors.append(f"Erro ao verificar privilégios: {str(e)}")
            return False
    
    def _repair_suggest_python_update(self, result: RepairResult) -> bool:
        """Fornece sugestões para atualização do Python"""
        try:
            python_version = sys.version_info
            result.message = f"Python {python_version.major}.{python_version.minor}.{python_version.micro} detectado"
            result.details['suggestions'] = [
                "Acesse https://python.org/downloads",
                "Baixe a versão mais recente do Python",
                "Execute o instalador",
                "Reinicie o sistema após a instalação"
            ]
            result.warnings.append("Atualização manual do Python necessária")
            return True  # Consideramos sucesso pois fornecemos as instruções
            
        except Exception as e:
            result.errors.append(f"Erro ao gerar sugestões: {str(e)}")
            return False
    
    def _repair_disable_conflicting_service(self, result: RepairResult, issue: Issue) -> bool:
        """Desabilita serviços conflitantes"""
        try:
            if not is_admin():
                result.errors.append("Privilégios administrativos necessários para desabilitar serviços")
                return False
            
            # Identificar serviço conflitante do problema
            conflicting_software = issue.details.get('software', '')
            
            service_mappings = {
                'VMware': ['VMwareHostd', 'VMAuthdService'],
                'VirtualBox': ['VBoxSDS'],
                'Hyper-V': ['vmms', 'vmcompute'],
                'Docker Desktop': ['com.docker.service']
            }
            
            services_to_disable = service_mappings.get(conflicting_software, [])
            
            if not services_to_disable:
                result.warnings.append(f"Nenhum serviço conhecido para desabilitar: {conflicting_software}")
                return False
            
            disabled_services = []
            for service in services_to_disable:
                try:
                    # Tentar parar o serviço
                    cmd_result = subprocess.run(
                        ['sc', 'stop', service],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if cmd_result.returncode == 0:
                        disabled_services.append(service)
                        logger.info(f"Serviço {service} parado com sucesso")
                    else:
                        result.warnings.append(f"Não foi possível parar o serviço {service}")
                        
                except Exception as e:
                    result.warnings.append(f"Erro ao parar serviço {service}: {str(e)}")
            
            if disabled_services:
                result.details['disabled_services'] = disabled_services
                result.message = f"Serviços desabilitados: {', '.join(disabled_services)}"
                return True
            else:
                result.message = "Nenhum serviço foi desabilitado"
                return False
                
        except Exception as e:
            result.errors.append(f"Erro ao desabilitar serviços: {str(e)}")
            return False
    
    def _repair_generic_disk_cleanup(self, result: RepairResult) -> bool:
        """Executa limpeza genérica de disco"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            optimization_result = org_manager.optimize_disk_usage()
            
            if optimization_result.status.value == "completed":
                result.details['space_freed'] = optimization_result.total_space_freed
                result.details['operations'] = optimization_result.operations_performed
                result.message = f"Otimização concluída: {format_size(optimization_result.total_space_freed)} liberados"
                return True
            else:
                result.errors.extend(optimization_result.errors)
                return False
                
        except Exception as e:
            result.errors.append(f"Erro na otimização de disco: {str(e)}")
            return False
    
    # Métodos de correção de inconsistências
    
    def _fix_yaml_file(self, config_file: Path) -> bool:
        """Tenta corrigir um arquivo YAML corrompido"""
        try:
            # Criar backup do arquivo corrompido
            backup_file = config_file.with_suffix('.yaml.bak')
            shutil.copy2(config_file, backup_file)
            
            # Tentar carregar e reescrever o arquivo
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Tentar corrigir problemas comuns
            content = content.replace('\t', '  ')  # Substituir tabs por espaços
            
            # Tentar carregar novamente
            data = yaml.safe_load(content)
            
            # Reescrever o arquivo
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Arquivo YAML corrigido: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao corrigir arquivo YAML {config_file}: {e}")
            return False
    
    def _create_default_config(self, config_file: Path) -> bool:
        """Cria um arquivo de configuração padrão"""
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            default_config = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'settings': {
                    'auto_backup': True,
                    'max_backups': 10,
                    'log_level': 'INFO'
                }
            }
            
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Arquivo de configuração padrão criado: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar configuração padrão {config_file}: {e}")
            return False
    
    def _fix_component_state(self, component: str, new_status: str) -> bool:
        """Corrige o estado de um componente"""
        try:
            state_file = self.base_path / "component_state.json"
            
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
            else:
                state_data = {}
            
            if component in state_data:
                state_data[component]['status'] = new_status
                state_data[component]['updated_at'] = datetime.now().isoformat()
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Estado do componente {component} atualizado para {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao corrigir estado do componente {component}: {e}")
            return False
    
    def _recreate_component_state(self) -> bool:
        """Recria o arquivo de estado dos componentes"""
        try:
            state_file = self.base_path / "component_state.json"
            
            # Criar backup se o arquivo existir
            if state_file.exists():
                backup_file = state_file.with_suffix('.json.bak')
                shutil.copy2(state_file, backup_file)
            
            # Criar novo arquivo de estado
            new_state = {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'components': {}
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(new_state, f, indent=2, ensure_ascii=False)
            
            logger.info("Arquivo de estado dos componentes recriado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao recriar estado dos componentes: {e}")
            return False
    
    def _create_component_state_file(self) -> bool:
        """Cria arquivo de estado dos componentes"""
        return self._recreate_component_state()
    
    def _remove_invalid_backup(self, backup_id: str) -> bool:
        """Remove um backup inválido"""
        try:
            backup_path = self.backups_dir / backup_id
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"Backup inválido removido: {backup_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover backup inválido {backup_id}: {e}")
            return False
    
    def _archive_old_backup(self, backup_id: str) -> bool:
        """Arquiva um backup antigo"""
        try:
            backup_path = self.backups_dir / backup_id
            archive_dir = self.backups_dir / "archived"
            archive_dir.mkdir(exist_ok=True)
            
            archive_path = archive_dir / backup_id
            shutil.move(str(backup_path), str(archive_path))
            
            logger.info(f"Backup arquivado: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao arquivar backup {backup_id}: {e}")
            return False
    
    def _create_directory(self, directory: Path) -> bool:
        """Cria um diretório"""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório criado: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar diretório {directory}: {e}")
            return False    

    # Métodos de backup específicos
    
    def _create_efi_backup(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Cria backup da partição EFI"""
        try:
            efi_backup_result = create_efi_backup(f"recovery_{int(time.time())}")
            
            if efi_backup_result and efi_backup_result.get('success'):
                # Copiar backup EFI para o diretório de backup do recovery
                efi_backup_path = Path(efi_backup_result['path'])
                target_efi_path = backup_path / "EFI"
                
                if efi_backup_path.exists():
                    shutil.copytree(efi_backup_path, target_efi_path)
                    metadata['efi_backup_path'] = str(efi_backup_path)
                    logger.info("Backup EFI criado com sucesso")
                    return True
            
            logger.error("Falha ao criar backup EFI")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao criar backup EFI: {e}")
            return False
    
    def _create_configuration_backup(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Cria backup das configurações"""
        try:
            config_dir = backup_path / "config"
            config_dir.mkdir(exist_ok=True)
            
            # Arquivos de configuração para backup
            config_files = [
                self.base_path / "env_dev" / "components.yaml",
                self.base_path / "config" / "settings.yaml",
                self.base_path / "component_state.json"
            ]
            
            backed_up_files = []
            for config_file in config_files:
                if config_file.exists():
                    target_file = config_dir / config_file.name
                    shutil.copy2(config_file, target_file)
                    backed_up_files.append(str(config_file))
            
            metadata['backed_up_files'] = backed_up_files
            logger.info(f"Backup de configuração criado: {len(backed_up_files)} arquivos")
            return len(backed_up_files) > 0
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de configuração: {e}")
            return False
    
    def _create_component_state_backup(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Cria backup do estado dos componentes"""
        try:
            components_dir = backup_path / "components"
            components_dir.mkdir(exist_ok=True)
            
            # Backup do estado dos componentes
            state_file = self.base_path / "component_state.json"
            if state_file.exists():
                shutil.copy2(state_file, components_dir / "component_state.json")
            
            # Backup de logs de instalação
            logs_dir = self.base_path / "logs"
            if logs_dir.exists():
                target_logs_dir = components_dir / "logs"
                shutil.copytree(logs_dir, target_logs_dir, ignore=shutil.ignore_patterns('*.lock'))
            
            metadata['component_state_backed_up'] = True
            logger.info("Backup do estado dos componentes criado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar backup do estado dos componentes: {e}")
            return False
    
    def _create_system_state_backup(self, backup_path: Path, metadata: Dict[str, Any]) -> bool:
        """Cria backup completo do estado do sistema"""
        try:
            # Combinar todos os tipos de backup
            success = True
            
            # Backup de configurações
            if not self._create_configuration_backup(backup_path, metadata):
                success = False
            
            # Backup do estado dos componentes
            if not self._create_component_state_backup(backup_path, metadata):
                success = False
            
            # Backup de informações do sistema
            system_info_file = backup_path / "system_info.json"
            try:
                diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
                system_info = {
                    'diagnostic_result': {
                        'system_info': diagnostic_result.system_info.__dict__,
                        'compatibility': diagnostic_result.compatibility.__dict__,
                        'overall_health': diagnostic_result.overall_health.value,
                        'timestamp': diagnostic_result.timestamp.isoformat()
                    },
                    'environment_variables': dict(os.environ),
                    'python_path': sys.path,
                    'working_directory': str(Path.cwd())
                }
                
                with open(system_info_file, 'w', encoding='utf-8') as f:
                    json.dump(system_info, f, indent=2, ensure_ascii=False, default=str)
                
            except Exception as e:
                logger.warning(f"Erro ao salvar informações do sistema: {e}")
            
            metadata['system_state_backup'] = True
            logger.info("Backup do estado do sistema criado")
            return success
            
        except Exception as e:
            logger.error(f"Erro ao criar backup do estado do sistema: {e}")
            return False
    
    # Métodos de restauração específicos
    
    def _restore_efi_backup(self, backup_info: BackupInfo, result: RestoreResult) -> bool:
        """Restaura backup da partição EFI"""
        try:
            efi_backup_path = Path(backup_info.path) / "EFI"
            
            if not efi_backup_path.exists():
                result.errors.append("Backup EFI não encontrado no backup")
                return False
            
            # Usar a função de restauração EFI existente
            success = restore_efi_backup(str(efi_backup_path))
            
            if success:
                result.restored_files.append("Partição EFI")
                result.message = "Partição EFI restaurada com sucesso"
                return True
            else:
                result.errors.append("Falha ao restaurar partição EFI")
                return False
                
        except Exception as e:
            result.errors.append(f"Erro ao restaurar EFI: {str(e)}")
            return False
    
    def update_components(self, components: List[str]) -> Dict[str, Any]:
        """
        Sistema de atualização automática de componentes.
        
        Args:
            components: Lista de componentes para atualizar
            
        Returns:
            Dict[str, Any]: Resultado das atualizações
        """
        logger.info(f"Iniciando atualização de {len(components)} componentes")
        
        update_results = {
            'total_components': len(components),
            'updated_components': [],
            'failed_components': [],
            'skipped_components': [],
            'errors': [],
            'warnings': [],
            'total_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Verificar componentes desatualizados primeiro
            outdated_info = self.check_outdated_components(components)
            
            for component in components:
                try:
                    component_info = outdated_info.get(component, {})
                    
                    if not component_info.get('needs_update', False):
                        update_results['skipped_components'].append({
                            'component': component,
                            'reason': 'Already up to date',
                            'current_version': component_info.get('current_version', 'unknown')
                        })
                        continue
                    
                    # Criar backup antes da atualização
                    backup_id = self._create_component_update_backup(component)
                    
                    # Executar atualização
                    update_result = self._update_single_component(component, component_info)
                    
                    if update_result['success']:
                        update_results['updated_components'].append({
                            'component': component,
                            'old_version': component_info.get('current_version', 'unknown'),
                            'new_version': update_result.get('new_version', 'unknown'),
                            'backup_id': backup_id,
                            'update_time': update_result.get('duration', 0)
                        })
                        logger.info(f"Componente {component} atualizado com sucesso")
                    else:
                        update_results['failed_components'].append({
                            'component': component,
                            'error': update_result.get('error', 'Unknown error'),
                            'backup_id': backup_id
                        })
                        logger.error(f"Falha ao atualizar {component}: {update_result.get('error')}")
                        
                        # Restaurar backup em caso de falha
                        if backup_id:
                            self._restore_component_backup(backup_id)
                
                except Exception as e:
                    error_msg = f"Erro ao atualizar {component}: {str(e)}"
                    update_results['errors'].append(error_msg)
                    update_results['failed_components'].append({
                        'component': component,
                        'error': error_msg
                    })
                    logger.error(error_msg)
            
            update_results['total_time'] = time.time() - start_time
            
            # Log do resumo
            logger.info(f"Atualização concluída: "
                       f"{len(update_results['updated_components'])} atualizados, "
                       f"{len(update_results['failed_components'])} falharam, "
                       f"{len(update_results['skipped_components'])} pulados")
            
        except Exception as e:
            update_results['errors'].append(f"Erro geral na atualização: {str(e)}")
            logger.error(f"Erro geral na atualização: {e}")
        
        return update_results
    
    def check_outdated_components(self, components: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Verifica componentes desatualizados e gera notificações.
        
        Args:
            components: Lista de componentes para verificar (None = todos)
            
        Returns:
            Dict[str, Dict[str, Any]]: Informações sobre componentes desatualizados
        """
        logger.info("Verificando componentes desatualizados")
        
        outdated_info = {}
        
        try:
            # Carregar configurações dos componentes
            components_config_path = self.base_path / "env_dev" / "components.yaml"
            
            if not components_config_path.exists():
                logger.warning("Arquivo de configuração de componentes não encontrado")
                return outdated_info
            
            import yaml
            with open(components_config_path, 'r', encoding='utf-8') as f:
                all_components = yaml.safe_load(f) or {}
            
            # Se não especificado, verificar todos os componentes
            if components is None:
                components = list(all_components.keys())
            
            # Carregar estado atual dos componentes
            state_file = self.base_path / "component_state.json"
            current_state = {}
            
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    current_state = json.load(f)
            
            for component in components:
                try:
                    component_config = all_components.get(component, {})
                    component_state = current_state.get(component, {})
                    
                    if component_state.get('status') != 'installed':
                        continue
                    
                    current_version = component_state.get('version', 'unknown')
                    latest_version = self._get_latest_version(component, component_config)
                    
                    needs_update = self._compare_versions(current_version, latest_version)
                    
                    outdated_info[component] = {
                        'current_version': current_version,
                        'latest_version': latest_version,
                        'needs_update': needs_update,
                        'last_checked': datetime.now().isoformat(),
                        'update_priority': self._get_update_priority(component, component_config),
                        'update_size_mb': component_config.get('update_size_mb', 0),
                        'changelog_url': component_config.get('changelog_url', ''),
                        'security_update': component_config.get('security_update', False)
                    }
                    
                    if needs_update:
                        logger.info(f"Componente desatualizado: {component} "
                                   f"({current_version} -> {latest_version})")
                
                except Exception as e:
                    logger.error(f"Erro ao verificar {component}: {e}")
                    outdated_info[component] = {
                        'error': str(e),
                        'needs_update': False,
                        'last_checked': datetime.now().isoformat()
                    }
            
        except Exception as e:
            logger.error(f"Erro geral na verificação de componentes: {e}")
        
        return outdated_info
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        Gera relatório completo de saúde do sistema.
        
        Returns:
            Dict[str, Any]: Relatório de saúde detalhado
        """
        logger.info("Gerando relatório de saúde do sistema")
        
        report = {
            'report_id': f"health_{int(time.time())}",
            'generated_at': datetime.now().isoformat(),
            'system_info': {},
            'diagnostic_results': {},
            'component_status': {},
            'outdated_components': {},
            'backup_status': {},
            'disk_usage': {},
            'inconsistencies': {},
            'recommendations': [],
            'overall_health_score': 0,
            'health_status': 'unknown',
            'critical_issues': [],
            'warnings': [],
            'maintenance_suggestions': []
        }
        
        try:
            # 1. Informações do sistema
            report['system_info'] = self._collect_system_info()
            
            # 2. Executar diagnóstico completo
            diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
            report['diagnostic_results'] = {
                'overall_health': diagnostic_result.overall_health.value,
                'issues_count': len(diagnostic_result.issues),
                'critical_issues': len([i for i in diagnostic_result.issues if i.severity.value == 'critical']),
                'error_issues': len([i for i in diagnostic_result.issues if i.severity.value == 'error']),
                'warning_issues': len([i for i in diagnostic_result.issues if i.severity.value == 'warning']),
                'compatibility_status': diagnostic_result.compatibility.status.value,
                'timestamp': diagnostic_result.timestamp.isoformat()
            }
            
            # 3. Status dos componentes
            report['component_status'] = self._analyze_component_status()
            
            # 4. Componentes desatualizados
            report['outdated_components'] = self.check_outdated_components()
            
            # 5. Status dos backups
            report['backup_status'] = self._analyze_backup_status()
            
            # 6. Uso de disco
            report['disk_usage'] = self._analyze_disk_usage()
            
            # 7. Inconsistências
            inconsistency_result = self.detect_and_fix_inconsistencies()
            report['inconsistencies'] = {
                'total_found': inconsistency_result.inconsistencies_found,
                'total_fixed': inconsistency_result.inconsistencies_fixed,
                'issues': inconsistency_result.issues,
                'errors': inconsistency_result.errors
            }
            
            # 8. Calcular pontuação de saúde
            report['overall_health_score'] = self._calculate_health_score(report)
            report['health_status'] = self._determine_health_status(report['overall_health_score'])
            
            # 9. Gerar recomendações
            report['recommendations'] = self._generate_health_recommendations(report)
            report['maintenance_suggestions'] = self._generate_maintenance_suggestions(report)
            
            # 10. Identificar problemas críticos
            report['critical_issues'] = self._identify_critical_issues(report)
            
            # Salvar relatório
            self._save_health_report(report)
            
            logger.info(f"Relatório de saúde gerado: Score {report['overall_health_score']}/100, "
                       f"Status: {report['health_status']}")
            
        except Exception as e:
            report['errors'] = [f"Erro ao gerar relatório: {str(e)}"]
            logger.error(f"Erro ao gerar relatório de saúde: {e}")
        
        return report
    
    def run_maintenance_tasks(self, tasks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executa tarefas de manutenção preventiva do sistema.
        
        Args:
            tasks: Lista de tarefas específicas (None = todas)
            
        Returns:
            Dict[str, Any]: Resultado das tarefas de manutenção
        """
        logger.info("Iniciando tarefas de manutenção preventiva")
        
        maintenance_result = {
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'total_duration': 0.0,
            'tasks_executed': [],
            'tasks_failed': [],
            'tasks_skipped': [],
            'overall_success': False,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        start_time = time.time()
        
        try:
            # Tarefas de manutenção disponíveis
            available_tasks = {
                'cleanup_temp_files': {
                    'name': 'Limpeza de arquivos temporários',
                    'function': self._maintenance_cleanup_temp_files,
                    'priority': 'high',
                    'estimated_time': 300  # 5 minutos
                },
                'rotate_logs': {
                    'name': 'Rotação de logs',
                    'function': self._maintenance_rotate_logs,
                    'priority': 'medium',
                    'estimated_time': 120  # 2 minutos
                },
                'backup_cleanup': {
                    'name': 'Limpeza de backups antigos',
                    'function': self._maintenance_backup_cleanup,
                    'priority': 'medium',
                    'estimated_time': 180  # 3 minutos
                },
                'component_verification': {
                    'name': 'Verificação de componentes',
                    'function': self._maintenance_component_verification,
                    'priority': 'high',
                    'estimated_time': 240  # 4 minutos
                },
                'system_optimization': {
                    'name': 'Otimização do sistema',
                    'function': self._maintenance_system_optimization,
                    'priority': 'low',
                    'estimated_time': 600  # 10 minutos
                },
                'security_scan': {
                    'name': 'Verificação de segurança',
                    'function': self._maintenance_security_scan,
                    'priority': 'high',
                    'estimated_time': 300  # 5 minutos
                }
            }
            
            # Se não especificado, executar tarefas de alta prioridade
            if tasks is None:
                tasks = [name for name, info in available_tasks.items() 
                        if info['priority'] in ['high', 'medium']]
            
            # Executar tarefas
            for task_name in tasks:
                if task_name not in available_tasks:
                    maintenance_result['tasks_skipped'].append({
                        'task': task_name,
                        'reason': 'Task not found'
                    })
                    continue
                
                task_info = available_tasks[task_name]
                
                try:
                    logger.info(f"Executando tarefa de manutenção: {task_info['name']}")
                    task_start = time.time()
                    
                    task_result = task_info['function']()
                    task_duration = time.time() - task_start
                    
                    if task_result.get('success', False):
                        maintenance_result['tasks_executed'].append({
                            'task': task_name,
                            'name': task_info['name'],
                            'duration': task_duration,
                            'result': task_result
                        })
                        logger.info(f"Tarefa {task_name} concluída em {task_duration:.2f}s")
                    else:
                        maintenance_result['tasks_failed'].append({
                            'task': task_name,
                            'name': task_info['name'],
                            'error': task_result.get('error', 'Unknown error'),
                            'duration': task_duration
                        })
                        logger.error(f"Tarefa {task_name} falhou: {task_result.get('error')}")
                
                except Exception as e:
                    error_msg = f"Erro na tarefa {task_name}: {str(e)}"
                    maintenance_result['errors'].append(error_msg)
                    maintenance_result['tasks_failed'].append({
                        'task': task_name,
                        'name': task_info['name'],
                        'error': error_msg
                    })
                    logger.error(error_msg)
            
            # Calcular resultado final
            maintenance_result['total_duration'] = time.time() - start_time
            maintenance_result['completed_at'] = datetime.now().isoformat()
            maintenance_result['overall_success'] = len(maintenance_result['tasks_failed']) == 0
            
            # Gerar recomendações baseadas nos resultados
            maintenance_result['recommendations'] = self._generate_maintenance_recommendations(
                maintenance_result
            )
            
            logger.info(f"Manutenção concluída: "
                       f"{len(maintenance_result['tasks_executed'])} sucessos, "
                       f"{len(maintenance_result['tasks_failed'])} falhas")
            
        except Exception as e:
            maintenance_result['errors'].append(f"Erro geral na manutenção: {str(e)}")
            logger.error(f"Erro geral na manutenção: {e}")
        
        return maintenance_result
    
    # Helper methods for maintenance system
    
    def _get_latest_version(self, component: str, component_config: Dict[str, Any]) -> str:
        """Obtém a versão mais recente de um componente"""
        try:
            # Simular verificação de versão (em implementação real, consultaria API/repositório)
            version_url = component_config.get('version_check_url', '')
            if version_url:
                # Aqui seria feita uma requisição HTTP para verificar a versão
                # Por enquanto, retorna a versão configurada
                return component_config.get('version', '1.0.0')
            
            return component_config.get('version', '1.0.0')
        except Exception:
            return 'unknown'
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compara versões para determinar se atualização é necessária"""
        try:
            if current == 'unknown' or latest == 'unknown':
                return False
            
            # Implementação simples de comparação de versões
            current_parts = [int(x) for x in current.split('.') if x.isdigit()]
            latest_parts = [int(x) for x in latest.split('.') if x.isdigit()]
            
            # Normalizar tamanhos
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return latest_parts > current_parts
        except Exception:
            return False
    
    def _get_update_priority(self, component: str, component_config: Dict[str, Any]) -> str:
        """Determina a prioridade de atualização de um componente"""
        if component_config.get('security_update', False):
            return 'critical'
        elif component_config.get('critical_component', False):
            return 'high'
        elif component_config.get('recommended_update', True):
            return 'medium'
        else:
            return 'low'
    
    def _create_component_update_backup(self, component: str) -> Optional[str]:
        """Cria backup antes de atualizar um componente"""
        try:
            backup_info = self.create_system_backup(
                BackupType.COMPONENT_STATE,
                f"pre_update_{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            return backup_info.id if backup_info else None
        except Exception as e:
            logger.error(f"Erro ao criar backup pré-atualização: {e}")
            return None
    
    def _update_single_component(self, component: str, component_info: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza um componente específico"""
        try:
            # Simular processo de atualização
            # Em implementação real, faria download e instalação da nova versão
            
            start_time = time.time()
            
            # Simular tempo de atualização
            time.sleep(1)
            
            # Atualizar estado do componente
            state_file = self.base_path / "component_state.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                if component in state_data:
                    state_data[component]['version'] = component_info.get('latest_version', 'unknown')
                    state_data[component]['updated_at'] = datetime.now().isoformat()
                    state_data[component]['update_status'] = 'updated'
                
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'new_version': component_info.get('latest_version', 'unknown'),
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _restore_component_backup(self, backup_id: str) -> bool:
        """Restaura backup de componente em caso de falha na atualização"""
        try:
            restore_result = self.restore_from_backup(backup_id)
            return restore_result.status == RecoveryStatus.COMPLETED
        except Exception as e:
            logger.error(f"Erro ao restaurar backup {backup_id}: {e}")
            return False
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Coleta informações básicas do sistema"""
        try:
            import platform
            
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'python_implementation': platform.python_implementation(),
                'hostname': platform.node(),
                'current_directory': str(Path.cwd()),
                'base_path': str(self.base_path),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao coletar informações do sistema: {e}")
            return {'error': str(e)}
    
    def _analyze_component_status(self) -> Dict[str, Any]:
        """Analisa o status atual dos componentes"""
        try:
            state_file = self.base_path / "component_state.json"
            
            if not state_file.exists():
                return {'error': 'Component state file not found'}
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            analysis = {
                'total_components': len(state_data),
                'installed_components': 0,
                'failed_components': 0,
                'pending_components': 0,
                'components_by_status': {},
                'last_updated': None
            }
            
            for component, info in state_data.items():
                status = info.get('status', 'unknown')
                analysis['components_by_status'][status] = analysis['components_by_status'].get(status, 0) + 1
                
                if status == 'installed':
                    analysis['installed_components'] += 1
                elif status == 'failed':
                    analysis['failed_components'] += 1
                elif status == 'pending':
                    analysis['pending_components'] += 1
                
                # Encontrar última atualização
                updated_at = info.get('updated_at')
                if updated_at:
                    if not analysis['last_updated'] or updated_at > analysis['last_updated']:
                        analysis['last_updated'] = updated_at
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar status dos componentes: {e}")
            return {'error': str(e)}
    
    def _analyze_backup_status(self) -> Dict[str, Any]:
        """Analisa o status dos backups"""
        try:
            backups = self.list_available_backups()
            
            analysis = {
                'total_backups': len(backups),
                'valid_backups': 0,
                'invalid_backups': 0,
                'backup_types': {},
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'average_size': 0
            }
            
            for backup in backups:
                analysis['total_size'] += backup.size
                
                if backup.is_valid:
                    analysis['valid_backups'] += 1
                else:
                    analysis['invalid_backups'] += 1
                
                backup_type = backup.backup_type.value
                analysis['backup_types'][backup_type] = analysis['backup_types'].get(backup_type, 0) + 1
                
                if not analysis['oldest_backup'] or backup.created_at < analysis['oldest_backup']:
                    analysis['oldest_backup'] = backup.created_at.isoformat()
                
                if not analysis['newest_backup'] or backup.created_at > analysis['newest_backup']:
                    analysis['newest_backup'] = backup.created_at.isoformat()
            
            if analysis['total_backups'] > 0:
                analysis['average_size'] = analysis['total_size'] / analysis['total_backups']
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar status dos backups: {e}")
            return {'error': str(e)}
    
    def _analyze_disk_usage(self) -> Dict[str, Any]:
        """Analisa o uso de disco"""
        try:
            disk_info = get_disk_space(str(self.base_path))
            
            if not disk_info:
                return {'error': 'Unable to get disk information'}
            
            # Analisar diretórios do projeto
            project_dirs = ['downloads', 'backups', 'logs', 'cache', 'temp']
            dir_sizes = {}
            
            for dir_name in project_dirs:
                dir_path = self.base_path / dir_name
                if dir_path.exists():
                    dir_sizes[dir_name] = self._calculate_directory_size(dir_path)
            
            total_project_size = sum(dir_sizes.values())
            
            return {
                'disk_total': disk_info.get('total', 0),
                'disk_used': disk_info.get('used', 0),
                'disk_free': disk_info.get('free', 0),
                'disk_free_percent': disk_info.get('free_percent', 0),
                'project_total_size': total_project_size,
                'directory_sizes': dir_sizes,
                'largest_directory': max(dir_sizes.items(), key=lambda x: x[1]) if dir_sizes else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar uso de disco: {e}")
            return {'error': str(e)}
    
    def _calculate_health_score(self, report: Dict[str, Any]) -> int:
        """Calcula pontuação de saúde do sistema (0-100)"""
        try:
            score = 100
            
            # Penalizar por problemas críticos
            diagnostic = report.get('diagnostic_results', {})
            critical_issues = diagnostic.get('critical_issues', 0)
            error_issues = diagnostic.get('error_issues', 0)
            warning_issues = diagnostic.get('warning_issues', 0)
            
            score -= critical_issues * 20
            score -= error_issues * 10
            score -= warning_issues * 5
            
            # Penalizar por componentes desatualizados
            outdated = report.get('outdated_components', {})
            outdated_count = len([c for c in outdated.values() if c.get('needs_update', False)])
            score -= outdated_count * 3
            
            # Penalizar por uso de disco alto
            disk_usage = report.get('disk_usage', {})
            free_percent = disk_usage.get('disk_free_percent', 100)
            if free_percent < 10:
                score -= 30
            elif free_percent < 20:
                score -= 15
            elif free_percent < 30:
                score -= 5
            
            # Penalizar por inconsistências
            inconsistencies = report.get('inconsistencies', {})
            unfixed_issues = inconsistencies.get('total_found', 0) - inconsistencies.get('total_fixed', 0)
            score -= unfixed_issues * 2
            
            # Bonificar por backups válidos
            backup_status = report.get('backup_status', {})
            valid_backups = backup_status.get('valid_backups', 0)
            if valid_backups > 0:
                score += min(valid_backups * 2, 10)
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Erro ao calcular pontuação de saúde: {e}")
            return 0
    
    def _determine_health_status(self, score: int) -> str:
        """Determina status de saúde baseado na pontuação"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'fair'
        elif score >= 40:
            return 'poor'
        else:
            return 'critical'
    
    def _generate_health_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas no relatório de saúde"""
        recommendations = []
        
        try:
            # Recomendações baseadas em problemas críticos
            diagnostic = report.get('diagnostic_results', {})
            if diagnostic.get('critical_issues', 0) > 0:
                recommendations.append("🚨 CRÍTICO: Resolva os problemas críticos imediatamente")
            
            # Recomendações de espaço em disco
            disk_usage = report.get('disk_usage', {})
            free_percent = disk_usage.get('disk_free_percent', 100)
            if free_percent < 10:
                recommendations.append("💾 URGENTE: Espaço em disco muito baixo (<10%)")
            elif free_percent < 20:
                recommendations.append("💾 Espaço em disco baixo (<20%), considere limpeza")
            
            # Recomendações de componentes
            outdated = report.get('outdated_components', {})
            security_updates = len([c for c in outdated.values() 
                                  if c.get('security_update', False)])
            if security_updates > 0:
                recommendations.append(f"🔒 {security_updates} atualizações de segurança disponíveis")
            
            # Recomendações de backup
            backup_status = report.get('backup_status', {})
            if backup_status.get('total_backups', 0) == 0:
                recommendations.append("💾 Nenhum backup encontrado - crie backups regulares")
            elif backup_status.get('invalid_backups', 0) > 0:
                recommendations.append("⚠️ Alguns backups estão corrompidos - verifique integridade")
            
            # Recomendações de manutenção
            score = report.get('overall_health_score', 0)
            if score < 60:
                recommendations.append("🔧 Execute manutenção preventiva para melhorar a saúde do sistema")
            
            if not recommendations:
                recommendations.append("✅ Sistema em bom estado - continue com manutenção regular")
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            recommendations.append("❌ Erro ao gerar recomendações")
        
        return recommendations
    
    def _generate_maintenance_suggestions(self, report: Dict[str, Any]) -> List[str]:
        """Gera sugestões de manutenção"""
        suggestions = []
        
        try:
            # Sugestões baseadas no uso de disco
            disk_usage = report.get('disk_usage', {})
            dir_sizes = disk_usage.get('directory_sizes', {})
            
            if dir_sizes.get('temp', 0) > 100 * 1024 * 1024:  # > 100MB
                suggestions.append("🧹 Limpar arquivos temporários (>100MB detectados)")
            
            if dir_sizes.get('logs', 0) > 500 * 1024 * 1024:  # > 500MB
                suggestions.append("📝 Arquivar logs antigos (>500MB detectados)")
            
            # Sugestões de backup
            backup_status = report.get('backup_status', {})
            if backup_status.get('total_backups', 0) > 15:
                suggestions.append("🗂️ Limpar backups antigos (>15 backups encontrados)")
            
            # Sugestões de componentes
            component_status = report.get('component_status', {})
            if component_status.get('failed_components', 0) > 0:
                suggestions.append("🔧 Reparar componentes com falha")
            
            # Sugestões gerais
            suggestions.extend([
                "📅 Execute manutenção semanal para manter o sistema otimizado",
                "🔍 Verifique atualizações mensalmente",
                "💾 Mantenha pelo menos 3 backups recentes"
            ])
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões de manutenção: {e}")
        
        return suggestions
    
    def _identify_critical_issues(self, report: Dict[str, Any]) -> List[str]:
        """Identifica problemas críticos que requerem atenção imediata"""
        critical_issues = []
        
        try:
            # Problemas de espaço em disco
            disk_usage = report.get('disk_usage', {})
            if disk_usage.get('disk_free_percent', 100) < 5:
                critical_issues.append("Espaço em disco criticamente baixo (<5%)")
            
            # Problemas de diagnóstico
            diagnostic = report.get('diagnostic_results', {})
            if diagnostic.get('critical_issues', 0) > 0:
                critical_issues.append(f"{diagnostic['critical_issues']} problemas críticos detectados")
            
            # Problemas de backup
            backup_status = report.get('backup_status', {})
            if backup_status.get('total_backups', 0) == 0:
                critical_issues.append("Nenhum backup disponível - risco de perda de dados")
            
            # Atualizações de segurança
            outdated = report.get('outdated_components', {})
            security_updates = len([c for c in outdated.values() 
                                  if c.get('security_update', False)])
            if security_updates > 0:
                critical_issues.append(f"{security_updates} atualizações críticas de segurança pendentes")
            
        except Exception as e:
            logger.error(f"Erro ao identificar problemas críticos: {e}")
        
        return critical_issues
    
    def _save_health_report(self, report: Dict[str, Any]) -> None:
        """Salva o relatório de saúde em arquivo"""
        try:
            reports_dir = self.recovery_logs_dir / "health_reports"
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"health_report_{report['report_id']}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Relatório de saúde salvo: {report_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar relatório de saúde: {e}")
    
    # Maintenance task implementations
    
    def _maintenance_cleanup_temp_files(self) -> Dict[str, Any]:
        """Tarefa de manutenção: limpeza de arquivos temporários"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            result = org_manager.cleanup_temporary_files()
            
            return {
                'success': result.status.value == 'completed',
                'files_removed': result.files_removed,
                'space_freed': result.space_freed,
                'errors': result.errors
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _maintenance_rotate_logs(self) -> Dict[str, Any]:
        """Tarefa de manutenção: rotação de logs"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            result = org_manager.rotate_logs()
            
            return {
                'success': result.status.value == 'completed',
                'logs_rotated': result.files_removed,
                'space_freed': result.space_freed,
                'errors': result.errors
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _maintenance_backup_cleanup(self) -> Dict[str, Any]:
        """Tarefa de manutenção: limpeza de backups antigos"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            result = org_manager.manage_backups()
            
            return {
                'success': result.status.value == 'completed',
                'backups_processed': result.backups_processed,
                'backups_removed': result.backups_removed,
                'space_freed': result.space_freed,
                'errors': result.errors
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _maintenance_component_verification(self) -> Dict[str, Any]:
        """Tarefa de manutenção: verificação de componentes"""
        try:
            diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
            
            return {
                'success': True,
                'overall_health': diagnostic_result.overall_health.value,
                'issues_found': len(diagnostic_result.issues),
                'critical_issues': len([i for i in diagnostic_result.issues if i.severity.value == 'critical'])
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _maintenance_system_optimization(self) -> Dict[str, Any]:
        """Tarefa de manutenção: otimização do sistema"""
        try:
            from env_dev.core.organization_manager import OrganizationManager
            
            org_manager = OrganizationManager(self.base_path)
            result = org_manager.optimize_disk_usage()
            
            return {
                'success': result.status.value == 'completed',
                'space_freed': result.total_space_freed,
                'operations': result.operations_performed,
                'errors': result.errors
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _maintenance_security_scan(self) -> Dict[str, Any]:
        """Tarefa de manutenção: verificação de segurança"""
        try:
            # Verificar componentes desatualizados com foco em segurança
            outdated = self.check_outdated_components()
            security_updates = [c for c in outdated.values() if c.get('security_update', False)]
            
            # Verificar integridade de backups
            backups = self.list_available_backups()
            invalid_backups = [b for b in backups if not self.validate_backup(b.id)]
            
            return {
                'success': True,
                'security_updates_available': len(security_updates),
                'invalid_backups': len(invalid_backups),
                'recommendations': [
                    f"{len(security_updates)} atualizações de segurança disponíveis" if security_updates else "Nenhuma atualização de segurança pendente",
                    f"{len(invalid_backups)} backups corrompidos encontrados" if invalid_backups else "Todos os backups estão íntegros"
                ]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_maintenance_recommendations(self, maintenance_result: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nos resultados da manutenção"""
        recommendations = []
        
        try:
            successful_tasks = len(maintenance_result.get('tasks_executed', []))
            failed_tasks = len(maintenance_result.get('tasks_failed', []))
            
            if failed_tasks == 0:
                recommendations.append("✅ Todas as tarefas de manutenção foram concluídas com sucesso")
            else:
                recommendations.append(f"⚠️ {failed_tasks} tarefas falharam - verifique os logs para detalhes")
            
            if successful_tasks > 0:
                recommendations.append(f"🔧 {successful_tasks} tarefas de manutenção executadas")
            
            # Recomendações baseadas na duração
            total_duration = maintenance_result.get('total_duration', 0)
            if total_duration > 600:  # > 10 minutos
                recommendations.append("⏱️ Manutenção demorou mais que o esperado - considere otimizações")
            
            recommendations.append("📅 Próxima manutenção recomendada em 1 semana")
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações de manutenção: {e}")
        
        return recommendations

    def _restore_configuration_backup(self, backup_info: BackupInfo, result: RestoreResult) -> bool:
        """Restaura backup das configurações"""
        try:
            config_backup_path = Path(backup_info.path) / "config"
            
            if not config_backup_path.exists():
                result.errors.append("Backup de configuração não encontrado")
                return False
            
            restored_files = []
            
            # Restaurar arquivos de configuração
            for config_file in config_backup_path.iterdir():
                if config_file.is_file():
                    # Determinar destino baseado no nome do arquivo
                    if config_file.name == "components.yaml":
                        target_path = self.base_path / "env_dev" / "components.yaml"
                    elif config_file.name == "settings.yaml":
                        target_path = self.base_path / "config" / "settings.yaml"
                    elif config_file.name == "component_state.json":
                        target_path = self.base_path / "component_state.json"
                    else:
                        continue
                    
                    # Criar backup do arquivo atual
                    if target_path.exists():
                        backup_current = target_path.with_suffix(f"{target_path.suffix}.restore_backup")
                        shutil.copy2(target_path, backup_current)
                    
                    # Restaurar arquivo
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(config_file, target_path)
                    restored_files.append(str(target_path))
            
            result.restored_files = restored_files
            result.message = f"Configurações restauradas: {len(restored_files)} arquivos"
            return len(restored_files) > 0
            
        except Exception as e:
            result.errors.append(f"Erro ao restaurar configurações: {str(e)}")
            return False
    
    def _restore_component_state_backup(self, backup_info: BackupInfo, result: RestoreResult) -> bool:
        """Restaura backup do estado dos componentes"""
        try:
            components_backup_path = Path(backup_info.path) / "components"
            
            if not components_backup_path.exists():
                result.errors.append("Backup do estado dos componentes não encontrado")
                return False
            
            restored_files = []
            
            # Restaurar estado dos componentes
            state_backup_file = components_backup_path / "component_state.json"
            if state_backup_file.exists():
                target_state_file = self.base_path / "component_state.json"
                
                # Backup do arquivo atual
                if target_state_file.exists():
                    backup_current = target_state_file.with_suffix(".json.restore_backup")
                    shutil.copy2(target_state_file, backup_current)
                
                shutil.copy2(state_backup_file, target_state_file)
                restored_files.append(str(target_state_file))
            
            # Restaurar logs se existirem
            logs_backup_path = components_backup_path / "logs"
            if logs_backup_path.exists():
                target_logs_path = self.base_path / "logs"
                
                # Backup dos logs atuais
                if target_logs_path.exists():
                    backup_logs_path = self.base_path / "logs.restore_backup"
                    if backup_logs_path.exists():
                        shutil.rmtree(backup_logs_path)
                    shutil.copytree(target_logs_path, backup_logs_path)
                    shutil.rmtree(target_logs_path)
                
                shutil.copytree(logs_backup_path, target_logs_path)
                restored_files.append(str(target_logs_path))
            
            result.restored_files = restored_files
            result.message = f"Estado dos componentes restaurado: {len(restored_files)} itens"
            return len(restored_files) > 0
            
        except Exception as e:
            result.errors.append(f"Erro ao restaurar estado dos componentes: {str(e)}")
            return False
    
    def _restore_system_state_backup(self, backup_info: BackupInfo, result: RestoreResult) -> bool:
        """Restaura backup completo do estado do sistema"""
        try:
            success = True
            all_restored_files = []
            
            # Restaurar configurações
            config_result = RestoreResult(backup_id=backup_info.id, status=RecoveryStatus.IN_PROGRESS, message="")
            if self._restore_configuration_backup(backup_info, config_result):
                all_restored_files.extend(config_result.restored_files)
            else:
                success = False
                result.errors.extend(config_result.errors)
            
            # Restaurar estado dos componentes
            component_result = RestoreResult(backup_id=backup_info.id, status=RecoveryStatus.IN_PROGRESS, message="")
            if self._restore_component_state_backup(backup_info, component_result):
                all_restored_files.extend(component_result.restored_files)
            else:
                success = False
                result.errors.extend(component_result.errors)
            
            result.restored_files = all_restored_files
            
            if success:
                result.message = f"Estado do sistema restaurado: {len(all_restored_files)} itens"
            else:
                result.message = "Restauração do estado do sistema concluída com erros"
            
            return success
            
        except Exception as e:
            result.errors.append(f"Erro ao restaurar estado do sistema: {str(e)}")
            return False
    
    # Métodos de validação de backup específicos
    
    def _validate_efi_backup(self, backup_path: Path) -> bool:
        """Valida backup da partição EFI"""
        try:
            efi_path = backup_path / "EFI"
            return efi_path.exists() and (efi_path / "BOOT").exists()
        except Exception:
            return False
    
    def _validate_configuration_backup(self, backup_path: Path) -> bool:
        """Valida backup de configuração"""
        try:
            config_path = backup_path / "config"
            return config_path.exists() and len(list(config_path.glob("*.yaml"))) > 0
        except Exception:
            return False
    
    def _validate_component_state_backup(self, backup_path: Path) -> bool:
        """Valida backup do estado dos componentes"""
        try:
            components_path = backup_path / "components"
            state_file = components_path / "component_state.json"
            return components_path.exists() and state_file.exists()
        except Exception:
            return False
    
    def _validate_system_state_backup(self, backup_path: Path) -> bool:
        """Valida backup do estado do sistema"""
        try:
            # Verificar se pelo menos um dos componentes principais existe
            has_config = (backup_path / "config").exists()
            has_components = (backup_path / "components").exists()
            has_system_info = (backup_path / "system_info.json").exists()
            
            return has_config or has_components or has_system_info
        except Exception:
            return False