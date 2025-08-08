#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Hierarchical Detection Prioritizer
Testes abrangentes para o sistema de priorização hierárquica de detecção.
"""

import unittest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.hierarchical_detection_prioritizer import (
    HierarchicalDetectionPrioritizer,
    DetectionPriority,
    CompatibilityLevel,
    PriorityScore,
    HierarchicalDetectionResult,
    HierarchicalDetectionReport
)
from core.detection_base import DetectedApplication, DetectionMethod, ApplicationStatus


class TestHierarchicalDetectionPrioritizer(unittest.TestCase):
    """Testes para HierarchicalDetectionPrioritizer"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.prioritizer = HierarchicalDetectionPrioritizer()
        
        # Criar aplicações de teste
        self.installed_app = DetectedApplication(
            name="Git",
            version="2.47.1",
            install_path="C:\\Program Files\\Git",
            executable_path="C:\\Program Files\\Git\\bin\\git.exe",
            detection_method=DetectionMethod.REGISTRY,
            status=ApplicationStatus.INSTALLED,
            confidence=0.95
        )
        
        self.portable_app = DetectedApplication(
            name="Git Portable",
            version="2.46.0",
            install_path="C:\\Users\\Test\\PortableApps\\Git",
            executable_path="C:\\Users\\Test\\PortableApps\\Git\\git.exe",
            detection_method=DetectionMethod.EXECUTABLE_SCAN,
            status=ApplicationStatus.INSTALLED,
            confidence=0.8
        )
        
        self.outdated_app = DetectedApplication(
            name="Git Old",
            version="2.30.0",
            install_path="C:\\Program Files (x86)\\Git",
            executable_path="C:\\Program Files (x86)\\Git\\bin\\git.exe",
            detection_method=DetectionMethod.PATH_BASED,
            status=ApplicationStatus.OUTDATED,
            confidence=0.7
        )
        
        self.custom_app = DetectedApplication(
            name="Git Custom",
            version="2.47.1",
            install_path="C:\\Users\\Test\\Documents\\CustomGit",
            executable_path="C:\\Users\\Test\\Documents\\CustomGit\\git.exe",
            detection_method=DetectionMethod.MANUAL_OVERRIDE,
            status=ApplicationStatus.INSTALLED,
            confidence=0.6
        )
    
    def test_prioritize_detections_installed_applications_priority(self):
        """Testa se aplicações instaladas têm prioridade máxima"""
        detected_apps = [self.portable_app, self.installed_app, self.outdated_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=detected_apps,
            required_version="2.47.1"
        )
        
        # Verificar se a aplicação instalada foi recomendada
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git")
        self.assertEqual(result.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.PERFECT)
    
    def test_prioritize_detections_compatible_versions_priority(self):
        """Testa priorização de versões compatíveis"""
        # Remover status INSTALLED para testar compatibilidade
        compatible_app = DetectedApplication(
            name="Git Compatible",
            version="2.47.0",
            install_path="C:\\Program Files\\Git",
            executable_path="C:\\Program Files\\Git\\bin\\git.exe",
            detection_method=DetectionMethod.REGISTRY,
            status=ApplicationStatus.UNKNOWN,
            confidence=0.9
        )
        
        detected_apps = [self.outdated_app, compatible_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=detected_apps,
            required_version="2.47.1"
        )
        
        # Verificar se a versão compatível foi priorizada
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Compatible")
        self.assertEqual(result.compatibility_level, CompatibilityLevel.COMPATIBLE)
    
    def test_prioritize_detections_standard_locations_priority(self):
        """Testa priorização de localizações padrão"""
        standard_location_app = DetectedApplication(
            name="Git Standard",
            version="2.46.0",
            install_path="C:\\Program Files\\Git",
            executable_path="C:\\Program Files\\Git\\bin\\git.exe",
            detection_method=DetectionMethod.PATH_BASED,
            status=ApplicationStatus.UNKNOWN,
            confidence=0.8
        )
        
        # Create custom app with UNKNOWN status to test standard location priority
        custom_app_unknown = DetectedApplication(
            name="Git Custom",
            version="2.47.1",
            install_path="C:\\Users\\Test\\Documents\\CustomGit",
            executable_path="C:\\Users\\Test\\Documents\\CustomGit\\git.exe",
            detection_method=DetectionMethod.MANUAL_OVERRIDE,
            status=ApplicationStatus.UNKNOWN,  # Changed to UNKNOWN
            confidence=0.6
        )
        
        detected_apps = [custom_app_unknown, standard_location_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=detected_apps
        )
        
        # Verificar se a localização padrão foi priorizada
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Standard")
    
    def test_prioritize_detections_custom_configurations_priority(self):
        """Testa priorização de configurações personalizadas"""
        detected_apps = [self.custom_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=detected_apps
        )
        
        # Verificar se a configuração personalizada foi detectada
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Custom")
        self.assertEqual(result.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)  # Ainda é INSTALLED
    
    def test_prioritize_detections_empty_list(self):
        """Testa comportamento com lista vazia"""
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=[]
        )
        
        self.assertIsNone(result.recommended_option)
        self.assertEqual(len(result.detected_applications), 0)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.INCOMPATIBLE)
    
    def test_calculate_compatibility_level_perfect(self):
        """Testa cálculo de compatibilidade perfeita"""
        compatibility_level = self.prioritizer._calculate_compatibility_level(
            self.installed_app, "2.47.1", None
        )
        
        self.assertEqual(compatibility_level, CompatibilityLevel.PERFECT)
    
    def test_calculate_compatibility_level_compatible(self):
        """Testa cálculo de compatibilidade"""
        app_with_compatible_version = DetectedApplication(
            name="Git",
            version="2.47.0",
            status=ApplicationStatus.INSTALLED,
            confidence=0.9
        )
        
        compatibility_level = self.prioritizer._calculate_compatibility_level(
            app_with_compatible_version, "2.47.1", None
        )
        
        self.assertEqual(compatibility_level, CompatibilityLevel.COMPATIBLE)
    
    def test_calculate_compatibility_level_outdated(self):
        """Testa cálculo de versão desatualizada"""
        compatibility_level = self.prioritizer._calculate_compatibility_level(
            self.outdated_app, "2.47.1", None
        )
        
        self.assertEqual(compatibility_level, CompatibilityLevel.OUTDATED)
    
    def test_calculate_compatibility_level_incompatible(self):
        """Testa cálculo de incompatibilidade"""
        very_old_app = DetectedApplication(
            name="Git Very Old",
            version="0.9.0",  # Changed to be more than 1 major version different
            status=ApplicationStatus.INSTALLED,
            confidence=0.9
        )
        
        compatibility_level = self.prioritizer._calculate_compatibility_level(
            very_old_app, "2.47.1", None
        )
        
        self.assertEqual(compatibility_level, CompatibilityLevel.INCOMPATIBLE)
    
    def test_priority_score_calculation(self):
        """Testa cálculo de score de prioridade"""
        priority_score = self.prioritizer._calculate_priority_score(
            self.installed_app,
            DetectionPriority.INSTALLED_APPLICATIONS,
            CompatibilityLevel.PERFECT
        )
        
        self.assertIsNotNone(priority_score)
        self.assertEqual(priority_score.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(priority_score.base_score, 0.9)
        self.assertEqual(priority_score.compatibility_bonus, 0.1)
        self.assertGreater(priority_score.total_score, 0.9)
    
    def test_is_compatible_version_exact_match(self):
        """Testa verificação de versão exata"""
        is_compatible = self.prioritizer._is_compatible_version(
            self.installed_app, "2.47.1", None
        )
        
        self.assertTrue(is_compatible)
    
    def test_is_compatible_version_minor_compatible(self):
        """Testa compatibilidade de versão minor"""
        app_with_higher_minor = DetectedApplication(
            name="Git",
            version="2.48.0",
            status=ApplicationStatus.INSTALLED,
            confidence=0.9
        )
        
        is_compatible = self.prioritizer._is_compatible_version(
            app_with_higher_minor, "2.47.1", None
        )
        
        self.assertTrue(is_compatible)
    
    def test_is_compatible_version_major_incompatible(self):
        """Testa incompatibilidade de versão major"""
        app_with_different_major = DetectedApplication(
            name="Git",
            version="3.0.0",
            status=ApplicationStatus.INSTALLED,
            confidence=0.9
        )
        
        is_compatible = self.prioritizer._is_compatible_version(
            app_with_different_major, "2.47.1", None
        )
        
        self.assertFalse(is_compatible)
    
    def test_is_standard_location_windows(self):
        """Testa detecção de localização padrão no Windows"""
        is_standard = self.prioritizer._is_standard_location(self.installed_app, "Git")
        self.assertTrue(is_standard)
        
        is_not_standard = self.prioritizer._is_standard_location(self.custom_app, "Git")
        self.assertFalse(is_not_standard)
    
    def test_has_custom_configuration(self):
        """Testa detecção de configuração personalizada"""
        has_custom = self.prioritizer._has_custom_configuration(self.custom_app, "Git")
        self.assertTrue(has_custom)
        
        has_not_custom = self.prioritizer._has_custom_configuration(self.installed_app, "Git")
        self.assertFalse(has_not_custom)
    
    def test_generate_reasoning(self):
        """Testa geração de raciocínio"""
        reasoning = self.prioritizer._generate_reasoning(
            "Git",
            self.installed_app,
            [self.installed_app, self.portable_app],
            CompatibilityLevel.PERFECT
        )
        
        self.assertIn("Selected installed application", reasoning)
        self.assertIn("registry", reasoning)
        self.assertIn("0.95", reasoning)
        self.assertIn("perfect", reasoning)
        self.assertIn("1 alternative", reasoning)
    
    def test_sort_by_priority_criteria(self):
        """Testa ordenação por critérios de prioridade"""
        apps = [self.portable_app, self.installed_app, self.outdated_app]
        
        sorted_apps = self.prioritizer._sort_by_priority_criteria(
            apps, DetectionPriority.INSTALLED_APPLICATIONS
        )
        
        # Deve ordenar por confiança (maior primeiro)
        self.assertEqual(sorted_apps[0], self.installed_app)  # confidence 0.95
        self.assertEqual(sorted_apps[1], self.portable_app)   # confidence 0.8
        self.assertEqual(sorted_apps[2], self.outdated_app)   # confidence 0.7


class TestHierarchicalDetectionReport(unittest.TestCase):
    """Testes para HierarchicalDetectionReport"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.prioritizer = HierarchicalDetectionPrioritizer()
        
        # Criar resultados de teste
        self.successful_result = HierarchicalDetectionResult(
            component_name="Git",
            priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
            recommended_option=DetectedApplication(
                name="Git",
                version="2.47.1",
                status=ApplicationStatus.INSTALLED,
                confidence=0.95
            ),
            compatibility_level=CompatibilityLevel.PERFECT,
            reasoning="Test reasoning",
            detection_metadata={"detection_time": 0.5}
        )
        
        self.failed_result = HierarchicalDetectionResult(
            component_name="Java",
            priority_level=DetectionPriority.CUSTOM_CONFIGURATIONS,
            compatibility_level=CompatibilityLevel.INCOMPATIBLE,
            reasoning="No suitable installation found",
            detection_metadata={"detection_time": 0.2, "error": "Not found"}
        )
    
    def test_generate_comprehensive_report(self):
        """Testa geração de relatório abrangente"""
        results = [self.successful_result, self.failed_result]
        
        report = self.prioritizer.generate_comprehensive_report(results)
        
        # Verificar estatísticas básicas
        self.assertEqual(report.total_components_analyzed, 2)
        self.assertEqual(report.successful_detections, 1)
        self.assertEqual(report.failed_detections, 1)
        
        # Verificar distribuição de prioridades
        self.assertEqual(report.priority_distribution[DetectionPriority.INSTALLED_APPLICATIONS], 1)
        self.assertEqual(report.priority_distribution[DetectionPriority.CUSTOM_CONFIGURATIONS], 1)
        
        # Verificar distribuição de compatibilidade
        self.assertEqual(report.compatibility_distribution[CompatibilityLevel.PERFECT], 1)
        self.assertEqual(report.compatibility_distribution[CompatibilityLevel.INCOMPATIBLE], 1)
        
        # Verificar confiança média
        self.assertEqual(report.detection_confidence_average, 0.95)
        
        # Verificar tempo total
        self.assertEqual(report.total_detection_time, 0.7)
        
        # Verificar informações do sistema
        self.assertIn("platform", report.system_info)
        self.assertIn("python_version", report.system_info)
        
        # Verificar erros
        self.assertIn("Failed to detect: Java", report.errors)
        self.assertIn("Java: Not found", report.errors)
    
    def test_generate_report_recommendations(self):
        """Testa geração de recomendações"""
        # Criar resultados com muitas configurações personalizadas
        custom_results = []
        for i in range(5):
            result = HierarchicalDetectionResult(
                component_name=f"Component{i}",
                priority_level=DetectionPriority.CUSTOM_CONFIGURATIONS,
                compatibility_level=CompatibilityLevel.COMPATIBLE
            )
            custom_results.append(result)
        
        report = self.prioritizer.generate_comprehensive_report(custom_results)
        
        # Deve recomendar padronização
        self.assertTrue(any("standardizing installations" in rec for rec in report.recommendations))
    
    def test_generate_report_warnings(self):
        """Testa geração de avisos"""
        # Criar resultado com baixa confiança
        low_confidence_result = HierarchicalDetectionResult(
            component_name="LowConfidence",
            priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
            recommended_option=DetectedApplication(
                name="LowConfidence",
                version="1.0.0",
                status=ApplicationStatus.INSTALLED,
                confidence=0.3  # Baixa confiança
            ),
            compatibility_level=CompatibilityLevel.INCOMPATIBLE
        )
        
        results = [low_confidence_result]
        report = self.prioritizer.generate_comprehensive_report(results)
        
        # Deve gerar avisos sobre compatibilidade e confiança
        self.assertTrue(any("incompatible versions" in warning for warning in report.warnings))
        self.assertTrue(any("low detection confidence" in warning for warning in report.warnings))
    
    def test_empty_results_report(self):
        """Testa relatório com resultados vazios"""
        report = self.prioritizer.generate_comprehensive_report([])
        
        self.assertEqual(report.total_components_analyzed, 0)
        self.assertEqual(report.successful_detections, 0)
        self.assertEqual(report.failed_detections, 0)
        self.assertEqual(report.detection_confidence_average, 0.0)
        self.assertEqual(report.total_detection_time, 0.0)


class TestPriorityScore(unittest.TestCase):
    """Testes para PriorityScore"""
    
    def test_priority_score_calculation(self):
        """Testa cálculo automático do score total"""
        score = PriorityScore(
            priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
            base_score=0.8,
            compatibility_bonus=0.1,
            location_bonus=0.05,
            configuration_bonus=0.03
        )
        
        expected_total = 0.8 + 0.1 + 0.05 + 0.03
        self.assertEqual(score.total_score, expected_total)
    
    def test_priority_score_max_limit(self):
        """Testa limite máximo do score"""
        score = PriorityScore(
            priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
            base_score=0.9,
            compatibility_bonus=0.2,  # Valores altos para testar limite
            location_bonus=0.1,
            configuration_bonus=0.1
        )
        
        # Score total deve ser limitado a 1.0
        self.assertEqual(score.total_score, 1.0)


class TestIntegrationScenarios(unittest.TestCase):
    """Testes de cenários de integração"""
    
    def setUp(self):
        """Configuração inicial"""
        self.prioritizer = HierarchicalDetectionPrioritizer()
    
    def test_complex_prioritization_scenario(self):
        """Testa cenário complexo de priorização"""
        # Criar múltiplas aplicações com diferentes características
        apps = [
            # Aplicação instalada em localização padrão (deve ser priorizada)
            DetectedApplication(
                name="Git Standard",
                version="2.47.1",
                install_path="C:\\Program Files\\Git",
                detection_method=DetectionMethod.REGISTRY,
                status=ApplicationStatus.INSTALLED,
                confidence=0.95
            ),
            # Aplicação portátil com versão compatível
            DetectedApplication(
                name="Git Portable",
                version="2.47.0",
                install_path="C:\\Users\\Test\\PortableApps\\Git",
                detection_method=DetectionMethod.EXECUTABLE_SCAN,
                status=ApplicationStatus.INSTALLED,
                confidence=0.8
            ),
            # Aplicação desatualizada em localização padrão
            DetectedApplication(
                name="Git Old",
                version="2.30.0",
                install_path="C:\\Program Files (x86)\\Git",
                detection_method=DetectionMethod.PATH_BASED,
                status=ApplicationStatus.OUTDATED,
                confidence=0.7
            ),
            # Aplicação personalizada com versão perfeita
            DetectedApplication(
                name="Git Custom",
                version="2.47.1",
                install_path="C:\\Users\\Test\\Documents\\CustomGit",
                detection_method=DetectionMethod.MANUAL_OVERRIDE,
                status=ApplicationStatus.INSTALLED,
                confidence=0.6
            )
        ]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=apps,
            required_version="2.47.1"
        )
        
        # A aplicação padrão instalada deve ser recomendada
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Standard")
        self.assertEqual(result.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.PERFECT)
        
        # Deve ter alternativas
        self.assertGreater(len(result.alternative_options), 0)
        
        # Score deve ser alto
        self.assertIsNotNone(result.priority_score)
        self.assertGreater(result.priority_score.total_score, 0.9)
    
    def test_no_perfect_match_scenario(self):
        """Testa cenário sem match perfeito"""
        apps = [
            DetectedApplication(
                name="Git Compatible",
                version="2.46.0",
                install_path="C:\\Program Files\\Git",
                detection_method=DetectionMethod.REGISTRY,
                status=ApplicationStatus.INSTALLED,
                confidence=0.9
            ),
            DetectedApplication(
                name="Git Outdated",
                version="2.30.0",
                install_path="C:\\Users\\Test\\Git",
                detection_method=DetectionMethod.EXECUTABLE_SCAN,
                status=ApplicationStatus.OUTDATED,
                confidence=0.7
            )
        ]
        
        result = self.prioritizer.prioritize_detections(
            component_name="Git",
            detected_applications=apps,
            required_version="2.47.1"
        )
        
        # Deve recomendar a versão compatível
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Compatible")
        # Changed expectation since 2.46.0 vs 2.47.1 is considered outdated (lower minor version)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.OUTDATED)
    
    def test_multiple_components_report(self):
        """Testa relatório com múltiplos componentes"""
        # Simular resultados para múltiplos componentes
        components = ["Git", "Java", "Python", "Node.js", ".NET"]
        results = []
        
        for i, component in enumerate(components):
            if i % 2 == 0:  # Componentes pares são bem-sucedidos
                result = HierarchicalDetectionResult(
                    component_name=component,
                    priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
                    recommended_option=DetectedApplication(
                        name=component,
                        version="1.0.0",
                        status=ApplicationStatus.INSTALLED,
                        confidence=0.9
                    ),
                    compatibility_level=CompatibilityLevel.PERFECT,
                    detection_metadata={"detection_time": 0.5}
                )
            else:  # Componentes ímpares falham
                result = HierarchicalDetectionResult(
                    component_name=component,
                    priority_level=DetectionPriority.CUSTOM_CONFIGURATIONS,
                    compatibility_level=CompatibilityLevel.INCOMPATIBLE,
                    reasoning="Not found",
                    detection_metadata={"detection_time": 0.2, "error": "Not found"}
                )
            results.append(result)
        
        report = self.prioritizer.generate_comprehensive_report(results)
        
        # Verificar estatísticas
        self.assertEqual(report.total_components_analyzed, 5)
        self.assertEqual(report.successful_detections, 3)  # Git, Python, .NET
        self.assertEqual(report.failed_detections, 2)     # Java, Node.js
        
        # Verificar que há erros reportados
        self.assertGreater(len(report.errors), 0)


if __name__ == '__main__':
    # Configurar logging para testes
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Executar testes
    unittest.main(verbosity=2)