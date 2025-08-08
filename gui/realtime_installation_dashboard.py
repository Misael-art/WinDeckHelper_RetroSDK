#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Instalação em Tempo Real
Interface completa para monitoramento de instalações com feedback detalhado
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
import json

# Importa componentes do projeto
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enhanced_progress import (
    DetailedProgress, OperationStage, ProgressTracker, 
    progress_manager, create_progress_tracker
)
from gui.enhanced_progress_widget import EnhancedProgressWidget
from gui.notification_system import NotificationCenter, NotificationLevel, NotificationCategory

class InstallationLogViewer(tk.Frame):
    """Visualizador de logs de instalação em tempo real"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuração
        self.max_lines = 1000
        self.auto_scroll = True
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Cria widgets do visualizador"""
        # Frame de controles
        self.controls_frame = tk.Frame(self)
        
        # Checkbox para auto-scroll
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_check = tk.Checkbutton(
            self.controls_frame, text="Auto-scroll", 
            variable=self.auto_scroll_var,
            command=self._on_auto_scroll_toggle
        )
        
        # Botão limpar
        self.clear_button = tk.Button(
            self.controls_frame, text="Limpar", 
            command=self.clear_logs
        )
        
        # Botão salvar
        self.save_button = tk.Button(
            self.controls_frame, text="Salvar", 
            command=self._save_logs
        )
        
        # Área de texto com scroll
        self.log_text = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, height=15, 
            font=("Consolas", 9), state=tk.DISABLED
        )
        
        # Configuração de cores para diferentes tipos de log
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("TIMESTAMP", foreground="blue", font=("Consolas", 8))
    
    def _setup_layout(self):
        """Configura layout"""
        self.controls_frame.pack(fill=tk.X, pady=(0, 5))
        self.auto_scroll_check.pack(side=tk.LEFT)
        self.clear_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.save_button.pack(side=tk.RIGHT)
        
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def add_log(self, level: str, message: str, component: str = None):
        """Adiciona entrada de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Formata mensagem
        if component:
            formatted_msg = f"[{timestamp}] [{component}] {message}\n"
        else:
            formatted_msg = f"[{timestamp}] {message}\n"
        
        # Adiciona ao texto
        self.log_text.config(state=tk.NORMAL)
        
        # Insere timestamp
        self.log_text.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")
        
        # Insere componente se fornecido
        if component:
            self.log_text.insert(tk.END, f"[{component}] ")
        
        # Insere mensagem com cor apropriada
        self.log_text.insert(tk.END, f"{message}\n", level.upper())
        
        # Limita número de linhas
        self._limit_lines()
        
        # Auto-scroll se habilitado
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        self.log_text.config(state=tk.DISABLED)
    
    def _limit_lines(self):
        """Limita número de linhas no log"""
        lines = self.log_text.get("1.0", tk.END).count("\n")
        if lines > self.max_lines:
            # Remove linhas antigas
            excess_lines = lines - self.max_lines
            self.log_text.delete("1.0", f"{excess_lines + 1}.0")
    
    def _on_auto_scroll_toggle(self):
        """Handler para toggle de auto-scroll"""
        self.auto_scroll = self.auto_scroll_var.get()
    
    def clear_logs(self):
        """Limpa todos os logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _save_logs(self):
        """Salva logs em arquivo"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Salvar logs de instalação"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    content = self.log_text.get("1.0", tk.END)
                    f.write(content)
                self.add_log("SUCCESS", f"Logs salvos em: {filename}")
            except Exception as e:
                self.add_log("ERROR", f"Erro ao salvar logs: {e}")

class InstallationSummary(tk.Frame):
    """Resumo de instalações"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0,
            'in_progress': 0
        }
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Cria widgets do resumo"""
        # Labels de estatísticas
        self.total_label = tk.Label(self, text="Total: 0", font=("Arial", 10, "bold"))
        self.completed_label = tk.Label(self, text="Concluídas: 0", fg="green")
        self.failed_label = tk.Label(self, text="Falharam: 0", fg="red")
        self.cancelled_label = tk.Label(self, text="Canceladas: 0", fg="orange")
        self.progress_label = tk.Label(self, text="Em andamento: 0", fg="blue")
        
        # Barra de progresso geral
        self.overall_progress = ttk.Progressbar(self, length=200, mode='determinate')
        self.overall_percent_label = tk.Label(self, text="0%")
    
    def _setup_layout(self):
        """Configura layout"""
        # Primeira linha
        row1 = tk.Frame(self)
        row1.pack(fill=tk.X, pady=2)
        self.total_label.pack(side=tk.LEFT)
        self.progress_label.pack(side=tk.RIGHT)
        
        # Segunda linha
        row2 = tk.Frame(self)
        row2.pack(fill=tk.X, pady=2)
        self.completed_label.pack(side=tk.LEFT)
        self.failed_label.pack(side=tk.RIGHT)
        
        # Terceira linha
        row3 = tk.Frame(self)
        row3.pack(fill=tk.X, pady=2)
        self.cancelled_label.pack(side=tk.LEFT)
        
        # Progresso geral
        progress_frame = tk.Frame(self)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Label(progress_frame, text="Progresso Geral:").pack(side=tk.LEFT)
        self.overall_progress.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        self.overall_percent_label.pack(side=tk.LEFT)
    
    def update_stats(self, operation_id: str, stage: OperationStage):
        """Atualiza estatísticas"""
        # Lógica simplificada - em implementação real, manteria estado de cada operação
        if stage == OperationStage.COMPLETING:
            self.stats['completed'] += 1
        elif stage == OperationStage.FAILED:
            self.stats['failed'] += 1
        elif stage == OperationStage.CANCELLED:
            self.stats['cancelled'] += 1
        
        self._update_display()
    
    def _update_display(self):
        """Atualiza display das estatísticas"""
        self.total_label.config(text=f"Total: {self.stats['total']}")
        self.completed_label.config(text=f"Concluídas: {self.stats['completed']}")
        self.failed_label.config(text=f"Falharam: {self.stats['failed']}")
        self.cancelled_label.config(text=f"Canceladas: {self.stats['cancelled']}")
        self.progress_label.config(text=f"Em andamento: {self.stats['in_progress']}")
        
        # Calcula progresso geral
        if self.stats['total'] > 0:
            completed_percent = (self.stats['completed'] / self.stats['total']) * 100
            self.overall_progress.configure(value=completed_percent)
            self.overall_percent_label.config(text=f"{completed_percent:.1f}%")
    
    def reset_stats(self):
        """Reseta estatísticas"""
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0,
            'in_progress': 0
        }
        self._update_display()

class RealtimeInstallationDashboard(tk.Toplevel):
    """Dashboard principal de instalação em tempo real"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuração da janela
        self.title("Dashboard de Instalação - Tempo Real")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Estado
        self.active_installations: Dict[str, ProgressTracker] = {}
        self.current_installation: Optional[str] = None
        self.notification_center = NotificationCenter(self)
        
        # Queue para comunicação thread-safe
        self.update_queue = queue.Queue()
        
        # Widgets
        self.notebook = None
        self.progress_widget = None
        self.log_viewer = None
        self.summary_widget = None
        
        self._create_widgets()
        self._setup_layout()
        self._setup_callbacks()
        self._start_update_loop()
        
        # Protocolo de fechamento
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_widgets(self):
        """Cria todos os widgets"""
        # Notebook para abas
        self.notebook = ttk.Notebook(self)
        
        # Aba de progresso
        self.progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_frame, text="Progresso Atual")
        
        # Widget de progresso aprimorado
        self.progress_widget = EnhancedProgressWidget(self.progress_frame)
        
        # Aba de logs
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Logs de Instalação")
        
        # Visualizador de logs
        self.log_viewer = InstallationLogViewer(self.log_frame)
        
        # Aba de resumo
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Resumo")
        
        # Widget de resumo
        self.summary_widget = InstallationSummary(self.summary_frame)
        
        # Frame de controles globais
        self.controls_frame = tk.Frame(self)
        
        # Botões de controle
        self.pause_all_button = tk.Button(
            self.controls_frame, text="Pausar Todas", 
            command=self._pause_all_installations
        )
        self.resume_all_button = tk.Button(
            self.controls_frame, text="Retomar Todas", 
            command=self._resume_all_installations
        )
        self.cancel_all_button = tk.Button(
            self.controls_frame, text="Cancelar Todas", 
            command=self._cancel_all_installations, fg="red"
        )
        
        # Separador
        self.separator = ttk.Separator(self.controls_frame, orient=tk.VERTICAL)
        
        # Botão de configurações
        self.settings_button = tk.Button(
            self.controls_frame, text="Configurações", 
            command=self._show_settings
        )
        
        # Status bar
        self.status_bar = tk.Label(
            self, text="Pronto", relief=tk.SUNKEN, anchor=tk.W
        )
    
    def _setup_layout(self):
        """Configura layout"""
        # Layout principal
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout da aba de progresso
        self.progress_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout da aba de logs
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout da aba de resumo
        self.summary_widget.pack(fill=tk.X, padx=10, pady=10)
        
        # Controles globais
        self.controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.pause_all_button.pack(side=tk.LEFT, padx=(0, 5))
        self.resume_all_button.pack(side=tk.LEFT, padx=(0, 5))
        self.cancel_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.separator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.settings_button.pack(side=tk.LEFT)
        
        # Status bar
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _setup_callbacks(self):
        """Configura callbacks do sistema de progresso"""
        # Callback global para todas as operações
        progress_manager.add_global_callback(self._on_global_progress_update)
        
        # Callback para o widget de progresso
        self.progress_widget.set_update_callback(self._on_progress_widget_update)
    
    def _start_update_loop(self):
        """Inicia loop de atualização da UI"""
        self._process_update_queue()
        self.after(100, self._start_update_loop)  # 10 FPS
    
    def _process_update_queue(self):
        """Processa queue de atualizações"""
        try:
            while True:
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == "progress":
                    operation_id, progress = data
                    self._handle_progress_update(operation_id, progress)
                elif update_type == "log":
                    level, message, component = data
                    self.log_viewer.add_log(level, message, component)
                elif update_type == "status":
                    self.status_bar.config(text=data)
                
        except queue.Empty:
            pass
    
    def _on_global_progress_update(self, operation_id: str, progress: DetailedProgress):
        """Callback para atualizações globais de progresso"""
        # Envia para queue thread-safe
        self.update_queue.put(("progress", (operation_id, progress)))
    
    def _handle_progress_update(self, operation_id: str, progress: DetailedProgress):
        """Processa atualização de progresso"""
        # Atualiza instalação atual se for a mesma
        if self.current_installation == operation_id:
            # O widget já está conectado ao tracker
            pass
        
        # Atualiza estatísticas
        self.summary_widget.update_stats(operation_id, progress.stage)
        
        # Log de marcos importantes
        if progress.stage == OperationStage.DOWNLOADING and progress.progress_percent == 0:
            self._add_log("INFO", "Iniciando download...", progress.component_name)
        elif progress.stage == OperationStage.INSTALLING and progress.progress_percent == 0:
            self._add_log("INFO", "Iniciando instalação...", progress.component_name)
        elif progress.stage == OperationStage.COMPLETING:
            self._add_log("SUCCESS", "Instalação concluída com sucesso!", progress.component_name)
            self._show_notification("Sucesso", f"Instalação de {progress.component_name} concluída", "success")
        elif progress.stage == OperationStage.FAILED:
            self._add_log("ERROR", f"Instalação falhou: {progress.current_step}", progress.component_name)
            self._show_notification("Erro", f"Instalação de {progress.component_name} falhou", "error")
        elif progress.stage == OperationStage.CANCELLED:
            self._add_log("WARNING", "Instalação cancelada", progress.component_name)
    
    def _on_progress_widget_update(self, progress: DetailedProgress):
        """Callback para atualizações do widget de progresso"""
        # Atualiza status bar
        status_text = f"{progress.component_name}: {progress.stage.value} ({progress.progress_percent:.1f}%)"
        self.update_queue.put(("status", status_text))
    
    def start_installation(self, operation_id: str, component_name: str, total_steps: int = 1) -> ProgressTracker:
        """Inicia nova instalação"""
        # Cria tracker
        tracker = create_progress_tracker(operation_id, component_name, total_steps)
        
        # Registra instalação ativa
        self.active_installations[operation_id] = tracker
        
        # Define como instalação atual
        self.current_installation = operation_id
        self.progress_widget.set_progress_tracker(tracker)
        
        # Atualiza estatísticas
        self.summary_widget.stats['total'] += 1
        self.summary_widget.stats['in_progress'] += 1
        self.summary_widget._update_display()
        
        # Log
        self._add_log("INFO", f"Iniciando instalação de {component_name}", component_name)
        
        # Notificação
        self._show_notification("Instalação", f"Iniciando instalação de {component_name}", "info")
        
        return tracker
    
    def start_installations(self, component_names: List[str], components_data: dict):
        """Inicia instalação de múltiplos componentes"""
        def installation_worker():
            try:
                from env_dev.core import installer
                
                total_components = len(component_names)
                installed_components = set()
                
                for i, component_name in enumerate(component_names):
                    # Cria tracker para este componente
                    operation_id = f"install_{component_name}_{int(time.time())}"
                    tracker = self.start_installation(operation_id, component_name, 5)
                    
                    try:
                        # Atualiza progresso
                        tracker.update_progress(0, OperationStage.INITIALIZING, "Preparando instalação...")
                        
                        # Obtém dados do componente
                        component_data = components_data.get(component_name)
                        if not component_data:
                            self._add_log("ERROR", f"Dados do componente não encontrados: {component_name}", component_name)
                            tracker.update_progress(100, OperationStage.FAILED, "Dados não encontrados")
                            continue
                        
                        # Instalação real
                        tracker.update_progress(25, OperationStage.DOWNLOADING, "Baixando componente...")
                        
                        success = installer.install_component(
                            component_name=component_name,
                            component_data=component_data,
                            all_components_data=components_data,
                            installed_components=installed_components
                        )
                        
                        if success:
                            tracker.update_progress(100, OperationStage.COMPLETED, "Instalação concluída")
                            self._add_log("SUCCESS", f"{component_name} instalado com sucesso", component_name)
                            self._show_notification("Sucesso", f"{component_name} instalado", "success")
                            
                            # Atualiza estatísticas
                            self.summary_widget.stats['completed'] += 1
                            self.summary_widget.stats['in_progress'] -= 1
                        else:
                            tracker.update_progress(100, OperationStage.FAILED, "Falha na instalação")
                            self._add_log("ERROR", f"Falha ao instalar {component_name}", component_name)
                            self._show_notification("Erro", f"Falha ao instalar {component_name}", "error")
                            
                            # Atualiza estatísticas
                            self.summary_widget.stats['failed'] += 1
                            self.summary_widget.stats['in_progress'] -= 1
                    
                    except Exception as e:
                        tracker.update_progress(100, OperationStage.FAILED, f"Erro: {str(e)}")
                        self._add_log("ERROR", f"Erro ao instalar {component_name}: {str(e)}", component_name)
                        self._show_notification("Erro", f"Erro ao instalar {component_name}", "error")
                        
                        # Atualiza estatísticas
                        self.summary_widget.stats['failed'] += 1
                        self.summary_widget.stats['in_progress'] -= 1
                    
                    # Atualiza display
                    self.summary_widget._update_display()
                
                # Notificação final
                completed = self.summary_widget.stats['completed']
                failed = self.summary_widget.stats['failed']
                
                if failed == 0:
                    self._show_notification("Concluído", f"Todas as {completed} instalações foram concluídas com sucesso", "success")
                else:
                    self._show_notification("Concluído", f"{completed} instalações concluídas, {failed} falharam", "warning")
                
            except Exception as e:
                self._add_log("ERROR", f"Erro geral na instalação: {str(e)}")
                self._show_notification("Erro", "Erro geral na instalação", "error")
        
        # Inicia worker em thread separada
        threading.Thread(target=installation_worker, daemon=True).start()
    
    def switch_to_installation(self, operation_id: str):
        """Muda para visualizar instalação específica"""
        if operation_id in self.active_installations:
            self.current_installation = operation_id
            tracker = self.active_installations[operation_id]
            self.progress_widget.set_progress_tracker(tracker)
            
            # Muda para aba de progresso
            self.notebook.select(0)
    
    def _add_log(self, level: str, message: str, component: str = None):
        """Adiciona log thread-safe"""
        self.update_queue.put(("log", (level, message, component)))
    
    def _show_notification(self, title: str, message: str, type_: str = "info"):
        """Exibe notificação"""
        level_map = {
            "info": NotificationLevel.INFO,
            "success": NotificationLevel.SUCCESS,
            "warning": NotificationLevel.WARNING,
            "error": NotificationLevel.ERROR
        }
        
        level = level_map.get(type_, NotificationLevel.INFO)
        self.notification_center.show_notification(
            title, message, level, NotificationCategory.INSTALLATION
        )
    
    def _pause_all_installations(self):
        """Pausa todas as instalações"""
        for tracker in self.active_installations.values():
            tracker.pause()
        self._add_log("INFO", "Todas as instalações foram pausadas")
    
    def _resume_all_installations(self):
        """Retoma todas as instalações"""
        for tracker in self.active_installations.values():
            tracker.resume()
        self._add_log("INFO", "Todas as instalações foram retomadas")
    
    def _cancel_all_installations(self):
        """Cancela todas as instalações"""
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("Confirmar", "Deseja realmente cancelar todas as instalações?"):
            for tracker in self.active_installations.values():
                tracker.cancel("Cancelado pelo usuário")
            self._add_log("WARNING", "Todas as instalações foram canceladas")
    
    def _show_settings(self):
        """Exibe janela de configurações"""
        # Placeholder para configurações
        import tkinter.messagebox as msgbox
        msgbox.showinfo("Configurações", "Configurações serão implementadas em versão futura")
    
    def _on_closing(self):
        """Handler para fechamento da janela"""
        # Verifica se há instalações em andamento
        active_count = len([t for t in self.active_installations.values() 
                          if not t.is_cancelled and t.current_progress.stage not in 
                          [OperationStage.COMPLETING, OperationStage.FAILED, OperationStage.CANCELLED]])
        
        if active_count > 0:
            import tkinter.messagebox as msgbox
            if not msgbox.askyesno("Confirmar", 
                                 f"Há {active_count} instalação(ões) em andamento. Deseja realmente fechar?"):
                return
        
        self.destroy()

# Função de conveniência para criar dashboard
def create_installation_dashboard(parent=None) -> RealtimeInstallationDashboard:
    """Cria e retorna dashboard de instalação"""
    return RealtimeInstallationDashboard(parent)

# Exemplo de uso
if __name__ == "__main__":
    import time
    from core.enhanced_progress import OperationStage
    
    def test_dashboard():
        root = tk.Tk()
        root.withdraw()  # Esconde janela principal
        
        # Cria dashboard
        dashboard = create_installation_dashboard(root)
        
        # Simula instalações
        def simulate_installations():
            time.sleep(1)
            
            # Primeira instalação
            tracker1 = dashboard.start_installation("install_1", "Python 3.11", 5)
            
            # Simula progresso
            for stage in [OperationStage.PREPARING, OperationStage.DOWNLOADING, 
                         OperationStage.INSTALLING, OperationStage.CONFIGURING]:
                tracker1.update_stage(stage, step_description=f"Executando {stage.value}...")
                time.sleep(2)
                
                if stage == OperationStage.DOWNLOADING:
                    # Simula download
                    total_size = 1024 * 1024 * 20  # 20MB
                    for i in range(0, total_size, 1024 * 100):
                        tracker1.update_download_progress(min(i + 1024 * 100, total_size), total_size)
                        time.sleep(0.1)
            
            tracker1.complete(True, "Instalação concluída!")
            
            # Segunda instalação após um tempo
            time.sleep(3)
            tracker2 = dashboard.start_installation("install_2", "Node.js 18", 4)
            
            for i in range(1, 5):
                tracker2.update_step(i, f"Executando passo {i}...")
                time.sleep(1.5)
            
            tracker2.complete(True, "Node.js instalado com sucesso!")
        
        # Inicia simulação
        threading.Thread(target=simulate_installations, daemon=True).start()
        
        root.mainloop()
    
    test_dashboard()