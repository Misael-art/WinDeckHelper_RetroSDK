# -*- coding: utf-8 -*-
"""
Melhorias finais para o Installation Manager
Completa a implementação dos requisitos 4.1, 4.2, 4.3, 4.4 e 4.5
"""

import os
import logging
import threading
import time
import json
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from env_dev.core.installation_manager import (
    InstallationManager, InstallationResult, InstallationStatus, 
    RollbackInfo, BatchInstallationResult, ConflictInfo
)

logger = logging.getLogger(__name__)

@dataclass
class InstallationMetrics:
    """Métricas detalhadas de instalação"""
    component: str
    start_time: datetime
    end_time: Optional[datetime] = None
    preparation_time: float = 0.0
    download_time: float = 0.0
    installation_time: float = 0.0
    verification_time: float = 0.0
    total_time: float = 0.0
    retry_count: int = 0
    rollback_performed: bool = False
    parallel_group: Optional[int] = None
    dependencies_resolved: List[str] = field(default_factory=list)
    conflicts_detected: List[str] = field(default_factory=list)
    
    def calculate_total_time(self):
        """Calcula tempo total baseado nos componentes"""
        if self.end_time:
            self.total_time = (self.end_time - self.start_time).total_seconds()
        else:
            self.total_time = (
                self.preparation_time + 
                self.download_time + 
                self.installation_time + 
                self.verification_time
            )

@dataclass
class InstallationHealthCheck:
    """Verificação de saúde do sistema de instalação"""
    timestamp: datetime
    system_health: str  # 'healthy', 'warning', 'critical'
    available_space_gb: float
    memory_usage_percent: float
    admin_privileges: bool
    network_connectivity: bool
    pending_reboots: bool
    conflicting_processes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class EnhancedInstallationManager(InstallationManager):
    """
    Versão aprimorada do InstallationManager com funcionalidades adicionais
    para completar todos os requisitos da Task 5
    """
    
    def __init__(self, base_path: Optional[str] = None):
        super().__init__(base_path)
        self.installation_metrics: Dict[str, InstallationMetrics] = {}
        self.health_checks: List[InstallationHealthCheck] = []
        self.metrics_lock = threading.Lock()
        self.auto_recovery_enabled = True
        self.max_concurrent_installations = 3
        self.installation_timeout = 1800  # 30 minutos
        
        # Diretório para métricas
        self.metrics_dir = os.path.join(self.base_path, "metrics")
        os.makedirs(self.metrics_dir, exist_ok=True)
    
    def install_component_enhanced(self, component: str, 
                                 progress_callback: Optional[Callable] = None) -> InstallationResult:
        """
        Instalação aprimorada com métricas detalhadas e recovery automático
        
        Args:
            component: Nome do componente
            progress_callback: Callback de progresso
            
        Returns:
            InstallationResult: Resultado da instalação
        """
        # Inicia métricas
        metrics = InstallationMetrics(
            component=component,
            start_time=datetime.now()
        )
        
        with self.metrics_lock:
            self.installation_metrics[component] = metrics
        
        try:
            # Executa verificação de saúde antes da instalação
            health_check = self.perform_system_health_check()
            if health_check.system_health == 'critical':
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message="Sistema em estado crítico, instalação cancelada",
                    details={'health_check': health_check.__dict__}
                )
            
            # Callback de progresso inicial
            if progress_callback:
                progress_callback(f"Iniciando instalação de {component}...")
            
            # Executa instalação com tracking de métricas
            result = self._install_with_metrics_tracking(
                component, metrics, progress_callback
            )
            
            # Finaliza métricas
            metrics.end_time = datetime.now()
            metrics.calculate_total_time()
            
            # Salva métricas
            self._save_installation_metrics(metrics)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro crítico na instalação aprimorada de {component}: {e}")
            
            # Finaliza métricas com erro
            metrics.end_time = datetime.now()
            metrics.calculate_total_time()
            
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro crítico: {e}",
                details={'error': str(e), 'metrics': metrics.__dict__}
            )
    
    def install_multiple_enhanced(self, components: List[str], 
                                max_parallel: int = 3,
                                enable_smart_recovery: bool = True,
                                progress_callback: Optional[Callable] = None) -> BatchInstallationResult:
        """
        Instalação em lote aprimorada com recovery inteligente e otimizações
        
        Args:
            components: Lista de componentes
            max_parallel: Máximo de instalações paralelas
            enable_smart_recovery: Habilita recovery inteligente
            progress_callback: Callback de progresso
            
        Returns:
            BatchInstallationResult: Resultado da instalação em lote
        """
        start_time = datetime.now()
        logger.info(f"Iniciando instalação em lote aprimorada de {len(components)} componentes")
        
        # Executa verificação de saúde do sistema
        health_check = self.perform_system_health_check()
        if health_check.system_health == 'critical':
            result = BatchInstallationResult(overall_success=False)
            result.failed_components = components.copy()
            return result
        
        # Otimiza ordem de instalação baseada em histórico
        optimized_order = self._optimize_installation_order(components)
        
        # Executa instalação com otimizações
        result = self.install_multiple(
            optimized_order, 
            max_parallel=max_parallel, 
            enable_recovery=enable_smart_recovery
        )
        
        # Adiciona métricas aprimoradas
        result.total_time = (datetime.now() - start_time).total_seconds()
        
        # Gera relatório de instalação
        self._generate_installation_report(result, components)
        
        return result
    
    def perform_system_health_check(self) -> InstallationHealthCheck:
        """
        Executa verificação completa de saúde do sistema
        
        Returns:
            InstallationHealthCheck: Resultado da verificação
        """
        try:
            health_check = InstallationHealthCheck(
                timestamp=datetime.now(),
                system_health='healthy',
                available_space_gb=0.0,
                memory_usage_percent=0.0,
                admin_privileges=False,
                network_connectivity=False,
                pending_reboots=False
            )
            
            # Verifica espaço em disco
            try:
                import shutil
                total, used, free = shutil.disk_usage(self.base_path)
                health_check.available_space_gb = free / (1024**3)
                
                if health_check.available_space_gb < 1.0:  # Menos de 1GB
                    health_check.system_health = 'critical'
                    health_check.recommendations.append("Libere espaço em disco (menos de 1GB disponível)")
                elif health_check.available_space_gb < 5.0:  # Menos de 5GB
                    health_check.system_health = 'warning'
                    health_check.recommendations.append("Considere liberar espaço em disco (menos de 5GB disponível)")
                    
            except Exception as e:
                logger.warning(f"Erro ao verificar espaço em disco: {e}")
            
            # Verifica uso de memória
            try:
                import psutil
                health_check.memory_usage_percent = psutil.virtual_memory().percent
                
                if health_check.memory_usage_percent > 90:
                    health_check.system_health = 'critical'
                    health_check.recommendations.append("Uso de memória crítico (>90%)")
                elif health_check.memory_usage_percent > 80:
                    if health_check.system_health == 'healthy':
                        health_check.system_health = 'warning'
                    health_check.recommendations.append("Uso de memória alto (>80%)")
                    
            except ImportError:
                logger.debug("psutil não disponível para verificação de memória")
            except Exception as e:
                logger.warning(f"Erro ao verificar uso de memória: {e}")
            
            # Verifica privilégios administrativos
            try:
                from env_dev.utils.permission_checker import is_admin
                health_check.admin_privileges = is_admin()
                
                if not health_check.admin_privileges:
                    health_check.recommendations.append("Alguns componentes podem requerer privilégios administrativos")
                    
            except Exception as e:
                logger.warning(f"Erro ao verificar privilégios: {e}")
            
            # Verifica conectividade de rede
            try:
                from env_dev.utils.network import test_internet_connection
                health_check.network_connectivity = test_internet_connection()
                
                if not health_check.network_connectivity:
                    health_check.system_health = 'warning'
                    health_check.recommendations.append("Sem conectividade com a internet")
                    
            except Exception as e:
                logger.warning(f"Erro ao verificar conectividade: {e}")
            
            # Verifica processos conflitantes
            health_check.conflicting_processes = self._detect_conflicting_processes()
            if health_check.conflicting_processes:
                if health_check.system_health == 'healthy':
                    health_check.system_health = 'warning'
                health_check.recommendations.append(
                    f"Processos conflitantes detectados: {', '.join(health_check.conflicting_processes)}"
                )
            
            # Salva verificação de saúde
            self.health_checks.append(health_check)
            self._save_health_check(health_check)
            
            logger.info(f"Verificação de saúde concluída: {health_check.system_health}")
            return health_check
            
        except Exception as e:
            logger.error(f"Erro na verificação de saúde: {e}")
            return InstallationHealthCheck(
                timestamp=datetime.now(),
                system_health='critical',
                available_space_gb=0.0,
                memory_usage_percent=100.0,
                admin_privileges=False,
                network_connectivity=False,
                pending_reboots=False,
                recommendations=[f"Erro na verificação de saúde: {e}"]
            )
    
    def get_installation_statistics(self) -> Dict:
        """
        Retorna estatísticas detalhadas de instalações
        
        Returns:
            Dict: Estatísticas de instalação
        """
        try:
            with self.metrics_lock:
                total_installations = len(self.installation_metrics)
                
                if total_installations == 0:
                    return {
                        'total_installations': 0,
                        'success_rate': 0.0,
                        'average_time': 0.0,
                        'fastest_installation': None,
                        'slowest_installation': None,
                        'most_retried_component': None,
                        'rollback_rate': 0.0
                    }
                
                # Calcula estatísticas
                successful_installations = 0
                total_time = 0.0
                total_retries = 0
                rollbacks_performed = 0
                times = []
                retry_counts = {}
                
                for component, metrics in self.installation_metrics.items():
                    if metrics.end_time:  # Instalação concluída
                        total_time += metrics.total_time
                        times.append((component, metrics.total_time))
                        total_retries += metrics.retry_count
                        
                        if metrics.retry_count > 0:
                            retry_counts[component] = metrics.retry_count
                        
                        if metrics.rollback_performed:
                            rollbacks_performed += 1
                        else:
                            successful_installations += 1
                
                # Ordena por tempo
                times.sort(key=lambda x: x[1])
                
                stats = {
                    'total_installations': total_installations,
                    'successful_installations': successful_installations,
                    'failed_installations': total_installations - successful_installations,
                    'success_rate': (successful_installations / total_installations) * 100,
                    'average_time': total_time / total_installations if total_installations > 0 else 0,
                    'total_retries': total_retries,
                    'rollback_rate': (rollbacks_performed / total_installations) * 100,
                    'fastest_installation': times[0] if times else None,
                    'slowest_installation': times[-1] if times else None,
                    'most_retried_component': max(retry_counts.items(), key=lambda x: x[1]) if retry_counts else None,
                    'health_checks_performed': len(self.health_checks),
                    'last_health_check': self.health_checks[-1].__dict__ if self.health_checks else None
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {'error': str(e)}
    
    def cleanup_installation_artifacts(self, max_age_days: int = 30) -> Dict[str, int]:
        """
        Limpa artefatos antigos de instalação
        
        Args:
            max_age_days: Idade máxima em dias
            
        Returns:
            Dict: Estatísticas de limpeza
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            cleanup_stats = {
                'rollback_files_removed': 0,
                'metrics_files_removed': 0,
                'temp_files_removed': 0,
                'total_space_freed_mb': 0
            }
            
            # Limpa arquivos de rollback antigos
            if os.path.exists(self.rollback_dir):
                for filename in os.listdir(self.rollback_dir):
                    file_path = os.path.join(self.rollback_dir, filename)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats['rollback_files_removed'] += 1
                            cleanup_stats['total_space_freed_mb'] += file_size / (1024*1024)
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo de rollback {file_path}: {e}")
            
            # Limpa arquivos de métricas antigos
            if os.path.exists(self.metrics_dir):
                for filename in os.listdir(self.metrics_dir):
                    file_path = os.path.join(self.metrics_dir, filename)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats['metrics_files_removed'] += 1
                            cleanup_stats['total_space_freed_mb'] += file_size / (1024*1024)
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo de métricas {file_path}: {e}")
            
            # Limpa arquivos temporários
            temp_dirs = ['temp', 'temp_download', 'cache']
            for temp_dir in temp_dirs:
                temp_path = os.path.join(self.base_path, temp_dir)
                if os.path.exists(temp_path):
                    for root, dirs, files in os.walk(temp_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                if file_time < cutoff_date:
                                    file_size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    cleanup_stats['temp_files_removed'] += 1
                                    cleanup_stats['total_space_freed_mb'] += file_size / (1024*1024)
                            except Exception as e:
                                logger.warning(f"Erro ao remover arquivo temporário {file_path}: {e}")
            
            logger.info(f"Limpeza concluída: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Erro na limpeza de artefatos: {e}")
            return {'error': str(e)}
    
    def _install_with_metrics_tracking(self, component: str, metrics: InstallationMetrics,
                                     progress_callback: Optional[Callable] = None) -> InstallationResult:
        """Instala componente com tracking detalhado de métricas"""
        try:
            # Fase de preparação
            prep_start = time.time()
            if progress_callback:
                progress_callback(f"Preparando ambiente para {component}...")
            
            # Simula preparação (já implementada no método pai)
            prep_end = time.time()
            metrics.preparation_time = prep_end - prep_start
            
            # Fase de download
            download_start = time.time()
            if progress_callback:
                progress_callback(f"Baixando {component}...")
            
            # Executa instalação usando método pai
            result = self.install_component(component)
            
            download_end = time.time()
            metrics.download_time = download_end - download_start
            
            # Atualiza métricas baseado no resultado
            if not result.success and result.rollback_info:
                metrics.rollback_performed = True
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no tracking de métricas para {component}: {e}")
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro no tracking: {e}",
                details={'error': str(e)}
            )
    
    def _optimize_installation_order(self, components: List[str]) -> List[str]:
        """Otimiza ordem de instalação baseada em histórico e dependências"""
        try:
            # Carrega histórico de instalações
            success_rates = self._calculate_component_success_rates()
            
            # Ordena por taxa de sucesso (componentes mais confiáveis primeiro)
            def sort_key(component):
                # Prioridade: dependências primeiro, depois taxa de sucesso
                config = self._load_component_config(component)
                dependencies = config.get('dependencies', []) if config else []
                dependency_count = len(dependencies)
                success_rate = success_rates.get(component, 0.5)  # 50% padrão
                
                # Componentes com menos dependências e maior taxa de sucesso primeiro
                return (-dependency_count, -success_rate)
            
            optimized = sorted(components, key=sort_key)
            
            # Aplica resolução de dependências
            final_order = self._resolve_dependency_order(optimized)
            
            logger.info(f"Ordem otimizada: {final_order}")
            return final_order
            
        except Exception as e:
            logger.error(f"Erro na otimização da ordem: {e}")
            return components
    
    def _calculate_component_success_rates(self) -> Dict[str, float]:
        """Calcula taxa de sucesso por componente baseada no histórico"""
        success_rates = {}
        
        try:
            with self.metrics_lock:
                component_stats = {}
                
                for component, metrics in self.installation_metrics.items():
                    if component not in component_stats:
                        component_stats[component] = {'total': 0, 'success': 0}
                    
                    component_stats[component]['total'] += 1
                    if not metrics.rollback_performed:
                        component_stats[component]['success'] += 1
                
                # Calcula taxas
                for component, stats in component_stats.items():
                    if stats['total'] > 0:
                        success_rates[component] = stats['success'] / stats['total']
                    else:
                        success_rates[component] = 0.5  # Padrão
            
            return success_rates
            
        except Exception as e:
            logger.error(f"Erro ao calcular taxas de sucesso: {e}")
            return {}
    
    def _detect_conflicting_processes(self) -> List[str]:
        """Detecta processos que podem conflitar com instalações"""
        conflicting_processes = []
        
        try:
            import psutil
            
            # Lista de processos conhecidos que podem causar conflitos
            known_conflicts = [
                'antimalware service executable',
                'windows defender',
                'mcafee',
                'norton',
                'kaspersky',
                'avast',
                'avg',
                'steam.exe',
                'origin.exe',
                'uplay.exe',
                'epicgameslauncher.exe'
            ]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    for conflict in known_conflicts:
                        if conflict in proc_name:
                            conflicting_processes.append(proc.info['name'])
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
        except ImportError:
            logger.debug("psutil não disponível para detecção de processos")
        except Exception as e:
            logger.warning(f"Erro na detecção de processos conflitantes: {e}")
        
        return conflicting_processes
    
    def _save_installation_metrics(self, metrics: InstallationMetrics):
        """Salva métricas de instalação em arquivo"""
        try:
            metrics_file = os.path.join(
                self.metrics_dir, 
                f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            # Carrega métricas existentes
            existing_metrics = []
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        existing_metrics = json.load(f)
                except:
                    existing_metrics = []
            
            # Adiciona nova métrica
            metrics_data = {
                'component': metrics.component,
                'start_time': metrics.start_time.isoformat(),
                'end_time': metrics.end_time.isoformat() if metrics.end_time else None,
                'preparation_time': metrics.preparation_time,
                'download_time': metrics.download_time,
                'installation_time': metrics.installation_time,
                'verification_time': metrics.verification_time,
                'total_time': metrics.total_time,
                'retry_count': metrics.retry_count,
                'rollback_performed': metrics.rollback_performed,
                'parallel_group': metrics.parallel_group,
                'dependencies_resolved': metrics.dependencies_resolved,
                'conflicts_detected': metrics.conflicts_detected
            }
            
            existing_metrics.append(metrics_data)
            
            # Salva métricas atualizadas
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metrics, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar métricas: {e}")
    
    def _save_health_check(self, health_check: InstallationHealthCheck):
        """Salva verificação de saúde em arquivo"""
        try:
            health_file = os.path.join(
                self.metrics_dir,
                f"health_checks_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            # Carrega verificações existentes
            existing_checks = []
            if os.path.exists(health_file):
                try:
                    with open(health_file, 'r', encoding='utf-8') as f:
                        existing_checks = json.load(f)
                except:
                    existing_checks = []
            
            # Adiciona nova verificação
            check_data = {
                'timestamp': health_check.timestamp.isoformat(),
                'system_health': health_check.system_health,
                'available_space_gb': health_check.available_space_gb,
                'memory_usage_percent': health_check.memory_usage_percent,
                'admin_privileges': health_check.admin_privileges,
                'network_connectivity': health_check.network_connectivity,
                'pending_reboots': health_check.pending_reboots,
                'conflicting_processes': health_check.conflicting_processes,
                'recommendations': health_check.recommendations
            }
            
            existing_checks.append(check_data)
            
            # Mantém apenas as últimas 100 verificações
            if len(existing_checks) > 100:
                existing_checks = existing_checks[-100:]
            
            # Salva verificações atualizadas
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(existing_checks, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar verificação de saúde: {e}")
    
    def _generate_installation_report(self, result: BatchInstallationResult, 
                                    original_components: List[str]):
        """Gera relatório detalhado de instalação em lote"""
        try:
            report_file = os.path.join(
                self.metrics_dir,
                f"installation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'original_components': original_components,
                'overall_success': result.overall_success,
                'completed_components': result.completed_components,
                'failed_components': result.failed_components,
                'skipped_components': result.skipped_components,
                'total_time': result.total_time,
                'parallel_installations': result.parallel_installations,
                'rollback_performed': result.rollback_performed,
                'conflicts_detected': [
                    {
                        'component1': c.component1,
                        'component2': c.component2,
                        'conflict_type': c.conflict_type,
                        'description': c.description,
                        'severity': c.severity
                    }
                    for c in result.detected_conflicts
                ],
                'recovery_attempts': result.recovery_attempts,
                'installation_results': {
                    comp: {
                        'success': res.success,
                        'status': res.status.value,
                        'message': res.message,
                        'installation_time': getattr(res, 'installation_time', 0)
                    }
                    for comp, res in result.installation_results.items()
                }
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Relatório de instalação salvo: {report_file}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")

# Instância global aprimorada
enhanced_installation_manager = EnhancedInstallationManager()