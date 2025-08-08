#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de Progresso Aprimorado
Componente GUI para exibir progresso detalhado com animações e feedback visual
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional, Callable
from datetime import datetime

# Importa o sistema de progresso aprimorado
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.enhanced_progress import DetailedProgress, OperationStage, ProgressTracker

class AnimatedProgressBar(ttk.Progressbar):
    """Barra de progresso com animação suave"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.target_value = 0
        self.current_value = 0
        self.animation_speed = 2.0  # Velocidade da animação
        self.animation_active = False
        self._animation_thread = None
    
    def set_value_animated(self, value: float):
        """Define valor com animação suave"""
        self.target_value = max(0, min(100, value))
        if not self.animation_active:
            self._start_animation()
    
    def _start_animation(self):
        """Inicia thread de animação"""
        if self._animation_thread and self._animation_thread.is_alive():
            return
        
        self.animation_active = True
        self._animation_thread = threading.Thread(target=self._animate, daemon=True)
        self._animation_thread.start()
    
    def _animate(self):
        """Loop de animação"""
        while self.animation_active:
            try:
                diff = self.target_value - self.current_value
                if abs(diff) < 0.1:
                    self.current_value = self.target_value
                    self.animation_active = False
                else:
                    self.current_value += diff * self.animation_speed * 0.016  # ~60fps
                
                # Atualiza na thread principal
                self.after_idle(lambda: self.configure(value=self.current_value))
                
                if not self.animation_active:
                    break
                    
                time.sleep(0.016)  # ~60fps
            except Exception:
                break

class StageIndicator(tk.Frame):
    """Indicador visual de estágios"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.stages = [
            ("Preparando", OperationStage.PREPARING),
            ("Baixando", OperationStage.DOWNLOADING),
            ("Extraindo", OperationStage.EXTRACTING),
            ("Instalando", OperationStage.INSTALLING),
            ("Configurando", OperationStage.CONFIGURING),
            ("Verificando", OperationStage.VERIFYING),
            ("Finalizando", OperationStage.COMPLETING)
        ]
        
        self.stage_labels = []
        self.stage_indicators = []
        self.current_stage = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Cria widgets dos estágios"""
        for i, (name, stage) in enumerate(self.stages):
            # Frame para cada estágio
            stage_frame = tk.Frame(self)
            stage_frame.pack(side=tk.LEFT, padx=2)
            
            # Indicador circular
            indicator = tk.Canvas(stage_frame, width=20, height=20, highlightthickness=0)
            indicator.pack()
            
            # Desenha círculo
            circle = indicator.create_oval(2, 2, 18, 18, 
                                         fill="lightgray", outline="gray", width=2)
            
            # Label do estágio
            label = tk.Label(stage_frame, text=name, font=("Arial", 8))
            label.pack()
            
            self.stage_indicators.append((indicator, circle))
            self.stage_labels.append(label)
            
            # Linha conectora (exceto último)
            if i < len(self.stages) - 1:
                line = tk.Canvas(self, width=30, height=20, highlightthickness=0)
                line.pack(side=tk.LEFT)
                line.create_line(5, 10, 25, 10, fill="lightgray", width=2)
    
    def update_stage(self, current_stage: OperationStage):
        """Atualiza estágio atual"""
        self.current_stage = current_stage
        
        for i, (name, stage) in enumerate(self.stages):
            indicator, circle = self.stage_indicators[i]
            label = self.stage_labels[i]
            
            if stage == current_stage:
                # Estágio atual - azul
                indicator.itemconfig(circle, fill="#007ACC", outline="#005A9E")
                label.config(fg="#007ACC", font=("Arial", 8, "bold"))
            elif self._is_stage_completed(stage, current_stage):
                # Estágio completado - verde
                indicator.itemconfig(circle, fill="#28A745", outline="#1E7E34")
                label.config(fg="#28A745", font=("Arial", 8))
            elif current_stage == OperationStage.FAILED:
                # Falha - vermelho para estágio atual
                if stage == self._get_failed_stage():
                    indicator.itemconfig(circle, fill="#DC3545", outline="#C82333")
                    label.config(fg="#DC3545", font=("Arial", 8, "bold"))
                else:
                    indicator.itemconfig(circle, fill="lightgray", outline="gray")
                    label.config(fg="gray", font=("Arial", 8))
            else:
                # Estágio pendente - cinza
                indicator.itemconfig(circle, fill="lightgray", outline="gray")
                label.config(fg="gray", font=("Arial", 8))
    
    def _is_stage_completed(self, stage: OperationStage, current_stage: OperationStage) -> bool:
        """Verifica se estágio foi completado"""
        stage_order = [s[1] for s in self.stages]
        try:
            stage_idx = stage_order.index(stage)
            current_idx = stage_order.index(current_stage)
            return stage_idx < current_idx
        except ValueError:
            return False
    
    def _get_failed_stage(self) -> OperationStage:
        """Retorna estágio onde falha ocorreu (simplificado)"""
        return OperationStage.INSTALLING  # Placeholder

class EnhancedProgressWidget(tk.Frame):
    """Widget completo de progresso aprimorado"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Variáveis de controle
        self.current_progress: Optional[DetailedProgress] = None
        self.progress_tracker: Optional[ProgressTracker] = None
        self.update_callback: Optional[Callable] = None
        
        # Widgets
        self.component_label = None
        self.stage_indicator = None
        self.progress_bar = None
        self.status_label = None
        self.details_frame = None
        self.download_info_label = None
        self.speed_label = None
        self.eta_label = None
        self.elapsed_label = None
        self.step_label = None
        
        # Controles
        self.control_frame = None
        self.pause_button = None
        self.cancel_button = None
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Cria todos os widgets"""
        # Título do componente
        self.component_label = tk.Label(self, text="Componente", 
                                      font=("Arial", 12, "bold"))
        
        # Indicador de estágios
        self.stage_indicator = StageIndicator(self)
        
        # Barra de progresso animada
        self.progress_bar = AnimatedProgressBar(self, length=400, mode='determinate')
        
        # Status principal
        self.status_label = tk.Label(self, text="Aguardando...", 
                                   font=("Arial", 10))
        
        # Frame de detalhes
        self.details_frame = tk.LabelFrame(self, text="Detalhes", padx=5, pady=5)
        
        # Informações de download
        self.download_info_label = tk.Label(self.details_frame, text="")
        self.speed_label = tk.Label(self.details_frame, text="")
        self.eta_label = tk.Label(self.details_frame, text="")
        self.elapsed_label = tk.Label(self.details_frame, text="")
        
        # Passo atual
        self.step_label = tk.Label(self.details_frame, text="", 
                                 font=("Arial", 9), wraplength=350)
        
        # Controles
        self.control_frame = tk.Frame(self)
        self.pause_button = tk.Button(self.control_frame, text="Pausar", 
                                    command=self._on_pause_click, state=tk.DISABLED)
        self.cancel_button = tk.Button(self.control_frame, text="Cancelar", 
                                     command=self._on_cancel_click, state=tk.DISABLED)
    
    def _setup_layout(self):
        """Configura layout dos widgets"""
        # Layout principal
        self.component_label.pack(pady=(0, 10))
        self.stage_indicator.pack(pady=(0, 10))
        self.progress_bar.pack(fill=tk.X, padx=20, pady=(0, 5))
        self.status_label.pack(pady=(0, 10))
        
        # Frame de detalhes
        self.details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Layout dos detalhes
        info_frame = tk.Frame(self.details_frame)
        info_frame.pack(fill=tk.X)
        
        # Primeira linha: download e velocidade
        download_frame = tk.Frame(info_frame)
        download_frame.pack(fill=tk.X)
        self.download_info_label.pack(side=tk.LEFT)
        self.speed_label.pack(side=tk.RIGHT)
        
        # Segunda linha: ETA e tempo decorrido
        time_frame = tk.Frame(info_frame)
        time_frame.pack(fill=tk.X, pady=(5, 0))
        self.eta_label.pack(side=tk.LEFT)
        self.elapsed_label.pack(side=tk.RIGHT)
        
        # Passo atual
        self.step_label.pack(fill=tk.X, pady=(10, 0))
        
        # Controles
        self.control_frame.pack(pady=(10, 0))
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))
        self.cancel_button.pack(side=tk.LEFT)
    
    def set_progress_tracker(self, tracker: ProgressTracker):
        """Define tracker de progresso"""
        if self.progress_tracker:
            self.progress_tracker.remove_callback(self._on_progress_update)
        
        self.progress_tracker = tracker
        if tracker:
            tracker.add_callback(self._on_progress_update)
            self.pause_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
            
            # Atualização inicial
            self._on_progress_update(tracker.get_current_progress())
    
    def _on_progress_update(self, progress: DetailedProgress):
        """Callback para atualização de progresso"""
        self.current_progress = progress
        
        # Atualiza na thread principal
        self.after_idle(self._update_display)
    
    def _update_display(self):
        """Atualiza display com progresso atual"""
        if not self.current_progress:
            return
        
        progress = self.current_progress
        
        # Atualiza componente
        self.component_label.config(text=progress.component_name)
        
        # Atualiza estágio
        self.stage_indicator.update_stage(progress.stage)
        
        # Atualiza barra de progresso
        self.progress_bar.set_value_animated(progress.progress_percent)
        
        # Atualiza status
        status_text = f"{progress.progress_percent:.1f}% - {progress.stage.value.title()}"
        self.status_label.config(text=status_text)
        
        # Atualiza detalhes
        self._update_details(progress)
        
        # Atualiza controles baseado no estado
        self._update_controls(progress)
        
        # Callback externo
        if self.update_callback:
            self.update_callback(progress)
    
    def _update_details(self, progress: DetailedProgress):
        """Atualiza informações detalhadas"""
        # Download info
        if progress.stage == OperationStage.DOWNLOADING and progress.total_bytes > 0:
            self.download_info_label.config(text=f"Download: {progress.get_download_info()}")
            self.speed_label.config(text=f"Velocidade: {progress.format_speed()}")
            self.eta_label.config(text=f"ETA: {progress.format_eta()}")
        else:
            self.download_info_label.config(text="")
            self.speed_label.config(text="")
            self.eta_label.config(text="")
        
        # Tempo decorrido
        self.elapsed_label.config(text=f"Tempo: {progress.get_elapsed_time()}")
        
        # Passo atual
        step_text = f"Passo {progress.current_step_number}/{progress.total_steps}: {progress.current_step}"
        self.step_label.config(text=step_text)
    
    def _update_controls(self, progress: DetailedProgress):
        """Atualiza estado dos controles"""
        if progress.stage in [OperationStage.COMPLETING, OperationStage.FAILED, OperationStage.CANCELLED]:
            self.pause_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)
        else:
            self.pause_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
            
            # Atualiza texto do botão pausar
            if self.progress_tracker and self.progress_tracker.is_paused:
                self.pause_button.config(text="Retomar")
            else:
                self.pause_button.config(text="Pausar")
    
    def _on_pause_click(self):
        """Handler para botão pausar/retomar"""
        if not self.progress_tracker:
            return
        
        if self.progress_tracker.is_paused:
            self.progress_tracker.resume()
        else:
            self.progress_tracker.pause()
    
    def _on_cancel_click(self):
        """Handler para botão cancelar"""
        if not self.progress_tracker:
            return
        
        # Confirma cancelamento
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("Confirmar", "Deseja realmente cancelar a operação?"):
            self.progress_tracker.cancel("Cancelado pelo usuário")
    
    def set_update_callback(self, callback: Callable[[DetailedProgress], None]):
        """Define callback para atualizações"""
        self.update_callback = callback
    
    def reset(self):
        """Reseta widget para estado inicial"""
        if self.progress_tracker:
            self.progress_tracker.remove_callback(self._on_progress_update)
        
        self.progress_tracker = None
        self.current_progress = None
        
        # Reseta display
        self.component_label.config(text="Componente")
        self.progress_bar.configure(value=0)
        self.status_label.config(text="Aguardando...")
        self.download_info_label.config(text="")
        self.speed_label.config(text="")
        self.eta_label.config(text="")
        self.elapsed_label.config(text="")
        self.step_label.config(text="")
        
        # Reseta controles
        self.pause_button.config(state=tk.DISABLED, text="Pausar")
        self.cancel_button.config(state=tk.DISABLED)
        
        # Reseta indicador de estágios
        self.stage_indicator.update_stage(OperationStage.PREPARING)

# Exemplo de uso
if __name__ == "__main__":
    import time
    from core.enhanced_progress import create_progress_tracker, OperationStage
    
    def test_widget():
        root = tk.Tk()
        root.title("Teste Widget de Progresso")
        root.geometry("500x400")
        
        # Cria widget
        progress_widget = EnhancedProgressWidget(root)
        progress_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cria tracker de teste
        tracker = create_progress_tracker("test_op", "Componente de Teste", 5)
        progress_widget.set_progress_tracker(tracker)
        
        # Simula progresso em thread separada
        def simulate_progress():
            time.sleep(1)
            
            # Preparando
            tracker.update_stage(OperationStage.PREPARING, step_description="Preparando instalação...")
            time.sleep(2)
            
            # Download
            tracker.update_stage(OperationStage.DOWNLOADING, step_description="Baixando arquivo...")
            total_size = 1024 * 1024 * 5  # 5MB
            for i in range(0, total_size, 1024 * 50):  # Chunks de 50KB
                tracker.update_download_progress(min(i + 1024 * 50, total_size), total_size)
                time.sleep(0.1)
            
            # Instalando
            tracker.update_stage(OperationStage.INSTALLING, step_description="Instalando componente...")
            for i in range(1, 6):
                tracker.update_step(i, f"Executando passo {i} de instalação...")
                time.sleep(1)
            
            # Concluindo
            tracker.complete(True, "Instalação concluída com sucesso!")
        
        # Inicia simulação
        threading.Thread(target=simulate_progress, daemon=True).start()
        
        root.mainloop()
    
    test_widget()