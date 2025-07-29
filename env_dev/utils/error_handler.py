#!/usr/bin/env python3
"""
Módulo de gestão de erros para o Environment Dev

Fornece um sistema de categorização de erros, mecanismos de recuperação automática
e formatação de mensagens de erro amigáveis ao usuário.
"""

import os
import sys
import logging
import traceback
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable, Tuple, Union
import inspect

# Configuração do logger
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Enumeração dos níveis de severidade de erros"""
    CRITICAL = auto()  # Erro fatal que impede a continuação do programa
    ERROR = auto()     # Erro grave que impede uma operação específica
    WARNING = auto()   # Problema não fatal que permite continuar
    INFO = auto()      # Informativo sobre algo inesperado

    def __str__(self):
        return self.name

class ErrorCategory(Enum):
    """Categorias de erros para classificação"""
    NETWORK = auto()        # Erros de rede/conexão
    FILESYSTEM = auto()     # Erros de acesso a arquivos
    PERMISSION = auto()     # Erros de permissão
    DEPENDENCY = auto()     # Erros de dependências
    CONFIGURATION = auto()  # Erros de configuração
    EXECUTION = auto()      # Erros na execução de processos externos
    VALIDATION = auto()     # Erros de validação de dados
    INSTALLATION = auto()   # Erros específicos de instalação
    PARSING = auto()        # Erros de parsing
    UNKNOWN = auto()        # Erros não classificados

    def __str__(self):
        return self.name

class EnvDevError:
    """
    Classe para representar e gerenciar erros do Environment Dev.

    Permite categorizar, logar e recuperar de erros de forma uniforme.
    """

    def __init__(self,
                 message: str,
                 original_error: Optional[Exception] = None,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 recoverable: bool = True,
                 recovery_hint: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Inicializa um novo erro do Environment Dev.

        Args:
            message: Mensagem descritiva do erro
            original_error: Exceção original que causou o erro, se houver
            severity: Nível de severidade do erro
            category: Categoria do erro
            recoverable: Se o erro permite recuperação automática
            recovery_hint: Dica para o usuário sobre como resolver o problema
            context: Informações adicionais sobre o contexto do erro
        """
        self.message = message
        self.original_error = original_error
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.recovery_hint = recovery_hint
        self.context = context or {}
        self.traceback = traceback.extract_stack()[:-1]  # Exclui este frame
        self.timestamp = logging.Formatter().converter()

        # Captura informações sobre quem criou este erro
        frame = inspect.currentframe().f_back
        self.module = frame.f_globals['__name__'] if frame else 'unknown'
        self.function = frame.f_code.co_name if frame else 'unknown'
        self.lineno = frame.f_lineno if frame else 0

    def log(self) -> None:
        """Loga o erro com o nível apropriado."""
        level_map = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.INFO: logging.INFO
        }

        level = level_map.get(self.severity, logging.ERROR)

        # Formata a mensagem de log
        log_message = f"[{self.category}] {self.message}"

        # Adiciona informações sobre o erro original
        if self.original_error:
            log_message += f" | Erro original: {type(self.original_error).__name__}: {str(self.original_error)}"

        # Loga com a origem do erro
        logger.log(level, f"{log_message} (em {self.module}.{self.function}:{self.lineno})")

        # Se for crítico ou erro, inclui o traceback completo no nível DEBUG
        if self.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.ERROR) and self.original_error:
            logger.debug("Traceback completo do erro original:", exc_info=self.original_error)

    def get_user_message(self) -> str:
        """Retorna uma mensagem formatada para o usuário."""

        header_map = {
            ErrorSeverity.CRITICAL: "ERRO CRÍTICO",
            ErrorSeverity.ERROR: "ERRO",
            ErrorSeverity.WARNING: "AVISO",
            ErrorSeverity.INFO: "INFO"
        }

        header = header_map.get(self.severity, "ERRO")
        formatted_message = f"{header}: {self.message}"

        # Adiciona dica de recuperação, se disponível
        if self.recovery_hint:
            formatted_message += f"\n\nSugestão: {self.recovery_hint}"

        return formatted_message

    def get_detail_message(self) -> str:
        """Retorna uma mensagem detalhada para depuração."""

        details = [
            f"Erro: {self.message}",
            f"Categoria: {self.category}",
            f"Severidade: {self.severity}",
            f"Recuperável: {'Sim' if self.recoverable else 'Não'}",
            f"Localização: {self.module}.{self.function}:{self.lineno}"
        ]

        if self.original_error:
            error_type = type(self.original_error).__name__
            error_msg = str(self.original_error)
            details.append(f"Erro original: {error_type}: {error_msg}")

        if self.context:
            context_str = "\n  ".join([f"{k}: {v}" for k, v in self.context.items()])
            details.append(f"Contexto:\n  {context_str}")

        return "\n".join(details)

    def __str__(self) -> str:
        return f"{self.severity} - {self.category}: {self.message}"

# Funções globais para simplificar o uso do sistema de erros

def handle_exception(e: Exception,
                    message: str = None,
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    category: Optional[ErrorCategory] = None,
                    context: Optional[Dict[str, Any]] = None) -> EnvDevError:
    """
    Manipula uma exceção e a converte para um EnvDevError.

    Args:
        e: A exceção capturada
        message: Mensagem personalizada (se None, usa str(e))
        severity: Nível de severidade do erro
        category: Categoria do erro (se None, será identificada automaticamente)
        context: Informações de contexto adicionais

    Returns:
        Um objeto EnvDevError configurado
    """
    if message is None:
        message = str(e)

    # Tenta determinar automaticamente a categoria se não especificada
    if category is None:
        category = categorize_exception(e)

    # Determina se o erro é recuperável com base na categoria e tipo
    recoverable = is_recoverable(e, category)

    # Gera uma dica de recuperação com base no tipo de erro
    recovery_hint = generate_recovery_hint(e, category)

    # Cria e loga o erro
    error = EnvDevError(
        message=message,
        original_error=e,
        severity=severity,
        category=category,
        recoverable=recoverable,
        recovery_hint=recovery_hint,
        context=context
    )

    error.log()
    return error

def categorize_exception(e: Exception) -> ErrorCategory:
    """
    Categoriza uma exceção com base em seu tipo.

    Args:
        e: A exceção a ser categorizada

    Returns:
        A categoria mais apropriada para a exceção
    """
    # Nome da classe de exceção para ajudar na categorização
    exception_name = type(e).__name__.lower()
    exception_module = type(e).__module__.lower()
    exception_str = str(e).lower()

    # Erros de rede
    if any(term in exception_name for term in ['connection', 'socket', 'url', 'http', 'request']):
        return ErrorCategory.NETWORK
    if 'timeout' in exception_name or 'timeout' in exception_str:
        return ErrorCategory.NETWORK
    if exception_module == 'requests' or 'urllib' in exception_module:
        return ErrorCategory.NETWORK

    # Erros de sistema de arquivos
    if any(term in exception_name for term in ['file', 'io', 'path', 'dir']):
        return ErrorCategory.FILESYSTEM
    if isinstance(e, (IOError, FileNotFoundError, PermissionError, IsADirectoryError)):
        return ErrorCategory.FILESYSTEM
    if any(term in exception_str for term in ['no such file', 'directory', 'path']):
        return ErrorCategory.FILESYSTEM

    # Erros de permissão
    if 'permission' in exception_name or 'access' in exception_name:
        return ErrorCategory.PERMISSION
    if isinstance(e, PermissionError):
        return ErrorCategory.PERMISSION
    if any(term in exception_str for term in ['permission', 'access denied', 'not allowed']):
        return ErrorCategory.PERMISSION

    # Erros de dependência
    if 'import' in exception_name or 'module' in exception_name:
        return ErrorCategory.DEPENDENCY
    if isinstance(e, ImportError) or isinstance(e, ModuleNotFoundError):
        return ErrorCategory.DEPENDENCY

    # Erros de parsing
    if any(term in exception_name for term in ['parse', 'syntax', 'json', 'yaml', 'xml']):
        return ErrorCategory.PARSING
    if 'yaml.parser' in exception_module or 'json.decoder' in exception_module:
        return ErrorCategory.PARSING

    # Se nenhum dos critérios acima for atendido
    return ErrorCategory.UNKNOWN

def is_recoverable(e: Exception, category: ErrorCategory) -> bool:
    """
    Determina se uma exceção é recuperável.

    Args:
        e: A exceção a verificar
        category: A categoria da exceção

    Returns:
        True se o erro for potencialmente recuperável, False caso contrário
    """
    # Alguns erros são quase sempre irrecuperáveis
    if isinstance(e, (SystemExit, KeyboardInterrupt, MemoryError)):
        return False

    # Erros críticos por categoria
    if category == ErrorCategory.PERMISSION:
        # Permissão geralmente requer intervenção do usuário
        return False

    if category == ErrorCategory.DEPENDENCY and isinstance(e, ImportError):
        # Falta de módulo geralmente requer instalação manual
        return False

    # Erros de timeout e conexão podem ser recuperáveis com retry
    if category == ErrorCategory.NETWORK and 'timeout' in str(e).lower():
        return True

    # Por padrão, assume que outros erros são recuperáveis
    return True

def generate_recovery_hint(e: Exception, category: ErrorCategory) -> Optional[str]:
    """
    Gera uma dica de recuperação para uma exceção.

    Args:
        e: A exceção para a qual gerar uma dica
        category: A categoria da exceção

    Returns:
        Uma string com uma dica de recuperação ou None se não houver dica
    """
    # Dicas por categoria
    if category == ErrorCategory.NETWORK:
        return "Verifique sua conexão com a internet e tente novamente. " \
               "Se o problema persistir, pode haver um problema no servidor remoto."

    if category == ErrorCategory.FILESYSTEM:
        if isinstance(e, FileNotFoundError):
            return "Verifique se o caminho do arquivo está correto e se ele existe."
        if isinstance(e, PermissionError):
            return "Você não tem permissão para acessar este arquivo. " \
                   "Tente executar como administrador."

    if category == ErrorCategory.PERMISSION:
        return "Esta operação requer privilégios elevados. " \
               "Tente executar o programa como administrador."

    if category == ErrorCategory.DEPENDENCY:
        if isinstance(e, ImportError) or isinstance(e, ModuleNotFoundError):
            module_name = str(e).split("'")[1] if "'" in str(e) else "o módulo necessário"
            return f"Instale {module_name} com 'pip install {module_name}' e tente novamente."

    if category == ErrorCategory.PARSING:
        return "O arquivo de configuração contém erros de sintaxe. " \
               "Verifique o formato e tente novamente."

    # Dica genérica
    return None

def try_recover(error: EnvDevError,
                recovery_function: Optional[Callable] = None,
                max_attempts: int = 3) -> Tuple[bool, Any]:
    """
    Tenta recuperar-se de um erro de forma automática.

    Args:
        error: O erro a recuperar
        recovery_function: Função de recuperação personalizada
        max_attempts: Número máximo de tentativas

    Returns:
        Tupla (sucesso, resultado) onde sucesso é True se recuperou com sucesso
    """
    # Obtém o logger do módulo
    logger = logging.getLogger(__name__)

    if not error.recoverable:
        logger.warning(f"Tentativa de recuperar de erro não recuperável: {error}")
        return False, None

    if recovery_function:
        try:
            logger.info(f"Tentando recuperar de erro {error.category} com função personalizada")
            result = recovery_function(error)
            return True, result
        except Exception as e:
            logger.error(f"Falha na função de recuperação personalizada: {e}")
            return False, None

    # Recuperação automática por categoria
    if error.category == ErrorCategory.NETWORK:
        # Implementa retry com backoff para erros de rede
        import time
        import random

        for attempt in range(max_attempts):
            logger.info(f"Tentativa {attempt+1}/{max_attempts} de reconexão...")

            try:
                # Se tivermos contexto com uma função para refazer
                if 'retry_function' in error.context and callable(error.context['retry_function']):
                    retry_args = error.context.get('retry_args', [])
                    retry_kwargs = error.context.get('retry_kwargs', {})

                    result = error.context['retry_function'](*retry_args, **retry_kwargs)
                    logger.info(f"Recuperação bem-sucedida na tentativa {attempt+1}")
                    return True, result

                # Se não temos função de retry, apenas esperamos
                sleep_time = (2 ** attempt) * (0.1 + random.random() * 0.1)  # Backoff exponencial
                time.sleep(sleep_time)
            except Exception as retry_error:
                logger.warning(f"Falha na tentativa {attempt+1}: {retry_error}")
                continue

    # Se chegou aqui, não conseguiu recuperar automaticamente
    logger.warning(f"Não foi possível recuperar automaticamente do erro: {error}")
    return False, None

# Classe para agrupar erros relacionados
class ErrorGroup:
    """
    Agrupa erros relacionados para apresentação e análise.

    Útil para mostrar um resumo dos problemas encontrados durante uma operação.
    """

    def __init__(self, name: str):
        """
        Inicializa um novo grupo de erros.

        Args:
            name: Nome descritivo do grupo
        """
        self.name = name
        self.errors: List[EnvDevError] = []

    def add(self, error: EnvDevError) -> None:
        """Adiciona um erro ao grupo."""
        self.errors.append(error)

    def has_critical(self) -> bool:
        """Verifica se há erros críticos no grupo."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    def has_errors(self) -> bool:
        """Verifica se há erros (não críticos) no grupo."""
        return any(error.severity == ErrorSeverity.ERROR for error in self.errors)

    def count(self) -> int:
        """Retorna o número total de erros no grupo."""
        return len(self.errors)

    def get_summary(self) -> str:
        """Retorna um resumo textual dos erros."""
        if not self.errors:
            return f"Grupo '{self.name}': Nenhum erro reportado."

        counts = {
            ErrorSeverity.CRITICAL: 0,
            ErrorSeverity.ERROR: 0,
            ErrorSeverity.WARNING: 0,
            ErrorSeverity.INFO: 0
        }

        for error in self.errors:
            counts[error.severity] += 1

        summary = [f"Grupo '{self.name}': {len(self.errors)} problema(s) encontrado(s)"]
        for severity, count in counts.items():
            if count > 0:
                summary.append(f"- {severity}: {count}")

        return "\n".join(summary)

    def get_details(self) -> str:
        """Retorna uma descrição detalhada de todos os erros."""
        if not self.errors:
            return f"Grupo '{self.name}': Nenhum erro reportado."

        details = [f"=== Detalhes do grupo '{self.name}' ==="]

        for i, error in enumerate(self.errors, 1):
            details.append(f"\n--- Erro {i}/{len(self.errors)} ---")
            details.append(error.get_detail_message())

        return "\n".join(details)

# Contexto global para gerenciar erros em toda a aplicação
class ErrorContext:
    """
    Contexto global para gerenciar erros em toda a aplicação.

    Permite rastrear e agrupar erros relacionados.
    """

    def __init__(self):
        """Inicializa um novo contexto de erros."""
        self.groups: Dict[str, ErrorGroup] = {}
        self.last_error: Optional[EnvDevError] = None

    def add_error(self, error: EnvDevError, group_name: str = "default") -> None:
        """
        Adiciona um erro a um grupo específico.

        Args:
            error: O erro a ser adicionado
            group_name: Nome do grupo ao qual adicionar o erro
        """
        if group_name not in self.groups:
            self.groups[group_name] = ErrorGroup(group_name)

        self.groups[group_name].add(error)
        self.last_error = error

    def get_group(self, group_name: str) -> Optional[ErrorGroup]:
        """Retorna um grupo específico de erros."""
        return self.groups.get(group_name)

    def get_all_groups(self) -> List[ErrorGroup]:
        """Retorna todos os grupos de erros."""
        return list(self.groups.values())

    def has_errors(self, group_name: Optional[str] = None) -> bool:
        """
        Verifica se há erros em um grupo específico ou em qualquer grupo.

        Args:
            group_name: Nome do grupo a verificar, ou None para verificar todos

        Returns:
            True se houver erros, False caso contrário
        """
        if group_name:
            group = self.groups.get(group_name)
            return group is not None and (group.has_errors() or group.has_critical())

        return any(group.has_errors() or group.has_critical() for group in self.groups.values())

    def clear(self, group_name: Optional[str] = None) -> None:
        """
        Limpa os erros de um grupo específico ou de todos os grupos.

        Args:
            group_name: Nome do grupo a limpar, ou None para limpar todos
        """
        if group_name:
            if group_name in self.groups:
                del self.groups[group_name]
        else:
            self.groups.clear()
            self.last_error = None

    def get_summary(self) -> str:
        """Retorna um resumo de todos os grupos de erros."""
        if not self.groups:
            return "Nenhum erro reportado."

        summaries = [group.get_summary() for group in self.groups.values()]
        return "\n\n".join(summaries)

# Instância global do contexto de erros
global_error_context = ErrorContext()

# Função para obter o contexto global de erros
def get_error_context() -> ErrorContext:
    """Retorna o contexto global de erros."""
    return global_error_context

# Decorador para tratamento automático de exceções
def handle_errors(category: Optional[ErrorCategory] = None,
                 group_name: str = "default",
                 recoverable: bool = True):
    """
    Decorador para tratar exceções automaticamente.

    Args:
        category: Categoria padrão para erros não categorizados
        group_name: Nome do grupo para agrupar erros relacionados
        recoverable: Se os erros são considerados recuperáveis por padrão

    Returns:
        Decorador configurado
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtém o logger do módulo
            logger = logging.getLogger(__name__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Captura a exceção e a converte para um EnvDevError
                error = handle_exception(
                    e,
                    message=f"Erro ao executar {func.__name__}: {str(e)}",
                    category=category,
                    context={"function": func.__name__, "args": args, "kwargs": kwargs}
                )

                # Adiciona ao contexto global
                global_error_context.add_error(error, group_name)

                # Registra no log
                logger.error(f"Exceção capturada pelo decorador handle_errors: {error}")

                # Tenta recuperar automaticamente se for recuperável
                if recoverable and error.recoverable:
                    success, result = try_recover(error)
                    if success:
                        logger.info(f"Recuperação automática bem-sucedida para {func.__name__}")
                        return result

                # Se chegou aqui, não conseguiu recuperar
                # Propaga o erro original para tratamento em nível superior
                raise

        return wrapper

    return decorator

# Funções de conveniência para criar erros comuns
def file_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a arquivos."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.FILESYSTEM,
        **kwargs
    )

def network_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a rede."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.NETWORK,
        **kwargs
    )

def permission_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a permissões."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.PERMISSION,
        recoverable=False,  # Erros de permissão geralmente não são recuperáveis automaticamente
        **kwargs
    )

def config_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a configuração."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.CONFIGURATION,
        **kwargs
    )

def dependency_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a dependências."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.DEPENDENCY,
        **kwargs
    )

def installation_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado a instalação."""
    # Remove o parâmetro 'component' dos kwargs se existir
    if 'component' in kwargs:
        component = kwargs.pop('component')
        # Opcionalmente, podemos adicionar o nome do componente ao contexto
        if 'context' not in kwargs:
            kwargs['context'] = {}
        if isinstance(kwargs['context'], dict):
            kwargs['context']['component_name'] = component

    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.INSTALLATION,
        **kwargs
    )

def execution_error(message: str, original_error: Optional[Exception] = None, **kwargs) -> EnvDevError:
    """Cria um erro relacionado à execução de processos externos."""
    return EnvDevError(
        message=message,
        original_error=original_error,
        category=ErrorCategory.EXECUTION,
        **kwargs
    )