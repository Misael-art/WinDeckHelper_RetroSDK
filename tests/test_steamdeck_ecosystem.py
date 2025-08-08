#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para Steam Deck Ecosystem Integration
Testa integração com GlosSI, Steam Cloud, modo overlay e Steam Input mapping.
"""

import unittest
from unittest.mock import Mock, patch
import time

from core.steamdeck_integration_layer import (
    SteamDeckIntegrationLayer,
    SteamDeckDetectionResult,
    DetectionMethod,
    SteamDeckModel
)


class TestSteamDeckEcosystemIntegration(unittest.TestCase):
    """Testes para integração com ecossistema Steam"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.integration_layer = SteamDeckIntegrationLayer()
    
    def test_glossi_integration_success(self):
        """Testa integração bem-sucedida com GlosSI"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, '_detect_glossi_installation') as mock_glossi_detect:
            
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock GlosSI encontrado
            mock_glossi_detect.return_value = {
                "found": True,
                "path": "C:\\Program Files\\GlosSI",
                "version": "1.0.0"
            }
            
            # Executar integração GlosSI
            result = self.integration_layer.integrate_with_glossi()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertTrue(result["glossi_installed"])
            self.assertEqual(result["glossi_version"], "1.0.0")
            self.assertIsInstance(result["supported_applications"], list)
            self.assertGreater(len(result["supported_applications"]), 0)
            self.assertIsInstance(result["configuration_profiles"], dict)
    
    def test_glossi_integration_not_found_auto_install(self):
        """Testa integração GlosSI quando não encontrado - instalação automática"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, '_detect_glossi_installation') as mock_glossi_detect, \
             patch.object(self.integration_layer, '_install_glossi_automatically') as mock_install:
            
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock GlosSI não encontrado
            mock_glossi_detect.return_value = {"found": False}
            
            # Mock instalação automática bem-sucedida
            mock_install.return_value = {
                "success": True,
                "path": "C:\\Users\\user\\AppData\\Local\\GlosSI",
                "version": "1.0.0"
            }
            
            # Executar integração GlosSI
            result = self.integration_layer.integrate_with_glossi()
            
            # Verificar que instalação automática foi tentada
            mock_install.assert_called_once()
            self.assertTrue(result["success"])
            self.assertTrue(result["glossi_installed"])
    
    def test_glossi_integration_non_steam_deck(self):
        """Testa integração GlosSI em dispositivo não-Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção negativa
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=False,
                detection_method=DetectionMethod.FALLBACK,
                confidence=0.1
            )
            
            # Executar integração GlosSI
            result = self.integration_layer.integrate_with_glossi()
            
            # Verificar falha apropriada
            self.assertFalse(result["success"])
            self.assertFalse(result["glossi_installed"])
            self.assertIn("Not a Steam Deck device", result["error_message"])
    
    def test_steam_cloud_synchronization_success(self):
        """Testa sincronização bem-sucedida via Steam Cloud"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, '_check_steam_login_status') as mock_login, \
             patch.object(self.integration_layer, '_check_steam_cloud_status') as mock_cloud:
            
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock Steam logado
            mock_login.return_value = {
                "logged_in": True,
                "username": "testuser"
            }
            
            # Mock Steam Cloud habilitado
            mock_cloud.return_value = {
                "enabled": True,
                "available_storage": "1GB"
            }
            
            # Executar sincronização Steam Cloud
            result = self.integration_layer.synchronize_via_steam_cloud()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertTrue(result["cloud_sync_enabled"])
            self.assertIsInstance(result["synced_configurations"], list)
            self.assertGreater(len(result["synced_configurations"]), 0)
            self.assertIsInstance(result["last_sync_timestamp"], float)
            self.assertIn(result["sync_status"], ["completed", "partial"])
    
    def test_steam_cloud_sync_not_logged_in(self):
        """Testa sincronização Steam Cloud quando não logado"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, '_check_steam_login_status') as mock_login:
            
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock Steam não logado
            mock_login.return_value = {"logged_in": False}
            
            # Executar sincronização Steam Cloud
            result = self.integration_layer.synchronize_via_steam_cloud()
            
            # Verificar falha apropriada
            self.assertFalse(result["success"])
            self.assertFalse(result["cloud_sync_enabled"])
            self.assertIn("Steam not logged in", result["error_message"])
    
    def test_overlay_mode_implementation(self):
        """Testa implementação do modo overlay"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Executar implementação do modo overlay
            result = self.integration_layer.implement_overlay_mode()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertTrue(result["overlay_enabled"])
            self.assertIsInstance(result["supported_tools"], list)
            self.assertGreater(len(result["supported_tools"]), 0)
            self.assertIn("overlay_hotkey", result)
            self.assertIn("overlay_position", result)
            self.assertIn("overlay_transparency", result)
            self.assertIn("performance_impact", result)
            self.assertIsInstance(result["game_compatibility"], dict)
    
    def test_steam_input_mapping_configuration(self):
        """Testa configuração de mapeamento Steam Input"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Executar configuração Steam Input
            result = self.integration_layer.configure_steam_input_mapping()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertTrue(result["steam_input_enabled"])
            self.assertIsInstance(result["development_profiles"], dict)
            self.assertGreater(len(result["development_profiles"]), 0)
            self.assertIsInstance(result["tool_mappings"], dict)
            self.assertIsInstance(result["gesture_mappings"], dict)
            self.assertIsInstance(result["macro_configurations"], dict)
    
    def test_steam_input_mapping_profiles(self):
        """Testa criação de perfis de desenvolvimento Steam Input"""
        profiles_result = self.integration_layer._create_development_profiles()
        
        self.assertTrue(profiles_result["success"])
        self.assertIsInstance(profiles_result["profiles"], dict)
        self.assertGreater(len(profiles_result["profiles"]), 0)
        
        # Verificar perfis específicos
        expected_profiles = ["ide_profile", "terminal_profile", "browser_profile"]
        for profile in expected_profiles:
            self.assertIn(profile, profiles_result["profiles"])
            self.assertIn("name", profiles_result["profiles"][profile])
            self.assertIn("description", profiles_result["profiles"][profile])
            self.assertIn("key_bindings", profiles_result["profiles"][profile])
    
    def test_development_macros_configuration(self):
        """Testa configuração de macros de desenvolvimento"""
        macros_result = self.integration_layer._configure_development_macros()
        
        self.assertTrue(macros_result["success"])
        self.assertIsInstance(macros_result["macros"], dict)
        self.assertGreater(len(macros_result["macros"]), 0)
        
        # Verificar macros específicos
        expected_macros = ["quick_commit", "run_tests", "build_project", "open_terminal"]
        for macro in expected_macros:
            self.assertIn(macro, macros_result["macros"])
            self.assertIn("sequence", macros_result["macros"][macro])
            self.assertIn("hotkey", macros_result["macros"][macro])
    
    def test_gesture_mappings_configuration(self):
        """Testa configuração de mapeamentos de gestos"""
        gesture_result = self.integration_layer._configure_gesture_mappings()
        
        self.assertTrue(gesture_result["success"])
        self.assertIsInstance(gesture_result["gestures"], dict)
        self.assertGreater(len(gesture_result["gestures"]), 0)
        
        # Verificar gestos específicos
        expected_gestures = ["swipe_up", "swipe_down", "pinch_in", "pinch_out", "two_finger_tap"]
        for gesture in expected_gestures:
            self.assertIn(gesture, gesture_result["gestures"])
    
    def test_steam_ecosystem_integration_report_positive(self):
        """Testa relatório de integração Steam para Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                model=SteamDeckModel.STEAM_DECK_512GB,
                confidence=0.95
            )
            
            # Gerar relatório de integração
            report = self.integration_layer.get_steam_ecosystem_integration_report()
            
            # Verificar estrutura do relatório
            self.assertTrue(report["steam_deck_detected"])
            self.assertEqual(report["detection_confidence"], 0.95)
            
            # Verificar seções de integração
            self.assertIn("integrations", report)
            self.assertIn("glossi", report["integrations"])
            self.assertIn("steam_cloud", report["integrations"])
            self.assertIn("overlay_mode", report["integrations"])
            self.assertIn("steam_input", report["integrations"])
            
            # Verificar score geral
            self.assertIn("overall_integration_score", report)
            self.assertGreaterEqual(report["overall_integration_score"], 0)
            self.assertLessEqual(report["overall_integration_score"], 100)
            
            # Verificar prontidão para desenvolvimento
            self.assertIn("development_readiness", report)
            self.assertIn(report["development_readiness"], ["excellent", "good", "fair", "poor"])
            
            # Verificar listas de feedback
            self.assertIsInstance(report["recommendations"], list)
            self.assertIsInstance(report["warnings"], list)
            self.assertIsInstance(report["errors"], list)
    
    def test_steam_ecosystem_integration_report_negative(self):
        """Testa relatório de integração para dispositivo não-Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção negativa
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=False,
                detection_method=DetectionMethod.FALLBACK,
                confidence=0.1
            )
            
            # Gerar relatório de integração
            report = self.integration_layer.get_steam_ecosystem_integration_report()
            
            # Verificar que detectou corretamente como não-Steam Deck
            self.assertFalse(report["steam_deck_detected"])
            self.assertEqual(report["detection_confidence"], 0.1)
            
            # Verificar que há aviso apropriado
            self.assertGreater(len(report["warnings"]), 0)
            self.assertTrue(any("not detected as steam deck" in warning.lower() 
                              for warning in report["warnings"]))
    
    def test_glossi_version_detection(self):
        """Testa detecção de versão do GlosSI"""
        with patch('subprocess.run') as mock_subprocess:
            # Mock resposta de versão
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "GlosSI v1.2.3"
            mock_subprocess.return_value = mock_result
            
            version = self.integration_layer._get_glossi_version("C:\\GlosSI\\GlosSI.exe")
            
            self.assertEqual(version, "GlosSI v1.2.3")
            mock_subprocess.assert_called_once_with(
                ["C:\\GlosSI\\GlosSI.exe", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
    
    def test_tool_specific_mappings(self):
        """Testa mapeamentos específicos por ferramenta"""
        mappings_result = self.integration_layer._configure_tool_specific_mappings()
        
        self.assertTrue(mappings_result["success"])
        self.assertIsInstance(mappings_result["mappings"], dict)
        self.assertGreater(len(mappings_result["mappings"]), 0)
        
        # Verificar ferramentas específicas
        expected_tools = ["vscode", "git", "terminal"]
        for tool in expected_tools:
            self.assertIn(tool, mappings_result["mappings"])
            self.assertIsInstance(mappings_result["mappings"][tool], dict)
    
    def test_overlay_tools_configuration(self):
        """Testa configuração de ferramentas do overlay"""
        tools_result = self.integration_layer._configure_overlay_tools()
        
        self.assertTrue(tools_result["success"])
        self.assertIsInstance(tools_result["tools"], list)
        self.assertGreater(len(tools_result["tools"]), 0)
        
        # Verificar ferramentas específicas
        expected_tools = ["Quick Terminal", "Code Snippets", "Git Status", "System Monitor"]
        for tool in expected_tools:
            self.assertIn(tool, tools_result["tools"])
    
    def test_cloud_storage_info(self):
        """Testa obtenção de informações de armazenamento na nuvem"""
        storage_info = self.integration_layer._get_cloud_storage_info()
        
        self.assertIn("total_bytes", storage_info)
        self.assertIn("used_bytes", storage_info)
        self.assertIn("available_bytes", storage_info)
        self.assertGreater(storage_info["total_bytes"], 0)
        self.assertGreaterEqual(storage_info["available_bytes"], 0)
        self.assertLessEqual(storage_info["used_bytes"], storage_info["total_bytes"])
    
    def test_configuration_sync_types(self):
        """Testa tipos de configuração para sincronização"""
        config_types = self.integration_layer._identify_configurations_for_sync()
        
        self.assertIsInstance(config_types, list)
        self.assertGreater(len(config_types), 0)
        
        # Verificar tipos específicos
        expected_types = [
            "controller_profiles",
            "input_mappings",
            "overlay_settings",
            "development_profiles"
        ]
        
        for config_type in expected_types:
            self.assertIn(config_type, config_types)
    
    def test_error_handling_in_ecosystem_integration(self):
        """Testa tratamento de erros durante integração do ecossistema"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Simular erro durante detecção
            mock_detection.side_effect = Exception("Test detection error")
            
            # Testar integração GlosSI
            result = self.integration_layer.integrate_with_glossi()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
            
            # Testar sincronização Steam Cloud
            result = self.integration_layer.synchronize_via_steam_cloud()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
            
            # Testar modo overlay
            result = self.integration_layer.implement_overlay_mode()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
            
            # Testar mapeamento Steam Input
            result = self.integration_layer.configure_steam_input_mapping()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])


class TestSteamDeckEcosystemIntegrationAdvanced(unittest.TestCase):
    """Testes avançados para integração com ecossistema Steam"""
    
    def setUp(self):
        """Configuração inicial dos testes avançados"""
        self.integration_layer = SteamDeckIntegrationLayer()
    
    def test_full_ecosystem_integration_workflow(self):
        """Testa fluxo completo de integração do ecossistema"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                model=SteamDeckModel.STEAM_DECK_512GB,
                confidence=0.95
            )
            
            # Executar todas as integrações
            glossi_result = self.integration_layer.integrate_with_glossi()
            cloud_result = self.integration_layer.synchronize_via_steam_cloud()
            overlay_result = self.integration_layer.implement_overlay_mode()
            input_result = self.integration_layer.configure_steam_input_mapping()
            
            # Verificar que todas foram bem-sucedidas
            self.assertTrue(glossi_result["success"])
            self.assertTrue(cloud_result["success"])
            self.assertTrue(overlay_result["success"])
            self.assertTrue(input_result["success"])
            
            # Gerar relatório final
            report = self.integration_layer.get_steam_ecosystem_integration_report()
            
            # Verificar relatório final
            self.assertTrue(report["steam_deck_detected"])
            self.assertGreaterEqual(report["overall_integration_score"], 80)
            self.assertEqual(report["development_readiness"], "excellent")
            
            # Verificar que todas as integrações foram aplicadas
            self.assertTrue(report["integrations"]["glossi"]["integrated"])
            self.assertTrue(report["integrations"]["steam_cloud"]["integrated"])
            self.assertTrue(report["integrations"]["overlay_mode"]["integrated"])
            self.assertTrue(report["integrations"]["steam_input"]["integrated"])
    
    def test_partial_integration_scenario(self):
        """Testa cenário de integração parcial com algumas falhas"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, '_check_steam_login_status') as mock_login:
            
            # Mock detecção Steam Deck positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock Steam não logado (falha na sincronização cloud)
            mock_login.return_value = {"logged_in": False}
            
            # Gerar relatório
            report = self.integration_layer.get_steam_ecosystem_integration_report()
            
            # Verificar que algumas integrações falharam
            self.assertTrue(report["steam_deck_detected"])
            self.assertLess(report["overall_integration_score"], 100)
            self.assertIn(report["development_readiness"], ["good", "fair"])
            
            # Deve haver avisos sobre falhas
            self.assertGreater(len(report["warnings"]), 0)


if __name__ == '__main__':
    unittest.main()