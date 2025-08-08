#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para Steam Deck Integration Layer
Testa detecção de hardware Steam Deck via DMI/SMBIOS e métodos de fallback.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import os
import platform
import time

from core.steamdeck_integration_layer import (
    SteamDeckIntegrationLayer,
    SteamDeckDetectionResult,
    DetectionMethod,
    SteamDeckModel,
    SteamDeckIntegrationError
)


class TestSteamDeckDetection(unittest.TestCase):
    """Testes para detecção Steam Deck"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.integration_layer = SteamDeckIntegrationLayer()
    
    def test_steam_deck_detection_initialization(self):
        """Testa inicialização do sistema de detecção"""
        self.assertIsNotNone(self.integration_layer)
        self.assertIsNone(self.integration_layer._detection_cache)
        self.assertEqual(self.integration_layer._cache_timeout, 300)
        self.assertIn("Valve", self.integration_layer._dmi_identifiers)
        self.assertIn("Jupiter", self.integration_layer._dmi_identifiers)
        self.assertIn("Steam Deck", self.integration_layer._dmi_identifiers)
    
    def test_manual_configuration_positive(self):
        """Testa configuração manual positiva"""
        result = self.integration_layer.allow_manual_configuration_for_edge_cases(True)
        
        self.assertTrue(result.is_steam_deck)
        self.assertEqual(result.detection_method, DetectionMethod.MANUAL_CONFIG)
        self.assertEqual(result.confidence, 1.0)
        self.assertTrue(result.detection_details["manual_override"])
        self.assertEqual(self.integration_layer._manual_override, True)
    
    def test_manual_configuration_negative(self):
        """Testa configuração manual negativa"""
        result = self.integration_layer.allow_manual_configuration_for_edge_cases(False)
        
        self.assertFalse(result.is_steam_deck)
        self.assertEqual(result.detection_method, DetectionMethod.MANUAL_CONFIG)
        self.assertEqual(result.confidence, 0.0)
        self.assertTrue(result.detection_details["manual_override"])
        self.assertEqual(self.integration_layer._manual_override, False)
    
    def test_steam_deck_model_determination(self):
        """Testa determinação do modelo Steam Deck"""
        # Teste modelo OLED
        hardware_info_oled = {"display": "1280x800 OLED", "model": "Steam Deck OLED"}
        model = self.integration_layer._determine_steam_deck_model(hardware_info_oled)
        self.assertEqual(model, SteamDeckModel.STEAM_DECK_OLED)
        
        # Teste modelo 512GB
        hardware_info_512 = {"storage": "512GB NVMe", "model": "Steam Deck 512GB"}
        model = self.integration_layer._determine_steam_deck_model(hardware_info_512)
        self.assertEqual(model, SteamDeckModel.STEAM_DECK_512GB)
        
        # Teste modelo desconhecido
        hardware_info_unknown = {"manufacturer": "Valve", "model": "Jupiter"}
        model = self.integration_layer._determine_steam_deck_model(hardware_info_unknown)
        self.assertEqual(model, SteamDeckModel.UNKNOWN)
    
    def test_comprehensive_detection_with_manual_override(self):
        """Testa detecção abrangente com override manual"""
        # Configurar override manual
        self.integration_layer._manual_override = True
        
        result = self.integration_layer.get_comprehensive_detection_result()
        
        self.assertTrue(result.is_steam_deck)
        self.assertEqual(result.detection_method, DetectionMethod.MANUAL_CONFIG)
        self.assertEqual(result.confidence, 1.0)
    
    def test_clear_detection_cache(self):
        """Testa limpeza do cache de detecção"""
        # Simular cache válido
        self.integration_layer._detection_cache = SteamDeckDetectionResult(
            is_steam_deck=True,
            detection_timestamp=time.time()
        )
        
        self.assertTrue(self.integration_layer._is_cache_valid())
        
        # Limpar cache
        self.integration_layer.clear_detection_cache()
        
        self.assertIsNone(self.integration_layer._detection_cache)
        self.assertFalse(self.integration_layer._is_cache_valid())
    
    def test_detection_report_generation(self):
        """Testa geração de relatório de detecção"""
        with patch.object(self.integration_layer, 'get_comprehensive_detection_result') as mock_detection:
            mock_detection.return_value = SteamDeckDetectionResult(
                is_steam_deck=True,
                detection_method=DetectionMethod.DMI_SMBIOS,
                model=SteamDeckModel.STEAM_DECK_512GB,
                confidence=0.95,
                hardware_info={"manufacturer": "Valve", "model": "Jupiter"},
                detection_details={"matched_identifier": "Valve"}
            )
            
            report = self.integration_layer.get_detection_report()
            
            self.assertTrue(report["steam_deck_detected"])
            self.assertEqual(report["detection_method"], "dmi_smbios")
            self.assertEqual(report["model"], "steam_deck_512gb")
            self.assertEqual(report["confidence"], 0.95)
            self.assertIn("manufacturer", report["hardware_info"])


if __name__ == '__main__':
    unittest.main()