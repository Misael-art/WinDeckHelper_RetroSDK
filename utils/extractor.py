import subprocess
import logging
import os
import shutil

# Tenta encontrar o executável do 7-Zip
SEVEN_ZIP_PATH = None
possible_paths = [
    os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "7-Zip", "7z.exe"),
    os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "7-Zip", "7z.exe"),
    "7z" # Tenta encontrar no PATH
]
for path in possible_paths:
    if shutil.which(path): # shutil.which verifica no PATH e se o arquivo existe
        SEVEN_ZIP_PATH = path
        break

def is_7zip_available():
    """Verifica se o executável do 7-Zip foi encontrado."""
    return SEVEN_ZIP_PATH is not None

def extract_archive(archive_path, destination_path, extract_subdir=None):
    """
    Extrai um arquivo compactado usando 7-Zip.

    Args:
        archive_path (str): Caminho para o arquivo compactado.
        destination_path (str): Diretório onde o conteúdo será extraído.
        extract_subdir (str, optional): Subdiretório dentro do arquivo a ser extraído.

    Returns:
        bool: True se a extração for bem-sucedida, False caso contrário.
    """
    if not is_7zip_available():
        logging.error("Executável do 7-Zip não encontrado. Verifique a instalação e o PATH.")
        return False

    if not os.path.exists(archive_path):
        logging.error(f"Arquivo de origem não encontrado: {archive_path}")
        return False

    # Garante que o diretório de destino exista
    os.makedirs(destination_path, exist_ok=True)

    # Comando do 7-Zip para extrair: 7z x [archive_path] -o[destination_path] -y
    # x: extrai com caminhos completos
    # -o: especifica o diretório de saída (sem espaço entre -o e o caminho)
    # -y: assume 'Sim' para todas as perguntas (sobrescrever, etc.)
    command = [
        SEVEN_ZIP_PATH,
        'x',
        archive_path,
        f'-o{destination_path}',
        '-y'
    ]

    # Se um subdiretório específico foi solicitado, adiciona-o ao comando
    if extract_subdir:
        logging.info(f"Extraindo apenas subdiretório: {extract_subdir}")
        command.append(f"{extract_subdir}\\*")

    logging.info(f"Extraindo '{os.path.basename(archive_path)}' para '{destination_path}'...")
    logging.debug(f"Executando comando: {' '.join(command)}")

    try:
        # Usa subprocess.run para maior controle e captura de saída/erros
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')

        if result.returncode == 0:
            logging.info("Extração concluída com sucesso.")
            logging.debug(f"Saída do 7-Zip:\n{result.stdout}")
            return True
        else:
            logging.error(f"Erro durante a extração (Código: {result.returncode}).")
            logging.error(f"Saída do 7-Zip (stdout):\n{result.stdout}")
            logging.error(f"Saída de erro do 7-Zip (stderr):\n{result.stderr}")
            return False

    except FileNotFoundError:
        logging.error(f"Erro: Comando '{SEVEN_ZIP_PATH}' não encontrado. Verifique a instalação do 7-Zip e o PATH.")
        return False
    except subprocess.SubprocessError as e:
        logging.error(f"Erro ao executar o processo de extração: {e}")
        return False
    except Exception as e:
        logging.error(f"Erro inesperado durante a extração: {e}")
        return False

if __name__ == '__main__':
    # Teste rápido (requer um arquivo .zip ou .7z e 7-Zip instalado)
    logging.basicConfig(level=logging.INFO)

    if not is_7zip_available():
        print("7-Zip não encontrado. Teste de extração não pode ser executado.")
    else:
        print(f"7-Zip encontrado em: {SEVEN_ZIP_PATH}")
        # Crie um arquivo zip de teste manualmente ou use um existente
        test_archive = "test_archive.zip"
        test_extract_dir = "temp_extract"
        if not os.path.exists(test_archive):
             # Cria um zip simples para teste se não existir
             import zipfile
             try:
                 with zipfile.ZipFile(test_archive, 'w') as zf:
                     zf.writestr("test.txt", "Este é um arquivo de teste.")
                 print(f"Arquivo de teste '{test_archive}' criado.")
             except Exception as e:
                 print(f"Falha ao criar arquivo de teste '{test_archive}': {e}")
                 test_archive = None # Impede a execução do teste

        if test_archive and os.path.exists(test_archive):
            print(f"\nTestando extração de '{test_archive}' para '{test_extract_dir}'...")
            success = extract_archive(test_archive, test_extract_dir)
            if success:
                print("Extração de teste concluída com sucesso.")
                # Verifica se o arquivo foi extraído
                if os.path.exists(os.path.join(test_extract_dir, "test.txt")):
                    print("Arquivo 'test.txt' encontrado no diretório de extração.")
                else:
                    print("AVISO: Arquivo 'test.txt' não encontrado após extração.")
                # Limpa
                # shutil.rmtree(test_extract_dir, ignore_errors=True)
                # os.remove(test_archive)
            else:
                print("Extração de teste falhou.")
        else:
            print(f"Arquivo de teste '{test_archive}' não encontrado ou não pôde ser criado. Pulando teste de extração.")