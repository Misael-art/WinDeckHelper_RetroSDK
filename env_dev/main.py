import argparse
import sys
import os
import subprocess
import io
import logging
import traceback

# Corrige o sys.path para importações relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Prints adicionais para depuração
print(f"env_dev/main.py: Iniciando carregamento")
print(f"Diretório atual: {os.getcwd()}")
print(f"Argumentos: {sys.argv}")
print(f"Python path: {sys.path}")

# Não vamos modificar o stdout para evitar problemas de I/O
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Importa o sistema de logging personalizado
from env_dev.utils.log_manager import setup_logging, SUCCESS
# Configura o logging
print("Configurando o sistema de logging...")
logger, log_manager = setup_logging()
print("Sistema de logging configurado com sucesso.")
# Configura FileHandler para capturar todos os erros desde o início
try:
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    main_log_file = os.path.join(log_dir, 'main_execution.log')
    # Usa 'w' para sobrescrever o log a cada execução e facilitar a leitura do último erro
    file_handler = logging.FileHandler(main_log_file, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)
    # Adiciona ao logger raiz para pegar tudo
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(logging.INFO) # Garante que INFO e acima sejam logados no arquivo
except Exception as e:
    print(f"AVISO: Não foi possível configurar o log principal em arquivo: {e}")

# Importa o loader de configuração
from env_dev.config.loader import load_all_components
# Importa o módulo de instalação
from env_dev.core import installer
# Importa a classe da GUI
from env_dev.gui.app_gui import AppGUI
# Importa outras funções utilitárias
from env_dev.utils.network import test_internet_connection

def parse_arguments():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Environment Dev - Gerenciador de ambiente de desenvolvimento")

    # Ações principais mutuamente exclusivas
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--check-env", action="store_true", help="Verifica o ambiente de desenvolvimento")
    action_group.add_argument("--list", action="store_true", help="Lista os componentes disponíveis")
    action_group.add_argument("--install", nargs="+", metavar="COMPONENTE", help="Instala os componentes especificados")
    action_group.add_argument("--dual-boot", action="store_true", help="Inicia o assistente de configuração dual boot Windows/Linux")

    # Opções para controlar a inicialização da GUI
    gui_group = parser.add_mutually_exclusive_group()
    gui_group.add_argument("--no-gui", action="store_true", help="Não iniciar a interface gráfica")
    gui_group.add_argument("--gui", action="store_true", help="Forçar a inicialização da interface gráfica")

    # Argumento para indicar que o script foi elevado
    parser.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)

    return parser.parse_args()

def main():
    """Função principal do programa."""
    print("DEBUG: main.py main() started", file=sys.stderr) # DEBUG INICIAL
    try: # ENVOLVE TUDO
        # Configura o logger principal
        session_id = log_manager.start_session("Environment Dev Python")
        logger.info("Iniciando Environment Dev (Python)...")

        # Analisa os argumentos da linha de comando
        args = parse_arguments()

        # Carrega a configuração de componentes
        components_data = load_all_components() # Usa o padrão 'components.yaml'
        if not components_data:
            logger.error("Falha ao carregar a configuração dos componentes. Encerrando.")
            # log_manager.stop_session() # Movido para o finally principal
            sys.exit(1) # Encerra se não conseguir carregar a config

        if args.check_env:
            logger.info("Verificando ambiente...")
            # (Futuro) Chamar função de verificação de ambiente
            # check_environment_status = env_manager.check_dependencies()
            # print(check_environment_status)
            pass # Placeholder
            # log_manager.stop_session() # Movido para o finally principal

        elif args.list:
            logger.info("Listando componentes disponíveis:")
            if components_data:
                # Ordena por categoria e depois por nome para melhor visualização
                sorted_components = sorted(components_data.items(), key=lambda item: (item[1].get('category', 'ZZZ'), item[0]))

                # Agrupa componentes por categoria para melhor organização
                categories = {}
                for name, data in sorted_components:
                    category = data.get('category', 'Outros')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((name, data.get('description', 'Sem descrição')))

                # Imprime componentes agrupados por categoria
                for category, components in sorted(categories.items()):
                    if not components:  # Pula categorias vazias
                        continue
                    print(f"\n--- {category} ---")
                    # Encontra o comprimento máximo dos nomes para alinhar as descrições
                    max_name_length = max(len(name) for name, _ in components) + 2

                    for name, description in components:
                        # Formata o nome com padding fixo para alinhar as descrições
                        padded_name = name.ljust(max_name_length)
                        # Garante que a descrição seja uma string e corrige codificação
                        desc_str = str(description).replace('\n', ' ').strip()
                        try:
                            # Tenta detectar e corrigir problemas de codificação
                            if not isinstance(desc_str, str):
                                desc_str = str(desc_str)
                            # Garante que a saída seja UTF-8
                            print(f"  - {padded_name}: {desc_str}")
                        except UnicodeEncodeError:
                            # Em caso de erro, usa representação ASCII
                            print(f"  - {padded_name}: {desc_str.encode('ascii', 'replace').decode('ascii')}")
            else:
                logger.warning("Nenhum componente encontrado na configuração.")
            # log_manager.stop_session() # Movido para o finally principal

        elif args.install:
            components_to_install = args.install
            logger.info(f"Tentando instalar os seguintes componentes: {', '.join(components_to_install)}")

            # Verifica a conexão antes de iniciar a instalação
            has_connection = test_internet_connection()
            if not has_connection:
                logger.warning("Sem conexão com a internet. Apenas componentes offline poderão ser instalados.")

            installed_in_session = set() # Rastreia o que foi instalado nesta execução
            failed_components = []

            for component_name in components_to_install:
                if component_name in installed_in_session:
                    logger.info(f"Componente '{component_name}' já instalado nesta sessão. Pulando.")
                    continue

                if component_name in components_data:
                    component_data = components_data[component_name]

                    # Verifica se o componente requer internet
                    requires_internet = component_data.get('requires_internet', True)
                    if requires_internet and not has_connection:
                        logger.error(f"Componente '{component_name}' requer conexão com a internet. Pulando.")
                        failed_components.append(component_name)
                        continue

                    success = installer.install_component(
                        component_name,
                        component_data,
                        components_data, # Passa todos os dados para checagem de dependência
                        installed_in_session
                    )
                    if not success:
                        logger.error(f"Falha geral ao instalar o componente '{component_name}'.")
                        failed_components.append(component_name)
                else:
                    logger.error(f"Componente '{component_name}' não encontrado na configuração.")
                    failed_components.append(component_name)

            # Resumo final
            if failed_components:
                logger.warning(f"Os seguintes componentes falharam na instalação: {', '.join(failed_components)}")
            else:
                logger.success("Todos os componentes solicitados foram processados com sucesso (ou já estavam instalados).")
            # Finaliza após ação CLI
            logger.info("Finalizando Environment Dev (CLI).")
            # log_manager.stop_session() # Movido para o finally principal

        elif args.dual_boot:
            logger.info("Iniciando assistente de dual boot Windows/Linux em modo automático...")
            try:
                # Verifica se o script do dual boot wrapper existe
                dual_boot_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dual_boot_wrapper.py")
                if os.path.exists(dual_boot_script):
                    logger.info(f"Executando script: {dual_boot_script}")
                    # Inicia diretamente em modo automático (comportamento padrão sem argumentos)
                    subprocess.Popen([sys.executable, dual_boot_script])
                    logger.info("Assistente de dual boot iniciado com sucesso.")
                else:
                    logger.error(f"Script do assistente de dual boot não encontrado: {dual_boot_script}")
                    logger.info("Tentando instalar os componentes necessários para dual boot...")

                    dual_boot_components = ["Grub2Win", "DualBootPartitionManager", "GloverWindows"]
                    installed_in_session = set()

                    for component_name in dual_boot_components:
                        if component_name in components_data:
                            logger.info(f"Instalando componente: {component_name}")
                            installer.install_component(
                                component_name,
                                components_data[component_name],
                                components_data,
                                installed_in_session
                            )

                    logger.info("Componentes para dual boot instalados. Por favor, execute o assistente novamente.")
            except Exception as e:
                logger.error(f"Erro ao iniciar o assistente de dual boot: {e}")

            # Finaliza após ação CLI
            logger.info("Finalizando Environment Dev (CLI).")
            # log_manager.stop_session() # Movido para o finally principal

        else:
            # Nenhuma ação CLI especificada, verifica se deve iniciar a GUI
            if args.no_gui:
                logger.info("Nenhuma ação CLI especificada e --no-gui presente. Use --help para ver as opções.")
                logger.info("Finalizando Environment Dev (CLI).")
                # log_manager.stop_session() # Movido para o finally principal
            elif args.gui or not any([args.check_env, args.list, args.install, args.dual_boot, args.no_gui]):
                # Inicia a GUI se --gui estiver presente ou se nenhuma ação CLI foi especificada
                logger.info("Iniciando interface gráfica (GUI)...")
                # A configuração de logging será gerenciada pela GUI a partir daqui

                # Tenta usar PyQt5 primeiro, depois Tkinter como fallback
                gui_started = False
                
                # Tentativa 1: Enhanced Dashboard (Primary)
                try:
                    from env_dev.gui.enhanced_dashboard import main as enhanced_main
                    logger.info("Usando Enhanced Dashboard com feedback em tempo real...")
                    enhanced_main(components_data)
                    gui_started = True
                    logger.info("Enhanced Dashboard fechado normalmente.")
                except ImportError as enhanced_error:
                    logger.warning(f"Enhanced Dashboard não disponível: {enhanced_error}. Tentando PyQt5...")
                except Exception as enhanced_error:
                    logger.error(f"Erro no Enhanced Dashboard: {enhanced_error}. Tentando PyQt5...")
                
                # Tentativa 2: PyQt5 (Fallback)
                if not gui_started:
                    try:
                        from env_dev.gui.app_gui_qt import main as qt_main, PYQT_AVAILABLE
                        if PYQT_AVAILABLE:
                            logger.info("Usando interface PyQt5...")
                            qt_main(components_data)
                            gui_started = True
                            logger.info("Interface PyQt5 fechada normalmente.")
                        else:
                            logger.warning("PyQt5 não está disponível, tentando Tkinter original...")
                    except ImportError as qt_error:
                        logger.warning(f"PyQt5 não disponível: {qt_error}. Tentando Tkinter original...")
                    except Exception as qt_error:
                        logger.error(f"Erro na interface PyQt5: {qt_error}. Tentando Tkinter original...")
                
                # Tentativa 3: Tkinter Original (Final Fallback)
                if not gui_started:
                    try: # Inner try for GUI
                        # Importa e cria a aplicação GUI Tkinter original
                        logger.info("Tentando inicializar a classe AppGUI (Tkinter original)...")
                        # Registra informações sobre o ambiente
                        logger.info(f"Diretório atual: {os.getcwd()}")
                        logger.info(f"Python path: {sys.path}")
                        logger.info(f"Argumentos: {sys.argv}")

                        # Verifica se a classe AppGUI está disponível
                        logger.info(f"AppGUI importada de: {AppGUI.__module__}")

                        # Inicializa a GUI
                        app = AppGUI(components_data)
                        logger.info("Instância AppGUI (Tkinter original) criada com sucesso")

                        # Inicia o loop principal
                        logger.info("Iniciando mainloop da interface gráfica (Tkinter original)...")
                        app.mainloop()

                        # O log de finalização será feito pela própria GUI (se ela fechar normalmente)
                        logger.info("Interface gráfica (Tkinter original) fechada normalmente.")
                        gui_started = True
                    except ImportError as ie:
                        logger.error(f"Erro ao importar módulos da GUI: {ie}")
                        traceback.print_exc()
                        # log_manager.stop_session() # Movido para o finally principal
                    except Exception as e:
                        # Loga qualquer exceção que ocorra durante a inicialização ou execução da GUI
                        logger.exception(f"Erro fatal na interface gráfica: {e}")
                        # Imprime o traceback no console para garantir visibilidade
                        print("--- TRACEBACK DO ERRO FATAL DA GUI ---", file=sys.stderr)
                        traceback.print_exc()
                        print("------------------------------------", file=sys.stderr)
                        # Tenta exibir um erro para o usuário se possível
                        try:
                            import tkinter as tk
                            from tkinter import messagebox
                            root = tk.Tk()
                            root.withdraw() # Esconde a janela principal do Tkinter
                            messagebox.showerror("Erro Fatal da GUI", f"Ocorreu um erro inesperado na interface gráfica.\nVerifique o arquivo 'logs/gui_initialization.log' para detalhes.\n\nErro: {e}")
                            root.destroy()
                        except Exception as tk_error:
                            print(f"AVISO: Não foi possível exibir a caixa de diálogo de erro Tkinter: {tk_error}")
                # finally: # Inner finally removido, tratado pelo finally principal
                #      log_manager.stop_session()

    # Outer except, aligned with the outer try (line 81)
    except Exception as main_exc: # CAPTURA QUALQUER ERRO EM main()
        print(f"--- ERRO FATAL CAPTURADO EM main() ---", file=sys.stderr)
        traceback.print_exc()
        print(f"------------------------------------", file=sys.stderr)
    # Outer finally, aligned with the outer try (line 81)
    finally:
        print("DEBUG: main.py main() finally block reached", file=sys.stderr)
        # Garante que a sessão de log seja sempre encerrada, independentemente do caminho ou erros
        # Verifica se log_manager existe antes de parar, caso a configuração inicial falhe
        if 'log_manager' in locals() and log_manager:
             log_manager.stop_session()

if __name__ == "__main__":
    # Garante que o diretório de trabalho seja o do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()