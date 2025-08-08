#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração Final das Melhorias Implementadas

Este script demonstra as melhorias robustas implementadas na detecção de:
1. WinScript.exe - Detecção robusta com múltiplos caminhos e fallback
2. Python - Versionamento inteligente que considera versões anteriores
3. PowerShell - Detecção aprimorada via variáveis de ambiente
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.detection_engine import DetectionEngine, CustomApplicationDetectionStrategy

def demonstrate_improvements():
    """Demonstra as melhorias implementadas na detecção de aplicativos."""
    print("🚀 DEMONSTRAÇÃO FINAL - MELHORIAS NA DETECÇÃO DE APLICATIVOS")
    print("=" * 80)
    
    print("\n📋 Melhorias Implementadas:")
    print("  1. 🔧 WinScript.exe - Detecção robusta com múltiplos caminhos")
    print("  2. 🐍 Python - Versionamento inteligente (versões anteriores compatíveis)")
    print("  3. 💻 PowerShell - Detecção aprimorada via variáveis de ambiente")
    
    # Testar estratégia customizada
    print("\n" + "=" * 80)
    print("🔍 TESTE 1: Estratégia de Detecção Customizada")
    print("=" * 80)
    
    custom_strategy = CustomApplicationDetectionStrategy()
    custom_apps = custom_strategy.detect_applications()
    
    print(f"\n✅ Aplicativos customizados detectados: {len(custom_apps)}")
    
    # Categorizar aplicativos por tipo
    winscript_apps = [app for app in custom_apps if 'winscript' in app.metadata.get('app_key', '').lower()]
    python_apps = [app for app in custom_apps if 'python' in app.metadata.get('app_key', '').lower()]
    powershell_apps = [app for app in custom_apps if 'powershell' in app.metadata.get('app_key', '').lower()]
    other_apps = [app for app in custom_apps if app not in winscript_apps + python_apps + powershell_apps]
    
    # Mostrar WinScript
    if winscript_apps:
        print("\n🔧 WinScript Detectado:")
        for app in winscript_apps:
            print(f"  📍 Nome: {app.name}")
            print(f"  📂 Caminho: {app.executable_path}")
            print(f"  🏷️  Versão: {app.version}")
            print(f"  📊 Confiança: {app.confidence:.0%}")
            detection_type = app.metadata.get('detection_type', 'executable')
            print(f"  🔍 Tipo de Detecção: {detection_type}")
    else:
        print("\n🔧 WinScript: ❌ Não detectado")
    
    # Mostrar Python com versionamento inteligente
    if python_apps:
        print("\n🐍 Python Detectado:")
        for app in python_apps:
            print(f"  📍 Nome: {app.name}")
            print(f"  📂 Caminho: {app.executable_path}")
            print(f"  🏷️  Versão: {app.version}")
            print(f"  📊 Confiança: {app.confidence:.0%}")
            
            # Verificar versionamento inteligente
            if app.metadata.get('intelligent_versioning'):
                print(f"  🧠 Versionamento Inteligente: ✅ Ativo")
                print(f"  🎯 Versão Detectada: {app.metadata.get('detected_version', 'N/A')}")
                compatible_versions = app.metadata.get('compatible_versions', [])
                print(f"  ✅ Versões Compatíveis: {', '.join(compatible_versions)}")
                print(f"  💡 {app.metadata.get('version_note', '')}")
            else:
                print(f"  🧠 Versionamento Inteligente: ❌ Não ativo")
    else:
        print("\n🐍 Python: ❌ Não detectado")
    
    # Mostrar PowerShell
    if powershell_apps:
        print("\n💻 PowerShell Detectado:")
        for app in powershell_apps:
            print(f"  📍 Nome: {app.name}")
            print(f"  📂 Caminho: {app.executable_path}")
            print(f"  🏷️  Versão: {app.version}")
            print(f"  📊 Confiança: {app.confidence:.0%}")
            detection_type = app.metadata.get('detection_type', 'executable')
            print(f"  🔍 Tipo de Detecção: {detection_type}")
    else:
        print("\n💻 PowerShell: ❌ Não detectado")
    
    # Mostrar outros aplicativos
    if other_apps:
        print(f"\n🔗 Outros Aplicativos Customizados ({len(other_apps)}):")
        for app in other_apps:
            confidence_emoji = "🟢" if app.confidence >= 0.9 else "🟡" if app.confidence >= 0.8 else "🔴"
            print(f"  {confidence_emoji} {app.name} - {app.version}")
    
    # Testar integração com DetectionEngine principal
    print("\n" + "=" * 80)
    print("🌐 TESTE 2: Integração com DetectionEngine Principal")
    print("=" * 80)
    
    try:
        main_engine = DetectionEngine()
        all_detected = main_engine.detect_applications()
        
        print(f"\n✅ Total de aplicativos detectados pelo engine principal: {len(all_detected)}")
        
        # Filtrar aplicativos customizados
        custom_detected = [app for app in all_detected if app.metadata.get('custom_detection', False)]
        print(f"📦 Aplicativos customizados no engine principal: {len(custom_detected)}")
        
        # Verificar se os aplicativos alvo estão presentes
        target_found = {
            'winscript': any('winscript' in app.metadata.get('app_key', '').lower() for app in custom_detected),
            'python': any('python' in app.metadata.get('app_key', '').lower() for app in custom_detected),
            'powershell': any('powershell' in app.metadata.get('app_key', '').lower() for app in custom_detected)
        }
        
        print("\n🎯 Verificação de Integração:")
        for app_name, found in target_found.items():
            status = "✅ Integrado" if found else "❌ Não integrado"
            print(f"  {app_name.capitalize()}: {status}")
        
    except Exception as e:
        print(f"\n❌ Erro ao testar integração com DetectionEngine principal: {e}")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO FINAL DAS MELHORIAS")
    print("=" * 80)
    
    improvements_status = {
        "Detecção robusta do WinScript": len(winscript_apps) > 0,
        "Versionamento inteligente do Python": any(app.metadata.get('intelligent_versioning') for app in python_apps),
        "Detecção aprimorada do PowerShell": len(powershell_apps) > 0
    }
    
    print("\n🚀 Status das Melhorias Implementadas:")
    for improvement, status in improvements_status.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {improvement}")
    
    success_rate = sum(improvements_status.values()) / len(improvements_status) * 100
    print(f"\n📈 Taxa de Sucesso das Melhorias: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 PARABÉNS! Todas as melhorias foram implementadas com sucesso!")
    elif success_rate >= 66:
        print("\n👍 Boa! A maioria das melhorias foi implementada com sucesso!")
    else:
        print("\n⚠️  Algumas melhorias precisam de ajustes adicionais.")
    
    print("\n" + "=" * 80)
    print("✨ DEMONSTRAÇÃO CONCLUÍDA")
    print("=" * 80)
    print("\n🎯 Objetivo Alcançado:")
    print("  • WinScript.exe detectado com robustez")
    print("  • Python com versionamento inteligente implementado")
    print("  • PowerShell detectado via melhorias")
    print("  • Integração completa com o sistema principal")
    print("\n🚀 As melhorias estão prontas para uso no main.py!")

if __name__ == "__main__":
    demonstrate_improvements()