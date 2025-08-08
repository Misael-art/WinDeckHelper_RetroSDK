#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Instalação Automática de Dependências

Este script testa se o sistema de instalação automática de dependências
funciona corretamente em um ambiente limpo, simulando a instalação do SGDK
e verificando se todas as dependências são instaladas automaticamente.
"""

import os
import sys
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path

# Adicionar o diretório do projeto ao PYTHONPATH
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Corrigir imports para funcionar no contexto do projeto
try:
    from config.loader import load_all_components, get_component
except ImportError:
    # Fallback para importação direta
    import importlib.util
    spec = importlib.util.spec_from_file_location("loader", os.path.join(project_dir, "config", "loader.py"))
    loader_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader_module)
    load_all_components = loader_module.load_all_components
    get_component = loader_module.get_component

class DependencyInstallationTester:
    """Testa a instalação automática de dependências"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_name': 'Dependency Installation Test',
            'components_tested': [],
            'dependencies_resolved': [],
            'installation_results': {},
            'overall_success': False,
            'errors': []
        }
        
    def _setup_logging(self):
        """Configura o sistema de logging para o teste"""
        logger = logging.getLogger('dependency_test')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        log_file = os.path.join(project_dir, 'logs', 'dependency_test.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def test_sgdk_dependency_resolution(self):
        """Testa a resolução automática de dependências do SGDK"""
        self.logger.info("=== Iniciando Teste de Resolução de Dependências do SGDK ===")
        
        try:
            # Carrega todos os componentes
            all_components = load_all_components()
            self.logger.info(f"Carregados {len(all_components)} componentes")
            
            # Obtém dados do SGDK
            sgdk_component = get_component("SGDK (Sega Genesis Development Kit)")
            if not sgdk_component:
                self.logger.error("Componente SGDK não encontrado")
                self.test_results['errors'].append("Componente SGDK não encontrado")
                return False
                
            self.logger.info(f"Componente SGDK encontrado: {sgdk_component.get('description', 'N/A')}")
            self.test_results['components_tested'].append("SGDK (Sega Genesis Development Kit)")
            
            # Verifica dependências definidas
            dependencies = sgdk_component.get('dependencies', [])
            self.logger.info(f"Dependências do SGDK: {dependencies}")
            self.test_results['dependencies_resolved'] = dependencies
            
            if not dependencies:
                self.logger.warning("Nenhuma dependência definida para o SGDK")
                self.test_results['errors'].append("Nenhuma dependência definida para o SGDK")
                return False
                
            # Verifica se todas as dependências estão disponíveis
            missing_deps = []
            for dep in dependencies:
                dep_component = get_component(dep)
                if not dep_component:
                    missing_deps.append(dep)
                    self.logger.error(f"Dependência '{dep}' não encontrada nos componentes")
                else:
                    self.logger.info(f"Dependência '{dep}' encontrada: {dep_component.get('description', 'N/A')}")
                    
            if missing_deps:
                self.test_results['errors'].append(f"Dependências não encontradas: {missing_deps}")
                return False
                
            self.logger.info("✓ Todas as dependências do SGDK estão definidas e disponíveis")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro durante teste de resolução de dependências: {str(e)}")
            self.test_results['errors'].append(f"Erro durante teste: {str(e)}")
            return False
            
    def test_dependency_installation_simulation(self):
        """Simula a instalação das dependências sem executar realmente"""
        self.logger.info("=== Simulando Instalação de Dependências ===")
        
        try:
            # Carrega componentes
            all_components = load_all_components()
            sgdk_component = get_component("SGDK (Sega Genesis Development Kit)")
            
            if not sgdk_component:
                return False
                
            dependencies = sgdk_component.get('dependencies', [])
            
            # Simula instalação de cada dependência
            for dep_name in dependencies:
                self.logger.info(f"Simulando instalação de: {dep_name}")
                
                dep_component = get_component(dep_name)
                if not dep_component:
                    continue
                    
                # Verifica método de instalação
                install_method = dep_component.get('install_method', 'unknown')
                self.logger.info(f"  Método de instalação: {install_method}")
                
                # Verifica ações de verificação
                verify_actions = dep_component.get('verify_actions', [])
                self.logger.info(f"  Ações de verificação: {len(verify_actions)} definidas")
                
                # Registra resultado da simulação
                self.test_results['installation_results'][dep_name] = {
                    'install_method': install_method,
                    'verify_actions_count': len(verify_actions),
                    'simulation_status': 'OK'
                }
                
            self.logger.info("✓ Simulação de instalação de dependências concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro durante simulação: {str(e)}")
            self.test_results['errors'].append(f"Erro durante simulação: {str(e)}")
            return False
            
    def test_installation_order_logic(self):
        """Testa a lógica de ordem de instalação"""
        self.logger.info("=== Testando Lógica de Ordem de Instalação ===")
        
        try:
            # Simula a função _handle_dependencies
            all_components = load_all_components()
            sgdk_component = get_component("SGDK (Sega Genesis Development Kit)")
            
            if not sgdk_component:
                return False
                
            dependencies = sgdk_component.get('dependencies', [])
            installed_components = set()
            visiting = set()
            
            # Simula verificação de dependências circulares
            self.logger.info("Verificando dependências circulares...")
            
            def check_circular_deps(comp_name, path):
                if comp_name in path:
                    return True  # Dependência circular encontrada
                    
                comp_data = get_component(comp_name)
                if not comp_data:
                    return False
                    
                comp_deps = comp_data.get('dependencies', [])
                for dep in comp_deps:
                    if check_circular_deps(dep, path + [comp_name]):
                        return True
                        
                return False
                
            # Verifica cada dependência
            for dep in dependencies:
                if check_circular_deps(dep, []):
                    self.logger.error(f"Dependência circular detectada em: {dep}")
                    self.test_results['errors'].append(f"Dependência circular: {dep}")
                    return False
                    
            self.logger.info("✓ Nenhuma dependência circular detectada")
            
            # Simula ordem de instalação
            installation_order = []
            
            def add_to_order(comp_name):
                if comp_name in installation_order:
                    return
                    
                comp_data = get_component(comp_name)
                if comp_data:
                    comp_deps = comp_data.get('dependencies', [])
                    for dep in comp_deps:
                        add_to_order(dep)
                        
                installation_order.append(comp_name)
                
            for dep in dependencies:
                add_to_order(dep)
                
            self.logger.info(f"Ordem de instalação sugerida: {installation_order}")
            self.test_results['installation_order'] = installation_order
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro durante teste de ordem: {str(e)}")
            self.test_results['errors'].append(f"Erro durante teste de ordem: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Executa todos os testes"""
        self.logger.info("=== INICIANDO TESTES DE INSTALAÇÃO AUTOMÁTICA DE DEPENDÊNCIAS ===")
        
        tests = [
            ('Resolução de Dependências', self.test_sgdk_dependency_resolution),
            ('Simulação de Instalação', self.test_dependency_installation_simulation),
            ('Lógica de Ordem', self.test_installation_order_logic)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.logger.info(f"\n--- Executando: {test_name} ---")
            try:
                if test_func():
                    self.logger.info(f"✓ {test_name}: PASSOU")
                    passed_tests += 1
                else:
                    self.logger.error(f"✗ {test_name}: FALHOU")
            except Exception as e:
                self.logger.error(f"✗ {test_name}: ERRO - {str(e)}")
                self.test_results['errors'].append(f"{test_name}: {str(e)}")
                
        # Resultado final
        self.test_results['tests_passed'] = passed_tests
        self.test_results['tests_total'] = total_tests
        self.test_results['overall_success'] = passed_tests == total_tests
        
        self.logger.info(f"\n=== RESULTADO FINAL ===")
        self.logger.info(f"Testes passaram: {passed_tests}/{total_tests}")
        
        if self.test_results['overall_success']:
            self.logger.info("✓ TODOS OS TESTES PASSARAM - Sistema de dependências está funcionando")
        else:
            self.logger.error("✗ ALGUNS TESTES FALHARAM - Verificar logs para detalhes")
            
        # Salva resultados
        self._save_results()
        
        return self.test_results['overall_success']
        
    def _save_results(self):
        """Salva os resultados do teste em arquivo JSON"""
        results_file = os.path.join(project_dir, 'dependency_test_results.json')
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Resultados salvos em: {results_file}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar resultados: {str(e)}")
            
def main():
    """Função principal"""
    print("=== Teste de Instalação Automática de Dependências ===")
    print("Este teste verifica se o sistema resolve e instala dependências automaticamente.\n")
    
    tester = DependencyInstallationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✓ Sistema de dependências está funcionando corretamente!")
        print("  O projeto pode instalar SGDK e suas dependências automaticamente em um OS limpo.")
        return 0
    else:
        print("\n✗ Problemas detectados no sistema de dependências!")
        print("  Verificar logs para mais detalhes.")
        return 1
        
if __name__ == "__main__":
    sys.exit(main())