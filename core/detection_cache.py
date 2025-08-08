"""Sistema de cache para otimizar detecção de aplicações.

Este módulo implementa um sistema de cache inteligente que armazena
resultados de detecção de aplicações para evitar execuções desnecessárias
de comandos custosos.

Author: AI Assistant
Date: 2024
"""

import json
import sqlite3
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from threading import Lock


@dataclass
class CacheEntry:
    """Representa uma entrada no cache de detecção."""
    app_name: str
    result: Dict[str, Any]
    timestamp: float
    ttl_seconds: int
    detection_method: str
    confidence_level: float
    
    def is_expired(self) -> bool:
        """Verifica se a entrada do cache expirou."""
        return time.time() - self.timestamp > self.ttl_seconds
    
    def expires_at(self) -> datetime:
        """Retorna quando a entrada expira."""
        return datetime.fromtimestamp(self.timestamp + self.ttl_seconds)


class DetectionCache:
    """Sistema de cache para resultados de detecção de aplicações."""
    
    def __init__(self, cache_dir: Optional[Path] = None, use_sqlite: bool = True):
        """Inicializa o sistema de cache.
        
        Args:
            cache_dir: Diretório para armazenar arquivos de cache
            use_sqlite: Se True, usa SQLite; se False, usa JSON
        """
        self.logger = logging.getLogger(__name__)
        self.cache_dir = cache_dir or Path.cwd() / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.use_sqlite = use_sqlite
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_lock = Lock()
        
        # Configurações padrão de TTL (em segundos)
        self.default_ttl_config = {
            "runtime": 3600,      # 1 hora para runtimes
            "application": 1800,  # 30 minutos para aplicações
            "system_tool": 7200,  # 2 horas para ferramentas do sistema
            "development_tool": 1800,  # 30 minutos para ferramentas de dev
            "default": 1800       # 30 minutos padrão
        }
        
        # Métricas de performance
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "expirations": 0
        }
        
        # Inicializar persistência
        if self.use_sqlite:
            self._init_sqlite()
        else:
            self.cache_file = self.cache_dir / "detection_cache.json"
        
        # Carregar cache existente
        self._load_cache()
    
    def _init_sqlite(self):
        """Inicializa o banco SQLite para cache."""
        self.db_path = self.cache_dir / "detection_cache.db"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    app_name TEXT PRIMARY KEY,
                    result TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    ttl_seconds INTEGER NOT NULL,
                    detection_method TEXT NOT NULL,
                    confidence_level REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON cache_entries(timestamp)
            """)
    
    def _load_cache(self):
        """Carrega cache da persistência."""
        try:
            if self.use_sqlite:
                self._load_from_sqlite()
            else:
                self._load_from_json()
            
            # Limpar entradas expiradas após carregar
            self.clear_expired_cache()
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar cache: {e}")
    
    def _load_from_sqlite(self):
        """Carrega cache do SQLite."""
        if not self.db_path.exists():
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM cache_entries"
            )
            
            for row in cursor.fetchall():
                app_name, result_json, timestamp, ttl, method, confidence = row
                
                entry = CacheEntry(
                    app_name=app_name,
                    result=json.loads(result_json),
                    timestamp=timestamp,
                    ttl_seconds=ttl,
                    detection_method=method,
                    confidence_level=confidence
                )
                
                self._memory_cache[app_name] = entry
    
    def _load_from_json(self):
        """Carrega cache do arquivo JSON."""
        if not self.cache_file.exists():
            return
        
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for app_name, entry_data in data.items():
            entry = CacheEntry(**entry_data)
            self._memory_cache[app_name] = entry
    
    def _save_cache(self):
        """Salva cache na persistência."""
        try:
            if self.use_sqlite:
                self._save_to_sqlite()
            else:
                self._save_to_json()
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")
    
    def _save_to_sqlite(self):
        """Salva cache no SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            # Limpar tabela
            conn.execute("DELETE FROM cache_entries")
            
            # Inserir entradas atuais
            for entry in self._memory_cache.values():
                conn.execute("""
                    INSERT INTO cache_entries 
                    (app_name, result, timestamp, ttl_seconds, detection_method, confidence_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry.app_name,
                    json.dumps(entry.result),
                    entry.timestamp,
                    entry.ttl_seconds,
                    entry.detection_method,
                    entry.confidence_level
                ))
    
    def _save_to_json(self):
        """Salva cache no arquivo JSON."""
        data = {}
        for app_name, entry in self._memory_cache.items():
            data[app_name] = asdict(entry)
        
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_ttl_for_app(self, app_name: str, app_type: str = "default") -> int:
        """Obtém TTL configurado para um tipo de aplicação.
        
        Args:
            app_name: Nome da aplicação
            app_type: Tipo da aplicação (runtime, application, etc.)
        
        Returns:
            TTL em segundos
        """
        return self.default_ttl_config.get(app_type, self.default_ttl_config["default"])
    
    def get_cached_result(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Obtém resultado do cache se válido.
        
        Args:
            app_name: Nome da aplicação
        
        Returns:
            Resultado do cache ou None se não encontrado/expirado
        """
        with self._cache_lock:
            entry = self._memory_cache.get(app_name)
            
            if entry is None:
                self.metrics["misses"] += 1
                return None
            
            if entry.is_expired():
                self.logger.debug(f"Cache expirado para {app_name}")
                del self._memory_cache[app_name]
                self.metrics["expirations"] += 1
                self.metrics["misses"] += 1
                return None
            
            self.metrics["hits"] += 1
            self.logger.debug(f"Cache hit para {app_name}")
            return entry.result.copy()
    
    def cache_result(self, app_name: str, result: Dict[str, Any], 
                    app_type: str = "default", detection_method: str = "unknown",
                    confidence_level: float = 1.0) -> None:
        """Armazena resultado no cache.
        
        Args:
            app_name: Nome da aplicação
            result: Resultado da detecção
            app_type: Tipo da aplicação para determinar TTL
            detection_method: Método usado para detecção
            confidence_level: Nível de confiança do resultado
        """
        ttl = self.get_ttl_for_app(app_name, app_type)
        
        entry = CacheEntry(
            app_name=app_name,
            result=result.copy(),
            timestamp=time.time(),
            ttl_seconds=ttl,
            detection_method=detection_method,
            confidence_level=confidence_level
        )
        
        with self._cache_lock:
            self._memory_cache[app_name] = entry
        
        self.logger.debug(f"Resultado cacheado para {app_name} (TTL: {ttl}s)")
        
        # Salvar periodicamente (a cada 10 entradas)
        if len(self._memory_cache) % 10 == 0:
            self._save_cache()
    
    def invalidate_cache(self, app_name: str) -> bool:
        """Invalida entrada específica do cache.
        
        Args:
            app_name: Nome da aplicação
        
        Returns:
            True se a entrada foi removida
        """
        with self._cache_lock:
            if app_name in self._memory_cache:
                del self._memory_cache[app_name]
                self.metrics["invalidations"] += 1
                self.logger.debug(f"Cache invalidado para {app_name}")
                return True
            return False
    
    def clear_expired_cache(self) -> int:
        """Remove todas as entradas expiradas do cache.
        
        Returns:
            Número de entradas removidas
        """
        expired_keys = []
        
        with self._cache_lock:
            for app_name, entry in self._memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(app_name)
            
            for key in expired_keys:
                del self._memory_cache[key]
        
        if expired_keys:
            self.logger.info(f"Removidas {len(expired_keys)} entradas expiradas do cache")
            self.metrics["expirations"] += len(expired_keys)
        
        return len(expired_keys)
    
    def clear_all_cache(self) -> None:
        """Limpa todo o cache."""
        with self._cache_lock:
            count = len(self._memory_cache)
            self._memory_cache.clear()
        
        self.logger.info(f"Cache completamente limpo ({count} entradas removidas)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        with self._cache_lock:
            total_requests = self.metrics["hits"] + self.metrics["misses"]
            hit_rate = (self.metrics["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "total_entries": len(self._memory_cache),
                "hits": self.metrics["hits"],
                "misses": self.metrics["misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "invalidations": self.metrics["invalidations"],
                "expirations": self.metrics["expirations"],
                "total_requests": total_requests
            }
    
    def get_cache_entries(self) -> List[Dict[str, Any]]:
        """Obtém lista de todas as entradas do cache.
        
        Returns:
            Lista com informações das entradas
        """
        with self._cache_lock:
            entries = []
            for entry in self._memory_cache.values():
                entries.append({
                    "app_name": entry.app_name,
                    "detection_method": entry.detection_method,
                    "confidence_level": entry.confidence_level,
                    "cached_at": datetime.fromtimestamp(entry.timestamp).isoformat(),
                    "expires_at": entry.expires_at().isoformat(),
                    "is_expired": entry.is_expired()
                })
            
            return sorted(entries, key=lambda x: x["cached_at"], reverse=True)
    
    def configure_ttl(self, app_type: str, ttl_seconds: int) -> None:
        """Configura TTL para um tipo de aplicação.
        
        Args:
            app_type: Tipo da aplicação
            ttl_seconds: TTL em segundos
        """
        self.default_ttl_config[app_type] = ttl_seconds
        self.logger.info(f"TTL configurado para {app_type}: {ttl_seconds}s")
    
    def save_and_close(self) -> None:
        """Salva cache e fecha recursos."""
        self._save_cache()
        self.logger.info("Cache salvo e recursos fechados")


# Instância global do cache
_cache_instance: Optional[DetectionCache] = None


def get_detection_cache() -> DetectionCache:
    """Obtém instância global do cache de detecção."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DetectionCache()
    return _cache_instance


def configure_cache(cache_dir: Optional[Path] = None, use_sqlite: bool = True) -> DetectionCache:
    """Configura e obtém instância do cache."""
    global _cache_instance
    _cache_instance = DetectionCache(cache_dir, use_sqlite)
    return _cache_instance