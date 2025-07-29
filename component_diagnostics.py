#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnóstico para componentes do Environment Dev Script.
Verifica o status de instalação de cada componente definido no arquivo components.yaml
e identifica possíveis problemas ou erros comuns.
"""

import os
import sys
import logging
import argparse
import yaml
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("component_diagnostics")

# Diretório base do projeto
script_dir = os.path.abspath(os.path.dirname(__file__))

# Caminho para o arquivo YAML de componentes
DEFAULT_COMPONENTS_YAML = os.path.join(script_dir, "env_dev", "components.yaml")

def load_components(yaml_path):
    """Carrega os componentes do arquivo YAML"""
    try:
        if not os.path.exists(yaml_path):
            logger.error(f"Arquivo de componentes não encontrado: {yaml_path}")
            return None
            
        with open(yaml_path, 'r', encoding='utf-8') as file:
            try:
                data = yaml.safe_load(file)
                
                # Verifica se é o formato novo (com chave 'components')
                if data and 'components' in data:
                    return data['components']
                    
                # Verifica se é formato legado (sem chave 'components', com componentes diretamente no root)
                elif data and isinstance(data, dict) and any(isinstance(value, dict) for value in data.values()):
                    # Assumindo que é o formato legado
                    logger.info("Detectado formato legado de arquivo YAML de componentes")
                    return data
                else:
                    logger.error(f"Arquivo YAML inválido ou sem componentes: {yaml_path}")
                    return None
            except yaml.YAMLError as e:
                logger.error(f"Erro ao analisar o arquivo YAML: {e}")
                return None
    except Exception as e:
        logger.error(f"Erro ao carregar componentes: {e}")
        return None

def check_file_exists(file_path):
    """Verifica se um arquivo existe no sistema"""
    return os.path.exists(file_path)

def check_registry_key(key_path, value_name=None, expected_value=None):
    """Verifica se uma chave do registro existe e opcionalmente compara seu valor"""
    import winreg
    
    # Identifica a raiz da chave
    if key_path.startswith("HKLM\\"):
        root = winreg.HKEY_LOCAL_MACHINE
        key_path = key_path[5:]
    elif key_path.startswith("HKCU\\"):
        root = winreg.HKEY_CURRENT_USER
        key_path = key_path[5:]
    else:
        logger.warning(f"Formato de chave de registro inválido: {key_path}")
        return False
    
    try:
        # Tenta abrir a chave
        with winreg.OpenKey(root, key_path) as key:
            # Se não for necessário verificar um valor específico
            if not value_name:
                return True
                
            # Tenta ler o valor específico
            try:
                reg_value, _ = winreg.QueryValueEx(key, value_name)
                
                # Compara o valor se um valor esperado foi fornecido
                if expected_value is not None:
                    return str(reg_value) == str(expected_value)
                    
                # Se nenhum valor esperado for fornecido, apenas verifica se o valor existe
                return True
                
            except FileNotFoundError:
                logger.warning(f"Valor '{value_name}' não encontrado na chave {key_path}")
                return False
                
    except FileNotFoundError:
        logger.warning(f"Chave de registro não encontrada: {key_path}")
        return False
    except Exception as e:
        logger.warning(f"Erro ao verificar registro {key_path}: {e}")
        return False

def check_url_availability(url):
    """Verifica se uma URL está disponível"""
    try:
        response = requests.head(url, timeout=5)
        return 200 <= response.status_code < 400
    except Exception as e:
        logger.warning(f"Erro ao verificar URL {url}: {e}")
        return False

def check_installation_status(component_name, component_data):
    """
    Verifica o status de instalação de um componente com base nas suas definições
    
    Returns:
        dict: Dicionário com informações de status do componente
    """
    status = {
        "name": component_name,
        "is_installed": False,
        "installation_path": None,
        "valid_download_url": False,
        "verification_details": [],
        "issues": []
    }
    
    # Verifica URL de download
    if component_data.get('download'):
        for platform, download_info in component_data['download'].items():
            url = download_info.get('url')
            if url:
                url_available = check_url_availability(url)
                status["valid_download_url"] = url_available
                if not url_available:
                    status["issues"].append(f"URL de download indisponível: {url}")

    # Verifica se é uma configuração antiga (legado)
    if 'download_url' in component_data:
        old_url = component_data.get('download_url')
        if old_url:
            url_available = check_url_availability(old_url)
            status["valid_download_url"] = url_available
            status["legacy_format"] = True
            if not url_available:
                status["issues"].append(f"URL legada de download indisponível: {old_url}")
    
    # Verifica itens específicos para confirmar instalação
    if 'verify_items' in component_data:
        for item in component_data['verify_items']:
            item_type = item.get('type')
            item_status = False
            
            if item_type == 'file' and 'path' in item:
                file_path = item['path']
                file_exists = check_file_exists(file_path)
                if file_exists and not status['installation_path']:
                    status['installation_path'] = os.path.dirname(file_path)
                item_status = file_exists
                status['verification_details'].append({
                    'type': 'file',
                    'path': file_path,
                    'exists': file_exists
                })
                if not file_exists:
                    status["issues"].append(f"Arquivo de verificação não encontrado: {file_path}")
            
            elif item_type == 'registry' and 'key' in item:
                key_path = item['key']
                value_name = item.get('value')
                expected_value = item.get('expected')
                
                registry_valid = check_registry_key(key_path, value_name, expected_value)
                item_status = registry_valid
                status['verification_details'].append({
                    'type': 'registry',
                    'key': key_path,
                    'value': value_name,
                    'expected': expected_value,
                    'exists': registry_valid
                })
                if not registry_valid:
                    status["issues"].append(f"Chave de registro não encontrada ou inválida: {key_path}")
            
            elif item_type == 'command' and 'command' in item:
                # Verificação de comando não implementada neste diagnóstico básico
                pass
    
    # Verificações baseadas em arquivos legados
    elif 'extract_path' in component_data:
        extract_path = component_data['extract_path']
        if extract_path:
            # Expande variáveis de ambiente
            if '${env:' in extract_path:
                import re
                env_vars = re.findall(r'\${env:([^}]+)}', extract_path)
                for var in env_vars:
                    if var in os.environ:
                        extract_path = extract_path.replace(f'${{env:{var}}}', os.environ[var])
            
            dir_exists = os.path.isdir(extract_path)
            if dir_exists:
                status['installation_path'] = extract_path
                status['verification_details'].append({
                    'type': 'directory',
                    'path': extract_path,
                    'exists': True
                })
            else:
                status["issues"].append(f"Diretório de extração não encontrado: {extract_path}")
    
    # Determina se o componente está instalado com base nas verificações
    if status['verification_details']:
        status['is_installed'] = any(detail.get('exists', False) for detail in status['verification_details'])
    
    return status

def diagnose_components(components_data, args):
    """
    Realiza diagnóstico de todos os componentes
    
    Args:
        components_data: Dicionário com dados dos componentes
        args: Argumentos de linha de comando
        
    Returns:
        dict: Resultados do diagnóstico
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_components": len(components_data),
        "installed_components": 0,
        "components_with_issues": 0,
        "components": []
    }
    
    for name, component in components_data.items():
        # Se um componente específico foi solicitado e não é este, pula
        if args.component and args.component != name:
            continue
            
        logger.info(f"Verificando componente: {name}")
        status = check_installation_status(name, component)
        
        if status['is_installed']:
            results['installed_components'] += 1
            
        if status['issues']:
            results['components_with_issues'] += 1
            
        results['components'].append(status)
    
    return results

def generate_report(results, output_format, output_file=None):
    """Gera relatório de diagnóstico no formato especificado"""
    if output_format == 'json':
        report = json.dumps(results, indent=2)
    else:  # formato texto
        report = create_text_report(results)
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Relatório salvo em: {output_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")
    else:
        print(report)
    
def create_text_report(results):
    """Cria um relatório em formato texto"""
    report = []
    report.append("=" * 80)
    report.append("RELATÓRIO DE DIAGNÓSTICO DE COMPONENTES")
    report.append("=" * 80)
    report.append(f"Data/Hora: {results['timestamp']}")
    report.append(f"Total de componentes: {results['total_components']}")
    report.append(f"Componentes instalados: {results['installed_components']}")
    report.append(f"Componentes com problemas: {results['components_with_issues']}")
    report.append("=" * 80)
    report.append("\nDETALHES DOS COMPONENTES:")
    
    for component in results['components']:
        report.append("\n" + "-" * 80)
        report.append(f"Nome: {component['name']}")
        report.append(f"Instalado: {'Sim' if component['is_installed'] else 'Não'}")
        
        if component['installation_path']:
            report.append(f"Caminho de instalação: {component['installation_path']}")
            
        if component.get('legacy_format'):
            report.append("Observação: Componente usa formato legado de configuração")
            
        if component['verification_details']:
            report.append("\nDetalhes de verificação:")
            for detail in component['verification_details']:
                if detail['type'] == 'file':
                    report.append(f"  - Arquivo: {detail['path']} - {'Encontrado' if detail['exists'] else 'NÃO ENCONTRADO'}")
                elif detail['type'] == 'registry':
                    report.append(f"  - Registro: {detail['key']} - {'Válido' if detail['exists'] else 'INVÁLIDO'}")
                elif detail['type'] == 'directory':
                    report.append(f"  - Diretório: {detail['path']} - {'Encontrado' if detail['exists'] else 'NÃO ENCONTRADO'}")
        
        if component['issues']:
            report.append("\nProblemas detectados:")
            for issue in component['issues']:
                report.append(f"  - {issue}")
    
    return "\n".join(report)

def main():
    """Função principal do script de diagnóstico"""
    parser = argparse.ArgumentParser(description='Ferramenta de diagnóstico para componentes do Environment Dev Script')
    parser.add_argument('--yaml', dest='yaml_path', default=DEFAULT_COMPONENTS_YAML,
                        help='Caminho para o arquivo YAML de componentes')
    parser.add_argument('--component', dest='component', 
                        help='Verificar apenas um componente específico')
    parser.add_argument('--format', dest='output_format', choices=['text', 'json'], default='text',
                        help='Formato de saída do relatório (padrão: text)')
    parser.add_argument('--output', dest='output_file',
                        help='Salvar relatório em arquivo ao invés de exibir na tela')
    parser.add_argument('--verbose', action='store_true',
                        help='Exibe informações detalhadas durante a execução')
    
    args = parser.parse_args()
    
    # Ajusta o nível de log com base na verbosidade
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Carrega os componentes
    logger.info(f"Carregando componentes de: {args.yaml_path}")
    components = load_components(args.yaml_path)
    
    if not components:
        logger.error("Não foi possível carregar os componentes. Abortando.")
        sys.exit(1)
    
    # Realiza diagnóstico
    logger.info("Iniciando diagnóstico de componentes...")
    results = diagnose_components(components, args)
    
    # Gera relatório
    logger.info("Gerando relatório...")
    generate_report(results, args.output_format, args.output_file)
    
    logger.info("Diagnóstico concluído.")
    
    # Retorna código de erro se houver componentes com problemas
    if results['components_with_issues'] > 0:
        sys.exit(2)
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Diagnóstico interrompido pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Erro não tratado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 