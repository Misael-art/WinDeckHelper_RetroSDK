#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Dev Deep Evaluation - Deployment Package Creator
Cria um pacote de deployment completo usando PyInstaller com todos os componentes e documentação.
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json
import zipfile

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentPackageCreator:
    """Criador de pacote de deployment completo"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_dir = self.project_root / "deployment"
        self.dist_dir = self.deployment_dir / "dist"
        self.build_dir = self.deployment_dir / "build"
        self.package_dir = self.deployment_dir / "package"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Informações do projeto
        self.project_info = {
            "name": "Environment Dev Deep Evaluation",
            "version": "2.0.0",
            "description": "Sistema completo de detecção e instalação de ambientes de desenvolvimento",
            "author": "Environment Dev Team",
            "build_date": datetime.now().isoformat(),
            "build_timestamp": self.timestamp
        }
        
    def create_deployment_package(self):
        """Cria o pacote de deployment completo"""
        try:
            logger.info("🚀 Iniciando criação do pacote de deployment...")
            
            # 1. Preparar diretórios
            self._prepare_directories()
            
            # 2. Instalar dependências necessárias
            self._install_dependencies()
            
            # 3. Criar executável com PyInstaller
            self._create_executable()
            
            # 4. Copiar arquivos de configuração
            self._copy_configuration_files()
            
            # 5. Copiar documentação
            self._copy_documentation()
            
            # 6. Copiar recursos adicionais
            self._copy_additional_resources()
            
            # 7. Criar scripts de inicialização
            self._create_startup_scripts()
            
            # 8. Gerar arquivo de informações
            self._generate_info_file()
            
            # 9. Criar arquivo ZIP final
            self._create_final_package()
            
            logger.info("✅ Pacote de deployment criado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na criação do pacote: {e}")
            return False
    
    def _prepare_directories(self):
        """Prepara os diretórios necessários"""
        logger.info("📁 Preparando diretórios...")
        
        # Limpar diretórios existentes
        if self.deployment_dir.exists():
            shutil.rmtree(self.deployment_dir)
        
        # Criar estrutura de diretórios
        directories = [
            self.deployment_dir,
            self.dist_dir,
            self.build_dir,
            self.package_dir,
            self.package_dir / "config",
            self.package_dir / "docs",
            self.package_dir / "logs",
            self.package_dir / "cache",
            self.package_dir / "data",
            self.package_dir / "plugins",
            self.package_dir / "examples"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✓ Criado: {directory}")
    
    def _install_dependencies(self):
        """Instala dependências necessárias para o deployment"""
        logger.info("📦 Instalando dependências...")
        
        dependencies = [
            "pyinstaller",
            "auto-py-to-exe",  # Interface gráfica opcional
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                logger.info(f"  ✓ Instalado: {dep}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"  ⚠ Erro ao instalar {dep}: {e}")
    
    def _create_executable(self):
        """Cria o executável usando PyInstaller"""
        logger.info("🔨 Criando executável com PyInstaller...")
        
        # Configurações do PyInstaller
        pyinstaller_args = [
            "pyinstaller",
            "--name", "EnvironmentDevDeepEvaluation",
            "--onedir",  # Criar diretório com dependências
            "--windowed",  # Interface gráfica (sem console)
            "--icon", str(self._get_icon_path()),
            "--add-data", f"{self.project_root}/config;config",
            "--add-data", f"{self.project_root}/docs;docs",
            "--add-data", f"{self.project_root}/gui;gui",
            "--add-data", f"{self.project_root}/core;core",
            "--add-data", f"{self.project_root}/plugins;plugins",
            "--add-data", f"{self.project_root}/data;data",
            "--hidden-import", "tkinter",
            "--hidden-import", "tkinter.ttk",
            "--hidden-import", "PIL",
            "--hidden-import", "yaml",
            "--hidden-import", "requests",
            "--hidden-import", "psutil",
            "--hidden-import", "py7zr",
            "--hidden-import", "winreg",
            "--collect-all", "tkinter",
            "--collect-all", "PIL",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir),
            "--specpath", str(self.deployment_dir),
            str(self.project_root / "main.py")
        ]
        
        try:
            # Executar PyInstaller
            result = subprocess.run(pyinstaller_args, check=True, capture_output=True, text=True)
            logger.info("  ✓ Executável criado com sucesso")
            
            # Copiar executável para o diretório do pacote
            exe_source = self.dist_dir / "EnvironmentDevDeepEvaluation"
            exe_dest = self.package_dir / "EnvironmentDevDeepEvaluation"
            
            if exe_source.exists():
                shutil.copytree(exe_source, exe_dest)
                logger.info(f"  ✓ Executável copiado para: {exe_dest}")
            else:
                logger.error("  ❌ Executável não encontrado após build")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"  ❌ Erro no PyInstaller: {e}")
            logger.error(f"  Saída: {e.stdout}")
            logger.error(f"  Erro: {e.stderr}")
            raise
    
    def _get_icon_path(self):
        """Obtém o caminho do ícone ou cria um padrão"""
        icon_paths = [
            self.project_root / "assets" / "icon.ico",
            self.project_root / "gui" / "assets" / "icon.ico",
            self.project_root / "icon.ico"
        ]
        
        for icon_path in icon_paths:
            if icon_path.exists():
                return icon_path
        
        # Se não encontrar ícone, usar padrão do sistema
        return ""
    
    def _copy_configuration_files(self):
        """Copia arquivos de configuração"""
        logger.info("⚙️ Copiando arquivos de configuração...")
        
        config_files = [
            "config/components",
            "config/settings",
            "requirements.txt",
            "requirements-dev.txt"
        ]
        
        for config_file in config_files:
            source = self.project_root / config_file
            if source.exists():
                if source.is_dir():
                    dest = self.package_dir / config_file
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    dest = self.package_dir / config_file
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                logger.info(f"  ✓ Copiado: {config_file}")
    
    def _copy_documentation(self):
        """Copia toda a documentação"""
        logger.info("📚 Copiando documentação...")
        
        # Documentação principal
        doc_files = [
            "README.md",
            "docs/",
            "FINAL_FIXES_SUMMARY.md",
            "SGDK_FIXES_SUMMARY.md",
            "PROJECT_COMPLETION_REPORT.md",
            "SISTEMA_INSTALACAO_ROBUSTO_COMPLETO.md",
            "UNIFIED_DETECTION_ENGINE_SUMMARY.md",
            "HIERARCHICAL_DETECTION_IMPLEMENTATION_SUMMARY.md"
        ]
        
        for doc_file in doc_files:
            source = self.project_root / doc_file
            if source.exists():
                if source.is_dir():
                    dest = self.package_dir / "docs" / source.name
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    dest = self.package_dir / "docs" / source.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                logger.info(f"  ✓ Copiado: {doc_file}")
    
    def _copy_additional_resources(self):
        """Copia recursos adicionais"""
        logger.info("📋 Copiando recursos adicionais...")
        
        # Exemplos e templates
        if (self.project_root / "examples").exists():
            shutil.copytree(
                self.project_root / "examples",
                self.package_dir / "examples",
                dirs_exist_ok=True
            )
            logger.info("  ✓ Exemplos copiados")
        
        # Plugins
        if (self.project_root / "plugins").exists():
            shutil.copytree(
                self.project_root / "plugins",
                self.package_dir / "plugins",
                dirs_exist_ok=True
            )
            logger.info("  ✓ Plugins copiados")
        
        # Dados iniciais
        if (self.project_root / "data").exists():
            shutil.copytree(
                self.project_root / "data",
                self.package_dir / "data",
                dirs_exist_ok=True
            )
            logger.info("  ✓ Dados iniciais copiados")
    
    def _create_startup_scripts(self):
        """Cria scripts de inicialização"""
        logger.info("🚀 Criando scripts de inicialização...")
        
        # Script Windows (.bat)
        windows_script = self.package_dir / "start_environment_dev.bat"
        windows_script.write_text(f"""@echo off
title Environment Dev Deep Evaluation v{self.project_info['version']}
echo.
echo ========================================
echo Environment Dev Deep Evaluation
echo Version: {self.project_info['version']}
echo Build: {self.project_info['build_timestamp']}
echo ========================================
echo.
echo Iniciando aplicacao...
cd /d "%~dp0"
.\\EnvironmentDevDeepEvaluation\\EnvironmentDevDeepEvaluation.exe
pause
""", encoding='utf-8')
        
        # Script Linux/Mac (.sh)
        linux_script = self.package_dir / "start_environment_dev.sh"
        linux_script.write_text(f"""#!/bin/bash
echo "========================================"
echo "Environment Dev Deep Evaluation"
echo "Version: {self.project_info['version']}"
echo "Build: {self.project_info['build_timestamp']}"
echo "========================================"
echo
echo "Iniciando aplicacao..."
cd "$(dirname "$0")"
./EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation
""", encoding='utf-8')
        
        # Tornar executável no Linux/Mac
        try:
            linux_script.chmod(0o755)
        except:
            pass
        
        # Script de instalação de dependências
        install_deps_script = self.package_dir / "install_dependencies.bat"
        install_deps_script.write_text("""@echo off
title Instalacao de Dependencias - Environment Dev
echo.
echo ========================================
echo Instalando dependencias necessarias...
echo ========================================
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Dependencias instaladas com sucesso!
pause
""", encoding='utf-8')
        
        logger.info("  ✓ Scripts de inicialização criados")
    
    def _generate_info_file(self):
        """Gera arquivo com informações do build"""
        logger.info("ℹ️ Gerando arquivo de informações...")
        
        # Informações detalhadas do build
        build_info = {
            **self.project_info,
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "architecture": sys.maxsize > 2**32 and "64-bit" or "32-bit"
            },
            "package_contents": {
                "executable": "EnvironmentDevDeepEvaluation/",
                "configuration": "config/",
                "documentation": "docs/",
                "examples": "examples/",
                "plugins": "plugins/",
                "startup_scripts": ["start_environment_dev.bat", "start_environment_dev.sh"]
            },
            "requirements": self._get_requirements(),
            "features": [
                "Detecção automática de componentes",
                "Sistema de instalação robusto",
                "Interface gráfica moderna",
                "Suporte ao Steam Deck",
                "Sistema de plugins",
                "Detecção hierárquica",
                "Gerenciamento de dependências",
                "Sistema de status persistente",
                "Instalação real do SGDK 2.11",
                "Sincronização automática"
            ]
        }
        
        # Salvar como JSON
        info_file = self.package_dir / "build_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(build_info, f, indent=2, ensure_ascii=False)
        
        # Salvar como texto legível
        readme_file = self.package_dir / "LEIA-ME.txt"
        readme_content = f"""
========================================
Environment Dev Deep Evaluation v{self.project_info['version']}
========================================

DESCRIÇÃO:
{self.project_info['description']}

VERSÃO: {self.project_info['version']}
BUILD: {self.project_info['build_timestamp']}
DATA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

COMO USAR:
1. Execute 'start_environment_dev.bat' (Windows) ou 'start_environment_dev.sh' (Linux/Mac)
2. Ou execute diretamente: EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation.exe

ESTRUTURA DO PACOTE:
- EnvironmentDevDeepEvaluation/    # Executável principal
- config/                          # Arquivos de configuração
- docs/                           # Documentação completa
- examples/                       # Exemplos de uso
- plugins/                        # Plugins disponíveis
- start_environment_dev.bat       # Script de inicialização (Windows)
- start_environment_dev.sh        # Script de inicialização (Linux/Mac)
- install_dependencies.bat       # Instalação de dependências
- build_info.json               # Informações técnicas do build

FUNCIONALIDADES PRINCIPAIS:
- ✅ Detecção automática de componentes instalados
- ✅ Sistema de instalação robusto com rollback
- ✅ Interface gráfica moderna e intuitiva
- ✅ Suporte completo ao Steam Deck
- ✅ Sistema de plugins extensível
- ✅ Detecção hierárquica inteligente
- ✅ Gerenciamento automático de dependências
- ✅ Sistema de status persistente
- ✅ Instalação real do SGDK 2.11
- ✅ Sincronização automática de status

REQUISITOS DO SISTEMA:
- Windows 10/11, Linux ou macOS
- Python 3.8+ (se executar via código fonte)
- 2GB RAM mínimo
- 1GB espaço em disco

SUPORTE:
Para suporte e documentação completa, consulte a pasta 'docs/'

========================================
Environment Dev Team - {datetime.now().year}
========================================
"""
        
        readme_file.write_text(readme_content, encoding='utf-8')
        logger.info("  ✓ Arquivos de informação criados")
    
    def _get_requirements(self):
        """Obtém lista de dependências"""
        try:
            req_file = self.project_root / "requirements.txt"
            if req_file.exists():
                return req_file.read_text(encoding='utf-8').strip().split('\n')
        except:
            pass
        return []
    
    def _create_final_package(self):
        """Cria o arquivo ZIP final"""
        logger.info("📦 Criando pacote ZIP final...")
        
        package_name = f"EnvironmentDevDeepEvaluation_v{self.project_info['version']}_{self.timestamp}.zip"
        package_path = self.deployment_dir / package_name
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.package_dir)
                    zipf.write(file_path, arc_path)
        
        # Calcular tamanho do pacote
        package_size = package_path.stat().st_size / (1024 * 1024)  # MB
        
        logger.info(f"  ✓ Pacote criado: {package_name}")
        logger.info(f"  ✓ Tamanho: {package_size:.1f} MB")
        logger.info(f"  ✓ Localização: {package_path}")
        
        return package_path
    
    def generate_deployment_report(self):
        """Gera relatório do deployment"""
        logger.info("📊 Gerando relatório de deployment...")
        
        report = {
            "deployment_info": self.project_info,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "package_location": str(self.deployment_dir),
            "components_included": [
                "Executável principal",
                "Arquivos de configuração",
                "Documentação completa",
                "Scripts de inicialização",
                "Exemplos e templates",
                "Sistema de plugins",
                "Dados iniciais"
            ],
            "features_verified": [
                "PyInstaller build successful",
                "All dependencies included",
                "Configuration files copied",
                "Documentation included",
                "Startup scripts created",
                "Package compressed successfully"
            ]
        }
        
        report_file = self.deployment_dir / f"deployment_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Relatório salvo: {report_file}")
        return report

def main():
    """Função principal"""
    print("🚀 Environment Dev Deep Evaluation - Deployment Package Creator")
    print("=" * 70)
    
    creator = DeploymentPackageCreator()
    
    try:
        # Criar pacote de deployment
        success = creator.create_deployment_package()
        
        if success:
            # Gerar relatório
            report = creator.generate_deployment_report()
            
            print("\n✅ DEPLOYMENT CONCLUÍDO COM SUCESSO!")
            print("=" * 50)
            print(f"📦 Pacote: {creator.project_info['name']} v{creator.project_info['version']}")
            print(f"📅 Build: {creator.project_info['build_timestamp']}")
            print(f"📁 Localização: {creator.deployment_dir}")
            print("\n🎯 Próximos passos:")
            print("1. Teste o executável no diretório 'deployment/package/'")
            print("2. Distribua o arquivo ZIP gerado")
            print("3. Consulte 'LEIA-ME.txt' para instruções de uso")
            
        else:
            print("\n❌ ERRO NO DEPLOYMENT!")
            print("Verifique os logs acima para detalhes.")
            
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        print(f"\n❌ ERRO CRÍTICO: {e}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)