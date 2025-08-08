"""Testes unitários para o VersionManager."""

import unittest
import sys
import os

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.version_manager import VersionManager, ParsedVersion, VersionFormat


class TestVersionManager(unittest.TestCase):
    """Testes para a classe VersionManager."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.vm = VersionManager()
    
    def test_parse_semantic_version(self):
        """Testa parsing de versões semânticas básicas."""
        version = self.vm.parse_version("1.2.3")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        self.assertIsNone(version.prerelease)
        self.assertIsNone(version.build)
    
    def test_parse_prerelease_version(self):
        """Testa parsing de versões com prerelease."""
        version = self.vm.parse_version("1.0.0-alpha.1")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        self.assertEqual(version.prerelease, "alpha.1")
        self.assertIsNone(version.build)
    
    def test_parse_build_version(self):
        """Testa parsing de versões com build metadata."""
        version = self.vm.parse_version("1.0.0+20130313144700")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        self.assertIsNone(version.prerelease)
        self.assertEqual(version.build, "20130313144700")
    
    def test_parse_full_semantic_version(self):
        """Testa parsing de versões semânticas completas."""
        version = self.vm.parse_version("1.0.0-alpha.1+20130313144700")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        self.assertEqual(version.prerelease, "alpha.1")
        self.assertEqual(version.build, "20130313144700")
    
    def test_parse_windows_style_version(self):
        """Testa parsing de versões estilo Windows."""
        version = self.vm.parse_version("2.47.1.windows.1")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 2)
        self.assertEqual(version.minor, 47)
        self.assertEqual(version.patch, 1)
        self.assertEqual(version.build, "1")
    
    def test_parse_simple_version(self):
        """Testa parsing de versões simples (major.minor)."""
        version = self.vm.parse_version("3.8")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 3)
        self.assertEqual(version.minor, 8)
        self.assertEqual(version.patch, 0)
    
    def test_parse_single_version(self):
        """Testa parsing de versões com apenas major."""
        version = self.vm.parse_version("5")
        self.assertIsNotNone(version)
        self.assertEqual(version.major, 5)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
    
    def test_parse_invalid_version(self):
        """Testa parsing de versões inválidas."""
        invalid_versions = [
            "",
            None,
            "abc",
            "1.2.3.4.5",
            "v1.2.3",
            "1.2.3-",
            "1.2.3+"
        ]
        
        for invalid in invalid_versions:
            with self.subTest(version=invalid):
                result = self.vm.parse_version(invalid)
                self.assertIsNone(result)
    
    def test_compare_versions_equal(self):
        """Testa comparação de versões iguais."""
        result = self.vm.compare_versions("1.2.3", "1.2.3")
        self.assertEqual(result, 0)
    
    def test_compare_versions_major_different(self):
        """Testa comparação com major version diferente."""
        result = self.vm.compare_versions("2.0.0", "1.9.9")
        self.assertEqual(result, 1)
        
        result = self.vm.compare_versions("1.0.0", "2.0.0")
        self.assertEqual(result, -1)
    
    def test_compare_versions_minor_different(self):
        """Testa comparação com minor version diferente."""
        result = self.vm.compare_versions("1.3.0", "1.2.9")
        self.assertEqual(result, 1)
        
        result = self.vm.compare_versions("1.1.0", "1.2.0")
        self.assertEqual(result, -1)
    
    def test_compare_versions_patch_different(self):
        """Testa comparação com patch version diferente."""
        result = self.vm.compare_versions("1.2.4", "1.2.3")
        self.assertEqual(result, 1)
        
        result = self.vm.compare_versions("1.2.2", "1.2.3")
        self.assertEqual(result, -1)
    
    def test_compare_versions_prerelease(self):
        """Testa comparação com versões prerelease."""
        # Prerelease é menor que release
        result = self.vm.compare_versions("1.0.0-alpha", "1.0.0")
        self.assertEqual(result, -1)
        
        result = self.vm.compare_versions("1.0.0", "1.0.0-alpha")
        self.assertEqual(result, 1)
        
        # Comparação entre prereleases
        result = self.vm.compare_versions("1.0.0-beta", "1.0.0-alpha")
        self.assertEqual(result, 1)
    
    def test_is_compatible_equal(self):
        """Testa compatibilidade com operador de igualdade."""
        self.assertTrue(self.vm.is_compatible("1.2.3", "==1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.4", "==1.2.3"))
        
        # Sem operador assume igualdade
        self.assertTrue(self.vm.is_compatible("1.2.3", "1.2.3"))
    
    def test_is_compatible_greater_equal(self):
        """Testa compatibilidade com operador maior ou igual."""
        self.assertTrue(self.vm.is_compatible("1.2.3", ">=1.2.3"))
        self.assertTrue(self.vm.is_compatible("1.2.4", ">=1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.2", ">=1.2.3"))
    
    def test_is_compatible_less_equal(self):
        """Testa compatibilidade com operador menor ou igual."""
        self.assertTrue(self.vm.is_compatible("1.2.3", "<=1.2.3"))
        self.assertTrue(self.vm.is_compatible("1.2.2", "<=1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.4", "<=1.2.3"))
    
    def test_is_compatible_greater(self):
        """Testa compatibilidade com operador maior."""
        self.assertTrue(self.vm.is_compatible("1.2.4", ">1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.3", ">1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.2", ">1.2.3"))
    
    def test_is_compatible_less(self):
        """Testa compatibilidade com operador menor."""
        self.assertTrue(self.vm.is_compatible("1.2.2", "<1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.3", "<1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.4", "<1.2.3"))
    
    def test_is_compatible_not_equal(self):
        """Testa compatibilidade com operador diferente."""
        self.assertTrue(self.vm.is_compatible("1.2.4", "!=1.2.3"))
        self.assertFalse(self.vm.is_compatible("1.2.3", "!=1.2.3"))
    
    def test_get_latest_version(self):
        """Testa obtenção da versão mais recente."""
        versions = ["1.0.0", "1.2.0", "1.1.5", "2.0.0-alpha", "1.3.0"]
        latest = self.vm.get_latest_version(versions)
        
        self.assertIsNotNone(latest)
        self.assertEqual(str(latest), "2.0.0-alpha")
    
    def test_get_latest_version_empty_list(self):
        """Testa obtenção da versão mais recente com lista vazia."""
        latest = self.vm.get_latest_version([])
        self.assertIsNone(latest)
    
    def test_get_latest_version_invalid_versions(self):
        """Testa obtenção da versão mais recente com versões inválidas."""
        versions = ["invalid", "abc", ""]
        latest = self.vm.get_latest_version(versions)
        self.assertIsNone(latest)
    
    def test_normalize_version(self):
        """Testa normalização de versões."""
        normalized = self.vm.normalize_version("1.2.3")
        self.assertEqual(normalized, "1.2.3")
        
        normalized = self.vm.normalize_version("1.2")
        self.assertEqual(normalized, "1.2.0")
        
        normalized = self.vm.normalize_version("5")
        self.assertEqual(normalized, "5.0.0")
        
        normalized = self.vm.normalize_version("invalid")
        self.assertIsNone(normalized)
    
    def test_parsed_version_str(self):
        """Testa representação string de ParsedVersion."""
        version = ParsedVersion(1, 2, 3)
        self.assertEqual(str(version), "1.2.3")
        
        version = ParsedVersion(1, 0, 0, "alpha.1")
        self.assertEqual(str(version), "1.0.0-alpha.1")
        
        version = ParsedVersion(1, 0, 0, build="20130313")
        self.assertEqual(str(version), "1.0.0+20130313")
        
        version = ParsedVersion(1, 0, 0, "alpha.1", "20130313")
        self.assertEqual(str(version), "1.0.0-alpha.1+20130313")
    
    def test_performance_multiple_versions(self):
        """Testa performance com múltiplas versões."""
        versions = [f"{i}.{j}.{k}" for i in range(1, 6) for j in range(0, 10) for k in range(0, 10)]
        
        # Testa parsing de todas as versões
        parsed_count = 0
        for version in versions:
            if self.vm.parse_version(version):
                parsed_count += 1
        
        self.assertEqual(parsed_count, len(versions))
        
        # Testa comparação
        result = self.vm.compare_versions(versions[0], versions[-1])
        self.assertEqual(result, -1)


if __name__ == '__main__':
    unittest.main()