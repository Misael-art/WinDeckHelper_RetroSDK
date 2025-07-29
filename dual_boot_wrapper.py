#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wrapper para iniciar o assistente de Dual Boot.
Este script facilita a integração do assistente de dual boot no sistema, incluindo
suporte para Linux e Glover Windows em configuração multi-boot.

Modo de uso:
    python dual_boot_wrapper.py            # Modo automático (padrão)
    python dual_boot_wrapper.py --manual   # Modo manual com menu de opções
"""

import os
import sys
import subprocess
import ctypes
import logging
import argparse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "dual_boot_helper.log"))
    ]
)

logger = logging.getLogger(__name__)

def is_admin():
    """Verifica se o script está sendo executado como administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"Erro ao verificar privilégios de administrador: {e}")
        return False

def check_dependencies():
    """Verifica se as dependências necessárias estão instaladas."""
    # Verifica se o Grub2Win está instalado
    grub2win_path = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Grub2Win", "grub2win.exe")
    grub2win_installed = os.path.exists(grub2win_path)
    
    # Verifica se o utilitário de dual boot está instalado
    dual_boot_manager_path = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), 
                                         "DualBootPartitionManager", "install_linux.bat")
    dual_boot_manager_installed = os.path.exists(dual_boot_manager_path)
    
    # Verifica se o Glover Windows está instalado
    glover_windows_path = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), 
                                      "GloverWindows", "install_glover.bat")
    glover_windows_installed = os.path.exists(glover_windows_path)
    
    return grub2win_installed, dual_boot_manager_installed, glover_windows_installed, grub2win_path, dual_boot_manager_path, glover_windows_path

def install_dependencies():
    """Instala as dependências necessárias se estiverem faltando."""
    # Verificar se environment_dev.py existe
    if not os.path.exists("environment_dev.py"):
        logger.error("Arquivo environment_dev.py não encontrado. Certifique-se de estar no diretório correto.")
        return False
    
    logger.info("Instalando dependências necessárias para o assistente de dual boot...")
    
    try:
        # Usa o sistema environment_dev.py para instalar as dependências
        subprocess.check_call([sys.executable, "environment_dev.py", "--install", "Grub2Win", "DualBootPartitionManager", "GloverWindows"])
        logger.info("Dependências instaladas com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar dependências: {e}")
        return False

def run_dual_boot_assistant(auto_mode=False):
    """Executa o assistente de dual boot.
    
    Args:
        auto_mode (bool): Se True, executa o assistente em modo automático
    """
    # Verificar se o script do assistente existe
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assistant_path = os.path.join(base_dir, "env_dev", "utils", "dual_boot_helper.py")
    
    if not os.path.exists(assistant_path):
        logger.error(f"Script do assistente de dual boot não encontrado em {assistant_path}")
        return False
    
    logger.info(f"Iniciando o assistente de dual boot em modo {'automático' if auto_mode else 'manual'}...")
    
    try:
        # Prepara os argumentos
        args = [sys.executable, assistant_path]
        if auto_mode:
            args.append('--auto')
            
        if is_admin():
            # Executa com privilégios atuais (admin)
            subprocess.Popen(args)
        else:
            # Tenta executar com privilégios elevados
            logger.info("Tentando executar o assistente com privilégios de administrador...")
            if sys.platform.startswith('win'):
                # Prepara um string com os argumentos
                cmd_args = f'"{assistant_path}"'
                if auto_mode:
                    cmd_args += ' --auto'
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd_args, None, 1)
            else:
                # Fallback para sistemas que não são Windows
                subprocess.Popen(args)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar o assistente de dual boot: {e}")
        return False

def main():
    """Função principal."""
    # Analisa argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Assistente de Dual Boot Windows/Linux")
    parser.add_argument('--manual', action='store_true', help='Iniciar em modo manual com menu de opções')
    args = parser.parse_args()
    
    # Se não for modo manual, inicia automaticamente o assistente
    if not args.manual:
        logger.info("=== Iniciando Assistente de Dual Boot em modo automático ===")
        return 0 if run_dual_boot_assistant(auto_mode=True) else 1
    
    # Se for modo manual, exibe o menu tradicional
    logger.info("=== Iniciando Wrapper do Assistente de Multi-Boot (Linux/Glover) ===")
    
    # Verifica as dependências
    grub2win_installed, dual_boot_manager_installed, glover_windows_installed, grub2win_path, dual_boot_manager_path, glover_windows_path = check_dependencies()
    
    # Se alguma dependência estiver faltando, tenta instalar
    if not (grub2win_installed and dual_boot_manager_installed and glover_windows_installed):
        logger.warning("Algumas dependências necessárias não estão instaladas.")
        
        # Pergunta se deve instalar
        install = input("Deseja instalar as dependências necessárias? (S/N): ")
        if install.lower() == 's':
            success = install_dependencies()
            if not success:
                logger.error("Não foi possível instalar as dependências. Encerrando.")
                return 1
            
            # Verifica novamente após instalação
            grub2win_installed, dual_boot_manager_installed, glover_windows_installed, grub2win_path, dual_boot_manager_path, glover_windows_path = check_dependencies()
    
    # Exibe estado atual das dependências
    logger.info(f"Grub2Win instalado: {'Sim' if grub2win_installed else 'Não'}")
    logger.info(f"Assistente de Dual Boot instalado: {'Sim' if dual_boot_manager_installed else 'Não'}")
    logger.info(f"Glover Windows instalado: {'Sim' if glover_windows_installed else 'Não'}")
    
    # Oferece opções ao usuário
    print("\nO que você deseja fazer?")
    print("1. Executar o Assistente de Dual Boot (Manual)")
    print("2. Executar o Assistente de Dual Boot (Automático)")
    if grub2win_installed:
        print("3. Abrir o Grub2Win (configuração de gerenciador de boot)")
    if dual_boot_manager_installed:
        print("4. Abrir o Assistente de Particionamento")
    if glover_windows_installed:
        print("5. Abrir o Glover Windows")
    print("6. Sair")
    
    choice = input("\nEscolha uma opção: ")
    
    if choice == "1":
        run_dual_boot_assistant(auto_mode=False)
    elif choice == "2":
        run_dual_boot_assistant(auto_mode=True)
    elif choice == "3" and grub2win_installed:
        logger.info("Abrindo Grub2Win...")
        try:
            subprocess.Popen([grub2win_path])
        except Exception as e:
            logger.error(f"Erro ao abrir Grub2Win: {e}")
    elif choice == "4" and dual_boot_manager_installed:
        logger.info("Abrindo Assistente de Particionamento...")
        try:
            subprocess.Popen([dual_boot_manager_path], shell=True)
        except Exception as e:
            logger.error(f"Erro ao abrir Assistente de Particionamento: {e}")
    elif choice == "5" and glover_windows_installed:
        logger.info("Abrindo Glover Windows...")
        try:
            subprocess.Popen([glover_windows_path], shell=True)
        except Exception as e:
            logger.error(f"Erro ao abrir Glover Windows: {e}")
    elif choice == "6":
        logger.info("Encerrando o wrapper.")
    else:
        logger.warning("Opção inválida ou não disponível.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 