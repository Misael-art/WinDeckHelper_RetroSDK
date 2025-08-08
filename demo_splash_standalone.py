#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo standalone da Splash Screen - Executa apenas a splash screen
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    from gui.splash_screen import AnimatedSplashScreen
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)

def main():
    """Demo da splash screen standalone"""
    app = QApplication(sys.argv)
    
    # Criar splash screen
    splash = AnimatedSplashScreen()
    splash.show()
    
    # Configurar timer para fechar após demonstração
    def close_splash():
        print("\n🎉 Demo da Splash Screen concluída!")
        print("\nCaracterísticas implementadas:")
        print("✅ Animação de fade in/out")
        print("✅ Barra de progresso com gradiente")
        print("✅ Status de carregamento dinâmico")
        print("✅ Design moderno com tema escuro")
        print("✅ Animação de pontos no texto")
        print("✅ Logo/ícone decorativo")
        print("✅ Informações de versão")
        print("\nA splash screen está integrada na aplicação principal!")
        splash.close()
        app.quit()
    
    # Fechar após o carregamento completo (simulado pelo worker thread)
    splash.worker.finished.connect(lambda: QTimer.singleShot(2000, close_splash))
    
    return app.exec_()

if __name__ == "__main__":
    print("🚀 Iniciando demo da Splash Screen...")
    print("📱 A splash screen será exibida por alguns segundos")
    print("⏳ Aguarde o carregamento completo...\n")
    
    sys.exit(main())