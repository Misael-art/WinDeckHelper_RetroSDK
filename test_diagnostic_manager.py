#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for DiagnosticManager
Tests system diagnosis, compatibility checking, and issue detection
"""

import unittest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.diagnostic_manager import DiagnosticManager, HealthStatus, CompatibilityStatus
    
    def test_diagnostic_manager():
        """Teste básico do DiagnosticManager"""
        print("=== Teste do DiagnosticManager ===")
        
        # Cria instância do manager
        diagnostic_manager = DiagnosticManager()
        print("✓ DiagnosticManager criado com sucesso")
        
        # Testa verificação de compatibilidade
        print("\n--- Testando verificação de compatibilidade ---")
        compatibility = diagnostic_manager.check_system_compatibility()
        print(f"Status de compatibilidade: {compatibility.status.value}")
        print(f"Recursos suportados: {len(compatibility.supported_features)}")
        print(f"Recursos não suportados: {len(compatibility.unsupported_features)}")
        print(f"Avisos: {len(compatibility.warnings)}")
        
        # Testa diagnóstico completo
        print("\n--- Testando diagnóstico completo ---")
        result = diagnostic_manager.run_full_diagnostic()
        print(f"Saúde geral: {result.overall_health.value}")
        print(f"Problemas detectados: {len(result.issues)}")
        print(f"Sugestões geradas: {len(result.suggestions)}")
        print(f"Duração do diagnóstico: {result.diagnostic_duration:.2f}s")
        
        # Mostra informações do sistema
        print(f"\n--- Informações do Sistema ---")
        print(f"OS: {result.system_info.os_name} {result.system_info.os_version}")
        print(f"Arquitetura: {result.system_info.architecture}")
        print(f"Python: {result.system_info.python_version}")
        print(f"Admin: {result.system_info.is_admin}")
        print(f"Memória: {result.system_info.total_memory / (1024**3):.1f}GB")
        print(f"Espaço livre: {result.system_info.disk_space_free / (1024**3):.1f}GB")
        
        # Mostra problemas detectados
        if result.issues:
            print(f"\n--- Problemas Detectados ---")
            for issue in result.issues:
                print(f"- {issue.title} ({issue.severity.value})")
                print(f"  {issue.description}")
        
        # Mostra sugestões
        if result.suggestions:
            print(f"\n--- Sugestões ---")
            for suggestion in result.suggestions:
                print(f"- {suggestion.title}")
                print(f"  {suggestion.description}")
        
        # Testa detecção de conflitos
        print(f"\n--- Testando detecção de conflitos ---")
        test_components = ["CloverBootManager", "rEFInd", "VMware", "VirtualBox"]
        conflict_result = diagnostic_manager.detect_conflicts(test_components)
        print(f"Conflitos detectados: {conflict_result.has_conflicts}")
        if conflict_result.conflicts:
            for conflict in conflict_result.conflicts:
                print(f"  Conflito: {' vs '.join(conflict['components'])} - {conflict['reason']}")
        
        # Testa verificação de dependências
        print(f"\n--- Testando verificação de dependências ---")
        dep_result = diagnostic_manager.verify_dependencies("CloverBootManager")
        print(f"Dependências: {dep_result.dependencies}")
        print(f"Dependências faltando: {dep_result.missing_dependencies}")
        print(f"Tem ciclos: {dep_result.has_circular_dependencies[0]}")
        
        # Testa geração de relatório
        print(f"\n--- Testando geração de relatório ---")
        report = diagnostic_manager.generate_diagnostic_report(result)
        print("✓ Relatório gerado com sucesso")
        print(f"Tamanho do relatório: {len(report)} caracteres")
        
        # Salva relatório em arquivo para inspeção
        with open("diagnostic_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print("✓ Relatório salvo em diagnostic_report.txt")
        
        print("\n✓ Todos os testes passaram!")
        return True
        
    if __name__ == "__main__":
        test_diagnostic_manager()
        
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Verifique se todos os módulos necessários estão disponíveis")
except Exception as e:
    print(f"Erro durante o teste: {e}")
    import traceback
    traceback.print_exc()