"""Testes para detecção de aplicações da Microsoft Store.

Testa a funcionalidade de detecção de aplicações UWP instaladas
através da Microsoft Store.

Author: AI Assistant
Date: 2024
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Adicionar o diretório pai ao path para importações
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.microsoft_store_detection import (
    MicrosoftStoreDetectionStrategy,
    UWPApplication
)
from core.detection_engine import DetectionMethod, ApplicationStatus


class TestUWPApplication(unittest.TestCase):
    """Testes para a classe UWPApplication."""
    
    def test_uwp_application_creation(self):
        """Testa criação de UWPApplication."""
        app = UWPApplication(
            name="TestApp",
            package_full_name="TestApp_1.0.0.0_x64__8wekyb3d8bbwe",
            package_family_name="TestApp_8wekyb3d8bbwe",
            version="1.0.0.0",
            publisher="CN=TestPublisher",
            install_location="C:\\Program Files\\WindowsApps\\TestApp",
            is_framework=False,
            is_bundle=False,
            architecture="x64"
        )
        
        self.assertEqual(app.name, "TestApp")
        self.assertEqual(app.version, "1.0.0.0")
        self.assertFalse(app.is_framework)
        self.assertEqual(app.architecture, "x64")
    
    def test_uwp_application_defaults(self):
        """Testa valores padrão de UWPApplication."""
        app = UWPApplication(
            name="TestApp",
            package_full_name="TestApp_1.0.0.0_x64__8wekyb3d8bbwe",
            package_family_name="TestApp_8wekyb3d8bbwe",
            version="1.0.0.0",
            publisher="CN=TestPublisher",
            install_location="C:\\Program Files\\WindowsApps\\TestApp"
        )
        
        self.assertFalse(app.is_framework)
        self.assertFalse(app.is_bundle)
        self.assertEqual(app.architecture, "")


class TestMicrosoftStoreDetectionStrategy(unittest.TestCase):
    """Testes para a estratégia de detecção da Microsoft Store."""
    
    def setUp(self):
        """Configuração para cada teste."""
        self.strategy = MicrosoftStoreDetectionStrategy()
    
    def test_initialization(self):
        """Testa inicialização da estratégia."""
        self.assertEqual(self.strategy.confidence_level, 0.9)
        self.assertIn("Microsoft.VisualStudioCode_8wekyb3d8bbwe", self.strategy.known_apps)
        self.assertIn("development", self.strategy.app_categories)
    
    def test_get_method_name(self):
        """Testa retorno do método de detecção."""
        self.assertEqual(self.strategy.get_method_name(), DetectionMethod.PACKAGE_MANAGER)
    
    def test_get_friendly_name_known_app(self):
        """Testa obtenção de nome amigável para app conhecido."""
        app = UWPApplication(
            name="Microsoft.VisualStudioCode",
            package_full_name="Microsoft.VisualStudioCode_1.0.0.0_x64__8wekyb3d8bbwe",
            package_family_name="Microsoft.VisualStudioCode_8wekyb3d8bbwe",
            version="1.0.0.0",
            publisher="CN=Microsoft",
            install_location=""
        )
        
        friendly_name = self.strategy._get_friendly_name(app)
        self.assertEqual(friendly_name, "Visual Studio Code")
    
    def test_get_friendly_name_unknown_app(self):
        """Testa obtenção de nome amigável para app desconhecido."""
        app = UWPApplication(
            name="SomeRandomApp",
            package_full_name="SomeRandomApp_1.0.0.0_x64__randomhash",
            package_family_name="SomeRandomApp_randomhash",
            version="1.0.0.0",
            publisher="CN=RandomPublisher",
            install_location=""
        )
        
        friendly_name = self.strategy._get_friendly_name(app)
        self.assertEqual(friendly_name, "Some Random App")
    
    def test_get_app_category(self):
        """Testa determinação de categoria da aplicação."""
        self.assertEqual(self.strategy._get_app_category("Visual Studio Code"), "development")
        self.assertEqual(self.strategy._get_app_category("Microsoft Edge"), "browser")
        self.assertEqual(self.strategy._get_app_category("Calculator"), "utility")
        self.assertEqual(self.strategy._get_app_category("Unknown App"), "other")
    
    def test_is_relevant_app_known(self):
        """Testa se app conhecido é relevante."""
        app = UWPApplication(
            name="Microsoft.VisualStudioCode",
            package_full_name="Microsoft.VisualStudioCode_1.0.0.0_x64__8wekyb3d8bbwe",
            package_family_name="Microsoft.VisualStudioCode_8wekyb3d8bbwe",
            version="1.0.0.0",
            publisher="CN=Microsoft",
            install_location=""
        )
        
        self.assertTrue(self.strategy._is_relevant_app(app, None))
    
    def test_is_relevant_app_framework(self):
        """Testa se framework vazio não é relevante."""
        app = UWPApplication(
            name="",
            package_full_name="Microsoft.VCLibs.140.00_14.0.30704.0_x64__8wekyb3d8bbwe",
            package_family_name="Microsoft.VCLibs.140.00_8wekyb3d8bbwe",
            version="14.0.30704.0",
            publisher="CN=Microsoft",
            install_location="",
            is_framework=True
        )
        
        self.assertFalse(self.strategy._is_relevant_app(app, None))
    
    def test_is_relevant_app_target_list(self):
        """Testa relevância com lista de apps alvo."""
        app = UWPApplication(
            name="SomeCodeEditor",
            package_full_name="SomeCodeEditor_1.0.0.0_x64__randomhash",
            package_family_name="SomeCodeEditor_randomhash",
            version="1.0.0.0",
            publisher="CN=RandomPublisher",
            install_location=""
        )
        
        # Deve ser relevante se estiver na lista alvo
        self.assertTrue(self.strategy._is_relevant_app(app, ["SomeCodeEditor"]))
        self.assertFalse(self.strategy._is_relevant_app(app, ["DifferentApp"]))
    
    def test_is_relevant_app_dev_pattern(self):
        """Testa relevância por padrão de desenvolvimento."""
        app = UWPApplication(
            name="MyVisualStudioExtension",
            package_full_name="MyVisualStudioExtension_1.0.0.0_x64__randomhash",
            package_family_name="MyVisualStudioExtension_randomhash",
            version="1.0.0.0",
            publisher="CN=RandomPublisher",
            install_location=""
        )
        
        self.assertTrue(self.strategy._is_relevant_app(app, None))
    
    def test_create_uwp_app_from_dict(self):
        """Testa criação de UWPApplication a partir de dicionário."""
        app_dict = {
            "Name": "TestApp",
            "PackageFullName": "TestApp_1.0.0.0_x64__8wekyb3d8bbwe",
            "PackageFamilyName": "TestApp_8wekyb3d8bbwe",
            "Version": "1.0.0.0",
            "Publisher": "CN=TestPublisher",
            "InstallLocation": "C:\\Program Files\\WindowsApps\\TestApp",
            "IsFramework": "False",
            "IsBundle": "True",
            "Architecture": "x64"
        }
        
        app = self.strategy._create_uwp_app_from_dict(app_dict)
        
        self.assertIsNotNone(app)
        self.assertEqual(app.name, "TestApp")
        self.assertEqual(app.version, "1.0.0.0")
        self.assertFalse(app.is_framework)
        self.assertTrue(app.is_bundle)
        self.assertEqual(app.architecture, "x64")
    
    def test_create_uwp_app_from_dict_invalid(self):
        """Testa criação de UWPApplication com dados inválidos."""
        app_dict = {}  # Dicionário vazio
        
        app = self.strategy._create_uwp_app_from_dict(app_dict)
        
        self.assertIsNotNone(app)
        self.assertEqual(app.name, "")
        self.assertEqual(app.version, "")
    
    def test_create_detected_application(self):
        """Testa criação de DetectedApplication."""
        uwp_app = UWPApplication(
            name="Microsoft.VisualStudioCode",
            package_full_name="Microsoft.VisualStudioCode_1.0.0.0_x64__8wekyb3d8bbwe",
            package_family_name="Microsoft.VisualStudioCode_8wekyb3d8bbwe",
            version="1.85.0",
            publisher="CN=Microsoft Corporation",
            install_location="C:\\Program Files\\WindowsApps\\Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
            architecture="x64"
        )
        
        detected_app = self.strategy._create_detected_application(uwp_app)
        
        self.assertIsNotNone(detected_app)
        self.assertEqual(detected_app.name, "Visual Studio Code")
        self.assertEqual(detected_app.version, "1.85.0")
        self.assertEqual(detected_app.detection_method, DetectionMethod.PACKAGE_MANAGER)
        self.assertEqual(detected_app.status, ApplicationStatus.INSTALLED)
        self.assertEqual(detected_app.confidence, 0.9)
        
        # Verificar metadata
        self.assertEqual(detected_app.metadata["app_type"], "uwp")
        self.assertEqual(detected_app.metadata["category"], "development")
        self.assertEqual(detected_app.metadata["package_family_name"], "Microsoft.VisualStudioCode_8wekyb3d8bbwe")
    
    @patch('subprocess.run')
    def test_get_uwp_packages_success(self, mock_run):
        """Testa obtenção bem-sucedida de pacotes UWP."""
        # Mock da resposta do PowerShell
        mock_response = {
            "Name": "Microsoft.VisualStudioCode",
            "PackageFullName": "Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
            "PackageFamilyName": "Microsoft.VisualStudioCode_8wekyb3d8bbwe",
            "Version": "1.85.0",
            "Publisher": "CN=Microsoft Corporation",
            "InstallLocation": "C:\\Program Files\\WindowsApps\\Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
            "IsFramework": False,
            "IsBundle": False,
            "Architecture": "x64"
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        uwp_apps = self.strategy._get_uwp_packages()
        
        self.assertEqual(len(uwp_apps), 1)
        self.assertEqual(uwp_apps[0].name, "Microsoft.VisualStudioCode")
        self.assertEqual(uwp_apps[0].version, "1.85.0")
    
    @patch('subprocess.run')
    def test_get_uwp_packages_multiple(self, mock_run):
        """Testa obtenção de múltiplos pacotes UWP."""
        # Mock da resposta do PowerShell com múltiplos pacotes
        mock_response = [
            {
                "Name": "Microsoft.VisualStudioCode",
                "PackageFullName": "Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
                "PackageFamilyName": "Microsoft.VisualStudioCode_8wekyb3d8bbwe",
                "Version": "1.85.0",
                "Publisher": "CN=Microsoft Corporation",
                "InstallLocation": "C:\\Program Files\\WindowsApps\\Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
                "IsFramework": False,
                "IsBundle": False,
                "Architecture": "x64"
            },
            {
                "Name": "Microsoft.WindowsTerminal",
                "PackageFullName": "Microsoft.WindowsTerminal_1.18.0_x64__8wekyb3d8bbwe",
                "PackageFamilyName": "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
                "Version": "1.18.0",
                "Publisher": "CN=Microsoft Corporation",
                "InstallLocation": "C:\\Program Files\\WindowsApps\\Microsoft.WindowsTerminal_1.18.0_x64__8wekyb3d8bbwe",
                "IsFramework": False,
                "IsBundle": False,
                "Architecture": "x64"
            }
        ]
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        uwp_apps = self.strategy._get_uwp_packages()
        
        self.assertEqual(len(uwp_apps), 2)
        self.assertEqual(uwp_apps[0].name, "Microsoft.VisualStudioCode")
        self.assertEqual(uwp_apps[1].name, "Microsoft.WindowsTerminal")
    
    @patch('subprocess.run')
    def test_get_uwp_packages_failure(self, mock_run):
        """Testa falha na obtenção de pacotes UWP."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Access denied"
        mock_run.return_value.stdout = ""
        
        # Mock do método alternativo
        with patch.object(self.strategy, '_get_uwp_packages_alternative', return_value=[]):
            uwp_apps = self.strategy._get_uwp_packages()
        
        self.assertEqual(len(uwp_apps), 0)
    
    @patch('subprocess.run')
    def test_get_uwp_packages_json_error(self, mock_run):
        """Testa erro de JSON na obtenção de pacotes UWP."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Invalid JSON output"
        
        # Mock do método de fallback
        with patch.object(self.strategy, '_parse_powershell_output_fallback', return_value=[]):
            uwp_apps = self.strategy._get_uwp_packages()
        
        self.assertEqual(len(uwp_apps), 0)
    
    @patch('subprocess.run')
    def test_detect_applications_with_target(self, mock_run):
        """Testa detecção com lista de aplicações alvo."""
        # Mock da resposta do PowerShell
        mock_response = {
            "Name": "Microsoft.VisualStudioCode",
            "PackageFullName": "Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
            "PackageFamilyName": "Microsoft.VisualStudioCode_8wekyb3d8bbwe",
            "Version": "1.85.0",
            "Publisher": "CN=Microsoft Corporation",
            "InstallLocation": "C:\\Program Files\\WindowsApps\\Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
            "IsFramework": False,
            "IsBundle": False,
            "Architecture": "x64"
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        detected_apps = self.strategy.detect_applications(["Visual Studio Code"])
        
        self.assertEqual(len(detected_apps), 1)
        self.assertEqual(detected_apps[0].name, "Visual Studio Code")
    
    @patch('subprocess.run')
    def test_get_installed_uwp_apps_summary(self, mock_run):
        """Testa obtenção de resumo de apps UWP instalados."""
        # Mock da resposta do PowerShell
        mock_response = [
            {
                "Name": "Microsoft.VisualStudioCode",
                "PackageFullName": "Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
                "PackageFamilyName": "Microsoft.VisualStudioCode_8wekyb3d8bbwe",
                "Version": "1.85.0",
                "Publisher": "CN=Microsoft Corporation",
                "InstallLocation": "C:\\Program Files\\WindowsApps\\Microsoft.VisualStudioCode_1.85.0_x64__8wekyb3d8bbwe",
                "IsFramework": False,
                "IsBundle": False,
                "Architecture": "x64"
            },
            {
                "Name": "Microsoft.VCLibs.140.00",
                "PackageFullName": "Microsoft.VCLibs.140.00_14.0.30704.0_x64__8wekyb3d8bbwe",
                "PackageFamilyName": "Microsoft.VCLibs.140.00_8wekyb3d8bbwe",
                "Version": "14.0.30704.0",
                "Publisher": "CN=Microsoft Corporation",
                "InstallLocation": "",
                "IsFramework": True,
                "IsBundle": False,
                "Architecture": "x64"
            }
        ]
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        summary = self.strategy.get_installed_uwp_apps_summary()
        
        self.assertEqual(summary["total_packages"], 2)
        self.assertEqual(summary["frameworks"], 1)
        self.assertEqual(summary["bundles"], 0)
        self.assertEqual(summary["known_apps"], 2)  # Ambos são conhecidos
        self.assertIn("development", summary["by_category"])
        self.assertIn("runtime", summary["by_category"])


if __name__ == '__main__':
    unittest.main()