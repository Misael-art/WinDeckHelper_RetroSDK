import requests
import logging
from requests.exceptions import RequestException
import socket

def test_internet_connection(test_url="https://www.google.com", timeout=5):
    """
    Verifica se há conexão com a internet tentando acessar uma URL específica.

    Args:
        test_url (str): A URL para testar a conexão. Padrão é 'https://www.google.com'.
        timeout (int): Tempo limite em segundos para a requisição. Padrão é 5.

    Returns:
        bool: True se a conexão for bem-sucedida, False caso contrário.
    """
    logging.info(f"Verificando conexão com a internet via {test_url}")
    
    # Primeiro método: Tenta fazer uma requisição HTTP
    try:
        response = requests.get(test_url, timeout=timeout)
        if response.status_code == 200:
            logging.info("Conexão com a internet confirmada (via HTTP)")
            return True
    except RequestException as e:
        logging.warning(f"Erro na verificação HTTP da conexão com a internet: {e}")
        # Continua para o segundo método
    
    # Segundo método (fallback): Tenta resolver um nome de domínio
    try:
        # Tenta resolver o google.com (um servidor DNS confiável)
        socket.gethostbyname("google.com")
        logging.info("Conexão com a internet confirmada (via DNS)")
        return True
    except socket.error as e:
        logging.warning(f"Erro na verificação DNS da conexão com a internet: {e}")
    
    logging.error("Falha na verificação da conexão com a internet")
    return False

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Testa a função
    is_connected = test_internet_connection()
    print(f"Conectado à internet: {is_connected}")
    
    # Testa com uma URL inválida (deve falhar no primeiro método mas pode passar no segundo)
    is_connected_invalid = test_internet_connection("https://site-que-nao-existe-12345.com")
    print(f"Teste com URL inválida: {is_connected_invalid}") 