"""
Testes para o sistema de plugins
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from environment_dev_deep_evaluation.core.plugin_system import (
    PluginSystemManager, PluginConflictDetector, PluginVersionManager,
    PluginMetadata, PluginVersion, PluginDependency, PluginConflict,
    PluginStatus, ConflictType
)


class TestPluginVersion:
    """Testes para PluginVersion"""
    
    def test_version_string_representation(self):
        """Testa representação string da versão"""
        version = PluginVersion(1, 2, 3)
        assert str(version) == "1.2.3"
        
        version_with_build = PluginVersion(1, 2, 3, "beta")
        assert str(version_with_build) == "1.2.3-beta"
    
    def test_version_comparison(self):
        """Testa comparação entre versões"""
        v1 = PluginVersion(1, 0, 0)
        v2 = PluginVersion(1, 1, 0)
        v3 = PluginVersion(2, 0, 0)
        
        assert v1 < v2
        assert v2 < v3
        assert v1 < v3
        assert v1 == PluginVersion(1, 0, 0)


class TestPluginDependency:
    """Testes para PluginDependency"""
    
    def test_compatibility_check(self):
        """Testa verificação de compatibilidade"""
        # Dependência com versão mínima
        dep = PluginDependency("test", min_version=PluginVersion(1, 0, 0))
        assert dep.is_compatible(PluginVersion(1, 0, 0))
        assert dep.is_compatible(PluginVersion(1, 1, 0))
        assert not dep.is_compatible(PluginVersion(0, 9, 0))
        
        # Dependência com versão máxima
        dep = PluginDependency("test", max_version=PluginVersion(2, 0, 0))
        assert dep.is_compatible(PluginVersion(1, 0, 0))
        assert dep.is_compatible(PluginVersion(2, 0, 0))
        assert not dep.is_compatible(PluginVersion(2, 1, 0))
        
        # Dependência com range de versões
        dep = PluginDependency("test", 
                             min_version=PluginVersion(1, 0, 0),
                             max_version=PluginVersion(2, 0, 0))
        assert dep.is_compatible(PluginVersion(1, 5, 0))
        assert not dep.is_compatible(PluginVersion(0, 9, 0))
        assert not dep.is_compatible(PluginVersion(2, 1, 0))


class TestPluginMetadata:
    """Testes para PluginMetadata"""
    
    def test_from_dict_creation(self):
        """Testa criação de metadados a partir de dicionário"""
        data = {
            "name": "test_plugin",
            "version": {"major": 1, "minor": 2, "patch": 3, "build": "beta"},
            "description": "Plugin de teste",
            "author": "Test Author",
            "dependencies": [
                {
                    "name": "dep1",
                    "min_version": {"major": 1, "minor": 0, "patch": 0},
                    "required": True
                }
            ],
            "provides": ["api1", "api2"],
            "requires": ["resource1"],
            "compatible_versions": ["1.0", "1.1"],
            "signature": "test_signature",
            "checksum": "test_checksum"
        }
        
        metadata = PluginMetadata.from_dict(data)
        
        assert metadata.name == "test_plugin"
        assert str(metadata.version) == "1.2.3-beta"
        assert metadata.description == "Plugin de teste"
        assert metadata.author == "Test Author"
        assert len(metadata.dependencies) == 1
        assert metadata.dependencies[0].name == "dep1"
        assert metadata.provides == ["api1", "api2"]
        assert metadata.requires == ["resource1"]
        assert metadata.signature == "test_signature"
        assert metadata.checksum == "test_checksum"


class TestPluginConflictDetector:
    """Testes para PluginConflictDetector"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.detector = PluginConflictDetector()
    
    def test_resource_conflict_detection(self):
        """Testa detecção de conflitos de recursos"""
        plugin1 = PluginMetadata(
            name="plugin1",
            version=PluginVersion(1, 0, 0),
            description="Plugin 1",
            author="Author 1",
            provides=["api1", "api2"]
        )
        
        plugin2 = PluginMetadata(
            name="plugin2",
            version=PluginVersion(1, 0, 0),
            description="Plugin 2",
            author="Author 2",
            provides=["api2", "api3"]
        )
        
        plugins = {"plugin1": plugin1, "plugin2": plugin2}
        conflicts = self.detector.detect_conflicts(plugins)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.RESOURCE_CONFLICT
        assert "api2" in conflicts[0].description
    
    def test_dependency_conflict_detection(self):
        """Testa detecção de conflitos de dependências"""
        plugin1 = PluginMetadata(
            name="plugin1",
            version=PluginVersion(1, 0, 0),
            description="Plugin 1",
            author="Author 1",
            dependencies=[
                PluginDependency("plugin2", min_version=PluginVersion(2, 0, 0))
            ]
        )
        
        plugin2 = PluginMetadata(
            name="plugin2",
            version=PluginVersion(1, 0, 0),
            description="Plugin 2",
            author="Author 2"
        )
        
        plugins = {"plugin1": plugin1, "plugin2": plugin2}
        conflicts = self.detector.detect_conflicts(plugins)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DEPENDENCY_CONFLICT
        assert conflicts[0].severity == "critical"
    
    def test_missing_dependency_detection(self):
        """Testa detecção de dependências ausentes"""
        plugin1 = PluginMetadata(
            name="plugin1",
            version=PluginVersion(1, 0, 0),
            description="Plugin 1",
            author="Author 1",
            dependencies=[
                PluginDependency("missing_plugin", required=True)
            ]
        )
        
        plugins = {"plugin1": plugin1}
        conflicts = self.detector.detect_conflicts(plugins)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.DEPENDENCY_CONFLICT
        assert conflicts[0].severity == "critical"
        assert "não está instalado" in conflicts[0].description


class TestPluginVersionManager:
    """Testes para PluginVersionManager"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PluginVersionManager(self.temp_dir)
    
    def test_version_availability_check(self):
        """Testa verificação de versões disponíveis"""
        # Simula histórico de versões
        self.manager.version_history["test_plugin"] = [
            PluginVersion(1, 0, 0),
            PluginVersion(1, 1, 0),
            PluginVersion(2, 0, 0)
        ]
        
        versions = self.manager.get_available_versions("test_plugin")
        assert len(versions) == 3
        
        latest = self.manager.get_latest_version("test_plugin")
        assert latest == PluginVersion(2, 0, 0)
    
    def test_update_availability_check(self):
        """Testa verificação de disponibilidade de atualização"""
        self.manager.version_history["test_plugin"] = [
            PluginVersion(1, 0, 0),
            PluginVersion(1, 1, 0),
            PluginVersion(2, 0, 0)
        ]
        
        current_version = PluginVersion(1, 0, 0)
        assert self.manager.can_update("test_plugin", current_version)
        
        latest_version = PluginVersion(2, 0, 0)
        assert not self.manager.can_update("test_plugin", latest_version)


class TestPluginSystemManager:
    """Testes para PluginSystemManager"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PluginSystemManager(self.temp_dir)
    
    def create_test_plugin(self, name: str, version: str = "1.0.0", 
                          provides: list = None, dependencies: list = None) -> Path:
        """Cria um plugin de teste"""
        plugin_dir = self.temp_dir / name
        plugin_dir.mkdir(exist_ok=True)
        
        version_parts = version.split('.')
        plugin_data = {
            "name": name,
            "version": {
                "major": int(version_parts[0]),
                "minor": int(version_parts[1]),
                "patch": int(version_parts[2])
            },
            "description": f"Plugin de teste {name}",
            "author": "Test Author",
            "provides": provides or [],
            "dependencies": dependencies or []
        }
        
        with open(plugin_dir / "plugin.json", 'w') as f:
            json.dump(plugin_data, f)
        
        return plugin_dir
    
    def test_plugin_loading(self):
        """Testa carregamento de plugin"""
        plugin_dir = self.create_test_plugin("test_plugin")
        
        success = self.manager.load_plugin(plugin_dir)
        assert success
        assert "test_plugin" in self.manager.loaded_plugins
        assert self.manager.plugin_status["test_plugin"] == PluginStatus.ACTIVE
    
    def test_plugin_unloading(self):
        """Testa descarregamento de plugin"""
        plugin_dir = self.create_test_plugin("test_plugin")
        self.manager.load_plugin(plugin_dir)
        
        success = self.manager.unload_plugin("test_plugin")
        assert success
        assert "test_plugin" not in self.manager.loaded_plugins
        assert "test_plugin" not in self.manager.plugin_status
    
    def test_conflict_detection_integration(self):
        """Testa integração da detecção de conflitos"""
        # Cria dois plugins com conflito de recursos
        plugin1_dir = self.create_test_plugin("plugin1", provides=["api1"])
        plugin2_dir = self.create_test_plugin("plugin2", provides=["api1"])
        
        self.manager.load_plugin(plugin1_dir)
        self.manager.load_plugin(plugin2_dir)
        
        conflicts = self.manager.get_conflicts()
        assert len(conflicts) > 0
        assert any(c.conflict_type == ConflictType.RESOURCE_CONFLICT for c in conflicts)
    
    def test_plugin_listing(self):
        """Testa listagem de plugins"""
        plugin_dir = self.create_test_plugin("test_plugin", provides=["api1"])
        self.manager.load_plugin(plugin_dir)
        
        plugins = self.manager.list_plugins()
        assert "test_plugin" in plugins
        assert plugins["test_plugin"]["version"] == "1.0.0"
        assert plugins["test_plugin"]["provides"] == ["api1"]
        assert plugins["test_plugin"]["status"] == "active"
    
    def test_conflict_report_generation(self):
        """Testa geração de relatório de conflitos"""
        # Cria plugins com conflitos
        plugin1_dir = self.create_test_plugin("plugin1", provides=["api1"])
        plugin2_dir = self.create_test_plugin("plugin2", provides=["api1"])
        
        self.manager.load_plugin(plugin1_dir)
        self.manager.load_plugin(plugin2_dir)
        
        report = self.manager.generate_conflict_report()
        
        assert "total_conflicts" in report
        assert "conflicts_by_severity" in report
        assert "affected_plugins" in report
        assert "generated_at" in report
        assert report["total_conflicts"] > 0
    
    @patch('environment_dev_deep_evaluation.core.plugin_system.PluginSystemManager._calculate_plugin_checksum')
    def test_plugin_integrity_verification(self, mock_checksum):
        """Testa verificação de integridade do plugin"""
        mock_checksum.return_value = "test_checksum"
        
        # Cria plugin com checksum
        plugin_dir = self.create_test_plugin("test_plugin")
        plugin_json_path = plugin_dir / "plugin.json"
        
        with open(plugin_json_path, 'r') as f:
            plugin_data = json.load(f)
        
        plugin_data["checksum"] = "test_checksum"
        
        with open(plugin_json_path, 'w') as f:
            json.dump(plugin_data, f)
        
        success = self.manager.load_plugin(plugin_dir)
        assert success
        mock_checksum.assert_called_once()
    
    def test_plugin_status_retrieval(self):
        """Testa recuperação de status do plugin"""
        plugin_dir = self.create_test_plugin("test_plugin")
        self.manager.load_plugin(plugin_dir)
        
        status = self.manager.get_plugin_status("test_plugin")
        assert status == PluginStatus.ACTIVE
        
        status = self.manager.get_plugin_status("nonexistent_plugin")
        assert status is None


if __name__ == "__main__":
    pytest.main([__file__])