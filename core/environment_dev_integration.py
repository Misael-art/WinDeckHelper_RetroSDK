# -*- coding: utf-8 -*-
"""
Integração principal do Environment Dev com o sistema de catálogo de runtime
Conecta todos os componentes desenvolvidos com a aplicação principal
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import queue
import time

# Importar todos os componentes desenvolvidos
from runtime_catalog_manager import RuntimeCatalogManager, RuntimeInfo, RuntimeStatus
from package_manager_integration import PackageManagerIntegrator, PackageManager
from configuration_manager import ConfigurationManager, ConfigProfile
from security_manager import SecurityManager, SecurityLevel
from plugin_manager import PluginManager
from plugin_security import PluginSecurityManager
from catalog_update_manager import CatalogUpdateManager
from .detection_engine import DetectionEngine, DetectionResult, DetectionMethod

@dataclass
class IntegrationConfig:
    """Configuração de integração do Environment Dev"""
    app_name: str = "Environment Dev"
    version: str = "2.0.0"
    data_directory: Path = Path.home() / ".environment_dev"
    config_file: str = "integration_config.json"
    log_level: str = "INFO"
    auto_update_enabled: bool = True
    plugin_system_enabled: bool = True
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    steam_deck_mode: bool = False
    backup_enabled: bool = True
    telemetry_enabled: bool = False

@dataclass
class SystemStatus:
    """Status do sistema integrado"""
    runtime_catalog_loaded: bool = False
    package_managers_detected: int = 0
    plugins_loaded: int = 0
    security_level: str = "unknown"
    last_update_check: Optional[datetime] = None
    steam_deck_detected: bool = False
    total_runtimes: int = 0
    installed_runtimes: int = 0
    pending_updates: int = 0
    system_health: str = "unknown"

class EnvironmentDevIntegrator:
    """Integrador principal do Environment Dev"""
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Inicializar integrador"""
        self.config = config or IntegrationConfig()
        self.logger = self._setup_logging()
        
        # Criar diretório de dados
        self.config.data_directory.mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        self.runtime_catalog = None
        self.package_integrator = None
        self.config_manager = None
        self.security_manager = None
        self.plugin_manager = None
        self.plugin_security = None
        self.update_manager = None
        self.detection_engine = None
        
        # Status do sistema
        self.system_status = SystemStatus()
        self.is_initialized = False
        self.background_tasks = []
        self.task_queue = queue.Queue()
        
        # Lock para operações thread-safe
        self._lock = threading.RLock()
        
        self.logger.info(f"Environment Dev Integrator inicializado - versão {self.config.version}")
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar sistema de logging"""
        logger = logging.getLogger("EnvironmentDev")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Configurar handler se não existir
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def initialize_system(self) -> bool:
        """Inicializar todo o sistema integrado"""
        try:
            with self._lock:
                self.logger.info("Iniciando inicialização do sistema...")
                
                # 1. Detectar ambiente Steam Deck
                self._detect_steam_deck()
                
                # 2. Inicializar gerenciadores principais
                self._initialize_core_managers()
                
                # 3. Inicializar sistema de segurança
                self._initialize_security_system()
                
                # 4. Inicializar sistema de plugins
                if self.config.plugin_system_enabled:
                    self._initialize_plugin_system()
                
                # 5. Carregar configurações existentes
                self._load_existing_configurations()
                
                # 6. Inicializar sistema de atualizações
                if self.config.auto_update_enabled:
                    self._initialize_update_system()
                
                # 7. Executar detecção inicial de runtimes
                self._perform_initial_detection()
                
                # 8. Iniciar tarefas em background
                self._start_background_tasks()
                
                # 9. Atualizar status do sistema
                self._update_system_status()
                
                self.is_initialized = True
                self.logger.info("Sistema inicializado com sucesso")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro durante inicialização: {e}")
            return False
    
    def _detect_steam_deck(self):
        """Detectar se está rodando no Steam Deck"""
        try:
            # Verificações específicas do Steam Deck
            steam_deck_indicators = [
                os.path.exists("/home/deck"),
                os.environ.get("USER") == "deck",
                os.path.exists("/usr/bin/steamos-session-select"),
                os.path.exists("/etc/steamos-release")
            ]
            
            self.config.steam_deck_mode = any(steam_deck_indicators)
            self.system_status.steam_deck_detected = self.config.steam_deck_mode
            
            if self.config.steam_deck_mode:
                self.logger.info("Steam Deck detectado - ativando otimizações específicas")
                # Ajustar configurações para Steam Deck
                self.config.security_level = SecurityLevel.HIGH
                self.config.backup_enabled = True
            
        except Exception as e:
            self.logger.warning(f"Erro na detecção Steam Deck: {e}")
    
    def _initialize_core_managers(self):
        """Inicializar gerenciadores principais"""
        # Runtime Catalog Manager
        self.runtime_catalog = RuntimeCatalogManager()
        self.runtime_catalog.catalog_file = self.config.data_directory / "runtime_catalog.json"
        
        # Package Manager Integrator
        self.package_integrator = PackageManagerIntegrator()
        
        # Configuration Manager
        self.config_manager = ConfigurationManager()
        self.config_manager.config_directory = self.config.data_directory / "configs"
        
        # Detection Engine
        self.detection_engine = DetectionEngine()
        
        self.logger.info("Gerenciadores principais inicializados")
    
    def _initialize_security_system(self):
        """Inicializar sistema de segurança"""
        self.security_manager = SecurityManager()
        self.security_manager.set_security_level(self.config.security_level)
        
        # Configurar auditoria
        audit_file = self.config.data_directory / "security_audit.log"
        self.security_manager.audit_file = audit_file
        
        self.logger.info(f"Sistema de segurança inicializado - nível: {self.config.security_level.value}")
    
    def _initialize_plugin_system(self):
        """Inicializar sistema de plugins"""
        try:
            # Plugin Manager
            self.plugin_manager = PluginManager()
            self.plugin_manager.plugin_directory = self.config.data_directory / "plugins"
            
            # Plugin Security Manager
            self.plugin_security = PluginSecurityManager()
            
            # Descobrir e carregar plugins
            discovered_plugins = self.plugin_manager.discover_plugins()
            self.logger.info(f"Descobertos {len(discovered_plugins)} plugins")
            
            # Carregar plugins seguros
            loaded_count = 0
            for plugin_info in discovered_plugins:
                try:
                    # Validar segurança do plugin
                    security_result = self.plugin_security.validate_plugin_security(
                        self.plugin_manager.plugin_directory / plugin_info.name
                    )
                    
                    if security_result["is_safe"]:
                        if self.plugin_manager.load_plugin(plugin_info.name):
                            loaded_count += 1
                    else:
                        self.logger.warning(f"Plugin {plugin_info.name} rejeitado por segurança")
                        
                except Exception as e:
                    self.logger.error(f"Erro ao carregar plugin {plugin_info.name}: {e}")
            
            self.system_status.plugins_loaded = loaded_count
            self.logger.info(f"Sistema de plugins inicializado - {loaded_count} plugins carregados")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do sistema de plugins: {e}")
    
    def _initialize_update_system(self):
        """Inicializar sistema de atualizações"""
        try:
            self.update_manager = CatalogUpdateManager(self.runtime_catalog)
            
            # Configurar mirrors padrão
            default_mirrors = [
                {
                    "url": "https://catalog.environmentdev.com/",
                    "name": "Official Mirror",
                    "location": "Global",
                    "priority": 100
                },
                {
                    "url": "https://mirror.github.com/environmentdev/",
                    "name": "GitHub Mirror",
                    "location": "Global",
                    "priority": 80
                }
            ]
            
            for mirror_data in default_mirrors:
                from catalog_update_manager import MirrorInfo, MirrorStatus
                mirror = MirrorInfo(
                    url=mirror_data["url"],
                    name=mirror_data["name"],
                    location=mirror_data["location"],
                    priority=mirror_data["priority"],
                    status=MirrorStatus.ACTIVE
                )
                self.update_manager.add_mirror(mirror)
            
            self.logger.info("Sistema de atualizações inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do sistema de atualizações: {e}")
    
    def _load_existing_configurations(self):
        """Carregar configurações existentes"""
        try:
            # Carregar catálogo de runtime
            if self.runtime_catalog.catalog_file.exists():
                self.runtime_catalog.load_catalog()
                self.system_status.runtime_catalog_loaded = True
                
                all_runtimes = self.runtime_catalog.get_all_runtimes()
                self.system_status.total_runtimes = len(all_runtimes)
                
                # Contar runtimes instalados
                installed_count = 0
                for runtime in all_runtimes:
                    if self.runtime_catalog.get_installation_status(runtime.name) == RuntimeStatus.INSTALLED:
                        installed_count += 1
                
                self.system_status.installed_runtimes = installed_count
                
                self.logger.info(f"Catálogo carregado: {self.system_status.total_runtimes} runtimes, {installed_count} instalados")
            
            # Carregar perfis de configuração
            if self.config_manager.config_directory.exists():
                profiles = self.config_manager.list_profiles()
                self.logger.info(f"Carregados {len(profiles)} perfis de configuração")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações existentes: {e}")
    
    def _perform_initial_detection(self):
        """Executar detecção inicial de runtimes"""
        try:
            # Detectar gerenciadores de pacote disponíveis
            available_managers = self.package_integrator.detect_available_managers()
            self.system_status.package_managers_detected = len(available_managers)
            
            self.logger.info(f"Detectados {len(available_managers)} gerenciadores de pacote: {[m.value for m in available_managers]}")
            
            # Executar detecção de runtimes instalados
            detection_results = self.detection_engine.detect_all_runtimes()
            
            detected_count = 0
            for result in detection_results:
                if result.found:
                    detected_count += 1
                    
                    # Adicionar ao catálogo se não existir
                    existing_runtime = self.runtime_catalog.get_runtime(result.runtime_name)
                    if not existing_runtime:
                        # Criar RuntimeInfo básico baseado na detecção
                        runtime_info = RuntimeInfo(
                            name=result.runtime_name,
                            version=result.version or "unknown",
                            description=f"Detected {result.runtime_name}",
                            category="detected",
                            tags=["auto-detected"],
                            download_url="",
                            install_size=0,
                            dependencies=[],
                            supported_platforms=["current"],
                            checksum="",
                            installation_path=Path(result.installation_path) if result.installation_path else None
                        )
                        
                        self.runtime_catalog.add_runtime(runtime_info)
            
            self.logger.info(f"Detecção inicial concluída: {detected_count} runtimes detectados")
            
        except Exception as e:
            self.logger.error(f"Erro na detecção inicial: {e}")
    
    def _start_background_tasks(self):
        """Iniciar tarefas em background"""
        try:
            # Task de verificação de atualizações
            if self.config.auto_update_enabled and self.update_manager:
                update_task = threading.Thread(
                    target=self._background_update_checker,
                    daemon=True,
                    name="UpdateChecker"
                )
                update_task.start()
                self.background_tasks.append(update_task)
            
            # Task de monitoramento do sistema
            monitor_task = threading.Thread(
                target=self._background_system_monitor,
                daemon=True,
                name="SystemMonitor"
            )
            monitor_task.start()
            self.background_tasks.append(monitor_task)
            
            # Task de processamento de fila
            queue_task = threading.Thread(
                target=self._background_queue_processor,
                daemon=True,
                name="QueueProcessor"
            )
            queue_task.start()
            self.background_tasks.append(queue_task)
            
            self.logger.info(f"Iniciadas {len(self.background_tasks)} tarefas em background")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar tarefas em background: {e}")
    
    def _background_update_checker(self):
        """Task em background para verificar atualizações"""
        while True:
            try:
                time.sleep(3600)  # Verificar a cada hora
                
                if self.update_manager:
                    update_info = self.update_manager.check_for_updates()
                    if update_info:
                        self.system_status.pending_updates += 1
                        self.logger.info(f"Atualização disponível: {update_info.version}")
                        
                        # Adicionar à fila de tarefas
                        self.task_queue.put({
                            "type": "update_available",
                            "data": update_info
                        })
                
                self.system_status.last_update_check = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Erro na verificação de atualizações: {e}")
                time.sleep(300)  # Aguardar 5 minutos antes de tentar novamente
    
    def _background_system_monitor(self):
        """Task em background para monitorar sistema"""
        while True:
            try:
                time.sleep(60)  # Monitorar a cada minuto
                
                # Atualizar status do sistema
                self._update_system_status()
                
                # Verificar saúde do sistema
                health_issues = self._check_system_health()
                
                if health_issues:
                    self.system_status.system_health = "warning"
                    for issue in health_issues:
                        self.logger.warning(f"Problema de saúde do sistema: {issue}")
                else:
                    self.system_status.system_health = "healthy"
                
            except Exception as e:
                self.logger.error(f"Erro no monitoramento do sistema: {e}")
                time.sleep(30)
    
    def _background_queue_processor(self):
        """Task em background para processar fila de tarefas"""
        while True:
            try:
                # Aguardar tarefa na fila
                task = self.task_queue.get(timeout=10)
                
                # Processar tarefa
                self._process_background_task(task)
                
                # Marcar tarefa como concluída
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro no processamento de tarefa: {e}")
    
    def _process_background_task(self, task: Dict[str, Any]):
        """Processar tarefa em background"""
        task_type = task.get("type")
        task_data = task.get("data")
        
        if task_type == "update_available":
            # Notificar sobre atualização disponível
            self.logger.info(f"Processando notificação de atualização: {task_data.version}")
            
        elif task_type == "runtime_install":
            # Processar instalação de runtime
            runtime_name = task_data.get("runtime_name")
            self.logger.info(f"Processando instalação de runtime: {runtime_name}")
            
        elif task_type == "security_scan":
            # Processar scan de segurança
            self.logger.info("Processando scan de segurança")
            
        else:
            self.logger.warning(f"Tipo de tarefa desconhecido: {task_type}")
    
    def _update_system_status(self):
        """Atualizar status do sistema"""
        try:
            with self._lock:
                # Atualizar contadores
                if self.runtime_catalog:
                    all_runtimes = self.runtime_catalog.get_all_runtimes()
                    self.system_status.total_runtimes = len(all_runtimes)
                    
                    installed_count = 0
                    for runtime in all_runtimes:
                        if self.runtime_catalog.get_installation_status(runtime.name) == RuntimeStatus.INSTALLED:
                            installed_count += 1
                    
                    self.system_status.installed_runtimes = installed_count
                
                # Atualizar nível de segurança
                if self.security_manager:
                    self.system_status.security_level = self.security_manager.security_level.value
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status do sistema: {e}")
    
    def _check_system_health(self) -> List[str]:
        """Verificar saúde do sistema"""
        issues = []
        
        try:
            # Verificar espaço em disco
            disk_usage = shutil.disk_usage(self.config.data_directory)
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb < 1.0:  # Menos de 1GB livre
                issues.append(f"Pouco espaço em disco: {free_space_gb:.1f}GB livres")
            
            # Verificar integridade dos arquivos
            critical_files = [
                self.runtime_catalog.catalog_file if self.runtime_catalog else None,
                self.config.data_directory / self.config.config_file
            ]
            
            for file_path in critical_files:
                if file_path and not file_path.exists():
                    issues.append(f"Arquivo crítico ausente: {file_path}")
            
            # Verificar status dos componentes
            if not self.system_status.runtime_catalog_loaded:
                issues.append("Catálogo de runtime não carregado")
            
            if self.system_status.package_managers_detected == 0:
                issues.append("Nenhum gerenciador de pacote detectado")
            
        except Exception as e:
            issues.append(f"Erro na verificação de saúde: {e}")
        
        return issues
    
    # Métodos públicos da API
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obter status completo do sistema"""
        with self._lock:
            return {
                "initialized": self.is_initialized,
                "version": self.config.version,
                "steam_deck_mode": self.config.steam_deck_mode,
                "status": asdict(self.system_status),
                "background_tasks": len(self.background_tasks),
                "queue_size": self.task_queue.qsize()
            }
    
    def install_runtime(self, runtime_name: str, background: bool = True) -> bool:
        """Instalar runtime"""
        try:
            if background:
                # Adicionar à fila de tarefas
                self.task_queue.put({
                    "type": "runtime_install",
                    "data": {"runtime_name": runtime_name}
                })
                return True
            else:
                # Instalação síncrona
                if self.runtime_catalog:
                    return self.runtime_catalog.install_runtime(runtime_name)
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na instalação de runtime {runtime_name}: {e}")
            return False
    
    def search_runtimes(self, **criteria) -> List[RuntimeInfo]:
        """Buscar runtimes no catálogo"""
        try:
            if self.runtime_catalog:
                return self.runtime_catalog.search_runtimes(**criteria)
            return []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de runtimes: {e}")
            return []
    
    def get_runtime_info(self, runtime_name: str) -> Optional[RuntimeInfo]:
        """Obter informações de um runtime"""
        try:
            if self.runtime_catalog:
                return self.runtime_catalog.get_runtime(runtime_name)
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do runtime {runtime_name}: {e}")
            return None
    
    def create_configuration_profile(self, profile: ConfigProfile) -> bool:
        """Criar perfil de configuração"""
        try:
            if self.config_manager:
                return self.config_manager.create_profile(profile)
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao criar perfil de configuração: {e}")
            return False
    
    def shutdown(self):
        """Encerrar sistema graciosamente"""
        try:
            self.logger.info("Iniciando encerramento do sistema...")
            
            # Parar tarefas em background
            for task in self.background_tasks:
                if task.is_alive():
                    # Note: daemon threads will be terminated automatically
                    pass
            
            # Salvar configurações
            if self.config_manager:
                self.config_manager.save_all_profiles()
            
            # Salvar catálogo
            if self.runtime_catalog:
                self.runtime_catalog.save_catalog()
            
            # Gerar relatório final de segurança
            if self.security_manager:
                security_report = self.security_manager.generate_security_report()
                self.logger.info(f"Relatório de segurança: {len(security_report['audit_entries'])} entradas")
            
            self.logger.info("Sistema encerrado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante encerramento: {e}")

# Função de conveniência para inicialização rápida
def initialize_environment_dev(config: Optional[IntegrationConfig] = None) -> EnvironmentDevIntegrator:
    """Inicializar Environment Dev com configuração padrão"""
    integrator = EnvironmentDevIntegrator(config)
    
    if integrator.initialize_system():
        return integrator
    else:
        raise RuntimeError("Falha na inicialização do Environment Dev")

# Exemplo de uso
if __name__ == "__main__":
    # Configuração personalizada
    config = IntegrationConfig(
        app_name="Environment Dev - Steam Deck Edition",
        version="2.0.0-steamdeck",
        log_level="DEBUG",
        steam_deck_mode=True,
        security_level=SecurityLevel.HIGH
    )
    
    # Inicializar sistema
    try:
        integrator = initialize_environment_dev(config)
        
        # Exibir status do sistema
        status = integrator.get_system_status()
        print("\n=== Environment Dev Status ===")
        print(f"Versão: {status['version']}")
        print(f"Modo Steam Deck: {status['steam_deck_mode']}")
        print(f"Runtimes no catálogo: {status['status']['total_runtimes']}")
        print(f"Runtimes instalados: {status['status']['installed_runtimes']}")
        print(f"Plugins carregados: {status['status']['plugins_loaded']}")
        print(f"Saúde do sistema: {status['status']['system_health']}")
        
        # Exemplo de busca
        steam_deck_runtimes = integrator.search_runtimes(tags=["steam-deck"])
        print(f"\nRuntimes otimizados para Steam Deck: {len(steam_deck_runtimes)}")
        
        # Manter sistema rodando por um tempo para demonstração
        print("\nSistema rodando... (Ctrl+C para encerrar)")
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            pass
        
        # Encerrar sistema
        integrator.shutdown()
        
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)