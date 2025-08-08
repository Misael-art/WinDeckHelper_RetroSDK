#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Sugestões Inteligentes

Este módulo implementa um sistema avançado de sugestões que analisa
aplicações detectadas e recomenda componentes relevantes baseado em:
- Padrões de uso
- Dependências
- Categorias de desenvolvimento
- Histórico de instalações
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
from pathlib import Path

from .component_matcher import ComponentMatcher, ComponentMatch
from .component_metadata_manager import ComponentMetadataManager
from .detection_engine import DetectedApplication


@dataclass
class SuggestionRule:
    """Regra de sugestão baseada em padrões."""
    name: str
    description: str
    trigger_components: List[str]  # Componentes que ativam a regra
    suggested_components: List[str]  # Componentes sugeridos
    confidence_boost: float = 0.1  # Boost de confiança
    category_filter: Optional[str] = None  # Filtro por categoria
    priority: int = 1  # Prioridade da regra
    active: bool = True


@dataclass
class SuggestionContext:
    """Contexto para geração de sugestões."""
    detected_apps: List[DetectedApplication]
    installed_components: Set[str]
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    development_focus: Optional[str] = None  # web, mobile, game, data_science, etc.
    experience_level: str = "intermediate"  # beginner, intermediate, advanced
    exclude_categories: Set[str] = field(default_factory=set)


@dataclass
class EnhancedSuggestion:
    """Sugestão aprimorada com contexto e reasoning."""
    component_name: str
    confidence: float
    reasoning: List[str]  # Lista de razões para a sugestão
    category: str
    priority: int
    dependencies: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    estimated_size: Optional[str] = None
    installation_complexity: str = "medium"  # easy, medium, hard
    tags: List[str] = field(default_factory=list)


class IntelligentSuggestionEngine:
    """Motor de sugestões inteligentes."""
    
    def __init__(self, 
                 component_matcher: ComponentMatcher,
                 metadata_manager: ComponentMetadataManager,
                 logger: Optional[logging.Logger] = None):
        self.component_matcher = component_matcher
        self.metadata_manager = metadata_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # Regras de sugestão
        self.suggestion_rules = self._initialize_suggestion_rules()
        
        # Histórico de sugestões (para aprendizado)
        self.suggestion_history: List[Dict[str, Any]] = []
        
        # Padrões de desenvolvimento comuns
        self.development_patterns = self._initialize_development_patterns()
    
    def _initialize_suggestion_rules(self) -> List[SuggestionRule]:
        """Inicializa regras de sugestão baseadas em padrões conhecidos."""
        rules = [
            # Desenvolvimento Web
            SuggestionRule(
                name="web_development_stack",
                description="Stack completo para desenvolvimento web",
                trigger_components=["nodejs", "vscode"],
                suggested_components=["git", "chrome", "postman", "docker"],
                confidence_boost=0.2,
                priority=10
            ),
            
            SuggestionRule(
                name="frontend_development",
                description="Ferramentas para desenvolvimento frontend",
                trigger_components=["nodejs", "npm"],
                suggested_components=["vscode", "chrome", "firefox", "git"],
                confidence_boost=0.15,
                priority=8
            ),
            
            # Desenvolvimento Python
            SuggestionRule(
                name="python_development",
                description="Ambiente Python completo",
                trigger_components=["python"],
                suggested_components=["vscode", "git", "pip", "jupyter"],
                confidence_boost=0.2,
                priority=9
            ),
            
            # Desenvolvimento Java
            SuggestionRule(
                name="java_development",
                description="Ambiente Java completo",
                trigger_components=["java", "jdk"],
                suggested_components=["maven", "gradle", "intellij", "git"],
                confidence_boost=0.2,
                priority=9
            ),
            
            # Gaming/Emulação
            SuggestionRule(
                name="retro_gaming_setup",
                description="Setup completo para jogos retrô",
                trigger_components=["retroarch"],
                suggested_components=["mednafen", "mame", "dolphin", "pcsx2"],
                confidence_boost=0.25,
                category_filter="emulator",
                priority=7
            ),
            
            # Ferramentas essenciais
            SuggestionRule(
                name="essential_tools",
                description="Ferramentas essenciais para qualquer desenvolvedor",
                trigger_components=["vscode", "git"],
                suggested_components=["7zip", "notepadplusplus", "chrome"],
                confidence_boost=0.1,
                priority=5
            ),
            
            # Containerização
            SuggestionRule(
                name="containerization_stack",
                description="Stack de containerização",
                trigger_components=["docker"],
                suggested_components=["kubernetes", "docker_compose", "portainer"],
                confidence_boost=0.2,
                priority=6
            ),
            
            # Desenvolvimento Mobile
            SuggestionRule(
                name="mobile_development",
                description="Ferramentas para desenvolvimento mobile",
                trigger_components=["android_studio", "flutter"],
                suggested_components=["java", "nodejs", "git", "chrome"],
                confidence_boost=0.15,
                priority=8
            )
        ]
        
        self.logger.info(f"Inicializadas {len(rules)} regras de sugestão")
        return rules
    
    def _initialize_development_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa padrões de desenvolvimento conhecidos."""
        patterns = {
            "web_frontend": {
                "core_components": ["nodejs", "vscode", "chrome", "git"],
                "optional_components": ["firefox", "postman", "figma"],
                "description": "Desenvolvimento frontend web",
                "confidence_multiplier": 1.2
            },
            
            "web_backend": {
                "core_components": ["nodejs", "python", "docker", "git"],
                "optional_components": ["postgresql", "redis", "nginx"],
                "description": "Desenvolvimento backend web",
                "confidence_multiplier": 1.1
            },
            
            "data_science": {
                "core_components": ["python", "jupyter", "git"],
                "optional_components": ["r", "anaconda", "tableau"],
                "description": "Ciência de dados",
                "confidence_multiplier": 1.3
            },
            
            "game_development": {
                "core_components": ["unity", "unreal_engine", "blender"],
                "optional_components": ["photoshop", "audacity", "git"],
                "description": "Desenvolvimento de jogos",
                "confidence_multiplier": 1.2
            },
            
            "retro_gaming": {
                "core_components": ["retroarch", "mednafen"],
                "optional_components": ["mame", "dolphin", "pcsx2", "ppsspp"],
                "description": "Jogos retrô e emulação",
                "confidence_multiplier": 1.4
            }
        }
        
        return patterns
    
    def analyze_context(self, context: SuggestionContext) -> Dict[str, Any]:
        """Analisa o contexto para identificar padrões de uso."""
        analysis = {
            "detected_categories": set(),
            "development_patterns": [],
            "missing_essentials": [],
            "confidence_factors": {}
        }
        
        # Analisa aplicações detectadas
        for app in context.detected_apps:
            matches = self.component_matcher.find_component_matches(app)
            for match in matches:
                if match.confidence >= 0.7:
                    metadata = self.metadata_manager.get_metadata(match.component_name)
                    if metadata:
                        analysis["detected_categories"].add(metadata.category)
        
        # Identifica padrões de desenvolvimento
        for pattern_name, pattern_data in self.development_patterns.items():
            core_components = pattern_data["core_components"]
            detected_core = len([comp for comp in core_components if comp in context.installed_components])
            
            if detected_core >= len(core_components) * 0.5:  # 50% dos componentes core
                analysis["development_patterns"].append({
                    "name": pattern_name,
                    "description": pattern_data["description"],
                    "completion": detected_core / len(core_components),
                    "multiplier": pattern_data["confidence_multiplier"]
                })
        
        # Identifica ferramentas essenciais em falta
        essential_tools = ["git", "vscode", "chrome", "7zip"]
        analysis["missing_essentials"] = [
            tool for tool in essential_tools 
            if tool not in context.installed_components
        ]
        
        return analysis
    
    def generate_suggestions(self, context: SuggestionContext) -> List[EnhancedSuggestion]:
        """Gera sugestões inteligentes baseadas no contexto."""
        suggestions = []
        analysis = self.analyze_context(context)
        
        # 1. Sugestões baseadas em correspondências diretas
        direct_suggestions = self._get_direct_match_suggestions(context)
        suggestions.extend(direct_suggestions)
        
        # 2. Sugestões baseadas em regras
        rule_suggestions = self._get_rule_based_suggestions(context, analysis)
        suggestions.extend(rule_suggestions)
        
        # 3. Sugestões baseadas em padrões de desenvolvimento
        pattern_suggestions = self._get_pattern_based_suggestions(context, analysis)
        suggestions.extend(pattern_suggestions)
        
        # 4. Sugestões de ferramentas essenciais
        essential_suggestions = self._get_essential_tool_suggestions(context, analysis)
        suggestions.extend(essential_suggestions)
        
        # Remove duplicatas e ordena por confiança
        unique_suggestions = self._deduplicate_and_rank(suggestions)
        
        # Aplica filtros do contexto
        filtered_suggestions = self._apply_context_filters(unique_suggestions, context)
        
        # Registra no histórico
        self._record_suggestion_session(context, filtered_suggestions)
        
        return filtered_suggestions[:10]  # Retorna top 10
    
    def _get_direct_match_suggestions(self, context: SuggestionContext) -> List[EnhancedSuggestion]:
        """Gera sugestões baseadas em correspondências diretas."""
        suggestions = []
        
        for app in context.detected_apps:
            matches = self.component_matcher.find_component_matches(app)
            
            for match in matches:
                if (match.confidence >= 0.6 and 
                    match.component_name not in context.installed_components):
                    
                    metadata = self.metadata_manager.get_metadata(match.component_name)
                    
                    reasoning = [f"Detectada aplicação '{app.name}' que corresponde a este componente"]
                    if match.match_type == "exact":
                        reasoning.append("Correspondência exata encontrada")
                    elif match.match_type == "fuzzy":
                        reasoning.append(f"Correspondência aproximada (similaridade: {match.confidence:.1%})")
                    
                    suggestions.append(EnhancedSuggestion(
                        component_name=match.component_name,
                        confidence=match.confidence,
                        reasoning=reasoning,
                        category=metadata.category if metadata else "unknown",
                        priority=metadata.priority if metadata else 1,
                        tags=metadata.tags if metadata else [],
                        installation_complexity="easy" if match.confidence > 0.9 else "medium"
                    ))
        
        return suggestions
    
    def _get_rule_based_suggestions(self, context: SuggestionContext, analysis: Dict[str, Any]) -> List[EnhancedSuggestion]:
        """Gera sugestões baseadas em regras definidas."""
        suggestions = []
        
        for rule in self.suggestion_rules:
            if not rule.active:
                continue
            
            # Verifica se a regra é ativada
            triggered = any(comp in context.installed_components for comp in rule.trigger_components)
            
            if triggered:
                for suggested_comp in rule.suggested_components:
                    if suggested_comp not in context.installed_components:
                        metadata = self.metadata_manager.get_metadata(suggested_comp)
                        
                        # Aplica filtro de categoria se especificado
                        if (rule.category_filter and metadata and 
                            metadata.category != rule.category_filter):
                            continue
                        
                        reasoning = [
                            f"Recomendado pela regra: {rule.description}",
                            f"Baseado na presença de: {', '.join(rule.trigger_components)}"
                        ]
                        
                        base_confidence = 0.7 + rule.confidence_boost
                        
                        suggestions.append(EnhancedSuggestion(
                            component_name=suggested_comp,
                            confidence=min(base_confidence, 1.0),
                            reasoning=reasoning,
                            category=metadata.category if metadata else "unknown",
                            priority=rule.priority,
                            tags=metadata.tags if metadata else [],
                            installation_complexity="medium"
                        ))
        
        return suggestions
    
    def _get_pattern_based_suggestions(self, context: SuggestionContext, analysis: Dict[str, Any]) -> List[EnhancedSuggestion]:
        """Gera sugestões baseadas em padrões de desenvolvimento identificados."""
        suggestions = []
        
        for pattern in analysis["development_patterns"]:
            pattern_data = self.development_patterns[pattern["name"]]
            
            # Sugere componentes opcionais do padrão
            for optional_comp in pattern_data["optional_components"]:
                if optional_comp not in context.installed_components:
                    metadata = self.metadata_manager.get_metadata(optional_comp)
                    
                    confidence = 0.6 * pattern["completion"] * pattern["multiplier"]
                    
                    reasoning = [
                        f"Recomendado para o padrão: {pattern['description']}",
                        f"Padrão detectado com {pattern['completion']:.1%} de completude"
                    ]
                    
                    suggestions.append(EnhancedSuggestion(
                        component_name=optional_comp,
                        confidence=min(confidence, 1.0),
                        reasoning=reasoning,
                        category=metadata.category if metadata else "unknown",
                        priority=5,
                        tags=metadata.tags if metadata else [],
                        installation_complexity="medium"
                    ))
        
        return suggestions
    
    def _get_essential_tool_suggestions(self, context: SuggestionContext, analysis: Dict[str, Any]) -> List[EnhancedSuggestion]:
        """Gera sugestões de ferramentas essenciais."""
        suggestions = []
        
        essential_priorities = {
            "git": (10, "Controle de versão essencial para desenvolvimento"),
            "vscode": (9, "Editor de código versátil e popular"),
            "chrome": (7, "Browser essencial para desenvolvimento web"),
            "7zip": (6, "Ferramenta de compressão útil")
        }
        
        for tool in analysis["missing_essentials"]:
            if tool in essential_priorities:
                priority, description = essential_priorities[tool]
                metadata = self.metadata_manager.get_metadata(tool)
                
                reasoning = [
                    f"Ferramenta essencial: {description}",
                    "Recomendado para a maioria dos desenvolvedores"
                ]
                
                suggestions.append(EnhancedSuggestion(
                    component_name=tool,
                    confidence=0.8,
                    reasoning=reasoning,
                    category=metadata.category if metadata else "essential",
                    priority=priority,
                    tags=metadata.tags if metadata else ["essential"],
                    installation_complexity="easy"
                ))
        
        return suggestions
    
    def _deduplicate_and_rank(self, suggestions: List[EnhancedSuggestion]) -> List[EnhancedSuggestion]:
        """Remove duplicatas e ordena sugestões por relevância."""
        # Agrupa por componente
        component_suggestions = defaultdict(list)
        for suggestion in suggestions:
            component_suggestions[suggestion.component_name].append(suggestion)
        
        # Mantém a melhor sugestão para cada componente
        unique_suggestions = []
        for component_name, comp_suggestions in component_suggestions.items():
            # Ordena por confiança e prioridade
            comp_suggestions.sort(key=lambda x: (x.confidence, x.priority), reverse=True)
            best_suggestion = comp_suggestions[0]
            
            # Combina reasoning de todas as sugestões
            all_reasoning = []
            for sugg in comp_suggestions:
                all_reasoning.extend(sugg.reasoning)
            best_suggestion.reasoning = list(set(all_reasoning))  # Remove duplicatas
            
            unique_suggestions.append(best_suggestion)
        
        # Ordena por score combinado
        unique_suggestions.sort(
            key=lambda x: (x.confidence * 0.7 + (x.priority / 10) * 0.3), 
            reverse=True
        )
        
        return unique_suggestions
    
    def _apply_context_filters(self, suggestions: List[EnhancedSuggestion], context: SuggestionContext) -> List[EnhancedSuggestion]:
        """Aplica filtros baseados no contexto do usuário."""
        filtered = []
        
        for suggestion in suggestions:
            # Filtro por categoria excluída
            if suggestion.category in context.exclude_categories:
                continue
            
            # Filtro por nível de experiência
            if context.experience_level == "beginner" and suggestion.installation_complexity == "hard":
                continue
            
            # Filtro por foco de desenvolvimento
            if context.development_focus:
                metadata = self.metadata_manager.get_metadata(suggestion.component_name)
                if metadata and context.development_focus not in metadata.tags:
                    suggestion.confidence *= 0.8  # Reduz confiança
            
            filtered.append(suggestion)
        
        return filtered
    
    def _record_suggestion_session(self, context: SuggestionContext, suggestions: List[EnhancedSuggestion]) -> None:
        """Registra sessão de sugestões para análise futura."""
        session_record = {
            "timestamp": datetime.now().isoformat(),
            "detected_apps_count": len(context.detected_apps),
            "installed_components_count": len(context.installed_components),
            "suggestions_count": len(suggestions),
            "top_suggestion": suggestions[0].component_name if suggestions else None,
            "development_focus": context.development_focus,
            "experience_level": context.experience_level
        }
        
        self.suggestion_history.append(session_record)
        
        # Mantém apenas os últimos 100 registros
        if len(self.suggestion_history) > 100:
            self.suggestion_history = self.suggestion_history[-100:]
    
    def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas das sugestões geradas."""
        if not self.suggestion_history:
            return {"message": "Nenhuma sessão de sugestões registrada"}
        
        recent_sessions = [
            session for session in self.suggestion_history
            if datetime.fromisoformat(session["timestamp"]) > datetime.now() - timedelta(days=30)
        ]
        
        top_suggestions = Counter(
            session["top_suggestion"] for session in recent_sessions 
            if session["top_suggestion"]
        )
        
        return {
            "total_sessions": len(self.suggestion_history),
            "recent_sessions": len(recent_sessions),
            "avg_suggestions_per_session": sum(s["suggestions_count"] for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0,
            "top_suggested_components": dict(top_suggestions.most_common(5)),
            "experience_levels": Counter(s["experience_level"] for s in recent_sessions),
            "development_focus": Counter(s["development_focus"] for s in recent_sessions if s["development_focus"])
        }


def create_suggestion_engine(component_matcher: ComponentMatcher,
                           metadata_manager: ComponentMetadataManager,
                           logger: Optional[logging.Logger] = None) -> IntelligentSuggestionEngine:
    """Factory function para criar um IntelligentSuggestionEngine."""
    return IntelligentSuggestionEngine(component_matcher, metadata_manager, logger)