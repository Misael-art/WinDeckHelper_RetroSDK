"""Testes unitários para o sistema de cache de detecção.

Author: AI Assistant
Date: 2024
"""

import unittest
import tempfile
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.detection_cache import DetectionCache, CacheEntry, get_detection_cache, configure_cache


class TestCacheEntry(unittest.TestCase):
    """Testes para a classe CacheEntry."""
    
    def test_cache_entry_creation(self):
        """Testa criação de entrada de cache."""
        entry = CacheEntry(
            app_name="git",
            result={"installed": True, "version": "2.40.0"},
            timestamp=time.time(),
            ttl_seconds=3600,
            detection_method="registry",
            confidence_level=0.95
        )
        
        self.assertEqual(entry.app_name, "git")
        self.assertTrue(entry.result["installed"])
        self.assertEqual(entry.ttl_seconds, 3600)
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiration(self):
        """Testa expiração de entrada de cache."""
        # Entrada já expirada
        entry = CacheEntry(
            app_name="test",
            result={},
            timestamp=time.time() - 7200,  # 2 horas atrás
            ttl_seconds=3600,  # TTL de 1 hora
            detection_method="test",
            confidence_level=1.0
        )
        
        self.assertTrue(entry.is_expired())
    
    def test_expires_at(self):
        """Testa cálculo de data de expiração."""
        timestamp = time.time()
        entry = CacheEntry(
            app_name="test",
            result={},
            timestamp=timestamp,
            ttl_seconds=3600,
            detection_method="test",
            confidence_level=1.0
        )
        
        expires_at = entry.expires_at()
        expected_timestamp = timestamp + 3600
        
        # Verificar se a diferença é menor que 1 segundo
        self.assertLess(abs(expires_at.timestamp() - expected_timestamp), 1)


class TestDetectionCache(unittest.TestCase):
    """Testes para a classe DetectionCache."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = DetectionCache(cache_dir=self.temp_dir, use_sqlite=False)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_initialization(self):
        """Testa inicialização do cache."""
        self.assertTrue(self.temp_dir.exists())
        self.assertIsInstance(self.cache.default_ttl_config, dict)
        self.assertIn("default", self.cache.default_ttl_config)
    
    def test_cache_result_and_get(self):
        """Testa armazenamento e recuperação de resultado."""
        result = {"installed": True, "version": "2.40.0", "path": "/usr/bin/git"}
        
        # Armazenar resultado
        self.cache.cache_result(
            app_name="git",
            result=result,
            app_type="runtime",
            detection_method="registry",
            confidence_level=0.95
        )
        
        # Recuperar resultado
        cached_result = self.cache.get_cached_result("git")
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result["installed"], True)
        self.assertEqual(cached_result["version"], "2.40.0")
        self.assertEqual(self.cache.metrics["hits"], 1)
    
    def test_cache_miss(self):
        """Testa cache miss."""
        result = self.cache.get_cached_result("nonexistent")
        
        self.assertIsNone(result)
        self.assertEqual(self.cache.metrics["misses"], 1)
    
    def test_cache_expiration(self):
        """Testa expiração automática de cache."""
        # Configurar TTL muito baixo
        self.cache.configure_ttl("test", 1)  # 1 segundo
        
        result = {"installed": True}
        self.cache.cache_result("test_app", result, app_type="test")
        
        # Verificar que está no cache
        cached = self.cache.get_cached_result("test_app")
        self.assertIsNotNone(cached)
        
        # Aguardar expiração
        time.sleep(1.1)
        
        # Verificar que expirou
        cached = self.cache.get_cached_result("test_app")
        self.assertIsNone(cached)
        self.assertEqual(self.cache.metrics["expirations"], 1)
    
    def test_invalidate_cache(self):
        """Testa invalidação manual de cache."""
        result = {"installed": True}
        self.cache.cache_result("test_app", result)
        
        # Verificar que está no cache
        self.assertIsNotNone(self.cache.get_cached_result("test_app"))
        
        # Invalidar
        invalidated = self.cache.invalidate_cache("test_app")
        self.assertTrue(invalidated)
        
        # Verificar que foi removido
        self.assertIsNone(self.cache.get_cached_result("test_app"))
        self.assertEqual(self.cache.metrics["invalidations"], 1)
    
    def test_clear_expired_cache(self):
        """Testa limpeza de entradas expiradas."""
        # Adicionar entrada que expira rapidamente
        self.cache.configure_ttl("test", 1)
        self.cache.cache_result("expired_app", {"test": True}, app_type="test")
        
        # Adicionar entrada que não expira
        self.cache.cache_result("valid_app", {"test": True}, app_type="runtime")
        
        # Aguardar expiração
        time.sleep(1.1)
        
        # Limpar expiradas
        removed_count = self.cache.clear_expired_cache()
        
        self.assertEqual(removed_count, 1)
        self.assertIsNone(self.cache.get_cached_result("expired_app"))
        self.assertIsNotNone(self.cache.get_cached_result("valid_app"))
    
    def test_clear_all_cache(self):
        """Testa limpeza completa do cache."""
        self.cache.cache_result("app1", {"test": True})
        self.cache.cache_result("app2", {"test": True})
        
        self.assertEqual(len(self.cache._memory_cache), 2)
        
        self.cache.clear_all_cache()
        
        self.assertEqual(len(self.cache._memory_cache), 0)
    
    def test_get_cache_stats(self):
        """Testa obtenção de estatísticas do cache."""
        # Adicionar algumas entradas e acessos
        self.cache.cache_result("app1", {"test": True})
        self.cache.get_cached_result("app1")  # hit
        self.cache.get_cached_result("nonexistent")  # miss
        
        stats = self.cache.get_cache_stats()
        
        self.assertEqual(stats["total_entries"], 1)
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate_percent"], 50.0)
        self.assertEqual(stats["total_requests"], 2)
    
    def test_get_cache_entries(self):
        """Testa obtenção de lista de entradas."""
        self.cache.cache_result(
            "git",
            {"installed": True},
            detection_method="registry",
            confidence_level=0.95
        )
        
        entries = self.cache.get_cache_entries()
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["app_name"], "git")
        self.assertEqual(entries[0]["detection_method"], "registry")
        self.assertEqual(entries[0]["confidence_level"], 0.95)
        self.assertIn("cached_at", entries[0])
        self.assertIn("expires_at", entries[0])
    
    def test_ttl_configuration(self):
        """Testa configuração de TTL."""
        original_ttl = self.cache.get_ttl_for_app("test", "runtime")
        
        # Configurar novo TTL
        new_ttl = 7200
        self.cache.configure_ttl("runtime", new_ttl)
        
        updated_ttl = self.cache.get_ttl_for_app("test", "runtime")
        
        self.assertNotEqual(original_ttl, updated_ttl)
        self.assertEqual(updated_ttl, new_ttl)
    
    def test_json_persistence(self):
        """Testa persistência em JSON."""
        # Adicionar entrada
        result = {"installed": True, "version": "1.0.0"}
        self.cache.cache_result("test_app", result)
        
        # Salvar
        self.cache._save_cache()
        
        # Verificar arquivo JSON
        self.assertTrue(self.cache.cache_file.exists())
        
        # Criar novo cache e carregar
        new_cache = DetectionCache(cache_dir=self.temp_dir, use_sqlite=False)
        
        # Verificar se carregou corretamente
        cached_result = new_cache.get_cached_result("test_app")
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result["version"], "1.0.0")


class TestDetectionCacheSQLite(unittest.TestCase):
    """Testes para DetectionCache com SQLite."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = DetectionCache(cache_dir=self.temp_dir, use_sqlite=True)
    
    def tearDown(self):
        """Limpeza após cada teste."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sqlite_persistence(self):
        """Testa persistência em SQLite."""
        # Adicionar entrada
        result = {"installed": True, "version": "1.0.0"}
        self.cache.cache_result("test_app", result)
        
        # Salvar
        self.cache._save_cache()
        
        # Verificar arquivo SQLite
        self.assertTrue(self.cache.db_path.exists())
        
        # Criar novo cache e carregar
        new_cache = DetectionCache(cache_dir=self.temp_dir, use_sqlite=True)
        
        # Verificar se carregou corretamente
        cached_result = new_cache.get_cached_result("test_app")
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result["version"], "1.0.0")


class TestGlobalCacheInstance(unittest.TestCase):
    """Testes para instância global do cache."""
    
    def test_get_detection_cache(self):
        """Testa obtenção da instância global."""
        cache1 = get_detection_cache()
        cache2 = get_detection_cache()
        
        # Deve retornar a mesma instância
        self.assertIs(cache1, cache2)
    
    def test_configure_cache(self):
        """Testa configuração da instância global."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            cache = configure_cache(cache_dir=temp_dir, use_sqlite=False)
            
            # Verificar se foi configurado corretamente
            self.assertEqual(cache.cache_dir, temp_dir)
            self.assertFalse(cache.use_sqlite)
            
            # Verificar se get_detection_cache retorna a mesma instância
            same_cache = get_detection_cache()
            self.assertIs(cache, same_cache)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()