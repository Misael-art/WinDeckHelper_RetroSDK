# -*- coding: utf-8 -*-
"""
Gerenciador de Downloads Seguro para Environment Dev Script
Implementa download robusto com verificação obrigatória de integridade,
retry automático e limpeza de downloads corrompidos.
"""

import os
import logging
import requests
import threading
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, Callable, Tuple, List, Union
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from env_dev.utils.checksum_manager import checksum_manager
from env_dev.core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory
from env_dev.utils.network import test_internet_connection
from env_dev.utils.mirror_manager import (
    load_mirrors_config, find_best_mirror, generate_alternative_urls,
    check_url_availability
)

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    """Status do download"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"

@dataclass
class DownloadProgress:
    """Informações detalhadas de progresso do download"""
    total_size: int
    downloaded_size: int
    speed: float  # bytes/segundo
    eta: float    # segundos estimados
    percentage: float
    status: DownloadStatus
    message: str = ""
    # Campos adicionais para tracking detalhado
    start_time: datetime = field(default_factory=datetime.now)
    elapsed_time: float = 0.0
    average_speed: float = 0.0
    instantaneous_speed: float = 0.0
    bytes_per_second_history: List[float] = field(default_factory=list)
    chunk_count: int = 0
    last_update_time: datetime = field(default_factory=datetime.now)
    url: str = ""
    component_name: str = ""
    
    def update_speed_history(self, current_speed: float, max_history: int = 10):
        """Atualiza histórico de velocidade para cálculo de média móvel"""
        self.bytes_per_second_history.append(current_speed)
        if len(self.bytes_per_second_history) > max_history:
            self.bytes_per_second_history.pop(0)
        
        # Calcula velocidade média móvel
        if self.bytes_per_second_history:
            self.average_speed = sum(self.bytes_per_second_history) / len(self.bytes_per_second_history)
    
    def format_speed(self, speed: float) -> str:
        """Formata velocidade em formato legível"""
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed/1024:.1f} KB/s"
        elif speed < 1024 * 1024 * 1024:
            return f"{speed/(1024*1024):.1f} MB/s"
        else:
            return f"{speed/(1024*1024*1024):.1f} GB/s"
    
    def format_size(self, size: int) -> str:
        """Formata tamanho em formato legível"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.1f} GB"
    
    def format_time(self, seconds: float) -> str:
        """Formata tempo em formato legível"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def get_detailed_status(self) -> str:
        """Retorna status detalhado formatado"""
        if self.status == DownloadStatus.DOWNLOADING:
            speed_str = self.format_speed(self.average_speed)
            size_str = f"{self.format_size(self.downloaded_size)}/{self.format_size(self.total_size)}"
            eta_str = self.format_time(self.eta) if self.eta > 0 else "calculando..."
            return f"{self.percentage:.1f}% - {size_str} - {speed_str} - ETA: {eta_str}"
        else:
            return self.message

@dataclass
class DownloadResult:
    """Resultado de uma operação de download"""
    success: bool
    file_path: str = ""
    message: str = ""
    error_type: Optional[str] = None
    retry_count: int = 0
    verification_passed: bool = False
    download_time: float = 0.0
    file_size: int = 0

@dataclass
class DownloadInfo:
    """Informações de um download ativo"""
    component_name: str
    url: str
    file_path: str
    status: DownloadStatus
    start_time: datetime
    progress: DownloadProgress
    retry_count: int = 0
    session: Optional[requests.Session] = None
    cancelled: bool = False

class DownloadManager:
    """
    Gerenciador robusto de downloads com verificação obrigatória de integridade.
    
    Implementa os requisitos:
    - 2.1: Verificação obrigatória de checksum/hash para todos os downloads
    - 2.2: Retry automático até 3 vezes para falhas de verificação
    - 2.3: Relatório específico de erro e sugestão de download manual
    """
    
    def __init__(self, max_concurrent_downloads: int = 3, chunk_size: int = 8192):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.chunk_size = chunk_size
        self.active_downloads: Dict[str, DownloadInfo] = {}
        self.download_lock = threading.Lock()
        self.mirrors_config = {}
        self.temp_dir = "temp_download"
        
    def set_mirrors_config(self, mirrors_config: Dict):
        """
        Define configuração de mirrors
        
        Args:
            mirrors_config: Configuração de mirrors carregada
        """
        self.mirrors_config = mirrors_config
        logger.info(f"Configurados {len(mirrors_config)} mirrors")
    
    def get_download_urls(self, component_data: Dict) -> List[str]:
        """
        Obtém lista de URLs para download com fallback de mirrors (Requisito 2.5)
        
        Args:
            component_data: Dados do componente
            
        Returns:
            Lista de URLs ordenadas por prioridade
        """
        urls = []
        
        # URL principal do componente
        primary_url = component_data.get('download_url')
        if primary_url:
            urls.append(primary_url)
        
        # URLs de mirrors definidas no componente
        mirror_urls = component_data.get('mirror_urls', [])
        urls.extend(mirror_urls)
        
        # Mirrors automáticos usando o sistema de mirror management (Requisito 2.5)
        if primary_url:
            try:
                # Carrega configuração de mirrors se não estiver carregada
                if not self.mirrors_config:
                    self.mirrors_config = load_mirrors_config()
                
                # Gera URLs alternativas usando o mirror manager
                alternative_urls = generate_alternative_urls(primary_url, self.mirrors_config)
                
                # Adiciona URLs alternativas que não estão na lista
                for alt_url in alternative_urls:
                    if alt_url not in urls:
                        urls.append(alt_url)
                        
                logger.info(f"Geradas {len(alternative_urls)-1} URLs alternativas para {primary_url}")
                
            except Exception as e:
                logger.warning(f"Erro ao gerar URLs alternativas: {e}")
        
        # Mirrors automáticos baseados na configuração legada (compatibilidade)
        if self.mirrors_config and 'mirrors' in self.mirrors_config:
            component_name = component_data.get('name', '')
            for mirror_name, mirror_config in self.mirrors_config['mirrors'].items():
                if mirror_config.get('enabled', True):
                    base_url = mirror_config.get('base_url')
                    if base_url and primary_url:
                        # Tenta construir URL do mirror
                        filename = os.path.basename(urlparse(primary_url).path)
                        mirror_url = urljoin(base_url, filename)
                        if mirror_url not in urls:
                            urls.append(mirror_url)
        
        logger.debug(f"URLs de download para {component_data.get('name', 'componente')}: {urls}")
        return urls

    def download_with_mirrors(self, url: str, expected_hash: str, 
                             algorithm: str = 'sha256') -> DownloadResult:
        """
        Baixa arquivo usando sistema de mirrors automático (Requisito 2.5)
        
        Args:
            url: URL principal para download
            expected_hash: Hash esperado para verificação
            algorithm: Algoritmo de hash
            
        Returns:
            DownloadResult com informações do download
        """
        start_time = time.time()
        
        # Verifica conectividade antes de tentar mirrors
        if not test_internet_connection():
            return DownloadResult(
                success=False,
                message="Sem conexão com a internet",
                error_type="connectivity_error"
            )
        
        try:
            # Carrega configuração de mirrors se necessário
            if not self.mirrors_config:
                self.mirrors_config = load_mirrors_config()
            
            # Encontra o melhor mirror disponível
            best_url, alternative_urls = find_best_mirror(url, self.mirrors_config)
            
            logger.info(f"Melhor URL encontrada: {best_url}")
            logger.info(f"URLs alternativas disponíveis: {len(alternative_urls)}")
            
            # Se o melhor mirror é diferente da URL original, usa o mirror
            if best_url != url:
                logger.info(f"Usando mirror automático: {best_url}")
                result = self.download_with_retry(best_url, expected_hash, algorithm=algorithm)
                if result.success:
                    result.message += f" (via mirror: {best_url})"
                    return result
            
            # Tenta com a URL original
            result = self.download_with_retry(url, expected_hash, algorithm=algorithm)
            if result.success:
                return result
            
            # Se falhou com a URL original, tenta com mirrors alternativos
            logger.warning(f"Falha na URL original, tentando mirrors alternativos...")
            
            for alt_url in alternative_urls[1:]:  # Pula a primeira que é a original
                if alt_url == best_url:  # Já tentamos o melhor mirror
                    continue
                    
                logger.info(f"Tentando mirror alternativo: {alt_url}")
                result = self.download_with_retry(alt_url, expected_hash, algorithm=algorithm)
                
                if result.success:
                    result.message += f" (via mirror alternativo: {alt_url})"
                    logger.info(f"Download bem-sucedido com mirror alternativo: {alt_url}")
                    return result
                
                logger.warning(f"Falha no mirror alternativo: {alt_url}")
            
            # Todas as tentativas falharam
            return DownloadResult(
                success=False,
                message=f"Falha em todas as URLs disponíveis (original + {len(alternative_urls)-1} mirrors)",
                error_type="all_mirrors_failed"
            )
            
        except Exception as e:
            logger.error(f"Erro no sistema de mirrors: {e}")
            # Fallback para download direto
            return self.download_with_retry(url, expected_hash, algorithm=algorithm)

    def check_connectivity_and_mirrors(self, url: str) -> Dict[str, bool]:
        """
        Verifica conectividade e disponibilidade de mirrors para uma URL
        
        Args:
            url: URL para verificar
            
        Returns:
            Dicionário com status de cada URL
        """
        connectivity_status = {}
        
        try:
            # Carrega configuração de mirrors
            if not self.mirrors_config:
                self.mirrors_config = load_mirrors_config()
            
            # Gera URLs alternativas
            alternative_urls = generate_alternative_urls(url, self.mirrors_config)
            
            # Verifica cada URL
            for test_url in alternative_urls:
                is_available = check_url_availability(test_url, timeout=5)
                connectivity_status[test_url] = is_available
                logger.debug(f"URL {test_url}: {'disponível' if is_available else 'indisponível'}")
            
        except Exception as e:
            logger.error(f"Erro na verificação de conectividade: {e}")
            connectivity_status[url] = False
        
        return connectivity_status
    
    def download_with_verification(self, url: str, expected_hash: str, 
                                  algorithm: str = 'sha256') -> DownloadResult:
        """
        Baixa arquivo com verificação obrigatória de hash (Requisito 2.1)
        
        Args:
            url: URL para download
            expected_hash: Hash esperado para verificação
            algorithm: Algoritmo de hash (padrão: sha256)
            
        Returns:
            DownloadResult com informações completas do download
        """
        start_time = time.time()
        component_name = os.path.basename(urlparse(url).path)
        
        # Verificação obrigatória de hash antes do download (Requisito 2.1)
        if not expected_hash:
            return DownloadResult(
                success=False,
                message="AVISO DE SEGURANÇA: Nenhum hash fornecido para verificação. Download rejeitado por segurança.",
                error_type="security_warning"
            )
        
        # Cria diretório temporário
        os.makedirs(self.temp_dir, exist_ok=True)
        temp_file_path = os.path.join(self.temp_dir, f"{component_name}.tmp")
        
        try:
            # Executa download
            download_success, error_msg = self._download_from_url(
                url, temp_file_path, component_name
            )
            
            if not download_success:
                return DownloadResult(
                    success=False,
                    message=f"Falha no download: {error_msg}",
                    error_type="download_error"
                )
            
            # Calcula hash do arquivo baixado
            calculated_hash = self._calculate_file_hash(temp_file_path, algorithm)
            
            if calculated_hash.lower() == expected_hash.lower():
                # Verificação passou - move arquivo para local final
                final_path = temp_file_path.replace('.tmp', '')
                os.rename(temp_file_path, final_path)
                
                file_size = os.path.getsize(final_path)
                download_time = time.time() - start_time
                
                return DownloadResult(
                    success=True,
                    file_path=final_path,
                    message=f"Download verificado com sucesso ({algorithm.upper()})",
                    verification_passed=True,
                    download_time=download_time,
                    file_size=file_size
                )
            else:
                # Falha na verificação - remove arquivo corrompido
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                return DownloadResult(
                    success=False,
                    message=f"Falha na verificação de integridade. Esperado: {expected_hash}, Calculado: {calculated_hash}",
                    error_type="verification_failed",
                    verification_passed=False
                )
                
        except Exception as e:
            # Limpa arquivo temporário em caso de erro
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return DownloadResult(
                success=False,
                message=f"Erro inesperado: {str(e)}",
                error_type="unexpected_error"
            )

    def download_with_retry(self, url: str, expected_hash: str, 
                           max_retries: int = 3, algorithm: str = 'sha256') -> DownloadResult:
        """
        Baixa arquivo com retry automático para falhas de verificação (Requisito 2.2)
        
        Args:
            url: URL para download
            expected_hash: Hash esperado
            max_retries: Número máximo de tentativas (padrão: 3)
            algorithm: Algoritmo de hash
            
        Returns:
            DownloadResult com informações de retry
        """
        last_result = None
        
        for attempt in range(max_retries):
            logger.info(f"Tentativa de download {attempt + 1}/{max_retries}: {url}")
            
            result = self.download_with_verification(url, expected_hash, algorithm)
            last_result = result
            result.retry_count = attempt
            
            if result.success:
                logger.info(f"Download bem-sucedido na tentativa {attempt + 1}")
                return result
            
            if result.error_type == "security_warning":
                # Não faz retry para avisos de segurança
                logger.warning("Download rejeitado por falta de hash - não fazendo retry")
                return result
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Backoff exponencial
                logger.warning(f"Tentativa {attempt + 1} falhou: {result.message}")
                logger.info(f"Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
        
        # Todas as tentativas falharam (Requisito 2.3)
        error_msg = self._generate_failure_report(url, last_result, max_retries)
        
        return DownloadResult(
            success=False,
            message=error_msg,
            error_type="max_retries_exceeded",
            retry_count=max_retries
        )

    def download_file(self, component_data: Dict, download_dir: str, 
                     progress_callback: Optional[Callable[[DownloadProgress], None]] = None) -> DownloadResult:
        """
        Interface principal para download de componentes com verificação obrigatória
        
        Args:
            component_data: Dados do componente com informações de checksum
            download_dir: Diretório de destino
            progress_callback: Callback para progresso
            
        Returns:
            DownloadResult com informações completas
        """
        component_name = component_data.get('name', 'unknown')
        
        # Verifica conectividade
        if not test_internet_connection():
            return DownloadResult(
                success=False,
                message="Sem conexão com a internet",
                error_type="connectivity_error"
            )
        
        # Obtém URLs de download
        download_urls = self.get_download_urls(component_data)
        if not download_urls:
            return DownloadResult(
                success=False,
                message="Nenhuma URL de download disponível",
                error_type="no_urls"
            )
        
        # Verifica se há informações de checksum (Requisito 2.1)
        if 'checksum' not in component_data:
            return DownloadResult(
                success=False,
                message="AVISO DE SEGURANÇA: Componente não possui informações de checksum. Download rejeitado por segurança.",
                error_type="security_warning"
            )
        
        # Extrai informações de checksum
        checksum_info = component_data['checksum']
        if isinstance(checksum_info, str):
            expected_hash = checksum_info
            algorithm = 'sha256'
        elif isinstance(checksum_info, dict):
            expected_hash = checksum_info.get('value')
            algorithm = checksum_info.get('algorithm', 'sha256')
        else:
            return DownloadResult(
                success=False,
                message="Formato de checksum inválido",
                error_type="invalid_checksum_format"
            )
        
        # Cria diretório de destino
        os.makedirs(download_dir, exist_ok=True)
        
        # Usa sistema de mirrors automático para a URL principal (Requisito 2.5)
        primary_url = download_urls[0] if download_urls else None
        if primary_url:
            logger.info(f"Tentando download com sistema de mirrors para: {primary_url}")
            result = self.download_with_mirrors(primary_url, expected_hash, algorithm=algorithm)
            
            if result.success:
                # Move arquivo para diretório final
                filename = self._get_filename(component_data, primary_url)
                final_path = os.path.join(download_dir, filename)
                
                if os.path.exists(result.file_path):
                    os.rename(result.file_path, final_path)
                    result.file_path = final_path
                
                logger.info(f"Download de {component_name} concluído com sucesso")
                return result
            
            logger.warning(f"Sistema de mirrors falhou: {result.message}")
        
        # Fallback: tenta URLs adicionais definidas no componente
        if len(download_urls) > 1:
            logger.info("Tentando URLs adicionais definidas no componente...")
            for url_index, url in enumerate(download_urls[1:], 2):
                logger.info(f"Tentando URL {url_index}/{len(download_urls)}: {url}")
                
                result = self.download_with_retry(url, expected_hash, algorithm=algorithm)
                
                if result.success:
                    # Move arquivo para diretório final
                    filename = self._get_filename(component_data, url)
                    final_path = os.path.join(download_dir, filename)
                    
                    if os.path.exists(result.file_path):
                        os.rename(result.file_path, final_path)
                        result.file_path = final_path
                    
                    logger.info(f"Download de {component_name} concluído com sucesso")
                    return result
                
                logger.warning(f"Falha na URL {url_index}: {result.message}")
        
        # Todas as tentativas falharam
        return DownloadResult(
            success=False,
            message=f"Falha em todas as URLs disponíveis (incluindo mirrors automáticos)",
            error_type="all_urls_failed"
        )
    
    def _download_from_url(self, url: str, file_path: str, component_name: str,
                          progress_callback: Optional[Callable[[DownloadProgress], None]] = None) -> Tuple[bool, str]:
        """
        Executa download de uma URL específica com tracking detalhado de progresso
        
        Args:
            url: URL para download
            file_path: Caminho do arquivo de destino
            component_name: Nome do componente
            progress_callback: Callback de progresso
            
        Returns:
            Tupla (sucesso, mensagem_erro)
        """
        try:
            # Inicia requisição
            headers = {
                'User-Agent': 'Environment-Dev-Script/1.0'
            }
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Obtém tamanho total
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            start_time = datetime.now()
            last_update_time = start_time
            chunk_count = 0
            
            # Cria objeto de progresso inicial
            progress = DownloadProgress(
                total_size=total_size,
                downloaded_size=0,
                speed=0,
                eta=0,
                percentage=0,
                status=DownloadStatus.DOWNLOADING,
                message=f"Iniciando download de {component_name}...",
                start_time=start_time,
                url=url,
                component_name=component_name
            )
            
            # Log detalhado do início do download
            logger.info(f"Iniciando download: {url}")
            logger.info(f"Tamanho do arquivo: {progress.format_size(total_size) if total_size > 0 else 'Desconhecido'}")
            
            # Atualiza progresso inicial
            if progress_callback:
                progress_callback(progress)
            
            # Download em chunks com tracking detalhado
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        chunk_count += 1
                        
                        current_time = datetime.now()
                        elapsed_time = (current_time - start_time).total_seconds()
                        
                        # Calcula progresso detalhado
                        if progress_callback and total_size > 0:
                            # Velocidade instantânea (baseada no último chunk)
                            time_since_last_update = (current_time - last_update_time).total_seconds()
                            instantaneous_speed = len(chunk) / time_since_last_update if time_since_last_update > 0 else 0
                            
                            # Velocidade média geral
                            average_speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                            
                            # Atualiza objeto de progresso
                            progress.downloaded_size = downloaded_size
                            progress.elapsed_time = elapsed_time
                            progress.instantaneous_speed = instantaneous_speed
                            progress.chunk_count = chunk_count
                            progress.last_update_time = current_time
                            progress.percentage = (downloaded_size / total_size) * 100
                            
                            # Atualiza histórico de velocidade para média móvel
                            progress.update_speed_history(instantaneous_speed)
                            
                            # Calcula ETA baseado na velocidade média móvel
                            if progress.average_speed > 0:
                                progress.eta = (total_size - downloaded_size) / progress.average_speed
                            else:
                                progress.eta = 0
                            
                            progress.speed = progress.average_speed
                            progress.message = f"Baixando {component_name}... {progress.get_detailed_status()}"
                            
                            # Callback de progresso (limitado para não sobrecarregar)
                            if chunk_count % 10 == 0 or time_since_last_update >= 0.5:  # Atualiza a cada 10 chunks ou 0.5s
                                progress_callback(progress)
                                last_update_time = current_time
                                
                                # Log detalhado a cada 5% de progresso
                                if int(progress.percentage) % 5 == 0 and int(progress.percentage) > 0:
                                    logger.debug(f"Download {component_name}: {progress.get_detailed_status()}")
            
            # Calcula estatísticas finais
            final_time = datetime.now()
            total_elapsed = (final_time - start_time).total_seconds()
            final_speed = downloaded_size / total_elapsed if total_elapsed > 0 else 0
            
            # Log detalhado da conclusão
            logger.info(f"Download concluído: {component_name}")
            logger.info(f"Tamanho final: {progress.format_size(downloaded_size)}")
            logger.info(f"Tempo total: {progress.format_time(total_elapsed)}")
            logger.info(f"Velocidade média: {progress.format_speed(final_speed)}")
            logger.info(f"Chunks processados: {chunk_count}")
            
            # Progresso final
            if progress_callback:
                progress.downloaded_size = downloaded_size
                progress.elapsed_time = total_elapsed
                progress.speed = final_speed
                progress.average_speed = final_speed
                progress.eta = 0
                progress.percentage = 100
                progress.status = DownloadStatus.COMPLETED
                progress.message = f"Download de {component_name} concluído - {progress.format_size(downloaded_size)} em {progress.format_time(total_elapsed)}"
                progress_callback(progress)
            
            return True, ""
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de rede: {e}"
            logger.error(f"Falha no download de {component_name}: {error_msg}")
            return False, error_msg
        except IOError as e:
            error_msg = f"Erro de E/S: {e}"
            logger.error(f"Falha no download de {component_name}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Erro inesperado: {e}"
            logger.error(f"Falha no download de {component_name}: {error_msg}")
            return False, error_msg
    
    def cleanup_failed_downloads(self, directory: str = None) -> List[str]:
        """
        Limpa downloads corrompidos e arquivos temporários (Requisito 2.3)
        
        Args:
            directory: Diretório para limpeza (padrão: temp_dir)
            
        Returns:
            Lista de arquivos removidos
        """
        if directory is None:
            directory = self.temp_dir
        
        if not os.path.exists(directory):
            return []
        
        removed_files = []
        corrupted_extensions = ['.tmp', '.partial', '.corrupted', '.download']
        
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Remove arquivos com extensões de arquivos corrompidos
                if any(filename.endswith(ext) for ext in corrupted_extensions):
                    try:
                        os.remove(file_path)
                        removed_files.append(file_path)
                        logger.info(f"Arquivo corrompido removido: {filename}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo {filename}: {e}")
                
                # Remove arquivos muito antigos (mais de 24h)
                elif os.path.isfile(file_path):
                    try:
                        file_age = time.time() - os.path.getmtime(file_path)
                        if file_age > 24 * 3600:  # 24 horas
                            os.remove(file_path)
                            removed_files.append(file_path)
                            logger.info(f"Arquivo antigo removido: {filename}")
                    except Exception as e:
                        logger.warning(f"Erro ao verificar idade do arquivo {filename}: {e}")
        
        except Exception as e:
            logger.error(f"Erro na limpeza de downloads: {e}")
        
        logger.info(f"Limpeza concluída: {len(removed_files)} arquivos removidos")
        return removed_files
    
    def get_download_progress(self, download_id: str) -> Optional[DownloadProgress]:
        """
        Obtém progresso de um download ativo (Requisito 2.4)
        
        Args:
            download_id: ID do download
            
        Returns:
            DownloadProgress ou None se não encontrado
        """
        with self.download_lock:
            if download_id in self.active_downloads:
                return self.active_downloads[download_id].progress
        return None
    
    def verify_file_integrity(self, file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        Verifica integridade de um arquivo usando hash (Requisito 2.1)
        
        Args:
            file_path: Caminho do arquivo
            expected_hash: Hash esperado
            algorithm: Algoritmo de hash
            
        Returns:
            True se a verificação passou
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            calculated_hash = self._calculate_file_hash(file_path, algorithm)
            return calculated_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"Erro na verificação de integridade: {e}")
            return False
    
    def _generate_failure_report(self, url: str, last_result: DownloadResult, max_retries: int) -> str:
        """
        Gera relatório detalhado de falha (Requisito 2.3)
        
        Args:
            url: URL que falhou
            last_result: Último resultado de tentativa
            max_retries: Número máximo de tentativas
            
        Returns:
            Relatório detalhado de falha
        """
        report_lines = [
            f"❌ FALHA NO DOWNLOAD APÓS {max_retries} TENTATIVAS",
            f"URL: {url}",
            f"Último erro: {last_result.message}",
            f"Tipo de erro: {last_result.error_type}",
            "",
            "🔧 SUGESTÕES PARA RESOLVER:",
            "1. Verifique sua conexão com a internet",
            "2. Tente novamente mais tarde (servidor pode estar temporariamente indisponível)",
            "3. Se o problema persistir, baixe o arquivo manualmente do site oficial",
            "4. Verifique se o arquivo pode estar corrompido no servidor",
            "5. Entre em contato com o suporte se necessário",
            "",
            f"⚠️  Para download manual, acesse: {url}",
            "   Após o download manual, coloque o arquivo no diretório de downloads"
        ]
        
        return "\n".join(report_lines)
    
    def _get_filename(self, component_data: Dict, url: str) -> str:
        """
        Determina nome do arquivo para download
        
        Args:
            component_data: Dados do componente
            url: URL de download
            
        Returns:
            Nome do arquivo
        """
        # Verifica se há nome específico no componente
        if 'filename' in component_data:
            return component_data['filename']
        
        # Extrai da URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Fallback se não conseguir extrair
        if not filename or '.' not in filename:
            component_name = component_data.get('name', 'download')
            filename = f"{component_name}.exe"  # Assume executável por padrão
        
        return filename
    
    def cancel_download(self, component_name: str) -> bool:
        """
        Cancela download em andamento
        
        Args:
            component_name: Nome do componente
            
        Returns:
            True se cancelado com sucesso
        """
        try:
            with self.download_lock:
                if component_name not in self.active_downloads:
                    logger.warning(f"Download {component_name} não encontrado")
                    return False
                
                download_info = self.active_downloads[component_name]
                
                # Marca como cancelado
                download_info['status'] = DownloadStatus.CANCELLED
                download_info['cancelled'] = True
                
                # Se há uma sessão de requests ativa, tenta cancelar
                if 'session' in download_info:
                    try:
                        download_info['session'].close()
                    except Exception as e:
                        logger.debug(f"Erro ao fechar sessão de download: {e}")
                
                # Remove arquivo parcial se existir
                temp_file = download_info.get('temp_file')
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.info(f"Arquivo temporário removido: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo temporário {temp_file}: {e}")
                
                logger.info(f"Download {component_name} cancelado com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao cancelar download {component_name}: {e}")
            return False
    
    def get_download_status(self, component_name: str) -> Optional[DownloadStatus]:
        """
        Obtém status de download
        
        Args:
            component_name: Nome do componente
            
        Returns:
            Status do download ou None se não encontrado
        """
        with self.download_lock:
            return self.active_downloads.get(component_name, {}).get('status')
    
    def cleanup_failed_downloads(self, download_dir: str = None):
        """
        Remove arquivos de downloads corrompidos (Requisito 2.3)
        
        Args:
            download_dir: Diretório de downloads (opcional, usa temp_dir se não especificado)
        """
        directories_to_clean = []
        
        if download_dir:
            directories_to_clean.append(download_dir)
        
        # Sempre limpa o diretório temporário
        directories_to_clean.append(self.temp_dir)
        
        cleaned_files = []
        
        for dir_path in directories_to_clean:
            try:
                if os.path.exists(dir_path):
                    for file in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, file)
                        if os.path.isfile(file_path):
                            # Remove arquivos temporários e corrompidos
                            if (file.endswith('.tmp') or 
                                file.endswith('.partial') or 
                                file.endswith('.corrupted')):
                                os.remove(file_path)
                                cleaned_files.append(file_path)
                                logger.info(f"Removido arquivo corrompido: {file}")
            except Exception as e:
                logger.error(f"Erro na limpeza de downloads em {dir_path}: {e}")
        
        if cleaned_files:
            logger.info(f"Limpeza concluída: {len(cleaned_files)} arquivos removidos")
        else:
            logger.debug("Nenhum arquivo corrompido encontrado para limpeza")
        
        return cleaned_files

    def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calcula hash de um arquivo usando o algoritmo especificado
        
        Args:
            file_path: Caminho do arquivo
            algorithm: Algoritmo de hash (md5, sha1, sha256, sha512)
            
        Returns:
            Hash hexadecimal do arquivo
        """
        hash_algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }
        
        if algorithm.lower() not in hash_algorithms:
            raise ValueError(f"Algoritmo {algorithm} não suportado")
        
        hash_func = hash_algorithms[algorithm.lower()]()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()

    def _generate_failure_report(self, url: str, last_result: DownloadResult, 
                                max_retries: int) -> str:
        """
        Gera relatório detalhado de falha para múltiplas tentativas (Requisito 2.3)
        
        Args:
            url: URL que falhou
            last_result: Último resultado de tentativa
            max_retries: Número de tentativas realizadas
            
        Returns:
            Mensagem detalhada com sugestões
        """
        base_msg = f"Falha após {max_retries} tentativas de download de {url}"
        
        if not last_result:
            return f"{base_msg}. Erro desconhecido."
        
        error_details = f"Último erro: {last_result.message}"
        
        # Sugestões específicas baseadas no tipo de erro
        suggestions = []
        
        if last_result.error_type == "verification_failed":
            suggestions.extend([
                "• O arquivo pode estar corrompido no servidor",
                "• Verifique se o hash esperado está correto",
                "• Tente novamente mais tarde"
            ])
        elif last_result.error_type == "download_error":
            suggestions.extend([
                "• Verifique sua conexão com a internet",
                "• O servidor pode estar temporariamente indisponível",
                "• Tente usar uma VPN se houver bloqueios regionais"
            ])
        elif last_result.error_type == "connectivity_error":
            suggestions.extend([
                "• Verifique sua conexão com a internet",
                "• Verifique configurações de proxy/firewall",
                "• Tente novamente quando a conexão estiver estável"
            ])
        
        # Sugestão de download manual
        suggestions.append("• Como alternativa, baixe o arquivo manualmente e coloque no diretório de downloads")
        
        suggestion_text = "\n".join(suggestions) if suggestions else ""
        
        return f"{base_msg}\n\n{error_details}\n\nSugestões para resolver:\n{suggestion_text}"

    def verify_file_integrity(self, file_path: str, expected_hash: str, 
                             algorithm: str = 'sha256') -> bool:
        """
        Verifica integridade de um arquivo já baixado
        
        Args:
            file_path: Caminho do arquivo
            expected_hash: Hash esperado
            algorithm: Algoritmo de hash
            
        Returns:
            True se o arquivo for íntegro
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado para verificação: {file_path}")
                return False
            
            calculated_hash = self._calculate_file_hash(file_path, algorithm)
            is_valid = calculated_hash.lower() == expected_hash.lower()
            
            if is_valid:
                logger.info(f"Verificação de integridade OK: {file_path}")
            else:
                logger.warning(f"Falha na verificação de integridade: {file_path}")
                logger.warning(f"Esperado: {expected_hash}, Calculado: {calculated_hash}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Erro na verificação de integridade: {e}")
            return False

    def get_download_progress(self, download_id: str) -> Optional[DownloadProgress]:
        """
        Obtém informações de progresso de um download ativo
        
        Args:
            download_id: ID do download
            
        Returns:
            ProgressInfo ou None se não encontrado
        """
        with self.download_lock:
            download_info = self.active_downloads.get(download_id)
            if download_info:
                return download_info.progress
            return None

    def _get_filename(self, component_data: Dict, url: str) -> str:
        """
        Obtém nome do arquivo para download
        
        Args:
            component_data: Dados do componente
            url: URL de download
            
        Returns:
            Nome do arquivo
        """
        # Tenta obter nome do componente
        if 'filename' in component_data:
            return component_data['filename']
        
        # Extrai nome da URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        if filename and '.' in filename:
            return filename
        
        # Fallback para nome do componente
        component_name = component_data.get('name', 'download')
        return f"{component_name}.exe"
    
    def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calcula hash de um arquivo
        
        Args:
            file_path: Caminho do arquivo
            algorithm: Algoritmo de hash
            
        Returns:
            Hash calculado em hexadecimal
        """
        hash_obj = hashlib.new(algorithm.lower())
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()


# Instância global do gerenciador de downloads
download_manager = DownloadManager()