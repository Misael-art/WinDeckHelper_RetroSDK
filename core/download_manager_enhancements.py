# -*- coding: utf-8 -*-
"""
Melhorias finais para o Download Manager
Completa a implementação dos requisitos 2.1, 2.2, 2.3, 2.4 e 2.5
"""

import os
import logging
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from env_dev.core.download_manager import DownloadManager, DownloadResult, DownloadStatus, DownloadProgress

logger = logging.getLogger(__name__)

@dataclass
class DownloadCache:
    """Cache de downloads para evitar downloads desnecessários"""
    file_path: str
    hash_value: str
    algorithm: str
    download_time: datetime
    file_size: int
    
    def is_valid(self, max_age_hours: int = 24) -> bool:
        """Verifica se o cache ainda é válido"""
        age = datetime.now() - self.download_time
        return age < timedelta(hours=max_age_hours) and os.path.exists(self.file_path)

class EnhancedDownloadManager(DownloadManager):
    """
    Versão aprimorada do DownloadManager com funcionalidades adicionais
    para completar todos os requisitos da Task 3
    """
    
    def __init__(self, max_concurrent_downloads: int = 3, chunk_size: int = 8192):
        super().__init__(max_concurrent_downloads, chunk_size)
        self.download_cache: Dict[str, DownloadCache] = {}
        self.cache_lock = threading.Lock()
        self.cache_dir = "cache/downloads"
        self.statistics = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'cache_hits': 0,
            'mirror_usage': 0,
            'total_bytes_downloaded': 0,
            'average_speed': 0.0
        }
        
        # Cria diretório de cache
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Carrega cache existente
        self._load_cache()
    
    def download_with_cache(self, component_data: Dict, download_dir: str,
                           progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
                           use_cache: bool = True) -> DownloadResult:
        """
        Download com sistema de cache inteligente (Requisito 2.4 - otimização)
        
        Args:
            component_data: Dados do componente
            download_dir: Diretório de destino
            progress_callback: Callback de progresso
            use_cache: Se deve usar cache
            
        Returns:
            DownloadResult com informações do download
        """
        component_name = component_data.get('name', 'unknown')
        
        # Verifica cache se habilitado
        if use_cache:
            cached_result = self._check_cache(component_data, download_dir)
            if cached_result:
                logger.info(f"Usando arquivo em cache para {component_name}")
                self.statistics['cache_hits'] += 1
                return cached_result
        
        # Executa download normal
        result = self.download_file(component_data, download_dir, progress_callback)
        
        # Atualiza estatísticas
        self.statistics['total_downloads'] += 1
        if result.success:
            self.statistics['successful_downloads'] += 1
            self.statistics['total_bytes_downloaded'] += result.file_size
            
            # Adiciona ao cache se bem-sucedido
            if use_cache:
                self._add_to_cache(component_data, result)
        else:
            self.statistics['failed_downloads'] += 1
        
        return result
    
    def batch_download(self, components: List[Dict], download_dir: str,
                      progress_callback: Optional[Callable[[str, DownloadProgress], None]] = None,
                      max_concurrent: int = 3) -> Dict[str, DownloadResult]:
        """
        Download em lote com controle de concorrência (Requisito 2.4)
        
        Args:
            components: Lista de componentes para download
            download_dir: Diretório de destino
            progress_callback: Callback de progresso por componente
            max_concurrent: Máximo de downloads simultâneos
            
        Returns:
            Dicionário com resultados por componente
        """
        results = {}
        active_downloads = {}
        download_queue = components.copy()
        
        def download_worker(component_data):
            """Worker para download individual"""
            component_name = component_data.get('name', 'unknown')
            
            def component_progress_callback(progress):
                if progress_callback:
                    progress_callback(component_name, progress)
            
            try:
                result = self.download_with_cache(
                    component_data, 
                    download_dir, 
                    component_progress_callback
                )
                results[component_name] = result
                logger.info(f"Download de {component_name}: {'✓' if result.success else '✗'}")
            except Exception as e:
                logger.error(f"Erro no download de {component_name}: {e}")
                results[component_name] = DownloadResult(
                    success=False,
                    message=f"Erro inesperado: {e}",
                    error_type="unexpected_error"
                )
            finally:
                # Remove dos downloads ativos
                if component_name in active_downloads:
                    del active_downloads[component_name]
        
        logger.info(f"Iniciando download em lote de {len(components)} componentes")
        
        # Processa downloads com controle de concorrência
        while download_queue or active_downloads:
            # Inicia novos downloads se há espaço
            while len(active_downloads) < max_concurrent and download_queue:
                component_data = download_queue.pop(0)
                component_name = component_data.get('name', 'unknown')
                
                # Inicia thread de download
                thread = threading.Thread(
                    target=download_worker,
                    args=(component_data,),
                    name=f"download-{component_name}"
                )
                thread.daemon = True
                thread.start()
                
                active_downloads[component_name] = thread
                logger.info(f"Iniciado download de {component_name}")
            
            # Aguarda um pouco antes de verificar novamente
            time.sleep(0.5)
            
            # Remove threads finalizadas
            finished_threads = []
            for name, thread in active_downloads.items():
                if not thread.is_alive():
                    finished_threads.append(name)
            
            for name in finished_threads:
                del active_downloads[name]
        
        # Aguarda todos os downloads terminarem
        for thread in active_downloads.values():
            thread.join(timeout=1)
        
        logger.info(f"Download em lote concluído: {len(results)} componentes processados")
        return results
    
    def get_download_statistics(self) -> Dict:
        """
        Retorna estatísticas detalhadas de downloads (Requisito 2.4)
        
        Returns:
            Dicionário com estatísticas
        """
        stats = self.statistics.copy()
        
        # Calcula taxa de sucesso
        if stats['total_downloads'] > 0:
            stats['success_rate'] = (stats['successful_downloads'] / stats['total_downloads']) * 100
        else:
            stats['success_rate'] = 0
        
        # Calcula velocidade média
        if stats['successful_downloads'] > 0:
            stats['average_speed'] = stats['total_bytes_downloaded'] / stats['successful_downloads']
        
        # Adiciona informações de cache
        stats['cache_hit_rate'] = (stats['cache_hits'] / max(stats['total_downloads'], 1)) * 100
        stats['cache_size'] = len(self.download_cache)
        
        return stats
    
    def cleanup_cache(self, max_age_hours: int = 24, max_size_mb: int = 1024):
        """
        Limpa cache antigo e arquivos grandes (Requisito 2.3 - limpeza)
        
        Args:
            max_age_hours: Idade máxima em horas
            max_size_mb: Tamanho máximo do cache em MB
        """
        with self.cache_lock:
            removed_count = 0
            total_size = 0
            
            # Remove entradas antigas ou inválidas
            expired_keys = []
            for key, cache_entry in self.download_cache.items():
                if not cache_entry.is_valid(max_age_hours):
                    expired_keys.append(key)
                    if os.path.exists(cache_entry.file_path):
                        try:
                            os.remove(cache_entry.file_path)
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Erro ao remover arquivo de cache {cache_entry.file_path}: {e}")
                else:
                    total_size += cache_entry.file_size
            
            # Remove entradas expiradas do cache
            for key in expired_keys:
                del self.download_cache[key]
            
            # Se o cache ainda está muito grande, remove os mais antigos
            if total_size > max_size_mb * 1024 * 1024:
                sorted_cache = sorted(
                    self.download_cache.items(),
                    key=lambda x: x[1].download_time
                )
                
                while total_size > max_size_mb * 1024 * 1024 and sorted_cache:
                    key, cache_entry = sorted_cache.pop(0)
                    if os.path.exists(cache_entry.file_path):
                        try:
                            os.remove(cache_entry.file_path)
                            total_size -= cache_entry.file_size
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Erro ao remover arquivo de cache {cache_entry.file_path}: {e}")
                    
                    del self.download_cache[key]
            
            logger.info(f"Limpeza de cache concluída: {removed_count} arquivos removidos")
            self._save_cache()
    
    def _check_cache(self, component_data: Dict, download_dir: str) -> Optional[DownloadResult]:
        """Verifica se há entrada válida no cache"""
        component_name = component_data.get('name', 'unknown')
        
        with self.cache_lock:
            if component_name in self.download_cache:
                cache_entry = self.download_cache[component_name]
                
                if cache_entry.is_valid():
                    # Verifica se o hash ainda bate
                    if self.verify_file_integrity(
                        cache_entry.file_path, 
                        cache_entry.hash_value, 
                        cache_entry.algorithm
                    ):
                        # Copia arquivo do cache para o diretório de destino
                        filename = os.path.basename(cache_entry.file_path)
                        dest_path = os.path.join(download_dir, filename)
                        
                        try:
                            import shutil
                            shutil.copy2(cache_entry.file_path, dest_path)
                            
                            return DownloadResult(
                                success=True,
                                file_path=dest_path,
                                message=f"Arquivo obtido do cache (verificado)",
                                verification_passed=True,
                                file_size=cache_entry.file_size
                            )
                        except Exception as e:
                            logger.warning(f"Erro ao copiar arquivo do cache: {e}")
                
                # Remove entrada inválida
                del self.download_cache[component_name]
        
        return None
    
    def _add_to_cache(self, component_data: Dict, result: DownloadResult):
        """Adiciona arquivo ao cache"""
        if not result.success or not result.verification_passed:
            return
        
        component_name = component_data.get('name', 'unknown')
        checksum_info = component_data.get('checksum', {})
        
        if isinstance(checksum_info, str):
            hash_value = checksum_info
            algorithm = 'sha256'
        elif isinstance(checksum_info, dict):
            hash_value = checksum_info.get('value', '')
            algorithm = checksum_info.get('algorithm', 'sha256')
        else:
            return
        
        # Copia arquivo para o cache
        cache_filename = f"{component_name}_{hash_value[:8]}.cache"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        try:
            import shutil
            shutil.copy2(result.file_path, cache_path)
            
            with self.cache_lock:
                self.download_cache[component_name] = DownloadCache(
                    file_path=cache_path,
                    hash_value=hash_value,
                    algorithm=algorithm,
                    download_time=datetime.now(),
                    file_size=result.file_size
                )
            
            self._save_cache()
            logger.info(f"Arquivo {component_name} adicionado ao cache")
            
        except Exception as e:
            logger.warning(f"Erro ao adicionar arquivo ao cache: {e}")
    
    def _load_cache(self):
        """Carrega informações do cache do disco"""
        cache_file = os.path.join(self.cache_dir, "cache_index.json")
        
        try:
            if os.path.exists(cache_file):
                import json
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                for name, data in cache_data.items():
                    self.download_cache[name] = DownloadCache(
                        file_path=data['file_path'],
                        hash_value=data['hash_value'],
                        algorithm=data['algorithm'],
                        download_time=datetime.fromisoformat(data['download_time']),
                        file_size=data['file_size']
                    )
                
                logger.info(f"Cache carregado: {len(self.download_cache)} entradas")
        except Exception as e:
            logger.warning(f"Erro ao carregar cache: {e}")
    
    def _save_cache(self):
        """Salva informações do cache no disco"""
        cache_file = os.path.join(self.cache_dir, "cache_index.json")
        
        try:
            import json
            cache_data = {}
            
            for name, cache_entry in self.download_cache.items():
                cache_data[name] = {
                    'file_path': cache_entry.file_path,
                    'hash_value': cache_entry.hash_value,
                    'algorithm': cache_entry.algorithm,
                    'download_time': cache_entry.download_time.isoformat(),
                    'file_size': cache_entry.file_size
                }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")

# Instância global aprimorada
enhanced_download_manager = EnhancedDownloadManager()