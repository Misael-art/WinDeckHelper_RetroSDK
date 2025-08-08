#!/usr/bin/env python3
"""
Demonstração do Sistema Integrado env_dev

Este exemplo mostra como usar todos os sistemas implementados:
1. Detecção de dependências transitivas
2. Verificação de integridade pós-instalação
3. Matriz de compatibilidade
4. Detecção de ambiente contaminado
5. Sistema de configuração dinâmica
6. Auto-reparo
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhanced_detection_engine import EnhancedDetectionEngine
from core.dependency_graph_analyzer import DependencyGraphAnalyzer
from core.post_installation_integrity import PostInstallationIntegrityChecker as IntegrityChecker
from core.compatibility_matrix import CompatibilityMatrix
from core.environment_contamination_detector import EnvironmentContaminationDetector
from core.dynamic_configuration_system import DynamicConfigurationSystem
from core.auto_repair_system import AutoRepairSystem

class IntegratedSystemDemo:
    """Demonstração completa do sistema integrado env_dev."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.logger = self._setup_logging()
        
        # Inicializar sistemas
        self.config_system = None
        self.detection_engine = None
        self.dependency_analyzer = None
        self.integrity_checker = None
        self.compatibility_matrix = None
        self.contamination_detector = None
        self.auto_repair = None
        
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging para a demonstração."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/integrated_demo.log')
            ]
        )
        return logging.getLogger(__name__)
    
    async def initialize_systems(self):
        """Inicializar todos os sistemas."""
        self.logger.info("Inicializando sistemas integrados...")
        
        try:
            # 1. Sistema de configuração dinâmica
            self.logger.info("Inicializando sistema de configuração...")
            self.config_system = DynamicConfigurationSystem(
                config_dir=str(self.config_dir)
            )
            # Configurações já carregadas no construtor
            
            # 2. Motor de detecção aprimorado
            self.logger.info("Inicializando motor de detecção...")
            self.detection_engine = EnhancedDetectionEngine(
                config_dir=self.config_dir
            )
            
            # 3. Analisador de dependências
            self.logger.info("Inicializando analisador de dependências...")
            self.dependency_analyzer = DependencyGraphAnalyzer()
            
            # 4. Verificador de integridade
            self.logger.info("Inicializando verificador de integridade...")
            self.integrity_checker = IntegrityChecker()
            
            # 5. Matriz de compatibilidade
            self.logger.info("Inicializando matriz de compatibilidade...")
            self.compatibility_matrix = CompatibilityMatrix(
                config_dir=str(self.config_dir / "compatibility_matrix.yaml")
            )
            self.compatibility_matrix.load_compatibility_data()
            
            # 6. Detector de contaminação
            self.logger.info("Inicializando detector de contaminação...")
            self.contamination_detector = EnvironmentContaminationDetector(
                config_dir=self.config_dir
            )
            self.contamination_detector.load_contamination_signatures()
            
            # 7. Sistema de auto-reparo
            self.logger.info("Inicializando sistema de auto-reparo...")
            self.auto_repair = AutoRepairSystem(
                config_dir=self.config_dir
            )
            
            self.logger.info("Todos os sistemas inicializados com sucesso!")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistemas: {e}")
            raise
    
    async def run_comprehensive_analysis(self) -> Dict:
        """Executar análise completa do ambiente."""
        self.logger.info("Iniciando análise completa do ambiente...")
        
        results = {
            'detection': None,
            'dependencies': None,
            'integrity': None,
            'compatibility': None,
            'contamination': None,
            'recommendations': [],
            'auto_repairs': []
        }
        
        try:
            # 1. Detecção de aplicações
            self.logger.info("Executando detecção de aplicações...")
            detection_result = self.detection_engine.detect_applications_enhanced()
            results['detection'] = detection_result
            
            # 2. Análise de dependências
            self.logger.info("Analisando dependências...")
            if detection_result and detection_result.base_result.applications:
                dependency_analysis = self.dependency_analyzer.analyze_component_dependencies(
                    "detected_applications",
                    {"applications": [app.name for app in detection_result.base_result.applications]}
                )
                results['dependencies'] = dependency_analysis
            
            # 3. Verificação de integridade
            self.logger.info("Verificando integridade...")
            integrity_results = []
            if detection_result and detection_result.base_result.applications:
                for app in detection_result.base_result.applications:
                    if app.install_path:
                         integrity_result = self.integrity_checker.verify_component_integrity(
                             app.name,
                             {"install_path": app.install_path},
                             app.install_path
                         )
                         integrity_results.append({
                             'application': app.name,
                            'result': integrity_result
                        })
            results['integrity'] = integrity_results
            
            # 4. Verificação de compatibilidade
            self.logger.info("Verificando compatibilidade...")
            if detection_result and detection_result.base_result.applications:
                compatibility_report = self.compatibility_matrix.generate_compatibility_report(
                    {app.name: app.version for app in detection_result.base_result.applications}
                )
                results['compatibility'] = compatibility_report
            
            # 5. Detecção de contaminação
            self.logger.info("Detectando contaminação do ambiente...")
            contamination_result = self.contamination_detector.detect_contamination()
            results['contamination'] = contamination_result
            
            # 6. Gerar recomendações
            self.logger.info("Gerando recomendações...")
            recommendations = await self._generate_recommendations(results)
            results['recommendations'] = recommendations
            
            # 7. Executar auto-reparo (se habilitado)
            if self.config_system.get('auto_repair.general_settings.auto_repair_enabled', False):
                self.logger.info("Executando auto-reparo...")
                auto_repair_results = await self._execute_auto_repairs(results)
                results['auto_repairs'] = auto_repair_results
            
            self.logger.info("Análise completa finalizada!")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro durante análise: {e}")
            raise
    
    async def _generate_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Gerar recomendações baseadas nos resultados da análise."""
        recommendations = []
        
        # Recomendações baseadas em problemas de integridade
        if analysis_results.get('integrity'):
            for integrity_result in analysis_results['integrity']:
                if integrity_result['result'].overall_status != 'valid':
                    recommendations.append({
                        'type': 'integrity_issue',
                        'priority': 'high',
                        'application': integrity_result['application'],
                        'description': f"Problemas de integridade detectados em {integrity_result['application']}",
                        'suggested_action': 'reinstall_application'
                    })
        
        # Recomendações baseadas em conflitos de compatibilidade
        if analysis_results.get('compatibility'):
            compatibility_report = analysis_results['compatibility']
            if hasattr(compatibility_report, 'conflicts') and compatibility_report.conflicts:
                for conflict in compatibility_report.conflicts:
                    recommendations.append({
                        'type': 'compatibility_conflict',
                        'priority': 'medium',
                        'description': f"Conflito de compatibilidade: {conflict.description}",
                        'suggested_action': 'resolve_conflict',
                        'conflict_details': conflict
                    })
        
        # Recomendações baseadas em contaminação
        if analysis_results.get('contamination'):
            contamination_result = analysis_results['contamination']
            if hasattr(contamination_result, 'detections') and contamination_result.detections:
                for detection in contamination_result.detections:
                    if detection.severity.value >= 3:  # Medium ou higher
                        recommendations.append({
                            'type': 'contamination_detected',
                            'priority': 'high' if detection.severity.value >= 4 else 'medium',
                            'description': f"Contaminação detectada: {detection.signature.name}",
                            'suggested_action': 'cleanup_contamination',
                            'detection_details': detection
                        })
        
        # Recomendações baseadas em dependências
        if analysis_results.get('dependencies'):
            dependency_analysis = analysis_results['dependencies']
            if hasattr(dependency_analysis, 'missing_dependencies') and dependency_analysis.missing_dependencies:
                recommendations.append({
                    'type': 'missing_dependencies',
                    'priority': 'medium',
                    'description': f"Dependências ausentes detectadas: {len(dependency_analysis.missing_dependencies)}",
                    'suggested_action': 'install_dependencies',
                    'missing_deps': dependency_analysis.missing_dependencies
                })
        
        return recommendations
    
    async def _execute_auto_repairs(self, analysis_results: Dict) -> List[Dict]:
        """Executar reparos automáticos baseados na análise."""
        repair_results = []
        
        try:
            # Executar diagnóstico automático
            diagnosis = await self.auto_repair.diagnose_problems()
            
            if diagnosis.detected_problems:
                self.logger.info(f"Detectados {len(diagnosis.detected_problems)} problemas para reparo")
                
                # Executar reparos automáticos
                for problem in diagnosis.detected_problems:
                    if problem.auto_repairable:
                        self.logger.info(f"Executando reparo automático para: {problem.description}")
                        repair_result = await self.auto_repair.execute_repair(problem.repair_action)
                        repair_results.append({
                            'problem': problem.description,
                            'action': problem.repair_action.name,
                            'result': repair_result
                        })
            
        except Exception as e:
            self.logger.error(f"Erro durante auto-reparo: {e}")
        
        return repair_results
    
    def generate_report(self, analysis_results: Dict) -> str:
        """Gerar relatório detalhado da análise."""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE ANÁLISE DO AMBIENTE DE DESENVOLVIMENTO")
        report.append("=" * 80)
        report.append("")
        
        # Resumo da detecção
        if analysis_results.get('detection'):
            detection = analysis_results['detection']
            report.append(f"APLICAÇÕES DETECTADAS: {len(detection.base_result.applications) if detection.base_result.applications else 0}")
            if detection.base_result.applications:
                for app in detection.base_result.applications:
                    report.append(f"  - {app.name} ({app.version or 'versão desconhecida'})")
            report.append("")
        
        # Resumo de dependências
        if analysis_results.get('dependencies'):
            deps = analysis_results['dependencies']
            report.append("ANÁLISE DE DEPENDÊNCIAS:")
            if hasattr(deps, 'total_dependencies'):
                report.append(f"  - Total de dependências: {deps.total_dependencies}")
            if hasattr(deps, 'missing_dependencies') and deps.missing_dependencies:
                report.append(f"  - Dependências ausentes: {len(deps.missing_dependencies)}")
            report.append("")
        
        # Resumo de integridade
        if analysis_results.get('integrity'):
            integrity_results = analysis_results['integrity']
            valid_count = sum(1 for r in integrity_results if r['result'].overall_status.value == 'valid')
            report.append("VERIFICAÇÃO DE INTEGRIDADE:")
            report.append(f"  - Aplicações válidas: {valid_count}/{len(integrity_results)}")
            report.append("")
        
        # Resumo de compatibilidade
        if analysis_results.get('compatibility'):
            compat = analysis_results['compatibility']
            report.append("ANÁLISE DE COMPATIBILIDADE:")
            if hasattr(compat, 'conflicts') and compat.conflicts:
                report.append(f"  - Conflitos detectados: {len(compat.conflicts)}")
            else:
                report.append("  - Nenhum conflito detectado")
            report.append("")
        
        # Resumo de contaminação
        if analysis_results.get('contamination'):
            contam = analysis_results['contamination']
            report.append("DETECÇÃO DE CONTAMINAÇÃO:")
            if hasattr(contam, 'detections') and contam.detections:
                report.append(f"  - Contaminações detectadas: {len(contam.detections)}")
                high_severity = sum(1 for d in contam.detections if d.severity.value >= 4)
                if high_severity > 0:
                    report.append(f"  - Severidade alta: {high_severity}")
            else:
                report.append("  - Ambiente limpo")
            report.append("")
        
        # Recomendações
        if analysis_results.get('recommendations'):
            recommendations = analysis_results['recommendations']
            report.append("RECOMENDAÇÕES:")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"  {i}. [{rec['priority'].upper()}] {rec['description']}")
            report.append("")
        
        # Auto-reparos executados
        if analysis_results.get('auto_repairs'):
            repairs = analysis_results['auto_repairs']
            report.append("AUTO-REPAROS EXECUTADOS:")
            for repair in repairs:
                status = "SUCESSO" if repair['result'].success else "FALHA"
                report.append(f"  - {repair['action']}: {status}")
            report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    async def cleanup(self):
        """Limpar recursos utilizados."""
        self.logger.info("Limpando recursos...")
        
        if self.contamination_detector:
            self.contamination_detector.stop_continuous_monitoring()
        
        if self.config_system:
            self.config_system.stop_file_monitoring()

async def main():
    """Função principal da demonstração."""
    demo = IntegratedSystemDemo()
    
    try:
        # Inicializar sistemas
        await demo.initialize_systems()
        
        # Executar análise completa
        results = await demo.run_comprehensive_analysis()
        
        # Gerar e exibir relatório
        report = demo.generate_report(results)
        print(report)
        
        # Salvar relatório
        os.makedirs('reports', exist_ok=True)
        with open('reports/integrated_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\nRelatório salvo em: reports/integrated_analysis_report.txt")
        
    except Exception as e:
        print(f"Erro durante execução: {e}")
        raise
    
    finally:
        # Limpar recursos
        await demo.cleanup()

if __name__ == "__main__":
    # Criar diretórios necessários
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Executar demonstração
    asyncio.run(main())