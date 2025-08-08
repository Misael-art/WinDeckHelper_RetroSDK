"""Classe base para gerenciadores de devkits retro
Fornece estrutura comum e padrões para todos os devkits retro"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import zipfile
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class DevkitInfo:
    """Informações básicas de um devkit"""
    name: str
    console: str
    devkit_name: str
    version: str
    dependencies: List[str]
    environment_vars: Dict[str, str]
    download_url: str
    install_commands: List[str]
    verification_files: List[str]

class RetroDevkitManager(ABC):
    """Classe base abstrata para gerenciadores de devkits retro"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        self.base_path = base_path
        self.logger = logger
        self.devkit_path = None
        self.emulators_path = None
        self.tools_path = None
        self._setup_paths()
        
    def _setup_paths(self):
        """Configura os caminhos específicos do devkit"""
        self.devkit_path = self.base_path / self.get_devkit_folder_name()
        self.emulators_path = self.devkit_path / "_Emuladores"
        self.tools_path = self.devkit_path / "_Tools"
        
    @abstractmethod
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do devkit"""
        pass
        
    @abstractmethod
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações básicas do devkit"""
        pass
        
    @abstractmethod
    def install_dependencies(self) -> bool:
        """Instala dependências específicas do devkit"""
        pass
        
    @abstractmethod
    def verify_installation(self) -> bool:
        """Verifica se a instalação está correta"""
        pass
        
    @abstractmethod
    def install_emulators(self) -> bool:
        """Instala emuladores específicos do console"""
        pass
        
    @abstractmethod
    def install_vscode_extensions(self) -> bool:
        """Instala extensões do VS Code específicas"""
        pass
        
    @abstractmethod
    def create_convenience_scripts(self) -> bool:
        """Cria scripts de conveniência para desenvolvimento"""
        pass
        
    @abstractmethod
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto para o devkit"""
        pass
        
    def create_base_directories(self) -> bool:
        """Cria diretórios base necessários"""
        try:
            directories = [
                self.devkit_path,
                self.emulators_path,
                self.tools_path,
                self.devkit_path / "projects",
                self.devkit_path / "templates",
                self.devkit_path / "scripts"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Diretório criado: {directory}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar diretórios base: {e}")
            return False
            
    def download_file(self, url: str, destination: Path, description: str = "") -> bool:
        """Download de arquivo com progress e verificação"""
        try:
            self.logger.info(f"Baixando {description}: {url}")
            
            # Criar diretório de destino se não existir
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Download do arquivo
            urllib.request.urlretrieve(url, destination)
            
            # Verificar se o arquivo foi baixado
            if destination.exists() and destination.stat().st_size > 0:
                self.logger.info(f"Download concluído: {destination}")
                return True
            else:
                self.logger.error(f"Falha no download: arquivo vazio ou não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro no download de {url}: {e}")
            return False
            
    def extract_archive(self, archive_path: Path, destination: Path) -> bool:
        """Extrai arquivo compactado"""
        try:
            self.logger.info(f"Extraindo {archive_path} para {destination}")
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(destination)
            elif archive_path.suffix.lower() in ['.7z']:
                # Para arquivos 7z, usar 7zip se disponível
                result = subprocess.run(
                    ['7z', 'x', str(archive_path), f'-o{destination}'],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    self.logger.error(f"Erro ao extrair 7z: {result.stderr}")
                    return False
            else:
                self.logger.error(f"Formato de arquivo não suportado: {archive_path.suffix}")
                return False
                
            self.logger.info(f"Extração concluída: {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na extração de {archive_path}: {e}")
            return False
            
    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Executa comando e retorna resultado"""
        try:
            self.logger.info(f"Executando comando: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Comando executado com sucesso")
                return True, result.stdout
            else:
                self.logger.error(f"Comando falhou: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout na execução do comando")
            return False, "Timeout"
        except Exception as e:
            self.logger.error(f"Erro na execução do comando: {e}")
            return False, str(e)
            
    def check_dependency(self, dependency: str) -> bool:
        """Verifica se uma dependência está instalada"""
        try:
            result = subprocess.run(
                [dependency, '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
            
    def setup_environment_variables(self) -> bool:
        """Configura variáveis de ambiente do devkit"""
        try:
            devkit_info = self.get_devkit_info()
            
            for var_name, var_value in devkit_info.environment_vars.items():
                os.environ[var_name] = var_value
                self.logger.info(f"Variável de ambiente configurada: {var_name}={var_value}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar variáveis de ambiente: {e}")
            return False
            
    def install_full_devkit(self) -> bool:
        """Instalação completa do devkit"""
        try:
            self.logger.info(f"Iniciando instalação completa do {self.get_devkit_info().name}")
            
            # 1. Criar diretórios base
            if not self.create_base_directories():
                return False
                
            # 2. Instalar dependências
            if not self.install_dependencies():
                return False
                
            # 3. Configurar variáveis de ambiente
            if not self.setup_environment_variables():
                return False
                
            # 4. Instalar emuladores
            if not self.install_emulators():
                self.logger.warning("Falha na instalação de emuladores, continuando...")
                
            # 5. Instalar extensões VS Code
            if not self.install_vscode_extensions():
                self.logger.warning("Falha na instalação de extensões VS Code, continuando...")
                
            # 6. Criar scripts de conveniência
            if not self.create_convenience_scripts():
                self.logger.warning("Falha na criação de scripts, continuando...")
                
            # 7. Verificar instalação
            if not self.verify_installation():
                self.logger.error("Verificação da instalação falhou")
                return False
                
            self.logger.info(f"Instalação completa do {self.get_devkit_info().name} concluída com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação completa: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do devkit"""
        devkit_info = self.get_devkit_info()
        
        return {
            "name": devkit_info.name,
            "console": devkit_info.console,
            "devkit_name": devkit_info.devkit_name,
            "version": devkit_info.version,
            "installed": self.verify_installation(),
            "devkit_path": str(self.devkit_path),
            "emulators_path": str(self.emulators_path),
            "tools_path": str(self.tools_path)
        }