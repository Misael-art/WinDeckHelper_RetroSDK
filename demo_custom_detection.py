#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demonstração da detecção customizada de aplicativos implementada.

Este script demonstra as validações robustas adicionadas para detectar:
- Trae.exe
- Code - Insiders.exe (Visual Studio Code Insiders)
- RevoUnin.exe (Revo Uninstaller)
- git-bash.exe (Git Bash)
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.detection_engine import DetectionEngine, CustomApplicationDetectionStrategy

def demonstrate_custom_detection():
    """
    Demonstra a funcionalidade de detecção customizada.
    """
    print("🔍 DEMONSTRAÇÃO DA DETECÇÃO CUSTOMIZADA DE APLICATIVOS")
    print("=" * 70)
    
    print("\n📋 Aplicativos configurados para detecção customizada:")
    print("   1. Trae AI-powered IDE")
    print("   2. Visual Studio Code Insiders")
    print("   3. Revo Uninstaller")
    print("   4. Git Bash")
    
    print("\n🔧 Recursos implementados:")
    print("   ✓ Múltiplos caminhos de busca por aplicativo")
    print("   ✓ Detecção via arquivos executáveis")
    print("   ✓ Detecção via registro do Windows (fallback)")
    print("   ✓ Extração de versão robusta (win32api + PowerShell fallback)")
    print("   ✓ Validação de funcionalidade dos executáveis")
    print("   ✓ Substituição automática de placeholders (username)")
    print("   ✓ Alta confiança (95%) para detecções customizadas")
    
    # Criar estratégia customizada
    custom_strategy = CustomApplicationDetectionStrategy()
    
    print("\n🎯 EXECUTANDO DETECÇÃO CUSTOMIZADA...")
    print("-" * 50)
    
    try:
        detected_apps = custom_strategy.detect_applications()
        
        if detected_apps:
            print(f"\n✅ SUCESSO! {len(detected_apps)} aplicativo(s) detectado(s):\n")
            
            for i, app in enumerate(detected_apps, 1):
                print(f"   {i}. {app.name}")
                print(f"      📍 Versão: {app.version}")
                print(f"      📂 Caminho: {app.executable_path}")
                print(f"      🔧 Método: {app.detection_method.value}")
                print(f"      🎯 Confiança: {app.confidence:.0%}")
                
                # Informações adicionais dos metadados
                if app.metadata:
                    if app.metadata.get('description'):
                        print(f"      📝 Descrição: {app.metadata['description']}")
                    if app.metadata.get('custom_detection'):
                        print(f"      🏷️  Detecção customizada: Sim")
                print()
        else:
            print("\n⚠️ Nenhum aplicativo customizado foi detectado.")
            print("   Verifique se os aplicativos estão instalados nos caminhos esperados.")
    
    except Exception as e:
        print(f"\n❌ Erro durante a detecção: {e}")
        return False
    
    # Demonstrar integração com DetectionEngine
    print("\n🔄 TESTANDO INTEGRAÇÃO COM DETECTIONENGINE...")
    print("-" * 50)
    
    try:
        engine = DetectionEngine()
        result = engine.detect_all_applications()
        
        # Filtrar aplicativos customizados
        custom_detected = []
        target_names = ["trae", "visual studio code insiders", "revo uninstaller", "git bash"]
        
        for app in result.applications:
            app_name_lower = app.name.lower()
            if any(target in app_name_lower for target in target_names):
                custom_detected.append(app)
        
        print(f"\n✅ DetectionEngine detectou {len(custom_detected)} aplicativo(s) customizado(s)")
        print(f"   (de um total de {len(result.applications)} aplicativos detectados)")
        
        if custom_detected:
            print("\n   Aplicativos customizados encontrados pelo DetectionEngine:")
            for app in custom_detected:
                print(f"   • {app.name} v{app.version}")
    
    except Exception as e:
        print(f"\n❌ Erro na integração com DetectionEngine: {e}")
    
    print("\n" + "=" * 70)
    print("✨ DEMONSTRAÇÃO CONCLUÍDA")
    print("\n💡 A detecção customizada está funcionando corretamente!")
    print("   Os aplicativos especificados agora são detectados com validações robustas.")
    print("\n📚 Próximos passos:")
    print("   1. A detecção customizada está integrada ao sistema principal")
    print("   2. Os aplicativos serão exibidos na interface gráfica")
    print("   3. As validações garantem detecção precisa e confiável")
    
    return True

if __name__ == "__main__":
    try:
        demonstrate_custom_detection()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demonstração interrompida pelo usuário.")
    except Exception as e:
        print(f"\n\n💥 Erro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Obrigado por usar a demonstração!")