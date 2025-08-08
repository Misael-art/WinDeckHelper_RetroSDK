#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo completo da integração Steam Deck
Demonstra todas as funcionalidades implementadas para Steam Deck.
"""

import json
import time
from core.steamdeck_integration_layer import SteamDeckIntegrationLayer


def main():
    """Demonstração completa da integração Steam Deck"""
    print("🎮 Steam Deck Integration Layer - Demonstração Completa")
    print("=" * 60)
    
    # Inicializar camada de integração
    integration_layer = SteamDeckIntegrationLayer()
    
    # 1. Detecção de Hardware Steam Deck
    print("\n1️⃣ DETECÇÃO DE HARDWARE STEAM DECK")
    print("-" * 40)
    
    detection_result = integration_layer.get_comprehensive_detection_result()
    print(f"Steam Deck Detectado: {detection_result.is_steam_deck}")
    print(f"Método de Detecção: {detection_result.detection_method.value}")
    print(f"Confiança: {detection_result.confidence:.2f}")
    print(f"Modelo: {detection_result.model.value if detection_result.model else 'Desconhecido'}")
    
    if detection_result.hardware_info:
        print("Informações de Hardware:")
        for key, value in detection_result.hardware_info.items():
            print(f"  - {key}: {value}")
    
    # 2. Otimizações Steam Deck
    print("\n2️⃣ OTIMIZAÇÕES STEAM DECK")
    print("-" * 40)
    
    # Configurações de Controlador
    print("\n🎮 Configurações de Controlador:")
    controller_result = integration_layer.apply_controller_specific_configurations()
    print(f"Sucesso: {controller_result['success']}")
    print(f"Configurações Aplicadas: {len(controller_result['configurations_applied'])}")
    if controller_result['configurations_applied']:
        for config in controller_result['configurations_applied']:
            print(f"  ✅ {config}")
    
    # Otimizações de Energia
    print("\n🔋 Otimizações de Energia:")
    power_result = integration_layer.optimize_power_profiles()
    print(f"Sucesso: {power_result['success']}")
    print(f"Otimizações Aplicadas: {len(power_result['optimizations_applied'])}")
    print(f"Melhoria Estimada da Bateria: {power_result['estimated_battery_improvement']}%")
    if power_result['optimizations_applied']:
        for optimization in power_result['optimizations_applied']:
            print(f"  ⚡ {optimization}")
    
    # Configurações de Touchscreen
    print("\n👆 Configurações de Touchscreen:")
    touchscreen_result = integration_layer.configure_touchscreen_drivers()
    print(f"Sucesso: {touchscreen_result['success']}")
    print(f"Configurações Aplicadas: {len(touchscreen_result['configurations_applied'])}")
    print(f"Versão do Driver: {touchscreen_result['driver_version']}")
    if touchscreen_result['configurations_applied']:
        for config in touchscreen_result['configurations_applied']:
            print(f"  📱 {config}")
    
    # 3. Integração com Ecossistema Steam
    print("\n3️⃣ INTEGRAÇÃO COM ECOSSISTEMA STEAM")
    print("-" * 40)
    
    # Integração GlosSI
    print("\n🔗 Integração GlosSI:")
    glossi_result = integration_layer.integrate_with_glossi()
    print(f"Sucesso: {glossi_result['success']}")
    print(f"GlosSI Instalado: {glossi_result['glossi_installed']}")
    print(f"Versão: {glossi_result['glossi_version']}")
    print(f"Aplicações Suportadas: {len(glossi_result['supported_applications'])}")
    if glossi_result['supported_applications']:
        print("Aplicações:")
        for app in glossi_result['supported_applications'][:5]:  # Mostrar apenas 5
            print(f"  📱 {app}")
        if len(glossi_result['supported_applications']) > 5:
            print(f"  ... e mais {len(glossi_result['supported_applications']) - 5}")
    
    # Sincronização Steam Cloud
    print("\n☁️ Sincronização Steam Cloud:")
    cloud_result = integration_layer.synchronize_via_steam_cloud()
    print(f"Sucesso: {cloud_result['success']}")
    print(f"Cloud Sync Habilitado: {cloud_result['cloud_sync_enabled']}")
    print(f"Configurações Sincronizadas: {len(cloud_result['synced_configurations'])}")
    print(f"Status de Sincronização: {cloud_result['sync_status']}")
    if cloud_result['synced_configurations']:
        for config in cloud_result['synced_configurations']:
            print(f"  ☁️ {config}")
    
    # Modo Overlay
    print("\n🎯 Modo Overlay:")
    overlay_result = integration_layer.implement_overlay_mode()
    print(f"Sucesso: {overlay_result['success']}")
    print(f"Overlay Habilitado: {overlay_result['overlay_enabled']}")
    print(f"Hotkey: {overlay_result['overlay_hotkey']}")
    print(f"Ferramentas Suportadas: {len(overlay_result['supported_tools'])}")
    print(f"Impacto na Performance: {overlay_result['performance_impact']}")
    if overlay_result['supported_tools']:
        for tool in overlay_result['supported_tools']:
            print(f"  🛠️ {tool}")
    
    # Mapeamento Steam Input
    print("\n🎮 Mapeamento Steam Input:")
    input_result = integration_layer.configure_steam_input_mapping()
    print(f"Sucesso: {input_result['success']}")
    print(f"Steam Input Habilitado: {input_result['steam_input_enabled']}")
    print(f"Perfis de Desenvolvimento: {len(input_result['development_profiles'])}")
    print(f"Mapeamentos de Ferramentas: {len(input_result['tool_mappings'])}")
    print(f"Gestos Configurados: {len(input_result['gesture_mappings'])}")
    print(f"Macros Configurados: {len(input_result['macro_configurations'])}")
    
    if input_result['development_profiles']:
        print("Perfis de Desenvolvimento:")
        for profile_name, profile_data in input_result['development_profiles'].items():
            print(f"  🎯 {profile_data['name']}: {profile_data['description']}")
    
    # 4. Relatórios Completos
    print("\n4️⃣ RELATÓRIOS COMPLETOS")
    print("-" * 40)
    
    # Relatório de Otimizações
    print("\n📊 Relatório de Otimizações Steam Deck:")
    optimization_report = integration_layer.get_steam_deck_optimization_report()
    print(f"Steam Deck Detectado: {optimization_report['steam_deck_detected']}")
    print(f"Confiança de Detecção: {optimization_report['detection_confidence']:.2f}")
    print(f"Score Geral de Otimização: {optimization_report['overall_optimization_score']}/100")
    
    print("\nStatus das Otimizações:")
    for opt_type, opt_data in optimization_report['optimizations'].items():
        status = "✅" if opt_data['applied'] else "❌"
        print(f"  {status} {opt_type.replace('_', ' ').title()}: {opt_data['applied']}")
    
    # Relatório de Integração Steam
    print("\n🎮 Relatório de Integração Steam:")
    steam_report = integration_layer.get_steam_ecosystem_integration_report()
    print(f"Steam Deck Detectado: {steam_report['steam_deck_detected']}")
    print(f"Score Geral de Integração: {steam_report['overall_integration_score']}/100")
    print(f"Prontidão para Desenvolvimento: {steam_report['development_readiness'].upper()}")
    
    print("\nStatus das Integrações:")
    for integration_type, integration_data in steam_report['integrations'].items():
        status = "✅" if integration_data['integrated'] else "❌"
        print(f"  {status} {integration_type.replace('_', ' ').title()}: {integration_data['integrated']}")
    
    # Recomendações
    if steam_report['recommendations']:
        print("\n💡 Recomendações:")
        for recommendation in steam_report['recommendations']:
            print(f"  • {recommendation}")
    
    # Avisos
    if steam_report['warnings']:
        print("\n⚠️ Avisos:")
        for warning in steam_report['warnings']:
            print(f"  • {warning}")
    
    # 5. Demonstração de Funcionalidades Específicas
    print("\n5️⃣ FUNCIONALIDADES ESPECÍFICAS")
    print("-" * 40)
    
    # Cache de Detecção
    print("\n🗄️ Sistema de Cache:")
    print(f"Cache Válido: {integration_layer._is_cache_valid()}")
    
    # Limpar cache e detectar novamente
    integration_layer.clear_detection_cache()
    print("Cache limpo")
    print(f"Cache Válido após limpeza: {integration_layer._is_cache_valid()}")
    
    # Configuração Manual
    print("\n⚙️ Configuração Manual:")
    manual_result = integration_layer.allow_manual_configuration_for_edge_cases(True)
    print(f"Configuração Manual Aplicada: {manual_result.is_steam_deck}")
    print(f"Método de Detecção: {manual_result.detection_method.value}")
    print(f"Override Manual Ativo: {integration_layer._manual_override}")
    
    # 6. Salvar Relatórios
    print("\n6️⃣ SALVANDO RELATÓRIOS")
    print("-" * 40)
    
    # Salvar relatório de detecção
    detection_report = integration_layer.get_detection_report()
    with open("steamdeck_detection_report.json", "w") as f:
        json.dump(detection_report, f, indent=2, default=str)
    print("✅ Relatório de detecção salvo em: steamdeck_detection_report.json")
    
    # Salvar relatório de otimizações
    with open("steamdeck_optimization_report.json", "w") as f:
        json.dump(optimization_report, f, indent=2, default=str)
    print("✅ Relatório de otimizações salvo em: steamdeck_optimization_report.json")
    
    # Salvar relatório de integração Steam
    with open("steamdeck_steam_integration_report.json", "w") as f:
        json.dump(steam_report, f, indent=2, default=str)
    print("✅ Relatório de integração Steam salvo em: steamdeck_steam_integration_report.json")
    
    # 7. Resumo Final
    print("\n7️⃣ RESUMO FINAL")
    print("-" * 40)
    
    total_score = (optimization_report['overall_optimization_score'] + 
                  steam_report['overall_integration_score']) / 2
    
    print(f"\n🎯 SCORE TOTAL STEAM DECK: {total_score:.1f}/100")
    
    if total_score >= 90:
        status = "🌟 EXCELENTE"
        message = "Steam Deck está perfeitamente configurado para desenvolvimento!"
    elif total_score >= 75:
        status = "✅ MUITO BOM"
        message = "Steam Deck está bem configurado com pequenos ajustes necessários."
    elif total_score >= 60:
        status = "⚠️ BOM"
        message = "Steam Deck tem configuração básica, considere melhorias."
    else:
        status = "❌ PRECISA MELHORAR"
        message = "Steam Deck precisa de configurações significativas."
    
    print(f"Status: {status}")
    print(f"Avaliação: {message}")
    
    print(f"\n📈 Estatísticas:")
    print(f"  • Otimizações Aplicadas: {len([o for o in optimization_report['optimizations'].values() if o['applied']])}/3")
    print(f"  • Integrações Steam: {len([i for i in steam_report['integrations'].values() if i['integrated']])}/4")
    print(f"  • Tempo Total de Execução: {time.time() - start_time:.2f}s")
    
    print("\n🎮 Demonstração completa finalizada!")
    print("=" * 60)


if __name__ == "__main__":
    start_time = time.time()
    main()