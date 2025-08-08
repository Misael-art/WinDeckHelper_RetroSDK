#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility Matrix - Sistema de Matriz de Compatibilidade para Resolução de Conflitos
Gerencia compatibilidade entre componentes, versões e dependências.
"""

import logging
import json
import re
import yaml
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import packaging.version as pkg_version
import packaging.specifiers as pkg_specifiers

class CompatibilityLevel(Enum):
    """Níveis de compatibilidade"""
    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"

class ConflictType(Enum):
    """Tipos de conflito"""
    VERSION_CONFLICT = "version_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    PLATFORM_CONFLICT = "platform_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    CONFIGURATION_CONFLICT = "configuration_conflict"
    RUNTIME_CONFLICT = "runtime_conflict"
    PATH_CONFLICT = "path_conflict"
    PORT_CONFLICT = "port_conflict"

class ResolutionStrategy(Enum):
    """Estratégias de resolução"""
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    ALTERNATIVE = "alternative"
    EXCLUDE = "exclude"
    ISOLATE = "isolate"
    CONFIGURE = "configure"
    MANUAL = "manual"
    IGNORE = "ignore"

@dataclass
class VersionConstraint:
    """Restrição de versão"""
    specifier: str  # e.g., ">=1.0,<2.0", "~=1.5", "==1.2.3"
    reason: Optional[str] = None
    source: Optional[str] = None
    
    def matches(self, version: str) -> bool:
        """Verifica se uma versão atende à restrição"""
        try:
            spec = pkg_specifiers.SpecifierSet(self.specifier)
            return pkg_version.Version(version) in spec
        except Exception:
            return False

@dataclass
class CompatibilityRule:
    """Regra de compatibilidade"""
    component_a: str
    component_b: str
    version_a: Optional[VersionConstraint] = None
    version_b: Optional[VersionConstraint] = None
    compatibility: CompatibilityLevel = CompatibilityLevel.COMPATIBLE
    platform: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    last_tested: Optional[str] = None

@dataclass
class ConflictDetection:
    """Detecção de conflito"""
    conflict_id: str
    type: ConflictType
    components: List[str]
    description: str
    severity: str  # "low", "medium", "high", "critical"
    affected_functionality: List[str] = field(default_factory=list)
    detection_method: str = "automatic"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConflictResolution:
    """Resolução de conflito"""
    conflict_id: str
    strategy: ResolutionStrategy
    actions: List[Dict[str, Any]] = field(default_factory=list)
    estimated_impact: str = "low"  # "low", "medium", "high"
    success_probability: float = 0.8
    rollback_plan: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class ComponentProfile:
    """Perfil de compatibilidade de um componente"""
    name: str
    version: str
    category: str
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    requires: Dict[str, VersionConstraint] = field(default_factory=dict)
    platform_support: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)

class CompatibilityMatrix:
    """Sistema de matriz de compatibilidade"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger("compatibility_matrix")
        self.config_dir = config_dir or Path.cwd() / "config"
        
        # Dados da matriz
        self.compatibility_rules: List[CompatibilityRule] = []
        self.component_profiles: Dict[str, ComponentProfile] = {}
        self.known_conflicts: Dict[str, ConflictDetection] = {}
        self.resolution_strategies: Dict[str, List[ConflictResolution]] = {}
        
        # Cache de compatibilidade
        self.compatibility_cache: Dict[str, CompatibilityLevel] = {}
        
        # Carregar dados
        self.load_compatibility_data()
    
    def load_compatibility_data(self):
        """Carrega dados de compatibilidade"""
        try:
            # Carregar regras de compatibilidade
            rules_file = self.config_dir / "compatibility_rules.yaml"
            if rules_file.exists():
                self._load_compatibility_rules(rules_file)
            
            # Carregar perfis de componentes
            profiles_file = self.config_dir / "component_profiles.yaml"
            if profiles_file.exists():
                self._load_component_profiles(profiles_file)
            
            # Carregar conflitos conhecidos
            conflicts_file = self.config_dir / "known_conflicts.yaml"
            if conflicts_file.exists():
                self._load_known_conflicts(conflicts_file)
            
            # Carregar estratégias de resolução
            resolutions_file = self.config_dir / "resolution_strategies.yaml"
            if resolutions_file.exists():
                self._load_resolution_strategies(resolutions_file)
            
            self.logger.info(f"Carregados {len(self.compatibility_rules)} regras de compatibilidade")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados de compatibilidade: {e}")
    
    def _load_compatibility_rules(self, file_path: Path):
        """Carrega regras de compatibilidade"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        for rule_data in data.get('compatibility_rules', []):
            rule = CompatibilityRule(
                component_a=rule_data['component_a'],
                component_b=rule_data['component_b'],
                compatibility=CompatibilityLevel(rule_data.get('compatibility', 'compatible')),
                platform=rule_data.get('platform'),
                conditions=rule_data.get('conditions', {}),
                notes=rule_data.get('notes'),
                last_tested=rule_data.get('last_tested')
            )
            
            # Processar restrições de versão
            if 'version_a' in rule_data:
                rule.version_a = VersionConstraint(
                    specifier=rule_data['version_a']['specifier'],
                    reason=rule_data['version_a'].get('reason'),
                    source=rule_data['version_a'].get('source')
                )
            
            if 'version_b' in rule_data:
                rule.version_b = VersionConstraint(
                    specifier=rule_data['version_b']['specifier'],
                    reason=rule_data['version_b'].get('reason'),
                    source=rule_data['version_b'].get('source')
                )
            
            self.compatibility_rules.append(rule)
    
    def _load_component_profiles(self, file_path: Path):
        """Carrega perfis de componentes"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        for profile_data in data.get('component_profiles', []):
            profile = ComponentProfile(
                name=profile_data['name'],
                version=profile_data['version'],
                category=profile_data['category'],
                dependencies=profile_data.get('dependencies', []),
                conflicts_with=profile_data.get('conflicts_with', []),
                provides=profile_data.get('provides', []),
                platform_support=profile_data.get('platform_support', []),
                resource_requirements=profile_data.get('resource_requirements', {}),
                configuration=profile_data.get('configuration', {})
            )
            
            # Processar requisitos
            if 'requires' in profile_data:
                for req_name, req_data in profile_data['requires'].items():
                    if isinstance(req_data, str):
                        profile.requires[req_name] = VersionConstraint(specifier=req_data)
                    else:
                        profile.requires[req_name] = VersionConstraint(
                            specifier=req_data['specifier'],
                            reason=req_data.get('reason'),
                            source=req_data.get('source')
                        )
            
            self.component_profiles[profile.name] = profile
    
    def _load_known_conflicts(self, file_path: Path):
        """Carrega conflitos conhecidos"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        for conflict_data in data.get('known_conflicts', []):
            conflict = ConflictDetection(
                conflict_id=conflict_data['conflict_id'],
                type=ConflictType(conflict_data['type']),
                components=conflict_data['components'],
                description=conflict_data['description'],
                severity=conflict_data['severity'],
                affected_functionality=conflict_data.get('affected_functionality', []),
                detection_method=conflict_data.get('detection_method', 'automatic'),
                metadata=conflict_data.get('metadata', {})
            )
            
            self.known_conflicts[conflict.conflict_id] = conflict
    
    def _load_resolution_strategies(self, file_path: Path):
        """Carrega estratégias de resolução"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        for conflict_id, strategies_data in data.get('resolution_strategies', {}).items():
            strategies = []
            for strategy_data in strategies_data:
                strategy = ConflictResolution(
                    conflict_id=conflict_id,
                    strategy=ResolutionStrategy(strategy_data['strategy']),
                    actions=strategy_data.get('actions', []),
                    estimated_impact=strategy_data.get('estimated_impact', 'low'),
                    success_probability=strategy_data.get('success_probability', 0.8),
                    rollback_plan=strategy_data.get('rollback_plan', []),
                    notes=strategy_data.get('notes')
                )
                strategies.append(strategy)
            
            self.resolution_strategies[conflict_id] = strategies
    
    def check_compatibility(self, component_a: str, version_a: str,
                          component_b: str, version_b: str,
                          platform: Optional[str] = None) -> CompatibilityLevel:
        """Verifica compatibilidade entre dois componentes"""
        
        # Verificar cache
        cache_key = f"{component_a}:{version_a}:{component_b}:{version_b}:{platform}"
        if cache_key in self.compatibility_cache:
            return self.compatibility_cache[cache_key]
        
        # Buscar regra específica
        compatibility = self._find_compatibility_rule(component_a, version_a, component_b, version_b, platform)
        
        # Se não encontrou regra específica, usar heurísticas
        if compatibility == CompatibilityLevel.UNKNOWN:
            compatibility = self._infer_compatibility(component_a, version_a, component_b, version_b, platform)
        
        # Salvar no cache
        self.compatibility_cache[cache_key] = compatibility
        
        return compatibility
    
    def _find_compatibility_rule(self, component_a: str, version_a: str,
                               component_b: str, version_b: str,
                               platform: Optional[str] = None) -> CompatibilityLevel:
        """Busca regra de compatibilidade específica"""
        
        for rule in self.compatibility_rules:
            # Verificar se os componentes correspondem (em qualquer ordem)
            if not ((rule.component_a == component_a and rule.component_b == component_b) or
                   (rule.component_a == component_b and rule.component_b == component_a)):
                continue
            
            # Verificar plataforma
            if rule.platform and platform and rule.platform != platform:
                continue
            
            # Verificar versões
            if rule.component_a == component_a:
                if rule.version_a and not rule.version_a.matches(version_a):
                    continue
                if rule.version_b and not rule.version_b.matches(version_b):
                    continue
            else:  # Ordem invertida
                if rule.version_a and not rule.version_a.matches(version_b):
                    continue
                if rule.version_b and not rule.version_b.matches(version_a):
                    continue
            
            # Verificar condições adicionais
            if rule.conditions and not self._check_conditions(rule.conditions):
                continue
            
            return rule.compatibility
        
        return CompatibilityLevel.UNKNOWN
    
    def _infer_compatibility(self, component_a: str, version_a: str,
                           component_b: str, version_b: str,
                           platform: Optional[str] = None) -> CompatibilityLevel:
        """Infere compatibilidade usando heurísticas"""
        
        # Verificar perfis de componentes
        profile_a = self.component_profiles.get(component_a)
        profile_b = self.component_profiles.get(component_b)
        
        if profile_a and profile_b:
            # Verificar conflitos explícitos
            if component_b in profile_a.conflicts_with or component_a in profile_b.conflicts_with:
                return CompatibilityLevel.INCOMPATIBLE
            
            # Verificar dependências
            if component_b in profile_a.dependencies or component_a in profile_b.dependencies:
                return CompatibilityLevel.COMPATIBLE
            
            # Verificar requisitos de versão
            if component_b in profile_a.requires:
                if not profile_a.requires[component_b].matches(version_b):
                    return CompatibilityLevel.INCOMPATIBLE
            
            if component_a in profile_b.requires:
                if not profile_b.requires[component_a].matches(version_a):
                    return CompatibilityLevel.INCOMPATIBLE
            
            # Verificar suporte de plataforma
            if platform:
                if (profile_a.platform_support and platform not in profile_a.platform_support or
                    profile_b.platform_support and platform not in profile_b.platform_support):
                    return CompatibilityLevel.PLATFORM_CONFLICT
        
        # Heurísticas baseadas em nomes e categorias
        if self._are_similar_components(component_a, component_b):
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        
        # Por padrão, assumir compatibilidade desconhecida
        return CompatibilityLevel.UNKNOWN
    
    def _check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Verifica condições adicionais"""
        # Implementar verificação de condições específicas
        # Por exemplo: versão do OS, arquitetura, etc.
        return True
    
    def _are_similar_components(self, component_a: str, component_b: str) -> bool:
        """Verifica se componentes são similares (podem conflitar)"""
        # Heurísticas simples baseadas em nomes
        similar_patterns = [
            (r'python.*', r'python.*'),
            (r'node.*', r'node.*'),
            (r'java.*', r'java.*'),
            (r'.*compiler.*', r'.*compiler.*'),
            (r'.*editor.*', r'.*editor.*')
        ]
        
        for pattern_a, pattern_b in similar_patterns:
            if (re.match(pattern_a, component_a.lower()) and 
                re.match(pattern_b, component_b.lower())):
                return True
        
        return False
    
    def detect_conflicts(self, installed_components: Dict[str, str],
                        platform: Optional[str] = None) -> List[ConflictDetection]:
        """Detecta conflitos entre componentes instalados"""
        conflicts = []
        
        # Verificar conflitos conhecidos
        for conflict in self.known_conflicts.values():
            if all(comp in installed_components for comp in conflict.components):
                conflicts.append(conflict)
        
        # Verificar conflitos por compatibilidade
        components = list(installed_components.items())
        for i, (comp_a, ver_a) in enumerate(components):
            for comp_b, ver_b in components[i+1:]:
                compatibility = self.check_compatibility(comp_a, ver_a, comp_b, ver_b, platform)
                
                if compatibility == CompatibilityLevel.INCOMPATIBLE:
                    conflict = ConflictDetection(
                        conflict_id=f"incompatible_{comp_a}_{comp_b}",
                        type=ConflictType.VERSION_CONFLICT,
                        components=[comp_a, comp_b],
                        description=f"Incompatibilidade detectada entre {comp_a} {ver_a} e {comp_b} {ver_b}",
                        severity="high",
                        detection_method="matrix_analysis"
                    )
                    conflicts.append(conflict)
        
        # Verificar conflitos de dependências
        dependency_conflicts = self._detect_dependency_conflicts(installed_components)
        conflicts.extend(dependency_conflicts)
        
        # Verificar conflitos de recursos
        resource_conflicts = self._detect_resource_conflicts(installed_components)
        conflicts.extend(resource_conflicts)
        
        return conflicts
    
    def _detect_dependency_conflicts(self, installed_components: Dict[str, str]) -> List[ConflictDetection]:
        """Detecta conflitos de dependências"""
        conflicts = []
        
        for comp_name, comp_version in installed_components.items():
            profile = self.component_profiles.get(comp_name)
            if not profile:
                continue
            
            # Verificar se todas as dependências estão satisfeitas
            for dep_name, constraint in profile.requires.items():
                if dep_name not in installed_components:
                    conflict = ConflictDetection(
                        conflict_id=f"missing_dependency_{comp_name}_{dep_name}",
                        type=ConflictType.DEPENDENCY_CONFLICT,
                        components=[comp_name],
                        description=f"{comp_name} requer {dep_name} {constraint.specifier} mas não está instalado",
                        severity="high",
                        affected_functionality=[comp_name]
                    )
                    conflicts.append(conflict)
                elif not constraint.matches(installed_components[dep_name]):
                    conflict = ConflictDetection(
                        conflict_id=f"version_mismatch_{comp_name}_{dep_name}",
                        type=ConflictType.VERSION_CONFLICT,
                        components=[comp_name, dep_name],
                        description=f"{comp_name} requer {dep_name} {constraint.specifier} mas {installed_components[dep_name]} está instalado",
                        severity="medium",
                        affected_functionality=[comp_name]
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_resource_conflicts(self, installed_components: Dict[str, str]) -> List[ConflictDetection]:
        """Detecta conflitos de recursos"""
        conflicts = []
        
        # Verificar conflitos de porta
        used_ports = {}
        for comp_name, comp_version in installed_components.items():
            profile = self.component_profiles.get(comp_name)
            if profile and 'ports' in profile.resource_requirements:
                for port in profile.resource_requirements['ports']:
                    if port in used_ports:
                        conflict = ConflictDetection(
                            conflict_id=f"port_conflict_{port}",
                            type=ConflictType.PORT_CONFLICT,
                            components=[comp_name, used_ports[port]],
                            description=f"Conflito de porta {port} entre {comp_name} e {used_ports[port]}",
                            severity="medium"
                        )
                        conflicts.append(conflict)
                    else:
                        used_ports[port] = comp_name
        
        # Verificar conflitos de caminho
        used_paths = {}
        for comp_name, comp_version in installed_components.items():
            profile = self.component_profiles.get(comp_name)
            if profile and 'paths' in profile.resource_requirements:
                for path in profile.resource_requirements['paths']:
                    if path in used_paths:
                        conflict = ConflictDetection(
                            conflict_id=f"path_conflict_{path.replace('/', '_')}",
                            type=ConflictType.PATH_CONFLICT,
                            components=[comp_name, used_paths[path]],
                            description=f"Conflito de caminho {path} entre {comp_name} e {used_paths[path]}",
                            severity="low"
                        )
                        conflicts.append(conflict)
                    else:
                        used_paths[path] = comp_name
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[ConflictDetection]) -> List[ConflictResolution]:
        """Resolve conflitos detectados"""
        resolutions = []
        
        for conflict in conflicts:
            # Buscar estratégias conhecidas
            if conflict.conflict_id in self.resolution_strategies:
                resolutions.extend(self.resolution_strategies[conflict.conflict_id])
            else:
                # Gerar estratégias automáticas
                auto_resolutions = self._generate_automatic_resolutions(conflict)
                resolutions.extend(auto_resolutions)
        
        # Ordenar por probabilidade de sucesso
        resolutions.sort(key=lambda r: r.success_probability, reverse=True)
        
        return resolutions
    
    def _generate_automatic_resolutions(self, conflict: ConflictDetection) -> List[ConflictResolution]:
        """Gera resoluções automáticas para conflitos"""
        resolutions = []
        
        if conflict.type == ConflictType.VERSION_CONFLICT:
            # Tentar upgrade/downgrade
            resolutions.append(ConflictResolution(
                conflict_id=conflict.conflict_id,
                strategy=ResolutionStrategy.UPGRADE,
                actions=[
                    {
                        'type': 'upgrade_component',
                        'component': conflict.components[0],
                        'target_version': 'latest'
                    }
                ],
                estimated_impact="medium",
                success_probability=0.7,
                notes="Tentar atualizar componente para versão compatível"
            ))
            
            # Alternativa: usar versão alternativa
            resolutions.append(ConflictResolution(
                conflict_id=conflict.conflict_id,
                strategy=ResolutionStrategy.ALTERNATIVE,
                actions=[
                    {
                        'type': 'find_alternative',
                        'component': conflict.components[1],
                        'criteria': 'compatible_version'
                    }
                ],
                estimated_impact="low",
                success_probability=0.6,
                notes="Buscar versão alternativa compatível"
            ))
        
        elif conflict.type == ConflictType.DEPENDENCY_CONFLICT:
            # Instalar dependência faltante
            resolutions.append(ConflictResolution(
                conflict_id=conflict.conflict_id,
                strategy=ResolutionStrategy.UPGRADE,
                actions=[
                    {
                        'type': 'install_dependency',
                        'dependency': conflict.components[-1] if len(conflict.components) > 1 else 'unknown',
                        'version': 'compatible'
                    }
                ],
                estimated_impact="low",
                success_probability=0.9,
                notes="Instalar dependência faltante"
            ))
        
        elif conflict.type in [ConflictType.PORT_CONFLICT, ConflictType.PATH_CONFLICT]:
            # Reconfigurar componente
            resolutions.append(ConflictResolution(
                conflict_id=conflict.conflict_id,
                strategy=ResolutionStrategy.CONFIGURE,
                actions=[
                    {
                        'type': 'reconfigure_component',
                        'component': conflict.components[0],
                        'parameter': 'port' if conflict.type == ConflictType.PORT_CONFLICT else 'path',
                        'action': 'change_to_available'
                    }
                ],
                estimated_impact="low",
                success_probability=0.8,
                notes="Reconfigurar para evitar conflito de recurso"
            ))
        
        return resolutions
    
    def get_compatibility_matrix(self, components: List[str]) -> Dict[str, Dict[str, CompatibilityLevel]]:
        """Gera matriz de compatibilidade para lista de componentes"""
        matrix = {}
        
        for comp_a in components:
            matrix[comp_a] = {}
            for comp_b in components:
                if comp_a == comp_b:
                    matrix[comp_a][comp_b] = CompatibilityLevel.COMPATIBLE
                else:
                    # Usar versão padrão ou mais recente conhecida
                    version_a = self._get_default_version(comp_a)
                    version_b = self._get_default_version(comp_b)
                    
                    compatibility = self.check_compatibility(comp_a, version_a, comp_b, version_b)
                    matrix[comp_a][comp_b] = compatibility
        
        return matrix
    
    def _get_default_version(self, component: str) -> str:
        """Obtém versão padrão de um componente"""
        profile = self.component_profiles.get(component)
        if profile:
            return profile.version
        return "1.0.0"  # Versão padrão
    
    def add_compatibility_rule(self, rule: CompatibilityRule):
        """Adiciona nova regra de compatibilidade"""
        self.compatibility_rules.append(rule)
        # Limpar cache relacionado
        self._clear_compatibility_cache(rule.component_a, rule.component_b)
    
    def add_component_profile(self, profile: ComponentProfile):
        """Adiciona novo perfil de componente"""
        self.component_profiles[profile.name] = profile
        # Limpar cache relacionado
        self._clear_compatibility_cache(profile.name)
    
    def _clear_compatibility_cache(self, *components):
        """Limpa cache de compatibilidade para componentes específicos"""
        keys_to_remove = []
        for key in self.compatibility_cache.keys():
            if any(comp in key for comp in components):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.compatibility_cache[key]
    
    def export_compatibility_data(self, output_dir: Path):
        """Exporta dados de compatibilidade"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Exportar regras
        rules_data = {
            'compatibility_rules': [
                {
                    'component_a': rule.component_a,
                    'component_b': rule.component_b,
                    'compatibility': rule.compatibility.value,
                    'platform': rule.platform,
                    'conditions': rule.conditions,
                    'notes': rule.notes,
                    'last_tested': rule.last_tested,
                    'version_a': {
                        'specifier': rule.version_a.specifier,
                        'reason': rule.version_a.reason,
                        'source': rule.version_a.source
                    } if rule.version_a else None,
                    'version_b': {
                        'specifier': rule.version_b.specifier,
                        'reason': rule.version_b.reason,
                        'source': rule.version_b.source
                    } if rule.version_b else None
                } for rule in self.compatibility_rules
            ]
        }
        
        with open(output_dir / "compatibility_rules.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(rules_data, f, default_flow_style=False, allow_unicode=True)
        
        # Exportar perfis
        profiles_data = {
            'component_profiles': [
                {
                    'name': profile.name,
                    'version': profile.version,
                    'category': profile.category,
                    'dependencies': profile.dependencies,
                    'conflicts_with': profile.conflicts_with,
                    'provides': profile.provides,
                    'requires': {
                        name: {
                            'specifier': constraint.specifier,
                            'reason': constraint.reason,
                            'source': constraint.source
                        } for name, constraint in profile.requires.items()
                    },
                    'platform_support': profile.platform_support,
                    'resource_requirements': profile.resource_requirements,
                    'configuration': profile.configuration
                } for profile in self.component_profiles.values()
            ]
        }
        
        with open(output_dir / "component_profiles.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(profiles_data, f, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"Dados de compatibilidade exportados para {output_dir}")
    
    def generate_compatibility_report(self, installed_components: Dict[str, str]) -> Dict[str, Any]:
        """Gera relatório de compatibilidade"""
        conflicts = self.detect_conflicts(installed_components)
        resolutions = self.resolve_conflicts(conflicts)
        
        # Estatísticas
        total_components = len(installed_components)
        total_conflicts = len(conflicts)
        critical_conflicts = sum(1 for c in conflicts if c.severity == "critical")
        high_conflicts = sum(1 for c in conflicts if c.severity == "high")
        
        # Matriz de compatibilidade
        matrix = self.get_compatibility_matrix(list(installed_components.keys()))
        
        return {
            'summary': {
                'total_components': total_components,
                'total_conflicts': total_conflicts,
                'critical_conflicts': critical_conflicts,
                'high_conflicts': high_conflicts,
                'compatibility_score': max(0, 100 - (total_conflicts * 10))
            },
            'conflicts': [
                {
                    'id': c.conflict_id,
                    'type': c.type.value,
                    'components': c.components,
                    'description': c.description,
                    'severity': c.severity,
                    'affected_functionality': c.affected_functionality
                } for c in conflicts
            ],
            'resolutions': [
                {
                    'conflict_id': r.conflict_id,
                    'strategy': r.strategy.value,
                    'actions': r.actions,
                    'estimated_impact': r.estimated_impact,
                    'success_probability': r.success_probability,
                    'notes': r.notes
                } for r in resolutions
            ],
            'compatibility_matrix': {
                comp_a: {
                    comp_b: level.value for comp_b, level in row.items()
                } for comp_a, row in matrix.items()
            }
        }

# Instância global
_compatibility_matrix: Optional[CompatibilityMatrix] = None

def get_compatibility_matrix() -> CompatibilityMatrix:
    """Obtém instância global da matriz de compatibilidade"""
    global _compatibility_matrix
    if _compatibility_matrix is None:
        _compatibility_matrix = CompatibilityMatrix()
    return _compatibility_matrix