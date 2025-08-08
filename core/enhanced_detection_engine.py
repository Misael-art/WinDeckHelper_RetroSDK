#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Detection Engine - Sistema de Detecção Aprimorado
Integra todos os sistemas de recomendações prioritárias com o motor de detecção existente.
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

# Importar sistemas existentes
from .detection_engine import DetectionEngine, DetectionResult, DetectedApplication, ApplicationStatus

# Importar novos sistemas implementados
from .dependency_graph_analyzer import DependencyGraphAnalyzer, DependencyConflict
from .post_installation_integrity import PostInstallationIntegrityChecker, ComponentIntegrityReport
from .compatibility_matrix import CompatibilityMatrix, ConflictDetection
from .environment_contamination_detector import EnvironmentContaminationDetector, ContaminationDetection
from .dynamic_configuration_system import DynamicConfigurationSystem
from .auto_repair_system import AutoRepairSystem, RepairSession

@dataclass
class EnhancedDetectionResult:
    """Resultado aprimorado de detecção com análises adicionais"""
    # Resultado base
    base_result: DetectionResult
    
    # Análises adicionais
    dependency_analysis: Optional[Dict[str, Any]] = None
    integrity_reports: List[ComponentIntegrityReport] = field(default_factory=list)
    compatibility_conflicts: List[ConflictDetection] = field(default_factory=list)
    contamination_detections: List[ContaminationDetection] = field(default_factory=list)
    repair_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Métricas de qualidade do ambiente
    environment_health_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    
    # Timestamps
    analysis_start_time: float = field(default_factory=time.time)
    analysis_end_time: Optional[float] = None
    total_analysis_time: float = 0.0

class EnhancedDetectionEngine:
    """Motor de detecção aprimorado com sistemas integrados"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger("enhanced_detection")
        self.config_dir = config_dir or Path.cwd() / "config"
        
        # Motor de detecção base
        self.base_engine = DetectionEngine()
        
        # Sistemas aprimorados
        self.dependency_analyzer = DependencyGraphAnalyzer()
        self.integrity_checker = PostInstallationIntegrityChecker()
        self.compatibility_matrix = CompatibilityMatrix()
        self.contamination_detector = EnvironmentContaminationDetector()
        self.config_system = DynamicConfigurationSystem()
        self.auto_repair = AutoRepairSystem()
        
        # Configurações
        self.enable_dependency_analysis = True
        self.enable_integrity_checking = True
        self.enable_compatibility_checking = True
        self.enable_contamination_detection = True
        self.enable_auto_repair = True
        self.auto_repair_threshold = 0.7  # Score mínimo para auto-reparo
        
        # Cache de análises
        self.analysis_cache = {}
        self.cache_ttl = 3600  # 1 hora
        
        # Lock para thread safety
        self.lock = threading.RLock()
        
        # Carregar configurações
        self.load_configuration()
        
        # Inicializar sistemas
        self.initialize_systems()
    
    def initialize_systems(self):
        """Inicializa todos os sistemas integrados"""
        try:
            # Carregar dados de compatibilidade
            self.compatibility_matrix.load_compatibility_data()
            
            # Criar baseline do sistema para detecção de contaminação
            self.contamination_detector.create_system_baseline()
            
            # Configurar sistema de configuração dinâmica
            config_files = [
                self.config_dir / "detection_config.yaml",
                self.config_dir / "compatibility_config.yaml",
                self.config_dir / "security_config.yaml"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    self.config_system.load_configuration_file(str(config_file))
            
            self.logger.info("Sistemas aprimorados inicializados com sucesso")
        
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistemas: {e}")
    
    def detect_applications_enhanced(self, target_apps: Optional[List[str]] = None,
                                   enable_deep_analysis: bool = True) -> EnhancedDetectionResult:
        """Executa detecção aprimorada com análises completas"""
        result = EnhancedDetectionResult(
            base_result=DetectionResult(),
            analysis_start_time=time.time()
        )
        
        try:
            self.logger.info("Iniciando detecção aprimorada de aplicações")
            
            # 1. Detecção base
            self.logger.info("Executando detecção base...")
            result.base_result = self.base_engine.detect_all_applications(target_apps)
            
            if enable_deep_analysis:
                # 2. Análise de dependências
                if self.enable_dependency_analysis:
                    self.logger.info("Analisando dependências...")
                    result.dependency_analysis = self._analyze_dependencies(result.base_result.applications)
                
                # 3. Verificação de integridade
                if self.enable_integrity_checking:
                    self.logger.info("Verificando integridade...")
                    result.integrity_reports = self._check_integrity(result.base_result.applications)
                
                # 4. Verificação de compatibilidade
                if self.enable_compatibility_checking:
                    self.logger.info("Verificando compatibilidade...")
                    result.compatibility_conflicts = self._check_compatibility(result.base_result.applications)
                
                # 5. Detecção de contaminação
                if self.enable_contamination_detection:
                    self.logger.info("Detectando contaminação do ambiente...")
                    result.contamination_detections = self._detect_contamination()
                
                # 6. Geração de recomendações de reparo
                if self.enable_auto_repair:
                    self.logger.info("Gerando recomendações de reparo...")
                    result.repair_recommendations = self._generate_repair_recommendations(result)
                
                # 7. Cálculo de scores de qualidade
                self.logger.info("Calculando scores de qualidade...")
                self._calculate_quality_scores(result)
            
            result.analysis_end_time = time.time()
            result.total_analysis_time = result.analysis_end_time - result.analysis_start_time
            
            self.logger.info(f"Detecção aprimorada concluída em {result.total_analysis_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Erro durante detecção aprimorada: {e}")
            result.base_result.errors.append(f"Erro na análise aprimorada: {e}")
        
        return result
    
    def _analyze_dependencies(self, applications: List[DetectedApplication]) -> Dict[str, Any]:
        """Analisa dependências das aplicações detectadas"""
        try:
            # Construir grafo de dependências
            for app in applications:
                self.dependency_analyzer.add_component(
                    app.name,
                    app.version,
                    app.metadata.get('dependencies', [])
                )
            
            # Analisar dependências transitivas
            transitive_deps = self.dependency_analyzer.analyze_transitive_dependencies()
            
            # Detectar conflitos
            conflicts = self.dependency_analyzer.detect_conflicts()
            
            # Gerar relatório
            dependency_report = self.dependency_analyzer.generate_dependency_report()
            
            return {
                'transitive_dependencies': transitive_deps,
                'conflicts': [conflict.__dict__ for conflict in conflicts],
                'dependency_report': dependency_report,
                'graph_data': self.dependency_analyzer.get_graph_visualization_data()
            }
        
        except Exception as e:
            self.logger.error(f"Erro na análise de dependências: {e}")
            return {'error': str(e)}
    
    def _check_integrity(self, applications: List[DetectedApplication]) -> List[ComponentIntegrityReport]:
        """Verifica integridade das aplicações instaladas"""
        reports = []
        
        try:
            for app in applications:
                # Criar definição de componente para verificação
                component_definition = {
                    'name': app.name,
                    'version': app.version,
                    'install_path': app.install_path,
                    'executable_path': app.executable_path,
                    'installation_method': app.metadata.get('installation_method', 'unknown'),
                    'verification_actions': app.metadata.get('verification_actions', [])
                }
                
                # Executar verificação de integridade
                report = self.integrity_checker.check_component_integrity(
                    app.name, component_definition
                )
                
                if report:
                    reports.append(report)
        
        except Exception as e:
            self.logger.error(f"Erro na verificação de integridade: {e}")
        
        return reports
    
    def _check_compatibility(self, applications: List[DetectedApplication]) -> List[ConflictDetection]:
        """Verifica compatibilidade entre aplicações"""
        conflicts = []
        
        try:
            # Criar perfis de componentes
            component_profiles = []
            for app in applications:
                profile = {
                    'name': app.name,
                    'version': app.version,
                    'platform': platform.system(),
                    'architecture': platform.machine(),
                    'install_path': app.install_path,
                    'metadata': app.metadata
                }
                component_profiles.append(profile)
            
            # Detectar conflitos
            conflicts = self.compatibility_matrix.detect_conflicts(component_profiles)
        
        except Exception as e:
            self.logger.error(f"Erro na verificação de compatibilidade: {e}")
        
        return conflicts
    
    def _detect_contamination(self) -> List[ContaminationDetection]:
        """Detecta contaminação do ambiente"""
        try:
            return self.contamination_detector.detect_contamination()
        
        except Exception as e:
            self.logger.error(f"Erro na detecção de contaminação: {e}")
            return []
    
    def _generate_repair_recommendations(self, result: EnhancedDetectionResult) -> List[Dict[str, Any]]:
        """Gera recomendações de reparo baseadas nas análises"""
        recommendations = []
        
        try:
            # Obter recomendações do sistema de auto-reparo
            base_recommendations = self.auto_repair.get_repair_recommendations()
            recommendations.extend(base_recommendations)
            
            # Adicionar recomendações baseadas em conflitos de dependência
            if result.dependency_analysis and 'conflicts' in result.dependency_analysis:
                for conflict in result.dependency_analysis['conflicts']:
                    recommendations.append({
                        'action_id': f"resolve_dependency_conflict_{conflict.get('component1', 'unknown')}",
                        'name': f"Resolver Conflito de Dependência: {conflict.get('component1', 'Unknown')}",
                        'description': f"Conflito detectado: {conflict.get('description', 'Conflito de versão')}",
                        'severity': 'high',
                        'auto_executable': False,
                        'estimated_time': 60
                    })
            
            # Adicionar recomendações baseadas em problemas de integridade
            for integrity_report in result.integrity_reports:
                if integrity_report.overall_status.value != 'healthy':
                    recommendations.append({
                        'action_id': f"fix_integrity_{integrity_report.component_name}",
                        'name': f"Corrigir Integridade: {integrity_report.component_name}",
                        'description': f"Problemas de integridade detectados em {integrity_report.component_name}",
                        'severity': 'medium',
                        'auto_executable': True,
                        'estimated_time': 90
                    })
            
            # Adicionar recomendações baseadas em conflitos de compatibilidade
            for conflict in result.compatibility_conflicts:
                recommendations.append({
                    'action_id': f"resolve_compatibility_conflict_{conflict.conflict_id}",
                    'name': f"Resolver Conflito de Compatibilidade",
                    'description': conflict.description,
                    'severity': conflict.severity.value,
                    'auto_executable': False,
                    'estimated_time': 120
                })
            
            # Adicionar recomendações baseadas em contaminação
            for contamination in result.contamination_detections:
                if contamination.severity.value in ['high', 'critical']:
                    recommendations.append({
                        'action_id': f"clean_contamination_{contamination.signature.name}",
                        'name': f"Limpar Contaminação: {contamination.signature.name}",
                        'description': contamination.signature.description,
                        'severity': contamination.severity.value,
                        'auto_executable': True,
                        'estimated_time': 45
                    })
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar recomendações: {e}")
        
        return recommendations
    
    def _calculate_quality_scores(self, result: EnhancedDetectionResult):
        """Calcula scores de qualidade do ambiente"""
        try:
            # Score de saúde do ambiente (0-100)
            health_factors = []
            
            # Fator: Aplicações detectadas vs esperadas
            if result.base_result.total_detected > 0:
                health_factors.append(min(100, result.base_result.total_detected * 10))
            
            # Fator: Integridade das aplicações
            if result.integrity_reports:
                healthy_apps = sum(1 for report in result.integrity_reports 
                                 if report.overall_status.value == 'healthy')
                integrity_score = (healthy_apps / len(result.integrity_reports)) * 100
                health_factors.append(integrity_score)
            
            # Fator: Conflitos de compatibilidade
            if result.compatibility_conflicts:
                conflict_penalty = min(50, len(result.compatibility_conflicts) * 10)
                health_factors.append(100 - conflict_penalty)
            else:
                health_factors.append(100)
            
            result.environment_health_score = sum(health_factors) / len(health_factors) if health_factors else 0
            
            # Score de segurança (0-100)
            security_factors = []
            
            # Fator: Contaminação detectada
            if result.contamination_detections:
                critical_contaminations = sum(1 for c in result.contamination_detections 
                                            if c.severity.value == 'critical')
                high_contaminations = sum(1 for c in result.contamination_detections 
                                        if c.severity.value == 'high')
                
                security_penalty = (critical_contaminations * 30) + (high_contaminations * 15)
                security_factors.append(max(0, 100 - security_penalty))
            else:
                security_factors.append(100)
            
            result.security_score = sum(security_factors) / len(security_factors) if security_factors else 100
            
            # Score de performance (0-100)
            performance_factors = []
            
            # Fator: Tempo de detecção
            if result.total_analysis_time > 0:
                # Penalizar tempos muito longos
                time_score = max(0, 100 - (result.total_analysis_time * 2))
                performance_factors.append(time_score)
            
            # Fator: Conflitos de dependência
            if result.dependency_analysis and 'conflicts' in result.dependency_analysis:
                conflict_count = len(result.dependency_analysis['conflicts'])
                dependency_score = max(0, 100 - (conflict_count * 15))
                performance_factors.append(dependency_score)
            else:
                performance_factors.append(100)
            
            result.performance_score = sum(performance_factors) / len(performance_factors) if performance_factors else 100
        
        except Exception as e:
            self.logger.error(f"Erro ao calcular scores: {e}")
            result.environment_health_score = 0
            result.security_score = 0
            result.performance_score = 0
    
    def execute_auto_repair(self, result: EnhancedDetectionResult) -> RepairSession:
        """Executa reparo automático baseado nos resultados da análise"""
        try:
            # Verificar se o score de saúde está abaixo do threshold
            if result.environment_health_score < (self.auto_repair_threshold * 100):
                self.logger.info(f"Score de saúde baixo ({result.environment_health_score:.1f}), iniciando auto-reparo")
                return self.auto_repair.auto_repair()
            else:
                self.logger.info(f"Score de saúde adequado ({result.environment_health_score:.1f}), auto-reparo não necessário")
                return None
        
        except Exception as e:
            self.logger.error(f"Erro durante auto-reparo: {e}")
            return None
    
    def generate_comprehensive_report(self, result: EnhancedDetectionResult) -> Dict[str, Any]:
        """Gera relatório abrangente da análise"""
        try:
            # Relatório base
            base_report = self.base_engine.generate_detection_report(result.base_result)
            
            # Relatório aprimorado
            enhanced_report = {
                'base_detection': json.loads(base_report),
                'analysis_summary': {
                    'total_analysis_time': result.total_analysis_time,
                    'environment_health_score': result.environment_health_score,
                    'security_score': result.security_score,
                    'performance_score': result.performance_score
                },
                'dependency_analysis': result.dependency_analysis,
                'integrity_summary': {
                    'total_components_checked': len(result.integrity_reports),
                    'healthy_components': sum(1 for r in result.integrity_reports if r.overall_status.value == 'healthy'),
                    'components_with_issues': sum(1 for r in result.integrity_reports if r.overall_status.value != 'healthy')
                },
                'compatibility_summary': {
                    'total_conflicts': len(result.compatibility_conflicts),
                    'critical_conflicts': sum(1 for c in result.compatibility_conflicts if c.severity.value == 'critical'),
                    'high_conflicts': sum(1 for c in result.compatibility_conflicts if c.severity.value == 'high')
                },
                'contamination_summary': {
                    'total_detections': len(result.contamination_detections),
                    'critical_contaminations': sum(1 for c in result.contamination_detections if c.severity.value == 'critical'),
                    'high_contaminations': sum(1 for c in result.contamination_detections if c.severity.value == 'high')
                },
                'repair_recommendations': {
                    'total_recommendations': len(result.repair_recommendations),
                    'auto_executable': sum(1 for r in result.repair_recommendations if r.get('auto_executable', False)),
                    'manual_required': sum(1 for r in result.repair_recommendations if not r.get('auto_executable', True))
                }
            }
            
            return enhanced_report
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {'error': str(e)}
    
    def load_configuration(self):
        """Carrega configurações do sistema"""
        config_file = self.config_dir / "enhanced_detection.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.enable_dependency_analysis = config.get('enable_dependency_analysis', True)
                self.enable_integrity_checking = config.get('enable_integrity_checking', True)
                self.enable_compatibility_checking = config.get('enable_compatibility_checking', True)
                self.enable_contamination_detection = config.get('enable_contamination_detection', True)
                self.enable_auto_repair = config.get('enable_auto_repair', True)
                self.auto_repair_threshold = config.get('auto_repair_threshold', 0.7)
                
                self.logger.info("Configuração do motor aprimorado carregada")
            
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configuração: {e}")

# Instância global
_enhanced_engine: Optional[EnhancedDetectionEngine] = None

def get_enhanced_detection_engine() -> EnhancedDetectionEngine:
    """Obtém instância global do motor de detecção aprimorado"""
    global _enhanced_engine
    if _enhanced_engine is None:
        _enhanced_engine = EnhancedDetectionEngine()
    return _enhanced_engine