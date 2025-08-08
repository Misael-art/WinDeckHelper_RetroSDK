#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para verificar se o splash screen está funcionando no main.py
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
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    from env_dev.gui.splash_screen import AnimatedSplashScreen
    print("✅ Importações bem-sucedidas!")
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    sys.exit(1)

def test_splash_integration():
    """Testa a integração do splash screen como no main.py"""
    print("🚀 Testando integração do splash screen...")
    
    app = QApplication(sys.argv)
    
    # Simular o que acontece no main.py
    splash = None
    try:
        splash = AnimatedSplashScreen()
        splash.show()
        print("✅ Splash screen criado e exibido!")
        
        # Simular as etapas de carregamento
        splash.update_status("Carregando componentes...")
        splash.update_progress(25)
        print("✅ Status atualizado: Carregando componentes...")
        
        app.processEvents()
        
        splash.update_progress(50)
        splash.update_status("Configurando interface...")
        print("✅ Status atualizado: Configurando interface...")
        
        app.processEvents()
        
        splash.update_progress(80)
        splash.update_status("Inicializando aplicação...")
        print("✅ Status atualizado: Inicializando aplicação...")
        
        app.processEvents()
        
        splash.update_progress(100)
        splash.update_status("Carregamento concluído!")
        print("✅ Status atualizado: Carregamento concluído!")
        
        app.processEvents()
        
        # Aguardar um pouco antes de fechar
        def close_splash():
            print("🎉 Fechando splash screen...")
            if hasattr(splash, 'fade_out'):
                splash.fade_out()
            else:
                splash.close()
            app.quit()
        
        QTimer.singleShot(3000, close_splash)
        
        print("🎯 Splash screen deve estar visível agora por 3 segundos...")
        app.exec_()
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        if splash:
            splash.close()
        app.quit()
        return False
    
    print("✅ Teste concluído com sucesso!")
    return True

if __name__ == "__main__":
    print("🧪 Iniciando teste do splash screen...")
    success = test_splash_integration()
    if success:
        print("\n🎉 Teste bem-sucedido! O splash screen está funcionando.")
    else:
        print("\n❌ Teste falhou. Verifique os logs acima.")
        sys.exit(1)