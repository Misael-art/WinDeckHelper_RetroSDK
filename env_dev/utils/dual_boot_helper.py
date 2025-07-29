#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de utilidade para preparar o sistema para dual boot Windows/Linux.
Este script fornece funções para verificar o sistema, configurar o gerenciador de boot,
e ajudar no processo de instalação do Linux em dual boot.
"""

import os
import sys
import subprocess
import logging
import winreg
import ctypes
import platform
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def is_admin():
    """Verifica se o script está sendo executado com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def check_system_compatibility():
    """
    Verifica se o sistema é compatível com dual boot com Linux.
    
    Returns:
        dict: Informações sobre compatibilidade do sistema
    """
    results = {
        "firmware_type": "Desconhecido",
        "boot_mode": "Desconhecido",
        "secure_boot": "Desconhecido",
        "fast_startup": "Desconhecido",
        "disk_partitioning": "GPT" if is_gpt_disk() else "MBR",
        "free_space": get_free_space("C:")
    }
    
    # Verifica o tipo de firmware (UEFI ou Legacy BIOS)
    try:
        output = subprocess.check_output("powershell -Command \"Get-ComputerInfo | Select-Object BiosFirmwareType\"", 
                                       shell=True, text=True, encoding='utf-8', errors='ignore')
        if "Uefi" in output:
            results["firmware_type"] = "UEFI"
            results["boot_mode"] = "UEFI"
        else:
            results["firmware_type"] = "Legacy BIOS"
            results["boot_mode"] = "Legacy"
    except:
        logger.warning("Não foi possível determinar o tipo de firmware")
    
    # Verifica se o Secure Boot está ativado (apenas para sistemas UEFI)
    if results["boot_mode"] == "UEFI":
        try:
            output = subprocess.check_output("powershell -Command \"Confirm-SecureBootUEFI\"", 
                                          shell=True, text=True, encoding='utf-8', errors='ignore')
            results["secure_boot"] = "Ativado" if "True" in output else "Desativado"
        except:
            logger.warning("Não foi possível verificar o status do Secure Boot")
    
    # Verifica se o Fast Startup está ativado
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                          r"SYSTEM\CurrentControlSet\Control\Session Manager\Power", 
                          0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "HiberbootEnabled")
            results["fast_startup"] = "Ativado" if value == 1 else "Desativado"
    except:
        logger.warning("Não foi possível verificar o status do Fast Startup")
    
    return results

def is_gpt_disk():
    """
    Verifica se o disco principal está usando tabela de partição GPT.
    
    Returns:
        bool: True se o disco estiver usando GPT, False caso contrário
    """
    try:
        output = subprocess.check_output("powershell -Command \"Get-Disk | Where-Object {$_.IsBoot -eq $true} | Select-Object -ExpandProperty PartitionStyle\"", 
                                      shell=True, text=True, encoding='utf-8', errors='ignore')
        return "GPT" in output
    except:
        logger.warning("Não foi possível determinar o estilo de partição do disco")
        return False

def get_free_space(drive):
    """
    Obtém o espaço livre em um drive específico.
    
    Args:
        drive (str): Letra da unidade (ex: "C:")
    
    Returns:
        float: Espaço livre em GB
    """
    try:
        if not drive.endswith(":"):
            drive += ":"
        
        total, used, free = shutil.disk_usage(drive)
        return round(free / (1024**3), 2)  # Converte para GB
    except:
        logger.warning(f"Não foi possível determinar o espaço livre no drive {drive}")
        return 0

def prepare_system_for_dual_boot(disable_fast_startup=True):
    """
    Prepara o sistema Windows para dual boot com Linux.
    
    Args:
        disable_fast_startup (bool): Se True, tenta desativar o Fast Startup
    
    Returns:
        bool: True se a preparação foi bem-sucedida, False caso contrário
    """
    if not is_admin():
        logger.error("Esta função requer privilégios de administrador")
        return False
    
    success = True
    
    # Desativa Fast Startup se solicitado
    if disable_fast_startup:
        try:
            subprocess.check_call("powershell -Command \"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -Name 'HiberbootEnabled' -Value 0\"", 
                                shell=True)
            logger.info("Fast Startup desativado com sucesso")
        except:
            logger.error("Não foi possível desativar o Fast Startup")
            success = False
    
    # Informa se o Secure Boot pode ser um problema
    system_info = check_system_compatibility()
    if system_info["secure_boot"] == "Ativado":
        logger.warning("O Secure Boot está ativado. Algumas distribuições Linux podem ter problemas. "
                      "Considere desativar o Secure Boot nas configurações da UEFI.")
    
    # Verifica se há espaço suficiente
    if system_info["free_space"] < 50:
        logger.warning(f"Há apenas {system_info['free_space']} GB livres. Recomendado pelo menos 50 GB para instalação do Linux.")
    
    return success

def create_system_report(output_file="dual_boot_report.txt"):
    """
    Cria um relatório detalhado sobre o sistema para auxiliar na instalação dual boot.
    
    Args:
        output_file (str): Nome do arquivo para salvar o relatório
    
    Returns:
        str: Caminho para o arquivo de relatório
    """
    system_info = check_system_compatibility()
    
    report = []
    report.append("=== Relatório de Compatibilidade para Dual Boot ===")
    report.append(f"Data: {subprocess.check_output('date /t', shell=True, text=True, encoding='utf-8', errors='ignore').strip()}")
    report.append(f"Sistema: Windows {platform.version()}")
    report.append("")
    report.append("--- Informações de Hardware e Firmware ---")
    report.append(f"Tipo de Firmware: {system_info['firmware_type']}")
    report.append(f"Modo de Boot: {system_info['boot_mode']}")
    report.append(f"Secure Boot: {system_info['secure_boot']}")
    report.append(f"Tipo de Particionamento: {system_info['disk_partitioning']}")
    report.append("")
    report.append("--- Informações de Armazenamento ---")
    report.append(f"Espaço Livre no Disco C:: {system_info['free_space']} GB")
    
    # Adiciona informações sobre discos e partições
    report.append("")
    report.append("--- Discos e Partições Disponíveis ---")
    try:
        disk_info = subprocess.check_output("powershell -Command \"Get-Disk | Format-Table -AutoSize | Out-String -Width 120\"", 
                                         shell=True, text=True, encoding='utf-8', errors='ignore')
        report.append(disk_info)
        
        partition_info = subprocess.check_output("powershell -Command \"Get-Partition | Format-Table -AutoSize | Out-String -Width 120\"", 
                                              shell=True, text=True, encoding='utf-8', errors='ignore')
        report.append(partition_info)
    except:
        report.append("Não foi possível obter informações detalhadas sobre discos e partições.")
    
    # Adiciona informações de compatibilidade e recomendações
    report.append("")
    report.append("--- Análise de Compatibilidade ---")
    
    # Verifica o modo de boot
    if system_info["boot_mode"] == "UEFI" and system_info["disk_partitioning"] == "GPT":
        report.append("✓ Configuração ideal: UEFI com particionamento GPT")
    elif system_info["boot_mode"] == "Legacy" and system_info["disk_partitioning"] == "MBR":
        report.append("✓ Configuração compatível: Legacy BIOS com particionamento MBR")
    elif system_info["boot_mode"] == "UEFI" and system_info["disk_partitioning"] == "MBR":
        report.append("⚠ Configuração mista: UEFI com particionamento MBR - Pode causar problemas!")
    elif system_info["boot_mode"] == "Legacy" and system_info["disk_partitioning"] == "GPT":
        report.append("⚠ Configuração mista: Legacy BIOS com particionamento GPT - Pode causar problemas!")
    
    # Verifica o Secure Boot
    if system_info["secure_boot"] == "Ativado":
        report.append("⚠ Secure Boot está ativado - Distribuições Linux podem precisar de configuração especial ou desativar o Secure Boot")
    else:
        report.append("✓ Secure Boot está desativado - Compatível com a maioria das distribuições Linux")
    
    # Verifica o Fast Startup
    if system_info["fast_startup"] == "Ativado":
        report.append("⚠ Fast Startup está ativado - Recomendado desativar para evitar problemas com o dual boot")
    else:
        report.append("✓ Fast Startup está desativado - Configuração ideal para dual boot")
    
    # Verifica o espaço livre
    if system_info["free_space"] >= 50:
        report.append(f"✓ Espaço livre suficiente ({system_info['free_space']} GB) - Recomendado mínimo de 50 GB")
    else:
        report.append(f"⚠ Espaço livre insuficiente ({system_info['free_space']} GB) - Considere liberar mais espaço")
    
    # Adiciona recomendações finais
    report.append("")
    report.append("--- Recomendações Finais ---")
    report.append("1. Sempre faça backup de dados importantes antes de qualquer modificação no sistema")
    report.append("2. Desfragmente o disco Windows antes de redimensionar partições")
    report.append("3. Se possível, use o modo de instalação 'ao lado do Windows' das distribuições Linux")
    report.append("4. Após a instalação, use o Grub2Win se precisar de mais controle sobre o processo de boot")
    report.append("5. Em caso de problemas, o Assistente de Dual Boot instalado pode ajudar na recuperação")
    
    # Escreve o relatório para um arquivo
    file_path = os.path.join(os.path.expanduser("~"), "Desktop", output_file)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    return file_path

def install_linux_iso_helper():
    """
    Abre uma interface para ajudar o usuário a selecionar e baixar uma ISO do Linux.
    """
    # Verifica se há navegador instalado
    default_browser = subprocess.check_output("powershell -Command \"(Get-ItemProperty HKCU:\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice).ProgId\"", 
                                           shell=True, text=True, encoding='utf-8', errors='ignore').strip()
    
    print("\n=== Assistente para Download de Linux ===")
    print("Distribuições Recomendadas para Dual Boot:")
    print("1. Ubuntu - Amigável para iniciantes, bom suporte para hardware")
    print("2. Linux Mint - Baseado no Ubuntu, interface familiar")
    print("3. Fedora - Inovador, atualizações frequentes")
    print("4. Pop!_OS - Otimizado para programadores e jogos")
    print("5. Zorin OS - Experiência similar ao Windows")
    print("6. Outra (pesquisar)")
    
    choice = input("\nEscolha uma opção (1-6): ")
    
    urls = {
        "1": "https://ubuntu.com/download/desktop",
        "2": "https://linuxmint.com/download.php",
        "3": "https://getfedora.org/",
        "4": "https://pop.system76.com/",
        "5": "https://zorin.com/os/download/",
        "6": "https://distrowatch.com/"
    }
    
    if choice in urls:
        url = urls[choice]
        print(f"\nAbrindo navegador em: {url}")
        try:
            os.system(f"start {url}")
        except:
            print(f"Não foi possível abrir o navegador. Visite: {url}")
    else:
        print("Opção inválida!")
    
    print("\nApós baixar a ISO:")
    print("1. Use Rufus para criar uma mídia bootável: https://rufus.ie/")
    print("2. Desative o Fast Startup no Windows")
    print("3. Durante a instalação, escolha 'Instalar ao lado do Windows'")
    print("4. Se solicitado, permita que o instalador redimensione as partições")

def disable_fast_startup():
    """
    Desativa o Fast Startup do Windows para melhor compatibilidade com dual boot.
    
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    if not is_admin():
        print("Esta operação requer privilégios de administrador!")
        return False
    
    try:
        subprocess.check_call("powershell -Command \"Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power' -Name 'HiberbootEnabled' -Value 0\"", 
                            shell=True)
        print("Fast Startup desativado com sucesso!")
        return True
    except:
        print("Não foi possível desativar o Fast Startup.")
        print("Tente desativar manualmente: Painel de Controle -> Opções de Energia -> Escolher a função dos botões de energia -> Desmarcar 'Ligar inicialização rápida'")
        return False

def detect_operating_systems():
    """
    Detecta outros sistemas operacionais instalados no computador.
    
    Returns:
        dict: Dicionário com informações sobre sistemas operacionais encontrados
    """
    os_info = {
        "windows": {
            "installed": True,  # Assumimos que Windows está instalado já que estamos rodando nele
            "version": platform.version(),
            "path": os.environ.get("SystemRoot", "C:\\Windows")
        },
        "linux": {
            "installed": False,
            "distros": [],
            "partitions": []
        },
        "macos": {
            "installed": False
        },
        "other": {
            "installed": False,
            "names": []
        }
    }
    
    # Procura por sinais de instalações Linux
    try:
        # Verifica partições com possíveis instalações Linux
        output = subprocess.check_output("powershell -Command \"Get-Partition | Format-Table -AutoSize | Out-String -Width 4096\"", 
                                     shell=True, text=True, encoding='utf-8', errors='ignore')
        
        # Procura por partições com tipos conhecidos de Linux
        if "EFI" in output or "Linux" in output or "83" in output or "0x83" in output:
            os_info["linux"]["installed"] = True
            
            # Tenta identificar distribuições pelo tipo de partição
            if "0x83" in output or "83" in output:
                os_info["linux"]["partitions"].append("Linux Native")
            if "0x82" in output or "82" in output:
                os_info["linux"]["partitions"].append("Linux Swap")
            if "0x8e" in output or "8e" in output:
                os_info["linux"]["partitions"].append("Linux LVM")
                
        # Verifica se existe GRUB ou bootloaders Linux
        if os.path.exists("C:/boot/grub") or os.path.exists("C:/grub"):
            os_info["linux"]["installed"] = True
            os_info["linux"]["distros"].append("Unknown (GRUB found)")
            
    except Exception as e:
        logger.warning(f"Erro ao detectar sistemas Linux: {e}")
    
    # Verifica se há entradas no BCD para outros sistemas
    try:
        output = subprocess.check_output("bcdedit /enum all", shell=True, text=True, encoding='utf-8', errors='ignore')
        if "linux" in output.lower() or "ubuntu" in output.lower() or "fedora" in output.lower() or "debian" in output.lower():
            os_info["linux"]["installed"] = True
            
            # Tenta identificar distribuições pelo nome no BCD (adiciona mais distros)
            detected_distros_bcd = set() # Usa um set para evitar duplicatas
            if "ubuntu" in output.lower(): detected_distros_bcd.add("Ubuntu")
            if "fedora" in output.lower(): detected_distros_bcd.add("Fedora")
            if "debian" in output.lower(): detected_distros_bcd.add("Debian")
            if "arch" in output.lower(): detected_distros_bcd.add("Arch Linux")
            if "suse" in output.lower(): detected_distros_bcd.add("SUSE Linux")
            if "mint" in output.lower(): detected_distros_bcd.add("Linux Mint")
            if "manjaro" in output.lower(): detected_distros_bcd.add("Manjaro")
            if "popos" in output.lower() or "pop!_os" in output.lower(): detected_distros_bcd.add("Pop!_OS")
            if "zorin" in output.lower(): detected_distros_bcd.add("Zorin OS")
            if "elementary" in output.lower(): detected_distros_bcd.add("elementary OS")
            
            # Adiciona as distros detectadas no BCD à lista principal (evitando duplicatas)
            current_distros = set(os_info["linux"]["distros"])
            current_distros.update(detected_distros_bcd)
            os_info["linux"]["distros"] = sorted(list(current_distros)) # Mantém ordenado

    except Exception as e:
        logger.warning(f"Erro ao verificar o BCD: {e}")
    
    # Verifica outras possíveis entradas de boot
    try:
        if os.path.exists("C:/Program Files/Grub2Win"):
            # Verifica configuração do Grub2Win
            if os.path.exists("C:/Program Files/Grub2Win/g2bootmgr/grub.cfg"):
                with open("C:/Program Files/Grub2Win/g2bootmgr/grub.cfg", "r", encoding="utf-8", errors="ignore") as f:
                    grub_config = f.read().lower()
                    if "linux" in grub_config:
                        os_info["linux"]["installed"] = True
                    if "macos" in grub_config or "darwin" in grub_config:
                        os_info["macos"]["installed"] = True
    except Exception as e:
        logger.warning(f"Erro ao verificar configuração do Grub2Win: {e}")
    
    return os_info

def automated_dual_boot_setup():
    """
    Executa automaticamente o diagnóstico e configuração de dual boot, apresentando feedback
    sobre pontos críticos e problemas potenciais.
    
    Returns:
        bool: True se o processo foi concluído com sucesso, False caso contrário
    """
    print("\n===== CONFIGURAÇÃO AUTOMÁTICA DE DUAL BOOT =====")
    print("Iniciando diagnóstico e configuração automática...")
    
    # 1. Verifica privilégios de administrador
    if not is_admin():
        print("\n[ERRO] Esta ferramenta requer privilégios de administrador.")
        print("Por favor, reinicie o script como administrador.")
        return False
    
    # 2. Detecta outros sistemas operacionais
    print("\n[1/5] Detectando sistemas operacionais instalados...")
    os_info = detect_operating_systems()
    
    print("\nSistemas operacionais detectados:")
    print(f"- Windows {os_info['windows']['version']}")
    
    if os_info["linux"]["installed"]:
        print("- Linux:")
        if os_info["linux"]["distros"]:
            for distro in os_info["linux"]["distros"]:
                print(f"  * {distro}")
        else:
            print("  * Instalação Linux genérica detectada")
        
        if os_info["linux"]["partitions"]:
            print("  * Partições Linux encontradas:")
            for part in os_info["linux"]["partitions"]:
                print(f"    - {part}")
    
    if os_info["macos"]["installed"]:
        print("- macOS")
    
    if os_info["other"]["installed"]:
        print("- Outros sistemas:")
        for name in os_info["other"]["names"]:
            print(f"  * {name}")
    
    # 3. Verifica a compatibilidade do sistema
    print("\n[2/5] Verificando compatibilidade do sistema...")
    compat_info = check_system_compatibility()
    
    issues = []
    warnings = []
    
    # Analisa problemas críticos e avisos
    if compat_info["firmware_type"] == "Legacy BIOS" and compat_info["disk_partitioning"] == "GPT":
        issues.append("Sistema usando Legacy BIOS com particionamento GPT - Incompatibilidade crítica")
    
    if compat_info["firmware_type"] == "UEFI" and compat_info["disk_partitioning"] == "MBR":
        issues.append("Sistema usando UEFI com particionamento MBR - Incompatibilidade crítica")
    
    if compat_info["secure_boot"] == "Ativado":
        warnings.append("Secure Boot está ativado - Pode impedir a inicialização de algumas distribuições Linux")
    
    if compat_info["fast_startup"] == "Ativado":
        warnings.append("Fast Startup está ativado - Pode causar problemas de acesso às partições Windows pelo Linux")
    
    if compat_info["free_space"] < 30:
        warnings.append(f"Pouco espaço livre ({compat_info['free_space']} GB) - Recomendado pelo menos 30 GB para Linux")
    
    if compat_info["free_space"] < 15:
        issues.append(f"Espaço livre muito baixo ({compat_info['free_space']} GB) - Insuficiente para instalação adequada")
    
    # Imprime diagnóstico de compatibilidade
    print("\nDiagnóstico de compatibilidade:")
    print(f"- Firmware: {compat_info['firmware_type']}")
    print(f"- Modo de Boot: {compat_info['boot_mode']}")
    print(f"- Secure Boot: {compat_info['secure_boot']}")
    print(f"- Fast Startup: {compat_info['fast_startup']}")
    print(f"- Particionamento: {compat_info['disk_partitioning']}")
    print(f"- Espaço Livre: {compat_info['free_space']} GB")
    
    # 4. Reporta problemas críticos e avisos
    if issues:
        print("\n[PROBLEMAS CRÍTICOS]")
        for issue in issues:
            print(f"❌ {issue}")
        
        print("\nRecomendação: Resolver os problemas críticos antes de continuar.")
        prompt = input("\nContinuar mesmo com problemas críticos? (s/N): ")
        if prompt.lower() != 's':
            return False
    
    if warnings:
        print("\n[AVISOS]")
        for warning in warnings:
            print(f"⚠️ {warning}")
    
    # 5. Desativa o Fast Startup automaticamente se necessário
    if compat_info["fast_startup"] == "Ativado":
        print("\n[3/5] Desativando Fast Startup...")
        if disable_fast_startup():
            print("✅ Fast Startup desativado com sucesso.")
        else:
            print("❌ Não foi possível desativar o Fast Startup automaticamente.")
            print("Recomendação: Desative manualmente através do Painel de Controle.")
    else:
        print("\n[3/5] Fast Startup já está desativado.")
    
    # 6. Verifica ou instala as ferramentas necessárias
    print("\n[4/5] Verificando ferramentas de gerenciamento de boot...")
    
    # Verifica se Grub2Win está instalado
    grub2win_installed = os.path.exists("C:/Program Files/Grub2Win/grub2win.exe")
    
    if not grub2win_installed:
        print("Grub2Win não detectado. Instalando...")
        try:
            subprocess.check_call([sys.executable, 
                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                            "environment_dev.py"), 
                                "--install", "Grub2Win"])
            print("✅ Grub2Win instalado com sucesso.")
            grub2win_installed = True
        except:
            print("❌ Falha ao instalar Grub2Win.")
    else:
        print("✅ Grub2Win já está instalado.")
    
    # 7. Configura o gerenciador de boot se possível
    print("\n[5/5] Configurando gerenciador de boot...")
    
    if grub2win_installed:
        if os_info["linux"]["installed"]:
            print("Linux detectado. Verificando configuração atual do Grub2Win...")
            # Verifica ou cria configuração para Linux
            try:
                if os.path.exists("C:/Program Files/Grub2Win/g2bootmgr/grub.cfg"):
                    with open("C:/Program Files/Grub2Win/g2bootmgr/grub.cfg", "r", encoding="utf-8", errors="ignore") as f:
                        grub_config = f.read()
                    
                    if "linux" in grub_config.lower() or "ubuntu" in grub_config.lower() or "fedora" in grub_config.lower():
                        print("✅ Configuração do Grub2Win para Linux já existe.")
                    else:
                        print("É necessário configurar o Grub2Win manualmente para o Linux encontrado.")
                        print("Iniciando Grub2Win...")
                        subprocess.Popen(["C:/Program Files/Grub2Win/grub2win.exe"])
                else:
                    print("Arquivo de configuração do Grub2Win não encontrado.")
                    print("Iniciando Grub2Win para configuração manual...")
                    subprocess.Popen(["C:/Program Files/Grub2Win/grub2win.exe"])
            except Exception as e:
                print(f"❌ Erro ao verificar configuração do Grub2Win: {e}")
        else:
            print("Nenhum sistema Linux detectado. Grub2Win está pronto para uso futuro.")
    else:
        print("❌ Grub2Win não está instalado. A configuração do gerenciador de boot deve ser feita manualmente.")
    
    # 8. Gera relatório final
    report_path = create_system_report("dual_boot_config_report.txt")
    print(f"\nRelatório detalhado criado em: {report_path}")
    
    # 9. Resumo e próximos passos
    print("\n===== CONFIGURAÇÃO FINALIZADA =====")
    
    if issues:
        print("\n⚠️ ATENÇÃO: Problemas críticos foram encontrados e podem impedir o dual boot adequado.")
    
    print("\nPróximos passos:")
    if not os_info["linux"]["installed"]:
        print("1. Baixe a distribuição Linux de sua preferência")
        print("2. Crie uma mídia bootável com a ISO do Linux")
        print("3. Instale o Linux selecionando a opção 'Instalar ao lado do Windows'")
        print("4. Após a instalação, use o Grub2Win para configurar o menu de boot se necessário")
    else:
        print("1. Use o Grub2Win para ajustar a configuração de boot se necessário")
        print("2. Teste o boot em ambos os sistemas para verificar funcionamento")
    
    print("\nFerramentas disponíveis:")
    print("- Grub2Win: Gerenciador de boot para Windows e Linux")
    print("- Assistente de Dual Boot: Utilitário avançado para gerenciar dual boot")
    
    print("\nObrigado por usar o Assistente de Configuração Automática de Dual Boot!")
    
    return True

def main():
    """Função principal que serve como interface de linha de comando."""
    if not sys.platform.startswith('win'):
        print("Este script é destinado apenas para sistemas Windows.")
        return 1
    
    # Verifica se foi solicitado modo automático através de argumentos de linha de comando
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        return 0 if automated_dual_boot_setup() else 1
    
    print("=== Assistente de Preparação para Dual Boot Windows/Linux ===")
    print("Este assistente ajudará a preparar seu sistema Windows para instalação de Linux em dual boot.")
    
    # Verifica privilégios de administrador
    if not is_admin():
        print("\nALERTA: Este script não está sendo executado como administrador.")
        print("Algumas funcionalidades podem não estar disponíveis.")
        print("Recomendado executar como administrador para funcionalidade completa.\n")
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Verificar compatibilidade do sistema")
        print("2. Gerar relatório detalhado do sistema")
        print("3. Desativar Fast Startup (recomendado)")
        print("4. Ajuda para baixar distribuições Linux")
        print("5. Abrir ferramenta de particionamento")
        print("6. Modo Automático (diagnóstico e configuração)")
        print("7. Sair")
        
        choice = input("\nEscolha uma opção (1-7): ")
        
        if choice == "1":
            print("\nVerificando compatibilidade do sistema...")
            compat_info = check_system_compatibility()
            
            print("\n=== Informações do Sistema ===")
            print(f"Firmware: {compat_info['firmware_type']}")
            print(f"Modo de Boot: {compat_info['boot_mode']}")
            print(f"Secure Boot: {compat_info['secure_boot']}")
            print(f"Fast Startup: {compat_info['fast_startup']}")
            print(f"Particionamento: {compat_info['disk_partitioning']}")
            print(f"Espaço Livre em C:: {compat_info['free_space']} GB")
            
            # Analisa compatibilidade
            issues = []
            if compat_info['secure_boot'] == "Ativado":
                issues.append("- Secure Boot está ativado, pode causar problemas com algumas distribuições Linux")
            if compat_info['fast_startup'] == "Ativado":
                issues.append("- Fast Startup está ativado, pode causar problemas de acesso às partições")
            if compat_info['free_space'] < 50:
                issues.append(f"- Pouco espaço livre ({compat_info['free_space']} GB), recomendado pelo menos 50 GB")
            
            if issues:
                print("\nProblemas potenciais detectados:")
                for issue in issues:
                    print(issue)
            else:
                print("\nNenhum problema potencial detectado. O sistema parece pronto para dual boot!")
        
        elif choice == "2":
            print("\nGerando relatório detalhado do sistema...")
            report_path = create_system_report()
            print(f"Relatório gerado com sucesso: {report_path}")
        
        elif choice == "3":
            print("\nDesativando Fast Startup...")
            if is_admin():
                disable_fast_startup()
            else:
                print("Esta operação requer privilégios de administrador!")
                print("Execute o script como administrador ou desative manualmente:")
                print("Painel de Controle -> Opções de Energia -> Escolher a função dos botões de energia -> Desmarcar 'Ligar inicialização rápida'")
        
        elif choice == "4":
            install_linux_iso_helper()
        
        elif choice == "5":
            print("\nAbrindo ferramenta de particionamento do Windows...")
            try:
                subprocess.Popen("diskmgmt.msc")
            except:
                print("Não foi possível abrir o Gerenciador de Disco.")
                print("Abra manualmente: Painel de Controle -> Ferramentas Administrativas -> Gerenciamento de Computador -> Gerenciamento de Disco")
        
        elif choice == "6":
            automated_dual_boot_setup()
        
        elif choice == "7":
            print("\nSaindo do assistente. Boa sorte com sua instalação de dual boot!")
            break
        
        else:
            print("\nOpção inválida! Por favor, escolha uma opção de 1 a 7.")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    sys.exit(main()) 