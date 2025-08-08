#!/usr/bin/env python3
"""
Mirror Manager para Environment Dev

Este módulo gerencia múltiplas URLs (mirrors) para download de componentes.
Quando uma URL principal falha, o sistema tenta automaticamente URLs alternativas.
"""

import logging
import random
import time
import os
import json
from typing import List, Dict, Tuple, Optional, Any, Union
from pathlib import Path
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from .error_handler import (
    EnvDevError, ErrorCategory, ErrorSeverity,
    network_error, config_error, handle_exception
)
from .network import test_internet_connection

# Configuração do logger
logger = logging.getLogger(__name__)

# Caminho para o arquivo de configuração de mirrors
DEFAULT_MIRRORS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "config", 
    "mirrors.json"
)

# Lista de mirrors públicos confiáveis para serviços comuns
DEFAULT_MIRRORS = {
    # GitHub
    "github.com": [
        "https://github.com",
        "https://raw.githubusercontent.com",
        "https://mirror.ghproxy.com/https://github.com"
    ],
    # SourceForge
    "sourceforge.net": [
        "https://sourceforge.net",
        "https://downloads.sourceforge.net",
        "https://master.dl.sourceforge.net",
        "https://versaweb.dl.sourceforge.net"
    ],
    # Outros servidores populares
    "download.savannah.gnu.org": [
        "https://download.savannah.gnu.org",
        "https://ftp.gnu.org/gnu",
        "https://mirrors.kernel.org/gnu"
    ],
    # Servidores Python
    "pypi.org": [
        "https://pypi.org/simple",
        "https://pypi.python.org/simple",
        "https://files.pythonhosted.org"
    ]
}

def _extract_domain(url: str) -> str:
    """
    Extrai o domínio de uma URL.
    
    Args:
        url: URL para analisar
        
    Returns:
        Domínio extraído da URL
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception as e:
        logger.warning(f"Não foi possível extrair domínio de {url}: {e}")
        # Fallback: tenta extrair manualmente
        if "://" in url:
            try:
                domain = url.split("://")[1].split("/")[0]
                return domain
            except Exception:
                pass
        return ""

def load_mirrors_config(config_file: str = DEFAULT_MIRRORS_FILE) -> Dict[str, List[str]]:
    """
    Carrega a configuração de mirrors do arquivo JSON.
    
    Args:
        config_file: Caminho para o arquivo de configuração
        
    Returns:
        Dicionário com domínios como chaves e listas de mirrors como valores
    """
    mirrors = DEFAULT_MIRRORS.copy()
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                user_mirrors = json.load(f)
                
                # Mescla os mirrors definidos pelo usuário com os padrões
                for domain, urls in user_mirrors.items():
                    if domain in mirrors:
                        # Adiciona apenas URLs que ainda não existem
                        mirrors[domain] = list(set(mirrors[domain] + urls))
                    else:
                        mirrors[domain] = urls
            
            logger.info(f"Configuração de mirrors carregada de {config_file}")
        else:
            logger.info(f"Arquivo de configuração de mirrors não encontrado: {config_file}. Usando padrões.")
    except Exception as e:
        err = config_error(
            f"Erro ao carregar configuração de mirrors: {e}",
            severity=ErrorSeverity.WARNING,
            original_error=e
        )
        err.log()
    
    return mirrors

def save_mirrors_config(mirrors: Dict[str, List[str]], config_file: str = DEFAULT_MIRRORS_FILE) -> bool:
    """
    Salva a configuração de mirrors em um arquivo JSON.
    
    Args:
        mirrors: Dicionário de mirrors para salvar
        config_file: Caminho para o arquivo de configuração
        
    Returns:
        True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(mirrors, f, indent=2)
            
        logger.info(f"Configuração de mirrors salva em {config_file}")
        return True
    except Exception as e:
        err = handle_exception(
            e,
            message=f"Erro ao salvar configuração de mirrors em {config_file}",
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.WARNING
        )
        err.log()
        return False

def generate_alternative_urls(url: str, mirrors_config: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    Gera URLs alternativas para uma URL principal com base na configuração de mirrors.
    
    Args:
        url: URL principal
        mirrors_config: Configuração de mirrors (opcional)
        
    Returns:
        Lista de URLs alternativas, incluindo a URL original como primeiro item
    """
    if mirrors_config is None:
        mirrors_config = load_mirrors_config()
    
    domain = _extract_domain(url)
    alt_urls = [url]  # A URL original é sempre a primeira opção
    
    if not domain:
        logger.warning(f"Não foi possível determinar o domínio para {url}")
        return alt_urls
    
    # Encontra mirrors para o domínio
    for mirror_domain, mirror_urls in mirrors_config.items():
        if mirror_domain in domain:
            # Encontrou um conjunto de mirrors para este domínio
            for mirror_base in mirror_urls:
                if mirror_base in url:
                    # Pula se for a mesma base da URL original
                    continue
                
                try:
                    # Substitui o domínio na URL original
                    alt_url = url.replace(f"https://{domain}", mirror_base)
                    alt_url = alt_url.replace(f"http://{domain}", mirror_base)
                    
                    # Evita duplicatas
                    if alt_url != url and alt_url not in alt_urls:
                        alt_urls.append(alt_url)
                except Exception as e:
                    logger.warning(f"Erro ao gerar URL alternativa: {e}")
    
    # Se encontramos alternativas, log informativo
    if len(alt_urls) > 1:
        logger.info(f"Geradas {len(alt_urls)-1} URLs alternativas para {url}")
    
    return alt_urls

# Alias para compatibilidade com o nome da função mostrada aos usuários
get_alternative_urls = generate_alternative_urls

def check_url_availability(url: str, timeout: int = 5) -> bool:
    """
    Verifica se uma URL está disponível.
    
    Args:
        url: URL para verificar
        timeout: Timeout em segundos
        
    Returns:
        True se a URL estiver disponível, False caso contrário
    """
    import requests
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return 200 <= response.status_code < 400
    except Exception as e:
        logger.debug(f"URL {url} indisponível: {e}")
        return False

def find_best_mirror(url: str, mirrors_config: Optional[Dict[str, List[str]]] = None, 
                   timeout: int = 5) -> Tuple[str, List[str]]:
    """
    Encontra o melhor mirror disponível para uma URL.
    
    Args:
        url: URL principal
        mirrors_config: Configuração de mirrors (opcional)
        timeout: Timeout em segundos para verificação
        
    Returns:
        Tupla (melhor_url, todas_urls_alternativas)
    """
    # Verifica conexão com a internet primeiro
    if not test_internet_connection():
        logger.warning("Sem conexão com a internet. Usando URL original sem verificar mirrors.")
        return url, [url]
    
    # Gera URLs alternativas
    alt_urls = generate_alternative_urls(url, mirrors_config)
    
    # Se só temos a URL original, retorna imediatamente
    if len(alt_urls) == 1:
        return url, alt_urls
    
    # Verifica a URL original primeiro
    if check_url_availability(url, timeout):
        logger.info(f"URL original disponível: {url}")
        return url, alt_urls
    
    # Tenta cada URL alternativa
    for alt_url in alt_urls[1:]:  # Pula a primeira que é a original
        if check_url_availability(alt_url, timeout):
            logger.info(f"URL alternativa disponível: {alt_url}")
            return alt_url, alt_urls
    
    # Se nenhuma alternativa funcionar, retorna a URL original
    logger.warning(f"Nenhum mirror disponível para {url}. Usando URL original.")
    return url, alt_urls

def register_mirror(domain: str, mirror_url: str, config_file: str = DEFAULT_MIRRORS_FILE) -> bool:
    """
    Registra um novo mirror para um domínio.
    
    Args:
        domain: Nome do domínio (ex: github.com)
        mirror_url: URL base do mirror
        config_file: Caminho para o arquivo de configuração
        
    Returns:
        True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        mirrors = load_mirrors_config(config_file)
        
        if domain in mirrors:
            if mirror_url not in mirrors[domain]:
                mirrors[domain].append(mirror_url)
                logger.info(f"Mirror {mirror_url} adicionado para {domain}")
            else:
                logger.info(f"Mirror {mirror_url} já existe para {domain}")
        else:
            mirrors[domain] = [mirror_url]
            logger.info(f"Novo domínio {domain} adicionado com mirror {mirror_url}")
        
        return save_mirrors_config(mirrors, config_file)
    except Exception as e:
        err = handle_exception(
            e,
            message=f"Erro ao registrar mirror {mirror_url} para {domain}",
            category=ErrorCategory.CONFIG,
            severity=ErrorSeverity.WARNING
        )
        err.log()
        return False

def remove_mirror(domain: str, mirror_url: str, config_file: str = DEFAULT_MIRRORS_FILE) -> bool:
    """
    Remove um mirror da configuração.
    
    Args:
        domain: Nome do domínio
        mirror_url: URL base do mirror a remover
        config_file: Caminho para o arquivo de configuração
        
    Returns:
        True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        mirrors = load_mirrors_config(config_file)
        
        if domain in mirrors and mirror_url in mirrors[domain]:
            mirrors[domain].remove(mirror_url)
            logger.info(f"Mirror {mirror_url} removido de {domain}")
            
            # Se não sobrou nenhum mirror, remove o domínio
            if not mirrors[domain]:
                del mirrors[domain]
                logger.info(f"Domínio {domain} removido por não ter mais mirrors")
            
            return save_mirrors_config(mirrors, config_file)
        else:
            logger.warning(f"Mirror {mirror_url} não encontrado para {domain}")
            return False
    except Exception as e:
        err = handle_exception(
            e,
            message=f"Erro ao remover mirror {mirror_url} para {domain}",
            category=ErrorCategory.CONFIG,
            severity=ErrorSeverity.WARNING
        )
        err.log()
        return False

def download_with_mirror_fallback(downloader_func, url: str, *args, **kwargs) -> Any:
    """
    Tenta baixar uma URL usando mirrors como fallback.
    
    Args:
        downloader_func: Função de download a ser usada (como download_file)
        url: URL principal para download
        *args, **kwargs: Argumentos adicionais para passar para a função de download
        
    Returns:
        Resultado da função de download
    """
    # Encontra o melhor mirror
    best_url, alt_urls = find_best_mirror(url)
    
    # Se o melhor é o original, tenta diretamente
    if best_url == url:
        return downloader_func(url, *args, **kwargs)
    
    # Adiciona um delay aleatório para evitar abusos de servidores
    time.sleep(random.uniform(0.5, 2.0))
    
    # Tenta com o melhor mirror
    try:
        logger.info(f"Tentando download com mirror: {best_url}")
        result = downloader_func(best_url, *args, **kwargs)
        if result:
            logger.info(f"Download bem-sucedido com mirror: {best_url}")
            return result
    except Exception as e:
        logger.warning(f"Falha no download com mirror {best_url}: {e}")
    
    # Se falhar com o melhor mirror, tenta os outros
    for alt_url in alt_urls:
        if alt_url == url or alt_url == best_url:
            continue
        
        # Adiciona um delay aleatório para evitar abusos de servidores
        time.sleep(random.uniform(1.0, 3.0))
        
        try:
            logger.info(f"Tentando download com mirror alternativo: {alt_url}")
            result = downloader_func(alt_url, *args, **kwargs)
            if result:
                logger.info(f"Download bem-sucedido com mirror alternativo: {alt_url}")
                return result
        except Exception as e:
            logger.warning(f"Falha no download com mirror alternativo {alt_url}: {e}")
    
    # Se todas as tentativas falharem, volta para a URL original
    # (no caso de mirrors temporariamente indisponíveis)
    logger.warning(f"Todas as tentativas com mirrors falharam. Voltando para URL original: {url}")
    return downloader_func(url, *args, **kwargs)

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Testes básicos
    test_url = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
    
    print(f"URLs alternativas para {test_url}:")
    alt_urls = get_alternative_urls(test_url)
    for url in alt_urls:
        print(f"- {url}")
    
    print("\nTestando disponibilidade...")
    best_url, all_urls = find_best_mirror(test_url)
    print(f"Melhor URL: {best_url}")