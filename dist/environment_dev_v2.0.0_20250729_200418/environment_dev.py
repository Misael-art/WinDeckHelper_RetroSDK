#!/usr/bin/env python3
"""
Environment Dev - Script de inicialização

Este script simplifica a execução do Environment Dev a partir da raiz do projeto.
Ele simplesmente redireciona para o módulo principal em env_dev/main.py.
"""

import os
import sys
import ctypes
import traceback
import subprocess
import time
import shutil
import logging

# Configuração de logging detalhado para depuração
DEBUG_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_trace.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_LOG_FILE, mode='w'),
        logging.StreamHandler()
    ]
)
debug_logger = logging.getLogger('debug')

def is_admin():
    """Verifica se o script está sendo executado como administrador no Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def request_elevation(args=None):
    """
    Solicita elevação de privilégios e aguarda a conclusão do processo elevado.

    Args:
        args: Lista de argumentos a serem passados para o processo elevado.
              Se None, usa sys.argv.

    Returns:
        int: Código de saída do processo elevado, ou -1 em caso de falha.
    """
    if args is None:
        args = sys.argv

    # Adiciona flag para evitar loop infinito de elevação
    if "--elevated" not in args:
        args = args + ["--elevated"]

    try:
        # Prepara o comando com argumentos corretamente escapados
        cmd_line = [sys.executable] + args

        # Adiciona impressão para depuração
        print(f"Solicitando elevação de privilégios para: {' '.join(cmd_line)}")

        # Usa ctypes para chamar ShellExecute diretamente, que mantém a GUI visível
        # em vez de usar subprocess com Start-Process
        cmd = f'"{sys.executable}" {" ".join(args)}'
        print(f"Comando para elevação: {cmd}")

        import ctypes
        import win32con  # Requer a biblioteca pywin32
        try:
            # Tenta importar pywin32
            shellExecute = ctypes.windll.shell32.ShellExecuteW
            result = shellExecute(None, "runas", sys.executable, " ".join(args), None, 1)

            # ShellExecute retorna um valor > 32 se bem-sucedido
            if result > 32:
                print("Elevação iniciada com sucesso via ShellExecute")
                # Aguarda um momento para o processo iniciar
                time.sleep(2)
                return 0
            else:
                print(f"ShellExecute falhou com código: {result}")
                # Tenta o método alternativo se o ShellExecute falhar
                raise Exception("ShellExecute falhou")

        except Exception as shell_error:
            print(f"Falha ao usar ShellExecute: {shell_error}. Tentando método alternativo...")
            # Método alternativo usando subprocess
            return_code = subprocess.call(['powershell', 'Start-Process',
                                        f'"{sys.executable}"',
                                        '-ArgumentList',
                                        f'"{" ".join(args)}"',
                                        '-Verb', 'runas'])
            print(f"Resultado da elevação alternativa: código de retorno {return_code}")
            return return_code

    except Exception as e:
        print(f"Falha ao solicitar elevação: {e}")
        traceback.print_exc()
        return -1

def validate_yaml_files():
    """
    Verifica e corrige arquivos YAML do projeto antes de iniciar.

    Returns:
        bool: True se todos os arquivos estão válidos (ou foram corrigidos), False caso contrário
    """
    # Adiciona o diretório do projeto ao path para que os imports funcionem
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)

    # Configura o Python para encontrar os módulos no diretório env_dev
    env_dev_dir = os.path.join(script_dir, 'env_dev')
    if env_dev_dir not in sys.path:
        sys.path.insert(0, env_dev_dir)

    # Verifica se o validador existe
    try:
        from env_dev.utils.yaml_validator import validate_and_fix_components_file

        # Valida e corrige o arquivo components.yaml
        components_file = os.path.join(env_dev_dir, 'components.yaml')
        success = validate_and_fix_components_file(components_file)

        if not success:
            print("AVISO: Não foi possível corrigir automaticamente o arquivo components.yaml.")
            print("O programa pode não funcionar corretamente. Considere corrigir manualmente o arquivo.")

            # Opção para o usuário continuar ou não
            try:
                response = input("Deseja continuar mesmo assim? (S/N): ")
                if response.upper() != 'S':
                    print("Programa encerrado pelo usuário.")
                    return False
            except Exception:
                # Se não conseguir pedir ao usuário (ex: em ambiente sem interatividade),
                # continua de qualquer forma
                pass

        return True

    except ImportError as e:
        print(f"ERRO: Não foi possível importar o validador YAML: {e}")
        return True  # Continua mesmo sem validação
    except Exception as e:
        print(f"ERRO ao validar arquivos YAML: {e}")
        traceback.print_exc()
        return True  # Continua mesmo com erro, para não impedir uso

# Importa main diretamente para execução no mesmo processo
try:
    from env_dev import main as env_dev_main
except ImportError as e:
    print(f"ERRO CRÍTICO: Falha ao importar env_dev.main: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

def main_direct_exec(): # Renomeia a função original
    """
    Função principal que inicia o Environment Dev
    """
    debug_logger.info("=== Iniciando função main() do environment_dev.py ===")
    debug_logger.info(f"Argumentos recebidos: {sys.argv}")
    debug_logger.info(f"Executando como administrador: {is_admin()}")

    try:
        # Valida arquivos YAML antes de iniciar
        debug_logger.info("Validando arquivos YAML...")
        if not validate_yaml_files():
            debug_logger.error("Falha na validação de arquivos YAML. Abortando.")
            return

        # Adiciona o diretório do projeto ao path para que os imports funcionem
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
        debug_logger.info(f"Diretório do script: {script_dir}")

        # NÃO muda o diretório de trabalho
        debug_logger.info(f"Diretório de trabalho atual: {os.getcwd()}")
        debug_logger.info(f"Argumentos do script: {sys.argv}")
        debug_logger.info(f"Python path: {sys.path}")

        # Chama a função main de env_dev.main diretamente
        try:
            debug_logger.info("Chamando env_dev_main.main() diretamente...")
            # Simula argumentos (força GUI para teste)
            # Precisamos garantir que parse_arguments() em main.py receba os args corretos
            original_argv = sys.argv
            sys.argv = [sys.argv[0], '--gui'] # Simula a chamada com --gui
            debug_logger.info(f"Simulando sys.argv como: {sys.argv}")

            env_dev_main.main() # Chama a função importada

            debug_logger.info("env_dev_main.main() concluído.")
            sys.argv = original_argv # Restaura argv original
        except Exception as e:
            debug_logger.error(f"Erro ao chamar env_dev_main.main(): {e}")
            traceback.print_exc()
            print(f"Erro ao chamar env_dev_main.main(): {e}", file=sys.stderr)
        finally:
            if 'original_argv' in locals():
                 sys.argv = original_argv # Garante restauração mesmo em caso de erro

    except Exception as e:
        print(f"ERRO não tratado: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Configura saída para UTF-8 para evitar problemas com caracteres especiais
    # Removida a configuração de stdout que estava causando problemas

    print(f"Iniciando Environment Dev (Execução Direta) a partir de: {os.path.abspath(__file__)}")
    print(f"Argumentos recebidos: {sys.argv}")
    print(f"Sistema: {sys.platform}")

    # Executa diretamente a função main_direct_exec SEM elevação para depuração
    print("Executando main_direct_exec() diretamente para depuração...")
    main_direct_exec()

    # Mantém a janela aberta após a execução
    print("\nExecução concluída.")
    input("Pressione ENTER para fechar...")