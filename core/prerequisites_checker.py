"""Verificador de pré-requisitos para RetroDevKits
Implementa checagem antecipada de dependências antes da instalação"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from shutil import which
from typing import List, Dict, Tuple, Optional
import logging

from config.retro_devkit_constants import (
    REQUIRED_TOOLS, OPTIONAL_TOOLS, TEMP_DOWNLOAD_PATH
)

class PrerequisitesChecker:
    """Verifica e instala pré-requisitos necessários para RetroDevKits"""
    
    def __init__(self, logger: logging.Logger, base_path: Path):
        self.logger = logger
        self.base_path = base_path
        self.system = platform.system().lower()
        self.temp_path = base_path / TEMP_DOWNLOAD_PATH
        self.temp_path.mkdir(exist_ok=True)
        
    def check_all_prerequisites(self, devkit_name: str = None) -> bool:
        """Verifica todos os pré-requisitos necessários"""
        self.logger.info("🔍 Verificando pré-requisitos do sistema...")
        
        # Verificar ferramentas obrigatórias
        missing_required = self._check_required_tools()
        if missing_required:
            self.logger.error(
                f"❌ Dependências obrigatórias ausentes: {', '.join(missing_required)}. "
                "Instale antes de continuar."
            )
            return False
            
        # Verificar ferramentas opcionais e tentar instalar
        missing_optional = self._check_optional_tools()
        if missing_optional:
            self.logger.info(f"⚠️ Ferramentas opcionais ausentes: {', '.join(missing_optional)}")
            if not self._install_optional_tools(missing_optional):
                self.logger.warning("Algumas ferramentas opcionais não puderam ser instaladas")
                
        # Verificações específicas por devkit
        if devkit_name:
            if not self._check_devkit_specific_requirements(devkit_name):
                return False
                
        self.logger.info("✅ Verificação de pré-requisitos concluída com sucesso!")
        return True
        
    def _check_required_tools(self) -> List[str]:
        """Verifica ferramentas obrigatórias"""
        system_key = "windows" if self.system == "windows" else "linux"
        required = REQUIRED_TOOLS.get(system_key, [])
        
        missing = [tool for tool in required if which(tool) is None]
        
        for tool in required:
            if which(tool):
                self.logger.debug(f"✅ {tool} encontrado")
            else:
                self.logger.error(f"❌ {tool} não encontrado")
                
        return missing
        
    def _check_optional_tools(self) -> List[str]:
        """Verifica ferramentas opcionais"""
        system_key = "windows" if self.system == "windows" else "linux"
        optional = OPTIONAL_TOOLS.get(system_key, [])
        
        missing = [tool for tool in optional if which(tool) is None]
        
        for tool in optional:
            if which(tool):
                self.logger.debug(f"✅ {tool} encontrado")
            else:
                self.logger.warning(f"⚠️ {tool} não encontrado (será instalado automaticamente)")
                
        return missing
        
    def _install_optional_tools(self, missing_tools: List[str]) -> bool:
        """Instala ferramentas opcionais ausentes"""
        success = True
        
        for tool in missing_tools:
            self.logger.info(f"📦 Tentando instalar {tool}...")
            
            if tool == "7z" and self.system == "windows":
                if self._install_7zip_portable():
                    self.logger.info(f"✅ {tool} instalado com sucesso")
                else:
                    self.logger.warning(f"⚠️ Falha ao instalar {tool}")
                    success = False
            elif tool == "wget" and self.system == "windows":
                if self._install_wget_windows():
                    self.logger.info(f"✅ {tool} instalado com sucesso")
                else:
                    self.logger.warning(f"⚠️ Falha ao instalar {tool}")
                    success = False
            else:
                self.logger.warning(f"⚠️ Instalação automática de {tool} não implementada")
                success = False
                
        return success
        
    def _install_7zip_portable(self) -> bool:
        """Instala 7-Zip portátil no Windows"""
        try:
            url = "https://www.7-zip.org/a/7z2301-extra.7z"
            zip_path = self.temp_path / "7zip.7z"
            install_path = self.base_path / "tools" / "7zip"
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Download
            self.logger.info("Baixando 7-Zip portátil...")
            urllib.request.urlretrieve(url, zip_path)
            
            # Como não temos 7z ainda, usar PowerShell para extrair
            ps_command = f"""Expand-Archive -Path '{zip_path}' -DestinationPath '{install_path}' -Force"""
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Adicionar ao PATH temporariamente
                seven_zip_exe = install_path / "7za.exe"
                if seven_zip_exe.exists():
                    os.environ["PATH"] = str(install_path) + os.pathsep + os.environ["PATH"]
                    zip_path.unlink()  # Limpar arquivo temporário
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao instalar 7-Zip: {e}")
            return False
            
    def _install_wget_windows(self) -> bool:
        """Instala wget no Windows"""
        try:
            url = "https://eternallybored.org/misc/wget/1.21.4/64/wget.exe"
            install_path = self.base_path / "tools" / "wget"
            install_path.mkdir(parents=True, exist_ok=True)
            wget_exe = install_path / "wget.exe"
            
            self.logger.info("Baixando wget...")
            urllib.request.urlretrieve(url, wget_exe)
            
            if wget_exe.exists():
                # Adicionar ao PATH temporariamente
                os.environ["PATH"] = str(install_path) + os.pathsep + os.environ["PATH"]
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao instalar wget: {e}")
            return False
            
    def _check_devkit_specific_requirements(self, devkit_name: str) -> bool:
        """Verificações específicas por devkit"""
        if devkit_name.lower() in ["sgdk", "megadrive"]:
            return self._check_sgdk_requirements()
        elif devkit_name.lower() == "gbdk":
            return self._check_gbdk_requirements()
        # Adicionar outras verificações específicas conforme necessário
        return True
        
    def _check_sgdk_requirements(self) -> bool:
        """Verificações específicas para SGDK"""
        # Verificar versão do Java
        try:
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, text=True
            )
            if "11" not in result.stderr and "17" not in result.stderr and "21" not in result.stderr:
                self.logger.warning("⚠️ Java 11+ recomendado para SGDK")
                
        except Exception:
            self.logger.error("❌ Não foi possível verificar versão do Java")
            return False
            
        return True
        
    def _check_gbdk_requirements(self) -> bool:
        """Verificações específicas para GBDK"""
        # GBDK tem menos dependências, verificação básica
        return True
        
    def get_system_info(self) -> Dict[str, str]:
        """Retorna informações do sistema para diagnóstico"""
        return {
            "system": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": sys.version,
            "java_available": "sim" if which("java") else "não",
            "make_available": "sim" if which("make") else "não",
            "7z_available": "sim" if which("7z") else "não",
            "wget_available": "sim" if which("wget") else "não"
        }