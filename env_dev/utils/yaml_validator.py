#!/usr/bin/env python3
"""
Módulo de validação de YAML para Environment Dev

Este módulo fornece funções para validar arquivos YAML usados no Environment Dev,
particularmente o arquivo de componentes (components.yaml).
"""

import os
import yaml
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

# Configuração de logging
logger = logging.getLogger(__name__)

def escape_yaml_special_chars(content: str) -> str:
    """
    Escapa os caracteres especiais do YAML que estão dentro de comandos batch/PowerShell.
    
    Args:
        content: O conteúdo do arquivo YAML a ser processado
        
    Returns:
        O conteúdo YAML com caracteres especiais escapados corretamente
    """
    # Padrão para encontrar blocos de comando (script_actions)
    script_block_pattern = r'(command: \|[\s\S]*?)(?=\n\s*[a-zA-Z_]|$)'
    
    def escape_block(match):
        block = match.group(1)
        # Escapar % como '%%' dentro de strings em comandos
        # Isso é específico para script_actions que contêm comandos batch
        if '%' in block:
            # Não escape % que já estão em variáveis YAML
            block = re.sub(r'(?<!\$\{env:)%(?!.*\})', '%%', block)
        return block
    
    # Aplicar a função para escapar os blocos
    escaped_content = re.sub(script_block_pattern, escape_block, content)
    return escaped_content

def validate_yaml(yaml_file: str) -> Tuple[bool, Optional[str]]:
    """
    Valida um arquivo YAML para garantir que ele está sintaticamente correto.
    
    Args:
        yaml_file: Caminho para o arquivo YAML a ser validado
        
    Returns:
        Tupla contendo (sucesso, mensagem_erro)
    """
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Tenta fazer o parse do YAML
        yaml.safe_load(content)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erro ao validar arquivo YAML: {str(e)}"

def validate_components_schema(components: Dict[str, Any]) -> List[str]:
    """
    Valida o esquema do dicionário de componentes.
    
    Args:
        components: Dicionário de componentes carregado do YAML
        
    Returns:
        Lista de mensagens de erro. Lista vazia significa que não há erros.
    """
    errors = []
    
    # Valida se o components é um dicionário não vazio
    if not isinstance(components, dict):
        errors.append("O arquivo de componentes não é um dicionário válido")
        return errors
    
    if not components:
        errors.append("O arquivo de componentes está vazio")
        return errors
    
    # Valida cada componente
    for component_name, component_data in components.items():
        # Pula entradas comentadas
        if component_name.startswith('#'):
            continue
            
        # Verifica se o componente é um dicionário
        if not isinstance(component_data, dict):
            errors.append(f"Componente '{component_name}' não é um dicionário válido")
            continue
        
        # Verifica campos obrigatórios
        required_fields = ['category', 'description']
        for field in required_fields:
            if field not in component_data:
                errors.append(f"Componente '{component_name}' não tem o campo obrigatório '{field}'")
        
        # Valida método de instalação
        if 'install_method' in component_data:
            method = component_data['install_method']
            valid_methods = ['exe', 'msi', 'pip', 'npm', 'archive', 'script', 'vcpkg']
            if method not in valid_methods:
                errors.append(f"Componente '{component_name}' tem método de instalação inválido: '{method}'")
                
        # Valida URL de download quando necessário
        if 'install_method' in component_data and component_data['install_method'] in ['exe', 'msi', 'archive']:
            if 'download_url' not in component_data and 'git_clone_url' not in component_data:
                errors.append(f"Componente '{component_name}' requer URL de download ou git_clone_url")
                
        # Valida script_actions
        if 'script_actions' in component_data:
            actions = component_data['script_actions']
            if not isinstance(actions, list):
                errors.append(f"Componente '{component_name}' tem script_actions que não é uma lista")
                continue
                
            for idx, action in enumerate(actions):
                if not isinstance(action, dict):
                    errors.append(f"Componente '{component_name}' tem uma ação de script inválida no índice {idx}")
                    continue
                    
                if 'type' not in action:
                    errors.append(f"Componente '{component_name}' tem uma ação de script sem 'type' no índice {idx}")
                
                if 'command' not in action and action.get('type') not in ['copy_file', 'delete_file']:
                    errors.append(f"Componente '{component_name}' tem uma ação de script sem 'command' no índice {idx}")
    
    return errors

def fix_yaml_file(yaml_file: str, output_file: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Tenta corrigir problemas comuns em um arquivo YAML.
    
    Args:
        yaml_file: Caminho para o arquivo YAML a ser corrigido
        output_file: Caminho para salvar o arquivo corrigido. Se None, sobrescreve o original.
        
    Returns:
        Tupla contendo (sucesso, mensagem_erro)
    """
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Aplica as correções
        corrected_content = escape_yaml_special_chars(content)
        
        # Se não for informado um arquivo de saída, usa o original
        if output_file is None:
            output_file = yaml_file
        
        # Verifica se o conteúdo corrigido é válido
        try:
            yaml.safe_load(corrected_content)
        except yaml.YAMLError as e:
            return False, f"O conteúdo corrigido ainda possui erros de YAML: {str(e)}"
        
        # Salva o conteúdo corrigido
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(corrected_content)
            
        return True, None
    except Exception as e:
        return False, f"Erro ao corrigir arquivo YAML: {str(e)}"

def validate_and_fix_components_file(components_file: str) -> bool:
    """
    Valida e, se necessário, corrige o arquivo de componentes.
    
    Args:
        components_file: Caminho para o arquivo de componentes
        
    Returns:
        True se o arquivo está válido ou foi corrigido com sucesso, False caso contrário
    """
    # Primeiro, tenta validar o arquivo
    valid, error_msg = validate_yaml(components_file)
    
    if valid:
        logger.info(f"Arquivo de componentes '{components_file}' é válido.")
        
        # Carrega para validar o esquema
        try:
            with open(components_file, 'r', encoding='utf-8') as f:
                components = yaml.safe_load(f)
                
            schema_errors = validate_components_schema(components)
            if schema_errors:
                for error in schema_errors:
                    logger.warning(f"Erro de esquema: {error}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Erro ao validar esquema: {str(e)}")
            return False
    else:
        logger.error(f"Arquivo de componentes '{components_file}' é inválido: {error_msg}")
        
        # Tenta corrigir o arquivo
        logger.info(f"Tentando corrigir arquivo de componentes '{components_file}'...")
        
        # Cria um backup do arquivo original
        backup_file = f"{components_file}.bak"
        try:
            import shutil
            shutil.copy2(components_file, backup_file)
            logger.info(f"Backup do arquivo original criado em '{backup_file}'")
        except Exception as e:
            logger.warning(f"Não foi possível criar backup: {str(e)}")
        
        # Tenta corrigir
        fixed, fix_error = fix_yaml_file(components_file)
        if fixed:
            logger.info(f"Arquivo de componentes '{components_file}' corrigido com sucesso.")
            return True
        else:
            logger.error(f"Não foi possível corrigir o arquivo: {fix_error}")
            
            # Tenta restaurar o backup
            try:
                if os.path.exists(backup_file):
                    shutil.copy2(backup_file, components_file)
                    logger.info(f"Arquivo original restaurado do backup.")
            except Exception as e:
                logger.error(f"Erro ao restaurar backup: {str(e)}")
                
            return False

if __name__ == "__main__":
    import sys
    
    # Configura log básico para teste
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 2:
        print("Uso: python yaml_validator.py <arquivo_yaml> [arquivo_saida]")
        sys.exit(1)
        
    yaml_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(yaml_file):
        print(f"Arquivo não encontrado: {yaml_file}")
        sys.exit(1)
        
    # Testa a validação
    valid, error_msg = validate_yaml(yaml_file)
    if valid:
        print(f"Arquivo YAML '{yaml_file}' é válido.")
    else:
        print(f"Arquivo YAML '{yaml_file}' é inválido: {error_msg}")
        
        # Tenta corrigir se inválido
        fixed, fix_error = fix_yaml_file(yaml_file, output_file)
        if fixed:
            print(f"Arquivo YAML corrigido e salvo em '{output_file or yaml_file}'.")
        else:
            print(f"Não foi possível corrigir o arquivo: {fix_error}")
            sys.exit(1) 