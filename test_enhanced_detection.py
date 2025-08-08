#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar as melhorias na detecção de aplicativos:
- WinScript.exe com detecção robusta
- Python com versionamento inteligente
- PowerShell com detecção via variáveis de ambiente
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.detection_engine import CustomApplicationDetectionStrategy

def test_enhanced_detection():
    """Testa as melhorias na detecção de aplicativos."""
    print("🔍 Testando Detecção Aprimorada de Aplicativos")
    print("=" * 60)
    
    # Inicializar estratégia de detecção customizada
    strategy = CustomApplicationDetectionStrategy()
    
    # Testar detecção de aplicativos específicos
    target_apps = ["winscript", "python", "powershell"]
    
    print("\n📋 Aplicativos alvo para teste:")
    for app in target_apps:
        print(f"  • {app}")
    
    print("\n🔎 Executando detecção...")
    detected_apps = strategy.detect_applications(target_apps)
    
    print(f"\n✅ Aplicativos detectados: {len(detected_apps)}")
    print("=" * 60)
    
    for i, app in enumerate(detected_apps, 1):
        print(f"\n{i}. {app.name}")
        print(f"   📍 Caminho: {app.executable_path}")
        print(f"   🏷️  Versão: {app.version}")
        print(f"   📂 Instalação: {app.install_path}")
        print(f"   🔍 Método: {app.detection_method.value}")
        print(f"   📊 Confiança: {app.confidence:.0%}")
        print(f"   📝 Descrição: {app.metadata.get('description', 'N/A')}")
        
        # Informações específicas para Python (versionamento inteligente)
        if 'intelligent_versioning' in app.metadata:
            print(f"   🧠 Versionamento Inteligente: Ativo")
            print(f"   🎯 Versão Detectada: {app.metadata.get('detected_version', 'N/A')}")
            print(f"   ✅ Versões Compatíveis: {', '.join(app.metadata.get('compatible_versions', []))}")
            print(f"   💡 Nota: {app.metadata.get('version_note', 'N/A')}")
        
        # Informações específicas para detecção especial
        if 'detection_type' in app.metadata:
            print(f"   🔧 Tipo de Detecção: {app.metadata['detection_type']}")
        
        print(f"   🏆 Status: {app.status.value}")
    
    # Testar detecção geral (todos os aplicativos customizados)
    print("\n" + "=" * 60)
    print("🌐 Testando Detecção Geral (Todos os Aplicativos Customizados)")
    print("=" * 60)
    
    all_detected = strategy.detect_applications()
    print(f"\n✅ Total de aplicativos customizados detectados: {len(all_detected)}")
    
    for app in all_detected:
        confidence_emoji = "🟢" if app.confidence >= 0.9 else "🟡" if app.confidence >= 0.8 else "🔴"
        print(f"  {confidence_emoji} {app.name} - {app.version} ({app.confidence:.0%})")
    
    # Verificações específicas
    print("\n" + "=" * 60)
    print("🧪 Verificações Específicas")
    print("=" * 60)
    
    # Verificar se WinScript foi detectado
    winscript_detected = any(app.metadata.get('app_key') == 'winscript' for app in all_detected)
    print(f"\n🔧 WinScript detectado: {'✅ Sim' if winscript_detected else '❌ Não'}")
    
    # Verificar se Python foi detectado com versionamento inteligente
    python_detected = any(app.metadata.get('app_key') == 'python' for app in all_detected)
    python_intelligent = any(app.metadata.get('intelligent_versioning') for app in all_detected)
    print(f"🐍 Python detectado: {'✅ Sim' if python_detected else '❌ Não'}")
    print(f"🧠 Versionamento inteligente ativo: {'✅ Sim' if python_intelligent else '❌ Não'}")
    
    # Verificar se PowerShell foi detectado
    powershell_detected = any(app.metadata.get('app_key') == 'powershell' for app in all_detected)
    print(f"💻 PowerShell detectado: {'✅ Sim' if powershell_detected else '❌ Não'}")
    
    print("\n" + "=" * 60)
    print("🎯 Resumo dos Testes")
    print("=" * 60)
    print(f"• Aplicativos alvo testados: {len(target_apps)}")
    print(f"• Aplicativos detectados nos testes específicos: {len(detected_apps)}")
    print(f"• Total de aplicativos customizados detectados: {len(all_detected)}")
    print(f"• Taxa de sucesso nos testes específicos: {len(detected_apps)/len(target_apps)*100:.1f}%")
    
    # Verificar melhorias implementadas
    improvements = []
    if winscript_detected:
        improvements.append("✅ Detecção robusta do WinScript")
    if python_intelligent:
        improvements.append("✅ Versionamento inteligente do Python")
    if powershell_detected:
        improvements.append("✅ Detecção aprimorada do PowerShell")
    
    print("\n🚀 Melhorias implementadas:")
    for improvement in improvements:
        print(f"  {improvement}")
    
    if not improvements:
        print("  ⚠️  Nenhuma melhoria foi detectada como ativa")
    
    print("\n" + "=" * 60)
    print("✨ Teste de Detecção Aprimorada Concluído!")
    print("=" * 60)

if __name__ == "__main__":
    test_enhanced_detection()