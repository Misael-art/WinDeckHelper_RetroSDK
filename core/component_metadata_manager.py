#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Metadados de Componentes

Este módulo gerencia metadados adicionais para componentes YAML,
incluindo aliases, tags, categorias e informações de correspondência
para melhorar o sistema de matching.
"""

import yaml
import json
import logging
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ComponentMetadata:
    """Metadados estendidos para um componente."""
    component_name: str
    aliases: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category: str = ""
    subcategory: str = ""
    detection_hints: List[str] = field(default_factory=list)  # Dicas para detecção
    executable_names: List[str] = field(default_factory=list)  # Nomes de executáveis conhecidos
    registry_keys: List[str] = field(default_factory=list)  # Chaves de registro para detecção
    file_patterns: List[str] = field(default_factory=list)  # Padrões de arquivo
    environment_vars: List[str] = field(default_factory=list)  # Variáveis de ambiente
    related_components: List[str] = field(default_factory=list)  # Componentes relacionados
    priority: int = 0  # Prioridade para sugestões (maior = mais importante)
    auto_suggest: bool = True  # Se deve ser sugerido automaticamente
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentMetadata':
        """Cria instância a partir de dicionário."""
        return cls(**data)


class ComponentMetadataManager:
    """Gerenciador de metadados de componentes."""
    
    def __init__(self, metadata_file: str = "component_metadata.json", logger: Optional[logging.Logger] = None):
        self.metadata_file = Path(metadata_file)
        self.logger = logger or logging.getLogger(__name__)
        self.metadata: Dict[str, ComponentMetadata] = {}
        
        # Carrega metadados existentes
        self.load_metadata()
        
        # Metadados padrão para componentes conhecidos
        self._initialize_default_metadata()
    
    def load_metadata(self) -> None:
        """Carrega metadados do arquivo."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.metadata = {
                    name: ComponentMetadata.from_dict(meta_data)
                    for name, meta_data in data.items()
                }
                
                self.logger.info(f"Carregados metadados para {len(self.metadata)} componentes")
            except Exception as e:
                self.logger.error(f"Erro ao carregar metadados: {e}")
                self.metadata = {}
        else:
            self.logger.info("Arquivo de metadados não encontrado, criando novo")
            self.metadata = {}
    
    def save_metadata(self) -> None:
        """Salva metadados no arquivo."""
        try:
            # Cria diretório se não existir
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                name: metadata.to_dict()
                for name, metadata in self.metadata.items()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Metadados salvos para {len(self.metadata)} componentes")
        except Exception as e:
            self.logger.error(f"Erro ao salvar metadados: {e}")
    
    def _initialize_default_metadata(self) -> None:
        """Inicializa metadados padrão para componentes conhecidos."""
        default_metadata = {
            # Desenvolvimento
            "vscode": ComponentMetadata(
                component_name="vscode",
                aliases=["visual studio code", "code", "vs code"],
                tags=["editor", "development", "microsoft"],
                category="development",
                subcategory="editor",
                executable_names=["code.exe", "code"],
                registry_keys=["HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{*}\\DisplayName"],
                detection_hints=["Visual Studio Code", "Microsoft Corporation"],
                priority=10,
                related_components=["git", "nodejs", "python"]
            ),
            
            "git": ComponentMetadata(
                component_name="git",
                aliases=["git scm", "git for windows"],
                tags=["vcs", "development", "scm"],
                category="development",
                subcategory="version_control",
                executable_names=["git.exe", "git"],
                environment_vars=["GIT_HOME", "PATH"],
                detection_hints=["Git", "git-scm.com"],
                priority=10,
                related_components=["vscode", "github_desktop"]
            ),
            
            "nodejs": ComponentMetadata(
                component_name="nodejs",
                aliases=["node.js", "node", "npm"],
                tags=["runtime", "javascript", "development"],
                category="runtime",
                subcategory="javascript",
                executable_names=["node.exe", "npm.exe", "node", "npm"],
                environment_vars=["NODE_HOME", "NPM_CONFIG_PREFIX"],
                detection_hints=["Node.js", "npm"],
                priority=9,
                related_components=["vscode", "yarn"]
            ),
            
            "python": ComponentMetadata(
                component_name="python",
                aliases=["python3", "py"],
                tags=["runtime", "programming", "development"],
                category="runtime",
                subcategory="python",
                executable_names=["python.exe", "python3.exe", "py.exe"],
                environment_vars=["PYTHON_HOME", "PYTHONPATH"],
                detection_hints=["Python", "Python Software Foundation"],
                priority=9,
                related_components=["pip", "vscode"]
            ),
            
            "java": ComponentMetadata(
                component_name="java",
                aliases=["jdk", "jre", "openjdk", "oracle jdk"],
                tags=["runtime", "programming", "development"],
                category="runtime",
                subcategory="java",
                executable_names=["java.exe", "javac.exe", "java"],
                environment_vars=["JAVA_HOME", "JRE_HOME"],
                detection_hints=["Java", "Oracle", "OpenJDK"],
                priority=8,
                related_components=["maven", "gradle"]
            ),
            
            # Browsers
            "chrome": ComponentMetadata(
                component_name="chrome",
                aliases=["google chrome", "chrome browser"],
                tags=["browser", "web", "google"],
                category="browser",
                executable_names=["chrome.exe", "google-chrome"],
                detection_hints=["Google Chrome", "Google LLC"],
                priority=7
            ),
            
            "firefox": ComponentMetadata(
                component_name="firefox",
                aliases=["mozilla firefox", "firefox browser"],
                tags=["browser", "web", "mozilla"],
                category="browser",
                executable_names=["firefox.exe", "firefox"],
                detection_hints=["Mozilla Firefox", "Mozilla Corporation"],
                priority=7
            ),
            
            # Emuladores
            "retroarch": ComponentMetadata(
                component_name="retroarch",
                aliases=["retro arch"],
                tags=["emulator", "gaming", "retro"],
                category="emulator",
                subcategory="multi_system",
                executable_names=["retroarch.exe", "retroarch"],
                detection_hints=["RetroArch"],
                priority=6,
                related_components=["mednafen", "mame"]
            ),
            
            "mednafen": ComponentMetadata(
                component_name="mednafen",
                aliases=["mednafen emulator"],
                tags=["emulator", "gaming", "multi_system"],
                category="emulator",
                subcategory="multi_system",
                executable_names=["mednafen.exe", "mednafen"],
                detection_hints=["Mednafen"],
                priority=5,
                related_components=["retroarch"]
            ),
            
            # Ferramentas
            "7zip": ComponentMetadata(
                component_name="7zip",
                aliases=["7-zip", "seven zip"],
                tags=["utility", "compression", "archive"],
                category="utility",
                subcategory="compression",
                executable_names=["7z.exe", "7zG.exe"],
                detection_hints=["7-Zip", "Igor Pavlov"],
                priority=6
            ),
            
            "vlc": ComponentMetadata(
                component_name="vlc",
                aliases=["vlc media player", "vlc player"],
                tags=["media", "player", "video"],
                category="media",
                subcategory="player",
                executable_names=["vlc.exe", "vlc"],
                detection_hints=["VLC media player", "VideoLAN"],
                priority=6
            )
        }
        
        # Adiciona metadados padrão apenas se não existirem
        for name, metadata in default_metadata.items():
            if name not in self.metadata:
                self.metadata[name] = metadata
        
        # Salva após inicialização
        self.save_metadata()
    
    def get_metadata(self, component_name: str) -> Optional[ComponentMetadata]:
        """Obtém metadados de um componente."""
        return self.metadata.get(component_name)
    
    def set_metadata(self, component_name: str, metadata: ComponentMetadata) -> None:
        """Define metadados para um componente."""
        metadata.last_updated = datetime.now().isoformat()
        self.metadata[component_name] = metadata
        self.save_metadata()
    
    def add_alias(self, component_name: str, alias: str) -> None:
        """Adiciona alias a um componente."""
        if component_name not in self.metadata:
            self.metadata[component_name] = ComponentMetadata(component_name=component_name)
        
        if alias not in self.metadata[component_name].aliases:
            self.metadata[component_name].aliases.append(alias)
            self.metadata[component_name].last_updated = datetime.now().isoformat()
            self.save_metadata()
    
    def add_tag(self, component_name: str, tag: str) -> None:
        """Adiciona tag a um componente."""
        if component_name not in self.metadata:
            self.metadata[component_name] = ComponentMetadata(component_name=component_name)
        
        if tag not in self.metadata[component_name].tags:
            self.metadata[component_name].tags.append(tag)
            self.metadata[component_name].last_updated = datetime.now().isoformat()
            self.save_metadata()
    
    def get_components_by_category(self, category: str) -> List[str]:
        """Obtém componentes por categoria."""
        return [
            name for name, metadata in self.metadata.items()
            if metadata.category.lower() == category.lower()
        ]
    
    def get_components_by_tag(self, tag: str) -> List[str]:
        """Obtém componentes por tag."""
        return [
            name for name, metadata in self.metadata.items()
            if tag.lower() in [t.lower() for t in metadata.tags]
        ]
    
    def search_components(self, query: str) -> List[str]:
        """Busca componentes por nome, alias ou tag."""
        query_lower = query.lower()
        results = []
        
        for name, metadata in self.metadata.items():
            # Busca no nome
            if query_lower in name.lower():
                results.append(name)
                continue
            
            # Busca em aliases
            if any(query_lower in alias.lower() for alias in metadata.aliases):
                results.append(name)
                continue
            
            # Busca em tags
            if any(query_lower in tag.lower() for tag in metadata.tags):
                results.append(name)
                continue
            
            # Busca em detection hints
            if any(query_lower in hint.lower() for hint in metadata.detection_hints):
                results.append(name)
                continue
        
        return results
    
    def get_all_aliases(self) -> Dict[str, List[str]]:
        """Obtém todos os aliases mapeados por componente."""
        return {
            name: metadata.aliases
            for name, metadata in self.metadata.items()
            if metadata.aliases
        }
    
    def get_all_executable_names(self) -> Dict[str, List[str]]:
        """Obtém todos os nomes de executáveis mapeados por componente."""
        return {
            name: metadata.executable_names
            for name, metadata in self.metadata.items()
            if metadata.executable_names
        }
    
    def update_from_yaml_components(self, yaml_components: Dict[str, Dict]) -> None:
        """Atualiza metadados baseado nos componentes YAML existentes."""
        updated_count = 0
        
        for component_name, component_data in yaml_components.items():
            # Cria metadados se não existir
            if component_name not in self.metadata:
                self.metadata[component_name] = ComponentMetadata(component_name=component_name)
            
            metadata = self.metadata[component_name]
            
            # Atualiza categoria se especificada no YAML
            if 'category' in component_data and not metadata.category:
                metadata.category = component_data['category']
                updated_count += 1
            
            # Extrai executáveis das verificações
            if 'verification' in component_data:
                for verification in component_data['verification']:
                    if verification.get('type') == 'command_exists':
                        command = verification.get('command', '')
                        if command and command not in metadata.executable_names:
                            metadata.executable_names.append(command)
                            updated_count += 1
            
            # Atualiza timestamp
            metadata.last_updated = datetime.now().isoformat()
        
        if updated_count > 0:
            self.save_metadata()
            self.logger.info(f"Atualizados metadados para {updated_count} componentes")
    
    def export_enhanced_yaml(self, component_name: str, original_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """Exporta YAML do componente com metadados aprimorados."""
        enhanced_yaml = original_yaml.copy()
        
        if component_name in self.metadata:
            metadata = self.metadata[component_name]
            
            # Adiciona metadados ao YAML
            enhanced_yaml['metadata'] = {
                'aliases': metadata.aliases,
                'tags': metadata.tags,
                'category': metadata.category,
                'subcategory': metadata.subcategory,
                'detection_hints': metadata.detection_hints,
                'executable_names': metadata.executable_names,
                'priority': metadata.priority,
                'auto_suggest': metadata.auto_suggest,
                'related_components': metadata.related_components
            }
        
        return enhanced_yaml
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtém estatísticas dos metadados."""
        total_components = len(self.metadata)
        categories = {}
        tags = {}
        
        for metadata in self.metadata.values():
            # Conta categorias
            category = metadata.category or 'unknown'
            categories[category] = categories.get(category, 0) + 1
            
            # Conta tags
            for tag in metadata.tags:
                tags[tag] = tags.get(tag, 0) + 1
        
        return {
            'total_components': total_components,
            'categories': categories,
            'top_tags': dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]),
            'components_with_aliases': len([m for m in self.metadata.values() if m.aliases]),
            'components_with_executables': len([m for m in self.metadata.values() if m.executable_names]),
            'auto_suggest_enabled': len([m for m in self.metadata.values() if m.auto_suggest])
        }


def create_metadata_manager(metadata_file: str = "component_metadata.json", 
                          logger: Optional[logging.Logger] = None) -> ComponentMetadataManager:
    """Factory function para criar um ComponentMetadataManager."""
    return ComponentMetadataManager(metadata_file, logger)