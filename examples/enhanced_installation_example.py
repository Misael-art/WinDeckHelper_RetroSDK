#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Integração do Sistema de Progresso Aprimorado
Demonstra como integrar o sistema de progresso detalhado com o instalador existente
"""

import sys
import os
import time
import threading
from typing import Dict, Any

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_progress import (
    create_progress_tracker, OperationStage, DetailedProgress
)
from gui.realtime_installation_dashboard import create_installation_dashboard
from gui.enhanced_progress_widget import EnhancedProgressWidget

def enhanced_install_component(component_name: str, component_data: Dict[str, Any], 
                             progress_tracker=None) -> bool:
    """
    Versão aprimorada da instalação de componente com progresso detalhado
    
    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        progress_tracker: Tracker de progresso (opcional)
    
    Returns:
        bool: True se instalação foi bem-sucedida
    """
    
    # Cria tracker se não fornecido
    if not progress_tracker:
        progress_tracker = create_progress_tracker(
            f"install_{component_name}", 
            component_name, 
            total_steps=6
        )
    
    try:
        # Estágio 1: Preparação
        progress_tracker.update_stage(
            OperationStage.PREPARING,
            step_description="Verificando pré-requisitos..."
        )
        progress_tracker.update_step(1, "Validando dados do componente...")
        time.sleep(1)  # Simula validação
        
        # Verifica se componente tem URL de download
        download_url = component_data.get('download_url')
        if not download_url:
            progress_tracker.complete(False, "URL de download não encontrada")
            return False
        
        # Estágio 2: Download
        progress_tracker.update_stage(
            OperationStage.DOWNLOADING,
            step_description="Baixando arquivo..."
        )
        progress_tracker.update_step(2, f"Conectando a {download_url}...")
        
        # Simula download com progresso detalhado
        total_size = component_data.get('size', 1024 * 1024 * 5)  # 5MB padrão
        chunk_size = 1024 * 50  # 50KB chunks
        
        for downloaded in range(0, total_size, chunk_size):
            if progress_tracker.is_cancelled:
                progress_tracker.cancel("Download cancelado pelo usuário")
                return False
            
            current_downloaded = min(downloaded + chunk_size, total_size)
            progress_tracker.update_download_progress(current_downloaded, total_size)
            time.sleep(0.05)  # Simula tempo de download
        
        # Estágio 3: Extração
        progress_tracker.update_stage(
            OperationStage.EXTRACTING,
            step_description="Extraindo arquivos..."
        )
        progress_tracker.update_step(3, "Descompactando arquivo baixado...")
        
        # Simula extração
        for i in range(10):
            if progress_tracker.is_cancelled:
                progress_tracker.cancel("Extração cancelada")
                return False
            
            progress = 30 + (i * 7)  # 30% a 100%
            progress_tracker.update_custom_progress(
                progress, 
                f"Extraindo arquivo {i+1}/10..."
            )
            time.sleep(0.3)
        
        # Estágio 4: Instalação
        progress_tracker.update_stage(
            OperationStage.INSTALLING,
            step_description="Instalando componente..."
        )
        progress_tracker.update_step(4, "Copiando arquivos...")
        
        # Simula instalação
        install_steps = [
            "Criando diretórios...",
            "Copiando executáveis...",
            "Copiando bibliotecas...",
            "Criando atalhos...",
            "Registrando componente..."
        ]
        
        for i, step_desc in enumerate(install_steps):
            if progress_tracker.is_cancelled:
                progress_tracker.cancel("Instalação cancelada")
                return False
            
            progress = 40 + (i * 12)  # 40% a 88%
            progress_tracker.update_custom_progress(progress, step_desc)
            time.sleep(0.8)
        
        # Estágio 5: Configuração
        progress_tracker.update_stage(
            OperationStage.CONFIGURING,
            step_description="Configurando componente..."
        )
        progress_tracker.update_step(5, "Aplicando configurações...")
        
        # Simula configuração
        config_steps = [
            "Criando arquivos de configuração...",
            "Configurando variáveis de ambiente...",
            "Registrando serviços..."
        ]
        
        for i, step_desc in enumerate(config_steps):
            if progress_tracker.is_cancelled:
                progress_tracker.cancel("Configuração cancelada")
                return False
            
            progress = 88 + (i * 4)  # 88% a 100%
            progress_tracker.update_custom_progress(progress, step_desc)
            time.sleep(0.5)
        
        # Estágio 6: Verificação
        progress_tracker.update_stage(
            OperationStage.VERIFYING,
            step_description="Verificando instalação..."
        )
        progress_tracker.update_step(6, "Testando componente instalado...")
        
        # Simula verificação
        time.sleep(1)
        
        # Verifica se instalação foi bem-sucedida (simulado)
        success = component_data.get('install_success', True)
        
        if success:
            progress_tracker.complete(True, f"Componente {component_name} instalado com sucesso!")
            return True
        else:
            progress_tracker.complete(False, f"Falha na verificação do componente {component_name}")
            return False
    
    except Exception as e:
        progress_tracker.complete(False, f"Erro durante instalação: {str(e)}")
        return False

def simulate_batch_installation():
    """
    Simula instalação em lote de múltiplos componentes
    """
    
    # Componentes de exemplo
    components = {
        "Python 3.11": {
            "download_url": "https://python.org/downloads/python-3.11.exe",
            "size": 1024 * 1024 * 25,  # 25MB
            "install_success": True
        },
        "Node.js 18": {
            "download_url": "https://nodejs.org/dist/v18.0.0/node-v18.0.0-x64.msi",
            "size": 1024 * 1024 * 30,  # 30MB
            "install_success": True
        },
        "Git 2.40": {
            "download_url": "https://github.com/git-for-windows/git/releases/download/v2.40.0.windows.1/Git-2.40.0-64-bit.exe",
            "size": 1024 * 1024 * 45,  # 45MB
            "install_success": False  # Simula falha
        }
    }
    
    def install_worker(component_name: str, component_data: Dict[str, Any]):
        """Worker para instalação individual"""
        print(f"Iniciando instalação de {component_name}...")
        
        # Cria tracker para este componente
        tracker = create_progress_tracker(
            f"install_{component_name.replace(' ', '_').lower()}",
            component_name,
            total_steps=6
        )
        
        # Adiciona callback para logging
        def log_progress(progress: DetailedProgress):
            print(f"[{component_name}] {progress.stage.value}: {progress.progress_percent:.1f}% - {progress.current_step}")
            
            if progress.stage == OperationStage.DOWNLOADING and progress.total_bytes > 0:
                print(f"  Download: {progress.get_download_info()} @ {progress.format_speed()} (ETA: {progress.format_eta()})")
        
        tracker.add_callback(log_progress)
        
        # Executa instalação
        success = enhanced_install_component(component_name, component_data, tracker)
        
        if success:
            print(f"✅ {component_name} instalado com sucesso!")
        else:
            print(f"❌ Falha na instalação de {component_name}")
        
        return success
    
    # Inicia instalações em paralelo
    threads = []
    for component_name, component_data in components.items():
        thread = threading.Thread(
            target=install_worker,
            args=(component_name, component_data),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        
        # Pequeno delay entre inicializações
        time.sleep(0.5)
    
    # Aguarda conclusão
    for thread in threads:
        thread.join()
    
    print("\n🎉 Instalação em lote concluída!")

def demo_with_gui():
    """
    Demonstração com interface gráfica
    """
    import tkinter as tk
    
    def run_demo():
        root = tk.Tk()
        root.title("Demo - Sistema de Progresso Aprimorado")
        root.geometry("600x400")
        
        # Cria widget de progresso
        progress_widget = EnhancedProgressWidget(root)
        progress_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Botão para iniciar demo
        def start_demo():
            # Cria tracker
            tracker = create_progress_tracker("demo_install", "Componente Demo", 5)
            progress_widget.set_progress_tracker(tracker)
            
            # Simula instalação em thread separada
            def demo_worker():
                component_data = {
                    "download_url": "https://example.com/demo.exe",
                    "size": 1024 * 1024 * 10,  # 10MB
                    "install_success": True
                }
                enhanced_install_component("Componente Demo", component_data, tracker)
            
            threading.Thread(target=demo_worker, daemon=True).start()
        
        start_button = tk.Button(root, text="Iniciar Demo", command=start_demo)
        start_button.pack(pady=10)
        
        # Botão para abrir dashboard
        def open_dashboard():
            dashboard = create_installation_dashboard(root)
            
            # Simula algumas instalações no dashboard
            def dashboard_demo():
                time.sleep(1)
                
                # Primeira instalação
                tracker1 = dashboard.start_installation("dash_demo_1", "Python 3.11", 5)
                component_data1 = {
                    "download_url": "https://python.org/downloads/python-3.11.exe",
                    "size": 1024 * 1024 * 25,
                    "install_success": True
                }
                enhanced_install_component("Python 3.11", component_data1, tracker1)
                
                time.sleep(2)
                
                # Segunda instalação
                tracker2 = dashboard.start_installation("dash_demo_2", "Node.js 18", 4)
                component_data2 = {
                    "download_url": "https://nodejs.org/downloads/node-18.exe",
                    "size": 1024 * 1024 * 30,
                    "install_success": True
                }
                enhanced_install_component("Node.js 18", component_data2, tracker2)
            
            threading.Thread(target=dashboard_demo, daemon=True).start()
        
        dashboard_button = tk.Button(root, text="Abrir Dashboard", command=open_dashboard)
        dashboard_button.pack(pady=5)
        
        root.mainloop()
    
    run_demo()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo do Sistema de Progresso Aprimorado")
    parser.add_argument("--mode", choices=["console", "gui"], default="console",
                       help="Modo de demonstração (console ou gui)")
    
    args = parser.parse_args()
    
    print("🚀 Iniciando demonstração do Sistema de Progresso Aprimorado...\n")
    
    if args.mode == "console":
        print("Modo Console - Instalação em lote simulada")
        simulate_batch_installation()
    else:
        print("Modo GUI - Interface gráfica")
        demo_with_gui()
    
    print("\n✨ Demonstração concluída!")