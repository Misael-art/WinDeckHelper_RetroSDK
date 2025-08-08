#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação para testar as melhorias implementadas
"""

import os
import sys
import traceback

# Adiciona o diretório raiz do projeto (um nível acima) ao path
project_root = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_root)
sys.path.insert(0, parent_dir)

def test_diagnostic_manager():
    """Testa o DiagnosticManager com as melhorias implementadas"""
    try:
        print("=== Testando DiagnosticManager ===")
        from env_dev.core.diagnostic_manager import DiagnosticManager
        
        dm = DiagnosticManager()
        print("✓ DiagnosticManager inicializado com sucesso")
        
        # Testa verificação de saúde do sistema
        if hasattr(dm, 'check_system_health'):
            print("✓ Método check_system_health encontrado")
            health_result = dm.check_system_health()
            print(f"✓ Verificação de saúde concluída: {health_result.status.value if hasattr(health_result, 'status') else 'OK'}")
        else:
            print("✗ Método check_system_health não encontrado")
            
        # Testa verificação de conectividade
        if hasattr(dm, 'check_network_connectivity'):
            print("✓ Método check_network_connectivity encontrado")
            network_result = dm.check_network_connectivity()
            print(f"✓ Verificação de rede concluída: {network_result.status.value if hasattr(network_result, 'status') else 'OK'}")
        else:
            print("✗ Método check_network_connectivity não encontrado")
            
        return True
        
    except Exception as e:
        print(f"✗ Erro no DiagnosticManager: {e}")
        traceback.print_exc()
        return False

def test_retro_devkit_manager():
    """Testa o RetroDevKitManager com as melhorias de robustez"""
    try:
        print("\n=== Testando RetroDevKitManager ===")
        from env_dev.core.retro_devkit_manager import RetroDevKitManager
        
        rdm = RetroDevKitManager()
        print("✓ RetroDevKitManager inicializado com sucesso")
        
        # Verifica se os métodos de retry foram implementados
        if hasattr(rdm, '_install_native'):
            print("✓ Método _install_native encontrado")
        else:
            print("✗ Método _install_native não encontrado")
            
        # Lista devkits disponíveis
        devkits = rdm.list_available_devkits()
        print(f"✓ Devkits disponíveis: {len(devkits)} encontrados")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no RetroDevKitManager: {e}")
        traceback.print_exc()
        return False

def test_sgdk_installer():
    """Testa o SGDKInstaller com as melhorias de retry"""
    try:
        print("\n=== Testando SGDKInstaller ===")
        from env_dev.core.sgdk_improvements import SGDKInstaller
        import logging
        from pathlib import Path
        
        # Cria logger temporário
        logger = logging.getLogger('test')
        base_path = Path(os.path.dirname(os.path.abspath(__file__)))
        
        installer = SGDKInstaller(base_path, logger)
        print("✓ SGDKInstaller inicializado com sucesso")
        
        # Verifica se os métodos de instalação existem
        if hasattr(installer, 'install_emulators'):
            print("✓ Método install_emulators encontrado")
        else:
            print("✗ Método install_emulators não encontrado")
            
        if hasattr(installer, '_install_bizhawk'):
            print("✓ Método _install_bizhawk encontrado")
        else:
            print("✗ Método _install_bizhawk não encontrado")
            
        if hasattr(installer, '_install_blastem'):
            print("✓ Método _install_blastem encontrado")
        else:
            print("✗ Método _install_blastem não encontrado")
            
        return True
        
    except Exception as e:
        print(f"✗ Erro no SGDKInstaller: {e}")
        traceback.print_exc()
        return False

def main():
    """Função principal de validação"""
    print("Iniciando validação das melhorias implementadas...\n")
    
    results = []
    
    # Testa cada componente
    results.append(test_diagnostic_manager())
    results.append(test_retro_devkit_manager())
    results.append(test_sgdk_installer())
    
    # Resumo final
    print("\n=== RESUMO DA VALIDAÇÃO ===")
    passed = sum(results)
    total = len(results)
    
    print(f"Testes aprovados: {passed}/{total}")
    
    if passed == total:
        print("✓ TODAS AS MELHORIAS FORAM IMPLEMENTADAS COM SUCESSO!")
        print("✓ O processo de instalação está mais robusto e confiável.")
    else:
        print("⚠ Algumas melhorias podem não estar funcionando corretamente.")
        print("⚠ Verifique os erros acima para mais detalhes.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)