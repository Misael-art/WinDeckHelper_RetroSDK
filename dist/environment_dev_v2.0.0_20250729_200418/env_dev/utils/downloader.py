import requests
import logging
import os
import sys
import time
import random
import shutil
import tempfile
from contextlib import closing
from typing import Optional, Dict, Any, Tuple, List, Callable
from pathlib import Path

# Importa a função de verificação de hash implementada
from env_dev.utils.hash_utils import verify_file_hash, get_file_hash

# Importa o sistema de gestão de erros
from env_dev.utils.error_handler import (
    EnvDevError, ErrorCategory, ErrorSeverity,
    handle_exception, network_error, file_error
)

# Importa o gestor de mirrors
from env_dev.utils.mirror_manager import (
    find_best_mirror, generate_alternative_urls,
    download_with_mirror_fallback
)

# Importa o módulo de verificação de espaço em disco
from env_dev.utils.disk_space import (
    ensure_space_for_download, format_size, clean_temp_directory,
    clean_downloads_directory, suggest_cleanup_actions
)

DEFAULT_CHUNK_SIZE = 8192  # Tamanho do chunk para download em bytes
MAX_RETRIES = 3           # Número máximo de tentativas de download
RETRY_BACKOFF_FACTOR = 2  # Fator para backoff exponencial entre tentativas
DOWNLOAD_TIMEOUT = 60     # Timeout padrão para downloads (segundos)
USER_AGENT = "Environment-Dev-Installer/1.0"  # User-Agent para identificar nossos downloads

# Configuração do logger
logger = logging.getLogger(__name__)

def _print_progress(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', callback=None):
    """
    Exibe uma barra de progresso no console e opcionalmente notifica um callback.

    Args:
        iteration: Iteração atual
        total: Total de iterações
        prefix: Texto de prefixo
        suffix: Texto de sufixo
        decimals: Número de casas decimais para porcentagem
        length: Comprimento da barra
        fill: Caractere de preenchimento
        callback: Função opcional para receber atualizações de progresso (percent)
    """
    if total <= 0:
        return

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)

    # Exibe no console
    progress_line = f'\r{prefix} |{bar}| {percent}% {suffix}'
    sys.stdout.write(progress_line)
    sys.stdout.flush()

    # Também loga para registro
    percent_float = float(percent)
    if iteration == 0 or iteration == total or percent_float % 10 == 0:  # Loga a cada 10%
        logger.info(f"Progresso: {percent}% ({iteration}/{total})")

    # Notifica o callback se fornecido
    if callback is not None:
        try:
            callback(float(percent))
        except Exception as e:
            logger.warning(f"Erro ao chamar callback de progresso: {e}")

    if iteration == total:
        sys.stdout.write('\n')
        sys.stdout.flush()

def _get_download_headers() -> Dict[str, str]:
    """
    Retorna cabeçalhos HTTP padrão para download.

    Returns:
        Dicionário com cabeçalhos HTTP
    """
    return {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

def _verify_and_clean_temp_file(temp_path: str,
                               destination_path: str,
                               expected_hash: Optional[str] = None,
                               hash_algorithm: str = "sha256") -> bool:
    """
    Verifica o hash de um arquivo temporário e o move para o destino final se for válido.

    Args:
        temp_path: Caminho do arquivo temporário
        destination_path: Caminho de destino final
        expected_hash: Hash esperado para verificação
        hash_algorithm: Algoritmo de hash a ser usado

    Returns:
        True se a verificação e movimentação for bem-sucedida, False caso contrário
    """
    # Verifica o hash se for esperado
    if expected_hash:
        if not verify_file_hash(temp_path, expected_hash, hash_algorithm):
            logger.error(f"Falha na verificação de hash para '{os.path.basename(destination_path)}'")
            try:
                os.remove(temp_path)
            except OSError:
                pass
            return False

        logger.info(f"Verificação de hash bem-sucedida para '{os.path.basename(destination_path)}'")

    # Cria o diretório de destino se não existir
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Move o arquivo temporário para o destino final
    try:
        # Se o arquivo de destino já existir, o remove primeiro
        if os.path.exists(destination_path):
            os.remove(destination_path)

        shutil.move(temp_path, destination_path)
        logger.info(f"Arquivo movido com sucesso para '{destination_path}'")
        return True
    except (OSError, IOError) as e:
        logger.error(f"Erro ao mover arquivo de '{temp_path}' para '{destination_path}': {e}")
        return False

def download_to_temp(url: str,
                    expected_hash: Optional[str] = None,
                    hash_algorithm: str = "sha256",
                    timeout: int = DOWNLOAD_TIMEOUT,
                    retry_count: int = MAX_RETRIES,
                    show_progress: bool = True,
                    use_mirrors: bool = True,
                    progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, Optional[str]]:
    """
    Baixa um arquivo para um local temporário com retry automático.

    Args:
        url: URL do arquivo a ser baixado
        expected_hash: Hash esperado para verificação
        hash_algorithm: Algoritmo de hash a ser usado
        timeout: Timeout em segundos para o download
        retry_count: Número máximo de tentativas
        show_progress: Se deve mostrar barra de progresso
        use_mirrors: Se deve tentar usar mirrors em caso de falha
        progress_callback: Função opcional para atualizar a barra de progresso na GUI

    Returns:
        Tupla (sucesso, caminho_temporário) - caminho_temporário é None se falhar
    """
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, f"env_dev_download_{int(time.time())}_{random.randint(1000, 9999)}")

    headers = _get_download_headers()

    # Se usar mirrors está habilitado, obtém a melhor URL
    if use_mirrors:
        best_url, alt_urls = find_best_mirror(url)
        if best_url != url:
            logger.info(f"Usando mirror para download: {best_url} (original: {url})")
            url = best_url

    for attempt in range(retry_count):
        try:
            # Espera exponencial entre tentativas
            if attempt > 0:
                wait_time = RETRY_BACKOFF_FACTOR ** attempt
                logger.info(f"Tentativa {attempt+1}/{retry_count} após {wait_time:.2f}s")
                time.sleep(wait_time)

            logger.info(f"Download de '{url}' para arquivo temporário (tentativa {attempt+1}/{retry_count})")

            with closing(requests.get(url, stream=True, timeout=timeout, headers=headers)) as r:
                r.raise_for_status()  # Verifica erros HTTP

                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0

                if show_progress and total_size > 0:
                    _print_progress(0, total_size, prefix='Progresso:', suffix='Completo', length=50, callback=progress_callback)

                with open(temp_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                        if chunk:  # Filtra chunks de keep-alive
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if show_progress and total_size > 0:
                                _print_progress(downloaded_size, total_size, prefix='Progresso:', suffix='Completo', length=50, callback=progress_callback)

            logger.info(f"Download concluído: {downloaded_size} bytes")

            # Verifica o hash se fornecido
            if expected_hash:
                file_hash = get_file_hash(temp_file, hash_algorithm)
                if file_hash.lower() != expected_hash.lower():
                    logger.warning(f"Hash incorreto: esperado={expected_hash}, obtido={file_hash}")
                    # Em caso de hash inválido, tenta novamente
                    continue
                logger.info(f"Hash verificado: {file_hash}")

            # Se chegou aqui, o download foi concluído com sucesso
            return True, temp_file

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro de rede na tentativa {attempt+1}/{retry_count}: {str(e)}")

            # Limpa arquivo temporário incompleto
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError as e:
                    logger.debug(f"Erro ao remover arquivo temporário {temp_file}: {e}")

            # Se for a última tentativa e usar mirrors estiver habilitado, tenta com URLs alternativas
            if attempt == retry_count - 1 and use_mirrors:
                # Obtém URLs alternativas (se ainda não obteve)
                _, alt_urls = find_best_mirror(url)

                # Tenta usar uma URL alternativa (ignorando a primeira que é a URL original/melhor)
                for alt_url in alt_urls[1:]:
                    if alt_url == url:
                        continue

                    logger.info(f"Tentando URL alternativa: {alt_url}")
                    try:
                        # Delay para evitar sobrecarga
                        time.sleep(random.uniform(0.5, 2.0))

                        with closing(requests.get(alt_url, stream=True, timeout=timeout, headers=headers)) as r:
                            r.raise_for_status()

                            total_size = int(r.headers.get('content-length', 0))
                            downloaded_size = 0

                            if show_progress and total_size > 0:
                                _print_progress(0, total_size, prefix=f'Mirror:', suffix='Completo', length=50, callback=progress_callback)

                            with open(temp_file, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        if show_progress and total_size > 0:
                                            _print_progress(downloaded_size, total_size, prefix=f'Mirror:', suffix='Completo', length=50, callback=progress_callback)

                        logger.info(f"Download concluído via mirror: {downloaded_size} bytes")

                        # Verifica o hash se fornecido
                        if expected_hash:
                            file_hash = get_file_hash(temp_file, hash_algorithm)
                            if file_hash.lower() != expected_hash.lower():
                                logger.warning(f"Hash incorreto via mirror: esperado={expected_hash}, obtido={file_hash}")
                                # Continua tentando outros mirrors
                                continue
                            logger.info(f"Hash verificado via mirror: {file_hash}")

                        return True, temp_file

                    except Exception as mirror_err:
                        logger.warning(f"Falha no mirror {alt_url}: {mirror_err}")
                        # Limpa arquivo temporário incompleto
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except OSError as e:
                                logger.debug(f"Erro ao remover arquivo temporário {temp_file}: {e}")
                        # Continua para o próximo mirror

            # Se ainda chegou aqui, todos os mirrors falharam ou não foram usados
            if attempt == retry_count - 1:
                err = network_error(
                    f"Falha no download após {retry_count} tentativas: {url}",
                    original_error=e
                )
                err.log()
                return False, None

        except (IOError, OSError) as e:
            logger.error(f"Erro de I/O ao salvar arquivo temporário: {str(e)}")
            err = file_error(
                f"Erro ao salvar arquivo temporário durante download: {str(e)}",
                original_error=e
            )
            err.log()
            return False, None

    # Se chegou aqui, todas as tentativas falharam
    logger.error(f"Todas as {retry_count} tentativas de download falharam: {url}")
    return False, None

def download_file(url: str,
                 destination_path: str,
                 expected_hash: Optional[str] = None,
                 hash_algorithm: str = "sha256",
                 timeout: int = DOWNLOAD_TIMEOUT,
                 retry_count: int = MAX_RETRIES,
                 show_progress: bool = True,
                 force_download: bool = False,
                 use_mirrors: bool = True,
                 progress_callback: Optional[Callable[[float], None]] = None) -> bool:
    """
    Baixa um arquivo de uma URL para um caminho de destino com tratamento de erros robusto.

    Args:
        url: A URL do arquivo a ser baixado
        destination_path: O caminho completo onde salvar o arquivo
        expected_hash: Hash esperado para verificação
        hash_algorithm: Algoritmo de hash a ser usado
        timeout: Timeout em segundos para o download
        retry_count: Número máximo de tentativas
        show_progress: Se deve mostrar a barra de progresso
        force_download: Se deve baixar mesmo se o arquivo já existir
        use_mirrors: Se deve tentar usar mirrors em caso de falha
        progress_callback: Função opcional para atualizar a barra de progresso na GUI

    Returns:
        True se o download for bem-sucedido (e hash verificado, se aplicável), False caso contrário
    """
    logger.info(f"Iniciando download de: {url}")
    logger.info(f"Destino: {destination_path}")

    # Normaliza o caminho de destino
    destination_path = os.path.abspath(destination_path)

    # Cria o diretório de destino se não existir
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Verifica se o arquivo já existe e tem o hash correto
    if os.path.exists(destination_path) and not force_download:
        if expected_hash:
            if verify_file_hash(destination_path, expected_hash, hash_algorithm):
                logger.info(f"Arquivo '{os.path.basename(destination_path)}' já existe e o hash corresponde. Pulando download.")
                # Notifica 100% de progresso se o arquivo já existir
                if progress_callback:
                    try:
                        progress_callback(100.0)
                    except Exception as e:
                        logger.warning(f"Erro ao chamar callback de progresso: {e}")
                return True
            else:
                logger.warning(f"Arquivo '{os.path.basename(destination_path)}' existe, mas o hash não corresponde. Baixando novamente.")
        else:
            logger.info(f"Arquivo '{os.path.basename(destination_path)}' já existe. Pulando download.")
            # Notifica 100% de progresso se o arquivo já existir
            if progress_callback:
                try:
                    progress_callback(100.0)
                except Exception as e:
                    logger.warning(f"Erro ao chamar callback de progresso: {e}")
            return True

    # Tenta obter o tamanho do arquivo antes de baixar
    try:
        with closing(requests.head(url, timeout=timeout)) as r:
            r.raise_for_status()
            content_length = int(r.headers.get('content-length', 0))

            if content_length > 0:
                logger.info(f"Tamanho do arquivo a ser baixado: {format_size(content_length)}")

                # Verifica se há espaço suficiente em disco
                has_space, message = ensure_space_for_download(content_length, os.path.dirname(destination_path))

                if not has_space:
                    logger.error(f"Espaço insuficiente em disco: {message}")
                    logger.error(suggest_cleanup_actions(content_length))

                    # Tenta limpar arquivos temporários automaticamente
                    success, cleanup_message = clean_temp_directory()
                    if success:
                        logger.info(cleanup_message)

                        # Verifica novamente após a limpeza
                        has_space, message = ensure_space_for_download(content_length, os.path.dirname(destination_path))
                        if has_space:
                            logger.info(f"Espaço suficiente após limpeza: {message}")
                        else:
                            logger.error(f"Ainda não há espaço suficiente após limpeza: {message}")
                            return False
                    else:
                        logger.error(f"Falha ao limpar arquivos temporários: {cleanup_message}")
                        return False
                else:
                    logger.info(f"Espaço em disco verificado: {message}")
    except Exception as e:
        logger.warning(f"Não foi possível verificar o tamanho do arquivo antes do download: {e}")
        # Continua com o download mesmo sem saber o tamanho

    try:
        # Baixa para arquivo temporário primeiro
        success, temp_file = download_to_temp(
            url=url,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm,
            timeout=timeout,
            retry_count=retry_count,
            show_progress=show_progress,
            use_mirrors=use_mirrors,
            progress_callback=progress_callback
        )

        if not success or not temp_file:
            logger.error("Falha no download para arquivo temporário")
            return False

        # Verifica e move o arquivo temporário para o destino final
        return _verify_and_clean_temp_file(
            temp_path=temp_file,
            destination_path=destination_path,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm
        )

    except Exception as e:
        # Captura qualquer exceção não tratada
        err = handle_exception(
            e,
            message=f"Erro inesperado durante o download de {url}",
            context={"url": url, "destination": destination_path}
        )
        err.log()
        return False

def download_files_batch(files: List[Dict[str, Any]],
                        parallel: bool = False,
                        continue_on_error: bool = True,
                        use_mirrors: bool = True) -> Dict[str, bool]:
    """
    Baixa vários arquivos em lote, opcionalmente em paralelo.

    Args:
        files: Lista de dicionários, cada um com parâmetros para download_file
               (deve conter pelo menos 'url' e 'destination_path')
        parallel: Se deve baixar em paralelo (requer threads)
        continue_on_error: Se deve continuar baixando após um erro
        use_mirrors: Se deve tentar usar mirrors em caso de falha

    Returns:
        Dicionário com resultados {destination_path: sucesso}
    """
    results = {}

    if parallel:
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {}

                # Inicia todos os downloads
                for file_info in files:
                    url = file_info.get('url')
                    dest = file_info.get('destination_path')

                    if not url or not dest:
                        logger.error(f"Informações de download incompletas: {file_info}")
                        continue

                    future = executor.submit(
                        download_file,
                        url=url,
                        destination_path=dest,
                        expected_hash=file_info.get('expected_hash'),
                        hash_algorithm=file_info.get('hash_algorithm', 'sha256'),
                        timeout=file_info.get('timeout', DOWNLOAD_TIMEOUT),
                        retry_count=file_info.get('retry_count', MAX_RETRIES),
                        show_progress=file_info.get('show_progress', False),  # Desativa progresso em downloads paralelos
                        force_download=file_info.get('force_download', False),
                        use_mirrors=file_info.get('use_mirrors', use_mirrors)
                    )

                    futures[future] = dest

                # Coleta os resultados
                for future in concurrent.futures.as_completed(futures):
                    dest = futures[future]
                    try:
                        success = future.result()
                        results[dest] = success
                    except Exception as e:
                        logger.error(f"Erro no download paralelo de {dest}: {e}")
                        results[dest] = False

                        if not continue_on_error:
                            # Cancela os downloads pendentes
                            for f in futures:
                                if not f.done():
                                    f.cancel()
                            break

        except ImportError:
            logger.warning("concurrent.futures não disponível. Usando downloads sequenciais.")
            parallel = False

    # Fallback para download sequencial
    if not parallel:
        for file_info in files:
            url = file_info.get('url')
            dest = file_info.get('destination_path')

            if not url or not dest:
                logger.error(f"Informações de download incompletas: {file_info}")
                continue

            success = download_file(
                url=url,
                destination_path=dest,
                expected_hash=file_info.get('expected_hash'),
                hash_algorithm=file_info.get('hash_algorithm', 'sha256'),
                timeout=file_info.get('timeout', DOWNLOAD_TIMEOUT),
                retry_count=file_info.get('retry_count', MAX_RETRIES),
                show_progress=file_info.get('show_progress', True),
                force_download=file_info.get('force_download', False),
                use_mirrors=file_info.get('use_mirrors', use_mirrors)
            )

            results[dest] = success

            if not success and not continue_on_error:
                break

    # Resumo dos resultados
    success_count = sum(1 for success in results.values() if success)
    logger.info(f"Downloads concluídos: {success_count}/{len(results)} com sucesso")

    return results

def get_cache_path(url: str, subdir: str = "downloads") -> str:
    """
    Gera um caminho de arquivo de cache para uma URL.

    Args:
        url: URL a ser cacheada
        subdir: Subdiretório dentro do cache

    Returns:
        Caminho para o arquivo de cache
    """
    from hashlib import md5

    # Gera um nome de arquivo baseado na URL
    url_hash = md5(url.encode('utf-8')).hexdigest()
    filename = os.path.basename(url)

    # Se o nome do arquivo for muito curto ou não tiver extensão, use apenas o hash
    if len(filename) < 5 or '.' not in filename:
        filename = f"{url_hash}"
    else:
        # Caso contrário, combine nome do arquivo com hash
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{url_hash[:8]}{ext}"

    # Determina o caminho do cache
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(script_dir, subdir)

    # Garante que o diretório de cache existe
    os.makedirs(cache_dir, exist_ok=True)

    return os.path.join(cache_dir, filename)

def download_with_cache(url: str,
                       expected_hash: Optional[str] = None,
                       hash_algorithm: str = "sha256",
                       cache_dir: str = "downloads",
                       force_download: bool = False,
                       use_mirrors: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Baixa um arquivo com suporte a cache.

    Args:
        url: URL a ser baixada
        expected_hash: Hash esperado do arquivo
        hash_algorithm: Algoritmo de hash a ser usado
        cache_dir: Diretório de cache
        force_download: Se deve ignorar o cache e baixar novamente
        use_mirrors: Se deve tentar usar mirrors em caso de falha

    Returns:
        Tupla (sucesso, caminho_local) - caminho_local é None se falhar
    """
    cache_path = get_cache_path(url, cache_dir)

    # Verifica se já existe no cache
    if os.path.exists(cache_path) and not force_download:
        logger.info(f"Arquivo encontrado no cache: {cache_path}")

        # Se tiver hash, verifica
        if expected_hash:
            if verify_file_hash(cache_path, expected_hash, hash_algorithm):
                logger.info("Hash do arquivo em cache verificado com sucesso")
                return True, cache_path
            else:
                logger.warning("Hash do arquivo em cache não corresponde, baixando novamente")
        else:
            # Sem verificação de hash, confia no cache
            return True, cache_path

    # Se não estiver no cache ou hash não corresponder, baixa
    if use_mirrors:
        # Use o sistema de fallback de mirrors para download
        success = download_with_mirror_fallback(
            download_file,
            url=url,
            destination_path=cache_path,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm,
            force_download=force_download,
            use_mirrors=False  # Evita recursão, já que download_with_mirror_fallback já trata mirrors
        )
    else:
        # Download normal sem usar o sistema de fallback de mirrors
        success = download_file(
            url=url,
            destination_path=cache_path,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm,
            force_download=force_download,
            use_mirrors=False
        )

    if success:
        return True, cache_path
    else:
        return False, None

def verify_url_status(url: str, use_mirrors: bool = True, timeout: int = 5) -> bool:
    """
    Verifica se uma URL está disponível.

    Args:
        url: URL a ser verificada
        use_mirrors: Se deve considerar mirrors ao verificar disponibilidade
        timeout: Timeout para a verificação em segundos

    Returns:
        True se a URL está disponível (original ou um mirror), False caso contrário
    """

    try:
        # Tenta verificar a URL original primeiro
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        is_available = 200 <= response.status_code < 400

        if is_available:
            return True

        # Se a URL original não estiver disponível e mirrors estiver habilitado
        if not is_available and use_mirrors:
            best_url, _ = find_best_mirror(url, timeout=timeout)
            if best_url != url:
                # Testa o mirror encontrado
                try:
                    mirror_response = requests.head(best_url, timeout=timeout, allow_redirects=True)
                    return 200 <= mirror_response.status_code < 400
                except Exception:
                    pass

        return is_available

    except Exception as e:
        logger.debug(f"Erro ao verificar URL {url}: {e}")

        # Se ocorrer erro e mirrors estiver habilitado, tenta encontrar um mirror
        if use_mirrors:
            try:
                best_url, _ = find_best_mirror(url, timeout=timeout)
                if best_url != url:
                    try:
                        mirror_response = requests.head(best_url, timeout=timeout, allow_redirects=True)
                        return 200 <= mirror_response.status_code < 400
                    except Exception:
                        pass
            except Exception:
                pass

        return False

def pre_validate_urls(urls: List[str], use_mirrors: bool = True) -> Dict[str, bool]:
    """
    Verifica a disponibilidade de várias URLs antes de iniciar downloads.

    Args:
        urls: Lista de URLs para verificar
        use_mirrors: Se deve considerar mirrors ao verificar disponibilidade

    Returns:
        Dicionário com resultados {url: disponível}
    """
    results = {}

    try:

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(verify_url_status, url, use_mirrors): url for url in urls}

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    is_available = future.result()
                    results[url] = is_available
                    status = "disponível" if is_available else "indisponível"
                    logger.info(f"URL {url} está {status}")
                except Exception as e:
                    results[url] = False
                    logger.warning(f"Erro ao verificar URL {url}: {e}")
    except ImportError:
        # Fallback para verificação sequencial
        for url in urls:
            try:
                is_available = verify_url_status(url, use_mirrors)
                results[url] = is_available
                status = "disponível" if is_available else "indisponível"
                logger.info(f"URL {url} está {status}")
            except Exception as e:
                results[url] = False
                logger.warning(f"Erro ao verificar URL {url}: {e}")

    # Sumariza os resultados
    available_count = sum(1 for available in results.values() if available)
    logger.info(f"Verificação de URLs concluída: {available_count}/{len(results)} disponíveis")

    return results

if __name__ == '__main__':
    # Teste rápido de download
    logging.basicConfig(level=logging.INFO)

    # URL de teste (GitHub releases são boas para teste)
    test_url = "https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe"
    test_dest = "temp_download/git_installer.exe"

    print(f"Testando download com cache e mirrors de {test_url}")
    success, cached_path = download_with_cache(test_url, use_mirrors=True)

    if success:
        print(f"Download em cache concluído com sucesso: {cached_path}")
        # Obtém o hash do arquivo baixado
        hash_value = get_file_hash(cached_path)
        print(f"Hash SHA-256 do arquivo: {hash_value}")
    else:
        print("Download em cache falhou.")