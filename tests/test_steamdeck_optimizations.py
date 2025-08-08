#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para Steam Deck Optimizations
Testa otimizações específicas para Steam Deck incluindo controlador, energia e touchscreen.
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


class TestSteamDeckOptimizations(unittest.TestCase):
    """Testes para otimizações Steam Deck"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.integration_layer = SteamDeckIntegrationLayer()
    
    def test_controller_configurations_on_steam_deck(self):
        """Testa configurações de controlador em Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Executar configurações de controlador
            result = self.integration_layer.apply_controller_specific_configurations()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertGreater(len(result["configurations_applied"]), 0)
            self.assertIsInstance(result["configurations_applied"], list)
            
            # Verificar configurações específicas
            if "steam_input" in result["configurations_applied"]:
                self.assertTrue(result["steam_input_enabled"])
            
            if "controller_profiles" in result["configurations_applied"]:
                self.assertIsInstance(result["controller_profiles_created"], list)
                self.assertGreater(len(result["controller_profiles_created"]), 0)
    
    def test_controller_configurations_on_non_steam_deck(self):
        """Testa configurações de controlador em dispositivo não-Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção negativa
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=False,
                detection_method=DetectionMethod.FALLBACK,
                confidence=0.1
            )
            
            # Executar configurações de controlador
            result = self.integration_layer.apply_controller_specific_configurations()
            
            # Verificar que falhou apropriadamente
            self.assertFalse(result["success"])
            self.assertEqual(len(result["configurations_applied"]), 0)
            self.assertIn("Not a Steam Deck device", result["error_message"])
    
    def test_power_profile_optimizations(self):
        """Testa otimizações de perfil de energia"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Executar otimizações de energia
            result = self.integration_layer.optimize_power_profiles()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertGreater(len(result["optimizations_applied"]), 0)
            self.assertIsInstance(result["optimizations_applied"], list)
            
            # Verificar otimizações específicas
            self.assertIn("current_profile", result)
            self.assertIn("estimated_battery_improvement", result)
            self.assertGreaterEqual(result["estimated_battery_improvement"], 0)
            self.assertLessEqual(result["estimated_battery_improvement"], 25)
            
            # Verificar flags de otimização
            self.assertIsInstance(result["cpu_governor_set"], bool)
            self.assertIsInstance(result["gpu_frequency_limited"], bool)
            self.assertIsInstance(result["thermal_throttling_enabled"], bool)
            self.assertIsInstance(result["battery_optimization_enabled"], bool)
    
    def test_touchscreen_driver_configuration(self):
        """Testa configuração de drivers de touchscreen"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Executar configurações de touchscreen
            result = self.integration_layer.configure_touchscreen_drivers()
            
            # Verificar resultado
            self.assertTrue(result["success"])
            self.assertGreater(len(result["configurations_applied"]), 0)
            self.assertIsInstance(result["configurations_applied"], list)
            
            # Verificar configurações específicas
            self.assertIsInstance(result["touch_enabled"], bool)
            self.assertIsInstance(result["multi_touch_enabled"], bool)
            self.assertIsInstance(result["gesture_recognition_enabled"], bool)
            self.assertIsInstance(result["calibration_applied"], bool)
            self.assertIsInstance(result["touch_sensitivity_configured"], bool)
            self.assertIsInstance(result["palm_rejection_enabled"], bool)
            self.assertIsInstance(result["edge_rejection_configured"], bool)
            
            # Verificar versão do driver
            self.assertIn("driver_version", result)
            self.assertNotEqual(result["driver_version"], "unknown")
    
    def test_steam_deck_optimization_report_positive(self):
        """Testa relatório de otimização para Steam Deck detectado"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Gerar relatório de otimização
            report = self.integration_layer.get_steam_deck_optimization_report()
            
            # Verificar estrutura do relatório
            self.assertTrue(report["steam_deck_detected"])
            self.assertEqual(report["detection_confidence"], 0.95)
            self.assertEqual(report["detection_method"], "dmi_smbios")
            
            # Verificar seção de otimizações
            self.assertIn("optimizations", report)
            self.assertIn("controller", report["optimizations"])
            self.assertIn("power", report["optimizations"])
            self.assertIn("touchscreen", report["optimizations"])
            
            # Verificar score geral
            self.assertIn("overall_optimization_score", report)
            self.assertGreaterEqual(report["overall_optimization_score"], 0)
            self.assertLessEqual(report["overall_optimization_score"], 100)
            
            # Verificar listas de feedback
            self.assertIsInstance(report["recommendations"], list)
            self.assertIsInstance(report["warnings"], list)
            self.assertIsInstance(report["errors"], list)
            
            # Verificar timestamp
            self.assertIn("report_timestamp", report)
            self.assertIsInstance(report["report_timestamp"], float)
    
    def test_steam_deck_optimization_report_negative(self):
        """Testa relatório de otimização para dispositivo não-Steam Deck"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção negativa
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=False,
                detection_method=DetectionMethod.FALLBACK,
                confidence=0.1
            )
            
            # Gerar relatório de otimização
            report = self.integration_layer.get_steam_deck_optimization_report()
            
            # Verificar que detectou corretamente como não-Steam Deck
            self.assertFalse(report["steam_deck_detected"])
            self.assertEqual(report["detection_confidence"], 0.1)
            
            # Verificar que há aviso apropriado
            self.assertGreater(len(report["warnings"]), 0)
            self.assertTrue(any("not detected as steam deck" in warning.lower() 
                              for warning in report["warnings"]))
    
    def test_steam_input_configuration(self):
        """Testa configuração específica do Steam Input"""
        # Testar com Steam presente
        with patch.object(self.integration_layer, '_detect_steam_client_presence') as mock_steam:
            mock_steam.return_value = {
                "found": True,
                "steam_path": "C:\\Program Files (x86)\\Steam"
            }
            
            result = self.integration_layer._configure_steam_input()
            
            self.assertTrue(result["success"])
            self.assertTrue(result["steam_input_enabled"])
            self.assertIn("api_version", result)
            self.assertTrue(result["controller_support"])
        
        # Testar sem Steam presente
        with patch.object(self.integration_layer, '_detect_steam_client_presence') as mock_steam:
            mock_steam.return_value = {
                "found": False,
                "steam_path": ""
            }
            
            result = self.integration_layer._configure_steam_input()
            
            self.assertFalse(result["success"])
            self.assertIn("Steam client not found", result["error"])
    
    def test_controller_profiles_creation(self):
        """Testa criação de perfis de controlador"""
        result = self.integration_layer._create_controller_profiles()
        
        self.assertTrue(result["success"])
        self.assertIsInstance(result["profiles"], list)
        self.assertGreater(len(result["profiles"]), 0)
        self.assertEqual(result["profiles_created"], len(result["profiles"]))
        
        # Verificar que perfis específicos estão incluídos
        expected_profiles = [
            "Development Tools Profile",
            "IDE Navigation Profile",
            "Terminal Profile",
            "Browser Profile"
        ]
        
        for profile in expected_profiles:
            self.assertIn(profile, result["profiles"])
    
    def test_battery_improvement_calculation(self):
        """Testa cálculo de melhoria da bateria"""
        # Teste com diferentes números de otimizações
        improvement_0 = self.integration_layer._calculate_battery_improvement(0)
        improvement_3 = self.integration_layer._calculate_battery_improvement(3)
        improvement_10 = self.integration_layer._calculate_battery_improvement(10)
        
        self.assertEqual(improvement_0, 0)
        self.assertEqual(improvement_3, 15)  # 3 * 5%
        self.assertEqual(improvement_10, 25)  # Máximo 25%
        
        # Verificar que nunca excede 25%
        improvement_high = self.integration_layer._calculate_battery_improvement(20)
        self.assertEqual(improvement_high, 25)
    
    def test_power_saving_features(self):
        """Testa ativação de recursos de economia de energia"""
        result = self.integration_layer._enable_power_saving_features()
        
        self.assertTrue(result["success"])
        self.assertIsInstance(result["features"], list)
        self.assertGreater(len(result["features"]), 0)
        self.assertEqual(result["features_enabled"], len(result["features"]))
        
        # Verificar recursos específicos
        expected_features = [
            "CPU frequency scaling",
            "GPU power gating", 
            "Display dimming",
            "USB power management",
            "Audio codec power down"
        ]
        
        for feature in expected_features:
            self.assertIn(feature, result["features"])
    
    def test_touchscreen_gesture_configuration(self):
        """Testa configuração de gestos do touchscreen"""
        result = self.integration_layer._configure_gesture_recognition()
        
        self.assertTrue(result["success"])
        self.assertIsInstance(result["gestures_enabled"], list)
        self.assertGreater(len(result["gestures_enabled"]), 0)
        self.assertIn("gesture_sensitivity", result)
        
        # Verificar gestos específicos
        expected_gestures = ["tap", "double_tap", "long_press", "swipe", "pinch", "rotate"]
        
        for gesture in expected_gestures:
            self.assertIn(gesture, result["gestures_enabled"])
    
    def test_error_handling_in_optimizations(self):
        """Testa tratamento de erros durante otimizações"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Simular erro durante detecção
            mock_detection.side_effect = Exception("Test detection error")
            
            # Testar configurações de controlador
            result = self.integration_layer.apply_controller_specific_configurations()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
            
            # Testar otimizações de energia
            result = self.integration_layer.optimize_power_profiles()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
            
            # Testar configurações de touchscreen
            result = self.integration_layer.configure_touchscreen_drivers()
            self.assertFalse(result["success"])
            self.assertIn("Test detection error", result["error_message"])
    
    def test_optimization_report_with_errors(self):
        """Testa relatório de otimização com erros"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection, \
             patch.object(self.integration_layer, 'apply_controller_specific_configurations') as mock_controller:
            
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                confidence=0.95
            )
            
            # Mock erro em configurações de controlador
            mock_controller.side_effect = Exception("Controller configuration failed")
            
            # Gerar relatório
            report = self.integration_layer.get_steam_deck_optimization_report()
            
            # Verificar que erros foram capturados
            self.assertGreater(len(report["errors"]), 0)
            self.assertTrue(any("Controller configuration failed" in error 
                              for error in report["errors"]))
            
            # Score deve ser menor devido aos erros
            self.assertLess(report["overall_optimization_score"], 100)


class TestSteamDeckOptimizationIntegration(unittest.TestCase):
    """Testes de integração para otimizações Steam Deck"""
    
    def setUp(self):
        """Configuração inicial dos testes de integração"""
        self.integration_layer = SteamDeckIntegrationLayer()
    
    def test_full_optimization_workflow(self):
        """Testa fluxo completo de otimização"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            # Mock detecção positiva
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                model=SteamDeckModel.STEAM_DECK_512GB,
                confidence=0.95
            )
            
            # Executar todas as otimizações
            controller_result = self.integration_layer.apply_controller_specific_configurations()
            power_result = self.integration_layer.optimize_power_profiles()
            touchscreen_result = self.integration_layer.configure_touchscreen_drivers()
            
            # Verificar que todas foram bem-sucedidas
            self.assertTrue(controller_result["success"])
            self.assertTrue(power_result["success"])
            self.assertTrue(touchscreen_result["success"])
            
            # Gerar relatório final
            report = self.integration_layer.get_steam_deck_optimization_report()
            
            # Verificar relatório final
            self.assertTrue(report["steam_deck_detected"])
            self.assertGreaterEqual(report["overall_optimization_score"], 80)
            self.assertTrue(report["optimizations"]["controller"]["applied"])
            self.assertTrue(report["optimizations"]["power"]["applied"])
            self.assertTrue(report["optimizations"]["touchscreen"]["applied"])
            
            # Deve haver recomendações positivas
            self.assertGreater(len(report["recommendations"]), 0)
            self.assertTrue(any("well optimized" in rec.lower() 
                              for rec in report["recommendations"]))


if __name__ == '__main__':
    unittest.main()