#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para Hierarchical Detection Prioritizer
Testa sistema de priorização hierárquica para detecção de aplicações.
"""

import unittest
from unittest.mock import Mock, patch
import os
import time

from core.hierarchical_detection_prioritizer import (
    HierarchicalDetectionPrioritizer,
    HierarchicalDetectionResult,
    HierarchicalDetectionReport,
    DetectionPriority,
    CompatibilityLevel,
    PriorityScore
)
from core.detection_base import DetectedApplication, DetectionMethod, ApplicationStatus


class TestHierarchicalDetectionPrioritizer(unittest.TestCase):
    """Testes para priorização hierárquica"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.prioritizer = HierarchicalDetectionPrioritizer()
        
        # Criar aplicações de teste
        self.installed_app = DetectedApplication(
            name="Git",
            version="2.47.1",
            install_path="C:\\Program Files\\Git",
            status=ApplicationStatus.INSTALLED,
            detection_method=DetectionMethod.REGISTRY,
            confidence=0.95
        )
        
        self.portable_app = DetectedApplication(
            name="Git Portable",
            version="2.46.0",
            install_path="C:\\PortableApps\\Git",
            status=ApplicationStatus.NOT_INSTALLED,
            detection_method=DetectionMethod.EXECUTABLE_SCAN,
            confidence=0.8
        )
        
        self.standard_location_app = DetectedApplication(
            name="Git System",
            version="2.45.0",
            install_path="C:\\Program Files (x86)\\Git",
            status=ApplicationStatus.NOT_INSTALLED,
            detection_method=DetectionMethod.PATH_BASED,
            confidence=0.7
        )
    
    def test_prioritizer_initialization(self):
        """Testa inicialização do priorizador"""
        self.assertIsNotNone(self.prioritizer)
        self.assertIsNotNone(self.prioritizer._standard_locations)
        self.assertIsNotNone(self.prioritizer._compatibility_rules)
        self.assertIsNotNone(self.prioritizer._custom_configurations)
    
    def test_prioritize_detections_with_installed_app(self):
        """Testa priorização com aplicação instalada"""
        detected_apps = [self.portable_app, self.installed_app, self.standard_location_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="git",
            detected_applications=detected_apps,
            required_version="2.47.1"
        )
        
        # Aplicação instalada deve ser recomendada
        self.assertEqual(result.component_name, "git")
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git")
        self.assertEqual(result.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.PERFECT)
        self.assertGreater(len(result.alternative_options), 0)
    
    def test_prioritize_detections_without_installed_app(self):
        """Testa priorização sem aplicação instalada"""
        detected_apps = [self.portable_app, self.standard_location_app]
        
        result = self.prioritizer.prioritize_detections(
            component_name="git",
            detected_applications=detected_apps,
            required_version="2.46.0"
        )
        
        # Aplicação portátil deve ser recomendada (maior confiança)
        self.assertEqual(result.component_name, "git")
        self.assertIsNotNone(result.recommended_option)
        self.assertEqual(result.recommended_option.name, "Git Portable")
        self.assertEqual(result.compatibility_level, CompatibilityLevel.PERFECT)
    
    def test_prioritize_detections_empty_list(self):
        """Testa priorização com lista vazia"""
        result = self.prioritizer.prioritize_detections(
            component_name="git",
            detected_applications=[],
            required_version="2.47.1"
        )
        
        self.assertEqual(result.component_name, "git")
        self.assertIsNone(result.recommended_option)
        self.assertEqual(len(result.detected_applications), 0)
        self.assertEqual(len(result.alternative_options), 0)
    
    def test_compatibility_level_calculation(self):
        """Testa cálculo de nível de compatibilidade"""
        # Versão perfeita
        compat_level = self.prioritizer._calculate_compatibility_level(
            self.installed_app, "2.47.1", None
        )
        self.assertEqual(compat_level, CompatibilityLevel.PERFECT)
        
        # Versão compatível (maior)
        app_newer = DetectedApplication(
            name="Git", version="2.48.0", install_path="", 
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        compat_level = self.prioritizer._calculate_compatibility_level(
            app_newer, "2.47.1", None
        )
        self.assertEqual(compat_level, CompatibilityLevel.COMPATIBLE)
        
        # Versão desatualizada
        app_older = DetectedApplication(
            name="Git", version="2.46.0", install_path="", 
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        compat_level = self.prioritizer._calculate_compatibility_level(
            app_older, "2.47.1", None
        )
        self.assertEqual(compat_level, CompatibilityLevel.OUTDATED)
        
        # Sem aplicação
        compat_level = self.prioritizer._calculate_compatibility_level(
            None, "2.47.1", None
        )
        self.assertEqual(compat_level, CompatibilityLevel.INCOMPATIBLE)
    
    def test_priority_score_calculation(self):
        """Testa cálculo de score de prioridade"""
        score = self.prioritizer._calculate_priority_score(
            self.installed_app,
            DetectionPriority.INSTALLED_APPLICATIONS,
            CompatibilityLevel.PERFECT
        )
        
        self.assertIsNotNone(score)
        self.assertEqual(score.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(score.base_score, 0.9)
        self.assertEqual(score.compatibility_bonus, 0.1)
        self.assertGreaterEqual(score.total_score, 0.9)
        self.assertLessEqual(score.total_score, 1.0)
    
    def test_is_compatible_version(self):
        """Testa verificação de compatibilidade de versão"""
        # Versão exata
        self.assertTrue(self.prioritizer._is_compatible_version(
            self.installed_app, "2.47.1", None
        ))
        
        # Versão compatível (major igual, minor maior)
        app_compatible = DetectedApplication(
            name="Git", version="2.48.0", install_path="", 
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        self.assertTrue(self.prioritizer._is_compatible_version(
            app_compatible, "2.47.1", None
        ))
        
        # Versão incompatível (major diferente)
        app_incompatible = DetectedApplication(
            name="Git", version="1.9.0", install_path="", 
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        self.assertFalse(self.prioritizer._is_compatible_version(
            app_incompatible, "2.47.1", None
        ))
        
        # Sem versão requerida
        self.assertTrue(self.prioritizer._is_compatible_version(
            self.installed_app, None, None
        ))
    
    def test_is_standard_location(self):
        """Testa verificação de localização padrão"""
        # Localização padrão
        self.assertTrue(self.prioritizer._is_standard_location(
            self.installed_app, "git"
        ))
        
        # Localização não padrão
        custom_app = DetectedApplication(
            name="Git", version="2.47.1", install_path="C:\\CustomApps\\Git",
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        self.assertFalse(self.prioritizer._is_standard_location(
            custom_app, "git"
        ))
    
    def test_has_custom_configuration(self):
        """Testa verificação de configuração personalizada"""
        # Configuração personalizada
        custom_app = DetectedApplication(
            name="Git", version="2.47.1", install_path="C:\\Users\\user\\portable\\Git",
            status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
        )
        self.assertTrue(self.prioritizer._has_custom_configuration(
            custom_app, "git"
        ))
        
        # Configuração padrão
        self.assertFalse(self.prioritizer._has_custom_configuration(
            self.installed_app, "git"
        ))
    
    def test_generate_comprehensive_report(self):
        """Testa geração de relatório abrangente"""
        # Criar resultados de teste
        results = [
            HierarchicalDetectionResult(
                component_name="git",
                priority_level=DetectionPriority.INSTALLED_APPLICATIONS,
                detected_applications=[self.installed_app],
                recommended_option=self.installed_app,
                compatibility_level=CompatibilityLevel.PERFECT,
                reasoning="Selected installed application"
            ),
            HierarchicalDetectionResult(
                component_name="python",
                priority_level=DetectionPriority.COMPATIBLE_VERSIONS,
                detected_applications=[self.portable_app],
                recommended_option=self.portable_app,
                compatibility_level=CompatibilityLevel.COMPATIBLE,
                reasoning="Selected compatible version"
            ),
            HierarchicalDetectionResult(
                component_name="java",
                priority_level=DetectionPriority.STANDARD_LOCATIONS,
                detected_applications=[],
                recommended_option=None,
                compatibility_level=CompatibilityLevel.INCOMPATIBLE,
                reasoning="No suitable installation found"
            )
        ]
        
        report = self.prioritizer.generate_comprehensive_report(results)
        
        # Verificar estatísticas básicas
        self.assertEqual(report.total_components_analyzed, 3)
        self.assertEqual(report.successful_detections, 2)
        self.assertEqual(report.failed_detections, 1)
        
        # Verificar distribuições
        self.assertIn(DetectionPriority.INSTALLED_APPLICATIONS, report.priority_distribution)
        self.assertIn(DetectionPriority.COMPATIBLE_VERSIONS, report.priority_distribution)
        self.assertIn(CompatibilityLevel.PERFECT, report.compatibility_distribution)
        self.assertIn(CompatibilityLevel.COMPATIBLE, report.compatibility_distribution)
        
        # Verificar confiança média
        self.assertGreater(report.detection_confidence_average, 0.0)
        
        # Verificar informações do sistema
        self.assertIn("platform", report.system_info)
        self.assertIn("python_version", report.system_info)
        
        # Verificar que há recomendações e avisos
        self.assertIsInstance(report.recommendations, list)
        self.assertIsInstance(report.warnings, list)
        self.assertIsInstance(report.errors, list)
    
    def test_sort_by_priority_criteria(self):
        """Testa ordenação por critérios de prioridade"""
        apps = [self.standard_location_app, self.installed_app, self.portable_app]
        
        sorted_apps = self.prioritizer._sort_by_priority_criteria(
            apps, DetectionPriority.INSTALLED_APPLICATIONS
        )
        
        # Deve ordenar por confiança (maior primeiro)
        self.assertEqual(sorted_apps[0].confidence, 0.95)  # installed_app
        self.assertEqual(sorted_apps[1].confidence, 0.8)   # portable_app
        self.assertEqual(sorted_apps[2].confidence, 0.7)   # standard_location_app
    
    def test_determine_priority_level(self):
        """Testa determinação do nível de prioridade"""
        apps = [self.installed_app, self.portable_app, self.standard_location_app]
        
        # Aplicação instalada deve ter prioridade máxima
        priority = self.prioritizer._determine_priority_level(self.installed_app, apps)
        self.assertEqual(priority, DetectionPriority.INSTALLED_APPLICATIONS)
        
        # Aplicação não instalada deve ter prioridade baseada na posição
        priority = self.prioritizer._determine_priority_level(self.portable_app, apps)
        self.assertIn(priority, [
            DetectionPriority.COMPATIBLE_VERSIONS,
            DetectionPriority.STANDARD_LOCATIONS,
            DetectionPriority.CUSTOM_CONFIGURATIONS
        ])
    
    def test_generate_reasoning(self):
        """Testa geração de raciocínio"""
        reasoning = self.prioritizer._generate_reasoning(
            "git",
            self.installed_app,
            [self.installed_app, self.portable_app],
            CompatibilityLevel.PERFECT
        )
        
        self.assertIn("Selected installed application", reasoning)
        self.assertIn("registry", reasoning.lower())
        self.assertIn("0.95", reasoning)
        self.assertIn("perfect", reasoning.lower())
        self.assertIn("1 alternative", reasoning)
    
    def test_error_handling_in_prioritization(self):
        """Testa tratamento de erros durante priorização"""
        # Simular erro durante priorização
        with patch.object(self.prioritizer, '_apply_hierarchical_prioritization') as mock_prioritize:
            mock_prioritize.side_effect = Exception("Test error")
            
            result = self.prioritizer.prioritize_detections(
                "test_component",
                [self.installed_app],
                "1.0.0"
            )
            
            self.assertEqual(result.component_name, "test_component")
            self.assertIsNone(result.recommended_option)
            self.assertIn("error", result.detection_metadata)
            self.assertIn("Test error", result.reasoning)


class TestHierarchicalDetectionIntegration(unittest.TestCase):
    """Testes de integração para priorização hierárquica"""
    
    def setUp(self):
        """Configuração inicial dos testes de integração"""
        self.prioritizer = HierarchicalDetectionPrioritizer()
    
    def test_full_prioritization_workflow(self):
        """Testa fluxo completo de priorização"""
        # Criar múltiplas aplicações com diferentes características
        apps = [
            DetectedApplication(
                name="Git Portable", version="2.46.0", install_path="C:\\PortableApps\\Git",
                status=ApplicationStatus.NOT_INSTALLED, detection_method=DetectionMethod.EXECUTABLE_SCAN, confidence=0.7
            ),
            DetectedApplication(
                name="Git", version="2.47.1", install_path="C:\\Program Files\\Git",
                status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.95
            ),
            DetectedApplication(
                name="Git Custom", version="2.45.0", install_path="C:\\CustomApps\\Git",
                status=ApplicationStatus.NOT_INSTALLED, detection_method=DetectionMethod.PATH_BASED, confidence=0.6
            ),
            DetectedApplication(
                name="Git System", version="2.48.0", install_path="C:\\Program Files (x86)\\Git",
                status=ApplicationStatus.NOT_INSTALLED, detection_method=DetectionMethod.PATH_BASED, confidence=0.8
            )
        ]
        
        # Executar priorização
        result = self.prioritizer.prioritize_detections(
            component_name="git",
            detected_applications=apps,
            required_version="2.47.1"
        )
        
        # Verificar resultado
        self.assertEqual(result.component_name, "git")
        self.assertIsNotNone(result.recommended_option)
        
        # Aplicação instalada deve ser recomendada
        self.assertEqual(result.recommended_option.name, "Git")
        self.assertEqual(result.priority_level, DetectionPriority.INSTALLED_APPLICATIONS)
        self.assertEqual(result.compatibility_level, CompatibilityLevel.PERFECT)
        
        # Deve haver alternativas
        self.assertEqual(len(result.alternative_options), 3)
        
        # Score deve ser alto
        self.assertIsNotNone(result.priority_score)
        self.assertGreaterEqual(result.priority_score.total_score, 0.9)
        
        # Reasoning deve ser informativo
        self.assertIn("installed application", result.reasoning.lower())
        self.assertIn("perfect", result.reasoning.lower())
    
    def test_complex_compatibility_scenarios(self):
        """Testa cenários complexos de compatibilidade"""
        # Cenário: versões muito diferentes
        apps = [
            DetectedApplication(
                name="Old Git", version="1.9.0", install_path="C:\\OldGit",
                status=ApplicationStatus.INSTALLED, detection_method=DetectionMethod.REGISTRY, confidence=0.9
            ),
            DetectedApplication(
                name="Future Git", version="3.0.0", install_path="C:\\FutureGit",
                status=ApplicationStatus.NOT_INSTALLED, detection_method=DetectionMethod.EXECUTABLE_SCAN, confidence=0.8
            ),
            DetectedApplication(
                name="Compatible Git", version="2.46.0", install_path="C:\\CompatibleGit",
                status=ApplicationStatus.NOT_INSTALLED, detection_method=DetectionMethod.PATH_BASED, confidence=0.7
            )
        ]
        
        result = self.prioritizer.prioritize_detections(
            component_name="git",
            detected_applications=apps,
            required_version="2.47.1"
        )
        
        # Deve escolher a versão mais compatível, não necessariamente a instalada
        self.assertIsNotNone(result.recommended_option)
        
        # Verificar que a compatibilidade foi considerada
        if result.recommended_option.name == "Old Git":
            self.assertIn(result.compatibility_level, [CompatibilityLevel.INCOMPATIBLE, CompatibilityLevel.OUTDATED])
        elif result.recommended_option.name == "Compatible Git":
            self.assertEqual(result.compatibility_level, CompatibilityLevel.OUTDATED)


if __name__ == '__main__':
    unittest.main()