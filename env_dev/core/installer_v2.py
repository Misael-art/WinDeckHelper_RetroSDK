# -*- coding: utf-8 -*-
"""
Instalador Refatorado para Environment Dev Script
Versão 2.0 - Arquitetura modular e robusta
"""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time

# Importa módulos modernos
from utils.checksum_manager import checksum_manager
from utils.robust_verification import robust_verifier
from utils.permission_checker import is_admin, check_write_permission
from core.download_manager import download_manager
from core.installation_manager import installation_manager, InstallationResult, InstallationStatus
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory
from core.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

class InstallerState(Enum):
    """Estados do instalador"""
    IDLE = "idle"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class InstallationProgress:
    """Progresso da instalação"""
    state: InstallerState
    component_name: str
    current_step: str
    progress_percent: float
    details: Dict[str, Any]
    error: Optional[str] = None

class ModernInstaller:
    """Instalador moderno com arquitetura robusta"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.rollback_manager = RollbackManager()
        self.current_state = InstallerState.IDLE
        self.installation_queue = queue.Queue()
        self.results = {}
        self.temp_dir = None
        self._setup_temp_directory()
    
    def _setup_temp_directory(self):
        """Configura diretório temporário"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix='env_dev_')
            logger.info(f"Diretório temporário criado: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Erro ao criar diretório temporário: {e}")
            self.temp_dir = os.path.join(tempfile.gettempdir(), 'env_dev_fallback')
            os.makedirs(self.temp_dir, exist_ok=True)
    
    def _update_progress(self, state: InstallerState, component_name: str, 
                        step: str, progress: float, details: Dict = None, error: str = None):
        """Atualiza progresso da instalação"""
        self.current_state = state
        
        progress_info = InstallationProgress(
            state=state,
            component_name=component_name,
            current_step=step,
            progress_percent=progress,
            details=details or {},
            error=error
        )
        
        if self.progress_callback:
            try:
                self.progress_callback(progress_info)
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")
    
    def install_component(self, component_data: Dict) -> InstallationResult:
        """
        Instala um componente individual
        
        Args:
            component_data: Dados do componente
        
        Returns:
            InstallationResult: Resultado da instalação
        """
        component_name = component_data.get('name', 'Unknown')
        
        try:
            logger.info(f"Iniciando instalação de {component_name}")
            
            # 1. Preparação
            self._update_progress(InstallerState.PREPARING, component_name, "Preparando instalação", 5)
            
            prep_result = self._prepare_installation(component_data)
            if not prep_result['success']:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message=prep_result['message'],
                    details=prep_result
                )
            
            # 2. Download
            self._update_progress(InstallerState.DOWNLOADING, component_name, "Baixando arquivo", 15)
            
            download_result = self._download_component(component_data)
            if not download_result['success']:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message=download_result['message'],
                    details=download_result
                )
            
            file_path = download_result['file_path']
            
            # 3. Verificação de integridade
            self._update_progress(InstallerState.VERIFYING, component_name, "Verificando integridade", 35)
            
            verify_result = self._verify_file_integrity(file_path, component_data)
            if not verify_result['success']:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message=verify_result['message'],
                    details=verify_result
                )
            
            # 4. Instalação
            self._update_progress(InstallerState.INSTALLING, component_name, "Instalando componente", 50)
            
            # Cria ponto de rollback
            rollback_id = self.rollback_manager.create_rollback_point(
                f"Instalação de {component_name}",
                {'component': component_data, 'file_path': file_path}
            )
            
            try:
                install_result = installation_manager.install_component(
                    file_path, 
                    component_data,
                    lambda msg: self._update_progress(InstallerState.INSTALLING, component_name, msg, 70)
                )
                
                if install_result.success:
                    # 5. Finalização
                    self._update_progress(InstallerState.FINALIZING, component_name, "Finalizando instalação", 85)
                    
                    final_result = self._finalize_installation(component_data, install_result)
                    
                    if final_result['success']:
                        self._update_progress(InstallerState.COMPLETED, component_name, "Instalação concluída", 100)
                        
                        # Remove ponto de rollback se tudo deu certo
                        self.rollback_manager.remove_rollback_point(rollback_id)
                        
                        return InstallationResult(
                            success=True,
                            status=InstallationStatus.COMPLETED,
                            message="Instalação concluída com sucesso",
                            details={
                                'preparation': prep_result,
                                'download': download_result,
                                'verification': verify_result,
                                'installation': install_result.details,
                                'finalization': final_result
                            },
                            installed_path=install_result.installed_path,
                            version=install_result.version
                        )
                    else:
                        # Rollback se finalização falhou
                        self.rollback_manager.execute_rollback(rollback_id)
                        return InstallationResult(
                            success=False,
                            status=InstallationStatus.FAILED,
                            message=f"Falha na finalização: {final_result['message']}",
                            details=final_result
                        )
                else:
                    # Rollback se instalação falhou
                    self.rollback_manager.execute_rollback(rollback_id)
                    return install_result
                    
            except Exception as e:
                # Rollback em caso de exceção
                self.rollback_manager.execute_rollback(rollback_id)
                raise
            
        except Exception as e:
            logger.error(f"Erro na instalação de {component_name}: {e}")
            self._update_progress(InstallerState.FAILED, component_name, "Erro na instalação", 0, error=str(e))
            
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro na instalação: {e}",
                details={'error': str(e), 'traceback': str(e.__traceback__)}
            )
        
        finally:
            # Limpeza
            self._cleanup_temp_files()
    
    def _prepare_installation(self, component_data: Dict) -> Dict[str, Any]:
        """Prepara a instalação verificando pré-requisitos"""
        try:
            component_name = component_data.get('name', 'Unknown')
            
            # Verifica se já está instalado
            if component_data.get('skip_if_installed', True):
                status = robust_verifier.get_comprehensive_status(component_data)
                if status['overall_status'] == 'fully_verified':
                    return {
                        'success': False,
                        'message': f"{component_name} já está instalado",
                        'already_installed': True,
                        'status': status
                    }
            
            # Verifica privilégios necessários
            if component_data.get('requires_admin', False):
                if not is_admin():
                    return {
                        'success': False,
                        'message': "Privilégios de administrador necessários",
                        'requires_admin': True
                    }
            
            # Verifica espaço em disco
            estimated_size = component_data.get('estimated_size', 100 * 1024 * 1024)  # 100MB padrão
            
            # Determina caminho de instalação
            install_path = component_data.get('install_path')
            if not install_path:
                # Usa caminho padrão se não especificado
                if is_admin():
                    install_path = f"C:\\Program Files\\{component_name}"
                else:
                    install_path = os.path.expanduser(f"~\\AppData\\Local\\{component_name}")
                component_data['install_path'] = install_path
            
            # Verifica se pode instalar no caminho
            if not check_write_permission(os.path.dirname(install_path)):
                return {
                    'success': False,
                    'message': f"Não é possível instalar em {install_path}: sem permissão de escrita",
                    'install_path_error': True
                }
            
            # Verifica espaço disponível
            try:
                free_space = shutil.disk_usage(os.path.dirname(install_path)).free
                if free_space < estimated_size * 2:  # Margem de segurança
                    return {
                        'success': False,
                        'message': f"Espaço insuficiente. Necessário: {estimated_size // (1024*1024)}MB, Disponível: {free_space // (1024*1024)}MB",
                        'insufficient_space': True
                    }
            except Exception as e:
                logger.warning(f"Não foi possível verificar espaço em disco: {e}")
            
            return {
                'success': True,
                'message': "Preparação concluída",
                'install_path': install_path,
                'estimated_size': estimated_size
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro na preparação: {e}",
                'error': str(e)
            }
    
    def _download_component(self, component_data: Dict) -> Dict[str, Any]:
        """Baixa o arquivo do componente"""
        try:
            download_url = component_data.get('download_url')
            if not download_url:
                return {
                    'success': False,
                    'message': "URL de download não especificada",
                    'no_url': True
                }
            
            # Determina nome do arquivo
            filename = component_data.get('filename')
            if not filename:
                filename = os.path.basename(download_url.split('?')[0])  # Remove query params
                if not filename:
                    filename = f"{component_data.get('name', 'download')}.exe"
            
            file_path = os.path.join(self.temp_dir, filename)
            
            # Callback de progresso do download
            def download_progress(downloaded, total):
                if total > 0:
                    progress = 15 + (downloaded / total) * 20  # 15-35%
                    self._update_progress(
                        InstallerState.DOWNLOADING, 
                        component_data.get('name', 'Unknown'),
                        f"Baixando: {downloaded // (1024*1024)}MB / {total // (1024*1024)}MB",
                        progress
                    )
            
            # Executa download
            success, message, details = download_manager.download_file(
                download_url,
                file_path,
                progress_callback=download_progress,
                max_retries=component_data.get('download_retries', 3),
                timeout=component_data.get('download_timeout', 300)
            )
            
            if success:
                return {
                    'success': True,
                    'message': "Download concluído",
                    'file_path': file_path,
                    'details': details
                }
            else:
                return {
                    'success': False,
                    'message': f"Falha no download: {message}",
                    'details': details
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro no download: {e}",
                'error': str(e)
            }
    
    def _verify_file_integrity(self, file_path: str, component_data: Dict) -> Dict[str, Any]:
        """Verifica integridade do arquivo baixado"""
        try:
            # Verifica se arquivo existe
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': "Arquivo baixado não encontrado",
                    'file_not_found': True
                }
            
            # Verifica tamanho mínimo
            file_size = os.path.getsize(file_path)
            min_size = component_data.get('min_file_size', 1024)  # 1KB mínimo
            
            if file_size < min_size:
                return {
                    'success': False,
                    'message': f"Arquivo muito pequeno: {file_size} bytes (mínimo: {min_size})",
                    'file_too_small': True
                }
            
            # Verifica checksums se disponíveis
            checksums = component_data.get('checksums', {})
            if checksums:
                for algorithm, expected_hash in checksums.items():
                    if algorithm.lower() in ['md5', 'sha1', 'sha256', 'sha512']:
                        actual_hash = checksum_manager.calculate_checksum(file_path, algorithm.lower())
                        
                        if actual_hash.lower() != expected_hash.lower():
                            return {
                                'success': False,
                                'message': f"Checksum {algorithm} não confere",
                                'checksum_mismatch': True,
                                'expected': expected_hash,
                                'actual': actual_hash
                            }
            
            return {
                'success': True,
                'message': "Integridade verificada",
                'file_size': file_size,
                'checksums_verified': len(checksums)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro na verificação: {e}",
                'error': str(e)
            }
    
    def _finalize_installation(self, component_data: Dict, install_result: InstallationResult) -> Dict[str, Any]:
        """Finaliza a instalação com verificações pós-instalação"""
        try:
            component_name = component_data.get('name', 'Unknown')
            
            # Aguarda um pouco para o sistema se estabilizar
            time.sleep(2)
            
            # Verifica se a instalação foi bem-sucedida
            final_status = robust_verifier.get_comprehensive_status(component_data)
            
            if final_status['overall_status'] in ['fully_verified', 'partially_verified']:
                # Executa pós-instalação se especificado
                post_install = component_data.get('post_install')
                if post_install:
                    post_result = self._run_post_install_tasks(post_install, install_result.installed_path)
                    if not post_result['success']:
                        return {
                            'success': False,
                            'message': f"Falha na pós-instalação: {post_result['message']}",
                            'post_install_failed': True,
                            'details': post_result
                        }
                
                return {
                    'success': True,
                    'message': "Instalação finalizada com sucesso",
                    'final_status': final_status,
                    'verification_score': final_status.get('verification_score', 0)
                }
            else:
                return {
                    'success': False,
                    'message': f"Verificação final falhou: {final_status['overall_status']}",
                    'verification_failed': True,
                    'final_status': final_status
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro na finalização: {e}",
                'error': str(e)
            }
    
    def _run_post_install_tasks(self, post_install: Dict, install_path: Optional[str]) -> Dict[str, Any]:
        """Executa tarefas de pós-instalação"""
        try:
            results = []
            
            # Executa comandos
            commands = post_install.get('commands', [])
            for command in commands:
                if install_path:
                    command = command.replace('{install_path}', install_path)
                
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=install_path if install_path else None
                    )
                    
                    results.append({
                        'command': command,
                        'success': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr
                    })
                    
                    if result.returncode != 0:
                        return {
                            'success': False,
                            'message': f"Comando falhou: {command}",
                            'command_results': results
                        }
                        
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'message': f"Timeout no comando: {command}",
                        'command_results': results
                    }
            
            # Cria atalhos se especificado
            shortcuts = post_install.get('shortcuts', [])
            for shortcut in shortcuts:
                self._create_shortcut(shortcut, install_path)
            
            return {
                'success': True,
                'message': "Pós-instalação concluída",
                'command_results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Erro na pós-instalação: {e}",
                'error': str(e)
            }
    
    def _cleanup_temp_files(self):
        """Limpa arquivos temporários"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                logger.info("Arquivos temporários limpos")
        except Exception as e:
            logger.warning(f"Erro ao limpar arquivos temporários: {e}")
    
    def install_multiple_components(self, components: List[Dict], 
                                  parallel: bool = False) -> Dict[str, InstallationResult]:
        """
        Instala múltiplos componentes
        
        Args:
            components: Lista de componentes para instalar
            parallel: Se deve instalar em paralelo (experimental)
        
        Returns:
            Dict com resultados de cada componente
        """
        results = {}
        
        if parallel:
            # Instalação paralela (experimental)
            threads = []
            thread_results = {}
            
            def install_worker(component_data):
                component_name = component_data.get('name', 'Unknown')
                thread_results[component_name] = self.install_component(component_data)
            
            for component_data in components:
                thread = threading.Thread(
                    target=install_worker,
                    args=(component_data,)
                )
                threads.append(thread)
                thread.start()
            
            # Aguarda todas as threads
            for thread in threads:
                thread.join()
            
            results = thread_results
        else:
            # Instalação sequencial
            for component_data in components:
                component_name = component_data.get('name', 'Unknown')
                results[component_name] = self.install_component(component_data)
                
                # Para se houver falha crítica
                if not results[component_name].success and component_data.get('critical', False):
                    logger.error(f"Componente crítico {component_name} falhou, parando instalação")
                    break
        
        return results
    
    def get_installation_summary(self, results: Dict[str, InstallationResult]) -> Dict[str, Any]:
        """Gera resumo das instalações"""
        successful = [name for name, result in results.items() if result.success]
        failed = [name for name, result in results.items() if not result.success]
        
        return {
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) * 100 if results else 0,
            'successful_components': successful,
            'failed_components': failed,
            'details': results
        }
    
    def _create_shortcut(self, shortcut_config: Dict[str, Any], install_path: str) -> bool:
        """
        Cria um atalho no sistema.
        
        Args:
            shortcut_config: Configuração do atalho (nome, caminho, ícone, etc.)
            install_path: Caminho de instalação do componente
        
        Returns:
            True se o atalho foi criado com sucesso
        """
        try:
            import win32com.client
            import os
            
            # Extrai configurações do atalho
            name = shortcut_config.get('name', 'Shortcut')
            target = shortcut_config.get('target', '')
            icon = shortcut_config.get('icon', '')
            description = shortcut_config.get('description', '')
            working_dir = shortcut_config.get('working_dir', install_path)
            arguments = shortcut_config.get('arguments', '')
            location = shortcut_config.get('location', 'desktop')  # desktop, start_menu, both
            
            # Resolve caminhos relativos
            if not os.path.isabs(target):
                target = os.path.join(install_path, target)
            
            if icon and not os.path.isabs(icon):
                icon = os.path.join(install_path, icon)
            
            # Verifica se o arquivo de destino existe
            if not os.path.exists(target):
                logger.warning(f"Arquivo de destino do atalho não encontrado: {target}")
                return False
            
            # Cria objeto shell
            shell = win32com.client.Dispatch("WScript.Shell")
            
            # Determina locais para criar o atalho
            locations = []
            if location in ['desktop', 'both']:
                desktop = shell.SpecialFolders("Desktop")
                locations.append(os.path.join(desktop, f"{name}.lnk"))
            
            if location in ['start_menu', 'both']:
                start_menu = shell.SpecialFolders("StartMenu")
                # Cria pasta do programa se não existir
                program_folder = os.path.join(start_menu, "Programs", name.split()[0] if ' ' in name else name)
                os.makedirs(program_folder, exist_ok=True)
                locations.append(os.path.join(program_folder, f"{name}.lnk"))
            
            # Cria atalhos em todos os locais especificados
            created_shortcuts = []
            for shortcut_path in locations:
                try:
                    shortcut = shell.CreateShortCut(shortcut_path)
                    shortcut.Targetpath = target
                    shortcut.WorkingDirectory = working_dir
                    shortcut.Arguments = arguments
                    shortcut.Description = description
                    
                    if icon and os.path.exists(icon):
                        shortcut.IconLocation = icon
                    
                    shortcut.save()
                    created_shortcuts.append(shortcut_path)
                    logger.info(f"Atalho criado: {shortcut_path}")
                    
                except Exception as e:
                    logger.error(f"Erro ao criar atalho em {shortcut_path}: {e}")
                    continue
            
            if created_shortcuts:
                # Registra para rollback
                if hasattr(self, 'rollback_manager') and self.rollback_manager:
                    for shortcut_path in created_shortcuts:
                        self.rollback_manager.register_action(
                            'delete_file',
                            file_path=shortcut_path
                        )
                
                logger.info(f"Atalho '{name}' criado com sucesso em {len(created_shortcuts)} local(is)")
                return True
            else:
                logger.error(f"Falha ao criar atalho '{name}' em qualquer local")
                return False
                
        except ImportError:
            logger.error("Módulo win32com não disponível. Instale pywin32 para criar atalhos.")
            return False
        except Exception as e:
            logger.error(f"Erro ao criar atalho '{shortcut_config.get('name', 'Unknown')}': {e}")
            return False
    
    def __del__(self):
        """Destrutor - limpa recursos"""
        self._cleanup_temp_files()

# Instância global
modern_installer = ModernInstaller()