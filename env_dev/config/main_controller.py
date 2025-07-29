#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Controlador principal para o Environment Dev
Este módulo coordena o carregamento e execução modular da aplicação
"""

import os
import sys
import logging
import argparse
import yaml
import threading
import time
from pathlib import Path

# Importar módulos do projeto
try:
    from config import constants
    from config.loader import load_all_components, get_component, list_categories, get_components_by_category
    from gui.app_gui import AppGUI
except ImportError:
    # Adicionar diretório pai ao PYTHONPATH
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import constants
    from config.loader import load_all_components, get_component, list_categories, get_components_by_category
    from gui.app_gui import AppGUI

# Configurar logger
logger = logging.getLogger("main_controller")
handler = logging.FileHandler(constants.MAIN_LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def setup_logging():
    """Configura o sistema de logging"""
    # Verifica se o diretório de logs existe
    logs_dir = os.path.dirname(constants.MAIN_LOG_FILE)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configuração global de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(constants.MAIN_LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Sistema de logging inicializado")
    
    if constants.DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
        logger.debug("Modo de depuração ativado")
    
    return logger

def parse_arguments():
    """Analisa os argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description="Environment Dev - Gerenciador modular de componentes")
    
    # Comandos principais
    parser.add_argument("--list", action="store_true", help="Lista todos os componentes disponíveis")
    parser.add_argument("--categories", action="store_true", help="Lista todas as categorias disponíveis")
    parser.add_argument("--install", type=str, help="Instala um componente específico")
    parser.add_argument("--verify", type=str, help="Verifica a instalação de um componente")
    parser.add_argument("--list-category", type=str, help="Lista componentes de uma categoria específica")
    parser.add_argument("--gui", action="store_true", help="Inicia a interface gráfica")
    
    # Opções avançadas
    parser.add_argument("--force", action="store_true", help="Força a instalação mesmo que já esteja instalado")
    parser.add_argument("--debug", action="store_true", help="Ativa modo de depuração")
    parser.add_argument("--no-deps", action="store_true", help="Não instala dependências")
    
    return parser.parse_args()

def initialize_system():
    """Inicializa o sistema e verifica requisitos"""
    logger.info("Inicializando Environment Dev")
    
    # Verificar privilégios administrativos
    if not constants.is_admin():
        logger.warning("AVISO: Este script não está sendo executado como administrador.")
        logger.warning("Algumas funções podem não funcionar corretamente.")
    
    # Verificar existência da estrutura modular
    if not constants.MIGRATION_COMPLETED:
        logger.error("A estrutura modular não foi encontrada. Execute a migração primeiro.")
        return False
    
    # Verificar existência dos arquivos de componentes
    component_files = os.listdir(constants.COMPONENTS_DIR)
    if not component_files:
        logger.error("Nenhum arquivo de componente encontrado em %s", constants.COMPONENTS_DIR)
        return False
    
    logger.info("Arquivos de componentes encontrados: %s", ", ".join(component_files))
    
    # Tentar carregar os componentes
    try:
        components = load_all_components()
        logger.info("Carregados %d componentes de %d arquivos", 
                   len(components), len(component_files))
        return True
    except Exception as e:
        logger.error("Erro ao carregar componentes: %s", str(e))
        if constants.DEBUG_MODE:
            import traceback
            logger.debug(traceback.format_exc())
        return False

def display_components():
    """Exibe a lista de componentes disponíveis"""
    components = load_all_components()
    if not components:
        logger.error("Nenhum componente disponível.")
        return
    
    print(f"\nComponentes disponíveis ({len(components)}):")
    print("="*50)
    
    # Organizar por categoria
    categories = {}
    for name, details in components.items():
        category = details.get("category", "Sem categoria")
        if category not in categories:
            categories[category] = []
        categories[category].append(name)
    
    # Exibir por categoria
    for category, names in sorted(categories.items()):
        print(f"\n{category} ({len(names)}):")
        for name in sorted(names):
            desc = components[name].get("description", "Sem descrição")
            print(f"  - {name}: {desc}")

def display_categories():
    """Exibe a lista de categorias disponíveis"""
    categories = list_categories()
    
    print("\nCategorias disponíveis:")
    print("="*30)
    for category in categories:
        components = get_components_by_category(category)
        print(f"- {category} ({len(components)} componentes)")

def display_category_components(category):
    """Exibe os componentes de uma categoria específica"""
    components = get_components_by_category(category)
    
    if not components:
        print(f"Nenhum componente encontrado na categoria '{category}'.")
        return
    
    print(f"\nComponentes na categoria '{category}' ({len(components)}):")
    print("="*60)
    for name, details in sorted(components.items()):
        desc = details.get("description", "Sem descrição")
        print(f"- {name}: {desc}")

def install_component(component_name, force=False, no_deps=False):
    """Instala um componente específico"""
    logger.info("Solicitada instalação do componente: %s", component_name)
    
    # Obter detalhes do componente
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado: %s", component_name)
        print(f"Erro: Componente '{component_name}' não encontrado.")
        return False
    
    logger.info("Detalhes do componente: %s", component)
    
    # Verificar dependências
    if not no_deps and "dependencies" in component and component["dependencies"]:
        logger.info("Instalando dependências: %s", component["dependencies"])
        for dep in component["dependencies"]:
            logger.info("Instalando dependência: %s", dep)
            # Chamar recursivamente para instalar dependência
            if not install_component(dep, force, no_deps):
                logger.error("Falha ao instalar dependência: %s", dep)
                print(f"Erro: Falha ao instalar dependência '{dep}'.")
                return False
    
    # Verificar se já está instalado
    if not force and is_component_installed(component_name):
        logger.info("Componente já instalado: %s", component_name)
        print(f"O componente '{component_name}' já está instalado.")
        return True
    
    # Instalar componente - este é um exemplo simplificado
    # O código real precisaria implementar lógica para cada método de instalação
    print(f"Instalando {component_name}...")
    logger.info("Iniciando instalação de %s", component_name)
    
    try:
        # Aqui seria implementada a lógica de instalação baseada no método
        # Por exemplo, download, execução de scripts, etc.
        
        logger.info("Instalação concluída com sucesso: %s", component_name)
        if "post_install_message" in component:
            print(f"\nInformação pós-instalação: {component['post_install_message']}")
        
        print(f"Componente '{component_name}' instalado com sucesso.")
        return True
    except Exception as e:
        logger.error("Erro durante a instalação de %s: %s", component_name, str(e))
        if constants.DEBUG_MODE:
            import traceback
            logger.debug(traceback.format_exc())
        print(f"Erro ao instalar '{component_name}': {str(e)}")
        return False

def is_component_installed(component_name):
    """Verifica se um componente está instalado"""
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado para verificação: %s", component_name)
        return False
    
    # Esta é uma lógica simplificada para verificar a instalação
    # O código real precisaria implementar verificação para cada tipo de verificação
    logger.info("Verificando instalação de %s", component_name)
    
    if "verify_actions" not in component:
        logger.warning("Nenhuma ação de verificação definida para %s", component_name)
        return False
    
    # Exemplo de verificação básica
    for action in component["verify_actions"]:
        action_type = action.get("type")
        
        if action_type == "file_exists":
            path = action.get("path")
            path = os.path.expandvars(path)  # Expandir variáveis de ambiente
            exists = os.path.exists(path)
            logger.info("Verificando existência de arquivo %s: %s", path, exists)
            if not exists:
                return False
        
        elif action_type == "directory_exists":
            path = action.get("path")
            path = os.path.expandvars(path)
            exists = os.path.isdir(path)
            logger.info("Verificando existência de diretório %s: %s", path, exists)
            if not exists:
                return False
        
        # Outros tipos de verificação seriam implementados aqui
    
    return True

def verify_component(component_name):
    """Verifica e exibe o status de instalação de um componente"""
    logger.info("Verificando componente: %s", component_name)
    
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado: %s", component_name)
        print(f"Erro: Componente '{component_name}' não encontrado.")
        return
    
    is_installed = is_component_installed(component_name)
    
    print(f"\nVerificação do componente '{component_name}':")
    print("="*50)
    print(f"Descrição: {component.get('description', 'Sem descrição')}")
    print(f"Categoria: {component.get('category', 'Sem categoria')}")
    print(f"Status: {'Instalado' if is_installed else 'Não instalado'}")
    
    # Exibir detalhes das ações de verificação
    if "verify_actions" in component:
        print("\nDetalhes da verificação:")
        for action in component["verify_actions"]:
            action_type = action.get("type")
            
            if action_type == "file_exists":
                path = action.get("path")
                path = os.path.expandvars(path)
                exists = os.path.exists(path)
                print(f"  - Arquivo {path}: {'Existe' if exists else 'Não existe'}")
            
            elif action_type == "directory_exists":
                path = action.get("path")
                path = os.path.expandvars(path)
                exists = os.path.isdir(path)
                print(f"  - Diretório {path}: {'Existe' if exists else 'Não existe'}")
            
            # Outros tipos de verificação seriam exibidos aqui

def start_gui():
    """Inicia a interface gráfica"""
    logger.info("Iniciando interface gráfica")
    
    try:
        # Configura o logger específico para a GUI
        gui_logger = logging.getLogger("gui")
        gui_handler = logging.FileHandler(constants.GUI_LOG_FILE)
        gui_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(gui_formatter)
        gui_logger.addHandler(gui_handler)
        gui_logger.setLevel(logging.INFO)
        
        # Importações necessárias para modificar o módulo downloader em tempo de execução
        from env_dev.utils import downloader as downloader_module
        
        # Guarda referência à função original para restaurar depois
        original_download_file = downloader_module.download_file
        
        # Iniciar a GUI
        gui = AppGUI()
        logger.info("Interface gráfica iniciada com sucesso")
        print("Interface gráfica iniciada. Consulte o log em %s para detalhes." % constants.GUI_LOG_FILE)
        
        # Modifica a função download_file para registrar o progresso na GUI
        def patched_download_file(*args, **kwargs):
            # Adiciona callback de progresso se não estiver presente
            if 'progress_callback' not in kwargs and hasattr(gui, 'download_progress_callback'):
                kwargs['progress_callback'] = gui.download_progress_callback
            return original_download_file(*args, **kwargs)
        
        # Substitui a função no módulo
        downloader_module.download_file = patched_download_file
        logger.info("Função de download modificada para suportar atualizações de progresso na GUI")
        
        try:
            # Inicia o loop principal da GUI
            gui.mainloop()  # Este método bloqueia até a janela ser fechada
        finally:
            # Restaura a função original ao fechar a GUI
            downloader_module.download_file = original_download_file
            logger.info("Função de download restaurada ao estado original")
        
    except Exception as e:
        logger.error("Erro ao iniciar interface gráfica: %s", str(e))
        if constants.DEBUG_MODE:
            import traceback
            logger.debug(traceback.format_exc())
        print(f"Erro ao iniciar interface gráfica: {str(e)}")
        print(f"Consulte o log em {constants.GUI_LOG_FILE} para mais detalhes.")

def run():
    """Executa o controlador principal com base nos argumentos fornecidos"""
    # Configurar logging
    setup_logging()
    
    # Analisar argumentos
    args = parse_arguments()
    
    # Configurar modo de depuração
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Modo de depuração ativado por argumento")
    
    # Inicializar sistema
    if not initialize_system():
        logger.error("Falha ao inicializar o sistema")
        return 1
    
    # Executar comando solicitado
    if args.list:
        display_components()
    elif args.categories:
        display_categories()
    elif args.list_category:
        display_category_components(args.list_category)
    elif args.install:
        install_component(args.install, args.force, args.no_deps)
    elif args.verify:
        verify_component(args.verify)
    elif args.gui:
        start_gui()
    else:
        # Se nenhum argumento fornecido, exibe ajuda
        print("Nenhum comando especificado. Use --help para ver as opções disponíveis.")
        logger.info("Nenhum comando especificado, exibindo ajuda")
        return 0
    
    logger.info("Execução concluída com sucesso")
    return 0

if __name__ == "__main__":
    sys.exit(run())