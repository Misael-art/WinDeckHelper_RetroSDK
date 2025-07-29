#!/usr/bin/env python3
"""
Script para atualizar automaticamente todos os hashes pendentes nos arquivos YAML de componentes.

Este script:
1. Escaneia todos os arquivos YAML em busca de HASH_PENDENTE_VERIFICACAO
2. Baixa os arquivos temporariamente
3. Calcula os hashes SHA256
4. Atualiza os arquivos YAML com os hashes corretos

Uso: python update_pending_hashes.py [--dry-run] [--component NOME]
"""

import os
import sys
import yaml
import hashlib
import requests
import tempfile
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from env_dev.utils.log_manager import setup_logging
from env_dev.utils.downloader import Downloader
from env_dev.utils.checksum_manager import ChecksumManager

class HashUpdater:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.logger, self.log_manager = setup_logging()
        self.downloader = Downloader()
        self.checksum_manager = ChecksumManager()
        self.components_dir = Path(__file__).parent.parent / "env_dev" / "config" / "components"
        self.updated_count = 0
        self.failed_count = 0
        
    def find_yaml_files(self) -> List[Path]:
        """Encontra todos os arquivos YAML na pasta de componentes"""
        yaml_files = []
        for file_path in self.components_dir.glob("*.yaml"):
            yaml_files.append(file_path)
        return yaml_files
    
    def load_yaml_file(self, file_path: Path) -> Tuple[Dict, bool]:
        """Carrega um arquivo YAML e verifica se tem hashes pendentes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            has_pending = False
            if data:
                for component_name, component_data in data.items():
                    if isinstance(component_data, dict):
                        hash_value = component_data.get('hash', '')
                        if hash_value == 'HASH_PENDENTE_VERIFICACAO':
                            has_pending = True
                            break
            
            return data, has_pending
        except Exception as e:
            self.logger.error(f"Erro ao carregar {file_path}: {e}")
            return {}, False
    
    def calculate_file_hash(self, url: str) -> str:
        """Baixa um arquivo temporariamente e calcula seu hash SHA256"""
        try:
            self.logger.info(f"Baixando arquivo para calcular hash: {url}")
            
            # Cria um diretório temporário
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extrai o nome do arquivo da URL
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = "download_temp"
                
                temp_file_path = os.path.join(temp_dir, filename)
                
                # Baixa o arquivo
                success = self.downloader.download_file(url, temp_file_path)
                if not success:
                    raise Exception("Falha no download")
                
                # Calcula o hash
                hash_value = self.checksum_manager.calculate_file_hash(temp_file_path, 'sha256')
                self.logger.success(f"Hash calculado: {hash_value}")
                return hash_value
                
        except Exception as e:
            self.logger.error(f"Erro ao calcular hash para {url}: {e}")
            raise
    
    def update_component_hash(self, component_data: Dict, component_name: str) -> bool:
        """Atualiza o hash de um componente específico"""
        if not isinstance(component_data, dict):
            return False
            
        hash_value = component_data.get('hash', '')
        if hash_value != 'HASH_PENDENTE_VERIFICACAO':
            return False
            
        download_url = component_data.get('download_url')
        if not download_url:
            self.logger.warning(f"Componente {component_name} não tem download_url")
            return False
        
        try:
            # Calcula o novo hash
            new_hash = self.calculate_file_hash(download_url)
            
            # Atualiza o componente
            component_data['hash'] = new_hash
            self.logger.success(f"Hash atualizado para {component_name}: {new_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"Falha ao atualizar hash para {component_name}: {e}")
            return False
    
    def save_yaml_file(self, file_path: Path, data: Dict) -> bool:
        """Salva o arquivo YAML atualizado"""
        try:
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Salvaria alterações em: {file_path}")
                return True
            
            # Backup do arquivo original
            backup_path = file_path.with_suffix('.yaml.backup')
            if not backup_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)
                self.logger.info(f"Backup criado: {backup_path}")
            
            # Salva o arquivo atualizado
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            self.logger.success(f"Arquivo atualizado: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar {file_path}: {e}")
            return False
    
    def update_file(self, file_path: Path, target_component: str = None) -> bool:
        """Atualiza todos os hashes pendentes em um arquivo"""
        self.logger.info(f"Processando arquivo: {file_path}")
        
        data, has_pending = self.load_yaml_file(file_path)
        if not has_pending:
            self.logger.info(f"Nenhum hash pendente encontrado em: {file_path}")
            return True
        
        file_updated = False
        
        for component_name, component_data in data.items():
            if target_component and component_name != target_component:
                continue
                
            if self.update_component_hash(component_data, component_name):
                file_updated = True
                self.updated_count += 1
            else:
                # Verifica se era um hash pendente que falhou
                if isinstance(component_data, dict) and component_data.get('hash') == 'HASH_PENDENTE_VERIFICACAO':
                    self.failed_count += 1
        
        if file_updated:
            return self.save_yaml_file(file_path, data)
        
        return True
    
    def run(self, target_component: str = None) -> bool:
        """Executa a atualização de hashes"""
        self.logger.info("Iniciando atualização de hashes pendentes...")
        
        if self.dry_run:
            self.logger.info("MODO DRY RUN - Nenhuma alteração será feita")
        
        yaml_files = self.find_yaml_files()
        self.logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
        
        success = True
        for file_path in yaml_files:
            try:
                if not self.update_file(file_path, target_component):
                    success = False
            except Exception as e:
                self.logger.error(f"Erro ao processar {file_path}: {e}")
                success = False
        
        # Relatório final
        self.logger.info(f"\n=== RELATÓRIO FINAL ===")
        self.logger.info(f"Hashes atualizados com sucesso: {self.updated_count}")
        self.logger.info(f"Falhas na atualização: {self.failed_count}")
        
        if self.updated_count > 0:
            self.logger.success(f"✅ {self.updated_count} hashes foram atualizados!")
        
        if self.failed_count > 0:
            self.logger.warning(f"⚠️ {self.failed_count} hashes falharam na atualização")
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Atualiza hashes pendentes nos arquivos YAML")
    parser.add_argument('--dry-run', action='store_true', help="Executa sem fazer alterações")
    parser.add_argument('--component', type=str, help="Atualiza apenas um componente específico")
    
    args = parser.parse_args()
    
    updater = HashUpdater(dry_run=args.dry_run)
    success = updater.run(target_component=args.component)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()