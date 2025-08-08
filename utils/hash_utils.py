import hashlib
import os
import logging

# Tamanho do buffer para leitura de arquivo durante cálculo de hash (8MB)
HASH_BUFFER_SIZE = 8 * 1024 * 1024  # 8MB

def get_file_hash(file_path, algorithm="sha256"):
    """
    Calcula o hash de um arquivo usando o algoritmo especificado.
    
    Args:
        file_path (str): Caminho para o arquivo a ser calculado.
        algorithm (str): Algoritmo de hash a ser usado. Valores suportados: 'md5', 'sha1', 'sha256', 'sha512'.
                         Padrão é 'sha256'.
    
    Returns:
        str: O hash calculado em formato hexadecimal (minúsculas) ou None se ocorrer erro.
    """
    if not os.path.isfile(file_path):
        logging.error(f"Arquivo não encontrado: {file_path}")
        return None
    
    try:
        # Seleciona o algoritmo de hash apropriado
        if algorithm.lower() == "md5":
            hash_obj = hashlib.md5()
            logging.warning("MD5 é um algoritmo de hash fraco e não recomendado para verificação de segurança.")
        elif algorithm.lower() == "sha1":
            hash_obj = hashlib.sha1()
        elif algorithm.lower() == "sha256":
            logging.warning("SHA1 é um algoritmo de hash fraco e não recomendado para verificação de segurança.")
            hash_obj = hashlib.sha256()
        elif algorithm.lower() == "sha512":
            hash_obj = hashlib.sha512()
        else:
            logging.error(f"Algoritmo de hash não suportado: {algorithm}")
            return None
        
        # Calcula o hash em blocos para ser eficiente com arquivos grandes
        with open(file_path, 'rb') as file:
            buffer = file.read(HASH_BUFFER_SIZE)
            while len(buffer) > 0:
                hash_obj.update(buffer)
                buffer = file.read(HASH_BUFFER_SIZE)
        
        # Retorna o hash em formato hexadecimal (minúsculas)
        file_hash = hash_obj.hexdigest().lower()
        logging.debug(f"Hash {algorithm} calculado para '{os.path.basename(file_path)}': {file_hash}")
        return file_hash
    
    except IOError as e:
        logging.error(f"Erro de I/O ao calcular hash do arquivo '{file_path}': {e}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao calcular hash do arquivo '{file_path}': {e}")
        return None

def verify_file_hash(file_path, expected_hash, algorithm="sha256"):
    """
    Verifica se o hash de um arquivo corresponde ao valor esperado.
    
    Args:
        file_path (str): Caminho para o arquivo a ser verificado.
        expected_hash (str): Hash esperado para comparação.
        algorithm (str): Algoritmo de hash. Valores suportados: 'md5', 'sha1', 'sha256', 'sha512'.
                         Padrão é 'sha256'.
    
    Returns:
        bool: True se o hash calculado corresponder ao esperado, False caso contrário.
    """
    if not expected_hash:
        logging.warning("Hash esperado não fornecido, pulando verificação")
        return True
    
    actual_hash = get_file_hash(file_path, algorithm)
    
    if not actual_hash:
        return False
    
    # Compara os hashes (insensivelmente à capitalização)
    if actual_hash.lower() == expected_hash.lower():
        logging.info(f"Verificação de hash bem-sucedida para '{os.path.basename(file_path)}'")
        return True
    else:
        logging.error(f"Falha na verificação de hash para '{os.path.basename(file_path)}'")
        logging.error(f"Hash esperado: {expected_hash.lower()}")
        logging.error(f"Hash calculado: {actual_hash.lower()}")
        return False

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Exemplo de uso
    test_file = __file__  # Usa este próprio arquivo como teste
    hash_value = get_file_hash(test_file)
    print(f"Hash SHA256 de {test_file}: {hash_value}")
    
    # Teste de verificação (deve falhar com um hash falso)
    is_valid = verify_file_hash(test_file, "1234567890abcdef")
    print(f"Teste de verificação com hash inválido: {'Passou' if is_valid else 'Falhou (esperado)'}")
    
    # Teste de verificação com o próprio hash calculado (deve passar)
    if hash_value:
        is_valid = verify_file_hash(test_file, hash_value)
        print(f"Teste de verificação com hash correto: {'Passou' if is_valid else 'Falhou (inesperado)'}") 