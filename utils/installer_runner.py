import subprocess
import logging
import os
import sys
import time # Importar time para logs de timeout

# Timeout padrão em segundos (ex: 30 minutos)
DEFAULT_INSTALLER_TIMEOUT = 1800

def run_installer(installer_path, install_args=None, timeout=DEFAULT_INSTALLER_TIMEOUT):
    """
    Executa um instalador (.exe ou .msi) com argumentos opcionais e timeout.

    Args:
        installer_path (str): Caminho completo para o arquivo do instalador.
        install_args (list or str, optional): Argumentos a serem passados para o instalador.
                                             Se for uma string, será dividida em uma lista.
                                             Defaults to None.
        timeout (int, optional): Tempo máximo em segundos para esperar a conclusão do instalador.
                                 Defaults to DEFAULT_INSTALLER_TIMEOUT.

    Returns:
        bool: True se o instalador executar e retornar código 0 ou 3010, False caso contrário ou timeout.
    """
    if not os.path.exists(installer_path):
        logging.error(f"Instalador não encontrado: {installer_path}")
        return False

    command = []
    is_msi = installer_path.lower().endswith('.msi')

    if is_msi:
        # Para MSI, usamos msiexec
        command.append('msiexec.exe')
        command.append('/i') # Opção para instalar
        # Não adicione aspas ao caminho, o subprocess.run com shell=False lida com espaços corretamente
        command.append(installer_path) # Caminho do MSI sem aspas adicionais
        # Argumentos padrão para instalação silenciosa de MSI
        default_msi_args = ['/quiet', '/norestart']
        if install_args:
            if isinstance(install_args, str):
                command.extend(install_args.split())
            else:
                command.extend(install_args)
            # Garante que os argumentos silenciosos padrão estejam presentes se não fornecidos
            if '/quiet' not in command and '/qn' not in command:
                 command.append('/quiet')
            if '/norestart' not in command:
                 command.append('/norestart')
        else:
            command.extend(default_msi_args)
    else:
        # Para EXE, executamos diretamente
        # Não adicione aspas ao caminho, o subprocess.run com shell=False lida com espaços corretamente
        command.append(installer_path)
        if install_args:
            if isinstance(install_args, str):
                command.extend(install_args.split())
            else:
                command.extend(install_args)

    logging.info(f"Executando instalador: {' '.join(command)}")

    try:
        # shell=True pode ser necessário para msiexec em alguns casos, mas tentamos sem primeiro
        # Usamos subprocess.run para esperar a conclusão, agora com timeout
        start_time = time.time()
        logging.info(f"Iniciando instalador com timeout de {timeout} segundos...")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False, # Não lança exceção em códigos de retorno != 0
            encoding='utf-8',
            errors='ignore',
            shell=False, # Sempre usar shell=False por segurança
            timeout=timeout # Adiciona o timeout
        ) # Parêntese fechado aqui
        end_time = time.time()
        logging.info(f"Instalador concluído em {end_time - start_time:.2f} segundos.")

        # Verifica o código de retorno APÓS a execução bem-sucedida (sem timeout)
        if result.returncode == 0 or (is_msi and result.returncode == 3010): # 3010 = Sucesso, reinicialização necessária
            logging.info(f"Instalador '{os.path.basename(installer_path)}' finalizado com sucesso (Código: {result.returncode}).")
            if result.returncode == 3010:
                 logging.warning("O instalador solicitou uma reinicialização do sistema.")
            logging.debug(f"Saída do instalador (stdout):\n{result.stdout}")
            return True
        else:
            logging.error(f"Erro durante a execução do instalador '{os.path.basename(installer_path)}' (Código: {result.returncode}).")
            logging.error(f"Saída do instalador (stdout):\n{result.stdout}")
            logging.error(f"Saída de erro do instalador (stderr):\n{result.stderr}")
            return False

    # Bloco except movido para o nível correto
    except subprocess.TimeoutExpired:
        logging.error(f"Erro: Timeout ({timeout}s) excedido durante a execução do instalador '{os.path.basename(installer_path)}'.")
        # Considerar se o processo deve ser terminado aqui (process.kill())
        # Por enquanto, apenas reporta o erro e retorna False
        return False
    except FileNotFoundError:
        logging.error(f"Erro: Comando ou instalador '{command[0]}' não encontrado.")
        return False
    except subprocess.SubprocessError as e:
        logging.error(f"Erro ao executar o processo do instalador: {e}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado durante a execução do instalador: {e}")
        return False

if __name__ == '__main__':
    # Teste rápido (requer um instalador .exe ou .msi)
    # CUIDADO: Este teste tentará executar um instalador real.
    # Use um instalador seguro e conhecido para teste, ou comente esta seção.

    logging.basicConfig(level=logging.INFO)

    # Exemplo com um instalador EXE (Notepad++) - Baixe-o primeiro se for testar
    test_exe_path = "temp_download/npp_installer.exe" # Supondo que foi baixado aqui
    test_exe_args = "/S" # Argumento silencioso

    # Exemplo com um instalador MSI (CMake) - Baixe-o primeiro se for testar
    test_msi_path = "temp_download/cmake_installer.msi" # Supondo que foi baixado aqui
    test_msi_args = "/quiet /norestart ADD_CMAKE_TO_PATH=System"

    print("\n--- Teste com Instalador EXE ---")
    if os.path.exists(test_exe_path):
        print(f"Testando execução de: {test_exe_path} com args: {test_exe_args}")
        success_exe = run_installer(test_exe_path, test_exe_args)
        print(f"Resultado do teste EXE: {'Sucesso' if success_exe else 'Falha'}")
    else:
        print(f"Instalador EXE de teste '{test_exe_path}' não encontrado. Pulando teste.")

    print("\n--- Teste com Instalador MSI ---")
    if os.path.exists(test_msi_path):
        print(f"Testando execução de: {test_msi_path} com args: {test_msi_args}")
        success_msi = run_installer(test_msi_path, test_msi_args)
        print(f"Resultado do teste MSI: {'Sucesso' if success_msi else 'Falha'}")
    else:
        print(f"Instalador MSI de teste '{test_msi_path}' não encontrado. Pulando teste.")

    # Lembre-se de limpar os arquivos baixados e desinstalar os programas se necessário após o teste.