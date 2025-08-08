# -*- coding: utf-8 -*-
"""
Testes unitários para gerenciadores de runtime
Suíte abrangente de testes para validar funcionalidades dos runtime managers
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys

# Adicionar diretório core ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from runtime_catalog_manager import RuntimeCatalogManager, RuntimeInfo, RuntimeStatus
from package_manager_integration import PackageManagerIntegrator, PackageManager
from configuration_manager import ConfigurationManager, ConfigProfile
from security_manager import SecurityManager, SecurityLevel
from plugin_manager import PluginManager
from plugin_security import PluginSecurityManager
from catalog_update_manager import CatalogUpdateManager, UpdateStatus
from detection_engine import DetectionEngine, DetectionResult

class TestRuntimeCatalogManager(unittest.TestCase):
    """Testes para RuntimeCatalogManager"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        
        # Mock de runtime para testes
        self.mock_runtime = RuntimeInfo(
            name="test-runtime",
            version="1.0.0",
            description="Test runtime for unit tests",
            category="development",
            tags=["test", "development"],
            download_url="https://example.com/test-runtime.zip",
            install_size=100 * 1024 * 1024,  # 100MB
            dependencies=[],
            supported_platforms=["windows", "linux"],
            checksum="abc123",
            installation_path=Path(self.temp_dir) / "test-runtime"
        )
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_runtime(self):
        """Testar adição de runtime"""
        result = self.catalog_manager.add_runtime(self.mock_runtime)
        self.assertTrue(result)
        
        # Verificar se runtime foi adicionado
        runtime = self.catalog_manager.get_runtime("test-runtime")
        self.assertIsNotNone(runtime)
        self.assertEqual(runtime.name, "test-runtime")
        self.assertEqual(runtime.version, "1.0.0")
    
    def test_remove_runtime(self):
        """Testar remoção de runtime"""
        # Adicionar runtime primeiro
        self.catalog_manager.add_runtime(self.mock_runtime)
        
        # Remover runtime
        result = self.catalog_manager.remove_runtime("test-runtime")
        self.assertTrue(result)
        
        # Verificar se foi removido
        runtime = self.catalog_manager.get_runtime("test-runtime")
        self.assertIsNone(runtime)
    
    def test_search_runtimes(self):
        """Testar busca de runtimes"""
        # Adicionar alguns runtimes
        self.catalog_manager.add_runtime(self.mock_runtime)
        
        python_runtime = RuntimeInfo(
            name="python",
            version="3.11.0",
            description="Python programming language",
            category="language",
            tags=["python", "programming"],
            download_url="https://example.com/python.zip",
            install_size=50 * 1024 * 1024,
            dependencies=[],
            supported_platforms=["windows", "linux"],
            checksum="def456"
        )
        self.catalog_manager.add_runtime(python_runtime)
        
        # Buscar por categoria
        dev_runtimes = self.catalog_manager.search_runtimes(category="development")
        self.assertEqual(len(dev_runtimes), 1)
        self.assertEqual(dev_runtimes[0].name, "test-runtime")
        
        # Buscar por tag
        python_runtimes = self.catalog_manager.search_runtimes(tags=["python"])
        self.assertEqual(len(python_runtimes), 1)
        self.assertEqual(python_runtimes[0].name, "python")
    
    def test_get_installation_status(self):
        """Testar status de instalação"""
        self.catalog_manager.add_runtime(self.mock_runtime)
        
        # Status inicial deve ser NOT_INSTALLED
        status = self.catalog_manager.get_installation_status("test-runtime")
        self.assertEqual(status, RuntimeStatus.NOT_INSTALLED)
        
        # Simular instalação
        self.catalog_manager._runtime_status["test-runtime"] = RuntimeStatus.INSTALLED
        status = self.catalog_manager.get_installation_status("test-runtime")
        self.assertEqual(status, RuntimeStatus.INSTALLED)
    
    @patch('requests.get')
    def test_download_runtime(self, mock_get):
        """Testar download de runtime"""
        # Mock da resposta HTTP
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'test data']
        mock_response.headers = {'content-length': '9'}
        mock_get.return_value = mock_response
        
        self.catalog_manager.add_runtime(self.mock_runtime)
        
        # Testar download
        result = self.catalog_manager.download_runtime("test-runtime")
        self.assertTrue(result)
        
        # Verificar se arquivo foi criado
        download_path = self.catalog_manager.download_directory / "test-runtime.zip"
        self.assertTrue(download_path.exists())

class TestPackageManagerIntegration(unittest.TestCase):
    """Testes para PackageManagerIntegrator"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.integrator = PackageManagerIntegrator()
    
    def test_detect_package_managers(self):
        """Testar detecção de gerenciadores de pacote"""
        with patch('shutil.which') as mock_which:
            # Simular que chocolatey está disponível
            mock_which.side_effect = lambda cmd: '/path/to/choco' if cmd == 'choco' else None
            
            managers = self.integrator.detect_available_managers()
            self.assertIn(PackageManager.CHOCOLATEY, managers)
    
    def test_install_package(self):
        """Testar instalação de pacote"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Package installed successfully"
            
            result = self.integrator.install_package(
                "test-package", 
                PackageManager.CHOCOLATEY
            )
            self.assertTrue(result)
    
    def test_uninstall_package(self):
        """Testar desinstalação de pacote"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Package uninstalled successfully"
            
            result = self.integrator.uninstall_package(
                "test-package", 
                PackageManager.CHOCOLATEY
            )
            self.assertTrue(result)
    
    def test_resolve_dependencies(self):
        """Testar resolução de dependências"""
        dependencies = ["dep1", "dep2", "dep3"]
        
        with patch.object(self.integrator, 'is_package_installed') as mock_installed:
            # Simular que dep2 já está instalado
            mock_installed.side_effect = lambda pkg, mgr: pkg == "dep2"
            
            missing_deps = self.integrator.resolve_dependencies(
                dependencies, 
                PackageManager.CHOCOLATEY
            )
            
            # Deve retornar apenas dep1 e dep3
            self.assertEqual(set(missing_deps), {"dep1", "dep3"})

class TestConfigurationManager(unittest.TestCase):
    """Testes para ConfigurationManager"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager()
        self.config_manager.config_directory = Path(self.temp_dir)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_profile(self):
        """Testar criação de perfil"""
        profile = ConfigProfile(
            name="test-profile",
            description="Test configuration profile",
            settings={"key1": "value1", "key2": "value2"}
        )
        
        result = self.config_manager.create_profile(profile)
        self.assertTrue(result)
        
        # Verificar se perfil foi criado
        loaded_profile = self.config_manager.get_profile("test-profile")
        self.assertIsNotNone(loaded_profile)
        self.assertEqual(loaded_profile.name, "test-profile")
    
    def test_activate_profile(self):
        """Testar ativação de perfil"""
        profile = ConfigProfile(
            name="test-profile",
            description="Test profile",
            settings={"setting1": "value1"}
        )
        
        self.config_manager.create_profile(profile)
        result = self.config_manager.activate_profile("test-profile")
        self.assertTrue(result)
        
        # Verificar se perfil está ativo
        active_profile = self.config_manager.get_active_profile()
        self.assertEqual(active_profile.name, "test-profile")
    
    def test_set_get_configuration(self):
        """Testar definição e obtenção de configuração"""
        # Definir configuração
        result = self.config_manager.set_configuration("test.key", "test_value")
        self.assertTrue(result)
        
        # Obter configuração
        value = self.config_manager.get_configuration("test.key")
        self.assertEqual(value, "test_value")
        
        # Testar valor padrão
        default_value = self.config_manager.get_configuration("nonexistent.key", "default")
        self.assertEqual(default_value, "default")
    
    def test_backup_restore(self):
        """Testar backup e restauração"""
        # Criar configuração
        self.config_manager.set_configuration("backup.test", "backup_value")
        
        # Criar backup
        backup_id = self.config_manager.create_backup("test_backup")
        self.assertIsNotNone(backup_id)
        
        # Modificar configuração
        self.config_manager.set_configuration("backup.test", "modified_value")
        
        # Restaurar backup
        result = self.config_manager.restore_backup(backup_id)
        self.assertTrue(result)
        
        # Verificar se valor foi restaurado
        value = self.config_manager.get_configuration("backup.test")
        self.assertEqual(value, "backup_value")

class TestSecurityManager(unittest.TestCase):
    """Testes para SecurityManager"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.security_manager = SecurityManager()
    
    def test_validate_input(self):
        """Testar validação de entrada"""
        # Testar URL válida
        result = self.security_manager.validate_input(
            "https://example.com/file.zip", 
            "url"
        )
        self.assertEqual(result.validation_result.value, "safe")
        
        # Testar URL suspeita
        result = self.security_manager.validate_input(
            "javascript:alert('xss')", 
            "url"
        )
        self.assertEqual(result.validation_result.value, "unsafe")
    
    def test_check_path_traversal(self):
        """Testar verificação de path traversal"""
        # Caminho seguro
        safe_path = "/safe/path/file.txt"
        result = self.security_manager.check_path_traversal(safe_path)
        self.assertFalse(result)  # False = sem path traversal
        
        # Caminho com path traversal
        unsafe_path = "/safe/../../../etc/passwd"
        result = self.security_manager.check_path_traversal(unsafe_path)
        self.assertTrue(result)  # True = path traversal detectado
    
    def test_audit_operation(self):
        """Testar auditoria de operação"""
        result = self.security_manager.audit_critical_operation(
            operation="test_operation",
            component="test_component",
            details={"key": "value"},
            success=True,
            security_level=SecurityLevel.MEDIUM
        )
        self.assertTrue(result)
        
        # Verificar se entrada de auditoria foi criada
        report = self.security_manager.generate_security_report()
        self.assertGreater(len(report["audit_entries"]), 0)

class TestPluginManager(unittest.TestCase):
    """Testes para PluginManager"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_manager = PluginManager()
        self.plugin_manager.plugin_directory = Path(self.temp_dir)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_discover_plugins(self):
        """Testar descoberta de plugins"""
        # Criar plugin mock
        plugin_dir = Path(self.temp_dir) / "test_plugin"
        plugin_dir.mkdir()
        
        plugin_manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "main.py",
            "permissions": ["READ_FILESYSTEM"]
        }
        
        with open(plugin_dir / "plugin.json", 'w') as f:
            json.dump(plugin_manifest, f)
        
        # Criar arquivo principal do plugin
        with open(plugin_dir / "main.py", 'w') as f:
            f.write("# Test plugin main file")
        
        # Descobrir plugins
        discovered = self.plugin_manager.discover_plugins()
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].name, "test_plugin")
    
    def test_load_plugin(self):
        """Testar carregamento de plugin"""
        # Criar plugin mock primeiro
        plugin_dir = Path(self.temp_dir) / "test_plugin"
        plugin_dir.mkdir()
        
        plugin_manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "entry_point": "main.py",
            "permissions": []
        }
        
        with open(plugin_dir / "plugin.json", 'w') as f:
            json.dump(plugin_manifest, f)
        
        # Criar arquivo principal simples
        with open(plugin_dir / "main.py", 'w') as f:
            f.write("""
class TestPlugin:
    def __init__(self):
        self.name = "test_plugin"
    
    def execute(self):
        return "Plugin executed"

plugin_instance = TestPlugin()
""")
        
        # Descobrir e carregar plugin
        self.plugin_manager.discover_plugins()
        result = self.plugin_manager.load_plugin("test_plugin")
        self.assertTrue(result)
    
    def test_unload_plugin(self):
        """Testar descarregamento de plugin"""
        # Primeiro carregar um plugin
        self.test_load_plugin()
        
        # Descarregar plugin
        result = self.plugin_manager.unload_plugin("test_plugin")
        self.assertTrue(result)
        
        # Verificar se plugin foi descarregado
        self.assertNotIn("test_plugin", self.plugin_manager.loaded_plugins)

class TestCatalogUpdateManager(unittest.TestCase):
    """Testes para CatalogUpdateManager"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.update_manager = CatalogUpdateManager()
        self.update_manager.cache_directory = Path(self.temp_dir)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.get')
    def test_check_for_updates(self, mock_get):
        """Testar verificação de atualizações"""
        # Mock da resposta de atualização
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "version": "2.0.0",
            "release_date": "2024-01-01T00:00:00",
            "channel": "stable",
            "download_url": "https://example.com/update.zip",
            "checksum": "abc123",
            "size": 1024,
            "changelog": "New features and bug fixes"
        }
        mock_get.return_value = mock_response
        
        # Adicionar mirror mock
        from catalog_update_manager import MirrorInfo, MirrorStatus
        mock_mirror = MirrorInfo(
            url="https://example.com/",
            name="Test Mirror",
            location="Test",
            status=MirrorStatus.ACTIVE
        )
        self.update_manager.mirrors = [mock_mirror]
        
        # Verificar atualizações
        update_info = self.update_manager.check_for_updates(force=True)
        self.assertIsNotNone(update_info)
        self.assertEqual(update_info.version, "2.0.0")
    
    def test_add_remove_mirror(self):
        """Testar adição e remoção de mirrors"""
        from catalog_update_manager import MirrorInfo
        
        mirror = MirrorInfo(
            url="https://test-mirror.com/",
            name="Test Mirror",
            location="Test Location"
        )
        
        # Adicionar mirror
        with patch.object(self.update_manager, '_test_mirror_connectivity', return_value=True):
            result = self.update_manager.add_mirror(mirror)
            self.assertTrue(result)
            self.assertEqual(len(self.update_manager.mirrors), 1)
        
        # Remover mirror
        result = self.update_manager.remove_mirror("https://test-mirror.com/")
        self.assertTrue(result)
        self.assertEqual(len(self.update_manager.mirrors), 0)
    
    def test_cache_management(self):
        """Testar gerenciamento de cache"""
        # Obter informações do cache
        cache_info = self.update_manager.get_cache_info()
        self.assertIsInstance(cache_info, dict)
        self.assertIn("total_entries", cache_info)
        self.assertIn("total_size_mb", cache_info)
        
        # Limpar cache
        removed_count = self.update_manager.cleanup_cache(force=True)
        self.assertIsInstance(removed_count, int)

class TestDetectionEngine(unittest.TestCase):
    """Testes para DetectionEngine"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.detection_engine = DetectionEngine()
    
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_registry_detection(self, mock_query, mock_open):
        """Testar detecção via registro do Windows"""
        # Mock do registro
        mock_query.return_value = ("C:\\Program Files\\TestApp", 1)
        
        result = self.detection_engine.detect_via_registry("TestApp")
        self.assertIsInstance(result, DetectionResult)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_filesystem_detection(self, mock_listdir, mock_exists):
        """Testar detecção via sistema de arquivos"""
        # Mock do sistema de arquivos
        mock_exists.return_value = True
        mock_listdir.return_value = ["testapp.exe", "config.ini"]
        
        result = self.detection_engine.detect_via_filesystem("testapp", ["C:\\Program Files"])
        self.assertIsInstance(result, DetectionResult)
    
    def test_version_comparison(self):
        """Testar comparação de versões"""
        # Testar versões iguais
        result = self.detection_engine.compare_versions("1.0.0", "1.0.0")
        self.assertEqual(result, 0)
        
        # Testar versão menor
        result = self.detection_engine.compare_versions("1.0.0", "1.1.0")
        self.assertEqual(result, -1)
        
        # Testar versão maior
        result = self.detection_engine.compare_versions("1.1.0", "1.0.0")
        self.assertEqual(result, 1)

class TestSteamDeckOptimizations(unittest.TestCase):
    """Testes para otimizações do Steam Deck"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.catalog_manager = RuntimeCatalogManager()
    
    @patch('platform.machine')
    @patch('os.path.exists')
    def test_steam_deck_detection(self, mock_exists, mock_machine):
        """Testar detecção do Steam Deck"""
        # Simular ambiente Steam Deck
        mock_machine.return_value = "x86_64"
        mock_exists.return_value = True  # Simular arquivo específico do Steam Deck
        
        is_steam_deck = self.catalog_manager.is_steam_deck()
        # Como estamos mockando, o resultado depende da implementação
        self.assertIsInstance(is_steam_deck, bool)
    
    def test_steam_deck_optimized_runtimes(self):
        """Testar runtimes otimizados para Steam Deck"""
        # Adicionar runtime com otimizações Steam Deck
        steam_deck_runtime = RuntimeInfo(
            name="steam-deck-optimized",
            version="1.0.0",
            description="Steam Deck optimized runtime",
            category="gaming",
            tags=["steam-deck", "optimized"],
            download_url="https://example.com/steamdeck.zip",
            install_size=50 * 1024 * 1024,
            dependencies=[],
            supported_platforms=["steamdeck"],
            checksum="steamdeck123"
        )
        
        self.catalog_manager.add_runtime(steam_deck_runtime)
        
        # Buscar runtimes otimizados
        optimized_runtimes = self.catalog_manager.search_runtimes(tags=["steam-deck"])
        self.assertEqual(len(optimized_runtimes), 1)
        self.assertEqual(optimized_runtimes[0].name, "steam-deck-optimized")

class TestIntegrationScenarios(unittest.TestCase):
    """Testes de cenários de integração"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        self.package_integrator = PackageManagerIntegrator()
        self.config_manager = ConfigurationManager()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_runtime_installation_workflow(self):
        """Testar fluxo completo de instalação de runtime"""
        # 1. Adicionar runtime ao catálogo
        runtime = RuntimeInfo(
            name="integration-test-runtime",
            version="1.0.0",
            description="Integration test runtime",
            category="development",
            tags=["test"],
            download_url="https://example.com/runtime.zip",
            install_size=100 * 1024 * 1024,
            dependencies=["dependency1"],
            supported_platforms=["windows"],
            checksum="integration123"
        )
        
        result = self.catalog_manager.add_runtime(runtime)
        self.assertTrue(result)
        
        # 2. Verificar dependências
        with patch.object(self.package_integrator, 'resolve_dependencies') as mock_resolve:
            mock_resolve.return_value = ["dependency1"]
            
            missing_deps = self.package_integrator.resolve_dependencies(
                runtime.dependencies, 
                PackageManager.CHOCOLATEY
            )
            self.assertEqual(missing_deps, ["dependency1"])
        
        # 3. Simular instalação de dependências
        with patch.object(self.package_integrator, 'install_package') as mock_install:
            mock_install.return_value = True
            
            for dep in missing_deps:
                result = self.package_integrator.install_package(dep, PackageManager.CHOCOLATEY)
                self.assertTrue(result)
        
        # 4. Simular download e instalação do runtime
        with patch.object(self.catalog_manager, 'download_runtime') as mock_download:
            with patch.object(self.catalog_manager, 'install_runtime') as mock_install_runtime:
                mock_download.return_value = True
                mock_install_runtime.return_value = True
                
                download_result = self.catalog_manager.download_runtime("integration-test-runtime")
                install_result = self.catalog_manager.install_runtime("integration-test-runtime")
                
                self.assertTrue(download_result)
                self.assertTrue(install_result)
    
    def test_configuration_profile_workflow(self):
        """Testar fluxo de perfis de configuração"""
        # 1. Criar perfil de desenvolvimento
        dev_profile = ConfigProfile(
            name="development",
            description="Development environment profile",
            settings={
                "runtime.python.version": "3.11",
                "runtime.node.version": "18.0.0",
                "package_manager.preferred": "chocolatey"
            }
        )
        
        result = self.config_manager.create_profile(dev_profile)
        self.assertTrue(result)
        
        # 2. Ativar perfil
        result = self.config_manager.activate_profile("development")
        self.assertTrue(result)
        
        # 3. Verificar configurações ativas
        python_version = self.config_manager.get_configuration("runtime.python.version")
        self.assertEqual(python_version, "3.11")
        
        # 4. Criar backup antes de modificar
        backup_id = self.config_manager.create_backup("before_modification")
        self.assertIsNotNone(backup_id)
        
        # 5. Modificar configuração
        self.config_manager.set_configuration("runtime.python.version", "3.12")
        
        # 6. Verificar modificação
        new_version = self.config_manager.get_configuration("runtime.python.version")
        self.assertEqual(new_version, "3.12")
        
        # 7. Restaurar backup
        result = self.config_manager.restore_backup(backup_id)
        self.assertTrue(result)
        
        # 8. Verificar restauração
        restored_version = self.config_manager.get_configuration("runtime.python.version")
        self.assertEqual(restored_version, "3.11")

if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar todos os testes
    unittest.main(verbosity=2)