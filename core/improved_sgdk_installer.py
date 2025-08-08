"""Instalador SGDK melhorado com todas as funcionalidades robustas
Implementa instalação completa com pré-requisitos, download seguro e rollback"""

import os
import platform
import subprocess
import logging
from pathlib import Path
from shutil import which
from typing import Dict, List, Optional, Tuple

from config.retro_devkit_constants import (
    SGDK_VERSION, SGDK_CHECKSUMS, SGDK_BASE_URL,
    WINDOWS_REQUIRED_TOOLS, WINDOWS_OPTIONAL_TOOLS,
    LINUX_REQUIRED_TOOLS, LINUX_OPTIONAL_TOOLS,
    DEFAULT_SGDK_PATH
)
from core.prerequisites_checker import PrerequisitesChecker
from core.robust_downloader import RobustDownloader

class ImprovedSGDKInstaller:
    """Instalador SGDK com todas as melhorias implementadas"""
    
    def __init__(self, logger: logging.Logger, base_path: Path):
        self.logger = logger
        self.base_path = base_path
        self.sgdk_path = base_path / DEFAULT_SGDK_PATH
        self.prerequisites_checker = PrerequisitesChecker(logger, base_path)
        self.downloader = RobustDownloader(logger, base_path)
        
    def install_sgdk(self, force_reinstall: bool = False) -> bool:
        """Instalação completa do SGDK com todas as verificações"""
        try:
            self.logger.info("🚀 Iniciando instalação do SGDK...")
            
            # Fase 1: Verificação de pré-requisitos
            if not self._check_prerequisites():
                return False
                
            # Fase 2: Verificação de instalação existente
            if not force_reinstall and self._is_sgdk_installed():
                self.logger.info("✅ SGDK já está instalado e funcionando")
                return True
                
            # Fase 3: Instalação de dependências do sistema
            if not self._install_system_dependencies():
                return False
                
            # Fase 4: Download e extração do SGDK
            if not self._download_and_extract_sgdk():
                return False
                
            # Fase 5: Configuração pós-instalação
            if not self._configure_sgdk():
                return False
                
            # Fase 6: Verificação final
            if not self._verify_installation():
                return False
                
            self.logger.info("🎉 SGDK instalado com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante instalação do SGDK: {e}")
            return False
            
    def _check_prerequisites(self) -> bool:
        """Verifica pré-requisitos antes de iniciar instalação"""
        self.logger.info("🔍 Verificando pré-requisitos...")
        
        # Verificar ferramentas obrigatórias
        system = platform.system().lower()
        required_tools = WINDOWS_REQUIRED_TOOLS if system == 'windows' else LINUX_REQUIRED_TOOLS
        
        missing_required = self.prerequisites_checker._check_required_tools()
        if missing_required:
            self.logger.error(
                f"❌ Dependências obrigatórias ausentes: {', '.join(missing_required)}\n"
                f"Por favor, instale-as antes de continuar."
            )
            return False
            
        # Verificar ferramentas opcionais
        optional_tools = WINDOWS_OPTIONAL_TOOLS if system == 'windows' else LINUX_OPTIONAL_TOOLS
        missing_optional = self.prerequisites_checker._check_optional_tools()
        
        if missing_optional:
            self.logger.warning(
                f"⚠️ Ferramentas opcionais ausentes: {', '.join(missing_optional)}\n"
                f"A instalação continuará, mas algumas funcionalidades podem não estar disponíveis."
            )
            
        # Verificação específica do SGDK
        if not self.prerequisites_checker._check_sgdk_requirements():
            return False
            
        self.logger.info("✅ Pré-requisitos verificados")
        return True
        
    def _is_sgdk_installed(self) -> bool:
        """Verifica se SGDK já está instalado e funcionando"""
        try:
            # Verificar arquivos essenciais
            essential_files = [
                self.sgdk_path / "bin" / "rescomp.jar",
                self.sgdk_path / "inc" / "genesis.h",
            ]
            
            # No Windows, verificar também o compilador
            if platform.system().lower() == 'windows':
                essential_files.append(self.sgdk_path / "bin" / "m68k-elf-gcc.exe")
                
            for file_path in essential_files:
                if not file_path.exists():
                    self.logger.debug(f"Arquivo essencial não encontrado: {file_path}")
                    return False
                    
            # Verificar se rescomp funciona
            rescomp_path = self.sgdk_path / "bin" / "rescomp.jar"
            try:
                result = subprocess.run(
                    ["java", "-jar", str(rescomp_path), "-help"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    self.logger.debug("rescomp.jar não está funcionando corretamente")
                    return False
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                self.logger.debug("Falha ao testar rescomp.jar")
                return False
                
            return True
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar instalação existente: {e}")
            return False
            
    def _install_system_dependencies(self) -> bool:
        """Instala dependências do sistema se necessário"""
        system = platform.system().lower()
        
        if system == 'windows':
            return self._install_windows_dependencies()
        else:
            return self._install_linux_dependencies()
            
    def _install_windows_dependencies(self) -> bool:
        """Instala dependências no Windows"""
        try:
            self.logger.info("🔧 Verificando dependências do Windows...")
            
            # Instalar 7-Zip portátil se necessário
            if not self.prerequisites_checker._install_7zip_portable():
                self.logger.warning("⚠️ Falha ao instalar 7-Zip portátil")
                
            # Instalar wget portátil se necessário
            if not self.prerequisites_checker._install_wget_windows():
                self.logger.warning("⚠️ Falha ao instalar wget portátil")
                
            # Verificar se Chocolatey está disponível para outras dependências
            if which("choco"):
                missing_tools = []
                
                if not which("java"):
                    missing_tools.append("openjdk11")
                    
                if not which("make"):
                    missing_tools.append("make")
                    
                if missing_tools:
                    self.logger.info(f"📦 Instalando via Chocolatey: {', '.join(missing_tools)}")
                    for tool in missing_tools:
                        result = subprocess.run(
                            ["choco", "install", tool, "-y"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            self.logger.warning(f"⚠️ Falha ao instalar {tool} via Chocolatey")
                            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar dependências do Windows: {e}")
            return False
            
    def _install_linux_dependencies(self) -> bool:
        """Instala dependências no Linux"""
        try:
            self.logger.info("🔧 Verificando dependências do Linux...")
            
            # Detectar gerenciador de pacotes
            package_managers = [
                ("apt", ["apt", "update"], ["apt", "install", "-y"]),
                ("yum", ["yum", "check-update"], ["yum", "install", "-y"]),
                ("dnf", ["dnf", "check-update"], ["dnf", "install", "-y"]),
                ("pacman", ["pacman", "-Sy"], ["pacman", "-S", "--noconfirm"])
            ]
            
            package_manager = None
            for pm_name, update_cmd, install_cmd in package_managers:
                if which(pm_name):
                    package_manager = (pm_name, update_cmd, install_cmd)
                    break
                    
            if not package_manager:
                self.logger.warning("⚠️ Nenhum gerenciador de pacotes conhecido encontrado")
                return True  # Continuar mesmo assim
                
            pm_name, update_cmd, install_cmd = package_manager
            
            # Mapear ferramentas para nomes de pacotes
            package_mapping = {
                "java": "openjdk-11-jdk",
                "make": "build-essential" if pm_name == "apt" else "make",
                "wget": "wget",
                "unzip": "unzip",
                "p7zip": "p7zip-full" if pm_name == "apt" else "p7zip"
            }
            
            missing_packages = []
            for tool in LINUX_REQUIRED_TOOLS:
                if not which(tool):
                    package_name = package_mapping.get(tool, tool)
                    missing_packages.append(package_name)
                    
            if missing_packages:
                self.logger.info(f"📦 Instalando via {pm_name}: {', '.join(missing_packages)}")
                
                # Atualizar cache de pacotes
                subprocess.run(update_cmd, capture_output=True)
                
                # Instalar pacotes
                for package in missing_packages:
                    result = subprocess.run(
                        install_cmd + [package],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        self.logger.warning(f"⚠️ Falha ao instalar {package} via {pm_name}")
                        
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar dependências do Linux: {e}")
            return False
            
    def _download_and_extract_sgdk(self) -> bool:
        """Download e extração do SGDK usando downloader robusto"""
        try:
            self.logger.info(f"📥 Baixando SGDK v{SGDK_VERSION}...")
            
            # Determinar URL e checksum baseado no sistema
            system = platform.system().lower()
            if system == 'windows':
                filename = f"sgdk{SGDK_VERSION.replace('.', '')}.7z"
                checksum = SGDK_CHECKSUMS.get(SGDK_VERSION, {}).get('windows')
            else:
                filename = f"sgdk{SGDK_VERSION.replace('.', '')}_linux.tar.gz"
                checksum = SGDK_CHECKSUMS.get(SGDK_VERSION, {}).get('linux')
                
            url = f"{SGDK_BASE_URL}/v{SGDK_VERSION}/{filename}"
            
            # Usar downloader robusto
            success = self.downloader.download_and_extract(
                url=url,
                extract_path=self.sgdk_path,
                expected_checksum=checksum,
                progress_callback=self._download_progress
            )
            
            if not success:
                self.logger.error("❌ Falha no download/extração do SGDK")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no download do SGDK: {e}")
            return False
            
    def _download_progress(self, downloaded: int, total: int) -> None:
        """Callback para progresso do download"""
        if total > 0:
            percent = (downloaded / total) * 100
            if percent % 10 == 0:  # Log a cada 10%
                self.logger.info(f"📥 Progresso: {percent:.0f}% ({downloaded}/{total} bytes)")
                
    def _configure_sgdk(self) -> bool:
        """Configuração pós-instalação do SGDK"""
        try:
            self.logger.info("⚙️ Configurando SGDK...")
            
            # Verificar estrutura de diretórios
            required_dirs = ["bin", "inc", "lib", "res"]
            for dir_name in required_dirs:
                dir_path = self.sgdk_path / dir_name
                if not dir_path.exists():
                    self.logger.warning(f"⚠️ Diretório esperado não encontrado: {dir_path}")
                    
            # Configurar variáveis de ambiente (opcional)
            self._setup_environment_variables()
            
            # Tornar executáveis executáveis no Linux
            if platform.system().lower() != 'windows':
                self._make_executables_executable()
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na configuração do SGDK: {e}")
            return False
            
    def _setup_environment_variables(self) -> None:
        """Configura variáveis de ambiente para SGDK"""
        try:
            # Definir GDK (SGDK path)
            os.environ['GDK'] = str(self.sgdk_path)
            
            # Adicionar bin ao PATH se não estiver
            bin_path = str(self.sgdk_path / "bin")
            current_path = os.environ.get('PATH', '')
            if bin_path not in current_path:
                os.environ['PATH'] = f"{bin_path}{os.pathsep}{current_path}"
                
            self.logger.debug("✅ Variáveis de ambiente configuradas")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao configurar variáveis de ambiente: {e}")
            
    def _make_executables_executable(self) -> None:
        """Torna executáveis executáveis no Linux"""
        try:
            bin_path = self.sgdk_path / "bin"
            if bin_path.exists():
                for file_path in bin_path.iterdir():
                    if file_path.is_file() and not file_path.suffix:
                        os.chmod(file_path, 0o755)
                        
            self.logger.debug("✅ Permissões de executáveis configuradas")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao configurar permissões: {e}")
            
    def _verify_installation(self) -> bool:
        """Verificação final da instalação"""
        try:
            self.logger.info("🔍 Verificando instalação final...")
            
            # Verificar arquivos essenciais
            essential_files = [
                "bin/rescomp.jar",
                "inc/genesis.h",
                "lib/libmd.a"
            ]
            
            if platform.system().lower() == 'windows':
                essential_files.extend([
                    "bin/m68k-elf-gcc.exe",
                    "bin/m68k-elf-ld.exe"
                ])
            else:
                essential_files.extend([
                    "bin/m68k-elf-gcc",
                    "bin/m68k-elf-ld"
                ])
                
            missing_files = []
            for file_rel_path in essential_files:
                file_path = self.sgdk_path / file_rel_path
                if not file_path.exists():
                    missing_files.append(file_rel_path)
                    
            if missing_files:
                self.logger.error(
                    f"❌ Arquivos essenciais não encontrados:\n"
                    f"  {chr(10).join(missing_files)}"
                )
                self._log_installation_contents()
                return False
                
            # Testar funcionalidade básica
            if not self._test_sgdk_functionality():
                return False
                
            self.logger.info("✅ Instalação verificada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação final: {e}")
            return False
            
    def _test_sgdk_functionality(self) -> bool:
        """Testa funcionalidade básica do SGDK"""
        try:
            # Testar rescomp
            rescomp_path = self.sgdk_path / "bin" / "rescomp.jar"
            result = subprocess.run(
                ["java", "-jar", str(rescomp_path), "-help"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                self.logger.error("❌ rescomp.jar não está funcionando")
                return False
                
            # Testar compilador (se disponível)
            gcc_name = "m68k-elf-gcc.exe" if platform.system().lower() == 'windows' else "m68k-elf-gcc"
            gcc_path = self.sgdk_path / "bin" / gcc_name
            
            if gcc_path.exists():
                result = subprocess.run(
                    [str(gcc_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    self.logger.warning("⚠️ Compilador m68k-elf-gcc não está funcionando")
                    
            self.logger.info("✅ Funcionalidade básica verificada")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao testar funcionalidade: {e}")
            return False
            
    def _log_installation_contents(self) -> None:
        """Registra conteúdo da instalação para diagnóstico"""
        try:
            self.logger.info("📁 Conteúdo da instalação para diagnóstico:")
            
            for root, dirs, files in os.walk(self.sgdk_path):
                level = root.replace(str(self.sgdk_path), '').count(os.sep)
                indent = '  ' * level
                self.logger.info(f"{indent}📁 {os.path.basename(root)}/")
                
                subindent = '  ' * (level + 1)
                for file in files[:10]:  # Limitar a 10 arquivos por diretório
                    self.logger.info(f"{subindent}📄 {file}")
                    
                if len(files) > 10:
                    self.logger.info(f"{subindent}... e mais {len(files) - 10} arquivos")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao listar conteúdo da instalação: {e}")
            
    def uninstall_sgdk(self) -> bool:
        """Remove instalação do SGDK"""
        try:
            if self.sgdk_path.exists():
                self.logger.info(f"🗑️ Removendo SGDK de {self.sgdk_path}")
                import shutil
                shutil.rmtree(self.sgdk_path)
                self.logger.info("✅ SGDK removido com sucesso")
                return True
            else:
                self.logger.info("ℹ️ SGDK não está instalado")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao remover SGDK: {e}")
            return False
            
    def get_installation_info(self) -> Dict[str, any]:
        """Retorna informações sobre a instalação"""
        info = {
            'installed': self._is_sgdk_installed(),
            'path': str(self.sgdk_path),
            'version': SGDK_VERSION,
            'files': {}
        }
        
        if info['installed']:
            # Coletar informações sobre arquivos essenciais
            essential_files = [
                "bin/rescomp.jar",
                "inc/genesis.h",
                "lib/libmd.a"
            ]
            
            for file_rel_path in essential_files:
                file_path = self.sgdk_path / file_rel_path
                info['files'][file_rel_path] = {
                    'exists': file_path.exists(),
                    'size': file_path.stat().st_size if file_path.exists() else 0
                }
                
        return info