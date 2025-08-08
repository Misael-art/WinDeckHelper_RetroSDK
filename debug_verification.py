#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.installer import Installer
import logging

# Configurar logging para ver mensagens de debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_specific_component():
    """Testa um componente específico com tipo de verificação desconhecido"""
    
    # Componente de teste com tipo 'file' desconhecido
    test_component = {
        'name': 'Test Component',
        'category': 'Test',
        'verify_actions': [
            {
                'type': 'file_exists',
                'path': 'C:\\NonExistent\\file.txt'
            }
        ]
    }
    
    installer = Installer()
    
    print("=== TESTE DE COMPONENTE COM TIPO DESCONHECIDO ===")
    print(f"Testando componente: {test_component['name']}")
    print(f"Tipo de verificação: {test_component['verify_actions'][0]['type']}")
    
    # Executar verificação usando a função estática
    from core.installer import _verify_installation
    result = _verify_installation(
        component_name=test_component['name'],
        component_data=test_component
    )
    
    print(f"\nResultado da verificação: {result}")
    print(f"Componente deveria ser detectado como: NÃO INSTALADO")
    print(f"Resultado atual: {'INSTALADO' if result else 'NÃO INSTALADO'}")
    
    if result:
        print("❌ FALSO POSITIVO DETECTADO!")
        return False
    else:
        print("✅ Verificação correta!")
        return True

if __name__ == "__main__":
    success = test_specific_component()
    sys.exit(0 if success else 1)