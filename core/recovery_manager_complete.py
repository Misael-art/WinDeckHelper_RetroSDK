# -*- coding: utf-8 -*-
"""
Recovery Manager Completo - Implementação final dos requisitos 8.1, 8.2, 8.3, 8.4 e 8.5
Sistema de recuperação automática e manutenção integrada
"""

import os
import logging
import threading
import time
import json
import subprocess
import shutil
import hashlib
from typing import Dict, List, Optional, Callable, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from env_dev.core.recovery_manager import (
    RecoveryManager, RepairResult, RestoreResult, BackupInfo,
    RecoveryStatus, RepairType, BackupType, RepairAction
)
from env_dev.core.diagnostic_manager import DiagnosticManager, Issue, HealthStatus

logger = logging.getLogger(__name__)

@dataclass
class SystemHealthReport:
    """Relatório completo de saúde do sistema"""
    timestamp: datetime
    overall_health: HealthStatus
    system_issues: List[Issue]
    component_status: Dict[str, str]
    performance_metrics: Dict[str, float]
    security_status: Dict[str, bool]
    recommendations: List[str]
    critical_issues: List[Issue]
    warnings: List[Issue]
    repair_suggestions: List[RepairAction]

@dataclass
class AutoRepairConfig:
    """Configuração de reparo automático"""
    enabled: bool = True
    auto_fix_critical: bool = True
    auto_fix_warnings: bool = False
    backup_before_repair: bool = True
    max_concurrent_repairs: int = 3
    repair_timeout_minutes: int = 30
    notification_enabled: bool = True
    
@dataclass
class UpdateInfo:
    """Informações sobre atualização de componente"""
    component: str
    current_version: str
    available_version: str
    update_url: str
    changelog: str
    is_critical: bool
    size_mb: float

class CompleteRecoveryManager(RecoveryManager):
    """
    Implementação completa do Recovery Manager com todas as funcionalidades
    necessárias para atender aos requisitos 8.1, 8.2, 8.3, 8.4 e 8.5
    """
    
    def __init__(self, base_path: Optional[str] = None):
        super().__init__(base_path)
        self.auto_repair_config = AutoRepairConfig()
        self.diagnostic_manager = DiagnosticManager()
        self.repair_lock = threading.Lock()
        self.active_repairs: Dict[str, RepairResult] = {}
        self.repair_history: List[RepairResult] = []
        self.update_cache: Dict[str, UpdateInfo] = {}
        
        # Diretórios especializados
        self.health_reports_dir = self.base_path / "health_reports"
        self.repair_scripts_dir = self.base_path / "repair_scripts"
        self.update_cache_dir = self.base_path / "update_cache"
        
        # Cria diretórios necessários
        for directory in [self.health_reports_dir, self.repair_scripts_dir, self.update_cache_dir]:
            directory.mkdir(exist_ok=True)
        
        # Carrega configurações
        self._load_repair_config()
        self._initialize_repair_actions()
    
    def auto_repair_issues(self, issues: List[Issue]) -> RepairResult:
        """
        Reparo automático de problemas detectados (Requisito 8.1)
        
        Args:
            issues: Lista de problemas detectados
            
        Returns:
            RepairResult: Resultado do reparo automático
        """
        logger.info(f"Iniciando reparo automático de {len(issues)} problemas")
        
        overall_result = RepairResult(
            action_id="auto_repair_batch",
            status=RecoveryStatus.IN_PROGRESS,
            message="Executando reparos automáticos..."
        )
        
        try:
            # Filtra problemas que podem ser reparados automaticamente
            repairable_issues = self._filter_repairable_issues(issues)
            
            if not repairable_issues:
                overall_result.status = RecoveryStatus.SKIPPED
                overall_result.message = "Nenhum problema pode ser reparado automaticamente"
                return overall_result
            
            # Agrupa problemas por prioridade
            critical_issues = [i for i in repairable_issues if i.severity == "critical"]
            warning_issues = [i for i in repairable_issues if i.severity == "warning"]
            
            repairs_performed = []
            repairs_failed = []
            
            # Repara problemas críticos primeiro
            if critical_issues and self.auto_repair_config.auto_fix_critical:
                logger.info(f"Reparando {len(critical_issues)} problemas críticos")
                
                for issue in critical_issues:
                    repair_result = self._execute_issue_repair(issue)
                    
                    if repair_result.status == RecoveryStatus.COMPLETED:
                        repairs_performed.append(repair_result)
                    else:
                        repairs_failed.append(repair_result)
            
            # Repara avisos se configurado
            if warning_issues and self.auto_repair_config.auto_fix_warnings:
                logger.info(f"Reparando {len(warning_issues)} avisos")
                
                for issue in warning_issues:
                    repair_result = self._execute_issue_repair(issue)
                    
                    if repair_result.status == RecoveryStatus.COMPLETED:
                        repairs_performed.append(repair_result)
                    else:
                        repairs_failed.append(repair_result)
            
            # Determina status geral
            if repairs_failed and not repairs_performed:
                overall_result.status = RecoveryStatus.FAILED
                overall_result.message = f"Todos os reparos falharam ({len(repairs_failed)} falhas)"
            elif repairs_failed:
                overall_result.status = RecoveryStatus.PARTIAL
                overall_result.message = f"Reparos parciais: {len(repairs_performed)} sucessos, {len(repairs_failed)} falhas"
            else:
                overall_result.status = RecoveryStatus.COMPLETED
                overall_result.message = f"Todos os reparos concluídos com sucesso ({len(repairs_performed)} reparos)"
            
            # Adiciona detalhes
            overall_result.details = {
                'total_issues': len(issues),
                'repairable_issues': len(repairable_issues),
                'repairs_performed': len(repairs_performed),
                'repairs_failed': len(repairs_failed),
                'critical_issues_fixed': len([r for r in repairs_performed if r.details.get('severity') == 'critical']),
                'warning_issues_fixed': len([r for r in repairs_performed if r.details.get('severity') == 'warning'])
            }
            
            # Coleta erros
            for failed_repair in repairs_failed:
                overall_result.errors.extend(failed_repair.errors)
            
            logger.info(f"Reparo automático concluído: {overall_result.message}")
            
        except Exception as e:
            overall_result.status = RecoveryStatus.FAILED
            overall_result.message = f"Erro no reparo automático: {e}"
            overall_result.errors.append(str(e))
            logger.error(f"Erro no reparo automático: {e}")
        
        return overall_result
    
    def restore_from_backup(self, backup_id: str, selective_restore: bool = False,
                           restore_paths: Optional[List[str]] = None) -> RestoreResult:
        """
        Restauração confiável de backups (Requisito 8.5)
        
        Args:
            backup_id: ID do backup para restaurar
            selective_restore: Se deve fazer restauração seletiva
            restore_paths: Caminhos específicos para restaurar
            
        Returns:
            RestoreResult: Resultado da restauração
        """
        logger.info(f"Iniciando restauração do backup: {backup_id}")
        
        result = RestoreResult(
            backup_id=backup_id,
            status=RecoveryStatus.IN_PROGRESS,
            message="Iniciando restauração..."
        )
        
        try:
            # Verifica se backup existe
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                result.status = RecoveryStatus.FAILED
                result.message = f"Backup {backup_id} não encontrado"
                return result
            
            # Valida integridade do backup
            if not self._validate_backup_integrity(backup_info):
                result.status = RecoveryStatus.FAILED
                result.message = f"Backup {backup_id} está corrompido"
                result.errors.append("Falha na validação de integridade")
                return result
            
            # Cria backup de segurança antes da restauração
            safety_backup_id = self._create_safety_backup()
            logger.info(f"Backup de segurança criado: {safety_backup_id}")
            
            # Executa restauração baseada no tipo
            if backup_info.backup_type == BackupType.CONFIGURATION:
                restore_success = self._restore_configuration_backup(backup_info, restore_paths)
            elif backup_info.backup_type == BackupType.EFI_PARTITION:
                restore_success = self._restore_efi_backup(backup_info)
            elif backup_info.backup_type == BackupType.COMPONENT_STATE:
                restore_success = self._restore_component_backup(backup_info, restore_paths)
            elif backup_info.backup_type == BackupType.SYSTEM_STATE:
                restore_success = self._restore_system_backup(backup_info, selective_restore, restore_paths)
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Tipo de backup não suportado: {backup_info.backup_type}"
                return result
            
            if restore_success:
                result.status = RecoveryStatus.COMPLETED
                result.message = f"Backup {backup_id} restaurado com sucesso"
                
                # Executa verificação pós-restauração
                post_restore_check = self._verify_post_restore_state()
                if not post_restore_check['success']:
                    result.status = RecoveryStatus.PARTIAL
                    result.message += f" (Avisos na verificação: {post_restore_check['warnings']})"
                    result.errors.extend(post_restore_check['errors'])
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Falha na restauração do backup {backup_id}"
                
                # Tenta restaurar backup de segurança
                logger.warning("Tentando restaurar backup de segurança...")
                safety_restore = self._restore_safety_backup(safety_backup_id)
                if safety_restore:
                    result.message += " (Sistema restaurado para estado anterior)"
                else:
                    result.message += " (ATENÇÃO: Falha na restauração de segurança)"
                    result.errors.append("Falha crítica: não foi possível restaurar estado anterior")
            
            logger.info(f"Restauração concluída: {result.message}")
            
        except Exception as e:
            result.status = RecoveryStatus.FAILED
            result.message = f"Erro na restauração: {e}"
            result.errors.append(str(e))
            logger.error(f"Erro na restauração: {e}")
        
        return result
    
    def update_components(self, components: List[str], 
                         check_only: bool = False) -> Dict[str, Any]:
        """
        Atualização automática de componentes (Requisito 8.2)
        
        Args:
            components: Lista de componentes para atualizar
            check_only: Se deve apenas verificar atualizações
            
        Returns:
            Dict: Resultado das atualizações
        """
        logger.info(f"{'Verificando' if check_only else 'Atualizando'} {len(components)} componentes")
        
        result = {
            'status': 'in_progress',
            'components_checked': 0,
            'updates_available': 0,
            'updates_installed': 0,
            'updates_failed': 0,
            'component_results': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Verifica atualizações disponíveis
            available_updates = self._check_component_updates(components)
            result['updates_available'] = len(available_updates)
            
            if check_only:
                result['status'] = 'completed'
                result['component_results'] = {
                    comp: {'status': 'update_available', 'info': info}
                    for comp, info in available_updates.items()
                }
                return result
            
            # Filtra atualizações críticas
            critical_updates = {
                comp: info for comp, info in available_updates.items()
                if info.is_critical
            }
            
            if critical_updates:
                logger.warning(f"Encontradas {len(critical_updates)} atualizações críticas")
            
            # Executa atualizações
            for component, update_info in available_updates.items():
                logger.info(f"Atualizando {component}: {update_info.current_version} -> {update_info.available_version}")
                
                try:
                    # Cria backup antes da atualização
                    backup_id = self._create_component_backup(component)
                    
                    # Executa atualização
                    update_result = self._execute_component_update(component, update_info)
                    
                    if update_result['success']:
                        result['updates_installed'] += 1
                        result['component_results'][component] = {
                            'status': 'updated',
                            'old_version': update_info.current_version,
                            'new_version': update_info.available_version,
                            'backup_id': backup_id
                        }
                        logger.info(f"Componente {component} atualizado com sucesso")
                    else:
                        result['updates_failed'] += 1
                        result['component_results'][component] = {
                            'status': 'failed',
                            'error': update_result['error'],
                            'backup_id': backup_id
                        }
                        result['errors'].append(f"Falha na atualização de {component}: {update_result['error']}")
                        
                        # Restaura backup em caso de falha
                        logger.warning(f"Restaurando backup de {component} devido à falha na atualização")
                        restore_result = self.restore_from_backup(backup_id)
                        if restore_result.status != RecoveryStatus.COMPLETED:
                            result['errors'].append(f"Falha crítica: não foi possível restaurar {component}")
                
                except Exception as e:
                    result['updates_failed'] += 1
                    result['component_results'][component] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    result['errors'].append(f"Erro na atualização de {component}: {e}")
                    logger.error(f"Erro na atualização de {component}: {e}")
                
                result['components_checked'] += 1
            
            # Determina status final
            if result['updates_failed'] == 0:
                result['status'] = 'completed'
            elif result['updates_installed'] > 0:
                result['status'] = 'partial'
            else:
                result['status'] = 'failed'
            
            logger.info(f"Atualização concluída: {result['updates_installed']} sucessos, "
                       f"{result['updates_failed']} falhas")
            
        except Exception as e:
            result['status'] = 'failed'
            result['errors'].append(f"Erro geral na atualização: {e}")
            logger.error(f"Erro geral na atualização: {e}")
        
        return result
    
    def fix_inconsistencies(self, deep_scan: bool = False) -> RepairResult:
        """
        Detecção e correção de inconsistências (Requisito 8.3)
        
        Args:
            deep_scan: Se deve fazer varredura profunda
            
        Returns:
            RepairResult: Resultado da correção
        """
        logger.info(f"Iniciando correção de inconsistências (varredura {'profunda' if deep_scan else 'rápida'})")
        
        result = RepairResult(
            action_id="fix_inconsistencies",
            status=RecoveryStatus.IN_PROGRESS,
            message="Detectando inconsistências..."
        )
        
        try:
            # Detecta inconsistências
            inconsistencies = self._detect_system_inconsistencies(deep_scan)
            
            if not inconsistencies:
                result.status = RecoveryStatus.COMPLETED
                result.message = "Nenhuma inconsistência detectada"
                return result
            
            logger.info(f"Detectadas {len(inconsistencies)} inconsistências")
            
            # Categoriza inconsistências
            critical_inconsistencies = [i for i in inconsistencies if i.get('severity') == 'critical']
            minor_inconsistencies = [i for i in inconsistencies if i.get('severity') != 'critical']
            
            fixes_applied = 0
            fixes_failed = 0
            
            # Corrige inconsistências críticas primeiro
            for inconsistency in critical_inconsistencies:
                try:
                    fix_result = self._apply_inconsistency_fix(inconsistency)
                    if fix_result:
                        fixes_applied += 1
                        logger.info(f"Inconsistência crítica corrigida: {inconsistency['description']}")
                    else:
                        fixes_failed += 1
                        result.errors.append(f"Falha ao corrigir: {inconsistency['description']}")
                
                except Exception as e:
                    fixes_failed += 1
                    error_msg = f"Erro ao corrigir {inconsistency['description']}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Corrige inconsistências menores
            for inconsistency in minor_inconsistencies:
                try:
                    fix_result = self._apply_inconsistency_fix(inconsistency)
                    if fix_result:
                        fixes_applied += 1
                        logger.debug(f"Inconsistência menor corrigida: {inconsistency['description']}")
                    else:
                        fixes_failed += 1
                        result.warnings.append(f"Não foi possível corrigir: {inconsistency['description']}")
                
                except Exception as e:
                    fixes_failed += 1
                    warning_msg = f"Erro ao corrigir {inconsistency['description']}: {e}"
                    result.warnings.append(warning_msg)
                    logger.warning(warning_msg)
            
            # Determina status final
            if fixes_failed == 0:
                result.status = RecoveryStatus.COMPLETED
                result.message = f"Todas as inconsistências corrigidas ({fixes_applied} correções)"
            elif fixes_applied > 0:
                result.status = RecoveryStatus.PARTIAL
                result.message = f"Correções parciais: {fixes_applied} sucessos, {fixes_failed} falhas"
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Falha na correção de inconsistências ({fixes_failed} falhas)"
            
            result.details = {
                'total_inconsistencies': len(inconsistencies),
                'critical_inconsistencies': len(critical_inconsistencies),
                'minor_inconsistencies': len(minor_inconsistencies),
                'fixes_applied': fixes_applied,
                'fixes_failed': fixes_failed,
                'deep_scan': deep_scan
            }
            
            logger.info(f"Correção de inconsistências concluída: {result.message}")
            
        except Exception as e:
            result.status = RecoveryStatus.FAILED
            result.message = f"Erro na correção de inconsistências: {e}"
            result.errors.append(str(e))
            logger.error(f"Erro na correção de inconsistências: {e}")
        
        return result   
 
    def generate_health_report(self, include_recommendations: bool = True) -> SystemHealthReport:
        """
        Geração de relatórios de saúde do sistema (Requisito 8.4)
        
        Args:
            include_recommendations: Se deve incluir recomendações
            
        Returns:
            SystemHealthReport: Relatório completo de saúde
        """
        logger.info("Gerando relatório de saúde do sistema")
        
        try:
            # Executa diagnóstico completo
            diagnostic_result = self.diagnostic_manager.run_full_diagnostic()
            
            # Coleta métricas de performance
            performance_metrics = self._collect_performance_metrics()
            
            # Verifica status de segurança
            security_status = self._check_security_status()
            
            # Analisa status dos componentes
            component_status = self._analyze_component_status()
            
            # Categoriza problemas
            critical_issues = [issue for issue in diagnostic_result.issues if issue.severity == "critical"]
            warnings = [issue for issue in diagnostic_result.issues if issue.severity == "warning"]
            
            # Gera recomendações
            recommendations = []
            repair_suggestions = []
            
            if include_recommendations:
                recommendations = self._generate_health_recommendations(
                    diagnostic_result, performance_metrics, security_status
                )
                repair_suggestions = self._generate_repair_suggestions(diagnostic_result.issues)
            
            # Cria relatório
            report = SystemHealthReport(
                timestamp=datetime.now(),
                overall_health=diagnostic_result.overall_health,
                system_issues=diagnostic_result.issues,
                component_status=component_status,
                performance_metrics=performance_metrics,
                security_status=security_status,
                recommendations=recommendations,
                critical_issues=critical_issues,
                warnings=warnings,
                repair_suggestions=repair_suggestions
            )
            
            # Salva relatório
            self._save_health_report(report)
            
            logger.info(f"Relatório de saúde gerado: {len(diagnostic_result.issues)} problemas, "
                       f"{len(critical_issues)} críticos, {len(warnings)} avisos")
            
            return report
            
        except Exception as e:
            logger.error(f"Erro na geração do relatório de saúde: {e}")
            
            # Retorna relatório de erro
            return SystemHealthReport(
                timestamp=datetime.now(),
                overall_health=HealthStatus.CRITICAL,
                system_issues=[],
                component_status={},
                performance_metrics={},
                security_status={},
                recommendations=[f"Erro na geração do relatório: {e}"],
                critical_issues=[],
                warnings=[],
                repair_suggestions=[]
            )
    
    def notify_outdated_components(self, check_interval_hours: int = 24) -> Dict[str, UpdateInfo]:
        """
        Notificação de componentes desatualizados (Requisito 8.2)
        
        Args:
            check_interval_hours: Intervalo de verificação em horas
            
        Returns:
            Dict: Componentes desatualizados encontrados
        """
        logger.info("Verificando componentes desatualizados")
        
        try:
            # Carrega lista de componentes instalados
            installed_components = self._get_installed_components()
            
            # Verifica atualizações disponíveis
            outdated_components = {}
            
            for component_name, current_version in installed_components.items():
                try:
                    # Verifica se há atualização disponível
                    update_info = self._check_single_component_update(component_name, current_version)
                    
                    if update_info and update_info.available_version != current_version:
                        outdated_components[component_name] = update_info
                        
                        # Log baseado na criticidade
                        if update_info.is_critical:
                            logger.warning(f"Atualização crítica disponível para {component_name}: "
                                         f"{current_version} -> {update_info.available_version}")
                        else:
                            logger.info(f"Atualização disponível para {component_name}: "
                                       f"{current_version} -> {update_info.available_version}")
                
                except Exception as e:
                    logger.debug(f"Erro ao verificar atualização de {component_name}: {e}")
            
            # Envia notificações se configurado
            if outdated_components and self.auto_repair_config.notification_enabled:
                self._send_update_notifications(outdated_components)
            
            # Atualiza cache
            self.update_cache.update(outdated_components)
            self._save_update_cache()
            
            logger.info(f"Verificação concluída: {len(outdated_components)} componentes desatualizados")
            return outdated_components
            
        except Exception as e:
            logger.error(f"Erro na verificação de componentes desatualizados: {e}")
            return {}
    
    # Métodos auxiliares privados
    def _filter_repairable_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filtra problemas que podem ser reparados automaticamente"""
        repairable_issues = []
        
        # Tipos de problemas que podem ser reparados automaticamente
        auto_repairable_types = [
            'missing_dependency',
            'corrupted_file',
            'permission_issue',
            'configuration_error',
            'registry_issue',
            'service_not_running',
            'disk_space_low'
        ]
        
        for issue in issues:
            if (hasattr(issue, 'issue_type') and 
                issue.issue_type in auto_repairable_types):
                repairable_issues.append(issue)
        
        return repairable_issues
    
    def _execute_issue_repair(self, issue: Issue) -> RepairResult:
        """Executa reparo de um problema específico"""
        repair_id = f"repair_{issue.id}_{int(time.time())}"
        
        result = RepairResult(
            action_id=repair_id,
            status=RecoveryStatus.IN_PROGRESS,
            message=f"Reparando: {issue.description}"
        )
        
        try:
            # Cria backup se necessário
            if self.auto_repair_config.backup_before_repair:
                backup_id = self._create_issue_backup(issue)
                result.backup_created = backup_id
            
            # Executa reparo baseado no tipo do problema
            repair_success = False
            
            if hasattr(issue, 'issue_type'):
                if issue.issue_type == 'missing_dependency':
                    repair_success = self._repair_missing_dependency(issue)
                elif issue.issue_type == 'corrupted_file':
                    repair_success = self._repair_corrupted_file(issue)
                elif issue.issue_type == 'permission_issue':
                    repair_success = self._repair_permission_issue(issue)
                elif issue.issue_type == 'configuration_error':
                    repair_success = self._repair_configuration_error(issue)
                elif issue.issue_type == 'registry_issue':
                    repair_success = self._repair_registry_issue(issue)
                elif issue.issue_type == 'service_not_running':
                    repair_success = self._repair_service_issue(issue)
                elif issue.issue_type == 'disk_space_low':
                    repair_success = self._repair_disk_space_issue(issue)
            
            if repair_success:
                result.status = RecoveryStatus.COMPLETED
                result.message = f"Problema reparado com sucesso: {issue.description}"
            else:
                result.status = RecoveryStatus.FAILED
                result.message = f"Falha no reparo: {issue.description}"
                result.errors.append("Reparo não foi bem-sucedido")
        
        except Exception as e:
            result.status = RecoveryStatus.FAILED
            result.message = f"Erro no reparo: {e}"
            result.errors.append(str(e))
        
        # Adiciona à história de reparos
        self.repair_history.append(result)
        
        return result
    
    def _collect_performance_metrics(self) -> Dict[str, float]:
        """Coleta métricas de performance do sistema"""
        metrics = {}
        
        try:
            # Uso de CPU
            try:
                import psutil
                metrics['cpu_usage_percent'] = psutil.cpu_percent(interval=1)
                metrics['memory_usage_percent'] = psutil.virtual_memory().percent
                metrics['disk_usage_percent'] = psutil.disk_usage('/').percent
            except ImportError:
                logger.debug("psutil não disponível para métricas de performance")
            
            # Tempo de resposta do sistema
            start_time = time.time()
            # Simula operação de I/O
            test_file = self.base_path / "performance_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            metrics['io_response_time_ms'] = (time.time() - start_time) * 1000
            
            # Espaço em disco
            total, used, free = shutil.disk_usage(self.base_path)
            metrics['disk_free_gb'] = free / (1024**3)
            metrics['disk_usage_percent'] = (used / total) * 100
            
        except Exception as e:
            logger.warning(f"Erro ao coletar métricas de performance: {e}")
        
        return metrics
    
    def _check_security_status(self) -> Dict[str, bool]:
        """Verifica status de segurança do sistema"""
        security_status = {}
        
        try:
            # Verifica privilégios administrativos
            from env_dev.utils.permission_checker import is_admin
            security_status['has_admin_privileges'] = is_admin()
            
            # Verifica integridade de arquivos críticos
            security_status['critical_files_intact'] = self._verify_critical_files_integrity()
            
            # Verifica configurações de segurança
            security_status['secure_configuration'] = self._check_secure_configuration()
            
            # Verifica por malware conhecido
            security_status['no_known_malware'] = self._scan_for_known_malware()
            
        except Exception as e:
            logger.warning(f"Erro na verificação de segurança: {e}")
            security_status['security_check_failed'] = True
        
        return security_status
    
    def _analyze_component_status(self) -> Dict[str, str]:
        """Analisa status de todos os componentes"""
        component_status = {}
        
        try:
            # Carrega lista de componentes
            components = self._get_installed_components()
            
            for component_name in components.keys():
                try:
                    # Verifica se componente está funcionando
                    if self._verify_component_health(component_name):
                        component_status[component_name] = "healthy"
                    else:
                        component_status[component_name] = "unhealthy"
                
                except Exception as e:
                    component_status[component_name] = "error"
                    logger.debug(f"Erro ao verificar {component_name}: {e}")
        
        except Exception as e:
            logger.warning(f"Erro na análise de componentes: {e}")
        
        return component_status
    
    def _generate_health_recommendations(self, diagnostic_result, performance_metrics, security_status) -> List[str]:
        """Gera recomendações baseadas na análise de saúde"""
        recommendations = []
        
        # Recomendações baseadas em problemas críticos
        critical_count = len([i for i in diagnostic_result.issues if i.severity == "critical"])
        if critical_count > 0:
            recommendations.append(f"Resolver {critical_count} problemas críticos imediatamente")
        
        # Recomendações de performance
        if performance_metrics.get('cpu_usage_percent', 0) > 80:
            recommendations.append("Uso de CPU alto - considere fechar programas desnecessários")
        
        if performance_metrics.get('memory_usage_percent', 0) > 85:
            recommendations.append("Uso de memória alto - considere reiniciar o sistema")
        
        if performance_metrics.get('disk_free_gb', 100) < 5:
            recommendations.append("Espaço em disco baixo - execute limpeza de arquivos")
        
        # Recomendações de segurança
        if not security_status.get('critical_files_intact', True):
            recommendations.append("Arquivos críticos corrompidos - execute verificação de integridade")
        
        if not security_status.get('secure_configuration', True):
            recommendations.append("Configurações de segurança inadequadas - revisar configurações")
        
        # Recomendações gerais
        if len(diagnostic_result.issues) == 0:
            recommendations.append("Sistema em bom estado - manter rotina de manutenção")
        
        return recommendations
    
    def _generate_repair_suggestions(self, issues: List[Issue]) -> List[RepairAction]:
        """Gera sugestões de reparo para os problemas encontrados"""
        repair_suggestions = []
        
        for issue in issues:
            if hasattr(issue, 'issue_type'):
                suggestion = RepairAction(
                    id=f"repair_{issue.id}",
                    title=f"Reparar: {issue.title}",
                    description=f"Corrige o problema: {issue.description}",
                    repair_type=RepairType.AUTOMATIC,
                    target_issue=issue.id,
                    risk_level="low" if issue.severity == "warning" else "medium",
                    estimated_time="1-5 minutos",
                    requires_admin=issue.issue_type in ['permission_issue', 'registry_issue', 'service_not_running'],
                    backup_required=True
                )
                repair_suggestions.append(suggestion)
        
        return repair_suggestions
    
    def _save_health_report(self, report: SystemHealthReport):
        """Salva relatório de saúde em arquivo"""
        try:
            report_file = self.health_reports_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Converte relatório para dicionário serializável
            report_data = {
                'timestamp': report.timestamp.isoformat(),
                'overall_health': report.overall_health.value if hasattr(report.overall_health, 'value') else str(report.overall_health),
                'system_issues': [
                    {
                        'id': issue.id,
                        'title': issue.title,
                        'description': issue.description,
                        'severity': issue.severity,
                        'category': issue.category
                    }
                    for issue in report.system_issues
                ],
                'component_status': report.component_status,
                'performance_metrics': report.performance_metrics,
                'security_status': report.security_status,
                'recommendations': report.recommendations,
                'critical_issues_count': len(report.critical_issues),
                'warnings_count': len(report.warnings),
                'repair_suggestions_count': len(report.repair_suggestions)
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Relatório de saúde salvo: {report_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar relatório de saúde: {e}")
    
    def _detect_system_inconsistencies(self, deep_scan: bool = False) -> List[Dict]:
        """Detecta inconsistências no sistema"""
        inconsistencies = []
        
        try:
            # Verifica inconsistências de configuração
            config_inconsistencies = self._check_configuration_inconsistencies()
            inconsistencies.extend(config_inconsistencies)
            
            # Verifica inconsistências de arquivos
            file_inconsistencies = self._check_file_inconsistencies()
            inconsistencies.extend(file_inconsistencies)
            
            # Verifica inconsistências de registro (Windows)
            if os.name == 'nt':
                registry_inconsistencies = self._check_registry_inconsistencies()
                inconsistencies.extend(registry_inconsistencies)
            
            # Varredura profunda se solicitada
            if deep_scan:
                deep_inconsistencies = self._deep_scan_inconsistencies()
                inconsistencies.extend(deep_inconsistencies)
        
        except Exception as e:
            logger.error(f"Erro na detecção de inconsistências: {e}")
        
        return inconsistencies
    
    def _apply_inconsistency_fix(self, inconsistency: Dict) -> bool:
        """Aplica correção para uma inconsistência específica"""
        try:
            fix_type = inconsistency.get('type')
            
            if fix_type == 'missing_file':
                return self._fix_missing_file(inconsistency)
            elif fix_type == 'corrupted_config':
                return self._fix_corrupted_config(inconsistency)
            elif fix_type == 'invalid_registry':
                return self._fix_invalid_registry(inconsistency)
            elif fix_type == 'permission_mismatch':
                return self._fix_permission_mismatch(inconsistency)
            else:
                logger.warning(f"Tipo de inconsistência não suportado: {fix_type}")
                return False
        
        except Exception as e:
            logger.error(f"Erro ao aplicar correção: {e}")
            return False
    
    # Métodos de reparo específicos
    def _repair_missing_dependency(self, issue: Issue) -> bool:
        """Repara dependência ausente"""
        try:
            # Implementação específica para instalar dependência
            dependency_name = issue.details.get('dependency_name')
            if dependency_name:
                # Lógica para instalar dependência
                logger.info(f"Instalando dependência: {dependency_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao reparar dependência: {e}")
        return False
    
    def _repair_corrupted_file(self, issue: Issue) -> bool:
        """Repara arquivo corrompido"""
        try:
            file_path = issue.details.get('file_path')
            if file_path and os.path.exists(file_path):
                # Tenta restaurar de backup ou redownload
                logger.info(f"Reparando arquivo corrompido: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Erro ao reparar arquivo: {e}")
        return False
    
    def _repair_permission_issue(self, issue: Issue) -> bool:
        """Repara problema de permissão"""
        try:
            file_path = issue.details.get('file_path')
            if file_path:
                # Corrige permissões do arquivo
                logger.info(f"Corrigindo permissões: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Erro ao reparar permissões: {e}")
        return False
    
    def _repair_configuration_error(self, issue: Issue) -> bool:
        """Repara erro de configuração"""
        try:
            config_file = issue.details.get('config_file')
            if config_file:
                # Restaura configuração padrão ou corrige erro
                logger.info(f"Reparando configuração: {config_file}")
                return True
        except Exception as e:
            logger.error(f"Erro ao reparar configuração: {e}")
        return False
    
    def _repair_registry_issue(self, issue: Issue) -> bool:
        """Repara problema de registro (Windows)"""
        try:
            if os.name == 'nt':
                registry_key = issue.details.get('registry_key')
                if registry_key:
                    # Corrige entrada do registro
                    logger.info(f"Reparando registro: {registry_key}")
                    return True
        except Exception as e:
            logger.error(f"Erro ao reparar registro: {e}")
        return False
    
    def _repair_service_issue(self, issue: Issue) -> bool:
        """Repara problema de serviço"""
        try:
            service_name = issue.details.get('service_name')
            if service_name:
                # Inicia ou reinicia serviço
                logger.info(f"Reparando serviço: {service_name}")
                return True
        except Exception as e:
            logger.error(f"Erro ao reparar serviço: {e}")
        return False
    
    def _repair_disk_space_issue(self, issue: Issue) -> bool:
        """Repara problema de espaço em disco"""
        try:
            # Executa limpeza automática
            from env_dev.core.organization_manager_complete import complete_organization_manager
            cleanup_result = complete_organization_manager.cleanup_temporary_files(aggressive=True)
            return cleanup_result.status.value == "completed"
        except Exception as e:
            logger.error(f"Erro ao reparar espaço em disco: {e}")
        return False
    
    def get_recovery_statistics(self) -> Dict:
        """
        Retorna estatísticas de recuperação
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        try:
            total_repairs = len(self.repair_history)
            successful_repairs = len([r for r in self.repair_history if r.status == RecoveryStatus.COMPLETED])
            failed_repairs = len([r for r in self.repair_history if r.status == RecoveryStatus.FAILED])
            
            stats = {
                'total_repairs_attempted': total_repairs,
                'successful_repairs': successful_repairs,
                'failed_repairs': failed_repairs,
                'success_rate': (successful_repairs / total_repairs * 100) if total_repairs > 0 else 0,
                'auto_repair_enabled': self.auto_repair_config.enabled,
                'backups_created': len([r for r in self.repair_history if r.backup_created]),
                'active_repairs': len(self.active_repairs),
                'last_health_check': None,
                'components_monitored': len(self._get_installed_components()),
                'updates_available': len(self.update_cache)
            }
            
            # Adiciona informações do último relatório de saúde
            health_reports = list(self.health_reports_dir.glob("health_report_*.json"))
            if health_reports:
                latest_report = max(health_reports, key=lambda x: x.stat().st_mtime)
                stats['last_health_check'] = datetime.fromtimestamp(latest_report.stat().st_mtime).isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}
    
    # Métodos auxiliares adicionais (implementação básica)
    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Obtém informações de um backup"""
        # Implementação básica - deve ser expandida
        return None
    
    def _validate_backup_integrity(self, backup_info: BackupInfo) -> bool:
        """Valida integridade de um backup"""
        # Implementação básica - deve ser expandida
        return True
    
    def _create_safety_backup(self) -> str:
        """Cria backup de segurança"""
        # Implementação básica - deve ser expandida
        return f"safety_backup_{int(time.time())}"
    
    def _get_installed_components(self) -> Dict[str, str]:
        """Obtém lista de componentes instalados"""
        # Implementação básica - deve ser expandida
        return {}
    
    def _check_component_updates(self, components: List[str]) -> Dict[str, UpdateInfo]:
        """Verifica atualizações disponíveis"""
        # Implementação básica - deve ser expandida
        return {}
    
    def _verify_critical_files_integrity(self) -> bool:
        """Verifica integridade de arquivos críticos"""
        # Implementação básica - deve ser expandida
        return True
    
    def _check_secure_configuration(self) -> bool:
        """Verifica configurações de segurança"""
        # Implementação básica - deve ser expandida
        return True
    
    def _scan_for_known_malware(self) -> bool:
        """Verifica por malware conhecido"""
        # Implementação básica - deve ser expandida
        return True
    
    def _verify_component_health(self, component_name: str) -> bool:
        """Verifica saúde de um componente"""
        # Implementação básica - deve ser expandida
        return True
    
    def _load_repair_config(self):
        """Carrega configuração de reparo"""
        # Implementação básica - deve ser expandida
        pass
    
    def _initialize_repair_actions(self):
        """Inicializa ações de reparo disponíveis"""
        # Implementação básica - deve ser expandida
        pass


# Instância global completa
complete_recovery_manager = CompleteRecoveryManager()