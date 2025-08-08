#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar a detecção customizada de aplicativos.

Este script testa especificamente a detecção dos aplicativos:
- Trae
- Visual Studio Code Insiders
- Revo Uninstaller
- Git Bash
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.detection_engine import CustomApplicationDetectionStrategy, DetectionEngine
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_custom_detection():
    """Testar a detecção customizada de aplicativos."""
    print("=" * 60)
    print("TESTE DE DETECÇÃO CUSTOMIZADA DE APLICATIVOS")
    print("=" * 60)
    
    # Criar instância da estratégia de detecção customizada
    custom_strategy = CustomApplicationDetectionStrategy()
    
    print("\n1. Testando detecção de aplicativos customizados...")
    print("-" * 50)
    
    # Testar cada aplicativo individualmente
    apps_to_test = [
        "trae",
        "vscode_insiders", 
        "revo_uninstaller",
        "git_bash"
    ]
    
    detected_apps = []
    
    for app_key in apps_to_test:
        print(f"\nTestando: {app_key}")
        app_config = custom_strategy.custom_applications.get(app_key)
        
        if app_config:
            print(f"  Nome: {app_config['name']}")
            print(f"  Descrição: {app_config['description']}")
            print(f"  Caminhos a verificar: {len(app_config['paths'])}")
            
            # Verificar cada caminho
            username = os.getenv('USERNAME', 'User')
            for i, path_template in enumerate(app_config['paths'], 1):
                exe_path = path_template.replace('{username}', username)
                exists = os.path.isfile(exe_path)
                print(f"    {i}. {exe_path} - {'✓ EXISTE' if exists else '✗ Não encontrado'}")
            
            # Tentar detectar o aplicativo
            detected = custom_strategy._detect_custom_application(app_key, app_config)
            
            if detected:
                print(f"  ✓ DETECTADO: {detected.name} v{detected.version}")
                print(f"    Caminho: {detected.executable_path}")
                print(f"    Publisher: {detected.metadata.get('publisher', 'N/A')}")
                print(f"    Método: {detected.detection_method.value}")
                detected_apps.append(detected)
            else:
                print(f"  ✗ NÃO DETECTADO")
        else:
            print(f"  ✗ Configuração não encontrada para {app_key}")
    
    print("\n" + "=" * 60)
    print("2. Testando detecção completa via DetectionEngine...")
    print("-" * 50)
    
    # Habilitar logs detalhados
    logging.getLogger("detection_engine").setLevel(logging.DEBUG)
    logging.getLogger("yaml_component_detection").setLevel(logging.DEBUG)
    
    # Testar com o DetectionEngine completo
    detection_engine = DetectionEngine()
    
    print("\nExecutando detecção completa...")
    all_detected = detection_engine.detect_all_applications()
    
    # Filtrar apenas os aplicativos customizados
    custom_detected = []
    target_names = ["trae", "visual studio code insiders", "revo uninstaller", "git bash"]
    
    for app in all_detected.applications:
        app_name_lower = app.name.lower()
        if any(target in app_name_lower for target in target_names):
            custom_detected.append(app)
    
    print(f"\nAplicativos customizados detectados pelo DetectionEngine: {len(custom_detected)}")
    
    for app in custom_detected:
        print(f"  ✓ {app.name} v{app.version}")
        print(f"    Caminho: {app.executable_path}")
        print(f"    Método: {app.detection_method.value}")
        print()
    
    print("\n" + "=" * 60)
    print("3. RESUMO DOS RESULTADOS")
    print("-" * 50)
    
    print(f"Aplicativos detectados pela estratégia customizada: {len(detected_apps)}")
    print(f"Aplicativos detectados pelo DetectionEngine: {len(custom_detected)}")
    
    if detected_apps:
        print("\nDetectados pela estratégia customizada:")
        for app in detected_apps:
            print(f"  - {app.name} ({app.executable_path})")
    
    if custom_detected:
        print("\nDetectados pelo DetectionEngine:")
        for app in custom_detected:
            print(f"  - {app.name} ({app.executable_path})")
    
    # Verificar se todos os aplicativos esperados foram detectados
    expected_apps = [
        "C:\\Users\\misae\\AppData\\Local\\Programs\\Trae\\Trae.exe",
        "C:\\Users\\misae\\AppData\\Local\\Programs\\Microsoft VS Code Insiders\\Code - Insiders.exe",
        "C:\\Program Files\\VS Revo Group\\Revo Uninstaller\\RevoUnin.exe",
        "C:\\Program Files\\Git\\git-bash.exe"
    ]
    
    print("\n" + "=" * 60)
    print("4. VERIFICAÇÃO DOS APLICATIVOS ESPERADOS")
    print("-" * 50)
    
    for expected_path in expected_apps:
        exists = os.path.isfile(expected_path)
        detected_by_custom = any(app.executable_path == expected_path for app in detected_apps)
        detected_by_engine = any(app.executable_path == expected_path for app in custom_detected)
        
        print(f"\n{os.path.basename(expected_path)}:")
        print(f"  Arquivo existe: {'✓' if exists else '✗'}")
        print(f"  Detectado pela estratégia customizada: {'✓' if detected_by_custom else '✗'}")
        print(f"  Detectado pelo DetectionEngine: {'✓' if detected_by_engine else '✗'}")
        print(f"  Caminho: {expected_path}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    test_custom_detection()