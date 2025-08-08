"""Downloader robusto com retry, checksum e rollback
Implementa download seguro com verificação de integridade e limpeza automática"""

import os
import hashlib
import shutil
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Callable
import logging
import py7zr
import zipfile
import tarfile

from config.retro_devkit_constants import (
    DOWNLOAD_MAX_RETRIES, DOWNLOAD_TIMEOUT, TEMP_DOWNLOAD_PATH
)

class RobustDownloader:
    """Downloader com retry, verificação de checksum e rollback automático"""
    
    def __init__(self, logger: logging.Logger, base_path: Path):
        self.logger = logger
        self.base_path = base_path
        self.temp_path = base_path / TEMP_DOWNLOAD_PATH
        self.temp_path.mkdir(exist_ok=True)
        
    def download_and_extract(
        self,
        url: str,
        extract_path: Path,
        expected_checksum: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """Download e extração com verificação completa"""
        
        # Determinar nome do arquivo
        filename = url.split('/')[-1]
        download_path = self.temp_path / filename
        
        try:
            # Fase 1: Download com retry
            if not self._download_with_retry(url, download_path, progress_callback):
                return False
                
            # Fase 2: Verificação de checksum
            if expected_checksum and not self._verify_checksum(download_path, expected_checksum):
                self._cleanup_files([download_path])
                return False
                
            # Fase 3: Backup da pasta de destino (se existir)
            backup_path = None
            if extract_path.exists():
                backup_path = self._create_backup(extract_path)
                
            # Fase 4: Extração
            if not self._extract_archive(download_path, extract_path):
                # Rollback em caso de falha
                if backup_path:
                    self._restore_backup(backup_path, extract_path)
                self._cleanup_files([download_path])
                return False
                
            # Fase 5: Verificação pós-extração
            if not self._verify_extraction(extract_path):
                # Rollback em caso de falha
                if backup_path:
                    self._restore_backup(backup_path, extract_path)
                else:
                    self._cleanup_directories([extract_path])
                self._cleanup_files([download_path])
                return False
                
            # Fase 6: Limpeza final
            self._cleanup_files([download_path])
            if backup_path:
                self._cleanup_directories([backup_path])
                
            self.logger.info(f"✅ Download e extração concluídos: {extract_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante download/extração: {e}")
            self._cleanup_files([download_path])
            return False
            
    def _download_with_retry(
        self,
        url: str,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """Download com retry automático"""
        
        for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
            try:
                self.logger.info(f"📥 Tentativa {attempt}/{DOWNLOAD_MAX_RETRIES}: {url}")
                
                # Remover arquivo parcial se existir
                if file_path.exists():
                    file_path.unlink()
                    
                # Download com progress callback
                def reporthook(block_num, block_size, total_size):
                    if progress_callback:
                        progress_callback(block_num * block_size, total_size)
                        
                urllib.request.urlretrieve(url, file_path, reporthook)
                
                # Verificar se arquivo foi baixado completamente
                if file_path.exists() and file_path.stat().st_size > 0:
                    self.logger.info(f"✅ Download concluído: {file_path.name}")
                    return True
                    
            except urllib.error.URLError as e:
                self.logger.warning(f"⚠️ Erro de rede (tentativa {attempt}): {e}")
            except Exception as e:
                self.logger.warning(f"⚠️ Erro no download (tentativa {attempt}): {e}")
                
            if attempt < DOWNLOAD_MAX_RETRIES:
                wait_time = 2 ** attempt  # Backoff exponencial
                self.logger.info(f"⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
                
        self.logger.error(f"❌ Falha no download após {DOWNLOAD_MAX_RETRIES} tentativas")
        return False
        
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verifica checksum SHA-256 do arquivo"""
        try:
            self.logger.info("🔍 Verificando integridade do arquivo...")
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    
            actual_checksum = sha256_hash.hexdigest()
            
            if actual_checksum.lower() == expected_checksum.lower():
                self.logger.info("✅ Checksum verificado com sucesso")
                return True
            else:
                self.logger.error(
                    f"❌ Checksum inválido!\n"
                    f"Esperado: {expected_checksum}\n"
                    f"Atual: {actual_checksum}"
                )
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação de checksum: {e}")
            return False
            
    def _extract_archive(self, archive_path: Path, extract_path: Path) -> bool:
        """Extrai arquivo usando biblioteca Python apropriada"""
        try:
            self.logger.info(f"📦 Extraindo {archive_path.name}...")
            
            # Criar diretório de destino
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Determinar tipo de arquivo e extrair
            if archive_path.suffix.lower() == '.7z':
                with py7zr.SevenZipFile(archive_path, 'r') as archive:
                    archive.extractall(path=extract_path)
            elif archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as archive:
                    archive.extractall(path=extract_path)
            elif archive_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz']:
                with tarfile.open(archive_path, 'r:*') as archive:
                    archive.extractall(path=extract_path)
            else:
                self.logger.error(f"❌ Formato de arquivo não suportado: {archive_path.suffix}")
                return False
                
            self.logger.info("✅ Extração concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na extração: {e}")
            return False
            
    def _verify_extraction(self, extract_path: Path) -> bool:
        """Verifica se a extração foi bem-sucedida"""
        try:
            if not extract_path.exists():
                self.logger.error("❌ Diretório de extração não existe")
                return False
                
            # Listar conteúdo para diagnóstico
            contents = list(extract_path.iterdir())
            if not contents:
                self.logger.error("❌ Diretório de extração está vazio")
                self._log_directory_contents(extract_path)
                return False
                
            self.logger.info(f"✅ Extração verificada: {len(contents)} itens extraídos")
            self._log_directory_contents(extract_path)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação de extração: {e}")
            return False
            
    def _create_backup(self, path: Path) -> Optional[Path]:
        """Cria backup de um diretório"""
        try:
            timestamp = int(time.time())
            backup_path = self.base_path / "backups" / f"{path.name}_backup_{timestamp}"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"💾 Criando backup: {backup_path}")
            shutil.copytree(path, backup_path)
            return backup_path
            
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao criar backup: {e}")
            return None
            
    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restaura backup"""
        try:
            self.logger.info(f"🔄 Restaurando backup: {backup_path} -> {target_path}")
            
            if target_path.exists():
                shutil.rmtree(target_path)
                
            shutil.copytree(backup_path, target_path)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Falha ao restaurar backup: {e}")
            return False
            
    def _cleanup_files(self, file_paths: list[Path]) -> None:
        """Remove arquivos temporários"""
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"🗑️ Arquivo removido: {file_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao remover arquivo {file_path}: {e}")
                
    def _cleanup_directories(self, dir_paths: list[Path]) -> None:
        """Remove diretórios temporários"""
        for dir_path in dir_paths:
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    self.logger.debug(f"🗑️ Diretório removido: {dir_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao remover diretório {dir_path}: {e}")
                
    def _log_directory_contents(self, path: Path, max_items: int = 20) -> None:
        """Registra conteúdo do diretório para diagnóstico"""
        try:
            if not path.exists():
                self.logger.debug(f"📁 Diretório não existe: {path}")
                return
                
            contents = list(path.iterdir())
            self.logger.debug(f"📁 Conteúdo de {path} ({len(contents)} itens):")
            
            for i, item in enumerate(contents[:max_items]):
                item_type = "📁" if item.is_dir() else "📄"
                size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                self.logger.debug(f"  {item_type} {item.name}{size}")
                
            if len(contents) > max_items:
                self.logger.debug(f"  ... e mais {len(contents) - max_items} itens")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao listar diretório {path}: {e}")