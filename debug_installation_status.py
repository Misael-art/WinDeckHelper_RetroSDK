#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debugar o status de instalação dos devkits retro
Identifica problemas na detecção de instalações
"""

import os
import sys
import subprocess
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_sgdk_installation():
    """Verifica detalhadamente a instalação do SGDK"""
    logger.info("=== VERIFICAÇÃO DETALHADA DO SGDK ===")
    
    # Caminho esperado do SGDK
    sgdk_path = Path("C:/Users/misae/RetroDevKits/retro_devkits/sgdk")
    logger.info(f"Caminho SGDK: {sgdk_path}")
    logger.info(f"SGDK existe: {sgdk_path.exists()}")
    
    if sgdk_path.exists():
        logger.info("📁 Conteúdo do diretório SGDK:")
        for item in sgdk_path.iterdir():
            logger.info(f"  - {item.name} ({'DIR' if item.is_dir() else 'FILE'})")
    
    # Verificar arquivos específicos
    files_to_check = [
        sgdk_path / "bin" / "rescomp.jar",
        sgdk_path / "inc" / "genesis.h",
        sgdk_path / "bin" / "gcc" / "bin" / "m68k-elf-gcc.exe"
    ]
    
    logger.info("\n📋 Verificação de arquivos essenciais:")
    for file_path in files_to_check:
        exists = file_path.exists()
        logger.info(f"  {'✅' if exists else '❌'} {file_path.relative_to(sgdk_path)}: {exists}")
    
    # Verificar comandos de verificação problemáticos
    logger.info("\n🔍 Testando comandos de verificação:")
    
    # Teste Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        logger.info(f"  ✅ Java: Disponível (código: {result.returncode})")
        if result.stderr:
            logger.info(f"    Versão: {result.stderr.split()[2] if len(result.stderr.split()) > 2 else 'N/A'}")
    except Exception as e:
        logger.error(f"  ❌ Java: Não disponível ({e})")
    
    # Teste Make
    try:
        result = subprocess.run(["make", "--version"], capture_output=True, text=True, timeout=10)
        logger.info(f"  ✅ Make: Disponível (código: {result.returncode})")
    except Exception as e:
        logger.error(f"  ❌ Make: Não disponível ({e})")
    
    # Teste comandos test -f (problemáticos no Windows)
    logger.info("\n⚠️  Testando comandos 'test -f' (problemáticos no Windows):")
    for file_path in files_to_check:
        test_command = f"test -f {file_path}"
        try:
            result = subprocess.run(test_command, shell=True, capture_output=True, text=True, timeout=10)
            logger.info(f"  {'✅' if result.returncode == 0 else '❌'} {test_command}: código {result.returncode}")
        except Exception as e:
            logger.error(f"  ❌ {test_command}: Erro ({e})")

def check_vscode_extensions():
    """Verifica extensões do VSCode instaladas"""
    logger.info("\n=== VERIFICAÇÃO DE EXTENSÕES VSCODE ===")
    
    try:
        # Verificar se VSCode está instalado
        result = subprocess.run(["code", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ VSCode está instalado")
            
            # Listar extensões instaladas
            result = subprocess.run(["code", "--list-extensions"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                extensions = result.stdout.strip().split('\n') if result.stdout.strip() else []
                logger.info(f"📦 Extensões instaladas ({len(extensions)}):")
                
                # Verificar extensões específicas do SGDK
                sgdk_extensions = [
                    "zerasul.genesis-code",
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly",
                    "ms-vscode.hexeditor"
                ]
                
                for ext in sgdk_extensions:
                    installed = ext in extensions
                    logger.info(f"  {'✅' if installed else '❌'} {ext}: {'Instalada' if installed else 'Não instalada'}")
                
                if extensions:
                    logger.info("\n📋 Todas as extensões:")
                    for ext in sorted(extensions):
                        logger.info(f"  - {ext}")
            else:
                logger.error("❌ Erro ao listar extensões")
        else:
            logger.error("❌ VSCode não está instalado ou não está no PATH")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar VSCode: {e}")

def check_emulators():
    """Verifica emuladores instalados"""
    logger.info("\n=== VERIFICAÇÃO DE EMULADORES ===")
    
    emulators = ["blastem", "gens", "fusion", "retroarch"]
    
    for emulator in emulators:
        try:
            result = subprocess.run([emulator, "--version"], capture_output=True, text=True, timeout=10)
            logger.info(f"  {'✅' if result.returncode == 0 else '❌'} {emulator}: {'Disponível' if result.returncode == 0 else 'Não disponível'}")
        except Exception:
            # Tentar encontrar executável
            import shutil
            exe_path = shutil.which(emulator) or shutil.which(f"{emulator}.exe")
            if exe_path:
                logger.info(f"  ⚠️  {emulator}: Encontrado em {exe_path} (mas não responde a --version)")
            else:
                logger.info(f"  ❌ {emulator}: Não encontrado")

def test_current_detection_system():
    """Testa o sistema atual de detecção"""
    logger.info("\n=== TESTANDO SISTEMA ATUAL DE DETECÇÃO ===")
    
    try:
        # Importar e testar o sistema atual
        sys.path.append(str(Path.cwd()))
        from core.retro_devkit_manager import RetroDevKitManager
        
        manager = RetroDevKitManager()
        status = manager.get_installation_status()
        
        logger.info("📊 Status reportado pelo sistema:")
        for devkit_id, is_installed in status.items():
            logger.info(f"  {'✅' if is_installed else '❌'} {devkit_id}: {'Instalado' if is_installed else 'Não instalado'}")
        
        # Verificar especificamente o SGDK
        if 'megadrive' in status:
            logger.info(f"\n🎯 SGDK (megadrive) reportado como: {'INSTALADO' if status['megadrive'] else 'NÃO INSTALADO'}")
            
            # Verificar comandos específicos do SGDK
            sgdk_devkit = manager.devkits['megadrive']
            logger.info("\n🔍 Comandos de verificação do SGDK:")
            for i, cmd in enumerate(sgdk_devkit.verification_commands, 1):
                logger.info(f"  {i}. {cmd}")
                
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    logger.info(f"     {'✅' if result.returncode == 0 else '❌'} Código: {result.returncode}")
                    if result.stderr:
                        logger.info(f"     Erro: {result.stderr.strip()[:100]}")
                except Exception as e:
                    logger.error(f"     ❌ Exceção: {e}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar sistema atual: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal"""
    logger.info("🔍 DIAGNÓSTICO COMPLETO DO SISTEMA DE DETECÇÃO DE DEVKITS")
    logger.info("=" * 60)
    
    check_sgdk_installation()
    check_vscode_extensions()
    check_emulators()
    test_current_detection_system()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Diagnóstico concluído!")
    
    # Sugestões de correção
    logger.info("\n💡 SUGESTÕES DE CORREÇÃO:")
    logger.info("1. Substituir comandos 'test -f' por verificação Python nativa")
    logger.info("2. Verificar dependências globais (Java, Make) de forma mais robusta")
    logger.info("3. Implementar verificação específica para Windows")
    logger.info("4. Adicionar verificação de extensões VSCode")
    logger.info("5. Melhorar detecção de emuladores")

if __name__ == "__main__":
    main()