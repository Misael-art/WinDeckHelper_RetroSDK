#!/usr/bin/env python3
"""
Módulo de gerenciamento de mirrors para Environment Dev

Este módulo fornece uma interface de linha de comando para gerenciar a configuração
de mirrors usados para downloads no Environment Dev.

Permite listar, adicionar, remover e testar mirrors para diferentes domínios.
"""

import os
import sys
import argparse
import logging
import json
from typing import List, Dict, Optional

# Adiciona o diretório pai ao sys.path para permitir importações relativas
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importa as funções de gerenciamento de mirrors
from env_dev.utils.mirror_manager import (
    load_mirrors_config, save_mirrors_config, register_mirror, 
    remove_mirror, check_url_availability, find_best_mirror
)

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("mirrors_management")

def list_mirrors(config_file: str, domain: Optional[str] = None) -> None:
    """
    Lista todos os mirrors configurados ou apenas para um domínio específico.
    
    Args:
        config_file: Caminho para o arquivo de configuração
        domain: Domínio específico a listar (opcional)
    """
    mirrors = load_mirrors_config(config_file)
    
    if not mirrors:
        print("Nenhum mirror configurado.")
        return
    
    if domain:
        if domain in mirrors:
            print(f"\nMirrors para {domain}:")
            for i, url in enumerate(mirrors[domain], 1):
                print(f"  {i}. {url}")
        else:
            print(f"Nenhum mirror configurado para o domínio '{domain}'.")
        return
    
    print("\nDomínios e mirrors configurados:")
    for domain, urls in mirrors.items():
        print(f"\n[{domain}]")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")

def add_mirror(config_file: str, domain: str, url: str) -> None:
    """
    Adiciona um novo mirror para um domínio.
    
    Args:
        config_file: Caminho para o arquivo de configuração
        domain: Domínio para o mirror
        url: URL base do mirror
    """
    success = register_mirror(domain, url, config_file)
    
    if success:
        print(f"Mirror '{url}' adicionado com sucesso para o domínio '{domain}'.")
    else:
        print(f"Falha ao adicionar mirror '{url}' para o domínio '{domain}'.")

def remove_mirror_cli(config_file: str, domain: str, url: str) -> None:
    """
    Remove um mirror existente.
    
    Args:
        config_file: Caminho para o arquivo de configuração
        domain: Domínio do mirror
        url: URL base do mirror a remover
    """
    success = remove_mirror(domain, url, config_file)
    
    if success:
        print(f"Mirror '{url}' removido com sucesso do domínio '{domain}'.")
    else:
        print(f"Falha ao remover mirror '{url}' do domínio '{domain}'. "
              f"Verifique se o domínio e URL existem na configuração.")

def test_mirrors(config_file: str, test_url: str) -> None:
    """
    Testa a disponibilidade de mirrors para uma URL específica.
    
    Args:
        config_file: Caminho para o arquivo de configuração
        test_url: URL para testar
    """
    print(f"Testando mirrors para URL: {test_url}")
    
    best_url, alt_urls = find_best_mirror(test_url)
    
    print("\nURLs alternativas encontradas:")
    for i, url in enumerate(alt_urls, 1):
        status = "✓" if check_url_availability(url) else "✗"
        if url == best_url:
            print(f"  {i}. {url} [MELHOR] {status}")
        else:
            print(f"  {i}. {url} {status}")
    
    if best_url == test_url:
        print("\nResultado: A URL original é a melhor opção disponível.")
    else:
        print(f"\nResultado: Mirror recomendado: {best_url}")

def export_mirrors(config_file: str, output_file: str) -> None:
    """
    Exporta a configuração de mirrors para um arquivo JSON separado.
    
    Args:
        config_file: Caminho para o arquivo de configuração atual
        output_file: Caminho para o arquivo de saída
    """
    mirrors = load_mirrors_config(config_file)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mirrors, f, indent=2)
        print(f"Configuração de mirrors exportada com sucesso para '{output_file}'.")
    except Exception as e:
        print(f"Erro ao exportar configuração: {e}")

def import_mirrors(config_file: str, input_file: str, overwrite: bool = False) -> None:
    """
    Importa configuração de mirrors de um arquivo JSON externo.
    
    Args:
        config_file: Caminho para o arquivo de configuração atual
        input_file: Caminho para o arquivo de entrada
        overwrite: Se deve sobrescrever a configuração atual (True) ou mesclar (False)
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            imported_mirrors = json.load(f)
        
        if not isinstance(imported_mirrors, dict):
            print("Formato de arquivo inválido. Deve ser um objeto JSON com domínios como chaves.")
            return
        
        if overwrite:
            # Sobrescreve totalmente a configuração
            save_mirrors_config(imported_mirrors, config_file)
            print(f"Configuração de mirrors substituída com sucesso por '{input_file}'.")
        else:
            # Mescla com a configuração existente
            current_mirrors = load_mirrors_config(config_file)
            
            for domain, urls in imported_mirrors.items():
                if domain in current_mirrors:
                    # Adiciona apenas URLs que não existem
                    current_mirrors[domain] = list(set(current_mirrors[domain] + urls))
                else:
                    current_mirrors[domain] = urls
            
            save_mirrors_config(current_mirrors, config_file)
            print(f"Configuração de mirrors mesclada com sucesso com '{input_file}'.")
    except Exception as e:
        print(f"Erro ao importar configuração: {e}")

def main():
    parser = argparse.ArgumentParser(description='Gerenciador de Mirrors para Environment Dev')
    subparsers = parser.add_subparsers(dest='command', help='Comando a executar')
    
    # Comando: list
    list_parser = subparsers.add_parser('list', help='Listar mirrors configurados')
    list_parser.add_argument('--domain', '-d', help='Listar apenas mirrors para um domínio específico')
    list_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    # Comando: add
    add_parser = subparsers.add_parser('add', help='Adicionar um novo mirror')
    add_parser.add_argument('domain', help='Domínio para o mirror (ex: github.com)')
    add_parser.add_argument('url', help='URL base do mirror')
    add_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    # Comando: remove
    remove_parser = subparsers.add_parser('remove', help='Remover um mirror existente')
    remove_parser.add_argument('domain', help='Domínio do mirror a remover')
    remove_parser.add_argument('url', help='URL base do mirror a remover')
    remove_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    # Comando: test
    test_parser = subparsers.add_parser('test', help='Testar mirrors para uma URL')
    test_parser.add_argument('url', help='URL para testar')
    test_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    # Comando: export
    export_parser = subparsers.add_parser('export', help='Exportar configuração para arquivo JSON')
    export_parser.add_argument('output', help='Arquivo de saída')
    export_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    # Comando: import
    import_parser = subparsers.add_parser('import', help='Importar configuração de arquivo JSON')
    import_parser.add_argument('input', help='Arquivo de entrada')
    import_parser.add_argument('--overwrite', '-o', action='store_true', 
                              help='Sobrescrever a configuração atual (padrão: mesclar)')
    import_parser.add_argument('--config', '-c', help='Arquivo de configuração personalizado')
    
    args = parser.parse_args()
    
    # Define o arquivo de configuração padrão
    from env_dev.utils.mirror_manager import DEFAULT_MIRRORS_FILE
    config_file = args.config if hasattr(args, 'config') and args.config else DEFAULT_MIRRORS_FILE
    
    # Executa o comando apropriado
    if args.command == 'list':
        list_mirrors(config_file, args.domain)
    elif args.command == 'add':
        add_mirror(config_file, args.domain, args.url)
    elif args.command == 'remove':
        remove_mirror_cli(config_file, args.domain, args.url)
    elif args.command == 'test':
        test_mirrors(config_file, args.url)
    elif args.command == 'export':
        export_mirrors(config_file, args.output)
    elif args.command == 'import':
        import_mirrors(config_file, args.input, args.overwrite)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1) 