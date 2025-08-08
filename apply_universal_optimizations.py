#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Aplicação das Otimizações Universais

Este script aplica as otimizações de dependências identificadas pelo
sistema universal a todos os componentes do ambiente de desenvolvimento.

Autor: Environment Dev Team
Versão: 1.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Adicionar o diretório core ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from universal_dependency_optimizer import (
    UniversalDependencyOptimizer,
    ComponentOptimization,
    get_universal_dependency_optimizer
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizationApplicator:
    """Classe para aplicar otimizações de forma segura e controlada"""
    
    def __init__(self, dry_run: bool = True):
        self.optimizer = get_universal_dependency_optimizer()
        self.dry_run = dry_run
        self.backup_created = False
        
    def run_optimization_process(self) -> bool:
        """Executa o processo completo de otimização"""
        logger.info("🚀 Iniciando Processo de Otimização Universal")
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("🔍 MODO DE SIMULAÇÃO - Nenhuma alteração será feita")
        else:
            logger.info("⚠️  MODO DE APLICAÇÃO - Alterações serão aplicadas")
        
        logger.info("="*60)
        
        try:
            # Passo 1: Análise inicial
            logger.info("\n📊 Passo 1: Análise do ambiente atual")
            analysis = self._analyze_current_environment()
            
            # Passo 2: Identificar otimizações
            logger.info("\n🔍 Passo 2: Identificando otimizações possíveis")
            optimizations = self.optimizer.optimize_all_components()
            
            if not optimizations:
                logger.info("✅ Sistema já está otimizado - nenhuma ação necessária")
                return True
            
            # Passo 3: Análise de impacto
            logger.info("\n📈 Passo 3: Análise de impacto das otimizações")
            impact_analysis = self._analyze_optimization_impact(optimizations)
            
            # Passo 4: Confirmação (se não for dry run)
            if not self.dry_run:
                logger.info("\n❓ Passo 4: Confirmação das alterações")
                if not self._confirm_optimizations(impact_analysis):
                    logger.info("❌ Operação cancelada pelo usuário")
                    return False
            
            # Passo 5: Backup (se não for dry run)
            if not self.dry_run:
                logger.info("\n💾 Passo 5: Criando backup")
                self._create_comprehensive_backup()
            
            # Passo 6: Aplicar otimizações
            logger.info("\n🔧 Passo 6: Aplicando otimizações")
            if self.dry_run:
                self._simulate_optimizations(optimizations)
            else:
                success = self.optimizer.apply_optimizations_to_files(optimizations, backup=False)
                if not success:
                    logger.error("❌ Falha na aplicação das otimizações")
                    return False
            
            # Passo 7: Relatório final
            logger.info("\n📄 Passo 7: Gerando relatório final")
            self._generate_final_report(optimizations, analysis, impact_analysis)
            
            logger.info("\n🎉 Processo de otimização concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"💥 Erro durante o processo de otimização: {e}")
            return False
    
    def _analyze_current_environment(self) -> Dict[str, Any]:
        """Analisa o ambiente atual"""
        files = self.optimizer._discover_component_files()
        total_components = 0
        components_by_category = {}
        
        for file_path in files:
            components = self.optimizer._load_components_from_file(file_path)
            total_components += len(components)
            
            for name, data in components.items():
                category = data.get('category', 'Unknown')
                if category not in components_by_category:
                    components_by_category[category] = 0
                components_by_category[category] += 1
        
        analysis = {
            'total_files': len(files),
            'total_components': total_components,
            'components_by_category': components_by_category,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📁 Arquivos de configuração: {analysis['total_files']}")
        logger.info(f"📦 Total de componentes: {analysis['total_components']}")
        logger.info("📊 Componentes por categoria:")
        for category, count in components_by_category.items():
            logger.info(f"  - {category}: {count}")
        
        return analysis
    
    def _analyze_optimization_impact(self, optimizations: Dict[str, ComponentOptimization]) -> Dict[str, Any]:
        """Analisa o impacto das otimizações"""
        total_savings = {
            'size_mb': sum(opt.estimated_savings['size_mb'] for opt in optimizations.values()),
            'time_seconds': sum(opt.estimated_savings['time_seconds'] for opt in optimizations.values()),
            'dependencies_skipped': sum(opt.estimated_savings['dependencies_skipped'] for opt in optimizations.values())
        }
        
        # Categorizar otimizações por tipo
        optimization_types = {
            'editor_optimizations': [],
            'runtime_optimizations': [],
            'tool_optimizations': [],
            'library_optimizations': []
        }
        
        for name, opt in optimizations.items():
            for dep in opt.skipped_dependencies:
                if 'Visual Studio Code' in dep or 'Cursor' in dep or 'IDE' in dep:
                    optimization_types['editor_optimizations'].append((name, dep))
                elif 'Java' in dep or 'Python' in dep or 'Node.js' in dep:
                    optimization_types['runtime_optimizations'].append((name, dep))
                elif 'Git' in dep or 'Make' in dep or '7-Zip' in dep:
                    optimization_types['tool_optimizations'].append((name, dep))
                else:
                    optimization_types['library_optimizations'].append((name, dep))
        
        impact = {
            'total_optimizations': len(optimizations),
            'total_savings': total_savings,
            'optimization_types': optimization_types,
            'high_impact_optimizations': [
                name for name, opt in optimizations.items() 
                if opt.estimated_savings['size_mb'] > 100
            ]
        }
        
        logger.info(f"🎯 Otimizações identificadas: {impact['total_optimizations']}")
        logger.info(f"💾 Economia total estimada: {total_savings['size_mb']} MB")
        logger.info(f"⏱️  Tempo total economizado: {total_savings['time_seconds']//60} minutos")
        logger.info(f"⏭️  Dependências evitadas: {total_savings['dependencies_skipped']}")
        
        if impact['high_impact_optimizations']:
            logger.info("🏆 Otimizações de alto impacto:")
            for name in impact['high_impact_optimizations']:
                savings = optimizations[name].estimated_savings
                logger.info(f"  - {name}: {savings['size_mb']} MB")
        
        return impact
    
    def _confirm_optimizations(self, impact_analysis: Dict[str, Any]) -> bool:
        """Solicita confirmação do usuário para aplicar otimizações"""
        total_savings = impact_analysis['total_savings']
        
        print("\n" + "="*60)
        print("⚠️  CONFIRMAÇÃO DE OTIMIZAÇÕES")
        print("="*60)
        print(f"📊 Otimizações a serem aplicadas: {impact_analysis['total_optimizations']}")
        print(f"💾 Economia estimada: {total_savings['size_mb']} MB")
        print(f"⏱️  Tempo economizado: {total_savings['time_seconds']//60} minutos")
        print(f"⏭️  Dependências evitadas: {total_savings['dependencies_skipped']}")
        
        if impact_analysis['high_impact_optimizations']:
            print("\n🏆 Otimizações de alto impacto:")
            for name in impact_analysis['high_impact_optimizations']:
                print(f"  - {name}")
        
        print("\n⚠️  ATENÇÃO: Esta operação modificará os arquivos de configuração.")
        print("📋 Um backup será criado automaticamente.")
        
        while True:
            response = input("\n❓ Deseja continuar? (s/N): ").strip().lower()
            if response in ['s', 'sim', 'y', 'yes']:
                return True
            elif response in ['n', 'não', 'nao', 'no', '']:
                return False
            else:
                print("❌ Resposta inválida. Digite 's' para sim ou 'n' para não.")
    
    def _create_comprehensive_backup(self) -> None:
        """Cria backup completo do sistema"""
        import shutil
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(f"backups/universal_optimization_{timestamp}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup dos arquivos de configuração
        config_dir = Path("config")
        if config_dir.exists():
            shutil.copytree(config_dir, backup_dir / "config", dirs_exist_ok=True)
        
        # Backup dos scripts principais
        important_files = [
            "core/installer.py",
            "core/retro_devkit_manager.py",
            "core/intelligent_dependency_manager.py",
            "core/universal_dependency_optimizer.py"
        ]
        
        scripts_backup = backup_dir / "scripts"
        scripts_backup.mkdir(exist_ok=True)
        
        for file_path in important_files:
            if Path(file_path).exists():
                shutil.copy2(file_path, scripts_backup / Path(file_path).name)
        
        # Criar arquivo de informações do backup
        backup_info = {
            'timestamp': timestamp,
            'backup_reason': 'Universal dependency optimization',
            'files_backed_up': len(list(backup_dir.rglob('*'))),
            'original_config_path': str(config_dir.absolute())
        }
        
        with open(backup_dir / "backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Backup completo criado em: {backup_dir}")
        self.backup_created = True
    
    def _simulate_optimizations(self, optimizations: Dict[str, ComponentOptimization]) -> None:
        """Simula a aplicação das otimizações"""
        logger.info("🎭 SIMULAÇÃO - As seguintes alterações seriam feitas:")
        
        for name, opt in optimizations.items():
            if opt.skipped_dependencies:
                logger.info(f"\n📝 {name}:")
                logger.info(f"  ➖ Dependências removidas: {', '.join(opt.skipped_dependencies)}")
                
                if opt.conditional_dependencies:
                    logger.info(f"  🔀 Dependências condicionais adicionadas: {len(opt.conditional_dependencies)}")
                
                savings = opt.estimated_savings
                logger.info(f"  💾 Economia: {savings['size_mb']} MB, {savings['time_seconds']//60} min")
    
    def _generate_final_report(self, optimizations: Dict[str, ComponentOptimization], 
                             analysis: Dict[str, Any], impact_analysis: Dict[str, Any]) -> None:
        """Gera relatório final completo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"optimization_final_report_{timestamp}.json"
        
        # Gerar relatório do otimizador
        optimization_report = self.optimizer.generate_optimization_report(optimizations)
        
        # Combinar com análises adicionais
        final_report = {
            'process_info': {
                'timestamp': datetime.now().isoformat(),
                'dry_run': self.dry_run,
                'backup_created': self.backup_created
            },
            'environment_analysis': analysis,
            'impact_analysis': impact_analysis,
            'optimization_details': optimization_report,
            'recommendations': self._generate_recommendations(optimizations, impact_analysis)
        }
        
        # Salvar relatório
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Relatório final salvo: {report_path}")
        
        # Mostrar resumo
        self._show_final_summary(final_report)
    
    def _generate_recommendations(self, optimizations: Dict[str, ComponentOptimization], 
                                impact_analysis: Dict[str, Any]) -> List[str]:
        """Gera recomendações baseadas nas otimizações"""
        recommendations = []
        
        total_savings = impact_analysis['total_savings']
        
        if total_savings['size_mb'] > 500:
            recommendations.append(
                "💾 Grande economia de espaço identificada. Considere aplicar as otimizações para liberar espaço significativo."
            )
        
        if total_savings['time_seconds'] > 600:  # 10 minutos
            recommendations.append(
                "⏱️  Economia significativa de tempo de instalação. As otimizações reduzirão substancialmente o tempo de setup."
            )
        
        editor_optimizations = impact_analysis['optimization_types']['editor_optimizations']
        if len(editor_optimizations) > 3:
            recommendations.append(
                "🖥️  Múltiplas otimizações de editores detectadas. O sistema instalará apenas editores necessários baseado no ambiente."
            )
        
        if impact_analysis['high_impact_optimizations']:
            recommendations.append(
                f"🎯 {len(impact_analysis['high_impact_optimizations'])} otimizações de alto impacto identificadas. Priorize a aplicação destas."
            )
        
        recommendations.append(
            "🔄 Execute este processo periodicamente para manter o sistema otimizado conforme novos componentes são adicionados."
        )
        
        return recommendations
    
    def _show_final_summary(self, final_report: Dict[str, Any]) -> None:
        """Mostra resumo final"""
        logger.info("\n" + "="*60)
        logger.info("📊 RESUMO FINAL DO PROCESSO")
        logger.info("="*60)
        
        process_info = final_report['process_info']
        impact = final_report['impact_analysis']
        total_savings = impact['total_savings']
        
        logger.info(f"🕐 Processo executado em: {process_info['timestamp']}")
        logger.info(f"🎭 Modo: {'Simulação' if process_info['dry_run'] else 'Aplicação'}")
        
        if process_info['backup_created']:
            logger.info("💾 Backup criado com sucesso")
        
        logger.info(f"\n📈 RESULTADOS:")
        logger.info(f"  🎯 Otimizações aplicadas: {impact['total_optimizations']}")
        logger.info(f"  💾 Espaço economizado: {total_savings['size_mb']} MB")
        logger.info(f"  ⏱️  Tempo economizado: {total_savings['time_seconds']//60} minutos")
        logger.info(f"  ⏭️  Dependências evitadas: {total_savings['dependencies_skipped']}")
        
        recommendations = final_report['recommendations']
        if recommendations:
            logger.info("\n💡 RECOMENDAÇÕES:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec}")
        
        logger.info("="*60)

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Aplica otimizações universais de dependências",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python apply_universal_optimizations.py --dry-run    # Simular otimizações
  python apply_universal_optimizations.py --apply     # Aplicar otimizações
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', 
                      help='Simular otimizações sem aplicar alterações')
    group.add_argument('--apply', action='store_true', 
                      help='Aplicar otimizações aos arquivos')
    
    args = parser.parse_args()
    
    print("🔧 Sistema de Otimização Universal de Dependências")
    print("="*60)
    
    applicator = OptimizationApplicator(dry_run=args.dry_run)
    success = applicator.run_optimization_process()
    
    if success:
        if args.dry_run:
            print("\n✅ Simulação concluída com sucesso!")
            print("💡 Use --apply para aplicar as otimizações")
        else:
            print("\n🎉 Otimizações aplicadas com sucesso!")
    else:
        print("\n❌ Processo falhou. Verifique os logs acima.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)