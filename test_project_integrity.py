#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Integridade do Projeto - Environment Dev

Verifica a integridade dos arquivos de configuração, estrutura do projeto
e a capacidade de instalação dos componentes.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

def test_project_structure() -> Dict[str, Any]:
    """Testa a estrutura básica do projeto"""
    print("📁 Testando estrutura do projeto...")
    
    result = {
        'valid': True,
        'missing_dirs': [],
        'missing_files': [],
        'details': []
    }
    
    # Diretórios esperados
    expected_dirs = [
        'core',
        'utils',
        'config',
        'config/components',
        'docs',
        'examples',
        'tools'
    ]
    
    # Arquivos críticos esperados
    expected_files = [
        'main.py',
        'core/component_manager.py',
        'core/installer.py',
        'core/retro_devkit_manager.py',
        'utils/env_checker.py',
        'utils/permission_checker.py',
        'config/components/runtimes.yaml',
        'config/components/dev_tools.yaml',
        'config/components/retro_devkits.yaml'
    ]
    
    # Verificar diretórios
    for dir_path in expected_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            result['missing_dirs'].append(dir_path)
            result['valid'] = False
        else:
            result['details'].append(f"✅ Diretório: {dir_path}")
    
    # Verificar arquivos
    for file_path in expected_files:
        full_path = Path(file_path)
        if not full_path.exists():
            result['missing_files'].append(file_path)
            result['valid'] = False
        else:
            result['details'].append(f"✅ Arquivo: {file_path}")
    
    if result['missing_dirs']:
        result['details'].append(f"❌ Diretórios ausentes: {', '.join(result['missing_dirs'])}")
    
    if result['missing_files']:
        result['details'].append(f"❌ Arquivos ausentes: {', '.join(result['missing_files'])}")
    
    return result

def test_config_files() -> Dict[str, Any]:
    """Testa a validade dos arquivos de configuração"""
    print("⚙️ Testando arquivos de configuração...")
    
    result = {
        'valid': True,
        'config_files': {},
        'details': []
    }
    
    config_files = [
        'config/components/runtimes.yaml',
        'config/components/dev_tools.yaml',
        'config/components/retro_devkits.yaml'
    ]
    
    for config_file in config_files:
        file_result = {
            'exists': False,
            'valid_yaml': False,
            'has_content': False,
            'error': None
        }
        
        try:
            config_path = Path(config_file)
            if config_path.exists():
                file_result['exists'] = True
                result['details'].append(f"✅ Arquivo existe: {config_file}")
                
                # Tentar carregar YAML
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    
                if content:
                    file_result['valid_yaml'] = True
                    file_result['has_content'] = True
                    result['details'].append(f"✅ YAML válido: {config_file}")
                    
                    # Verificações específicas
                    if 'runtimes.yaml' in config_file:
                        if 'Java Runtime Environment' in content and 'Make' in content:
                            result['details'].append("✅ Configurações Java e Make encontradas")
                        else:
                            result['details'].append("⚠️ Configurações Java/Make podem estar ausentes")
                    
                    elif 'retro_devkits.yaml' in config_file:
                        if 'SGDK' in content:
                            sgdk_config = content['SGDK']
                            if 'dependencies' in sgdk_config:
                                deps = sgdk_config['dependencies']
                                if 'Java Runtime Environment' in deps and 'Make' in deps:
                                    result['details'].append("✅ Dependências do SGDK configuradas")
                                else:
                                    result['details'].append("⚠️ Dependências do SGDK incompletas")
                            else:
                                result['details'].append("⚠️ SGDK sem dependências definidas")
                        else:
                            result['details'].append("❌ Configuração do SGDK não encontrada")
                            result['valid'] = False
                else:
                    file_result['valid_yaml'] = True
                    result['details'].append(f"⚠️ Arquivo vazio: {config_file}")
            else:
                result['details'].append(f"❌ Arquivo não existe: {config_file}")
                result['valid'] = False
                
        except yaml.YAMLError as e:
            file_result['error'] = f"YAML inválido: {e}"
            result['details'].append(f"❌ YAML inválido em {config_file}: {e}")
            result['valid'] = False
        except Exception as e:
            file_result['error'] = str(e)
            result['details'].append(f"❌ Erro ao ler {config_file}: {e}")
            result['valid'] = False
        
        result['config_files'][config_file] = file_result
    
    return result

def test_python_modules() -> Dict[str, Any]:
    """Testa se os módulos Python podem ser importados"""
    print("🐍 Testando módulos Python...")
    
    result = {
        'valid': True,
        'modules': {},
        'details': []
    }
    
    # Módulos críticos para testar
    modules_to_test = [
        ('core.component_manager', 'ComponentManager'),
        ('core.installer', 'Installer'),
        ('core.retro_devkit_manager', 'RetroDevKitManager'),
        ('utils.env_checker', 'check_path_for_executable'),
        ('utils.permission_checker', 'is_admin')
    ]
    
    # Adicionar diretório atual ao path
    if str(Path.cwd()) not in sys.path:
        sys.path.insert(0, str(Path.cwd()))
    
    for module_name, class_or_func in modules_to_test:
        module_result = {
            'importable': False,
            'has_target': False,
            'error': None
        }
        
        try:
            # Tentar importar módulo
            module = __import__(module_name, fromlist=[class_or_func])
            module_result['importable'] = True
            result['details'].append(f"✅ Módulo importado: {module_name}")
            
            # Verificar se classe/função existe
            if hasattr(module, class_or_func):
                module_result['has_target'] = True
                result['details'].append(f"✅ {class_or_func} encontrado em {module_name}")
            else:
                result['details'].append(f"❌ {class_or_func} não encontrado em {module_name}")
                result['valid'] = False
                
        except ImportError as e:
            module_result['error'] = f"Erro de importação: {e}"
            result['details'].append(f"❌ Falha ao importar {module_name}: {e}")
            result['valid'] = False
        except Exception as e:
            module_result['error'] = str(e)
            result['details'].append(f"❌ Erro inesperado com {module_name}: {e}")
            result['valid'] = False
        
        result['modules'][module_name] = module_result
    
    return result

def test_dependencies_config() -> Dict[str, Any]:
    """Testa especificamente a configuração das dependências do SGDK"""
    print("🔗 Testando configuração de dependências...")
    
    result = {
        'valid': True,
        'sgdk_deps': [],
        'java_config': {},
        'make_config': {},
        'details': []
    }
    
    try:
        # Carregar configuração do SGDK
        sgdk_config_path = Path('config/components/retro_devkits.yaml')
        if sgdk_config_path.exists():
            with open(sgdk_config_path, 'r', encoding='utf-8') as f:
                sgdk_data = yaml.safe_load(f)
                
            if 'SGDK' in sgdk_data:
                sgdk_info = sgdk_data['SGDK']
                if 'dependencies' in sgdk_info:
                    result['sgdk_deps'] = sgdk_info['dependencies']
                    result['details'].append(f"✅ Dependências do SGDK: {', '.join(result['sgdk_deps'])}")
                    
                    # Verificar se Java e Make estão nas dependências
                    if 'Java Runtime Environment' in result['sgdk_deps']:
                        result['details'].append("✅ Java listado como dependência")
                    else:
                        result['details'].append("❌ Java não listado como dependência")
                        result['valid'] = False
                    
                    if 'Make' in result['sgdk_deps']:
                        result['details'].append("✅ Make listado como dependência")
                    else:
                        result['details'].append("❌ Make não listado como dependência")
                        result['valid'] = False
                else:
                    result['details'].append("❌ SGDK sem dependências definidas")
                    result['valid'] = False
            else:
                result['details'].append("❌ SGDK não encontrado na configuração")
                result['valid'] = False
        
        # Carregar configuração de runtimes
        runtime_config_path = Path('config/components/runtimes.yaml')
        if runtime_config_path.exists():
            with open(runtime_config_path, 'r', encoding='utf-8') as f:
                runtime_data = yaml.safe_load(f)
                
            # Verificar configuração do Java
            if 'Java Runtime Environment' in runtime_data:
                result['java_config'] = runtime_data['Java Runtime Environment']
                java_config = result['java_config']
                
                if 'install_method' in java_config:
                    result['details'].append(f"✅ Java - Método de instalação: {java_config['install_method']}")
                
                if 'verification' in java_config:
                    verification = java_config['verification']
                    if 'commands' in verification:
                        result['details'].append(f"✅ Java - Comandos de verificação: {', '.join(verification['commands'])}")
                    if 'environment_variables' in verification:
                        result['details'].append(f"✅ Java - Variáveis de ambiente: {', '.join(verification['environment_variables'])}")
            
            # Verificar configuração do Make
            if 'Make' in runtime_data:
                result['make_config'] = runtime_data['Make']
                make_config = result['make_config']
                
                if 'install_method' in make_config:
                    result['details'].append(f"✅ Make - Método de instalação: {make_config['install_method']}")
                
                if 'verification' in make_config:
                    verification = make_config['verification']
                    if 'commands' in verification:
                        result['details'].append(f"✅ Make - Comandos de verificação: {', '.join(verification['commands'])}")
        
    except Exception as e:
        result['details'].append(f"❌ Erro ao verificar configurações: {e}")
        result['valid'] = False
    
    return result

def main():
    """Função principal do teste de integridade"""
    print("🔍 TESTE DE INTEGRIDADE DO PROJETO")
    print("=" * 45)
    print("📋 Verificando estrutura, configurações e módulos...")
    print("")
    
    # Executar todos os testes
    tests = [
        ("Estrutura do Projeto", test_project_structure),
        ("Arquivos de Configuração", test_config_files),
        ("Módulos Python", test_python_modules),
        ("Configuração de Dependências", test_dependencies_config)
    ]
    
    results = {}
    all_valid = True
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        print("-" * (len(test_name) + 5))
        
        try:
            test_result = test_func()
            results[test_name] = test_result
            
            # Mostrar detalhes
            for detail in test_result['details']:
                print(f"   {detail}")
            
            if not test_result['valid']:
                all_valid = False
                print(f"   ❌ {test_name}: FALHOU")
            else:
                print(f"   ✅ {test_name}: OK")
                
        except Exception as e:
            print(f"   ❌ Erro no teste {test_name}: {e}")
            results[test_name] = {'valid': False, 'error': str(e)}
            all_valid = False
    
    # Resumo final
    print("\n" + "=" * 45)
    print("📋 RESUMO DA INTEGRIDADE:")
    print("-" * 25)
    
    for test_name, test_result in results.items():
        status = "✅ OK" if test_result.get('valid', False) else "❌ FALHOU"
        print(f"   {status} {test_name}")
    
    print("")
    if all_valid:
        print("🎉 PROJETO ÍNTEGRO E PRONTO PARA USO!")
        print("")
        print("✅ Estrutura completa")
        print("✅ Configurações válidas")
        print("✅ Módulos funcionais")
        print("✅ Dependências do SGDK configuradas")
        print("")
        print("🚀 Próximo passo: Executar instalação dos componentes")
        print("   python main.py --install sgdk")
    else:
        print("⚠️ PROBLEMAS DE INTEGRIDADE DETECTADOS")
        print("")
        print("🔧 Ações recomendadas:")
        print("   1. Verificar se todos os arquivos estão presentes")
        print("   2. Validar sintaxe dos arquivos YAML")
        print("   3. Reinstalar dependências Python se necessário")
        print("   4. Verificar permissões de arquivo")
    
    # Salvar resultados
    with open('project_integrity_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("")
    print("📄 Relatório salvo: project_integrity_results.json")
    
    return all_valid

if __name__ == '__main__':
    success = main()
    print("")
    input("Pressione Enter para sair...")
    sys.exit(0 if success else 1)