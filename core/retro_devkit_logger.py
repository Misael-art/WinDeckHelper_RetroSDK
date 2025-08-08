"""Sistema de logging unificado para retro devkits
Gerencia logs centralizados para todos os devkits retro"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import json
from enum import Enum

# Tentar importar o handler seguro para Windows
try:
    from utils.windows_safe_rotating_handler import WindowsSafeRotatingFileHandler
    USE_WINDOWS_SAFE_HANDLER = True
except ImportError:
    USE_WINDOWS_SAFE_HANDLER = False

class LogLevel(Enum):
    """Níveis de log disponíveis"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class RetroDevkitLogger:
    """Logger unificado para retro devkits"""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, base_path: Path, log_level: str = "INFO", enable_file_logging: bool = True):
        if hasattr(self, '_initialized'):
            return
            
        self.base_path = base_path
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_file_logging = enable_file_logging
        
        # Diretório de logs
        self.log_dir = base_path / "logs" / "retro_devkits"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de log principal
        self.main_log_file = self.log_dir / "retro_devkits.log"
        
        # Configurar formatadores
        self._setup_formatters()
        
        # Configurar handlers
        self._setup_handlers()
        
        # Criar logger principal
        self.main_logger = self._create_logger("retro_devkits", self.main_log_file)
        
        self._initialized = True
        
    def _setup_formatters(self):
        """Configura formatadores de log"""
        # Formatador detalhado para arquivos
        self.file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Formatador simples para console
        self.console_formatter = logging.Formatter(
            fmt='%(levelname)s | %(name)s | %(message)s'
        )
        
        # Formatador JSON para logs estruturados
        self.json_formatter = JsonFormatter()
        
    def _setup_handlers(self):
        """Configura handlers de log"""
        # Handler para console
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(self.log_level)
        self.console_handler.setFormatter(self.console_formatter)
        
        if self.enable_file_logging:
            # Handler para arquivo principal (com rotação)
            if USE_WINDOWS_SAFE_HANDLER:
                self.file_handler = WindowsSafeRotatingFileHandler(
                    self.main_log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
            else:
                self.file_handler = logging.handlers.RotatingFileHandler(
                    self.main_log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
            self.file_handler.setLevel(logging.DEBUG)
            self.file_handler.setFormatter(self.file_formatter)
            
            # Handler para logs de erro
            if USE_WINDOWS_SAFE_HANDLER:
                self.error_handler = WindowsSafeRotatingFileHandler(
                    self.log_dir / "errors.log",
                    maxBytes=5*1024*1024,  # 5MB
                    backupCount=3,
                    encoding='utf-8'
                )
            else:
                self.error_handler = logging.handlers.RotatingFileHandler(
                    self.log_dir / "errors.log",
                    maxBytes=5*1024*1024,  # 5MB
                    backupCount=3,
                    encoding='utf-8'
                )
            self.error_handler.setLevel(logging.ERROR)
            self.error_handler.setFormatter(self.file_formatter)
            
            # Handler para logs JSON estruturados
            if USE_WINDOWS_SAFE_HANDLER:
                self.json_handler = WindowsSafeRotatingFileHandler(
                    self.log_dir / "structured.jsonl",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=3,
                    encoding='utf-8'
                )
            else:
                self.json_handler = logging.handlers.RotatingFileHandler(
                    self.log_dir / "structured.jsonl",
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=3,
                    encoding='utf-8'
                )
            self.json_handler.setLevel(logging.INFO)
            self.json_handler.setFormatter(self.json_formatter)
            
    def _create_logger(self, name: str, log_file: Optional[Path] = None) -> logging.Logger:
        """Cria um logger específico"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Evitar duplicação de handlers
        if logger.handlers:
            return logger
            
        # Adicionar handler de console
        logger.addHandler(self.console_handler)
        
        if self.enable_file_logging:
            # Adicionar handlers de arquivo
            logger.addHandler(self.file_handler)
            logger.addHandler(self.error_handler)
            logger.addHandler(self.json_handler)
            
            # Handler específico para o devkit (se especificado)
            if log_file and log_file != self.main_log_file:
                if USE_WINDOWS_SAFE_HANDLER:
                    devkit_handler = WindowsSafeRotatingFileHandler(
                        log_file,
                        maxBytes=5*1024*1024,  # 5MB
                        backupCount=3,
                        encoding='utf-8'
                    )
                else:
                    devkit_handler = logging.handlers.RotatingFileHandler(
                        log_file,
                        maxBytes=5*1024*1024,  # 5MB
                        backupCount=3,
                        encoding='utf-8'
                    )
                devkit_handler.setLevel(logging.DEBUG)
                devkit_handler.setFormatter(self.file_formatter)
                logger.addHandler(devkit_handler)
                
        # Evitar propagação para o logger raiz
        logger.propagate = False
        
        return logger
        
    def get_logger(self, devkit_name: str) -> logging.Logger:
        """Obtém logger para um devkit específico"""
        if devkit_name not in self._loggers:
            log_file = self.log_dir / f"{devkit_name.lower()}.log"
            logger_name = f"retro_devkits.{devkit_name.lower()}"
            self._loggers[devkit_name] = self._create_logger(logger_name, log_file)
            
        return self._loggers[devkit_name]
        
    def get_main_logger(self) -> logging.Logger:
        """Obtém logger principal"""
        return self.main_logger
        
    def set_log_level(self, level: str):
        """Define nível de log global"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.log_level = log_level
        
        # Atualizar nível do handler de console
        self.console_handler.setLevel(log_level)
        
        # Atualizar todos os loggers existentes
        for logger in self._loggers.values():
            logger.setLevel(logging.DEBUG)  # Manter DEBUG para capturar tudo
            
        self.main_logger.setLevel(logging.DEBUG)
        
    def enable_debug_mode(self):
        """Habilita modo debug"""
        self.set_log_level("DEBUG")
        self.main_logger.info("Modo debug habilitado")
        
    def disable_debug_mode(self):
        """Desabilita modo debug"""
        self.set_log_level("INFO")
        self.main_logger.info("Modo debug desabilitado")
        
    def log_devkit_operation(self, devkit_name: str, operation: str, 
                           status: str, details: Optional[Dict[str, Any]] = None):
        """Log estruturado para operações de devkit"""
        logger = self.get_logger(devkit_name)
        
        log_data = {
            "devkit": devkit_name,
            "operation": operation,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
            
        if status.lower() in ['success', 'completed', 'installed']:
            logger.info(f"{operation}: {status}", extra={'structured_data': log_data})
        elif status.lower() in ['warning', 'partial']:
            logger.warning(f"{operation}: {status}", extra={'structured_data': log_data})
        elif status.lower() in ['error', 'failed']:
            logger.error(f"{operation}: {status}", extra={'structured_data': log_data})
        else:
            logger.info(f"{operation}: {status}", extra={'structured_data': log_data})
            
    def log_installation_progress(self, devkit_name: str, component: str, 
                                progress: int, total: int, message: str = ""):
        """Log de progresso de instalação"""
        logger = self.get_logger(devkit_name)
        
        percentage = (progress / total * 100) if total > 0 else 0
        
        log_data = {
            "devkit": devkit_name,
            "component": component,
            "progress": progress,
            "total": total,
            "percentage": round(percentage, 1),
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[{percentage:.1f}%] {component}: {message}", 
                   extra={'structured_data': log_data})
        
    def log_build_process(self, devkit_name: str, project_name: str, 
                         build_type: str, status: str, duration: Optional[float] = None):
        """Log de processo de build"""
        logger = self.get_logger(devkit_name)
        
        log_data = {
            "devkit": devkit_name,
            "project": project_name,
            "build_type": build_type,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if duration is not None:
            log_data["duration_seconds"] = round(duration, 2)
            
        if status.lower() == 'success':
            logger.info(f"Build {build_type} concluído para {project_name}", 
                       extra={'structured_data': log_data})
        elif status.lower() == 'failed':
            logger.error(f"Build {build_type} falhou para {project_name}", 
                        extra={'structured_data': log_data})
        else:
            logger.info(f"Build {build_type} {status} para {project_name}", 
                       extra={'structured_data': log_data})
            
    def log_emulator_launch(self, devkit_name: str, emulator_name: str, 
                          rom_file: str, status: str):
        """Log de lançamento de emulador"""
        logger = self.get_logger(devkit_name)
        
        log_data = {
            "devkit": devkit_name,
            "emulator": emulator_name,
            "rom_file": rom_file,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if status.lower() == 'launched':
            logger.info(f"Emulador {emulator_name} iniciado com {rom_file}", 
                       extra={'structured_data': log_data})
        elif status.lower() == 'failed':
            logger.error(f"Falha ao iniciar {emulator_name} com {rom_file}", 
                        extra={'structured_data': log_data})
        else:
            logger.info(f"Emulador {emulator_name}: {status}", 
                       extra={'structured_data': log_data})
            
    def get_log_summary(self, devkit_name: Optional[str] = None, 
                       hours: int = 24) -> Dict[str, Any]:
        """Obtém resumo dos logs"""
        try:
            # Ler logs estruturados
            structured_log_file = self.log_dir / "structured.jsonl"
            if not structured_log_file.exists():
                return {"error": "Arquivo de logs estruturados não encontrado"}
                
            summary = {
                "total_entries": 0,
                "by_level": {"INFO": 0, "WARNING": 0, "ERROR": 0, "DEBUG": 0},
                "by_devkit": {},
                "recent_operations": [],
                "errors": []
            }
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            with open(structured_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filtrar por devkit se especificado
                        if devkit_name and entry.get('devkit') != devkit_name:
                            continue
                            
                        # Filtrar por tempo
                        entry_time = datetime.fromisoformat(entry.get('timestamp', '1970-01-01')).timestamp()
                        if entry_time < cutoff_time:
                            continue
                            
                        summary["total_entries"] += 1
                        
                        # Contar por nível
                        level = entry.get('levelname', 'INFO')
                        if level in summary["by_level"]:
                            summary["by_level"][level] += 1
                            
                        # Contar por devkit
                        devkit = entry.get('devkit', 'unknown')
                        if devkit not in summary["by_devkit"]:
                            summary["by_devkit"][devkit] = 0
                        summary["by_devkit"][devkit] += 1
                        
                        # Coletar operações recentes
                        if 'operation' in entry:
                            summary["recent_operations"].append({
                                "devkit": devkit,
                                "operation": entry['operation'],
                                "status": entry.get('status', 'unknown'),
                                "timestamp": entry['timestamp']
                            })
                            
                        # Coletar erros
                        if level == 'ERROR':
                            summary["errors"].append({
                                "devkit": devkit,
                                "message": entry.get('message', ''),
                                "timestamp": entry['timestamp']
                            })
                            
                    except json.JSONDecodeError:
                        continue
                        
            # Limitar listas
            summary["recent_operations"] = summary["recent_operations"][-20:]
            summary["errors"] = summary["errors"][-10:]
            
            return summary
            
        except Exception as e:
            return {"error": f"Erro ao gerar resumo: {str(e)}"}
            
    def cleanup_old_logs(self, days: int = 30):
        """Remove logs antigos"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.main_logger.info(f"Log antigo removido: {log_file.name}")
                    
            self.main_logger.info(f"Limpeza de logs concluída (>{days} dias)")
            
        except Exception as e:
            self.main_logger.error(f"Erro na limpeza de logs: {e}")
            
    def export_logs(self, export_path: Path, devkit_name: Optional[str] = None, 
                   hours: int = 24) -> bool:
        """Exporta logs para arquivo"""
        try:
            summary = self.get_log_summary(devkit_name, hours)
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "devkit_filter": devkit_name,
                "hours_filter": hours,
                "summary": summary
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.main_logger.info(f"Logs exportados para: {export_path}")
            return True
            
        except Exception as e:
            self.main_logger.error(f"Erro ao exportar logs: {e}")
            return False

class JsonFormatter(logging.Formatter):
    """Formatador JSON para logs estruturados"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "levelname": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno
        }
        
        # Adicionar dados estruturados se disponíveis
        if hasattr(record, 'structured_data'):
            log_data.update(record.structured_data)
            
        # Adicionar informações de exceção se disponíveis
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)

# Função de conveniência para obter logger
def get_retro_logger(devkit_name: str, base_path: Optional[Path] = None) -> logging.Logger:
    """Função de conveniência para obter logger de devkit"""
    if base_path is None:
        base_path = Path.cwd()
        
    logger_manager = RetroDevkitLogger(base_path)
    return logger_manager.get_logger(devkit_name)