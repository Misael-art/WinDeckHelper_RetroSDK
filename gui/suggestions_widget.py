#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de Sugestões Inteligentes para PyQt5

Este módulo implementa a interface gráfica para exibir sugestões
inteligentes de componentes baseadas em aplicações detectadas.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import logging

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QListWidget, QListWidgetItem, QTextEdit, QProgressBar,
        QGroupBox, QFrame, QLineEdit, QComboBox, QCheckBox,
        QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
        QSpacerItem, QSizePolicy, QMessageBox, QTabWidget,
        QScrollArea, QGridLayout
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
except ImportError:
    # Fallback para evitar erros de importação
    class QWidget: pass
    class QVBoxLayout: pass
    class QThread: pass
    class pyqtSignal:
        def __init__(self, *args): pass

try:
    from env_dev.core.suggestion_service import SuggestionService, create_suggestion_service
    from env_dev.core.intelligent_suggestions import EnhancedSuggestion, SuggestionContext
    from env_dev.core.component_matcher import ComponentMatch
    from env_dev.core.detection_engine import DetectedApplication
except ImportError as e:
    print(f"Erro ao importar módulos de sugestões: {e}")
    # Fallback classes
    class SuggestionService: pass
    class EnhancedSuggestion: pass
    class SuggestionContext: pass
    class ComponentMatch: pass
    class DetectedApplication: pass
    def create_suggestion_service(*args): return None


class SuggestionCard(QFrame):
    """Card individual para exibir uma sugestão."""
    
    install_requested = pyqtSignal(str)  # component_name
    details_requested = pyqtSignal(str)  # component_name
    
    def __init__(self, suggestion: EnhancedSuggestion, parent=None):
        super().__init__(parent)
        self.suggestion = suggestion
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do card."""
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #007bff;
                background-color: #e3f2fd;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header com nome e confiança
        header_layout = QHBoxLayout()
        
        # Nome do componente
        name_label = QLabel(self.suggestion.component_name)
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setStyleSheet("color: #212529; background: transparent; border: none;")
        header_layout.addWidget(name_label)
        
        # Badge de confiança
        confidence_badge = self.create_confidence_badge()
        header_layout.addWidget(confidence_badge)
        
        # Badge de categoria
        category_badge = self.create_category_badge()
        header_layout.addWidget(category_badge)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Descrição/Reasoning
        if self.suggestion.reasoning:
            reasoning_label = QLabel(self.suggestion.reasoning)
            reasoning_label.setWordWrap(True)
            reasoning_label.setStyleSheet("""
                color: #6c757d;
                font-size: 10px;
                background: transparent;
                border: none;
                padding: 4px;
            """)
            layout.addWidget(reasoning_label)
        
        # Tags
        if self.suggestion.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            
            for tag in self.suggestion.tags[:3]:  # Máximo 3 tags
                tag_label = QLabel(f"#{tag}")
                tag_label.setStyleSheet("""
                    background-color: #e9ecef;
                    color: #495057;
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 9px;
                    border: none;
                """)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        install_btn = QPushButton("Instalar")
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        install_btn.clicked.connect(lambda: self.install_requested.emit(self.suggestion.component_name))
        buttons_layout.addWidget(install_btn)
        
        details_btn = QPushButton("Detalhes")
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        details_btn.clicked.connect(lambda: self.details_requested.emit(self.suggestion.component_name))
        buttons_layout.addWidget(details_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def create_confidence_badge(self) -> QLabel:
        """Cria badge de confiança."""
        confidence = self.suggestion.confidence
        
        if confidence >= 0.8:
            color = "#28a745"  # Verde
            text = "Alta"
        elif confidence >= 0.6:
            color = "#ffc107"  # Amarelo
            text = "Média"
        else:
            color = "#dc3545"  # Vermelho
            text = "Baixa"
        
        badge = QLabel(f"{text} ({confidence:.0%})")
        badge.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 9px;
            font-weight: bold;
            border: none;
        """)
        return badge
    
    def create_category_badge(self) -> QLabel:
        """Cria badge de categoria."""
        category_colors = {
            "development": "#17a2b8",
            "runtime": "#6f42c1",
            "tool": "#fd7e14",
            "system": "#20c997",
            "unknown": "#6c757d"
        }
        
        color = category_colors.get(self.suggestion.category.lower(), "#6c757d")
        
        badge = QLabel(self.suggestion.category.title())
        badge.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 8px;
            padding: 2px 6px;
            font-size: 9px;
            border: none;
        """)
        return badge


class SuggestionsWorker(QThread):
    """Worker thread para carregar sugestões."""
    
    suggestions_loaded = pyqtSignal(list)  # List[EnhancedSuggestion]
    error_occurred = pyqtSignal(str)  # error message
    progress_updated = pyqtSignal(str, int)  # message, percentage
    
    def __init__(self, suggestion_service: SuggestionService):
        super().__init__()
        self.suggestion_service = suggestion_service
        self.should_stop = False
    
    def run(self):
        """Executa o carregamento de sugestões."""
        try:
            self.progress_updated.emit("Inicializando serviço de sugestões...", 10)
            
            if self.should_stop:
                return
            
            # Inicializa o serviço
            asyncio.run(self.suggestion_service.initialize())
            
            if self.should_stop:
                return
            
            self.progress_updated.emit("Detectando aplicações instaladas...", 30)
            
            # Atualiza cache de detecção
            asyncio.run(self.suggestion_service.refresh_detection_cache())
            
            if self.should_stop:
                return
            
            self.progress_updated.emit("Gerando sugestões inteligentes...", 70)
            
            # Obtém sugestões
            suggestions = self.suggestion_service.get_component_suggestions(force_refresh=True)
            
            if self.should_stop:
                return
            
            self.progress_updated.emit("Finalizando...", 100)
            self.suggestions_loaded.emit(suggestions)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Para a execução do worker."""
        self.should_stop = True


class SuggestionsWidget(QWidget):
    """Widget principal para exibir sugestões inteligentes."""
    
    install_component = pyqtSignal(str)  # component_name
    show_component_details = pyqtSignal(str)  # component_name
    
    def __init__(self, suggestion_service: Optional[SuggestionService] = None, parent=None):
        super().__init__(parent)
        self.suggestion_service = suggestion_service
        self.suggestions: List[EnhancedSuggestion] = []
        self.filtered_suggestions: List[EnhancedSuggestion] = []
        self.suggestion_cards: List[SuggestionCard] = []
        self.worker: Optional[SuggestionsWorker] = None
        
        self.setup_ui()
        
        if self.suggestion_service:
            self.load_suggestions()
    
    def setup_ui(self):
        """Configura a interface do widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 Sugestões Inteligentes")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #212529; margin-bottom: 8px;")
        header_layout.addWidget(title)
        
        # Botão de atualizar
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_suggestions)
        header_layout.addWidget(refresh_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        # Campo de busca
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Buscar sugestões...")
        self.search_field.textChanged.connect(self.filter_suggestions)
        filters_layout.addWidget(self.search_field)
        
        # Filtro por categoria
        self.category_filter = QComboBox()
        self.category_filter.addItems(["Todas", "Development", "Runtime", "Tool", "System"])
        self.category_filter.currentTextChanged.connect(self.filter_suggestions)
        filters_layout.addWidget(self.category_filter)
        
        # Filtro por confiança
        self.confidence_filter = QComboBox()
        self.confidence_filter.addItems(["Todas", "Alta (80%+)", "Média (60%+)", "Baixa (<60%)"])
        self.confidence_filter.currentTextChanged.connect(self.filter_suggestions)
        filters_layout.addWidget(self.confidence_filter)
        
        # Checkbox para mostrar apenas essenciais
        self.essentials_only = QCheckBox("Apenas Essenciais")
        self.essentials_only.toggled.connect(self.filter_suggestions)
        filters_layout.addWidget(self.essentials_only)
        
        layout.addLayout(filters_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Carregando sugestões...")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Área de scroll para as sugestões
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget container para as sugestões
        self.suggestions_container = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_layout.setSpacing(8)
        self.suggestions_layout.addStretch()
        
        scroll_area.setWidget(self.suggestions_container)
        layout.addWidget(scroll_area)
        
        # Estatísticas no rodapé
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #6c757d; font-size: 10px; padding: 4px;")
        layout.addWidget(self.stats_label)
    
    def set_suggestion_service(self, service: SuggestionService):
        """Define o serviço de sugestões."""
        self.suggestion_service = service
        self.load_suggestions()
    
    def load_suggestions(self):
        """Carrega sugestões usando worker thread."""
        if not self.suggestion_service:
            self.status_label.setText("❌ Serviço de sugestões não disponível")
            return
        
        # Para worker anterior se existir
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        # Cria novo worker
        self.worker = SuggestionsWorker(self.suggestion_service)
        self.worker.suggestions_loaded.connect(self.on_suggestions_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.progress_updated.connect(self.on_progress_updated)
        
        # Mostra progresso
        self.progress_bar.setVisible(True)
        self.status_label.setText("Carregando sugestões...")
        
        # Inicia worker
        self.worker.start()
    
    def refresh_suggestions(self):
        """Atualiza as sugestões."""
        self.clear_suggestions()
        self.load_suggestions()
    
    def on_suggestions_loaded(self, suggestions: List[EnhancedSuggestion]):
        """Callback quando sugestões são carregadas."""
        self.suggestions = suggestions
        self.filtered_suggestions = suggestions.copy()
        
        self.progress_bar.setVisible(False)
        self.display_suggestions()
        self.update_stats()
        
        if suggestions:
            self.status_label.setText(f"✅ {len(suggestions)} sugestões carregadas")
        else:
            self.status_label.setText("ℹ️ Nenhuma sugestão encontrada")
    
    def on_error(self, error_message: str):
        """Callback quando ocorre erro."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ Erro: {error_message}")
        
        # Mostra dialog de erro
        QMessageBox.warning(self, "Erro", f"Erro ao carregar sugestões:\n{error_message}")
    
    def on_progress_updated(self, message: str, percentage: int):
        """Callback para atualização de progresso."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
    
    def display_suggestions(self):
        """Exibe as sugestões na interface."""
        self.clear_suggestions()
        
        if not self.filtered_suggestions:
            no_suggestions_label = QLabel("🤷 Nenhuma sugestão encontrada com os filtros atuais")
            no_suggestions_label.setAlignment(Qt.AlignCenter)
            no_suggestions_label.setStyleSheet("""
                color: #6c757d;
                font-size: 14px;
                padding: 40px;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
            """)
            self.suggestions_layout.insertWidget(0, no_suggestions_label)
            return
        
        # Ordena sugestões por confiança e prioridade
        sorted_suggestions = sorted(
            self.filtered_suggestions,
            key=lambda s: (s.confidence, s.priority),
            reverse=True
        )
        
        # Cria cards para cada sugestão
        for suggestion in sorted_suggestions:
            card = SuggestionCard(suggestion)
            card.install_requested.connect(self.install_component.emit)
            card.details_requested.connect(self.show_component_details.emit)
            
            self.suggestion_cards.append(card)
            self.suggestions_layout.insertWidget(-1, card)  # Insere antes do stretch
    
    def clear_suggestions(self):
        """Limpa as sugestões exibidas."""
        # Remove todos os cards
        for card in self.suggestion_cards:
            card.setParent(None)
            card.deleteLater()
        
        self.suggestion_cards.clear()
        
        # Remove outros widgets (exceto stretch)
        for i in reversed(range(self.suggestions_layout.count() - 1)):
            item = self.suggestions_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
    
    def filter_suggestions(self):
        """Filtra sugestões baseado nos critérios selecionados."""
        if not self.suggestions:
            return
        
        filtered = self.suggestions.copy()
        
        # Filtro por texto
        search_text = self.search_field.text().lower().strip()
        if search_text:
            filtered = [
                s for s in filtered
                if (search_text in s.component_name.lower() or
                    search_text in s.reasoning.lower() or
                    any(search_text in tag.lower() for tag in s.tags))
            ]
        
        # Filtro por categoria
        category = self.category_filter.currentText()
        if category != "Todas":
            filtered = [s for s in filtered if s.category.lower() == category.lower()]
        
        # Filtro por confiança
        confidence = self.confidence_filter.currentText()
        if confidence == "Alta (80%+)":
            filtered = [s for s in filtered if s.confidence >= 0.8]
        elif confidence == "Média (60%+)":
            filtered = [s for s in filtered if 0.6 <= s.confidence < 0.8]
        elif confidence == "Baixa (<60%)":
            filtered = [s for s in filtered if s.confidence < 0.6]
        
        # Filtro por essenciais
        if self.essentials_only.isChecked():
            filtered = [s for s in filtered if "essential" in s.tags]
        
        self.filtered_suggestions = filtered
        self.display_suggestions()
        self.update_stats()
    
    def update_stats(self):
        """Atualiza estatísticas exibidas."""
        total = len(self.suggestions)
        filtered = len(self.filtered_suggestions)
        
        if total == 0:
            self.stats_label.setText("")
            return
        
        high_confidence = len([s for s in self.filtered_suggestions if s.confidence >= 0.8])
        essentials = len([s for s in self.filtered_suggestions if "essential" in s.tags])
        
        stats_text = f"📊 Exibindo {filtered} de {total} sugestões | "
        stats_text += f"🎯 {high_confidence} alta confiança | "
        stats_text += f"⭐ {essentials} essenciais"
        
        self.stats_label.setText(stats_text)
    
    def get_suggestions_summary(self) -> Dict[str, Any]:
        """Obtém resumo das sugestões para relatórios."""
        if not self.suggestions:
            return {}
        
        categories = {}
        confidence_levels = {"high": 0, "medium": 0, "low": 0}
        
        for suggestion in self.suggestions:
            # Conta por categoria
            category = suggestion.category
            categories[category] = categories.get(category, 0) + 1
            
            # Conta por nível de confiança
            if suggestion.confidence >= 0.8:
                confidence_levels["high"] += 1
            elif suggestion.confidence >= 0.6:
                confidence_levels["medium"] += 1
            else:
                confidence_levels["low"] += 1
        
        return {
            "total_suggestions": len(self.suggestions),
            "categories": categories,
            "confidence_levels": confidence_levels,
            "essentials_count": len([s for s in self.suggestions if "essential" in s.tags]),
            "top_suggestions": [
                {
                    "component_name": s.component_name,
                    "confidence": s.confidence,
                    "category": s.category,
                    "reasoning": s.reasoning[:100] + "..." if len(s.reasoning) > 100 else s.reasoning
                }
                for s in sorted(self.suggestions, key=lambda x: x.confidence, reverse=True)[:5]
            ]
        }
    
    def closeEvent(self, event):
        """Cleanup ao fechar o widget."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()