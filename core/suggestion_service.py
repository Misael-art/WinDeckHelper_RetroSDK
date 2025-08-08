#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Sugestões Integrado

Este módulo coordena todos os componentes do sistema de sugestões:
- ComponentMatcher para correspondência de aplicações
- ComponentMetadataManager para metadados
- IntelligentSuggestionEngine para sugestões avançadas
- Interface com o sistema de detecção existente
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import json
from dataclasses import asdict

from .component_matcher import ComponentMatcher, ComponentMatch, create_component_matcher
from .component_metadata_manager import ComponentMetadataManager, create_metadata_manager
from .intelligent_suggestions import (
    IntelligentSuggestionEngine, 
    SuggestionContext, 
    EnhancedSuggestion,
    create_suggestion_engine
)
from .detection_engine import DetectionEngine, DetectedApplication
from .installer import Installer


class SuggestionService:
    """Serviço principal que coordena o sistema de sugestões."""
    
    def __init__(self, 
                 components_data: Dict[str, Dict],
                 detection_engine: DetectionEngine,
                 installer: Installer,
                 logger: Optional[logging.Logger] = None):
        self.components_data = components_data
        self.detection_engine = detection_engine
        self.installer = installer
        self.logger = logger or logging.getLogger(__name__)
        
        # Inicializa componentes do sistema
        self.metadata_manager = create_metadata_manager(
            metadata_file="data/component_metadata.json",
            logger=self.logger
        )
        
        self.component_matcher = create_component_matcher(
            components_data=components_data,
            logger=self.logger
        )
        
        self.suggestion_engine = create_suggestion_engine(
            component_matcher=self.component_matcher,
            metadata_manager=self.metadata_manager,
            logger=self.logger
        )
        
        # Cache de resultados
        self._detection_cache: Optional[List[DetectedApplication]] = None
        self._suggestions_cache: Optional[List[EnhancedSuggestion]] = None
        self._cache_timestamp: Optional[float] = None
        
        # Configurações
        self.cache_duration = 300  # 5 minutos
        
        self.logger.info("SuggestionService inicializado com sucesso")
    
    async def initialize(self) -> None:
        """Inicializa o serviço de forma assíncrona."""
        try:
            # Atualiza metadados baseado nos componentes YAML
            self.metadata_manager.update_from_yaml_components(self.components_data)
            
            # Executa detecção inicial
            await self.refresh_detection_cache()
            
            self.logger.info("SuggestionService inicializado e cache atualizado")
        except Exception as e:
            self.logger.error(f"Erro na inicialização do SuggestionService: {e}")
            raise
    
    async def refresh_detection_cache(self) -> List[DetectedApplication]:
        """Atualiza cache de aplicações detectadas."""
        try:
            self.logger.info("Iniciando detecção de aplicações...")
            
            # Executa detecção (pode ser demorado)
            detection_result = await asyncio.to_thread(self.detection_engine.detect_all_applications)
            
            self._detection_cache = detection_result.applications
            self._cache_timestamp = asyncio.get_event_loop().time()
            
            # Invalida cache de sugestões
            self._suggestions_cache = None
            
            self.logger.info(f"Detectadas {len(self._detection_cache)} aplicações")
            return self._detection_cache
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de aplicações: {e}")
            return []
    
    def get_detected_applications(self) -> List[DetectedApplication]:
        """Obtém aplicações detectadas (usa cache se disponível)."""
        if self._detection_cache is None:
            self.logger.warning("Cache de detecção vazio, executando detecção síncrona")
            detection_result = self.detection_engine.detect_all_applications()
            self._detection_cache = detection_result.applications
            self._cache_timestamp = asyncio.get_event_loop().time()
        
        return self._detection_cache or []
    
    def find_component_matches(self, app_name: str) -> List[ComponentMatch]:
        """Encontra correspondências para uma aplicação específica."""
        # Cria DetectedApplication temporária
        temp_app = DetectedApplication(
            name=app_name,
            version="unknown",
            publisher="unknown",
            install_path="",
            executable_path=""
        )
        
        return self.component_matcher.find_component_matches(temp_app)
    
    def get_component_suggestions(self, 
                                context: Optional[SuggestionContext] = None,
                                force_refresh: bool = False) -> List[EnhancedSuggestion]:
        """Obtém sugestões de componentes baseadas no contexto."""
        # Verifica cache
        current_time = asyncio.get_event_loop().time()
        if (not force_refresh and 
            self._suggestions_cache is not None and 
            self._cache_timestamp is not None and 
            current_time - self._cache_timestamp < self.cache_duration):
            return self._suggestions_cache
        
        # Obtém aplicações detectadas
        detected_apps = self.get_detected_applications()
        
        # Obtém componentes instalados
        installed_components = self._get_installed_components()
        
        # Cria contexto padrão se não fornecido
        if context is None:
            context = SuggestionContext(
                detected_apps=detected_apps,
                installed_components=installed_components
            )
        else:
            # Atualiza contexto com dados atuais
            context.detected_apps = detected_apps
            context.installed_components = installed_components
        
        # Gera sugestões
        suggestions = self.suggestion_engine.generate_suggestions(context)
        
        # Atualiza cache
        self._suggestions_cache = suggestions
        self._cache_timestamp = current_time
        
        return suggestions
    
    def _get_installed_components(self) -> Set[str]:
        """Obtém lista de componentes já instalados."""
        installed = set()
        
        for component_name in self.components_data.keys():
            try:
                if self.installer.check_component_installed(component_name):
                    installed.add(component_name)
            except Exception as e:
                self.logger.debug(f"Erro ao verificar componente {component_name}: {e}")
        
        return installed
    
    def get_suggestions_by_category(self, category: str) -> List[EnhancedSuggestion]:
        """Obtém sugestões filtradas por categoria."""
        all_suggestions = self.get_component_suggestions()
        return [s for s in all_suggestions if s.category.lower() == category.lower()]
    
    def get_missing_essentials(self) -> List[EnhancedSuggestion]:
        """Obtém sugestões de ferramentas essenciais em falta."""
        all_suggestions = self.get_component_suggestions()
        return [s for s in all_suggestions if "essential" in s.tags]
    
    def search_components(self, query: str) -> List[Dict[str, Any]]:
        """Busca componentes por nome, alias ou tag."""
        # Busca nos metadados
        metadata_results = self.metadata_manager.search_components(query)
        
        # Busca correspondências fuzzy
        fuzzy_matches = []
        for component_name in self.components_data.keys():
            similarity = self.component_matcher.calculate_fuzzy_similarity(query, component_name)
            if similarity >= 0.5:
                fuzzy_matches.append((component_name, similarity))
        
        # Combina resultados
        results = []
        all_matches = set(metadata_results + [match[0] for match in fuzzy_matches])
        
        for component_name in all_matches:
            component_data = self.components_data.get(component_name, {})
            metadata = self.metadata_manager.get_metadata(component_name)
            
            # Calcula relevância
            relevance = 0.5
            if component_name in metadata_results:
                relevance += 0.3
            
            fuzzy_match = next((m for m in fuzzy_matches if m[0] == component_name), None)
            if fuzzy_match:
                relevance += fuzzy_match[1] * 0.2
            
            results.append({
                "component_name": component_name,
                "display_name": component_data.get("name", component_name),
                "description": component_data.get("description", ""),
                "category": metadata.category if metadata else "unknown",
                "tags": metadata.tags if metadata else [],
                "relevance": relevance,
                "installed": self.installer.check_component_installed(component_name)
            })
        
        # Ordena por relevância
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:20]  # Retorna top 20
    
    def get_component_details(self, component_name: str) -> Dict[str, Any]:
        """Obtém detalhes completos de um componente."""
        component_data = self.components_data.get(component_name, {})
        metadata = self.metadata_manager.get_metadata(component_name)
        
        # Encontra aplicações detectadas relacionadas
        detected_apps = self.get_detected_applications()
        related_apps = []
        
        for app in detected_apps:
            matches = self.component_matcher.find_component_matches(app)
            for match in matches:
                if match.component_name == component_name and match.confidence >= 0.6:
                    related_apps.append({
                        "name": app.name,
                        "version": app.version,
                        "confidence": match.confidence,
                        "match_type": match.match_type
                    })
        
        # Obtém componentes relacionados
        related_components = []
        if metadata and metadata.related_components:
            for related_name in metadata.related_components:
                if related_name in self.components_data:
                    related_data = self.components_data[related_name]
                    related_components.append({
                        "name": related_name,
                        "display_name": related_data.get("name", related_name),
                        "installed": self.installer.check_component_installed(related_name)
                    })
        
        return {
            "component_name": component_name,
            "display_name": component_data.get("name", component_name),
            "description": component_data.get("description", ""),
            "category": metadata.category if metadata else "unknown",
            "subcategory": metadata.subcategory if metadata else "",
            "tags": metadata.tags if metadata else [],
            "aliases": metadata.aliases if metadata else [],
            "priority": metadata.priority if metadata else 0,
            "installed": self.installer.check_component_installed(component_name),
            "related_apps": related_apps,
            "related_components": related_components,
            "metadata": asdict(metadata) if metadata else {}
        }
    
    def export_suggestions_report(self, filepath: str) -> None:
        """Exporta relatório completo de sugestões."""
        try:
            suggestions = self.get_component_suggestions()
            detected_apps = self.get_detected_applications()
            installed_components = self._get_installed_components()
            
            report = {
                "timestamp": asyncio.get_event_loop().time(),
                "summary": {
                    "detected_applications": len(detected_apps),
                    "installed_components": len(installed_components),
                    "suggestions_count": len(suggestions),
                    "high_confidence_suggestions": len([s for s in suggestions if s.confidence >= 0.8])
                },
                "detected_applications": [
                    {
                        "name": app.name,
                        "version": app.version,
                        "publisher": app.publisher,
                        "install_path": app.install_path
                    }
                    for app in detected_apps
                ],
                "installed_components": list(installed_components),
                "suggestions": [
                    {
                        "component_name": s.component_name,
                        "confidence": s.confidence,
                        "reasoning": s.reasoning,
                        "category": s.category,
                        "priority": s.priority,
                        "tags": s.tags,
                        "installation_complexity": s.installation_complexity
                    }
                    for s in suggestions
                ],
                "statistics": self.suggestion_engine.get_suggestion_statistics(),
                "metadata_stats": self.metadata_manager.get_statistics()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Relatório de sugestões exportado para {filepath}")
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar relatório: {e}")
            raise
    
    def add_custom_suggestion_rule(self, 
                                 name: str,
                                 trigger_components: List[str],
                                 suggested_components: List[str],
                                 description: str = "",
                                 confidence_boost: float = 0.1) -> None:
        """Adiciona regra de sugestão customizada."""
        from .intelligent_suggestions import SuggestionRule
        
        rule = SuggestionRule(
            name=name,
            description=description,
            trigger_components=trigger_components,
            suggested_components=suggested_components,
            confidence_boost=confidence_boost,
            priority=5  # Prioridade média para regras customizadas
        )
        
        self.suggestion_engine.suggestion_rules.append(rule)
        
        # Invalida cache para forçar recálculo
        self._suggestions_cache = None
        
        self.logger.info(f"Regra de sugestão customizada '{name}' adicionada")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Obtém status do serviço de sugestões."""
        return {
            "initialized": True,
            "cache_status": {
                "detection_cached": self._detection_cache is not None,
                "suggestions_cached": self._suggestions_cache is not None,
                "cache_age_seconds": (
                    asyncio.get_event_loop().time() - self._cache_timestamp
                    if self._cache_timestamp else None
                )
            },
            "components_count": len(self.components_data),
            "metadata_count": len(self.metadata_manager.metadata),
            "suggestion_rules_count": len(self.suggestion_engine.suggestion_rules),
            "detected_apps_count": len(self._detection_cache) if self._detection_cache else 0
        }


def create_suggestion_service(components_data: Dict[str, Dict],
                            detection_engine: DetectionEngine,
                            installer: Installer,
                            logger: Optional[logging.Logger] = None) -> SuggestionService:
    """Factory function para criar um SuggestionService."""
    return SuggestionService(components_data, detection_engine, installer, logger)