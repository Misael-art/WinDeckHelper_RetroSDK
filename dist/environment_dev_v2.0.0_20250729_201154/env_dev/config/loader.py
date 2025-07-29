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
    """Carrega todos os componentes de todos os arquivos YAML na pasta config/components"""
    components = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    components_dir = os.path.join(script_dir, "components")
    
    if not os.path.exists(components_dir):
        logger.error(f"Diretório de componentes não encontrado: {components_dir}")
        return components
    
    # Listar todos os arquivos YAML no diretório components
    yaml_files = glob.glob(os.path.join(components_dir, "*.yaml"))
    if not yaml_files:
        logger.warning(f"Nenhum arquivo YAML encontrado em {components_dir}")
        return components
    
    logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
    
    # Carregar cada arquivo YAML e validar componentes
    for yaml_file in yaml_files:
        logger.info(f"Carregando {yaml_file}")
        file_data = load_yaml_file(yaml_file)
        
        if not file_data:
            logger.error(f"Falha ao carregar {yaml_file}")
            continue
        
        # Validar e adicionar componentes
        valid_components = 0
        for component_name, component_data in file_data.items():
            if component_name.startswith('_'):  # Ignorar metadados
                continue
                
            if validate_component(component_name, component_data):
                components[component_name] = component_data
                valid_components += 1
            else:
                logger.warning(f"Componente '{component_name}' ignorado devido a erros de validação")
        
        logger.info(f"Carregados {valid_components} componentes válidos de {yaml_file}")
    
    logger.info(f"Total de {len(components)} componentes carregados")
    return components

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