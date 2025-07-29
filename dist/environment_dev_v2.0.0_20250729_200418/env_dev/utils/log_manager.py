import logging
import os
import sys
import uuid
from logging.handlers import RotatingFileHandler

# Cores para o terminal (ANSI)
class TerminalColors:
    INFO = '\033[94m'      # Azul
    WARNING = '\033[93m'   # Amarelo
    ERROR = '\033[91m'     # Vermelho
    SUCCESS = '\033[92m'   # Verde
    DEBUG = '\033[96m'     # Ciano
    BOLD = '\033[1m'       # Negrito
    RESET = '\033[0m'      # Reset
    INSTALLATION = '\033[95m'  # Magenta
    ROLLBACK = '\033[93;1m'    # Amarelo negrito
    VERIFICATION = '\033[94;1m'  # Azul negrito

# Níveis de log personalizados
SUCCESS = 25  # Entre WARNING (30) e INFO (20)
INSTALLATION = 26  # Entre SUCCESS (25) e INFO (20)
ROLLBACK = 27  # Entre INSTALLATION (26) e SUCCESS (25)
VERIFICATION = 28  # Entre ROLLBACK (27) e SUCCESS (25)

logging.addLevelName(SUCCESS, 'SUCCESS')
logging.addLevelName(INSTALLATION, 'INSTALL')
logging.addLevelName(ROLLBACK, 'ROLLBACK')
logging.addLevelName(VERIFICATION, 'VERIFY')

class ColoredFormatter(logging.Formatter):
    """Formatador personalizado que adiciona cores aos logs no terminal."""

    def format(self, record):
        # Guarda o levelname original
        orig_levelname = record.levelname

        # Adiciona cores baseadas no nível
        if record.levelno == logging.INFO:
            record.levelname = f"{TerminalColors.INFO}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == logging.WARNING:
            record.levelname = f"{TerminalColors.WARNING}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            record.levelname = f"{TerminalColors.ERROR}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == SUCCESS:
            record.levelname = f"{TerminalColors.SUCCESS}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == logging.DEBUG:
            record.levelname = f"{TerminalColors.DEBUG}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == INSTALLATION:
            record.levelname = f"{TerminalColors.INSTALLATION}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == ROLLBACK:
            record.levelname = f"{TerminalColors.ROLLBACK}{record.levelname}{TerminalColors.RESET}"
        elif record.levelno == VERIFICATION:
            record.levelname = f"{TerminalColors.VERIFICATION}{record.levelname}{TerminalColors.RESET}"

        # Formata a mensagem
        result = super().format(record)

        # Restaura o levelname original para não afetar outros formatadores
        record.levelname = orig_levelname

        return result

class EnvironmentLogger:
    """
    Gerenciador de logging personalizado que estende as funcionalidades do
    módulo logging padrão com suporte a cores no terminal, rotação de arquivos,
    e sessões de log.
    """

    def __init__(self, log_dir=None, log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
        """
        Inicializa o gerenciador de logs.

        Args:
            log_dir (str, optional): Diretório para os arquivos de log. Se None, usa '../logs/'.
            log_file (str, optional): Nome do arquivo de log. Se None, usa 'environment_dev.log'.
            console_level (int, optional): Nível de log do console. Padrão é INFO.
            file_level (int, optional): Nível de log do arquivo. Padrão é DEBUG.
        """
        # Define o diretório e arquivo de log
        if log_dir is None:
            # Usa o diretório 'logs' no mesmo nível que 'environment_dev_python'
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.log_dir = os.path.join(base_dir, 'logs')
        else:
            self.log_dir = log_dir

        if log_file is None:
            self.log_file = 'environment_dev.log'
        else:
            self.log_file = log_file

        # Garante que o diretório de logs existe
        os.makedirs(self.log_dir, exist_ok=True)

        # Caminho completo para o arquivo de log
        self.log_path = os.path.join(self.log_dir, self.log_file)

        # Configura o logger raiz
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # Captura todos os níveis

        # Remove handlers existentes para evitar duplicação
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Adiciona métodos para os níveis personalizados à CLASSE Logger
        # O primeiro argumento 'self_logger' será a instância do logger.
        def success(self_logger, msg, *args, **kwargs):
            if args:
                formatted_msg = msg % args
            else:
                formatted_msg = msg
            # Usa self_logger (a instância real) para chamar log()
            self_logger.log(SUCCESS, formatted_msg, **kwargs)

        def installation(self_logger, msg, *args, **kwargs):
            if args:
                formatted_msg = msg % args
            else:
                formatted_msg = msg
            self_logger.log(INSTALLATION, formatted_msg, **kwargs)

        def rollback(self_logger, msg, *args, **kwargs):
            if args:
                formatted_msg = msg % args
            else:
                formatted_msg = msg
            self_logger.log(ROLLBACK, formatted_msg, **kwargs)

        def verification(self_logger, msg, *args, **kwargs):
            if args:
                formatted_msg = msg % args
            else:
                formatted_msg = msg
            self_logger.log(VERIFICATION, formatted_msg, **kwargs)

        # Adiciona os métodos à CLASSE Logger para que todas as instâncias os tenham
        if not hasattr(logging.Logger, 'success'):
             logging.Logger.success = success
        if not hasattr(logging.Logger, 'installation'):
             logging.Logger.installation = installation
        if not hasattr(logging.Logger, 'rollback'):
             logging.Logger.rollback = rollback
        if not hasattr(logging.Logger, 'verification'):
             logging.Logger.verification = verification

        # Não é mais necessário adicionar à instância self.logger separadamente

        # Cria formatadores
        console_format = '%(levelname)s: %(message)s'
        file_format = '%(asctime)s - %(levelname)-8s - %(filename)s:%(lineno)d - %(message)s'
        self.detailed_console_format = '%(asctime)s - %(levelname)s - %(message)s'

        # Configura handler para o console
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(console_level)
        self.console_formatter = ColoredFormatter(console_format)
        self.console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(self.console_handler)

        # Configura handler para arquivo com rotação
        # Máximo de 5MB por arquivo, mantém até 5 arquivos de backup
        self.file_handler = RotatingFileHandler(
            self.log_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
        )
        self.file_handler.setLevel(file_level)
        self.file_formatter = logging.Formatter(file_format)
        self.file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(self.file_handler)

        # ID da sessão atual
        self.session_id = str(uuid.uuid4())

    def start_session(self, session_name=None):
        """
        Inicia uma nova sessão de log com um ID único.

        Args:
            session_name (str, optional): Nome adicional para identificar a sessão.
                                        Padrão é None.

        Returns:
            str: ID da sessão.
        """
        self.session_id = str(uuid.uuid4())

        if session_name:
            session_info = f"Sessão '{session_name}' iniciada com ID: {self.session_id}"
        else:
            session_info = f"Sessão iniciada com ID: {self.session_id}"

        self.logger.info(session_info)
        return self.session_id

    def stop_session(self):
        """Encerra a sessão de log atual."""
        self.logger.info(f"Sessão {self.session_id} encerrada")

    def set_console_level(self, level):
        """Define o nível de log para o console."""
        self.console_handler.setLevel(level)

    def set_file_level(self, level):
        """Define o nível de log para o arquivo."""
        self.file_handler.setLevel(level)

    def use_detailed_console_format(self, detailed=True):
        """Alterna entre formato de console simples e detalhado."""
        if detailed:
            format_str = self.detailed_console_format
        else:
            format_str = '%(levelname)s: %(message)s'

        self.console_formatter = ColoredFormatter(format_str)
        self.console_handler.setFormatter(self.console_formatter)

    def get_logger(self):
        """Retorna o logger configurado."""
        return self.logger

# Para uso em outros módulos
def setup_logging(log_dir=None, log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configura e retorna um gerenciador de logs.

    Esta é a função principal a ser importada por outros módulos.

    Args:
        log_dir (str, optional): Diretório para os arquivos de log.
        log_file (str, optional): Nome do arquivo de log.
        console_level (int, optional): Nível de log do console.
        file_level (int, optional): Nível de log do arquivo.

    Returns:
        tuple: (logger, logger_manager)
    """
    manager = EnvironmentLogger(log_dir, log_file, console_level, file_level)
    logger = manager.get_logger()
    return logger, manager

if __name__ == "__main__":
    # Demonstração e teste
    logger, manager = setup_logging(console_level=logging.DEBUG)

    # Inicia uma sessão
    session_id = manager.start_session("Demo")

    # Testa os diferentes níveis de log padrão
    logger.debug("Esta é uma mensagem de debug")
    logger.info("Esta é uma mensagem de informação")
    logger.warning("Esta é uma mensagem de aviso")
    logger.error("Esta é uma mensagem de erro")
    logger.critical("Esta é uma mensagem crítica")

    # Testa os níveis de log personalizados
    logger.success("Esta é uma mensagem de sucesso")
    logger.installation("Instalando componente: TestComponent")
    logger.rollback("Executando rollback para: TestComponent")
    logger.verification("Verificando instalação de: TestComponent")

    # Alterna para formato detalhado no console
    manager.use_detailed_console_format(True)
    logger.info("Agora usando formato detalhado no console")

    # Exemplo de uso em um fluxo de instalação
    logger.installation("Iniciando instalação do componente: Python")
    logger.info("Baixando Python 3.10.0...")
    logger.info("Extraindo arquivos...")
    logger.verification("Verificando instalação do Python...")
    logger.success("Python 3.10.0 instalado com sucesso!")

    # Exemplo de uso em um fluxo com erro
    logger.installation("Iniciando instalação do componente: NodeJS")
    logger.info("Baixando NodeJS 16.13.0...")
    logger.error("Falha ao extrair arquivos do NodeJS")
    logger.rollback("Iniciando rollback para: NodeJS")
    logger.rollback("Removendo arquivos temporários...")
    logger.rollback("Rollback concluído para: NodeJS")

    # Encerra a sessão
    manager.stop_session()

    print(f"\nLogs salvos em: {manager.log_path}")