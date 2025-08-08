#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hierarchical Detection Prioritizer
Sistema de priorização hierárquica para detecção de aplicações e runtimes.
Implementa priorização baseada em aplicações instaladas, versões compatíveis,
localizações padrão e configurações personalizadas.
"""

import logging
import os
import platform
import subprocess
import winreg
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import time

from .detection_base import DetectedApplication, DetectionMethod, ApplicationStatus


class DetectionPriority(Enum):
    """Prioridades hierárquicas de detecção"""
    INSTALLED_APPLICATIONS = 1  # Aplicações já instaladas (prioridade máxima)
    COMPATIBLE_VERSIONS = 2     # Versões compatíveis
    STANDARD_LOCATIONS = 3      # Localizações padrão do sistema
    CUSTOM_CONFIGURATIONS = 4   # Configurações personalizadas do usuário


class CompatibilityLevel(Enum):
    """Níveis de compatibilidade"""
    PERFECT = "perfect"         # Versão exata requerida
    COMPATIBLE = "compatible"   # Versão compatível
    OUTDATED = "outdated"      # Versão desatualizada mas funcional
    INCOMPATIBLE = "incompatible"  # Versão incompatível


@dataclass
class PriorityScore:
    """Score de prioridade para uma detecção"""
    priority_level: DetectionPriority
    base_score: float  # Score base (0.0 - 1.0)
    compatibility_bonus: float = 0.0  # Bônus por compatibilidade
    location_bonus: float = 0.0       # Bônus por localização
    configuration_bonus: float = 0.0  # Bônus por configuração
    total_score: float = field(init=False)
    
    def __post_init__(self):
        """Calcula o score total"""
        self.total_score = min(1.0, self.base_score + self.compatibility_bonus + 
                              self.location_bonus + self.configuration_bonus)


@dataclass
class HierarchicalDetectionResult:
    """Resultado de detecção hierárquica com priorização"""
    component_name: str
    priority_level: DetectionPriority
    detected_applications: List[DetectedApplication] = field(default_factory=list)
    recommended_option: Optional[DetectedApplication] = None
    priority_score: Optional[PriorityScore] = None
    compatibility_level: CompatibilityLevel = CompatibilityLevel.INCOMPATIBLE
    reasoning: str = ""
    alternative_options: List[DetectedApplication] = field(default_factory=list)
    detection_metadata: Dict[str, Any] = field(default_factory=dict)
    detection_timestamp: float = field(default_factory=time.time)


@dataclass
class HierarchicalDetectionReport:
    """Relatório abrangente de detecção hierárquica"""
    total_components_analyzed: int = 0
    successful_detections: int = 0
    failed_detections: int = 0
    hierarchical_results: List[HierarchicalDetectionResult] = field(default_factory=list)
    priority_distribution: Dict[DetectionPriority, int] = field(default_factory=dict)
    compatibility_distribution: Dict[CompatibilityLevel, int] = field(default_factory=dict)
    detection_confidence_average: float = 0.0
    total_detection_time: float = 0.0
    system_info: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    report_timestamp: float = field(default_factory=time.time)


class HierarchicalDetectionPrioritizer:
    """
    Sistema de priorização hierárquica para detecção de aplicações.
    
    Implementa a estratégia de priorização definida nos requisitos:
    1. Aplicações já instaladas (prioridade máxima)
    2. Versões compatíveis (verificação de compatibilidade)
    3. Localizações padrão do sistema (paths conhecidos)
    4. Configurações personalizadas do usuário (configurações específicas)
    """
    
    def __init__(self):
        self.logger = logging.getLogger("hierarchical_detection_prioritizer")
        self._standard_locations = self._initialize_standard_locations()
        self._compatibility_rules = self._initialize_compatibility_rules()
        self._custom_configurations = self._load_custom_configurations()
    
    def prioritize_detections(self, 
                            component_name: str,
                            detected_applications: List[DetectedApplication],
                            required_version: Optional[str] = None,
                            compatibility_rules: Optional[Dict[str, Any]] = None) -> HierarchicalDetectionResult:
        """
        Prioriza detecções de acordo com a hierarquia definida.
        
        Args:
            component_name: Nome do componente sendo analisado
            detected_applications: Lista de aplicações detectadas
            required_version: Versão requerida (opcional)
            compatibility_rules: Regras de compatibilidade específicas (opcional)
            
        Returns:
            HierarchicalDetectionResult com priorização aplicada
        """
        start_time = time.time()
        
        try:
            # Aplicar priorização hierárquica
            prioritized_apps = self._apply_hierarchical_prioritization(
                component_name, detected_applications, required_version, compatibility_rules
            )
            
            # Determinar recomendação principal
            recommended_option = self._determine_recommended_option(prioritized_apps)
            
            # Calcular nível de compatibilidade
            compatibility_level = self._calculate_compatibility_level(
                recommended_option, required_version, compatibility_rules
            )
            
            # Gerar reasoning
            reasoning = self._generate_reasoning(
                component_name, recommended_option, prioritized_apps, compatibility_level
            )
            
            # Determinar prioridade principal
            priority_level = self._determine_priority_level(recommended_option, prioritized_apps)
            
            # Calcular score de prioridade
            priority_score = self._calculate_priority_score(
                recommended_option, priority_level, compatibility_level
            )
            
            # Preparar alternativas
            alternative_options = [app for app in prioritized_apps if app != recommended_option]
            
            result = HierarchicalDetectionResult(
                component_name=component_name,
                priority_level=priority_level,
                detected_applications=prioritized_apps,
                recommended_option=recommended_option,
                priority_score=priority_score,
                compatibility_level=compatibility_level,
                reasoning=reasoning,
                alternative_options=alternative_options,
                detection_metadata={
                    "total_detections": len(detected_applications),
                    "prioritized_detections": len(prioritized_apps),
                    "detection_time": time.time() - start_time,
                    "required_version": required_version,
                    "compatibility_rules_applied": compatibility_rules is not None
                }
            )
            
            self.logger.info(f"Hierarchical prioritization completed for {component_name}: "
                           f"{len(prioritized_apps)} apps prioritized, "
                           f"recommended: {recommended_option.name if recommended_option else 'None'}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in hierarchical prioritization for {component_name}: {e}")
            return HierarchicalDetectionResult(
                component_name=component_name,
                priority_level=DetectionPriority.CUSTOM_CONFIGURATIONS,
                reasoning=f"Error during prioritization: {str(e)}",
                detection_metadata={"error": str(e)}
            )
    
    def generate_comprehensive_report(self, 
                                    hierarchical_results: List[HierarchicalDetectionResult]) -> HierarchicalDetectionReport:
        """
        Gera relatório abrangente de detecção hierárquica.
        
        Args:
            hierarchical_results: Lista de resultados hierárquicos
            
        Returns:
            HierarchicalDetectionReport com análise completa
        """
        try:
            report = HierarchicalDetectionReport()
            
            # Estatísticas básicas
            report.total_components_analyzed = len(hierarchical_results)
            report.successful_detections = len([r for r in hierarchical_results if r.recommended_option])
            report.failed_detections = report.total_components_analyzed - report.successful_detections
            report.hierarchical_results = hierarchical_results
            
            # Distribuição de prioridades
            priority_counts = {}
            for result in hierarchical_results:
                priority = result.priority_level
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            report.priority_distribution = priority_counts
            
            # Distribuição de compatibilidade
            compatibility_counts = {}
            for result in hierarchical_results:
                compat = result.compatibility_level
                compatibility_counts[compat] = compatibility_counts.get(compat, 0) + 1
            report.compatibility_distribution = compatibility_counts
            
            # Confiança média
            confidence_scores = []
            for result in hierarchical_results:
                if result.recommended_option:
                    confidence_scores.append(result.recommended_option.confidence)
            report.detection_confidence_average = (
                sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            )
            
            # Tempo total de detecção
            report.total_detection_time = sum(
                r.detection_metadata.get("detection_time", 0.0) for r in hierarchical_results
            )
            
            # Informações do sistema
            report.system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "python_version": platform.python_version()
            }
            
            # Gerar recomendações
            report.recommendations = self._generate_report_recommendations(hierarchical_results)
            
            # Gerar avisos
            report.warnings = self._generate_report_warnings(hierarchical_results)
            
            # Gerar erros
            report.errors = self._generate_report_errors(hierarchical_results)
            
            self.logger.info(f"Comprehensive report generated: {report.successful_detections}/"
                           f"{report.total_components_analyzed} successful detections")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return HierarchicalDetectionReport(
                errors=[f"Error generating report: {str(e)}"]
            )
    
    def _apply_hierarchical_prioritization(self,
                                         component_name: str,
                                         detected_applications: List[DetectedApplication],
                                         required_version: Optional[str],
                                         compatibility_rules: Optional[Dict[str, Any]]) -> List[DetectedApplication]:
        """Aplica priorização hierárquica às aplicações detectadas"""
        if not detected_applications:
            return []
        
        # Classificar aplicações por prioridade
        prioritized_apps = []
        
        # 1. Aplicações já instaladas (prioridade máxima)
        installed_apps = [app for app in detected_applications 
                         if app.status == ApplicationStatus.INSTALLED]
        prioritized_apps.extend(self._sort_by_priority_criteria(installed_apps, DetectionPriority.INSTALLED_APPLICATIONS))
        
        # 2. Versões compatíveis
        if required_version or compatibility_rules:
            compatible_apps = [app for app in detected_applications 
                             if app not in prioritized_apps and 
                             self._is_compatible_version(app, required_version, compatibility_rules)]
            prioritized_apps.extend(self._sort_by_priority_criteria(compatible_apps, DetectionPriority.COMPATIBLE_VERSIONS))
        
        # 3. Localizações padrão do sistema
        standard_location_apps = [app for app in detected_applications 
                                if app not in prioritized_apps and 
                                self._is_standard_location(app, component_name)]
        prioritized_apps.extend(self._sort_by_priority_criteria(standard_location_apps, DetectionPriority.STANDARD_LOCATIONS))
        
        # 4. Configurações personalizadas do usuário
        custom_config_apps = [app for app in detected_applications 
                            if app not in prioritized_apps and 
                            self._has_custom_configuration(app, component_name)]
        prioritized_apps.extend(self._sort_by_priority_criteria(custom_config_apps, DetectionPriority.CUSTOM_CONFIGURATIONS))
        
        # Adicionar aplicações restantes
        remaining_apps = [app for app in detected_applications if app not in prioritized_apps]
        prioritized_apps.extend(remaining_apps)
        
        return prioritized_apps
    
    def _sort_by_priority_criteria(self, 
                                 applications: List[DetectedApplication], 
                                 priority_level: DetectionPriority) -> List[DetectedApplication]:
        """Ordena aplicações dentro do mesmo nível de prioridade"""
        return sorted(applications, key=lambda app: (
            -app.confidence,  # Maior confiança primeiro
            app.detection_method.value,  # Método de detecção
            app.version  # Versão
        ))
    
    def _determine_recommended_option(self, prioritized_apps: List[DetectedApplication]) -> Optional[DetectedApplication]:
        """Determina a opção recomendada da lista priorizada"""
        if not prioritized_apps:
            return None
        
        # A primeira aplicação da lista priorizada é a recomendada
        return prioritized_apps[0]
    
    def _calculate_compatibility_level(self,
                                     application: Optional[DetectedApplication],
                                     required_version: Optional[str],
                                     compatibility_rules: Optional[Dict[str, Any]]) -> CompatibilityLevel:
        """Calcula o nível de compatibilidade de uma aplicação"""
        if not application:
            return CompatibilityLevel.INCOMPATIBLE
        
        if not required_version and not compatibility_rules:
            return CompatibilityLevel.COMPATIBLE
        
        # Verificar compatibilidade de versão
        if required_version:
            if application.version == required_version:
                return CompatibilityLevel.PERFECT
            elif self._is_compatible_version(application, required_version, compatibility_rules):
                return CompatibilityLevel.COMPATIBLE
            elif self._is_outdated_but_functional(application, required_version):
                return CompatibilityLevel.OUTDATED
            else:
                # Check if major versions are too different for incompatibility
                try:
                    app_version_parts = application.version.split('.')
                    required_version_parts = required_version.split('.')
                    
                    if len(app_version_parts) >= 1 and len(required_version_parts) >= 1:
                        app_major = int(app_version_parts[0])
                        req_major = int(required_version_parts[0])
                        
                        # If major versions differ by more than 1, it's incompatible
                        if abs(app_major - req_major) > 1:
                            return CompatibilityLevel.INCOMPATIBLE
                        else:
                            return CompatibilityLevel.OUTDATED
                    
                except (ValueError, IndexError):
                    pass
                
                return CompatibilityLevel.INCOMPATIBLE
        
        return CompatibilityLevel.COMPATIBLE
    
    def _generate_reasoning(self,
                          component_name: str,
                          recommended_option: Optional[DetectedApplication],
                          prioritized_apps: List[DetectedApplication],
                          compatibility_level: CompatibilityLevel) -> str:
        """Gera explicação do raciocínio de priorização"""
        if not recommended_option:
            return f"No suitable installation found for {component_name}"
        
        reasoning_parts = []
        
        # Explicar por que esta opção foi escolhida
        if recommended_option.status == ApplicationStatus.INSTALLED:
            reasoning_parts.append("Selected installed application (highest priority)")
        
        reasoning_parts.append(f"Detection method: {recommended_option.detection_method.value}")
        reasoning_parts.append(f"Confidence: {recommended_option.confidence:.2f}")
        reasoning_parts.append(f"Compatibility: {compatibility_level.value}")
        
        if len(prioritized_apps) > 1:
            reasoning_parts.append(f"{len(prioritized_apps) - 1} alternative options available")
        
        return "; ".join(reasoning_parts)
    
    def _determine_priority_level(self,
                                recommended_option: Optional[DetectedApplication],
                                prioritized_apps: List[DetectedApplication]) -> DetectionPriority:
        """Determina o nível de prioridade da opção recomendada"""
        if not recommended_option:
            return DetectionPriority.CUSTOM_CONFIGURATIONS
        
        if recommended_option.status == ApplicationStatus.INSTALLED:
            return DetectionPriority.INSTALLED_APPLICATIONS
        
        # Determinar baseado na posição na lista priorizada
        index = prioritized_apps.index(recommended_option) if recommended_option in prioritized_apps else -1
        
        if index == 0:
            return DetectionPriority.INSTALLED_APPLICATIONS
        elif index <= len(prioritized_apps) // 4:
            return DetectionPriority.COMPATIBLE_VERSIONS
        elif index <= len(prioritized_apps) // 2:
            return DetectionPriority.STANDARD_LOCATIONS
        else:
            return DetectionPriority.CUSTOM_CONFIGURATIONS
    
    def _calculate_priority_score(self,
                                application: Optional[DetectedApplication],
                                priority_level: DetectionPriority,
                                compatibility_level: CompatibilityLevel) -> Optional[PriorityScore]:
        """Calcula o score de prioridade para uma aplicação"""
        if not application:
            return None
        
        # Score base baseado no nível de prioridade
        base_scores = {
            DetectionPriority.INSTALLED_APPLICATIONS: 0.9,
            DetectionPriority.COMPATIBLE_VERSIONS: 0.7,
            DetectionPriority.STANDARD_LOCATIONS: 0.5,
            DetectionPriority.CUSTOM_CONFIGURATIONS: 0.3
        }
        
        base_score = base_scores.get(priority_level, 0.1)
        
        # Bônus por compatibilidade
        compatibility_bonuses = {
            CompatibilityLevel.PERFECT: 0.1,
            CompatibilityLevel.COMPATIBLE: 0.05,
            CompatibilityLevel.OUTDATED: 0.0,
            CompatibilityLevel.INCOMPATIBLE: -0.2
        }
        
        compatibility_bonus = compatibility_bonuses.get(compatibility_level, 0.0)
        
        # Bônus por localização (se em localização padrão)
        location_bonus = 0.05 if self._is_standard_location(application, "") else 0.0
        
        # Bônus por configuração (se tem configuração personalizada)
        configuration_bonus = 0.03 if self._has_custom_configuration(application, "") else 0.0
        
        return PriorityScore(
            priority_level=priority_level,
            base_score=base_score,
            compatibility_bonus=compatibility_bonus,
            location_bonus=location_bonus,
            configuration_bonus=configuration_bonus
        )
    
    def _is_compatible_version(self,
                             application: DetectedApplication,
                             required_version: Optional[str],
                             compatibility_rules: Optional[Dict[str, Any]]) -> bool:
        """Verifica se a versão da aplicação é compatível"""
        if not required_version:
            return True
        
        try:
            # Implementação básica de comparação de versões
            app_version_parts = application.version.split('.')
            required_version_parts = required_version.split('.')
            
            # Comparar versões major.minor
            if len(app_version_parts) >= 2 and len(required_version_parts) >= 2:
                app_major = int(app_version_parts[0])
                app_minor = int(app_version_parts[1])
                req_major = int(required_version_parts[0])
                req_minor = int(required_version_parts[1])
                
                # Compatível se major igual e minor >= requerido
                return app_major == req_major and app_minor >= req_minor
            
            return application.version == required_version
            
        except (ValueError, IndexError):
            # Se não conseguir comparar versões, considerar compatível
            return True
    
    def _is_outdated_but_functional(self,
                                  application: DetectedApplication,
                                  required_version: str) -> bool:
        """Verifica se a versão é desatualizada mas ainda funcional"""
        try:
            app_version_parts = application.version.split('.')
            required_version_parts = required_version.split('.')
            
            if len(app_version_parts) >= 1 and len(required_version_parts) >= 1:
                app_major = int(app_version_parts[0])
                req_major = int(required_version_parts[0])
                
                # Funcional se major version não está muito atrás
                if abs(app_major - req_major) <= 1:
                    return True
                
                # Se major version é muito diferente, é incompatível
                return False
            
            return False
            
        except (ValueError, IndexError):
            return False
    
    def _is_standard_location(self, application: DetectedApplication, component_name: str) -> bool:
        """Verifica se a aplicação está em localização padrão"""
        if not application.install_path:
            return False
        
        install_path_lower = application.install_path.lower()
        
        # Localizações padrão comuns
        standard_paths = [
            "program files",
            "program files (x86)",
            "/usr/bin",
            "/usr/local/bin",
            "/opt",
            "c:\\windows\\system32"
        ]
        
        return any(std_path in install_path_lower for std_path in standard_paths)
    
    def _has_custom_configuration(self, application: DetectedApplication, component_name: str) -> bool:
        """Verifica se a aplicação tem configuração personalizada"""
        # Verificar se há configurações personalizadas conhecidas
        custom_config_indicators = [
            "portable",
            "custom",
            "user",
            "appdata",
            "documents"
        ]
        
        install_path_lower = application.install_path.lower() if application.install_path else ""
        
        return any(indicator in install_path_lower for indicator in custom_config_indicators)
    
    def _initialize_standard_locations(self) -> Dict[str, List[str]]:
        """Inicializa localizações padrão por sistema operacional"""
        if platform.system() == "Windows":
            return {
                "system": [
                    "C:\\Program Files",
                    "C:\\Program Files (x86)",
                    "C:\\Windows\\System32"
                ],
                "user": [
                    os.path.expanduser("~\\AppData\\Local"),
                    os.path.expanduser("~\\AppData\\Roaming")
                ]
            }
        else:
            return {
                "system": [
                    "/usr/bin",
                    "/usr/local/bin",
                    "/opt"
                ],
                "user": [
                    os.path.expanduser("~/.local/bin"),
                    os.path.expanduser("~/bin")
                ]
            }
    
    def _initialize_compatibility_rules(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa regras de compatibilidade padrão"""
        return {
            "git": {
                "min_version": "2.0.0",
                "recommended_version": "2.47.1"
            },
            "dotnet": {
                "min_version": "6.0.0",
                "recommended_version": "8.0.0"
            },
            "java": {
                "min_version": "11.0.0",
                "recommended_version": "21.0.0"
            },
            "python": {
                "min_version": "3.8.0",
                "recommended_version": "3.12.0"
            },
            "node": {
                "min_version": "16.0.0",
                "recommended_version": "20.0.0"
            }
        }
    
    def _load_custom_configurations(self) -> Dict[str, Any]:
        """Carrega configurações personalizadas do usuário"""
        try:
            config_path = Path.home() / ".environment_dev" / "custom_detection_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.debug(f"Could not load custom configurations: {e}")
        
        return {}
    
    def _generate_report_recommendations(self, results: List[HierarchicalDetectionResult]) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        # Contar detecções por prioridade
        priority_counts = {}
        for result in results:
            priority = result.priority_level
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Recomendações baseadas na distribuição de prioridades
        total_results = len(results)
        if total_results > 0:
            installed_ratio = priority_counts.get(DetectionPriority.INSTALLED_APPLICATIONS, 0) / total_results
            
            if installed_ratio < 0.5:
                recommendations.append("Consider installing more components to improve detection reliability")
            
            if priority_counts.get(DetectionPriority.CUSTOM_CONFIGURATIONS, 0) > total_results * 0.3:
                recommendations.append("Many components detected in custom locations - consider standardizing installations")
        
        return recommendations
    
    def _generate_report_warnings(self, results: List[HierarchicalDetectionResult]) -> List[str]:
        """Gera avisos baseados nos resultados"""
        warnings = []
        
        # Verificar compatibilidade
        incompatible_count = len([r for r in results if r.compatibility_level == CompatibilityLevel.INCOMPATIBLE])
        if incompatible_count > 0:
            warnings.append(f"{incompatible_count} components have incompatible versions")
        
        # Verificar confiança baixa
        low_confidence_count = len([r for r in results 
                                  if r.recommended_option and r.recommended_option.confidence < 0.5])
        if low_confidence_count > 0:
            warnings.append(f"{low_confidence_count} components have low detection confidence")
        
        return warnings
    
    def _generate_report_errors(self, results: List[HierarchicalDetectionResult]) -> List[str]:
        """Gera erros baseados nos resultados"""
        errors = []
        
        # Verificar detecções falhadas
        failed_detections = [r for r in results if not r.recommended_option]
        if failed_detections:
            errors.extend([f"Failed to detect: {r.component_name}" for r in failed_detections])
        
        # Verificar erros nos metadados
        for result in results:
            if "error" in result.detection_metadata:
                errors.append(f"{result.component_name}: {result.detection_metadata['error']}")
        
        return errors