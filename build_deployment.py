#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script Otimizado para Environment Dev Deep Evaluation
Script de build que usa PyInstaller com configurações otimizadas.
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedBuilder:
    """Builder otimizado para o projeto"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.deployment_dir = self.project_root / "deployment"
        self.spec_file = self.project_root / "environment_dev.spec"
        
    def clean_previous_builds(self):
        """Limpa builds anteriores"""
        logger.info("🧹 Limpando builds anteriores...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.deployment_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"  ✓ Removido: {dir_path}")
        
        # Remover arquivos temporários do PyInstaller
        temp_files = list(self.project_root.glob("*.spec"))
        for temp_file in temp_files:
            if temp_file.name != "environment_dev.spec":
                temp_file.unlink()
                logger.info(f"  ✓ Removido: {temp_file}")
    
    def install_build_dependencies(self):
        """Instala dependências necessárias para o build"""
        logger.info("📦 Instalando dependências de build...")
        
        build_deps = [
            "pyinstaller>=5.0",
            "pillow",
            "pyyaml",
            "requests",
            "psutil",
            "py7zr",
        ]
        
        for dep in build_deps:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "--upgrade", dep
                ], check=True, capture_output=True)
                logger.info(f"  ✓ Instalado: {dep}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"  ⚠ Erro ao instalar {dep}: {e}")
    
    def verify_project_structure(self):
        """Verifica se a estrutura do projeto está correta"""
        logger.info("🔍 Verificando estrutura do projeto...")
        
        required_files = [
            "main.py",
            "core/__init__.py",
            "gui/__init__.py",
            "config/components",
            "docs/README.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                logger.info(f"  ✓ Encontrado: {file_path}")
        
        if missing_files:
            logger.error(f"  ❌ Arquivos ausentes: {missing_files}")
            return False
        
        logger.info("  ✅ Estrutura do projeto verificada")
        return True
    
    def create_optimized_spec(self):
        """Cria arquivo spec otimizado se não existir"""
        if not self.spec_file.exists():
            logger.info("📝 Criando arquivo spec otimizado...")
            # O arquivo já foi criado anteriormente
            logger.info("  ✓ Arquivo spec já existe")
        else:
            logger.info("  ✓ Usando arquivo spec existente")
    
    def build_executable(self):
        """Constrói o executável usando PyInstaller"""
        logger.info("🔨 Construindo executável...")
        
        # Comando PyInstaller otimizado
        cmd = [
            "pyinstaller",
            "--clean",  # Limpar cache
            "--noconfirm",  # Não pedir confirmação
            str(self.spec_file)
        ]
        
        try:
            # Executar build
            logger.info(f"  Executando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            
            logger.info("  ✅ Build concluído com sucesso")
            
            # Verificar se o executável foi criado
            exe_path = self.dist_dir / "EnvironmentDevDeepEvaluation"
            if exe_path.exists():
                logger.info(f"  ✓ Executável criado: {exe_path}")
                return True
            else:
                logger.error("  ❌ Executável não encontrado após build")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"  ❌ Erro no build: {e}")
            logger.error(f"  Stdout: {e.stdout}")
            logger.error(f"  Stderr: {e.stderr}")
            return False
    
    def optimize_executable(self):
        """Otimiza o executável criado"""
        logger.info("⚡ Otimizando executável...")
        
        exe_dir = self.dist_dir / "EnvironmentDevDeepEvaluation"
        if not exe_dir.exists():
            logger.error("  ❌ Diretório do executável não encontrado")
            return False
        
        # Remover arquivos desnecessários
        unnecessary_files = [
            "*.pyc",
            "__pycache__",
            "*.pyo",
            "*.log",
            "test_*",
            "debug_*"
        ]
        
        removed_count = 0
        for pattern in unnecessary_files:
            for file_path in exe_dir.rglob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)
                    removed_count += 1
        
        logger.info(f"  ✓ Removidos {removed_count} arquivos desnecessários")
        
        # Calcular tamanho final
        total_size = sum(f.stat().st_size for f in exe_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        logger.info(f"  ✓ Tamanho final: {size_mb:.1f} MB")
        
        return True
    
    def create_portable_package(self):
        """Cria pacote portável completo"""
        logger.info("📦 Criando pacote portável...")
        
        # Criar diretório de deployment
        self.deployment_dir.mkdir(exist_ok=True)
        package_dir = self.deployment_dir / "EnvironmentDevDeepEvaluation_Portable"
        
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        
        # Copiar executável
        exe_source = self.dist_dir / "EnvironmentDevDeepEvaluation"
        exe_dest = package_dir / "EnvironmentDevDeepEvaluation"
        shutil.copytree(exe_source, exe_dest)
        logger.info("  ✓ Executável copiado")
        
        # Copiar arquivos essenciais
        essential_files = [
            ("README.md", "README.md"),
            ("requirements.txt", "requirements.txt"),
            ("FINAL_FIXES_SUMMARY.md", "docs/FINAL_FIXES_SUMMARY.md"),
            ("SGDK_FIXES_SUMMARY.md", "docs/SGDK_FIXES_SUMMARY.md"),
        ]
        
        for source_file, dest_file in essential_files:
            source_path = self.project_root / source_file
            dest_path = package_dir / dest_file
            if source_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                logger.info(f"  ✓ Copiado: {source_file}")
        
        # Copiar diretórios essenciais
        essential_dirs = [
            ("config", "config"),
            ("docs", "docs"),
            ("data", "data"),
        ]
        
        for source_dir, dest_dir in essential_dirs:
            source_path = self.project_root / source_dir
            dest_path = package_dir / dest_dir
            if source_path.exists():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                logger.info(f"  ✓ Copiado: {source_dir}/")
        
        # Criar scripts de inicialização
        self._create_launch_scripts(package_dir)
        
        # Criar arquivo de informações
        self._create_package_info(package_dir)
        
        logger.info(f"  ✅ Pacote portável criado: {package_dir}")
        return package_dir
    
    def _create_launch_scripts(self, package_dir):
        """Cria scripts de inicialização"""
        # Script Windows
        bat_script = package_dir / "Iniciar_Environment_Dev.bat"
        bat_script.write_text("""@echo off
title Environment Dev Deep Evaluation v2.0
echo.
echo ==========================================
echo  Environment Dev Deep Evaluation v2.0
echo  Sistema de Detecao e Instalacao
echo ==========================================
echo.
echo Iniciando aplicacao...
cd /d "%~dp0"
.\\EnvironmentDevDeepEvaluation\\EnvironmentDevDeepEvaluation.exe
if errorlevel 1 (
    echo.
    echo Erro ao executar a aplicacao!
    echo Verifique se todas as dependencias estao instaladas.
    pause
)
""", encoding='utf-8')
        
        # Script Linux/Mac
        sh_script = package_dir / "iniciar_environment_dev.sh"
        sh_script.write_text("""#!/bin/bash
echo "=========================================="
echo " Environment Dev Deep Evaluation v2.0"
echo " Sistema de Detecao e Instalacao"
echo "=========================================="
echo
echo "Iniciando aplicacao..."
cd "$(dirname "$0")"
./EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation
""", encoding='utf-8')
        
        try:
            sh_script.chmod(0o755)
        except:
            pass
    
    def _create_package_info(self, package_dir):
        """Cria arquivo de informações do pacote"""
        info_content = f"""
==========================================
Environment Dev Deep Evaluation v2.0
==========================================

DESCRIÇÃO:
Sistema completo de detecção e instalação de ambientes de desenvolvimento
com suporte a múltiplas plataformas e Steam Deck.

BUILD INFO:
- Versão: 2.0.0
- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- Plataforma: {sys.platform}
- Python: {sys.version.split()[0]}

COMO USAR:
1. Windows: Execute "Iniciar_Environment_Dev.bat"
2. Linux/Mac: Execute "./iniciar_environment_dev.sh"
3. Ou execute diretamente: EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation.exe

ESTRUTURA:
- EnvironmentDevDeepEvaluation/  # Executável principal
- config/                        # Configurações
- docs/                         # Documentação
- data/                         # Dados iniciais
- Iniciar_Environment_Dev.bat   # Launcher Windows
- iniciar_environment_dev.sh    # Launcher Linux/Mac

FUNCIONALIDADES:
✅ Detecção automática de componentes
✅ Sistema de instalação robusto
✅ Interface gráfica moderna
✅ Suporte ao Steam Deck
✅ Sistema de plugins
✅ SGDK 2.11 com instalação real
✅ Sincronização automática de status

REQUISITOS:
- Windows 10/11, Linux ou macOS
- 2GB RAM mínimo
- 1GB espaço em disco

==========================================
Environment Dev Team - {datetime.now().year}
==========================================
"""
        
        info_file = package_dir / "LEIA-ME.txt"
        info_file.write_text(info_content, encoding='utf-8')
    
    def generate_build_report(self):
        """Gera relatório do build"""
        logger.info("📊 Gerando relatório de build...")
        
        report = {
            "build_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "platform": sys.platform,
                "python_version": sys.version,
                "pyinstaller_version": self._get_pyinstaller_version()
            },
            "build_status": "success",
            "output_location": str(self.deployment_dir),
            "executable_size": self._get_executable_size(),
            "components_included": [
                "Core detection engine",
                "GUI interface",
                "Configuration files",
                "Documentation",
                "SGDK real installer",
                "Component status manager",
                "Steam Deck support"
            ]
        }
        
        report_file = self.deployment_dir / f"build_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Relatório salvo: {report_file}")
        return report
    
    def _get_pyinstaller_version(self):
        """Obtém versão do PyInstaller"""
        try:
            result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _get_executable_size(self):
        """Calcula tamanho do executável"""
        exe_dir = self.dist_dir / "EnvironmentDevDeepEvaluation"
        if exe_dir.exists():
            total_size = sum(f.stat().st_size for f in exe_dir.rglob('*') if f.is_file())
            return f"{total_size / (1024 * 1024):.1f} MB"
        return "unknown"

def main():
    """Função principal do build"""
    print("🚀 Environment Dev Deep Evaluation - Build Otimizado")
    print("=" * 60)
    
    builder = OptimizedBuilder()
    
    try:
        # 1. Limpar builds anteriores
        builder.clean_previous_builds()
        
        # 2. Instalar dependências
        builder.install_build_dependencies()
        
        # 3. Verificar estrutura
        if not builder.verify_project_structure():
            logger.error("❌ Estrutura do projeto inválida")
            return False
        
        # 4. Criar spec otimizado
        builder.create_optimized_spec()
        
        # 5. Construir executável
        if not builder.build_executable():
            logger.error("❌ Falha na construção do executável")
            return False
        
        # 6. Otimizar executável
        if not builder.optimize_executable():
            logger.error("❌ Falha na otimização")
            return False
        
        # 7. Criar pacote portável
        package_dir = builder.create_portable_package()
        
        # 8. Gerar relatório
        report = builder.generate_build_report()
        
        print("\n✅ BUILD CONCLUÍDO COM SUCESSO!")
        print("=" * 40)
        print(f"📦 Pacote: Environment Dev Deep Evaluation v2.0")
        print(f"📁 Localização: {package_dir}")
        print(f"💾 Tamanho: {report['executable_size']}")
        print("\n🎯 Próximos passos:")
        print("1. Teste o executável no pacote criado")
        print("2. Distribua o diretório completo")
        print("3. Use os scripts de inicialização fornecidos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no build: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)