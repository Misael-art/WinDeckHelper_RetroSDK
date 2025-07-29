#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para validar arquivos YAML.
Este script verifica a sintaxe e a estrutura dos arquivos YAML de componentes.
"""

import os
import yaml
import logging
import argparse
import jsonschema
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Esquema para validação dos componentes
COMPONENT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "description": {"type": "string"},
        "dependencies": {
            "type": "array",
            "items": {"type": "string"}
        },
        "download_url": {"type": "string"},
        "install_method": {"type": "string"},
        "install_args": {"type": ["string", "array"]},
        "extract_path": {"type": "string"},
        "script_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "command": {"type": "string"},
                    "command_file": {"type": "string"},
                    "args": {"type": "array"}
                }
            }
        },
        "verify_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "path": {"type": "string"},
                    "name": {"type": "string"}
                }
            }
        },
        "post_install_message": {"type": "string"},
        "hash": {"type": "string"},
        "hash_algorithm": {"type": "string"}
    },
    "required": ["category", "description"]
}

def validate_yaml_file(file_path):
    """Valida um arquivo YAML quanto a sua sintaxe e estrutura."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                if not data:
                    logging.error(f"Arquivo YAML vazio: {file_path}")
                    return False, "Arquivo vazio"
                
                # Validar cada componente
                for component_name, component_data in data.items():
                    try:
                        jsonschema.validate(instance=component_data, schema=COMPONENT_SCHEMA)
                    except jsonschema.exceptions.ValidationError as e:
                        logging.error(f"Erro de validação no componente '{component_name}': {e}")
                        return False, f"Erro no componente {component_name}: {e}"
                
                return True, f"Arquivo válido com {len(data)} componentes"
            
            except yaml.YAMLError as e:
                logging.error(f"Erro de sintaxe YAML em {file_path}: {e}")
                return False, f"Erro de sintaxe: {e}"
    
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo {file_path}: {e}")
        return False, f"Erro de leitura: {e}"

def validate_directory(dir_path):
    """Valida todos os arquivos YAML em um diretório."""
    results = {}
    path = Path(dir_path)
    
    if not path.exists() or not path.is_dir():
        logging.error(f"Diretório não encontrado: {dir_path}")
        return results
    
    for yaml_file in path.glob("*.yaml"):
        valid, message = validate_yaml_file(yaml_file)
        results[yaml_file.name] = {"valid": valid, "message": message}
        
        if valid:
            logging.info(f"✓ {yaml_file.name}: {message}")
        else:
            logging.error(f"✗ {yaml_file.name}: {message}")
    
    return results

def main():
    """Função principal para executar a validação."""
    parser = argparse.ArgumentParser(description="Validador de arquivos YAML de componentes")
    parser.add_argument("path", help="Caminho para um arquivo YAML ou diretório")
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        valid, message = validate_yaml_file(path)
        if valid:
            logging.info(f"✓ {path.name}: {message}")
            return 0
        else:
            logging.error(f"✗ {path.name}: {message}")
            return 1
    
    elif path.is_dir():
        results = validate_directory(path)
        invalid_count = sum(1 for result in results.values() if not result["valid"])
        
        if invalid_count == 0:
            logging.info(f"Todos os {len(results)} arquivos YAML são válidos.")
            return 0
        else:
            logging.error(f"{invalid_count} de {len(results)} arquivos YAML são inválidos.")
            return 1
    
    else:
        logging.error(f"Caminho não encontrado: {args.path}")
        return 1

if __name__ == "__main__":
    exit(main()) 