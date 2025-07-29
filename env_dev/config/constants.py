#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Constantes e configurações para o Environment Dev
Este arquivo contém valores usados em diferentes partes do sistema
"""

import os
import sys
from pathlib import Path

# Diretórios base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
COMPONENTS_DIR = os.path.join(CONFIG_DIR, "components")
SCRIPTS_DIR = os.path.join(CONFIG_DIR, "scripts")
LOGS_DIR = os.path.join(BASE_DIR, "..", "logs")
GUI_DIR = os.path.join(BASE_DIR, "gui")

# Arquivos importantes
LEGACY_COMPONENTS_FILE = os.path.join(BASE_DIR, "components.yaml")
MAIN_LOG_FILE = os.path.join(LOGS_DIR, "main_execution.log")
ENV_DEV_LOG_FILE = os.path.join(LOGS_DIR, "environment_dev.log")
GUI_LOG_FILE = os.path.join(LOGS_DIR, "gui_initialization.log")

# Categorias de componentes
CATEGORIES = {
    "BUILD_TOOLS": "Build Tools",
    "COMPILERS": "Compilers",
    "EDITORS": "Editors",
    "ENVIRONMENTS": "Environments",
    "LIBRARIES": "Libraries",
    "PACKAGE_MANAGERS": "Package Managers",
    "RUNTIMES": "Runtimes",
    "SDKS": "SDKs",
    "UTILITIES": "Utilities",
    "VIRTUALIZATION": "Virtualization",
    "BOOT_MANAGERS": "Boot Managers",
    "AI_TOOLS": "AI Tools",
    "GAME_DEV": "Game Development",
    "DRIVERS": "Drivers" 
}

# Métodos de instalação
INSTALL_METHODS = [
    "exe", "msi", "archive", "script", "pip", "vcpkg", "git"
]

# Estado da aplicação
APP_VERSION = "1.5.0"
DEBUG_MODE = os.environ.get("ENV_DEV_DEBUG", "0") == "1"
MIGRATION_COMPLETED = os.path.exists(COMPONENTS_DIR)

def get_os_specific_path(path):
    """Converte um caminho genérico para o formato específico do sistema operacional"""
    return os.path.normpath(path)

def ensure_dir_exists(dir_path):
    """Garante que um diretório existe, criando-o se necessário"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return dir_path

def is_admin():
    """Verifica se o script está sendo executado com privilégios administrativos"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        # Se falhar, assumimos que não está rodando como admin
        return False

# Certificar-se de que os diretórios principais existem
for directory in [LOGS_DIR, COMPONENTS_DIR, SCRIPTS_DIR]:
    ensure_dir_exists(directory) 