#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Otimizador Universal de Dependências

Este módulo integra o sistema inteligente de gestão de dependências
com todos os componentes existentes, aplicando otimizações automáticas
baseadas no ambiente do usuário.

Autor: Environment Dev Team
Versão: 1.0.0
"""

import os
import sys
import logging
import yaml
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import copy

# Importar o gerenciador inteligente
from intelligent_dependency_manager import (
    IntelligentDependencyManager, 
    InstallationPlan, 
    DependencyStatus,
    get_intelligent_dependency_manager
)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComponentOptimization:
    """Resultado da otimização de um componente"""
    component_name: str
    original_dependencies: List[str]
    optimized_dependencies: List[str]
    skipped_dependencies: List[str]
    conditional_dependencies: Dict[str, Any]
    optimization_report: Dict[str, Any]
    estimated_savings: Dict[str, int]  # tempo e espaço economizados

class UniversalDependencyOptimizer:
    """Otimizador universal que aplica gestão inteligente a todos os componentes"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/components"
        self.dependency_manager = get_intelligent_dependency_manager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.optimization_cache = {}
        
        # Padrões de otimização por categoria
        self.optimization_patterns = {
            "Retro Development": {
                "common_dependencies": ["Microsoft Visual C++ Redistributable"],
                "editor_dependencies": ["Visual Studio Code"],
                "conditional_rules": {
                    "editors": {
                        "condition": "no_compatible_editor_detected",
                        "alternatives": ["Visual Studio Code", "Cursor IDE", "TRAE AI IDE"]
                    }
                }
            },
            "Development Environment": {
                "common_dependencies": ["Node.js", "Python", "Git"],
                "editor_dependencies": ["Visual Studio Code", "Cursor IDE", "Visual Studio Code Insiders"],
                "conditional_rules": {
                    "editors": {
                        "condition": "no_compatible_editor_detected",
                        "alternatives": ["Visual Studio Code", "Cursor IDE", "TRAE AI IDE", "Visual Studio Code Insiders"]
                    }
                }
            },
            "Multimedia": {
                "common_dependencies": ["Microsoft Visual C++ Redistributable"],
                "conditional_rules": {}
            },
            "Productivity": {
                "common_dependencies": [],
                "conditional_rules": {}
            },
            "Utilities": {
                "common_dependencies": [],
                "conditional_rules": {}
            }
        }
    
    def optimize_all_components(self) -> Dict[str, ComponentOptimization]:
        """Otimiza todos os componentes encontrados"""
        self.logger.info("🚀 Iniciando otimização universal de dependências...")
        
        optimizations = {}
        component_files = self._discover_component_files()
        
        for file_path in component_files:
            self.logger.info(f"📁 Processando arquivo: {file_path}")
            components = self._load_components_from_file(file_path)
            
            for component_name, component_data in components.items():
                if self._should_optimize_component(component_name, component_data):
                    optimization = self._optimize_component(component_name, component_data)
                    if optimization:
                        optimizations[component_name] = optimization
        
        self._generate_optimization_summary(optimizations)
        return optimizations
    
    def optimize_component(self, component_name: str, component_data: Dict[str, Any]) -> Optional[ComponentOptimization]:
        """Otimiza um componente específico"""
        return self._optimize_component(component_name, component_data)
    
    def _discover_component_files(self) -> List[str]:
        """Descobre todos os arquivos de componentes"""
        config_dir = Path(self.config_path)
        if not config_dir.exists():
            self.logger.warning(f"Diretório de configuração não encontrado: {config_dir}")
            return []
        
        yaml_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
        return [str(f) for f in yaml_files]
    
    def _load_components_from_file(self, file_path: str) -> Dict[str, Any]:
        """Carrega componentes de um arquivo YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data
        except Exception as e:
            self.logger.error(f"Erro ao carregar {file_path}: {e}")
            return {}
    
    def _should_optimize_component(self, component_name: str, component_data: Dict[str, Any]) -> bool:
        """Determina se um componente deve ser otimizado"""
        # Pular componentes que já têm otimização inteligente
        custom_installer = component_data.get('custom_installer', '')
        if 'intelligent' in custom_installer.lower():
            self.logger.info(f"⏭️  Pulando {component_name} - já tem instalador inteligente")
            return False
        
        # Verificar se tem dependências para otimizar
        dependencies = component_data.get('dependencies', [])
        if not dependencies:
            return False
        
        return True
    
    def _optimize_component(self, component_name: str, component_data: Dict[str, Any]) -> Optional[ComponentOptimization]:
        """Otimiza um componente específico"""
        self.logger.info(f"🔧 Otimizando componente: {component_name}")
        
        original_dependencies = component_data.get('dependencies', [])
        if not original_dependencies:
            return None
        
        # Detectar categoria do componente
        category = component_data.get('category', 'Unknown')
        optimization_pattern = self.optimization_patterns.get(category, {})
        
        # Criar plano de instalação inteligente
        conditional_dependencies = self._create_conditional_dependencies(
            original_dependencies, 
            optimization_pattern
        )
        
        plan = self.dependency_manager.create_installation_plan(
            component_name,
            original_dependencies,
            conditional_dependencies
        )
        
        # Calcular otimizações
        optimized_dependencies = plan.dependencies_to_install
        skipped_dependencies = plan.dependencies_to_skip
        
        # Calcular economia estimada
        estimated_savings = self._calculate_savings(original_dependencies, skipped_dependencies)
        
        # Gerar relatório
        optimization_report = self.dependency_manager.generate_report(plan)
        
        optimization = ComponentOptimization(
            component_name=component_name,
            original_dependencies=original_dependencies,
            optimized_dependencies=optimized_dependencies,
            skipped_dependencies=skipped_dependencies,
            conditional_dependencies=conditional_dependencies,
            optimization_report=optimization_report,
            estimated_savings=estimated_savings
        )
        
        self._log_component_optimization(optimization)
        return optimization
    
    def _create_conditional_dependencies(self, dependencies: List[str], 
                                       optimization_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Cria dependências condicionais baseadas no padrão de otimização"""
        conditional_deps = {}
        
        editor_dependencies = optimization_pattern.get('editor_dependencies', [])
        conditional_rules = optimization_pattern.get('conditional_rules', {})
        
        # Identificar dependências de editores
        editor_deps_found = [dep for dep in dependencies if dep in editor_dependencies]
        
        if editor_deps_found and 'editors' in conditional_rules:
            conditional_deps['editors'] = {
                'condition': conditional_rules['editors']['condition'],
                'dependencies': editor_deps_found,
                'reason': f"Editor será instalado apenas se nenhum compatível for detectado"
            }
        
        return conditional_deps
    
    def _calculate_savings(self, original_deps: List[str], skipped_deps: List[str]) -> Dict[str, int]:
        """Calcula economia estimada"""
        # Estimativas baseadas em tamanhos típicos de dependências
        dependency_sizes = {
            "Visual Studio Code": 200,  # MB
            "Java Runtime Environment": 150,
            "Node.js": 100,
            "Git": 50,
            "Python": 100,
            "Microsoft Visual C++ Redistributable": 30
        }
        
        dependency_times = {
            "Visual Studio Code": 300,  # segundos
            "Java Runtime Environment": 180,
            "Node.js": 120,
            "Git": 60,
            "Python": 180,
            "Microsoft Visual C++ Redistributable": 60
        }
        
        saved_size = sum(dependency_sizes.get(dep, 50) for dep in skipped_deps)
        saved_time = sum(dependency_times.get(dep, 60) for dep in skipped_deps)
        
        return {
            'size_mb': saved_size,
            'time_seconds': saved_time,
            'dependencies_skipped': len(skipped_deps)
        }
    
    def _log_component_optimization(self, optimization: ComponentOptimization) -> None:
        """Registra a otimização de um componente"""
        self.logger.info(f"✅ Otimização concluída para {optimization.component_name}:")
        
        if optimization.skipped_dependencies:
            self.logger.info(f"  ⏭️  Dependências puladas: {', '.join(optimization.skipped_dependencies)}")
        
        savings = optimization.estimated_savings
        if savings['dependencies_skipped'] > 0:
            self.logger.info(f"  💾 Economia estimada: {savings['size_mb']} MB, {savings['time_seconds']//60} min")
        
        if optimization.conditional_dependencies:
            self.logger.info(f"  🔀 Dependências condicionais configuradas: {len(optimization.conditional_dependencies)}")
    
    def _generate_optimization_summary(self, optimizations: Dict[str, ComponentOptimization]) -> None:
        """Gera resumo geral das otimizações"""
        if not optimizations:
            self.logger.info("ℹ️  Nenhuma otimização aplicada")
            return
        
        total_components = len(optimizations)
        total_deps_skipped = sum(len(opt.skipped_dependencies) for opt in optimizations.values())
        total_size_saved = sum(opt.estimated_savings['size_mb'] for opt in optimizations.values())
        total_time_saved = sum(opt.estimated_savings['time_seconds'] for opt in optimizations.values())
        
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 RESUMO GERAL DAS OTIMIZAÇÕES")
        self.logger.info("="*60)
        self.logger.info(f"🎯 Componentes otimizados: {total_components}")
        self.logger.info(f"⏭️  Total de dependências puladas: {total_deps_skipped}")
        self.logger.info(f"💾 Espaço total economizado: {total_size_saved} MB")
        self.logger.info(f"⏱️  Tempo total economizado: {total_time_saved//60} minutos")
        
        # Mostrar componentes com maior economia
        sorted_optimizations = sorted(
            optimizations.values(),
            key=lambda x: x.estimated_savings['size_mb'],
            reverse=True
        )
        
        self.logger.info("\n🏆 TOP 5 OTIMIZAÇÕES (por economia de espaço):")
        for i, opt in enumerate(sorted_optimizations[:5], 1):
            savings = opt.estimated_savings
            self.logger.info(
                f"  {i}. {opt.component_name}: {savings['size_mb']} MB, "
                f"{savings['time_seconds']//60} min ({savings['dependencies_skipped']} deps)"
            )
        
        self.logger.info("="*60)
    
    def apply_optimizations_to_files(self, optimizations: Dict[str, ComponentOptimization], 
                                   backup: bool = True) -> bool:
        """Aplica as otimizações aos arquivos de configuração"""
        self.logger.info("📝 Aplicando otimizações aos arquivos de configuração...")
        
        if backup:
            self._create_backup()
        
        # Agrupar otimizações por arquivo
        file_optimizations = self._group_optimizations_by_file(optimizations)
        
        success = True
        for file_path, component_optimizations in file_optimizations.items():
            if not self._apply_optimizations_to_file(file_path, component_optimizations):
                success = False
        
        if success:
            self.logger.info("✅ Todas as otimizações foram aplicadas com sucesso")
        else:
            self.logger.error("❌ Algumas otimizações falharam")
        
        return success
    
    def _create_backup(self) -> None:
        """Cria backup dos arquivos de configuração"""
        import shutil
        from datetime import datetime
        
        backup_dir = Path(f"backups/optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        config_dir = Path(self.config_path)
        if config_dir.exists():
            shutil.copytree(config_dir, backup_dir / "components", dirs_exist_ok=True)
            self.logger.info(f"📋 Backup criado em: {backup_dir}")
    
    def _group_optimizations_by_file(self, optimizations: Dict[str, ComponentOptimization]) -> Dict[str, List[ComponentOptimization]]:
        """Agrupa otimizações por arquivo de origem"""
        # Para simplificar, assumimos que cada categoria tem seu próprio arquivo
        file_groups = {}
        
        for opt in optimizations.values():
            # Determinar arquivo baseado no nome do componente
            # Esta lógica pode ser refinada baseada na estrutura real
            if "SGDK" in opt.component_name or "GBDK" in opt.component_name or "Development Kit" in opt.component_name:
                file_key = "retro_devkits.yaml"
            elif "MCP" in opt.component_name:
                file_key = "mcps.yaml"
            else:
                file_key = "misc.yaml"
            
            if file_key not in file_groups:
                file_groups[file_key] = []
            file_groups[file_key].append(opt)
        
        return file_groups
    
    def _apply_optimizations_to_file(self, file_name: str, optimizations: List[ComponentOptimization]) -> bool:
        """Aplica otimizações a um arquivo específico"""
        file_path = Path(self.config_path) / file_name
        
        if not file_path.exists():
            self.logger.warning(f"Arquivo não encontrado: {file_path}")
            return False
        
        try:
            # Carregar arquivo atual
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Aplicar otimizações
            for opt in optimizations:
                if opt.component_name in data:
                    self._update_component_config(data[opt.component_name], opt)
            
            # Salvar arquivo atualizado
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            self.logger.info(f"✅ Arquivo atualizado: {file_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar {file_name}: {e}")
            return False
    
    def _update_component_config(self, component_config: Dict[str, Any], optimization: ComponentOptimization) -> None:
        """Atualiza a configuração de um componente com as otimizações"""
        # Atualizar dependências
        if optimization.optimized_dependencies != optimization.original_dependencies:
            component_config['dependencies'] = optimization.optimized_dependencies
        
        # Adicionar dependências condicionais se houver
        if optimization.conditional_dependencies:
            component_config['conditional_dependencies'] = optimization.conditional_dependencies
        
        # Adicionar comentário sobre otimização
        if optimization.skipped_dependencies:
            note = f"Otimizado automaticamente - dependências condicionais: {', '.join(optimization.skipped_dependencies)}"
            component_config['optimization_note'] = note
    
    def generate_optimization_report(self, optimizations: Dict[str, ComponentOptimization]) -> Dict[str, Any]:
        """Gera relatório completo das otimizações"""
        from datetime import datetime
        
        total_savings = {
            'size_mb': sum(opt.estimated_savings['size_mb'] for opt in optimizations.values()),
            'time_seconds': sum(opt.estimated_savings['time_seconds'] for opt in optimizations.values()),
            'dependencies_skipped': sum(opt.estimated_savings['dependencies_skipped'] for opt in optimizations.values())
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_components_optimized': len(optimizations),
                'total_savings': total_savings
            },
            'optimizations': {
                name: {
                    'original_dependencies': opt.original_dependencies,
                    'optimized_dependencies': opt.optimized_dependencies,
                    'skipped_dependencies': opt.skipped_dependencies,
                    'estimated_savings': opt.estimated_savings
                }
                for name, opt in optimizations.items()
            }
        }

def get_universal_dependency_optimizer(config_path: str = None) -> UniversalDependencyOptimizer:
    """Factory function para obter uma instância do otimizador"""
    return UniversalDependencyOptimizer(config_path)

if __name__ == "__main__":
    # Exemplo de uso
    optimizer = get_universal_dependency_optimizer()
    
    print("🚀 Iniciando otimização universal...")
    optimizations = optimizer.optimize_all_components()
    
    if optimizations:
        print("\n📊 Gerando relatório...")
        report = optimizer.generate_optimization_report(optimizations)
        
        # Salvar relatório
        report_path = "optimization_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {report_path}")
        
        # Perguntar se deve aplicar as otimizações
        response = input("\n❓ Aplicar otimizações aos arquivos? (s/N): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            optimizer.apply_optimizations_to_files(optimizations)
    else:
        print("ℹ️  Nenhuma otimização necessária")