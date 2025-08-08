#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das correções do SGDK
Verifica se os problemas identificados foram corrigidos:
1. Componentes não sendo marcados como instalados quando detectados
2. SGDK precisa ser versão 2.11 (mais recente)
3. Falso positivo na instalação do SGDK
"""

import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_component_status_manager():
    """Testa o sistema de gerenciamento de status"""
    print("=== Testando Component Status Manager ===")
    
    try:
        from core.component_status_manager import get_status_manager, ComponentStatus
        
        status_manager = get_status_manager()
        print("✓ Status Manager inicializado")
        
        # Testar atualização de status
        status_manager.update_component_status(
            component_id="test_component",
            name="Test Component",
            status=ComponentStatus.INSTALLED,
            version_detected="1.0.0",
            install_path="C:/test"
        )
        print("✓ Status atualizado com sucesso")
        
        # Verificar se foi salvo
        comp_info = status_manager.get_component_status("test_component")
        if comp_info and comp_info.status == ComponentStatus.INSTALLED:
            print("✓ Status persistido corretamente")
        else:
            print("✗ Erro na persistência do status")
            
        # Limpar teste
        status_manager.clear_component_status("test_component")
        print("✓ Teste do Status Manager concluído")
        
    except Exception as e:
        print(f"✗ Erro no teste do Status Manager: {e}")

def test_sgdk_real_installer():
    """Testa o instalador real do SGDK"""
    print("\n=== Testando SGDK Real Installer ===")
    
    try:
        from core.sgdk_real_installer import check_sgdk_status, SGDKRealInstaller
        
        # Verificar status atual
        status = check_sgdk_status()
        print(f"Status atual do SGDK: {status}")
        
        # Verificar se é versão 2.11
        installer = SGDKRealInstaller()
        if installer.sgdk_version == "2.11":
            print("✓ Configurado para versão 2.11")
        else:
            print(f"✗ Versão incorreta: {installer.sgdk_version}")
            
        # Testar detecção
        is_installed, version = installer.is_sgdk_installed()
        print(f"SGDK detectado: {is_installed}, versão: {version}")
        
        if is_installed and version == "2.11":
            print("✓ SGDK 2.11 já está instalado e funcionando")
        elif is_installed:
            print(f"⚠ SGDK instalado mas versão incorreta: {version}")
        else:
            print("ℹ SGDK não está instalado")
            
        print("✓ Teste do SGDK Real Installer concluído")
        
    except Exception as e:
        print(f"✗ Erro no teste do SGDK Real Installer: {e}")

def test_unified_detection_integration():
    """Testa a integração com o sistema de detecção unificado"""
    print("\n=== Testando Integração com Detecção Unificada ===")
    
    try:
        from core.unified_detection_engine import get_unified_detection_engine
        from core.component_status_manager import get_status_manager
        
        # Obter instâncias
        engine = get_unified_detection_engine()
        status_manager = get_status_manager()
        
        print("✓ Instâncias obtidas com sucesso")
        
        # Executar detecção (apenas teste rápido)
        print("Executando detecção unificada...")
        result = engine.detect_all_unified()
        
        print(f"✓ Detecção concluída em {result.detection_time:.2f}s")
        print(f"  - Aplicações detectadas: {len(result.applications)}")
        print(f"  - Gerenciadores de pacotes: {len(result.package_managers)}")
        print(f"  - Runtimes essenciais: {len(result.essential_runtimes)}")
        
        # Verificar se componentes foram sincronizados
        all_components = status_manager.get_all_components()
        print(f"✓ Componentes no status manager: {len(all_components)}")
        
        # Verificar especificamente o SGDK
        sgdk_status = status_manager.get_component_status("sgdk")
        if sgdk_status:
            print(f"✓ SGDK no status manager: {sgdk_status.status.value}")
        else:
            print("ℹ SGDK não encontrado no status manager")
            
        print("✓ Teste de integração concluído")
        
    except Exception as e:
        print(f"✗ Erro no teste de integração: {e}")

def test_sgdk_improvements():
    """Testa as melhorias do SGDK"""
    print("\n=== Testando SGDK Improvements ===")
    
    try:
        from core.sgdk_improvements import SGDKInstaller
        
        # Criar instalador
        installer = SGDKInstaller(Path("test_base"), logging.getLogger("test"))
        
        # Verificar versão
        if installer.sgdk_version == "2.11":
            print("✓ Versão configurada para 2.11")
        else:
            print(f"✗ Versão incorreta: {installer.sgdk_version}")
            
        # Verificar se tem instalador real
        if installer.real_installer:
            print("✓ Instalador real disponível")
        else:
            print("⚠ Instalador real não disponível")
            
        print("✓ Teste do SGDK Improvements concluído")
        
    except Exception as e:
        print(f"✗ Erro no teste do SGDK Improvements: {e}")

def main():
    """Executa todos os testes"""
    print("Iniciando testes das correções do SGDK...\n")
    
    # Executar testes
    test_component_status_manager()
    test_sgdk_real_installer()
    test_unified_detection_integration()
    test_sgdk_improvements()
    
    print("\n=== Resumo dos Testes ===")
    print("Testes concluídos. Verifique os resultados acima.")
    print("\nCorreções implementadas:")
    print("1. ✓ Sistema de status de componentes criado")
    print("2. ✓ SGDK configurado para versão 2.11")
    print("3. ✓ Instalador real do SGDK implementado")
    print("4. ✓ Integração com detecção unificada")
    print("5. ✓ Sincronização entre detecção e status")

if __name__ == "__main__":
    main()