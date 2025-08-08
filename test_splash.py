#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para demonstrar a Splash Screen
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
parent_dir = project_root.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt5.QtCore import QTimer
    from env_dev.gui.splash_screen import AnimatedSplashScreen
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)

class TestMainWindow(QMainWindow):
    """Janela principal de teste"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Environment Dev Script - Teste Splash Screen")
        self.setGeometry(200, 200, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Label de boas-vindas
        welcome_label = QLabel("🎉 Splash Screen carregada com sucesso!")
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #0078d4;
                text-align: center;
                padding: 50px;
            }
        """)
        
        info_label = QLabel("""
        A Splash Screen foi implementada com as seguintes características:
        
        ✅ Animação de fade in/out
        ✅ Barra de progresso animada
        ✅ Status de carregamento dinâmico
        ✅ Design moderno com gradientes
        ✅ Integração com a aplicação principal
        ✅ Animação de pontos no texto de status
        
        A splash screen é exibida automaticamente durante a inicialização
        da aplicação principal e desaparece quando o carregamento é concluído.
        """)
        
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                line-height: 1.6;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        
        layout.addWidget(welcome_label)
        layout.addWidget(info_label)

def main():
    """Função principal de teste"""
    app = QApplication(sys.argv)
    
    # Criar e exibir splash screen
    splash = AnimatedSplashScreen()
    splash.show()
    app.processEvents()
    
    # Simular carregamento
    splash.update_status("Inicializando teste...")
    splash.update_progress(25)
    app.processEvents()
    
    # Criar janela principal
    main_window = TestMainWindow()
    
    # Simular mais carregamento
    splash.update_status("Preparando interface...")
    splash.update_progress(75)
    app.processEvents()
    
    # Finalizar splash e mostrar janela principal
    splash.update_progress(100)
    splash.update_status("Carregamento concluído!")
    app.processEvents()
    
    # Aguardar e fechar splash
    def show_main_window():
        if hasattr(splash, 'fade_out'):
            splash.fade_out()
        else:
            splash.close()
        main_window.show()
    
    QTimer.singleShot(2000, show_main_window)
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())