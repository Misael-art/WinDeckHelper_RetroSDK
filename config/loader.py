#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de carregamento de componentes modulares YAML
Este módulo gerencia o carregamento dos arquivos YAML de componentes
"""

import os
import sys
import yaml
import glob
import logging
from pathlib import Path
import jsonschema

# Importar filtro de OS
try:
    import sys
    from pathlib import Path
    # Adicionar o diretório utils ao path
    utils_path = Path(__file__).parent.parent / 'utils'
    sys.path.insert(0, str(utils_path))
    from os_component_filter import os_filter
except ImportError as e:
    # Fallback se o filtro não estiver disponível
    print(f"Aviso: Filtro de OS não disponível: {e}")
    class DummyFilter:
        def filter_components_data(self, data):
            return data
    os_filter = DummyFilter()

# Configurar logger
logger = logging.getLogger("yaml_loader")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Schema para validação do YAML
COMPONENT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "description": {"type": "string"},
        "download_url": {"type": "string"},
        "install_method": {"type": "string"},
        "install_args": {"type": ["string", "array"]},
        "extract_path": {"type": "string"},
        "verify_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "path": {"type": "string"},
                    "command": {"type": "string"},
                    "expected_contains": {"type": "string"},
                    "name": {"type": "string"}
                },
                "required": ["type"]
            }
        },
        "dependencies": {
            "type": "array",
            "items": {"type": "string"}
        },
        "post_install_message": {"type": "string"},
        "script_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "command": {"type": "string"},
                    "args": {"type": "array"},
                    "working_dir": {"type": "string"}
                },
                "required": ["type", "command"]
            }
        },
        "add_to_path": {
            "type": "array",
            "items": {"type": "string"}
        },
        "env_vars": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["name", "value"]
            }
        },
        "git_clone_url": {"type": "string"},
        "hash": {"type": "string"},
        "hash_algorithm": {"type": "string"},
        "requires_wsl": {"type": "boolean"}
    },
    "required": ["description", "install_method"]
}

def validate_component(name, component_data):
    """Valida um componente contra o schema"""
    try:
        jsonschema.validate(instance=component_data, schema=COMPONENT_SCHEMA)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Erro de validação no componente '{name}': {e}")
        return False

def load_yaml_file(file_path):
    """Carrega um arquivo YAML"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        logger.error(f"Erro ao analisar YAML em {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {file_path}: {e}")
        return None

def load_all_components():
    """Carrega todos os componentes de todos os arquivos YAML na pasta config/components, runtimes Python e módulos core"""
    components = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    components_dir = os.path.join(script_dir, "components")
    core_dir = os.path.join(os.path.dirname(script_dir), "core")
    
    # Carregar componentes YAML
    if os.path.exists(components_dir):
        yaml_files = glob.glob(os.path.join(components_dir, "*.yaml"))
        if yaml_files:
            logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
            
            for yaml_file in yaml_files:
                logger.info(f"Carregando {yaml_file}")
                file_data = load_yaml_file(yaml_file)
                
                if not file_data:
                    logger.error(f"Falha ao carregar {yaml_file}")
                    continue
                
                valid_components = 0
                for component_name, component_data in file_data.items():
                    if component_name.startswith('_'):
                        continue
                        
                    if validate_component(component_name, component_data):
                        components[component_name] = component_data
                        valid_components += 1
                    else:
                        logger.warning(f"Componente '{component_name}' ignorado devido a erros de validação")
                
                logger.info(f"Carregados {valid_components} componentes válidos de {yaml_file}")
    
    # Carregar runtimes Python
    runtimes_dir = os.path.join(core_dir, "runtimes")
    if os.path.exists(runtimes_dir):
        runtime_files = glob.glob(os.path.join(runtimes_dir, "*_runtime.py"))
        logger.info(f"Encontrados {len(runtime_files)} runtimes Python")
        
        for runtime_file in runtime_files:
            runtime_name = os.path.basename(runtime_file).replace('_runtime.py', '').replace('_', ' ').title()
            components[runtime_name] = {
                'category': 'Runtimes',
                'description': f'Runtime {runtime_name} para desenvolvimento',
                'install_method': 'python_runtime',
                'runtime_file': runtime_file,
                'verify_actions': [{'type': 'file_exists', 'path': runtime_file}]
            }
    
    # Carregar módulos de melhorias de devkits retro
    retro_improvements = [
        'gba_improvements.py', 'gbdk_improvements.py', 'n64_improvements.py',
        'neogeo_improvements.py', 'nes_improvements.py', 'psx_improvements.py',
        'sgdk_improvements.py', 'snes_improvements.py', 'saturn_improvements.py'
    ]
    
    for improvement_file in retro_improvements:
        improvement_path = os.path.join(core_dir, improvement_file)
        if os.path.exists(improvement_path):
            improvement_name = improvement_file.replace('_improvements.py', '').replace('_', ' ').upper()
            components[f'{improvement_name} Devkit'] = {
                'category': 'Desenvolvimento Retro',
                'description': f'Melhorias e ferramentas para desenvolvimento {improvement_name}',
                'install_method': 'python_module',
                'module_file': improvement_path,
                'verify_actions': [{'type': 'file_exists', 'path': improvement_path}]
            }
    
    # Carregar retro devkit base
    retro_devkit_file = os.path.join(core_dir, "retro_devkit_base.py")
    if os.path.exists(retro_devkit_file):
        components['Retro Devkit Manager'] = {
            'category': 'Desenvolvimento Retro',
            'description': 'Gerenciador base para desenvolvimento de jogos retro',
            'install_method': 'python_module',
            'module_file': retro_devkit_file,
            'verify_actions': [{'type': 'file_exists', 'path': retro_devkit_file}]
        }
        logger.info("Carregado Retro Devkit Manager")
    
    # Carregar environment dev integration
    env_dev_file = os.path.join(core_dir, "environment_dev_integration.py")
    if os.path.exists(env_dev_file):
        components['Environment Dev Integration'] = {
            'category': 'Integração',
            'description': 'Integração com ambiente de desenvolvimento',
            'install_method': 'python_module',
            'module_file': env_dev_file,
            'verify_actions': [{'type': 'file_exists', 'path': env_dev_file}]
        }
        logger.info("Carregado Environment Dev Integration")
    
    logger.info(f"Total de {len(components)} componentes carregados")
    
    # Aplicar filtro de OS para remover componentes incompatíveis
    filtered_components = os_filter.filter_components_data(components)
    
    if len(filtered_components) != len(components):
        removed_count = len(components) - len(filtered_components)
        logger.info(f"Filtrados {removed_count} componentes incompatíveis com o SO atual")
    
    return filtered_components

def get_component(name):
    """Obtém um componente específico pelo nome"""
    components = load_all_components()
    return components.get(name)

def get_components_by_category(category):
    """Obtém todos os componentes de uma categoria específica"""
    components = load_all_components()
    return {name: data for name, data in components.items() 
            if data.get('category') == category}

def list_categories():
    """Lista todas as categorias disponíveis"""
    components = load_all_components()
    categories = set(data.get('category', 'Sem categoria') 
                     for data in components.values())
    return sorted(list(categories))

if __name__ == "__main__":
    # Teste simples quando executado diretamente
    logging.basicConfig(level=logging.INFO)
    components = load_all_components()
    print(f"Carregados {len(components)} componentes")
    
    categories = list_categories()
    print(f"Categorias disponíveis: {', '.join(categories)}")
    
    if len(sys.argv) > 1:
        component_name = sys.argv[1]
        component = get_component(component_name)
        if component:
            print(f"\nDetalhes do componente '{component_name}':")
            print(yaml.dump({component_name: component}, default_flow_style=False))
        else:
            print(f"Componente '{component_name}' não encontrado")