#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Correspondência entre Aplicações Detectadas e Componentes YAML

Este módulo implementa um sistema inteligente para relacionar aplicações
detectadas no sistema com componentes YAML disponíveis, incluindo:
- Mapeamento direto de nomes
- Matching fuzzy para variações
- Sistema de sugestões
- Metadados para facilitar correspondência
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
import json

from .detection_engine import DetectedApplication


@dataclass
class ComponentMatch:
    """Representa uma correspondência entre aplicação detectada e componente YAML."""
    component_name: str
    detected_app: DetectedApplication
    confidence: float  # 0.0 a 1.0
    match_type: str  # 'exact', 'fuzzy', 'alias', 'executable'
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class SuggestionResult:
    """Resultado de sugestão de componentes baseado em aplicações detectadas."""
    suggested_components: List[ComponentMatch]
    missing_components: List[str]  # Componentes que poderiam ser úteis
    confidence_score: float
    reasoning: str


class ComponentMatcher:
    """Sistema principal de correspondência entre aplicações e componentes."""
    
    def __init__(self, components_data: Dict[str, Dict], logger: Optional[logging.Logger] = None):
        self.components_data = components_data
        self.logger = logger or logging.getLogger(__name__)
        
        # Mapas de correspondência
        self.name_mappings = self._build_name_mappings()
        self.alias_mappings = self._build_alias_mappings()
        self.executable_mappings = self._build_executable_mappings()
        
        # Configurações de matching fuzzy
        self.fuzzy_threshold = 0.7
        self.exact_threshold = 0.95
    
    def _build_name_mappings(self) -> Dict[str, str]:
        """Constrói mapeamento direto de nomes conhecidos."""
        mappings = {
            # Desenvolvimento
            "visual studio code": "vscode",
            "vscode": "vscode",
            "code": "vscode",
            "node.js": "nodejs",
            "node": "nodejs",
            "npm": "nodejs",
            "java jdk": "java",
            "openjdk": "java",
            "oracle jdk": "java",
            "adoptopenjdk": "java",
            ".net": "dotnet",
            ".net core": "dotnet",
            ".net framework": "dotnet",
            "python": "python",
            "git": "git",
            "docker": "docker",
            "docker desktop": "docker",
            
            # Editores
            "notepad++": "notepadplusplus",
            "sublime text": "sublime_text",
            "atom": "atom",
            "vim": "vim",
            "emacs": "emacs",
            
            # Browsers
            "google chrome": "chrome",
            "chrome": "chrome",
            "mozilla firefox": "firefox",
            "firefox": "firefox",
            "microsoft edge": "edge",
            "edge": "edge",
            
            # Ferramentas
            "7-zip": "7zip",
            "winrar": "winrar",
            "vlc media player": "vlc",
            "vlc": "vlc",
            "obs studio": "obs",
            "obs": "obs",
            
            # Emuladores
            "retroarch": "retroarch",
            "mednafen": "mednafen",
            "dolphin": "dolphin",
            "pcsx2": "pcsx2",
            "ppsspp": "ppsspp",
            "project64": "project64",
            "visualboyadvance": "vba",
            "snes9x": "snes9x",
            "zsnes": "zsnes",
            "epsxe": "epsxe",
            "no$gba": "nogba",
            "desmume": "desmume",
            "citra": "citra",
            "yuzu": "yuzu",
            "ryujinx": "ryujinx",
            "mame": "mame",
            "fbneo": "fbneo",
            "final burn neo": "fbneo"
        }
        
        self.logger.info(f"Construído mapeamento de nomes com {len(mappings)} entradas")
        return mappings
    
    def _build_alias_mappings(self) -> Dict[str, List[str]]:
        """Constrói mapeamento de aliases baseado nos metadados dos componentes."""
        aliases = {}
        
        for component_name, component_data in self.components_data.items():
            component_aliases = []
            
            # Aliases explícitos nos metadados
            if 'aliases' in component_data:
                component_aliases.extend(component_data['aliases'])
            
            # Aliases baseados no nome
            if 'name' in component_data:
                name = component_data['name'].lower()
                component_aliases.append(name)
                
                # Variações comuns
                component_aliases.append(name.replace(' ', ''))
                component_aliases.append(name.replace(' ', '_'))
                component_aliases.append(name.replace(' ', '-'))
            
            # Aliases baseados em executáveis
            if 'verification' in component_data:
                for verification in component_data['verification']:
                    if verification.get('type') == 'command_exists':
                        command = verification.get('command', '')
                        if command:
                            component_aliases.append(command.lower())
            
            if component_aliases:
                aliases[component_name] = list(set(component_aliases))
        
        self.logger.info(f"Construído mapeamento de aliases para {len(aliases)} componentes")
        return aliases
    
    def _build_executable_mappings(self) -> Dict[str, str]:
        """Constrói mapeamento baseado em executáveis."""
        mappings = {}
        
        for component_name, component_data in self.components_data.items():
            # Executáveis das verificações
            if 'verification' in component_data:
                for verification in component_data['verification']:
                    if verification.get('type') == 'command_exists':
                        command = verification.get('command', '')
                        if command:
                            mappings[command.lower()] = component_name
                            # Adiciona variações com .exe
                            if not command.endswith('.exe'):
                                mappings[f"{command.lower()}.exe"] = component_name
        
        self.logger.info(f"Construído mapeamento de executáveis com {len(mappings)} entradas")
        return mappings
    
    def normalize_name(self, name: str) -> str:
        """Normaliza nome para comparação."""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        
        # Remove caracteres especiais comuns
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Remove palavras comuns que não ajudam na identificação
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = normalized.split()
        words = [word for word in words if word not in stop_words]
        
        return ' '.join(words)
    
    def calculate_fuzzy_similarity(self, name1: str, name2: str) -> float:
        """Calcula similaridade fuzzy entre dois nomes."""
        if not name1 or not name2:
            return 0.0
        
        # Normaliza ambos os nomes
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Usa SequenceMatcher para calcular similaridade
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Bonus para correspondências de palavras-chave
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            similarity = max(similarity, word_overlap)
        
        return similarity
    
    def find_component_matches(self, detected_app: DetectedApplication) -> List[ComponentMatch]:
        """Encontra correspondências para uma aplicação detectada."""
        matches = []
        app_name = detected_app.name.lower()
        normalized_app_name = self.normalize_name(detected_app.name)
        
        # 1. Correspondência exata por mapeamento direto
        if app_name in self.name_mappings:
            component_name = self.name_mappings[app_name]
            if component_name in self.components_data:
                matches.append(ComponentMatch(
                    component_name=component_name,
                    detected_app=detected_app,
                    confidence=1.0,
                    match_type='exact',
                    metadata={'mapping_source': 'direct_name'}
                ))
        
        # 2. Correspondência por executável
        if detected_app.executable_path:
            exe_name = Path(detected_app.executable_path).stem.lower()
            if exe_name in self.executable_mappings:
                component_name = self.executable_mappings[exe_name]
                if component_name in self.components_data:
                    matches.append(ComponentMatch(
                        component_name=component_name,
                        detected_app=detected_app,
                        confidence=0.9,
                        match_type='executable',
                        metadata={'executable': exe_name}
                    ))
        
        # 3. Correspondência por aliases
        for component_name, aliases in self.alias_mappings.items():
            for alias in aliases:
                if self.calculate_fuzzy_similarity(app_name, alias) >= self.exact_threshold:
                    matches.append(ComponentMatch(
                        component_name=component_name,
                        detected_app=detected_app,
                        confidence=0.85,
                        match_type='alias',
                        metadata={'matched_alias': alias}
                    ))
                    break
        
        # 4. Correspondência fuzzy
        for component_name, component_data in self.components_data.items():
            # Evita duplicatas
            if any(match.component_name == component_name for match in matches):
                continue
            
            # Testa contra o nome do componente
            component_display_name = component_data.get('name', component_name)
            similarity = self.calculate_fuzzy_similarity(normalized_app_name, component_display_name)
            
            if similarity >= self.fuzzy_threshold:
                matches.append(ComponentMatch(
                    component_name=component_name,
                    detected_app=detected_app,
                    confidence=similarity,
                    match_type='fuzzy',
                    metadata={'similarity_score': similarity}
                ))
        
        # Ordena por confiança (maior primeiro)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicatas mantendo a melhor correspondência
        unique_matches = []
        seen_components = set()
        
        for match in matches:
            if match.component_name not in seen_components:
                unique_matches.append(match)
                seen_components.add(match.component_name)
        
        return unique_matches
    
    def generate_suggestions(self, detected_apps: List[DetectedApplication]) -> SuggestionResult:
        """Gera sugestões de componentes baseado em aplicações detectadas."""
        all_matches = []
        detected_categories = set()
        
        # Encontra correspondências para todas as aplicações
        for app in detected_apps:
            matches = self.find_component_matches(app)
            all_matches.extend(matches)
            
            # Identifica categorias das aplicações detectadas
            for match in matches:
                if match.confidence >= 0.7:  # Apenas correspondências confiáveis
                    component_data = self.components_data.get(match.component_name, {})
                    category = component_data.get('category', 'unknown')
                    detected_categories.add(category.lower())
        
        # Filtra apenas as melhores correspondências
        high_confidence_matches = [match for match in all_matches if match.confidence >= 0.7]
        
        # Identifica componentes em falta que poderiam ser úteis
        missing_components = self._suggest_missing_components(detected_categories, high_confidence_matches)
        
        # Calcula score de confiança geral
        if high_confidence_matches:
            avg_confidence = sum(match.confidence for match in high_confidence_matches) / len(high_confidence_matches)
        else:
            avg_confidence = 0.0
        
        # Gera reasoning
        reasoning = self._generate_reasoning(detected_apps, high_confidence_matches, missing_components)
        
        return SuggestionResult(
            suggested_components=high_confidence_matches,
            missing_components=missing_components,
            confidence_score=avg_confidence,
            reasoning=reasoning
        )
    
    def _suggest_missing_components(self, detected_categories: Set[str], matches: List[ComponentMatch]) -> List[str]:
        """Sugere componentes que poderiam ser úteis baseado nas categorias detectadas."""
        matched_components = {match.component_name for match in matches}
        suggestions = []
        
        # Regras de sugestão baseadas em categorias
        category_suggestions = {
            'development': ['git', 'vscode', 'nodejs', 'python', 'docker'],
            'editor': ['vscode', 'notepadplusplus', 'sublime_text'],
            'runtime': ['nodejs', 'python', 'java', 'dotnet'],
            'browser': ['chrome', 'firefox'],
            'emulator': ['retroarch', 'mednafen'],
            'game_dev': ['unity', 'unreal_engine', 'blender']
        }
        
        for category in detected_categories:
            if category in category_suggestions:
                for suggested_component in category_suggestions[category]:
                    if (suggested_component not in matched_components and 
                        suggested_component in self.components_data and
                        suggested_component not in suggestions):
                        suggestions.append(suggested_component)
        
        return suggestions[:5]  # Limita a 5 sugestões
    
    def _generate_reasoning(self, detected_apps: List[DetectedApplication], 
                          matches: List[ComponentMatch], missing_components: List[str]) -> str:
        """Gera explicação do reasoning das sugestões."""
        reasoning_parts = []
        
        if matches:
            reasoning_parts.append(f"Encontradas {len(matches)} correspondências baseadas em {len(detected_apps)} aplicações detectadas.")
            
            # Agrupa por tipo de correspondência
            match_types = {}
            for match in matches:
                match_type = match.match_type
                if match_type not in match_types:
                    match_types[match_type] = 0
                match_types[match_type] += 1
            
            type_descriptions = {
                'exact': 'correspondências exatas',
                'fuzzy': 'correspondências aproximadas',
                'alias': 'correspondências por alias',
                'executable': 'correspondências por executável'
            }
            
            for match_type, count in match_types.items():
                description = type_descriptions.get(match_type, match_type)
                reasoning_parts.append(f"{count} {description}")
        
        if missing_components:
            reasoning_parts.append(f"Sugeridos {len(missing_components)} componentes adicionais que podem ser úteis.")
        
        return " ".join(reasoning_parts) if reasoning_parts else "Nenhuma correspondência encontrada."
    
    def export_mappings(self, filepath: str) -> None:
        """Exporta mapeamentos para arquivo JSON para debug/análise."""
        export_data = {
            'name_mappings': self.name_mappings,
            'alias_mappings': self.alias_mappings,
            'executable_mappings': self.executable_mappings,
            'components_count': len(self.components_data),
            'fuzzy_threshold': self.fuzzy_threshold
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Mapeamentos exportados para {filepath}")


def create_component_matcher(components_data: Dict[str, Dict], logger: Optional[logging.Logger] = None) -> ComponentMatcher:
    """Factory function para criar um ComponentMatcher."""
    return ComponentMatcher(components_data, logger)