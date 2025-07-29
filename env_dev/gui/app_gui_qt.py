#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Gráfica do Environment Dev Script usando PyQt5
Alternativa ao Tkinter para resolver problemas de compatibilidade
"""

import sys
import os
import time
import traceback
from pathlib import Path
from typing import List, Dict

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QListWidget, QListWidgetItem, QTextEdit, QProgressBar,
        QTabWidget, QGroupBox, QCheckBox, QMessageBox, QSplitter,
        QTreeWidget, QTreeWidgetItem, QHeaderView, QFrame, QLineEdit,
        QSpacerItem, QSizePolicy
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
    PYQT_AVAILABLE = True
    print("PyQt5 importado com sucesso")
except ImportError as e:
    print(f"PyQt5 não disponível: {e}")
    PYQT_AVAILABLE = False
    # Fallback para evitar erros de importação
    class QMainWindow: pass
    class QWidget: pass
    class QVBoxLayout: pass
    class QThread: pass
    class pyqtSignal:
        def __init__(self, *args): pass
except Exception as e:
    print(f"Erro ao importar PyQt5: {e}")
    PYQT_AVAILABLE = False
    # Fallback para evitar erros de importação
    class QMainWindow: pass
    class QWidget: pass
    class QVBoxLayout: pass
    class QThread: pass
    class pyqtSignal:
        def __init__(self, *args): pass

# Ajusta o path para encontrar os módulos
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from env_dev.config.loader import load_all_components
    from env_dev.core import installer
    from env_dev.core.installer import _verify_installation
    from env_dev.utils.log_manager import setup_logging
except Exception as e:
    print(f"Erro ao importar módulos: {e}")
    traceback.print_exc()

class InstallationWorker(QThread):
    """Worker thread para instalações em background"""
    progress_updated = pyqtSignal(str, int)  # message, progress
    installation_finished = pyqtSignal(str, bool)  # component, success
    log_message = pyqtSignal(str, str)  # level, message
    
    def __init__(self, components_to_install: List[str], components_data: Dict):
        super().__init__()
        self.components_to_install = components_to_install
        self.components_data = components_data
        self.should_stop = False
    
    def run(self):
        """Executa as instalações"""
        try:
            total_components = len(self.components_to_install)
            
            for i, component_name in enumerate(self.components_to_install):
                if self.should_stop:
                    break
                    
                progress = int((i / total_components) * 100)
                self.progress_updated.emit(f"Instalando {component_name}...", progress)
                
                try:
                    # Simula instalação (substitua pela lógica real)
                    component_data = self.components_data.get(component_name)
                    if component_data:
                        # Chamada real de instalação
                        from env_dev.core import installer
                        try:
                            result = installer.install_component(component_name, component_data, self.components_data)
                        except Exception as e:
                            print(f"Erro na instalação de {component_name}: {e}")
                            result = False
                        
                        self.installation_finished.emit(component_name, result)
                        self.log_message.emit("INFO", f"Componente {component_name} instalado com sucesso")
                    else:
                        self.installation_finished.emit(component_name, False)
                        self.log_message.emit("ERROR", f"Componente {component_name} não encontrado")
                        
                except Exception as e:
                    self.installation_finished.emit(component_name, False)
                    self.log_message.emit("ERROR", f"Erro ao instalar {component_name}: {str(e)}")
            
            self.progress_updated.emit("Instalação concluída", 100)
            
        except Exception as e:
            self.log_message.emit("ERROR", f"Erro geral na instalação: {str(e)}")
    
    def stop(self):
        """Para a instalação"""
        self.should_stop = True

class EnvironmentDevGUI(QMainWindow):
    """Interface gráfica principal usando PyQt5"""
    
    def __init__(self, components_data=None):
        super().__init__()
        self.components_data = components_data or {}
        self.installation_worker = None
        self.logger = None
        
        # Configura logging
        self.setup_logging()
        
        # Carrega componentes se não foram fornecidos
        if not self.components_data:
            self.load_components()
        
        # Configura a interface
        self.setup_ui()
        
        # Configura tema escuro
        self.setup_dark_theme()
        
    def setup_logging(self):
        """Configura o sistema de logging"""
        try:
            self.logger, _ = setup_logging()
            self.logger.info("GUI PyQt5 inicializada")
        except Exception as e:
            print(f"Erro ao configurar logging: {e}")
    
    def load_components(self):
        """Carrega os componentes disponíveis"""
        try:
            self.components_data = load_all_components()
            if self.logger:
                self.logger.info(f"Carregados {len(self.components_data)} componentes")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao carregar componentes: {e}")
            else:
                print(f"Erro ao carregar componentes: {e}")
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        self.setWindowTitle("Environment Dev Script - PyQt5")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Painel esquerdo - Lista de componentes
        self.setup_components_panel(splitter)
        
        # Painel direito - Logs e controles
        self.setup_control_panel(splitter)
        
        # Configura proporções do splitter
        splitter.setSizes([400, 800])
    
    def setup_components_panel(self, parent):
        """Configura o painel de componentes"""
        components_widget = QWidget()
        layout = QVBoxLayout(components_widget)
        
        # Título
        title = QLabel("Componentes Disponíveis")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Campo de busca
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Buscar componentes...")
        self.search_field.textChanged.connect(self.filter_components)
        layout.addWidget(self.search_field)
        
        # Lista de componentes
        self.components_list = QListWidget()
        self.components_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.components_list)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.install_button = QPushButton("Instalar Selecionados")
        self.install_button.clicked.connect(self.install_selected)
        buttons_layout.addWidget(self.install_button)
        
        self.verify_button = QPushButton("Verificar Instalados")
        self.verify_button.clicked.connect(self.verify_installations)
        buttons_layout.addWidget(self.verify_button)
        
        layout.addLayout(buttons_layout)
        
        # Popula a lista
        self.populate_components_list()
        
        parent.addWidget(components_widget)
    
    def setup_control_panel(self, parent):
        """Configura o painel de controle"""
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        
        # Abas
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Aba de logs
        self.setup_logs_tab(tabs)
        
        # Aba de progresso
        self.setup_progress_tab(tabs)
        
        # Aba de configurações
        self.setup_settings_tab(tabs)
        
        parent.addWidget(control_widget)
    
    def setup_logs_tab(self, tabs):
        """Configura a aba de logs"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Área de logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Botões de controle de logs
        log_buttons = QHBoxLayout()
        
        clear_logs_btn = QPushButton("Limpar Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        log_buttons.addWidget(clear_logs_btn)
        
        save_logs_btn = QPushButton("Salvar Logs")
        save_logs_btn.clicked.connect(self.save_logs)
        log_buttons.addWidget(save_logs_btn)
        
        layout.addLayout(log_buttons)
        
        tabs.addTab(logs_widget, "Logs")
    
    def setup_progress_tab(self, tabs):
        """Configura a aba de progresso"""
        progress_widget = QWidget()
        layout = QVBoxLayout(progress_widget)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Label de status
        self.status_label = QLabel("Pronto")
        layout.addWidget(self.status_label)
        
        # Botão de cancelar
        self.cancel_button = QPushButton("Cancelar Instalação")
        self.cancel_button.clicked.connect(self.cancel_installation)
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        tabs.addTab(progress_widget, "Progresso")
    
    def setup_settings_tab(self, tabs):
        """Configura a aba de configurações"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Configurações gerais
        general_group = QGroupBox("Configurações Gerais")
        general_layout = QVBoxLayout(general_group)
        
        self.auto_verify_checkbox = QCheckBox("Verificar automaticamente após instalação")
        self.auto_verify_checkbox.setChecked(True)
        general_layout.addWidget(self.auto_verify_checkbox)
        
        self.show_details_checkbox = QCheckBox("Mostrar detalhes de instalação")
        self.show_details_checkbox.setChecked(True)
        general_layout.addWidget(self.show_details_checkbox)
        
        layout.addWidget(general_group)
        
        # Espaçador
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        tabs.addTab(settings_widget, "Configurações")
    
    def setup_dark_theme(self):
        """Configura tema escuro"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                selection-background-color: #0078d4;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 2px;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def populate_components_list(self):
        """Popula a lista de componentes"""
        self.components_list.clear()
        
        # Agrupa por categoria
        categories = {}
        for name, data in self.components_data.items():
            category = data.get('category', 'Outros')
            if category not in categories:
                categories[category] = []
            categories[category].append((name, data))
        
        # Adiciona itens agrupados
        for category in sorted(categories.keys()):
            # Adiciona cabeçalho da categoria
            category_item = QListWidgetItem(f"--- {category} ---")
            category_item.setFlags(Qt.NoItemFlags)  # Não selecionável
            category_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.components_list.addItem(category_item)
            
            # Adiciona componentes da categoria
            for name, data in sorted(categories[category]):
                description = data.get('description', 'Sem descrição')
                item_text = f"  {name} - {description}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, name)  # Armazena o nome real
                self.components_list.addItem(item)
    
    def filter_components(self, text):
        """Filtra componentes baseado no texto de busca"""
        for i in range(self.components_list.count()):
            item = self.components_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def install_selected(self):
        """Instala os componentes selecionados"""
        selected_items = self.components_list.selectedItems()
        components_to_install = []
        
        for item in selected_items:
            component_name = item.data(Qt.UserRole)
            if component_name:  # Ignora cabeçalhos de categoria
                components_to_install.append(component_name)
        
        if not components_to_install:
            QMessageBox.warning(self, "Aviso", "Nenhum componente selecionado para instalação.")
            return
        
        # Confirma instalação
        reply = QMessageBox.question(
            self, "Confirmar Instalação",
            f"Deseja instalar {len(components_to_install)} componente(s)?\n\n" +
            "\n".join(components_to_install),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_installation(components_to_install)
    
    def start_installation(self, components_to_install):
        """Inicia o processo de instalação"""
        self.install_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Cria e inicia worker thread
        self.installation_worker = InstallationWorker(components_to_install, self.components_data)
        self.installation_worker.progress_updated.connect(self.update_progress)
        self.installation_worker.installation_finished.connect(self.on_installation_finished)
        self.installation_worker.log_message.connect(self.add_log_message)
        self.installation_worker.finished.connect(self.on_installation_complete)
        self.installation_worker.start()
    
    def update_progress(self, message, progress):
        """Atualiza o progresso da instalação"""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)
        self.add_log_message("INFO", message)
    
    def on_installation_finished(self, component, success):
        """Callback quando uma instalação individual termina"""
        status = "sucesso" if success else "falha"
        self.add_log_message("INFO", f"Instalação de {component}: {status}")
    
    def on_installation_complete(self):
        """Callback quando todas as instalações terminam"""
        self.install_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Instalação concluída")
        self.add_log_message("INFO", "Todas as instalações foram concluídas")
    
    def cancel_installation(self):
        """Cancela a instalação em andamento"""
        if self.installation_worker and self.installation_worker.isRunning():
            self.installation_worker.stop()
            self.installation_worker.wait()
            self.add_log_message("WARNING", "Instalação cancelada pelo usuário")
            self.on_installation_complete()
    
    def verify_installations(self):
        """Verifica quais componentes estão instalados"""
        self.add_log_message("INFO", "Iniciando verificação de instalações...")
        # Aqui você implementaria a lógica de verificação
        # Por enquanto, apenas simula
        QMessageBox.information(self, "Verificação", "Funcionalidade de verificação será implementada.")
    
    def add_log_message(self, level, message):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll para o final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Limpa os logs"""
        self.log_text.clear()
    
    def save_logs(self):
        """Salva os logs em arquivo"""
        # Implementar salvamento de logs
        QMessageBox.information(self, "Salvar Logs", "Funcionalidade de salvamento será implementada.")
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if self.installation_worker and self.installation_worker.isRunning():
            reply = QMessageBox.question(
                self, "Fechar Aplicação",
                "Há uma instalação em andamento. Deseja cancelar e fechar?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.installation_worker.stop()
                self.installation_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main(components_data=None):
    """Função principal para inicializar a interface PyQt5"""
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt5 não está disponível")
    
    app = QApplication(sys.argv)
    
    # Se não foram fornecidos dados de componentes, carrega dados de exemplo
    if components_data is None:
        components_data = {
            "Git": {
                "name": "Git",
                "description": "Sistema de controle de versão distribuído",
                "category": "Version Control",
                "installed": False
            },
            "Python": {
                "name": "Python",
                "description": "Linguagem de programação",
                "category": "Development Tools",
                "installed": True
            }
        }
    
    window = EnvironmentDevGUI(components_data)
    window.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())