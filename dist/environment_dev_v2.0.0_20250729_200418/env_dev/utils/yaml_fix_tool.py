#!/usr/bin/env python3
"""
Ferramenta para corrigir problemas em arquivos YAML do Environment Dev

Esta ferramenta pode ser executada diretamente para corrigir o arquivo components.yaml
ou outros arquivos YAML usados no projeto.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona o diretório pai ao sys.path para permitir importações relativas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # env_dev
project_root = os.path.dirname(parent_dir)  # raiz do projeto

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importa nosso validador YAML
from utils.yaml_validator import validate_yaml, fix_yaml_file, validate_components_schema

def main():
    parser = argparse.ArgumentParser(description='Ferramenta para corrigir arquivos YAML do Environment Dev')
    parser.add_argument('file', nargs='?', default=None, 
                        help='Arquivo YAML a ser corrigido (padrão: components.yaml)')
    parser.add_argument('--output', '-o', default=None,
                        help='Arquivo de saída (padrão: mesmo que entrada)')
    parser.add_argument('--validate-only', '-v', action='store_true',
                        help='Apenas validar, sem corrigir')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Forçar correção mesmo se o arquivo for válido')
    
    args = parser.parse_args()
    
    # Se arquivo não especificado, usa components.yaml do projeto
    if args.file is None:
        yaml_file = os.path.join(parent_dir, 'components.yaml')
    else:
        yaml_file = args.file
    
    # Verifica se o arquivo existe
    if not os.path.exists(yaml_file):
        logger.error(f"Arquivo não encontrado: {yaml_file}")
        return 1
    
    logger.info(f"Processando arquivo YAML: {yaml_file}")
    
    # Valida o arquivo
    valid, error_msg = validate_yaml(yaml_file)
    
    if valid:
        logger.info(f"Arquivo YAML '{yaml_file}' é válido sintaticamente.")
        
        # Verifica schema se for o components.yaml
        if Path(yaml_file).name == 'components.yaml':
            try:
                import yaml
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    components = yaml.safe_load(f)
                    
                schema_errors = validate_components_schema(components)
                if schema_errors:
                    logger.warning("Arquivo tem erros de esquema:")
                    for error in schema_errors:
                        logger.warning(f"- {error}")
                else:
                    logger.info("Arquivo também é válido quanto ao esquema.")
            except Exception as e:
                logger.error(f"Erro ao validar esquema: {e}")
        
        # Se estiver tudo ok e não forçar, sai
        if not args.force:
            logger.info("Nenhuma correção necessária.")
            return 0
        
        logger.info("Forçando correção mesmo com arquivo válido...")
    else:
        logger.error(f"Arquivo YAML '{yaml_file}' é inválido: {error_msg}")
    
    # Se só validar, para aqui
    if args.validate_only:
        return 0 if valid else 1
    
    # Corrige o arquivo
    output_file = args.output or yaml_file
    
    # Cria backup antes de modificar
    if output_file == yaml_file:
        backup_file = f"{yaml_file}.bak"
        try:
            import shutil
            shutil.copy2(yaml_file, backup_file)
            logger.info(f"Backup criado em: {backup_file}")
        except Exception as e:
            logger.warning(f"Não foi possível criar backup: {e}")
    
    # Aplica a correção
    fixed, fix_error = fix_yaml_file(yaml_file, output_file)
    
    if fixed:
        logger.info(f"Arquivo corrigido e salvo em: {output_file}")
        
        # Valida novamente para garantir
        valid_after, error_after = validate_yaml(output_file)
        if valid_after:
            logger.info("Arquivo corrigido é válido!")
            return 0
        else:
            logger.error(f"Arquivo corrigido ainda tem problemas: {error_after}")
            return 1
    else:
        logger.error(f"Não foi possível corrigir o arquivo: {fix_error}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 