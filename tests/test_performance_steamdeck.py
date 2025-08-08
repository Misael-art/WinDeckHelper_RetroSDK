# -*- coding: utf-8 -*-
"""
Testes de performance e cenários específicos do Steam Deck
Testes para validar performance com catálogos grandes e otimizações Steam Deck
"""

import unittest
import tempfile
import shutil
import time
import threading
import concurrent.futures
import psutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import random
import string
import gc
import memory_profiler

# Adicionar diretório core ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from runtime_catalog_manager import RuntimeCatalogManager, RuntimeInfo, RuntimeStatus
from package_manager_integration import PackageManagerIntegrator, PackageManager
from configuration_manager import ConfigurationManager, ConfigProfile
from security_manager import SecurityManager
from plugin_manager import PluginManager
from catalog_update_manager import CatalogUpdateManager
from detection_engine import DetectionEngine, DetectionResult, DetectionMethod

class TestLargeCatalogPerformance(unittest.TestCase):
    """Testes de performance para catálogos grandes"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        self.catalog_manager.catalog_file = Path(self.temp_dir) / "large_catalog.json"
        
        # Configurar limites de performance
        self.max_search_time = 2.0  # segundos
        self.max_load_time = 5.0    # segundos
        self.max_memory_usage = 500 * 1024 * 1024  # 500MB
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        gc.collect()
    
    def generate_large_catalog(self, num_runtimes=10000):
        """Gerar catálogo grande para testes de performance"""
        categories = ["language", "framework", "database", "tool", "runtime", "library"]
        platforms = ["windows", "linux", "macos", "steamdeck"]
        
        runtimes = []
        
        for i in range(num_runtimes):
            # Gerar dados aleatórios mas consistentes
            random.seed(i)  # Seed consistente para reproduzibilidade
            
            name = f"runtime-{i:05d}"
            version = f"{random.randint(1, 10)}.{random.randint(0, 20)}.{random.randint(0, 100)}"
            category = random.choice(categories)
            
            # Gerar tags relevantes
            tags = [category]
            if random.random() > 0.7:
                tags.append("popular")
            if random.random() > 0.8:
                tags.append("steam-deck")
            if random.random() > 0.9:
                tags.append("gaming")
            
            # Gerar dependências ocasionais
            dependencies = []
            if random.random() > 0.7:
                num_deps = random.randint(1, 3)
                for j in range(num_deps):
                    dep_id = random.randint(0, max(0, i-1))
                    dependencies.append(f"runtime-{dep_id:05d}")
            
            runtime = RuntimeInfo(
                name=name,
                version=version,
                description=f"Generated runtime {name} for performance testing",
                category=category,
                tags=tags,
                download_url=f"https://example.com/downloads/{name}-{version}.zip",
                install_size=random.randint(10, 1000) * 1024 * 1024,  # 10MB - 1GB
                dependencies=dependencies,
                supported_platforms=random.sample(platforms, random.randint(1, len(platforms))),
                checksum=f"checksum{i:05d}",
                metadata={
                    "performance_tier": random.choice(["low", "medium", "high"]),
                    "steam_deck_optimized": "steam-deck" in tags,
                    "install_complexity": random.choice(["simple", "moderate", "complex"])
                }
            )
            
            runtimes.append(runtime)
        
        return runtimes
    
    def test_large_catalog_loading_performance(self):
        """Testar performance de carregamento de catálogo grande"""
        # 1. Gerar catálogo grande
        print(f"\nGerando catálogo com 10.000 runtimes...")
        large_runtimes = self.generate_large_catalog(10000)
        
        # 2. Salvar catálogo
        catalog_data = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "runtimes": [runtime.__dict__ for runtime in large_runtimes]
        }
        
        with open(self.catalog_manager.catalog_file, 'w') as f:
            json.dump(catalog_data, f)
        
        # 3. Medir tempo de carregamento
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        self.catalog_manager.load_catalog()
        
        load_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss
        memory_used = end_memory - start_memory
        
        print(f"Tempo de carregamento: {load_time:.2f}s")
        print(f"Memória utilizada: {memory_used / 1024 / 1024:.2f}MB")
        
        # 4. Verificar limites de performance
        self.assertLess(load_time, self.max_load_time, 
                       f"Carregamento muito lento: {load_time:.2f}s > {self.max_load_time}s")
        self.assertLess(memory_used, self.max_memory_usage,
                       f"Uso de memória excessivo: {memory_used / 1024 / 1024:.2f}MB")
        
        # 5. Verificar integridade dos dados
        loaded_runtimes = self.catalog_manager.get_all_runtimes()
        self.assertEqual(len(loaded_runtimes), 10000)
    
    def test_search_performance_large_catalog(self):
        """Testar performance de busca em catálogo grande"""
        # 1. Carregar catálogo grande
        large_runtimes = self.generate_large_catalog(10000)
        for runtime in large_runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 2. Testes de busca por diferentes critérios
        search_tests = [
            {"name": "Busca por nome", "kwargs": {"name_pattern": "runtime-00500"}},
            {"name": "Busca por categoria", "kwargs": {"category": "language"}},
            {"name": "Busca por tags", "kwargs": {"tags": ["popular"]}},
            {"name": "Busca por plataforma", "kwargs": {"platform": "steamdeck"}},
            {"name": "Busca complexa", "kwargs": {"category": "framework", "tags": ["steam-deck"], "platform": "windows"}}
        ]
        
        for test in search_tests:
            with self.subTest(search_type=test["name"]):
                start_time = time.time()
                
                results = self.catalog_manager.search_runtimes(**test["kwargs"])
                
                search_time = time.time() - start_time
                
                print(f"{test['name']}: {search_time:.3f}s, {len(results)} resultados")
                
                # Verificar limite de tempo
                self.assertLess(search_time, self.max_search_time,
                               f"Busca muito lenta: {search_time:.3f}s > {self.max_search_time}s")
                
                # Verificar que resultados são válidos
                self.assertIsInstance(results, list)
                for result in results:
                    self.assertIsInstance(result, RuntimeInfo)
    
    def test_concurrent_operations_performance(self):
        """Testar performance de operações concorrentes"""
        # 1. Carregar catálogo médio
        medium_runtimes = self.generate_large_catalog(1000)
        for runtime in medium_runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 2. Definir operações concorrentes
        def search_operation(thread_id):
            """Operação de busca para thread"""
            results = []
            for i in range(10):
                search_results = self.catalog_manager.search_runtimes(
                    category=random.choice(["language", "framework", "tool"])
                )
                results.extend(search_results)
            return len(results)
        
        def status_check_operation(thread_id):
            """Operação de verificação de status"""
            statuses = []
            for i in range(20):
                runtime_name = f"runtime-{random.randint(0, 999):05d}"
                status = self.catalog_manager.get_installation_status(runtime_name)
                statuses.append(status)
            return len(statuses)
        
        # 3. Executar operações concorrentes
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submeter tarefas de busca
            search_futures = [executor.submit(search_operation, i) for i in range(5)]
            
            # Submeter tarefas de verificação de status
            status_futures = [executor.submit(status_check_operation, i) for i in range(5)]
            
            # Aguardar conclusão
            search_results = [future.result() for future in search_futures]
            status_results = [future.result() for future in status_futures]
        
        total_time = time.time() - start_time
        
        print(f"Operações concorrentes completadas em {total_time:.2f}s")
        print(f"Resultados de busca: {sum(search_results)}")
        print(f"Verificações de status: {sum(status_results)}")
        
        # 4. Verificar performance
        self.assertLess(total_time, 10.0, "Operações concorrentes muito lentas")
        self.assertGreater(sum(search_results), 0, "Nenhum resultado de busca")
        self.assertGreater(sum(status_results), 0, "Nenhuma verificação de status")
    
    def test_memory_usage_optimization(self):
        """Testar otimização de uso de memória"""
        # 1. Medir memória inicial
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss
        
        # 2. Carregar catálogo grande em lotes
        batch_size = 1000
        total_runtimes = 5000
        
        memory_measurements = []
        
        for batch_start in range(0, total_runtimes, batch_size):
            batch_end = min(batch_start + batch_size, total_runtimes)
            batch_runtimes = self.generate_large_catalog(batch_size)
            
            # Adicionar lote ao catálogo
            for runtime in batch_runtimes:
                self.catalog_manager.add_runtime(runtime)
            
            # Medir memória após cada lote
            current_memory = psutil.Process().memory_info().rss
            memory_used = current_memory - initial_memory
            memory_measurements.append(memory_used)
            
            print(f"Lote {batch_start//batch_size + 1}: {memory_used / 1024 / 1024:.2f}MB")
        
        # 3. Verificar crescimento linear da memória
        final_memory = memory_measurements[-1]
        memory_per_runtime = final_memory / total_runtimes
        
        print(f"Memória total utilizada: {final_memory / 1024 / 1024:.2f}MB")
        print(f"Memória por runtime: {memory_per_runtime / 1024:.2f}KB")
        
        # 4. Verificar limites
        self.assertLess(final_memory, self.max_memory_usage * 2,  # Limite mais alto para teste grande
                       "Uso de memória excessivo")
        self.assertLess(memory_per_runtime, 50 * 1024,  # 50KB por runtime
                       "Uso de memória por runtime muito alto")
        
        # 5. Testar limpeza de memória
        self.catalog_manager.clear_catalog()
        gc.collect()
        
        final_cleanup_memory = psutil.Process().memory_info().rss
        memory_after_cleanup = final_cleanup_memory - initial_memory
        
        print(f"Memória após limpeza: {memory_after_cleanup / 1024 / 1024:.2f}MB")
        
        # Verificar que a memória foi liberada (permitir alguma margem)
        self.assertLess(memory_after_cleanup, final_memory * 0.3,
                       "Memória não foi adequadamente liberada")

class TestSteamDeckSpecificScenarios(unittest.TestCase):
    """Testes específicos para cenários Steam Deck"""
    
    def setUp(self):
        """Configurar ambiente Steam Deck simulado"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        self.detection_engine = DetectionEngine()
        self.config_manager = ConfigurationManager()
        
        # Configurar ambiente Steam Deck
        self.steam_deck_env = {
            "HOME": "/home/deck",
            "USER": "deck",
            "DESKTOP_SESSION": "plasma",
            "XDG_CURRENT_DESKTOP": "KDE"
        }
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('platform.machine')
    @patch('os.path.exists')
    @patch('subprocess.run')
    @patch.dict('os.environ', {'HOME': '/home/deck', 'USER': 'deck'})
    def test_steam_deck_detection_performance(self, mock_subprocess, mock_exists, mock_machine):
        """Testar performance de detecção Steam Deck"""
        # 1. Configurar mocks para Steam Deck
        mock_machine.return_value = "x86_64"
        mock_exists.side_effect = lambda path: any([
            "/home/deck" in str(path),
            "/usr/bin/steamos-session-select" in str(path),
            "/etc/steamos-release" in str(path)
        ])
        
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "SteamOS 3.4.6"
        
        # 2. Medir tempo de detecção
        detection_times = []
        
        for i in range(100):  # 100 detecções para média
            start_time = time.time()
            
            is_steam_deck = self.catalog_manager.is_steam_deck()
            
            detection_time = time.time() - start_time
            detection_times.append(detection_time)
        
        # 3. Calcular estatísticas
        avg_detection_time = sum(detection_times) / len(detection_times)
        max_detection_time = max(detection_times)
        min_detection_time = min(detection_times)
        
        print(f"\nTempo médio de detecção Steam Deck: {avg_detection_time*1000:.2f}ms")
        print(f"Tempo máximo: {max_detection_time*1000:.2f}ms")
        print(f"Tempo mínimo: {min_detection_time*1000:.2f}ms")
        
        # 4. Verificar limites de performance
        self.assertLess(avg_detection_time, 0.1, "Detecção Steam Deck muito lenta")
        self.assertLess(max_detection_time, 0.5, "Pico de detecção muito alto")
    
    def test_steam_deck_optimized_runtime_filtering(self):
        """Testar filtragem otimizada de runtimes para Steam Deck"""
        # 1. Criar mix de runtimes (otimizados e não otimizados)
        runtimes = []
        
        # Runtimes otimizados para Steam Deck
        for i in range(100):
            runtime = RuntimeInfo(
                name=f"steamdeck-runtime-{i}",
                version="1.0.0",
                description=f"Steam Deck optimized runtime {i}",
                category="gaming",
                tags=["steam-deck", "gaming", "optimized"],
                download_url=f"https://example.com/steamdeck-runtime-{i}.zip",
                install_size=random.randint(50, 200) * 1024 * 1024,
                dependencies=[],
                supported_platforms=["steamdeck", "linux"],
                checksum=f"steamdeck{i}checksum",
                metadata={
                    "steam_deck_optimized": True,
                    "performance_profile": "gaming",
                    "power_efficiency": "high"
                }
            )
            runtimes.append(runtime)
        
        # Runtimes genéricos
        for i in range(400):
            runtime = RuntimeInfo(
                name=f"generic-runtime-{i}",
                version="1.0.0",
                description=f"Generic runtime {i}",
                category=random.choice(["development", "productivity", "utility"]),
                tags=["generic", "cross-platform"],
                download_url=f"https://example.com/generic-runtime-{i}.zip",
                install_size=random.randint(10, 500) * 1024 * 1024,
                dependencies=[],
                supported_platforms=["windows", "linux", "macos"],
                checksum=f"generic{i}checksum",
                metadata={
                    "steam_deck_optimized": False
                }
            )
            runtimes.append(runtime)
        
        # 2. Adicionar todos os runtimes
        for runtime in runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 3. Testar filtragem otimizada
        start_time = time.time()
        
        steam_deck_runtimes = self.catalog_manager.search_runtimes(
            tags=["steam-deck"],
            platform="steamdeck"
        )
        
        filter_time = time.time() - start_time
        
        print(f"\nFiltragem Steam Deck: {filter_time*1000:.2f}ms")
        print(f"Runtimes encontrados: {len(steam_deck_runtimes)}")
        
        # 4. Verificar resultados
        self.assertEqual(len(steam_deck_runtimes), 100, "Número incorreto de runtimes Steam Deck")
        self.assertLess(filter_time, 0.5, "Filtragem muito lenta")
        
        # Verificar que todos são otimizados para Steam Deck
        for runtime in steam_deck_runtimes:
            self.assertIn("steam-deck", runtime.tags)
            self.assertIn("steamdeck", runtime.supported_platforms)
    
    def test_steam_deck_power_management_simulation(self):
        """Testar simulação de gerenciamento de energia Steam Deck"""
        # 1. Simular diferentes modos de energia
        power_modes = [
            {"name": "performance", "cpu_limit": 100, "gpu_limit": 100, "tdp": 15},
            {"name": "balanced", "cpu_limit": 80, "gpu_limit": 80, "tdp": 10},
            {"name": "power_save", "cpu_limit": 60, "gpu_limit": 60, "tdp": 7}
        ]
        
        # 2. Criar runtimes com diferentes requisitos de energia
        power_intensive_runtimes = []
        
        for i in range(50):
            runtime = RuntimeInfo(
                name=f"power-runtime-{i}",
                version="1.0.0",
                description=f"Power intensive runtime {i}",
                category="gaming",
                tags=["steam-deck", "gaming", "high-performance"],
                download_url=f"https://example.com/power-runtime-{i}.zip",
                install_size=random.randint(100, 1000) * 1024 * 1024,
                dependencies=[],
                supported_platforms=["steamdeck"],
                checksum=f"power{i}checksum",
                metadata={
                    "power_requirements": {
                        "min_tdp": random.randint(5, 15),
                        "recommended_tdp": random.randint(10, 15),
                        "cpu_intensive": random.choice([True, False]),
                        "gpu_intensive": random.choice([True, False])
                    },
                    "performance_scaling": {
                        "low_power": random.randint(30, 60),
                        "balanced": random.randint(60, 85),
                        "high_power": random.randint(85, 100)
                    }
                }
            )
            power_intensive_runtimes.append(runtime)
        
        # 3. Adicionar runtimes
        for runtime in power_intensive_runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 4. Testar filtragem por modo de energia
        for power_mode in power_modes:
            start_time = time.time()
            
            # Filtrar runtimes compatíveis com o modo de energia
            compatible_runtimes = []
            
            for runtime in power_intensive_runtimes:
                power_req = runtime.metadata.get("power_requirements", {})
                min_tdp = power_req.get("min_tdp", 0)
                
                if min_tdp <= power_mode["tdp"]:
                    compatible_runtimes.append(runtime)
            
            filter_time = time.time() - start_time
            
            print(f"\nModo {power_mode['name']}: {len(compatible_runtimes)} runtimes compatíveis")
            print(f"Tempo de filtragem: {filter_time*1000:.2f}ms")
            
            # Verificar performance
            self.assertLess(filter_time, 0.1, f"Filtragem lenta no modo {power_mode['name']}")
    
    def test_steam_deck_storage_optimization(self):
        """Testar otimização de armazenamento Steam Deck"""
        # 1. Simular limitações de armazenamento Steam Deck
        storage_scenarios = [
            {"name": "64GB eMMC", "total_space": 64 * 1024 * 1024 * 1024, "available_space": 20 * 1024 * 1024 * 1024},
            {"name": "256GB NVMe", "total_space": 256 * 1024 * 1024 * 1024, "available_space": 100 * 1024 * 1024 * 1024},
            {"name": "512GB NVMe", "total_space": 512 * 1024 * 1024 * 1024, "available_space": 300 * 1024 * 1024 * 1024}
        ]
        
        # 2. Criar runtimes de diferentes tamanhos
        size_varied_runtimes = []
        
        sizes = [10, 50, 100, 500, 1000, 2000, 5000]  # MB
        
        for i, size_mb in enumerate(sizes * 10):  # 70 runtimes total
            runtime = RuntimeInfo(
                name=f"size-runtime-{i}",
                version="1.0.0",
                description=f"Runtime with {size_mb}MB size",
                category="development",
                tags=["steam-deck", "size-optimized"],
                download_url=f"https://example.com/size-runtime-{i}.zip",
                install_size=size_mb * 1024 * 1024,
                dependencies=[],
                supported_platforms=["steamdeck"],
                checksum=f"size{i}checksum",
                metadata={
                    "compression_ratio": random.uniform(0.3, 0.8),
                    "install_type": random.choice(["full", "minimal", "portable"]),
                    "storage_efficiency": random.choice(["high", "medium", "low"])
                }
            )
            size_varied_runtimes.append(runtime)
        
        # 3. Adicionar runtimes
        for runtime in size_varied_runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 4. Testar otimização de armazenamento para cada cenário
        for scenario in storage_scenarios:
            start_time = time.time()
            
            # Filtrar runtimes que cabem no espaço disponível
            fitting_runtimes = []
            total_size = 0
            
            # Ordenar por tamanho (menores primeiro)
            sorted_runtimes = sorted(size_varied_runtimes, key=lambda r: r.install_size)
            
            for runtime in sorted_runtimes:
                if total_size + runtime.install_size <= scenario["available_space"]:
                    fitting_runtimes.append(runtime)
                    total_size += runtime.install_size
            
            optimization_time = time.time() - start_time
            
            print(f"\n{scenario['name']}:")
            print(f"  Runtimes que cabem: {len(fitting_runtimes)}")
            print(f"  Espaço utilizado: {total_size / 1024 / 1024 / 1024:.2f}GB")
            print(f"  Espaço disponível: {scenario['available_space'] / 1024 / 1024 / 1024:.2f}GB")
            print(f"  Tempo de otimização: {optimization_time*1000:.2f}ms")
            
            # Verificar eficiência
            self.assertLess(optimization_time, 0.1, "Otimização de armazenamento lenta")
            self.assertLessEqual(total_size, scenario["available_space"], "Excedeu espaço disponível")
            
            # Verificar utilização eficiente do espaço (pelo menos 80% se possível)
            utilization = total_size / scenario["available_space"]
            if len(size_varied_runtimes) > len(fitting_runtimes):
                # Se nem todos os runtimes cabem, deve usar pelo menos 80% do espaço
                self.assertGreater(utilization, 0.8, "Utilização de espaço ineficiente")
    
    def test_steam_deck_thermal_management_simulation(self):
        """Testar simulação de gerenciamento térmico Steam Deck"""
        # 1. Simular condições térmicas
        thermal_conditions = [
            {"name": "cool", "ambient_temp": 20, "max_cpu_temp": 85, "max_gpu_temp": 90},
            {"name": "normal", "ambient_temp": 25, "max_cpu_temp": 80, "max_gpu_temp": 85},
            {"name": "warm", "ambient_temp": 30, "max_cpu_temp": 75, "max_gpu_temp": 80},
            {"name": "hot", "ambient_temp": 35, "max_cpu_temp": 70, "max_gpu_temp": 75}
        ]
        
        # 2. Criar runtimes com diferentes perfis térmicos
        thermal_runtimes = []
        
        for i in range(40):
            runtime = RuntimeInfo(
                name=f"thermal-runtime-{i}",
                version="1.0.0",
                description=f"Thermal profile runtime {i}",
                category="gaming",
                tags=["steam-deck", "thermal-aware"],
                download_url=f"https://example.com/thermal-runtime-{i}.zip",
                install_size=random.randint(100, 500) * 1024 * 1024,
                dependencies=[],
                supported_platforms=["steamdeck"],
                checksum=f"thermal{i}checksum",
                metadata={
                    "thermal_profile": {
                        "cpu_load": random.randint(20, 100),
                        "gpu_load": random.randint(20, 100),
                        "heat_generation": random.choice(["low", "medium", "high"]),
                        "thermal_throttling_sensitive": random.choice([True, False])
                    },
                    "performance_scaling": {
                        "thermal_limit_60c": random.randint(50, 70),
                        "thermal_limit_70c": random.randint(70, 85),
                        "thermal_limit_80c": random.randint(85, 100)
                    }
                }
            )
            thermal_runtimes.append(runtime)
        
        # 3. Adicionar runtimes
        for runtime in thermal_runtimes:
            self.catalog_manager.add_runtime(runtime)
        
        # 4. Testar adaptação térmica
        for condition in thermal_conditions:
            start_time = time.time()
            
            # Filtrar runtimes adequados para a condição térmica
            suitable_runtimes = []
            
            for runtime in thermal_runtimes:
                thermal_profile = runtime.metadata.get("thermal_profile", {})
                heat_gen = thermal_profile.get("heat_generation", "medium")
                
                # Lógica simplificada de adequação térmica
                is_suitable = False
                if condition["name"] == "cool":
                    is_suitable = True  # Todos adequados
                elif condition["name"] == "normal":
                    is_suitable = heat_gen in ["low", "medium"]
                elif condition["name"] == "warm":
                    is_suitable = heat_gen == "low"
                else:  # hot
                    is_suitable = heat_gen == "low" and not thermal_profile.get("thermal_throttling_sensitive", False)
                
                if is_suitable:
                    suitable_runtimes.append(runtime)
            
            adaptation_time = time.time() - start_time
            
            print(f"\nCondição térmica '{condition['name']}' ({condition['ambient_temp']}°C):")
            print(f"  Runtimes adequados: {len(suitable_runtimes)}")
            print(f"  Tempo de adaptação: {adaptation_time*1000:.2f}ms")
            
            # Verificar performance e lógica
            self.assertLess(adaptation_time, 0.05, "Adaptação térmica lenta")
            
            # Verificar que condições mais quentes têm menos runtimes adequados
            if condition["name"] == "hot":
                self.assertLess(len(suitable_runtimes), len(thermal_runtimes) * 0.5,
                               "Muitos runtimes adequados para condição quente")

if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Verificar se psutil está disponível
    try:
        import psutil
    except ImportError:
        print("Aviso: psutil não está disponível. Alguns testes de performance podem falhar.")
    
    # Executar testes com verbosidade
    unittest.main(verbosity=2, buffer=True)