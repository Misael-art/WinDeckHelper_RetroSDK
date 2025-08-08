#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para problemas de detecção de software
Verifica os componentes específicos mencionados pelo usuário
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_hardlinkshellext():
    """Verifica HardLinkShellExt_X64"""
    print("\n=== Verificando HardLinkShellExt_X64 ===")
    
    # Caminhos possíveis
    paths = [
        r"C:\Program Files\HardlinkShellExt\HardlinkShellExt.dll",
        r"C:\Program Files (x86)\HardlinkShellExt\HardlinkShellExt.dll",
        r"C:\Windows\System32\HardlinkShellExt.dll",
        r"C:\Windows\SysWOW64\HardlinkShellExt.dll"
    ]
    
    found = False
    for path in paths:
        if os.path.exists(path):
            print(f"✓ Encontrado: {path}")
            print(f"  Tamanho: {os.path.getsize(path)} bytes")
            found = True
        else:
            print(f"✗ Não encontrado: {path}")
    
    if not found:
        print("❌ HardLinkShellExt não detectado em nenhum local padrão")
    
    return found

def check_revo_uninstaller():
    """Verifica Revo Uninstaller"""
    print("\n=== Verificando Revo Uninstaller ===")
    
    # Caminhos possíveis
    paths = [
        os.path.expandvars(r"${ProgramFiles}\Revo Uninstaller Free\RevoUPort.exe"),
        r"C:\Program Files\Revo Uninstaller Free\RevoUPort.exe",
        r"C:\Program Files (x86)\Revo Uninstaller Free\RevoUPort.exe",
        r"C:\Program Files\VS Revo Group\Revo Uninstaller\Revouninstaller.exe",
        r"C:\Program Files (x86)\VS Revo Group\Revo Uninstaller\Revouninstaller.exe"
    ]
    
    found = False
    for path in paths:
        if os.path.exists(path):
            print(f"✓ Encontrado: {path}")
            print(f"  Tamanho: {os.path.getsize(path)} bytes")
            found = True
        else:
            print(f"✗ Não encontrado: {path}")
    
    if not found:
        print("❌ Revo Uninstaller não detectado em nenhum local padrão")
    
    return found

def check_kde_plasma():
    """Verifica KDE Plasma (deve ser falso positivo no Windows)"""
    print("\n=== Verificando KDE Plasma (deve ser falso no Windows) ===")
    
    # No Windows, KDE Plasma não deveria estar instalado
    if os.name == 'nt':
        print("✓ Sistema Windows detectado - KDE Plasma não deveria estar disponível")
        print("❌ Se o sistema está detectando KDE Plasma, é um falso positivo")
        return False
    else:
        print("Sistema não-Windows detectado")
        return True

def check_protondb():
    """Verifica ProtonDB (deve ser falso positivo no Windows)"""
    print("\n=== Verificando ProtonDB (deve ser falso no Windows) ===")
    
    # ProtonDB é apenas um site, não um software instalável
    print("✓ ProtonDB é apenas um site web (https://www.protondb.com/)")
    print("❌ Se o sistema está tentando detectar ProtonDB como software instalado, é um erro")
    return False

def check_powershell_preview():
    """Verifica PowerShell Preview"""
    print("\n=== Verificando PowerShell Preview ===")
    
    # Verifica PowerShell Core/Preview
    pwsh_paths = [
        shutil.which("pwsh"),
        shutil.which("pwsh-preview"),
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        r"C:\Program Files\PowerShell\7-preview\pwsh.exe"
    ]
    
    found = False
    for path in pwsh_paths:
        if path and os.path.exists(path):
            print(f"✓ Encontrado: {path}")
            try:
                result = subprocess.run([path, "-Command", "$PSVersionTable.PSVersion"], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"  Versão: {version}")
                    if "preview" in version.lower():
                        print("  ✓ Versão Preview detectada")
                        found = True
            except Exception as e:
                print(f"  Erro ao verificar versão: {e}")
        else:
            print(f"✗ Não encontrado: {path}")
    
    # Verifica Windows PowerShell padrão
    winps_path = shutil.which("powershell")
    if winps_path:
        print(f"✓ Windows PowerShell encontrado: {winps_path}")
        try:
            result = subprocess.run([winps_path, "-Command", "$PSVersionTable.PSVersion"], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  Versão: {version}")
        except Exception as e:
            print(f"  Erro ao verificar versão: {e}")
    
    if not found:
        print("❌ PowerShell Preview não detectado")
    
    return found

def check_python_313():
    """Verifica Python 3.13"""
    print("\n=== Verificando Python 3.13 ===")
    
    # Verifica Python no PATH
    python_paths = [
        shutil.which("python"),
        shutil.which("python3"),
        shutil.which("python3.13"),
        shutil.which("py")
    ]
    
    found_313 = False
    for path in python_paths:
        if path and os.path.exists(path):
            print(f"✓ Python encontrado: {path}")
            try:
                result = subprocess.run([path, "--version"], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"  Versão: {version}")
                    if "3.13" in version:
                        print("  ✓ Python 3.13 detectado")
                        found_313 = True
            except Exception as e:
                print(f"  Erro ao verificar versão: {e}")
    
    # Verifica instalações via py launcher
    try:
        result = subprocess.run(["py", "-0"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("\nVersões Python disponíveis via py launcher:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
                if "3.13" in line:
                    found_313 = True
    except Exception as e:
        print(f"Erro ao verificar py launcher: {e}")
    
    if not found_313:
        print("❌ Python 3.13 não detectado")
    
    return found_313

def main():
    """Função principal"""
    print("Diagnóstico de Problemas de Detecção de Software")
    print("=" * 50)
    
    results = {
        "HardLinkShellExt_X64": check_hardlinkshellext(),
        "Revo Uninstaller": check_revo_uninstaller(),
        "KDE Plasma": check_kde_plasma(),
        "ProtonDB": check_protondb(),
        "PowerShell Preview": check_powershell_preview(),
        "Python 3.13": check_python_313()
    }
    
    print("\n" + "=" * 50)
    print("RESUMO DOS RESULTADOS:")
    print("=" * 50)
    
    for component, detected in results.items():
        status = "✓ DETECTADO" if detected else "✗ NÃO DETECTADO"
        print(f"{component:20} : {status}")
    
    print("\nNOTAS:")
    print("- KDE Plasma e ProtonDB não deveriam ser detectados no Windows")
    print("- Se eles estão sendo detectados, são falsos positivos")
    print("- Verifique as configurações nos arquivos YAML para corrigir")

if __name__ == "__main__":
    main()