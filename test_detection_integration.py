#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de integração da detecção customizada no DetectionEngine principal.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.detection_engine import DetectionEngine, CustomApplicationDetectionStrategy

def test_detection_integration():
    """
    Testa se a detecção customizada está integrada corretamente no DetectionEngine.
    """
    print("=" * 60)
    print("TESTE DE INTEGRAÇÃO DA DETECÇÃO CUSTOMIZADA")
    print("=" * 60)
    
    # Criar instância do DetectionEngine
    engine = DetectionEngine()
    
    print(f"\n1. Estratégias registradas no DetectionEngine: {len(engine.strategies)}")
    for i, strategy in enumerate(engine.strategies, 1):
        strategy_name = strategy.__class__.__name__
        print(f"   {i}. {strategy_name}")
    
    # Verificar se CustomApplicationDetectionStrategy está presente
    custom_strategy = None
    for strategy in engine.strategies:
        if isinstance(strategy, CustomApplicationDetectionStrategy):
            custom_strategy = strategy
            break
    
    if custom_strategy:
        print("\n✓ CustomApplicationDetectionStrategy encontrada!")
        print(f"   Aplicativos customizados configurados: {len(custom_strategy.custom_applications)}")
        for app_key, app_config in custom_strategy.custom_applications.items():
            print(f"   - {app_key}: {app_config['name']}")
    else:
        print("\n✗ CustomApplicationDetectionStrategy NÃO encontrada!")
        return False
    
    print("\n2. Testando detecção via DetectionEngine...")
    print("-" * 50)
    
    # Executar detecção completa
    try:
        result = engine.detect_all_applications()
        print(f"\nDetecção completa executada com sucesso!")
        print(f"Total de aplicativos detectados: {len(result.applications)}")
        
        # Filtrar aplicativos customizados
        custom_apps = []
        target_names = ["trae", "visual studio code insiders", "revo uninstaller", "git bash"]
        
        for app in result.applications:
            app_name_lower = app.name.lower()
            if any(target in app_name_lower for target in target_names):
                custom_apps.append(app)
        
        print(f"\nAplicativos customizados detectados: {len(custom_apps)}")
        for app in custom_apps:
            print(f"  ✓ {app.name} v{app.version}")
            print(f"    Caminho: {app.executable_path}")
            print(f"    Método: {app.detection_method.value}")
            print(f"    Confiança: {app.confidence:.2f}")
            print()
        
        return len(custom_apps) > 0
        
    except Exception as e:
        print(f"\n✗ Erro durante a detecção: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_custom_strategy_directly():
    """
    Testa a estratégia customizada diretamente.
    """
    print("\n3. Testando estratégia customizada diretamente...")
    print("-" * 50)
    
    strategy = CustomApplicationDetectionStrategy()
    
    try:
        detected_apps = strategy.detect_applications()
        print(f"\nDetecção direta executada com sucesso!")
        print(f"Aplicativos detectados: {len(detected_apps)}")
        
        for app in detected_apps:
            print(f"  ✓ {app.name} v{app.version}")
            print(f"    Caminho: {app.executable_path}")
            print(f"    Método: {app.detection_method.value}")
            print()
        
        return len(detected_apps) > 0
        
    except Exception as e:
        print(f"\n✗ Erro durante a detecção direta: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # Teste de integração
        integration_success = test_detection_integration()
        
        # Teste direto
        direct_success = test_custom_strategy_directly()
        
        print("\n" + "=" * 60)
        print("RESUMO DOS TESTES")
        print("=" * 60)
        print(f"Integração no DetectionEngine: {'✓ SUCESSO' if integration_success else '✗ FALHA'}")
        print(f"Detecção direta: {'✓ SUCESSO' if direct_success else '✗ FALHA'}")
        
        if integration_success and direct_success:
            print("\n🎉 Todos os testes passaram! A detecção customizada está funcionando.")
        else:
            print("\n⚠️ Alguns testes falharam. Verifique a implementação.")
            
    except Exception as e:
        print(f"\n💥 Erro crítico durante os testes: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nTeste concluído.")