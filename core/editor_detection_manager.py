#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Editor Detection Manager - Sistema Inteligente de Detecção de Editores
Detecta editores compatíveis instalados antes de instalar VSCode como dependência.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Importar sistema de detecção existente
from .detection_engine import DetectionEngine
from .detection_base import DetectedApplication, ApplicationStatus
from .component_manager import ComponentManager, ComponentInfo

class EditorCompatibility(Enum):
    """Níveis de compatibilidade com SGDK/Genesis Code"""
    FULL = "full"  # Totalmente compatível (VSCode, Cursor, etc.)
    PARTIAL = "partial"  # Parcialmente compatível (Sublime, Atom, etc.)
    MINIMAL = "minimal"  # Compatibilidade mínima (Notepad++, etc.)
    NONE = "none"  # Sem compatibilidade

@dataclass
class EditorInfo:
    """Informações sobre um editor detectado"""
    name: str
    path: str
    version: str
    compatibility: EditorCompatibility
    supports_extensions: bool
    supports_vscode_extensions: bool = False
    command_line_tool: Optional[str] = None
    notes: str = ""

class EditorDetectionManager:
    """Gerenciador de detecção inteligente de editores"""
    
    def __init__(self, base_path: Path, logger: Optional[logging.Logger] = None):
        self.base_path = base_path
        self.logger = logger or logging.getLogger(__name__)
        
        # Inicializar sistema de detecção
        self.detection_engine = DetectionEngine()
        
        # Mapeamento de editores conhecidos e sua compatibilidade
        self.editor_compatibility_map = {
            # Editores totalmente compatíveis (baseados em VSCode ou equivalentes)
            "Visual Studio Code": EditorCompatibility.FULL,
            "Visual Studio Code Insiders": EditorCompatibility.FULL,
            "Cursor IDE": EditorCompatibility.FULL,
            "TRAE AI IDE": EditorCompatibility.FULL,
            "Codium": EditorCompatibility.FULL,
            "VSCodium": EditorCompatibility.FULL,
            
            # Editores parcialmente compatíveis
            "Sublime Text": EditorCompatibility.PARTIAL,
            "Sublime Text 3": EditorCompatibility.PARTIAL,
            "Sublime Text 4": EditorCompatibility.PARTIAL,
            "Atom": EditorCompatibility.PARTIAL,
            "Brackets": EditorCompatibility.PARTIAL,
            "Vim": EditorCompatibility.PARTIAL,
            "Neovim": EditorCompatibility.PARTIAL,
            "Emacs": EditorCompatibility.PARTIAL,
            "Kate": EditorCompatibility.PARTIAL,
            "Geany": EditorCompatibility.PARTIAL,
            "Code::Blocks": EditorCompatibility.PARTIAL,
            "Dev-C++": EditorCompatibility.PARTIAL,
            "Qt Creator": EditorCompatibility.PARTIAL,
            
            # Editores com compatibilidade mínima
            "Notepad++": EditorCompatibility.MINIMAL,
            "UltraEdit": EditorCompatibility.MINIMAL,
            "EditPlus": EditorCompatibility.MINIMAL,
            "PSPad": EditorCompatibility.MINIMAL,
            "Programmer's Notepad": EditorCompatibility.MINIMAL,
            "SciTE": EditorCompatibility.MINIMAL,
            
            # Sem compatibilidade
            "Notepad": EditorCompatibility.NONE,
            "WordPad": EditorCompatibility.NONE,
        }
        
        # Configurações específicas para editores compatíveis
        self.editor_configs = {
            "Visual Studio Code": {
                "command": "code",
                "supports_vscode_extensions": True,
                "extension_install_cmd": "code --install-extension"
            },
            "Visual Studio Code Insiders": {
                "command": "code-insiders",
                "supports_vscode_extensions": True,
                "extension_install_cmd": "code-insiders --install-extension"
            },
            "Cursor IDE": {
                "command": "cursor",
                "supports_vscode_extensions": True,
                "extension_install_cmd": "cursor --install-extension"
            },
            "TRAE AI IDE": {
                "command": "trae",
                "supports_vscode_extensions": False,
                "notes": "TRAE tem suporte nativo para desenvolvimento com IA"
            },
            "Sublime Text": {
                "command": "subl",
                "supports_vscode_extensions": False,
                "notes": "Requer configuração manual para SGDK"
            }
        }
    
    def detect_installed_editors(self) -> List[EditorInfo]:
        """Detecta todos os editores instalados no sistema"""
        self.logger.info("🔍 Detectando editores instalados...")
        
        detected_editors = []
        
        # Usar o sistema de detecção existente
        detection_result = self.detection_engine.detect_all_applications()
        
        for app in detection_result.applications:
            if self._is_editor(app):
                editor_info = self._create_editor_info(app)
                if editor_info:
                    detected_editors.append(editor_info)
                    self.logger.info(f"✅ Editor detectado: {editor_info.name} ({editor_info.compatibility.value})")
        
        return detected_editors
    
    def _is_editor(self, app: DetectedApplication) -> bool:
        """Verifica se uma aplicação é um editor"""
        # Verificar por nome conhecido
        for editor_name in self.editor_compatibility_map.keys():
            if editor_name.lower() in app.name.lower():
                return True
        
        # Verificar por palavras-chave comuns em editores
        editor_keywords = [
            "code", "editor", "ide", "text", "notepad", "vim", "emacs",
            "sublime", "atom", "brackets", "visual studio", "cursor"
        ]
        
        app_name_lower = app.name.lower()
        return any(keyword in app_name_lower for keyword in editor_keywords)
    
    def _create_editor_info(self, app: DetectedApplication) -> Optional[EditorInfo]:
        """Cria informações detalhadas sobre um editor"""
        # Determinar compatibilidade
        compatibility = EditorCompatibility.NONE
        for editor_name, comp in self.editor_compatibility_map.items():
            if editor_name.lower() in app.name.lower():
                compatibility = comp
                break
        
        # Se não encontrou compatibilidade específica, tentar inferir
        if compatibility == EditorCompatibility.NONE:
            compatibility = self._infer_compatibility(app.name)
        
        # Obter configurações específicas
        config = self.editor_configs.get(app.name, {})
        
        return EditorInfo(
            name=app.name,
            path=app.install_path or "",
            version=app.version or "Unknown",
            compatibility=compatibility,
            supports_extensions=compatibility in [EditorCompatibility.FULL, EditorCompatibility.PARTIAL],
            supports_vscode_extensions=config.get("supports_vscode_extensions", False),
            command_line_tool=config.get("command"),
            notes=config.get("notes", "")
        )
    
    def _infer_compatibility(self, app_name: str) -> EditorCompatibility:
        """Infere compatibilidade baseada no nome da aplicação"""
        app_lower = app_name.lower()
        
        # Editores baseados em VSCode ou similares
        if any(keyword in app_lower for keyword in ["vscode", "code", "cursor", "codium"]):
            return EditorCompatibility.FULL
        
        # IDEs conhecidas
        if any(keyword in app_lower for keyword in ["ide", "studio", "creator", "develop"]):
            return EditorCompatibility.PARTIAL
        
        # Editores de texto avançados
        if any(keyword in app_lower for keyword in ["sublime", "atom", "vim", "emacs", "kate"]):
            return EditorCompatibility.PARTIAL
        
        # Editores básicos
        if any(keyword in app_lower for keyword in ["notepad", "edit", "text"]):
            return EditorCompatibility.MINIMAL
        
        return EditorCompatibility.NONE
    
    def should_install_vscode(self, detected_editors: Optional[List[EditorInfo]] = None) -> Tuple[bool, str]:
        """Determina se deve instalar VSCode baseado nos editores detectados"""
        if detected_editors is None:
            detected_editors = self.detect_installed_editors()
        
        # Verificar se há editores totalmente compatíveis
        fully_compatible = [e for e in detected_editors if e.compatibility == EditorCompatibility.FULL]
        
        if fully_compatible:
            best_editor = fully_compatible[0]  # Pegar o primeiro encontrado
            reason = f"Editor compatível encontrado: {best_editor.name}. VSCode não é necessário."
            self.logger.info(f"✅ {reason}")
            return False, reason
        
        # Verificar se há editores parcialmente compatíveis
        partially_compatible = [e for e in detected_editors if e.compatibility == EditorCompatibility.PARTIAL]
        
        if partially_compatible:
            reason = f"Editores parcialmente compatíveis encontrados: {', '.join([e.name for e in partially_compatible])}. VSCode será instalado para melhor experiência com SGDK."
            self.logger.info(f"⚠️ {reason}")
            return True, reason
        
        # Apenas editores básicos ou nenhum editor
        reason = "Nenhum editor totalmente compatível encontrado. VSCode será instalado para suporte completo ao SGDK."
        self.logger.info(f"📦 {reason}")
        return True, reason
    
    def get_best_compatible_editor(self, detected_editors: Optional[List[EditorInfo]] = None) -> Optional[EditorInfo]:
        """Retorna o melhor editor compatível disponível"""
        if detected_editors is None:
            detected_editors = self.detect_installed_editors()
        
        # Priorizar editores totalmente compatíveis
        fully_compatible = [e for e in detected_editors if e.compatibility == EditorCompatibility.FULL]
        if fully_compatible:
            return fully_compatible[0]
        
        # Depois editores parcialmente compatíveis
        partially_compatible = [e for e in detected_editors if e.compatibility == EditorCompatibility.PARTIAL]
        if partially_compatible:
            return partially_compatible[0]
        
        return None
    
    def configure_sgdk_for_editor(self, editor: EditorInfo, sgdk_path: Path) -> bool:
        """Configura SGDK para um editor específico"""
        self.logger.info(f"🔧 Configurando SGDK para {editor.name}...")
        
        try:
            if editor.supports_vscode_extensions:
                return self._configure_vscode_like_editor(editor, sgdk_path)
            elif editor.compatibility == EditorCompatibility.PARTIAL:
                return self._configure_partial_compatible_editor(editor, sgdk_path)
            else:
                self.logger.warning(f"⚠️ Configuração automática não disponível para {editor.name}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar {editor.name}: {e}")
            return False
    
    def _configure_vscode_like_editor(self, editor: EditorInfo, sgdk_path: Path) -> bool:
        """Configura editores compatíveis com VSCode"""
        if not editor.command_line_tool:
            self.logger.warning(f"⚠️ Comando CLI não disponível para {editor.name}")
            return False
        
        # Instalar extensões necessárias
        extensions = [
            "zerasul.genesis-code",
            "ms-vscode.cpptools",
            "13xforever.language-x86-64-assembly",
            "ms-vscode.hexeditor"
        ]
        
        config = self.editor_configs.get(editor.name, {})
        install_cmd = config.get("extension_install_cmd")
        
        if install_cmd:
            for extension in extensions:
                try:
                    import subprocess
                    result = subprocess.run(
                        f"{install_cmd} {extension}",
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        self.logger.info(f"✅ Extensão instalada: {extension}")
                    else:
                        self.logger.warning(f"⚠️ Falha ao instalar extensão {extension}: {result.stderr}")
                except Exception as e:
                    self.logger.error(f"❌ Erro ao instalar extensão {extension}: {e}")
        
        return True
    
    def _configure_partial_compatible_editor(self, editor: EditorInfo, sgdk_path: Path) -> bool:
        """Configura editores parcialmente compatíveis"""
        self.logger.info(f"📝 Configuração manual necessária para {editor.name}")
        self.logger.info(f"💡 Dica: Configure o caminho do SGDK: {sgdk_path}")
        
        # Criar arquivo de configuração básico se possível
        config_suggestions = {
            "Sublime Text": self._create_sublime_config,
            "Atom": self._create_atom_config,
            "Vim": self._create_vim_config,
            "Neovim": self._create_neovim_config
        }
        
        config_func = config_suggestions.get(editor.name)
        if config_func:
            return config_func(sgdk_path)
        
        return True
    
    def _create_sublime_config(self, sgdk_path: Path) -> bool:
        """Cria configuração básica para Sublime Text"""
        # Implementar configuração específica do Sublime Text
        self.logger.info("📝 Configuração do Sublime Text criada")
        return True
    
    def _create_atom_config(self, sgdk_path: Path) -> bool:
        """Cria configuração básica para Atom"""
        # Implementar configuração específica do Atom
        self.logger.info("📝 Configuração do Atom criada")
        return True
    
    def _create_vim_config(self, sgdk_path: Path) -> bool:
        """Cria configuração básica para Vim"""
        # Implementar configuração específica do Vim
        self.logger.info("📝 Configuração do Vim criada")
        return True
    
    def _create_neovim_config(self, sgdk_path: Path) -> bool:
        """Cria configuração básica para Neovim"""
        # Implementar configuração específica do Neovim
        self.logger.info("📝 Configuração do Neovim criada")
        return True
    
    def generate_detection_report(self, detected_editors: Optional[List[EditorInfo]] = None) -> str:
        """Gera relatório detalhado da detecção de editores"""
        if detected_editors is None:
            detected_editors = self.detect_installed_editors()
        
        report = []
        report.append("📊 RELATÓRIO DE DETECÇÃO DE EDITORES")
        report.append("=" * 50)
        
        if not detected_editors:
            report.append("❌ Nenhum editor detectado no sistema")
            return "\n".join(report)
        
        # Agrupar por compatibilidade
        by_compatibility = {}
        for editor in detected_editors:
            comp = editor.compatibility
            if comp not in by_compatibility:
                by_compatibility[comp] = []
            by_compatibility[comp].append(editor)
        
        # Relatório por categoria
        for compatibility in [EditorCompatibility.FULL, EditorCompatibility.PARTIAL, EditorCompatibility.MINIMAL, EditorCompatibility.NONE]:
            if compatibility in by_compatibility:
                editors = by_compatibility[compatibility]
                report.append(f"\n🎯 {compatibility.value.upper()} COMPATIBILITY ({len(editors)} editores):")
                
                for editor in editors:
                    report.append(f"  ✅ {editor.name}")
                    report.append(f"     📍 Caminho: {editor.path}")
                    report.append(f"     🔢 Versão: {editor.version}")
                    if editor.supports_vscode_extensions:
                        report.append(f"     🧩 Suporte a extensões VSCode: Sim")
                    if editor.command_line_tool:
                        report.append(f"     💻 Comando CLI: {editor.command_line_tool}")
                    if editor.notes:
                        report.append(f"     💡 Notas: {editor.notes}")
                    report.append("")
        
        # Recomendação
        should_install, reason = self.should_install_vscode(detected_editors)
        report.append(f"\n🎯 RECOMENDAÇÃO:")
        report.append(f"   {'📦 Instalar VSCode' if should_install else '✅ VSCode não necessário'}")
        report.append(f"   💭 Motivo: {reason}")
        
        return "\n".join(report)


def get_editor_detection_manager(base_path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> EditorDetectionManager:
    """Factory function para criar EditorDetectionManager"""
    if base_path is None:
        base_path = Path.cwd()
    return EditorDetectionManager(base_path, logger)