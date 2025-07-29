# -*- coding: utf-8 -*-
"""
Gerenciador de Checksums para Environment Dev Script
Implementa verificação robusta de integridade de arquivos
"""

import hashlib
import logging
import requests
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ChecksumManager:
    """
    Gerencia verificação de checksums para downloads e arquivos
    """
    
    SUPPORTED_ALGORITHMS = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }
    
    def __init__(self):
        self.checksums_cache = {}
        
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calcula o hash de um arquivo
        
        Args:
            file_path: Caminho para o arquivo
            algorithm: Algoritmo de hash (md5, sha1, sha256, sha512)
            
        Returns:
            Hash hexadecimal do arquivo
            
        Raises:
            ValueError: Se o algoritmo não for suportado
            FileNotFoundError: Se o arquivo não existir
        """
        if algorithm.lower() not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Algoritmo {algorithm} não suportado. Use: {list(self.SUPPORTED_ALGORITHMS.keys())}")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        hash_func = self.SUPPORTED_ALGORITHMS[algorithm.lower()]()
        
        try:
            with open(file_path, 'rb') as f:
                # Lê o arquivo em chunks para economizar memória
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
                    
            calculated_hash = hash_func.hexdigest()
            logger.debug(f"Hash {algorithm} calculado para {file_path}: {calculated_hash}")
            return calculated_hash
            
        except Exception as e:
            logger.error(f"Erro ao calcular hash de {file_path}: {e}")
            raise
    
    def verify_file_integrity(self, file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        Verifica a integridade de um arquivo comparando com hash esperado
        
        Args:
            file_path: Caminho para o arquivo
            expected_hash: Hash esperado
            algorithm: Algoritmo usado
            
        Returns:
            True se o arquivo for íntegro, False caso contrário
        """
        try:
            calculated_hash = self.calculate_file_hash(file_path, algorithm)
            is_valid = calculated_hash.lower() == expected_hash.lower()
            
            if is_valid:
                logger.info(f"Verificação de integridade OK: {file_path}")
            else:
                logger.warning(f"Falha na verificação de integridade: {file_path}")
                logger.warning(f"Esperado: {expected_hash}")
                logger.warning(f"Calculado: {calculated_hash}")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Erro na verificação de integridade: {e}")
            return False
    
    def download_checksum_file(self, checksum_url: str, timeout: int = 30) -> Optional[Dict[str, str]]:
        """
        Baixa arquivo de checksums de uma URL
        
        Args:
            checksum_url: URL do arquivo de checksums
            timeout: Timeout para download
            
        Returns:
            Dicionário com nome_arquivo: hash ou None se falhar
        """
        try:
            logger.info(f"Baixando checksums de: {checksum_url}")
            response = requests.get(checksum_url, timeout=timeout)
            response.raise_for_status()
            
            checksums = {}
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Formato: hash filename ou hash *filename
                parts = line.split()
                if len(parts) >= 2:
                    hash_value = parts[0]
                    filename = parts[1].lstrip('*')
                    checksums[filename] = hash_value
                    
            logger.info(f"Carregados {len(checksums)} checksums")
            return checksums
            
        except Exception as e:
            logger.error(f"Erro ao baixar checksums: {e}")
            return None
    
    def verify_download_integrity(self, file_path: str, component_data: Dict) -> Tuple[bool, str]:
        """
        Verifica integridade de um download usando dados do componente
        
        Args:
            file_path: Caminho do arquivo baixado
            component_data: Dados do componente com informações de checksum
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Verifica se há informações de checksum
            if 'checksum' not in component_data:
                return False, "Nenhuma informação de checksum disponível"
                
            checksum_info = component_data['checksum']
            
            # Suporte a diferentes formatos de checksum
            if isinstance(checksum_info, str):
                # Formato simples: apenas o hash (assume SHA256)
                expected_hash = checksum_info
                algorithm = 'sha256'
            elif isinstance(checksum_info, dict):
                # Formato detalhado com algoritmo
                algorithm = checksum_info.get('algorithm', 'sha256')
                expected_hash = checksum_info.get('value')
                
                if not expected_hash:
                    return False, "Hash não especificado nas informações de checksum"
            else:
                return False, "Formato de checksum inválido"
            
            # Verifica integridade
            is_valid = self.verify_file_integrity(file_path, expected_hash, algorithm)
            
            if is_valid:
                return True, f"Arquivo verificado com sucesso ({algorithm.upper()})"
            else:
                return False, f"Falha na verificação de integridade ({algorithm.upper()})"
                
        except Exception as e:
            logger.error(f"Erro na verificação de download: {e}")
            return False, f"Erro na verificação: {str(e)}"
    
    def generate_checksums_for_directory(self, directory: str, algorithm: str = 'sha256') -> Dict[str, str]:
        """
        Gera checksums para todos os arquivos em um diretório
        
        Args:
            directory: Diretório para processar
            algorithm: Algoritmo de hash
            
        Returns:
            Dicionário com arquivo: hash
        """
        checksums = {}
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.error(f"Diretório não encontrado: {directory}")
            return checksums
            
        try:
            for file_path in directory_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(directory_path)
                    hash_value = self.calculate_file_hash(str(file_path), algorithm)
                    checksums[str(relative_path)] = hash_value
                    
            logger.info(f"Gerados checksums para {len(checksums)} arquivos")
            return checksums
            
        except Exception as e:
            logger.error(f"Erro ao gerar checksums: {e}")
            return checksums
    
    def save_checksums_file(self, checksums: Dict[str, str], output_file: str, algorithm: str = 'sha256'):
        """
        Salva checksums em arquivo no formato padrão
        
        Args:
            checksums: Dicionário com arquivo: hash
            output_file: Arquivo de saída
            algorithm: Algoritmo usado
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Checksums gerados com {algorithm.upper()}\n")
                f.write(f"# Formato: {algorithm} *arquivo\n\n")
                
                for filename, hash_value in sorted(checksums.items()):
                    f.write(f"{hash_value} *{filename}\n")
                    
            logger.info(f"Checksums salvos em: {output_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar checksums: {e}")
            raise

# Instância global para uso em outros módulos
checksum_manager = ChecksumManager()