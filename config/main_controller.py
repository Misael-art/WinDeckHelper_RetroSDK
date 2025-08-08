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
    # Adicionar importação da GUI Qt
    try:
        from gui.app_gui_qt import main as start_qt_gui
        QT_GUI_AVAILABLE = True
    except ImportError:
        QT_GUI_AVAILABLE = False
        start_qt_gui = None
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
    parser = argparse.ArgumentParser(
        description="Environment Dev - Gerenciador modular de componentes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemplos de uso:
  %(prog)s --list                          # Lista todos os componentes
  %(prog)s --install sgdk                  # Instala o SGDK
  %(prog)s --install sgdk java --force     # Instala SGDK e Java forçadamente
  %(prog)s --install-category retro        # Instala todos os componentes da categoria retro
  %(prog)s --verify sgdk                   # Verifica se SGDK está instalado
  %(prog)s --verify-all                    # Verifica todos os componentes
  %(prog)s --list-category development     # Lista componentes de desenvolvimento
  %(prog)s --gui                           # Inicia interface gráfica (Tkinter)
  %(prog)s --gui-qt                        # Inicia interface gráfica (PyQt5)"""
    )
    
    # Comandos principais
    parser.add_argument("--list", action="store_true", help="Lista todos os componentes disponíveis")
    parser.add_argument("--categories", action="store_true", help="Lista todas as categorias disponíveis")
    parser.add_argument("--install", nargs="+", help="Instala um ou mais componentes específicos")
    parser.add_argument("--install-category", type=str, help="Instala todos os componentes de uma categoria")
    parser.add_argument("--verify", nargs="+", help="Verifica a instalação de um ou mais componentes")
    parser.add_argument("--verify-all", action="store_true", help="Verifica a instalação de todos os componentes")
    parser.add_argument("--list-category", type=str, help="Lista componentes de uma categoria específica")
    parser.add_argument("--gui", action="store_true", help="Inicia a interface gráfica (Tkinter)")
    parser.add_argument("--gui-qt", action="store_true", help="Inicia a interface gráfica (PyQt5)")
    
    # Opções avançadas
    parser.add_argument("--force", action="store_true", help="Força a instalação mesmo que já esteja instalado")
    parser.add_argument("--debug", action="store_true", help="Ativa modo de depuração")
    parser.add_argument("--no-deps", action="store_true", help="Não instala dependências")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso (menos output)")
    parser.add_argument("--verbose", action="store_true", help="Modo verboso (mais detalhes)")
    
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
    """Instala um componente específico usando o mesmo processo da GUI"""
    logger.info("Solicitada instalação do componente: %s", component_name)
    
    # Importar o instalador principal
    try:
        from core.installer import install_component as core_install_component
        from core.rollback_manager import RollbackManager
    except ImportError:
        logger.error("Erro ao importar módulos de instalação")
        print("Erro: Módulos de instalação não encontrados.")
        return False
    
    # Obter detalhes do componente
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado: %s", component_name)
        print(f"Erro: Componente '{component_name}' não encontrado.")
        return False
    
    logger.info("Detalhes do componente: %s", component)
    
    # Verificar se já está instalado (se não forçar reinstalação)
    if not force and is_component_installed(component_name):
        logger.info("Componente já instalado: %s", component_name)
        print(f"O componente '{component_name}' já está instalado.")
        return True
    
    # Carregar todos os componentes para resolver dependências
    all_components = load_all_components()
    
    # Criar conjunto para rastrear componentes instalados
    installed_components = set()
    
    # Criar gerenciador de rollback
    rollback_mgr = RollbackManager()
    rollback_mgr.start_transaction(component_name)
    
    # Criar uma fila simples para capturar status updates
    import queue
    status_queue = queue.Queue()
    
    # Função para processar atualizações de status
    def process_status_updates():
        while True:
            try:
                update = status_queue.get(timeout=0.1)
                if update.get('type') == 'stage':
                    print(f"[{update['component']}] {update['stage']}")
                elif update.get('type') == 'progress':
                    percent = update.get('percent', 0)
                    print(f"[{update['component']}] Progresso: {percent}%")
                elif update.get('type') == 'result':
                    status = update.get('status', 'UNKNOWN')
                    message = update.get('message', '')
                    if status == 'SUCCESS':
                        print(f"[{update['component']}] ✓ {message}")
                    elif status == 'FAILED':
                        print(f"[{update['component']}] ✗ {message}")
                    else:
                        print(f"[{update['component']}] {status}: {message}")
                status_queue.task_done()
            except queue.Empty:
                break
    
    print(f"Instalando {component_name}...")
    logger.info("Iniciando instalação de %s usando core installer", component_name)
    
    try:
        # Usar o instalador principal (mesmo processo da GUI)
        success = core_install_component(
            component_name=component_name,
            component_data=component,
            all_components_data=all_components if not no_deps else None,
            installed_components=installed_components,
            progress_callback=None,
            rollback_mgr=rollback_mgr,
            status_queue=status_queue
        )
        
        # Processar atualizações de status pendentes
        process_status_updates()
        
        if success:
            logger.info("Instalação concluída com sucesso: %s", component_name)
            print(f"\n✓ Componente '{component_name}' instalado com sucesso.")
            return True
        else:
            logger.error("Falha na instalação de %s", component_name)
            print(f"\n✗ Falha ao instalar '{component_name}'.")
            return False
            
    except Exception as e:
        logger.error("Erro durante a instalação de %s: %s", component_name, str(e))
        if constants.DEBUG_MODE:
            import traceback
            logger.debug(traceback.format_exc())
        print(f"\n✗ Erro ao instalar '{component_name}': {str(e)}")
        
        # Processar atualizações de status pendentes mesmo em caso de erro
        process_status_updates()
        
        return False

def is_component_installed(component_name):
    """Verifica se um componente está instalado usando o sistema de detecção YAML corrigido"""
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado para verificação: %s", component_name)
        return False

    logger.info("Verificando instalação de %s", component_name)
    
    if "verify_actions" not in component:
        logger.warning("Nenhuma ação de verificação definida para %s", component_name)
        return False

    # Usar o sistema de detecção YAML corrigido com lógica OR
    try:
        from core.yaml_component_detection import YAMLComponentDetectionStrategy
        strategy = YAMLComponentDetectionStrategy()
        
        # Verificar se o componente pode ser detectado
        detected = strategy._detect_yaml_component(component_name, component)
        
        if detected:
            logger.info(f"[OK] {component_name} detectado com sucesso via YAML strategy")
            return True
        else:
            logger.info(f"[FAIL] {component_name} não foi detectado via YAML strategy")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao usar YAML detection strategy para {component_name}: {e}")
        # Fallback para lógica antiga em caso de erro
        return _legacy_component_verification(component_name, component)

def _legacy_component_verification(component_name, component):
    """Verificação legada como fallback"""
    logger.warning(f"Usando verificação legada para {component_name}")
    
    # Melhorar verificação com múltiplas tentativas
    for action in component["verify_actions"]:
        action_type = action.get("type")
        
        if action_type == "file_exists":
            path = action.get("path")
            path = os.path.expandvars(path)
            
            # Adicionar verificações alternativas
            alternative_paths = action.get("alternative_paths", [])
            paths_to_check = [path] + alternative_paths
            
            found = False
            for check_path in paths_to_check:
                if os.path.exists(check_path):
                    found = True
                    break
            
            if not found:
                # Tentar busca por padrão
                if action.get("search_pattern"):
                    import glob
                    matches = glob.glob(action.get("search_pattern"))
                    if matches:
                        found = True
                        
            if not found:
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

def install_multiple_components(component_names, force=False, no_deps=False, quiet=False):
    """Instala múltiplos componentes"""
    if not component_names:
        print("Erro: Nenhum componente especificado.")
        return False
    
    success_count = 0
    total_count = len(component_names)
    
    if not quiet:
        print(f"\nInstalando {total_count} componente(s): {', '.join(component_names)}")
        print("=" * 60)
    
    for i, component_name in enumerate(component_names, 1):
        if not quiet:
            print(f"\n[{i}/{total_count}] Processando: {component_name}")
            print("-" * 40)
        
        success = install_component(component_name, force, no_deps)
        if success:
            success_count += 1
            if not quiet:
                print(f"✓ {component_name} instalado com sucesso")
        else:
            if not quiet:
                print(f"✗ Falha ao instalar {component_name}")
    
    if not quiet:
        print(f"\n=== Resumo da Instalação ===")
        print(f"Sucessos: {success_count}/{total_count}")
        print(f"Falhas: {total_count - success_count}/{total_count}")
    
    return success_count == total_count

def install_category_components(category_name, force=False, no_deps=False, quiet=False):
    """Instala todos os componentes de uma categoria"""
    components = get_components_by_category(category_name)
    
    if not components:
        print(f"Erro: Categoria '{category_name}' não encontrada ou vazia.")
        return False
    
    component_names = [comp['name'] for comp in components]
    
    if not quiet:
        print(f"\nInstalando categoria '{category_name}' ({len(component_names)} componentes)")
    
    return install_multiple_components(component_names, force, no_deps, quiet)

def verify_component(component_name, quiet=False, auto_repair=True):
    """Verifica e exibe o status de instalação de um componente"""
    logger.info("Verificando componente: %s", component_name)
    
    component = get_component(component_name)
    
    if not component:
        logger.error("Componente não encontrado: %s", component_name)
        print(f"Erro: Componente '{component_name}' não encontrado.")
        return False
    
    is_installed = is_component_installed(component_name)
    
    # Se não está instalado e auto-reparo está habilitado
    if not is_installed and auto_repair:
        logger.info(f"Tentando auto-reparo para {component_name}")
        
        # Tentar reinstalação automática
        try:
            success = install_component(component_name, force=True)
            if success:
                is_installed = is_component_installed(component_name)
                if is_installed:
                    logger.info(f"Auto-reparo bem-sucedido para {component_name}")
                else:
                    logger.warning(f"Reinstalação concluída mas verificação ainda falha para {component_name}")
        except Exception as e:
            logger.error(f"Erro durante auto-reparo de {component_name}: {e}")
    
    if quiet:
        status_symbol = "✓" if is_installed else "✗"
        print(f"{status_symbol} {component_name}: {'Instalado' if is_installed else 'Não instalado'}")
    else:
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
    
    return is_installed

def verify_multiple_components(component_names, quiet=False):
    """Verifica múltiplos componentes"""
    if not component_names:
        print("Erro: Nenhum componente especificado.")
        return False
    
    installed_count = 0
    total_count = len(component_names)
    
    if not quiet:
        print(f"\nVerificando {total_count} componente(s)")
        print("=" * 50)
    
    for component_name in component_names:
        is_installed = verify_component(component_name, quiet=True)
        if is_installed:
            installed_count += 1
        
        if not quiet:
            verify_component(component_name, quiet=False)
    
    if not quiet:
        print(f"\n=== Resumo da Verificação ===")
        print(f"Instalados: {installed_count}/{total_count}")
        print(f"Não instalados: {total_count - installed_count}/{total_count}")
    
    return installed_count == total_count

def verify_all_components(quiet=False):
    """Verifica todos os componentes disponíveis"""
    all_components = load_all_components()
    
    if not all_components:
        print("Erro: Nenhum componente encontrado.")
        return False
    
    component_names = list(all_components.keys())
    
    if not quiet:
        print(f"\nVerificando todos os componentes ({len(component_names)} total)")
    
    return verify_multiple_components(component_names, quiet)

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

def start_gui_qt():
    """Inicia a interface gráfica PyQt5"""
    logger.info("Iniciando interface gráfica PyQt5")
    
    if not QT_GUI_AVAILABLE:
        logger.error("PyQt5 não está disponível")
        print("Erro: PyQt5 não está instalado ou disponível.")
        print("Para instalar PyQt5, execute: pip install PyQt5")
        return
    
    try:
        # Configura o logger específico para a GUI Qt
        gui_logger = logging.getLogger("gui_qt")
        gui_handler = logging.FileHandler(constants.GUI_LOG_FILE)
        gui_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(gui_formatter)
        gui_logger.addHandler(gui_handler)
        gui_logger.setLevel(logging.INFO)
        
        logger.info("Interface gráfica PyQt5 iniciada com sucesso")
        print("Interface gráfica PyQt5 iniciada. Consulte o log em %s para detalhes." % constants.GUI_LOG_FILE)
        
        # Inicia a GUI Qt
        start_qt_gui()
        
    except Exception as e:
        logger.error("Erro ao iniciar interface gráfica PyQt5: %s", str(e))
        if constants.DEBUG_MODE:
            import traceback
            logger.debug(traceback.format_exc())
        print(f"Erro ao iniciar interface gráfica PyQt5: {str(e)}")
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
    
    # Configurar modo verboso
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Modo verboso ativado")
    
    # Inicializar sistema
    if not initialize_system():
        logger.error("Falha ao inicializar o sistema")
        return 1
    
    # Executar comando solicitado
    try:
        if args.list:
            display_components()
        elif args.categories:
            display_categories()
        elif args.list_category:
            display_category_components(args.list_category)
        elif args.install:
            # Instalar múltiplos componentes
            success = install_multiple_components(
                args.install, 
                args.force, 
                args.no_deps, 
                args.quiet
            )
            return 0 if success else 1
        elif args.install_category:
            # Instalar categoria completa
            success = install_category_components(
                args.install_category,
                args.force,
                args.no_deps,
                args.quiet
            )
            return 0 if success else 1
        elif args.verify:
            # Verificar múltiplos componentes
            success = verify_multiple_components(args.verify, args.quiet)
            return 0 if success else 1
        elif args.verify_all:
            # Verificar todos os componentes
            success = verify_all_components(args.quiet)
            return 0 if success else 1
        elif args.gui:
            start_gui()
        elif args.gui_qt:
            start_gui_qt()
        else:
            # Se nenhum argumento fornecido, inicia GUI Qt por padrão
            if QT_GUI_AVAILABLE:
                if not args.quiet:
                    print("Iniciando interface gráfica Qt...")
                logger.info("Nenhum comando especificado, iniciando GUI Qt por padrão")
                start_gui_qt()
            else:
                # Fallback para GUI Tkinter se Qt não estiver disponível
                if not args.quiet:
                    print("GUI Qt não disponível, iniciando interface Tkinter...")
                logger.info("GUI Qt não disponível, iniciando GUI Tkinter como fallback")
                start_gui()
            return 0
    
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n\nOperação cancelada pelo usuário.")
        logger.info("Operação cancelada pelo usuário")
        return 130  # Código de saída padrão para SIGINT
    except Exception as e:
        logger.error("Erro não tratado: %s", str(e))
        if args.debug or args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        if not args.quiet:
            print(f"Erro: {str(e)}")
        return 1
    
    logger.info("Execução concluída com sucesso")
    return 0

if __name__ == "__main__":
    sys.exit(run())