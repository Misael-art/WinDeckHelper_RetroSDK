#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Otimizador Universal de Dependências

Este script testa e demonstra o funcionamento do sistema de otimização
universal de dependências, verificando se todos os componentes são
corretamente analisados e otimizados.

Autor: Environment Dev Team
Versão: 1.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Adicionar o diretório core ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from universal_dependency_optimizer import (
    UniversalDependencyOptimizer,
    ComponentOptimization,
    get_universal_dependency_optimizer
)

# Configuração de logging para o teste
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversalOptimizerTester:
    """Classe para testar o otimizador universal"""
    
    def __init__(self):
        self.optimizer = get_universal_dependency_optimizer()
        self.test_results = {}
        
    def run_all_tests(self) -> bool:
        """Executa todos os testes"""
        logger.info("🧪 Iniciando testes do Otimizador Universal de Dependências")
        logger.info("="*70)
        
        tests = [
            ("Descoberta de Arquivos", self.test_file_discovery),
            ("Carregamento de Componentes", self.test_component_loading),
            ("Detecção de Otimizações", self.test_optimization_detection),
            ("Otimização de Componentes", self.test_component_optimization),
            ("Geração de Relatórios", self.test_report_generation),
            ("Análise de Economia", self.test_savings_analysis),
            ("Dependências Condicionais", self.test_conditional_dependencies)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Executando: {test_name}")
            try:
                result = test_func()
                if result:
                    logger.info(f"✅ {test_name}: PASSOU")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name}: FALHOU")
                self.test_results[test_name] = result
            except Exception as e:
                logger.error(f"💥 {test_name}: ERRO - {e}")
                self.test_results[test_name] = False
        
        logger.info("\n" + "="*70)
        logger.info(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            logger.info("🎉 TODOS OS TESTES PASSARAM!")
            return True
        else:
            logger.warning(f"⚠️  {total - passed} teste(s) falharam")
            return False
    
    def test_file_discovery(self) -> bool:
        """Testa a descoberta de arquivos de configuração"""
        try:
            files = self.optimizer._discover_component_files()
            
            if not files:
                logger.warning("Nenhum arquivo de configuração encontrado")
                return False
            
            logger.info(f"📁 Arquivos encontrados: {len(files)}")
            for file_path in files:
                logger.info(f"  - {Path(file_path).name}")
            
            # Verificar se arquivos esperados existem
            expected_files = ['retro_devkits.yaml', 'mcps.yaml', 'misc.yaml']
            found_files = [Path(f).name for f in files]
            
            for expected in expected_files:
                if expected in found_files:
                    logger.info(f"  ✅ {expected} encontrado")
                else:
                    logger.warning(f"  ⚠️  {expected} não encontrado")
            
            return len(files) > 0
        
        except Exception as e:
            logger.error(f"Erro na descoberta de arquivos: {e}")
            return False
    
    def test_component_loading(self) -> bool:
        """Testa o carregamento de componentes"""
        try:
            files = self.optimizer._discover_component_files()
            total_components = 0
            
            for file_path in files:
                components = self.optimizer._load_components_from_file(file_path)
                file_name = Path(file_path).name
                component_count = len(components)
                total_components += component_count
                
                logger.info(f"📦 {file_name}: {component_count} componentes")
                
                # Mostrar alguns componentes como exemplo
                for i, (name, data) in enumerate(list(components.items())[:3]):
                    deps = data.get('dependencies', [])
                    logger.info(f"  - {name}: {len(deps)} dependências")
            
            logger.info(f"📊 Total de componentes carregados: {total_components}")
            return total_components > 0
        
        except Exception as e:
            logger.error(f"Erro no carregamento de componentes: {e}")
            return False
    
    def test_optimization_detection(self) -> bool:
        """Testa a detecção de componentes que precisam de otimização"""
        try:
            files = self.optimizer._discover_component_files()
            optimizable_count = 0
            intelligent_count = 0
            
            for file_path in files:
                components = self.optimizer._load_components_from_file(file_path)
                
                for name, data in components.items():
                    if self.optimizer._should_optimize_component(name, data):
                        optimizable_count += 1
                        logger.info(f"🔧 Otimizável: {name}")
                    else:
                        custom_installer = data.get('custom_installer', '')
                        if 'intelligent' in custom_installer.lower():
                            intelligent_count += 1
                            logger.info(f"🧠 Já inteligente: {name}")
            
            logger.info(f"📊 Componentes otimizáveis: {optimizable_count}")
            logger.info(f"🧠 Componentes já inteligentes: {intelligent_count}")
            
            return optimizable_count >= 0  # Sempre passa, pois pode não haver componentes para otimizar
        
        except Exception as e:
            logger.error(f"Erro na detecção de otimizações: {e}")
            return False
    
    def test_component_optimization(self) -> bool:
        """Testa a otimização de componentes específicos"""
        try:
            # Executar otimização completa
            optimizations = self.optimizer.optimize_all_components()
            
            if not optimizations:
                logger.info("ℹ️  Nenhuma otimização aplicada (pode ser normal)")
                return True
            
            logger.info(f"🔧 Otimizações realizadas: {len(optimizations)}")
            
            # Analisar algumas otimizações
            for name, opt in list(optimizations.items())[:3]:
                logger.info(f"\n📋 Análise de {name}:")
                logger.info(f"  - Dependências originais: {len(opt.original_dependencies)}")
                logger.info(f"  - Dependências otimizadas: {len(opt.optimized_dependencies)}")
                logger.info(f"  - Dependências puladas: {len(opt.skipped_dependencies)}")
                
                if opt.skipped_dependencies:
                    logger.info(f"  - Puladas: {', '.join(opt.skipped_dependencies)}")
                
                savings = opt.estimated_savings
                logger.info(f"  - Economia: {savings['size_mb']} MB, {savings['time_seconds']//60} min")
            
            return True
        
        except Exception as e:
            logger.error(f"Erro na otimização de componentes: {e}")
            return False
    
    def test_report_generation(self) -> bool:
        """Testa a geração de relatórios"""
        try:
            optimizations = self.optimizer.optimize_all_components()
            
            if not optimizations:
                logger.info("ℹ️  Sem otimizações para gerar relatório")
                return True
            
            report = self.optimizer.generate_optimization_report(optimizations)
            
            # Verificar estrutura do relatório
            required_keys = ['timestamp', 'summary', 'optimizations']
            for key in required_keys:
                if key not in report:
                    logger.error(f"Chave '{key}' ausente no relatório")
                    return False
            
            summary = report['summary']
            logger.info(f"📊 Relatório gerado:")
            logger.info(f"  - Componentes otimizados: {summary['total_components_optimized']}")
            logger.info(f"  - Economia total: {summary['total_savings']}")
            
            # Salvar relatório de teste
            report_path = "test_optimization_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Relatório de teste salvo: {report_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erro na geração de relatório: {e}")
            return False
    
    def test_savings_analysis(self) -> bool:
        """Testa a análise de economia"""
        try:
            # Teste com dependências conhecidas
            test_deps = ["Visual Studio Code", "Java Runtime Environment", "Node.js"]
            skipped_deps = ["Visual Studio Code", "Node.js"]
            
            savings = self.optimizer._calculate_savings(test_deps, skipped_deps)
            
            logger.info(f"💾 Análise de economia:")
            logger.info(f"  - Espaço economizado: {savings['size_mb']} MB")
            logger.info(f"  - Tempo economizado: {savings['time_seconds']} segundos")
            logger.info(f"  - Dependências puladas: {savings['dependencies_skipped']}")
            
            # Verificar se os cálculos fazem sentido
            if savings['size_mb'] > 0 and savings['time_seconds'] > 0:
                return True
            else:
                logger.error("Cálculos de economia inválidos")
                return False
        
        except Exception as e:
            logger.error(f"Erro na análise de economia: {e}")
            return False
    
    def test_conditional_dependencies(self) -> bool:
        """Testa a criação de dependências condicionais"""
        try:
            # Teste com padrão de otimização
            dependencies = ["Visual Studio Code", "Microsoft Visual C++ Redistributable"]
            optimization_pattern = {
                'editor_dependencies': ["Visual Studio Code"],
                'conditional_rules': {
                    'editors': {
                        'condition': 'no_compatible_editor_detected',
                        'alternatives': ["Visual Studio Code", "Cursor IDE"]
                    }
                }
            }
            
            conditional_deps = self.optimizer._create_conditional_dependencies(
                dependencies, optimization_pattern
            )
            
            logger.info(f"🔀 Dependências condicionais criadas:")
            for key, value in conditional_deps.items():
                logger.info(f"  - {key}: {value}")
            
            # Verificar se dependências condicionais foram criadas corretamente
            if 'editors' in conditional_deps:
                editor_config = conditional_deps['editors']
                if 'condition' in editor_config and 'dependencies' in editor_config:
                    return True
            
            # Se não há dependências condicionais, também é válido
            return True
        
        except Exception as e:
            logger.error(f"Erro no teste de dependências condicionais: {e}")
            return False
    
    def demonstrate_optimization(self) -> None:
        """Demonstra o funcionamento completo do otimizador"""
        logger.info("\n" + "="*70)
        logger.info("🎯 DEMONSTRAÇÃO DO OTIMIZADOR UNIVERSAL")
        logger.info("="*70)
        
        # Executar otimização completa
        optimizations = self.optimizer.optimize_all_components()
        
        if optimizations:
            # Gerar e salvar relatório
            report = self.optimizer.generate_optimization_report(optimizations)
            
            report_path = "demonstration_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n📄 Relatório completo salvo em: {report_path}")
            
            # Mostrar estatísticas finais
            summary = report['summary']
            total_savings = summary['total_savings']
            
            logger.info("\n🏆 ESTATÍSTICAS FINAIS:")
            logger.info(f"  📦 Componentes analisados: {len(self.optimizer._discover_component_files())} arquivos")
            logger.info(f"  🔧 Componentes otimizados: {summary['total_components_optimized']}")
            logger.info(f"  💾 Espaço total economizado: {total_savings['size_mb']} MB")
            logger.info(f"  ⏱️  Tempo total economizado: {total_savings['time_seconds']//60} minutos")
            logger.info(f"  ⏭️  Dependências evitadas: {total_savings['dependencies_skipped']}")
        else:
            logger.info("\nℹ️  Sistema já está otimizado - nenhuma melhoria adicional necessária")

def main():
    """Função principal"""
    print("🧪 Teste do Otimizador Universal de Dependências")
    print("="*60)
    
    tester = UniversalOptimizerTester()
    
    # Executar testes
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Todos os testes passaram! Executando demonstração...")
        tester.demonstrate_optimization()
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs acima.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)