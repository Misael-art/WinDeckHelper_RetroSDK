"""Constantes centralizadas para RetroDevKits
Este arquivo centraliza versões e configurações dos devkits para evitar inconsistências"""

# Versões dos DevKits
SGDK_VERSION = "2.11"
GBDK_VERSION = "4.2.0"
CC65_VERSION = "2.19"
DEVKITPRO_VERSION = "r58"

# URLs base para downloads
SGDK_BASE_URL = "https://github.com/Stephane-D/SGDK/releases/download"
GBDK_BASE_URL = "https://github.com/gbdk-2020/gbdk-2020/releases/download"
CC65_BASE_URL = "https://github.com/cc65/cc65/releases/download"
DEVKITPRO_BASE_URL = "https://github.com/devkitPro/installer/releases/download"

# Checksums SHA-256 (atualize conforme necessário)
SGDK_CHECKSUMS = {
    "2.11": {
        "windows": "5cc704b7e3a15183c33e721a1d7f84c067cf78808754556d03bb14764df51437",
        "linux": "b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567a"
    }
}

# Dependências obrigatórias por sistema
REQUIRED_TOOLS = {
    "windows": ["java", "make"],
    "linux": ["java", "make", "gcc", "wget"]
}

# Aliases para compatibilidade
WINDOWS_REQUIRED_TOOLS = REQUIRED_TOOLS["windows"]
LINUX_REQUIRED_TOOLS = REQUIRED_TOOLS["linux"]

# Ferramentas opcionais (serão instaladas automaticamente se ausentes)
OPTIONAL_TOOLS = {
    "windows": ["7z", "wget"],
    "linux": ["7z"]
}

# Aliases para compatibilidade
WINDOWS_OPTIONAL_TOOLS = OPTIONAL_TOOLS["windows"]
LINUX_OPTIONAL_TOOLS = OPTIONAL_TOOLS["linux"]

# Configurações de retry
DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_TIMEOUT = 300  # 5 minutos
VERIFICATION_MAX_RETRIES = 2

# Caminhos padrão
DEFAULT_INSTALL_PATH = "retro_devkits"
DEFAULT_SGDK_PATH = "retro_devkits/sgdk"
TEMP_DOWNLOAD_PATH = "temp_download"
BACKUP_PATH = "backups"

# Configurações de logging
LOG_LEVEL_DETAILED = True
LOG_DIRECTORY_LISTING = True