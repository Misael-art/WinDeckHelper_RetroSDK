"""
Testes para o sistema de integração de plugins
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from environment_dev_deep_evaluation.core.plugin_integration import (
    PluginIntegrationManager, RuntimeRegistry, BackwardCompatibilityManager,
    PluginStatusFeedback, RuntimeDefinition, RuntimeType, PluginAPIVersion,
    PluginAPI, PluginAPIV1, PluginAPIV2, PluginIntegrationResult
)
from environment_dev_deep_evaluation.core.plugin_system import (
    PluginMetadata, PluginVersion, PluginStatus
)


class MockPlugin(PluginAPIV1):
    """Plugin mock para testes"""
    
    def __init__(self, name="test_plugin", runtimes=None):
        self._name = name
        self._runtimes = runtimes or []
        self._initialized = False
    
    @property
    def plugin_name(self) -> str:
        return self._name
    
    def get_provided_runtimes(self):
        return self._runtimes
    
    def initialize(self, context):
        self._initialized = True
        return True
    
    def cleanup(self):
        self._initialized = False
        return True


class MockPluginV2(PluginAPIV2):
    """Plugin mock v2 para testes"""
    
    def __init__(self, name="test_plugin_v2", runtimes=None):
        self._name = name
        self._runtimes = runtimes or []
        self._initialized = False
    
    @property
    def plugin_name(self) -> str:
        return self._name
    
    def get_provided_runtimes(self):
        return self._runtimes
    
    def initialize(self, context):
        self._initialized = True
        return True
    
    def cleanup(self):
        self._initialized = False
        return True
    
    def get_runtime_dependencies(self, runtime_name: str):
        return []
    
    def can_auto_update(self, runtime_name: str):
        return True
    
    def get_configuration_schema(self, runtime_name: str):
        return {"type": "object", "properties": {}}


class TestRuntimeDefinition:
    """Testes para RuntimeDefinition"""
    
    def test_runtime_definition_creation(self):
        """Testa criação de definição de runtime"""
        runtime = RuntimeDefinition(
            name="test_runtime",
            version="1.0.0",
            runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Test runtime",
            detection_methods=["registry", "path"],
            installation_methods=["download", "package_manager"],
            validation_commands=["test_runtime --version"]
        )
        
        assert runtime.name == "test_runtime"
        assert runtime.version == "1.0.0"
        assert runtime.runtime_type == RuntimeType.PROGRAMMING_LANGUAGE
        assert len(runtime.detection_methods) == 2
        assert len(runtime.installation_methods) == 2
        assert len(runtime.validation_commands) == 1
    
    def test_runtime_definition_to_dict(self):
        """Testa conversão para dicionário"""
        runtime = RuntimeDefinition(
            name="test_runtime",
            version="1.0.0",
            runtime_type=RuntimeType.DEVELOPMENT_TOOL,
            description="Test runtime",
            detection_methods=["path"],
            installation_methods=["download"],
            validation_commands=["test --version"],
            environment_variables={"TEST_HOME": "/opt/test"},
            dependencies=["dependency1"]
        )
        
        result = runtime.to_dict()
        
        assert result["name"] == "test_runtime"
        assert result["runtime_type"] == "development_tool"
        assert result["environment_variables"]["TEST_HOME"] == "/opt/test"
        assert result["dependencies"] == ["dependency1"]


class TestRuntimeRegistry:
    """Testes para RuntimeRegistry"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.registry = RuntimeRegistry()
    
    def test_runtime_registration(self):
        """Testa registro de runtime"""
        runtime = RuntimeDefinition(
            name="test_runtime",
            version="1.0.0",
            runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Test runtime",
            detection_methods=["path"],
            installation_methods=["download"],
            validation_commands=["test --version"]
        )
        
        success = self.registry.register_runtime(runtime, "test_plugin")
        assert success
        assert "test_runtime" in self.registry.registered_runtimes
        assert self.registry.runtime_providers["test_runtime"] == "test_plugin"
    
    def test_runtime_unregistration(self):
        """Testa remoção de registro de runtime"""
        runtime = RuntimeDefinition(
            name="test_runtime",
            version="1.0.0",
            runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Test runtime",
            detection_methods=["path"],
            installation_methods=["download"],
            validation_commands=["test --version"]
        )
        
        self.registry.register_runtime(runtime, "test_plugin")
        success = self.registry.unregister_runtime("test_runtime")
        
        assert success
        assert "test_runtime" not in self.registry.registered_runtimes
        assert "test_runtime" not in self.registry.runtime_providers
    
    def test_get_runtimes_by_type(self):
        """Testa obtenção de runtimes por tipo"""
        runtime1 = RuntimeDefinition(
            name="lang1", version="1.0.0", runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Language 1", detection_methods=["path"], 
            installation_methods=["download"], validation_commands=["lang1 --version"]
        )
        
        runtime2 = RuntimeDefinition(
            name="tool1", version="1.0.0", runtime_type=RuntimeType.DEVELOPMENT_TOOL,
            description="Tool 1", detection_methods=["path"],
            installation_methods=["download"], validation_commands=["tool1 --version"]
        )
        
        self.registry.register_runtime(runtime1, "plugin1")
        self.registry.register_runtime(runtime2, "plugin2")
        
        languages = self.registry.get_runtimes_by_type(RuntimeType.PROGRAMMING_LANGUAGE)
        tools = self.registry.get_runtimes_by_type(RuntimeType.DEVELOPMENT_TOOL)
        
        assert len(languages) == 1
        assert len(tools) == 1
        assert languages[0].name == "lang1"
        assert tools[0].name == "tool1"
    
    def test_list_all_runtimes(self):
        """Testa listagem de todos os runtimes"""
        runtime = RuntimeDefinition(
            name="test_runtime", version="1.0.0", runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Test runtime", detection_methods=["path"],
            installation_methods=["download"], validation_commands=["test --version"]
        )
        
        self.registry.register_runtime(runtime, "test_plugin")
        all_runtimes = self.registry.list_all_runtimes()
        
        assert "test_runtime" in all_runtimes
        assert all_runtimes["test_runtime"]["provider_plugin"] == "test_plugin"
        assert all_runtimes["test_runtime"]["definition"]["name"] == "test_runtime"


class TestBackwardCompatibilityManager:
    """Testes para BackwardCompatibilityManager"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.manager = BackwardCompatibilityManager()
    
    def test_compatibility_mapping_registration(self):
        """Testa registro de mapeamento de compatibilidade"""
        def dummy_mapping(data):
            return data
        
        self.manager.register_compatibility_mapping("old_api", "new_api", dummy_mapping)
        
        assert self.manager.is_deprecated("old_api")
        assert self.manager.get_replacement_api("old_api") == "new_api"
    
    def test_legacy_plugin_conversion(self):
        """Testa conversão de plugin legado"""
        legacy_data = {
            "name": "legacy_plugin",
            "runtimes": [
                {"name": "old_runtime", "type": "programming_language"}
            ]
        }
        
        converted = self.manager.convert_legacy_plugin(legacy_data)
        
        assert "api_version" in converted
        assert converted["api_version"] == "1.0"
        assert "runtime_definitions" in converted
        assert converted["runtime_definitions"][0]["runtime_type"] == "programming_language"


class TestPluginStatusFeedback:
    """Testes para PluginStatusFeedback"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.feedback = PluginStatusFeedback()
    
    def test_status_update(self):
        """Testa atualização de status"""
        self.feedback.update_plugin_status(
            "test_plugin", PluginStatus.ACTIVE, "Plugin activated"
        )
        
        current = self.feedback.get_current_status("test_plugin")
        assert current is not None
        assert current["status"] == "active"
        assert current["message"] == "Plugin activated"
    
    def test_status_history(self):
        """Testa histórico de status"""
        self.feedback.update_plugin_status(
            "test_plugin", PluginStatus.INACTIVE, "Plugin deactivated"
        )
        self.feedback.update_plugin_status(
            "test_plugin", PluginStatus.ACTIVE, "Plugin activated"
        )
        
        history = self.feedback.get_plugin_status_history("test_plugin")
        assert len(history) == 2
        assert history[0]["status"] == "inactive"
        assert history[1]["status"] == "active"
    
    def test_callback_registration(self):
        """Testa registro de callback"""
        callback_called = False
        
        def test_callback(plugin_name, status, message, details):
            nonlocal callback_called
            callback_called = True
        
        self.feedback.register_feedback_callback(test_callback)
        self.feedback.update_plugin_status(
            "test_plugin", PluginStatus.ACTIVE, "Test message"
        )
        
        assert callback_called
    
    def test_status_report_generation(self):
        """Testa geração de relatório de status"""
        self.feedback.update_plugin_status(
            "plugin1", PluginStatus.ACTIVE, "Active"
        )
        self.feedback.update_plugin_status(
            "plugin2", PluginStatus.ERROR, "Error"
        )
        
        report = self.feedback.generate_status_report()
        
        assert report["total_plugins"] == 2
        assert "plugin1" in report["plugins"]
        assert "plugin2" in report["plugins"]
        assert report["plugins"]["plugin1"]["current_status"]["status"] == "active"


class TestPluginIntegrationManager:
    """Testes para PluginIntegrationManager"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PluginIntegrationManager(self.temp_dir)
    
    def create_test_runtime(self, name="test_runtime"):
        """Cria runtime de teste"""
        return RuntimeDefinition(
            name=name,
            version="1.0.0",
            runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description=f"Test runtime {name}",
            detection_methods=["path"],
            installation_methods=["download"],
            validation_commands=[f"{name} --version"]
        )
    
    def create_test_metadata(self, name="test_plugin"):
        """Cria metadados de teste"""
        return PluginMetadata(
            name=name,
            version=PluginVersion(1, 0, 0),
            description=f"Test plugin {name}",
            author="Test Author"
        )
    
    def create_test_plugin_file(self, plugin_name="test_plugin", api_version="v1"):
        """Cria arquivo de plugin de teste"""
        plugin_dir = self.temp_dir / plugin_name
        plugin_dir.mkdir(exist_ok=True)
        
        if api_version == "v1":
            plugin_code = f'''
from environment_dev_deep_evaluation.core.plugin_integration import PluginAPIV1, RuntimeDefinition, RuntimeType

class Plugin(PluginAPIV1):
    @property
    def plugin_name(self):
        return "{plugin_name}"
    
    def get_provided_runtimes(self):
        return [RuntimeDefinition(
            name="test_runtime",
            version="1.0.0",
            runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Test runtime",
            detection_methods=["path"],
            installation_methods=["download"],
            validation_commands=["test --version"]
        )]
    
    def initialize(self, context):
        return True
    
    def cleanup(self):
        return True
'''
        else:
            plugin_code = f'''
from environment_dev_deep_evaluation.core.plugin_integration import PluginAPIV2, RuntimeDefinition, RuntimeType

class Plugin(PluginAPIV2):
    @property
    def plugin_name(self):
        return "{plugin_name}"
    
    def get_provided_runtimes(self):
        return [RuntimeDefinition(
            name="test_runtime_v2",
            version="2.0.0",
            runtime_type=RuntimeType.DEVELOPMENT_TOOL,
            description="Test runtime v2",
            detection_methods=["registry"],
            installation_methods=["package_manager"],
            validation_commands=["test2 --version"]
        )]
    
    def initialize(self, context):
        return True
    
    def cleanup(self):
        return True
    
    def get_runtime_dependencies(self, runtime_name):
        return []
    
    def can_auto_update(self, runtime_name):
        return True
    
    def get_configuration_schema(self, runtime_name):
        return {{"type": "object"}}
'''
        
        with open(plugin_dir / "main.py", 'w') as f:
            f.write(plugin_code)
        
        return plugin_dir
    
    @patch('environment_dev_deep_evaluation.core.plugin_integration.PluginIntegrationManager._load_plugin_instance')
    def test_plugin_integration_success(self, mock_load):
        """Testa integração bem-sucedida de plugin"""
        # Setup
        runtime = self.create_test_runtime()
        mock_plugin = MockPlugin("test_plugin", [runtime])
        mock_load.return_value = mock_plugin
        
        metadata = self.create_test_metadata()
        plugin_path = self.temp_dir / "test_plugin"
        plugin_path.mkdir()
        
        # Test
        result = self.manager.integrate_plugin(plugin_path, metadata)
        
        # Assertions
        assert result.success
        assert len(result.runtimes_added) == 1
        assert result.runtimes_added[0] == "test_runtime"
        assert "test_plugin" in self.manager.loaded_plugin_instances
    
    @patch('environment_dev_deep_evaluation.core.plugin_integration.PluginIntegrationManager._load_plugin_instance')
    def test_plugin_integration_failure(self, mock_load):
        """Testa falha na integração de plugin"""
        # Setup
        mock_load.return_value = None  # Simula falha no carregamento
        
        metadata = self.create_test_metadata()
        plugin_path = self.temp_dir / "test_plugin"
        plugin_path.mkdir()
        
        # Test
        result = self.manager.integrate_plugin(plugin_path, metadata)
        
        # Assertions
        assert not result.success
        assert len(result.errors) > 0
        assert "Failed to load plugin instance" in result.errors[0]
    
    def test_plugin_integration_removal(self):
        """Testa remoção de integração de plugin"""
        # Setup - adiciona plugin primeiro
        runtime = self.create_test_runtime()
        mock_plugin = MockPlugin("test_plugin", [runtime])
        
        self.manager.loaded_plugin_instances["test_plugin"] = mock_plugin
        self.manager.runtime_registry.register_runtime(runtime, "test_plugin")
        
        # Test
        success = self.manager.remove_plugin_integration("test_plugin")
        
        # Assertions
        assert success
        assert "test_plugin" not in self.manager.loaded_plugin_instances
        assert "test_runtime" not in self.manager.runtime_registry.registered_runtimes
    
    def test_get_available_runtimes(self):
        """Testa obtenção de runtimes disponíveis"""
        # Setup
        runtime = self.create_test_runtime()
        self.manager.runtime_registry.register_runtime(runtime, "test_plugin")
        
        # Test
        available = self.manager.get_available_runtimes()
        
        # Assertions
        assert "test_runtime" in available
        assert available["test_runtime"]["provider_plugin"] == "test_plugin"
    
    def test_get_runtimes_by_category(self):
        """Testa obtenção de runtimes por categoria"""
        # Setup
        runtime1 = RuntimeDefinition(
            name="lang1", version="1.0.0", runtime_type=RuntimeType.PROGRAMMING_LANGUAGE,
            description="Language", detection_methods=["path"],
            installation_methods=["download"], validation_commands=["lang1 --version"]
        )
        runtime2 = RuntimeDefinition(
            name="tool1", version="1.0.0", runtime_type=RuntimeType.DEVELOPMENT_TOOL,
            description="Tool", detection_methods=["path"],
            installation_methods=["download"], validation_commands=["tool1 --version"]
        )
        
        self.manager.runtime_registry.register_runtime(runtime1, "plugin1")
        self.manager.runtime_registry.register_runtime(runtime2, "plugin2")
        
        # Test
        languages = self.manager.get_runtimes_by_category(RuntimeType.PROGRAMMING_LANGUAGE)
        tools = self.manager.get_runtimes_by_category(RuntimeType.DEVELOPMENT_TOOL)
        
        # Assertions
        assert len(languages) == 1
        assert len(tools) == 1
        assert languages[0].name == "lang1"
        assert tools[0].name == "tool1"
    
    def test_plugin_status_report(self):
        """Testa geração de relatório de status"""
        # Setup
        self.manager.status_feedback.update_plugin_status(
            "test_plugin", PluginStatus.ACTIVE, "Active"
        )
        
        # Test
        report = self.manager.get_plugin_status_report()
        
        # Assertions
        assert "total_plugins" in report
        assert report["total_plugins"] == 1
        assert "test_plugin" in report["plugins"]
    
    def test_integration_results_retrieval(self):
        """Testa recuperação de resultados de integração"""
        # Setup
        result = PluginIntegrationResult("test_plugin", True, ["runtime1"])
        self.manager.integration_results["test_plugin"] = result
        
        # Test
        results = self.manager.get_integration_results()
        
        # Assertions
        assert "test_plugin" in results
        assert results["test_plugin"]["success"] == True
        assert results["test_plugin"]["runtimes_added"] == ["runtime1"]


if __name__ == "__main__":
    pytest.main([__file__])