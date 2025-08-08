#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Progress Tracking System
Provides detailed progress tracking with ETA, speed calculation, and stage management
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import time
import threading
from collections import deque

class OperationStage(Enum):
    """Estágios de operação para instalação"""
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    CONFIGURING = "configuring"
    VERIFYING = "verifying"
    COMPLETING = "completing"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DetailedProgress:
    """Estrutura detalhada de progresso"""
    operation_id: str
    component_name: str
    stage: OperationStage
    progress_percent: float
    current_step: str
    total_steps: int
    current_step_number: int
    
    # Download específico
    bytes_downloaded: int = 0
    total_bytes: int = 0
    download_speed: float = 0.0  # bytes/sec
    eta_seconds: Optional[int] = None
    
    # Metadados
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    sub_operations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_eta(self) -> Optional[int]:
        """Calcula ETA baseado na velocidade atual"""
        if self.download_speed > 0 and self.total_bytes > 0:
            remaining_bytes = self.total_bytes - self.bytes_downloaded
            return int(remaining_bytes / self.download_speed)
        return None
    
    def format_speed(self) -> str:
        """Formata velocidade para exibição"""
        if self.download_speed < 1024:
            return f"{self.download_speed:.1f} B/s"
        elif self.download_speed < 1024 * 1024:
            return f"{self.download_speed / 1024:.1f} KB/s"
        else:
            return f"{self.download_speed / (1024 * 1024):.1f} MB/s"
    
    def format_eta(self) -> str:
        """Formata ETA para exibição"""
        eta = self.calculate_eta()
        if eta is None:
            return "Calculando..."
        
        if eta < 60:
            return f"{eta}s"
        elif eta < 3600:
            return f"{eta // 60}m {eta % 60}s"
        else:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def format_bytes(self, bytes_value: int) -> str:
        """Formata bytes para exibição"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
    
    def get_download_info(self) -> str:
        """Retorna informação formatada de download"""
        if self.total_bytes > 0:
            downloaded_str = self.format_bytes(self.bytes_downloaded)
            total_str = self.format_bytes(self.total_bytes)
            return f"{downloaded_str} / {total_str}"
        return "Tamanho desconhecido"
    
    def get_elapsed_time(self) -> str:
        """Retorna tempo decorrido formatado"""
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            return f"{total_seconds // 60}m {total_seconds % 60}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

class ProgressTracker:
    """Rastreador de progresso aprimorado com thread safety"""
    
    def __init__(self, operation_id: str, component_name: str, total_steps: int = 1):
        self.operation_id = operation_id
        self.component_name = component_name
        self.current_progress = DetailedProgress(
            operation_id=operation_id,
            component_name=component_name,
            stage=OperationStage.PREPARING,
            progress_percent=0.0,
            current_step="Inicializando...",
            total_steps=total_steps,
            current_step_number=0
        )
        self.callbacks: List[Callable[[DetailedProgress], None]] = []
        self.speed_history = deque(maxlen=10)  # Últimas 10 amostras
        self._lock = threading.Lock()
        self.is_cancelled = False
        self.is_paused = False
        
        # Para cálculo de velocidade suavizada
        self.last_bytes = 0
        self.last_time = time.time()
    
    def add_callback(self, callback: Callable[[DetailedProgress], None]):
        """Adiciona callback para updates de progresso"""
        with self._lock:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[DetailedProgress], None]):
        """Remove callback de progresso"""
        with self._lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
    
    def update_stage(self, stage: OperationStage, total_steps: int = None, step_description: str = None):
        """Atualiza estágio atual"""
        with self._lock:
            self.current_progress.stage = stage
            if total_steps is not None:
                self.current_progress.total_steps = total_steps
            if step_description:
                self.current_progress.current_step = step_description
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def update_step(self, step_number: int, step_description: str = None, progress_percent: float = None):
        """Atualiza passo atual"""
        with self._lock:
            self.current_progress.current_step_number = step_number
            if step_description:
                self.current_progress.current_step = step_description
            
            # Calcula progresso baseado no passo se não fornecido
            if progress_percent is not None:
                self.current_progress.progress_percent = progress_percent
            else:
                self.current_progress.progress_percent = (
                    step_number / self.current_progress.total_steps
                ) * 100
            
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def update_download_progress(self, downloaded: int, total: int = None):
        """Atualiza progresso de download com cálculo de velocidade"""
        with self._lock:
            current_time = time.time()
            
            # Calcula velocidade baseada em amostras recentes
            if self.last_bytes > 0 and downloaded > self.last_bytes:
                time_diff = current_time - self.last_time
                if time_diff > 0.1:  # Mínimo 100ms entre amostras
                    bytes_diff = downloaded - self.last_bytes
                    speed = bytes_diff / time_diff
                    
                    # Adiciona à história de velocidade
                    self.speed_history.append(speed)
                    
                    # Calcula média suavizada
                    if len(self.speed_history) > 0:
                        self.current_progress.download_speed = sum(self.speed_history) / len(self.speed_history)
                    
                    self.last_bytes = downloaded
                    self.last_time = current_time
            elif self.last_bytes == 0:
                self.last_bytes = downloaded
                self.last_time = current_time
            
            # Atualiza progresso
            self.current_progress.bytes_downloaded = downloaded
            if total is not None:
                self.current_progress.total_bytes = total
            
            # Calcula porcentagem
            if self.current_progress.total_bytes > 0:
                self.current_progress.progress_percent = (
                    downloaded / self.current_progress.total_bytes
                ) * 100
            
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def update_custom_progress(self, progress_percent: float, description: str = None, metadata: Dict[str, Any] = None):
        """Atualiza progresso customizado"""
        with self._lock:
            self.current_progress.progress_percent = max(0, min(100, progress_percent))
            if description:
                self.current_progress.current_step = description
            if metadata:
                self.current_progress.metadata.update(metadata)
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def add_sub_operation(self, operation: str):
        """Adiciona sub-operação à lista"""
        with self._lock:
            self.current_progress.sub_operations.append(operation)
            self._notify_callbacks()
    
    def complete(self, success: bool = True, message: str = None):
        """Marca operação como completa"""
        with self._lock:
            if success:
                self.current_progress.stage = OperationStage.COMPLETING
                self.current_progress.progress_percent = 100.0
                self.current_progress.current_step = message or "Concluído com sucesso"
            else:
                self.current_progress.stage = OperationStage.FAILED
                self.current_progress.current_step = message or "Operação falhou"
            
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def cancel(self, message: str = None):
        """Cancela operação"""
        with self._lock:
            self.is_cancelled = True
            self.current_progress.stage = OperationStage.CANCELLED
            self.current_progress.current_step = message or "Operação cancelada"
            self.current_progress.last_update = datetime.now()
            self._notify_callbacks()
    
    def pause(self):
        """Pausa operação"""
        with self._lock:
            self.is_paused = True
    
    def resume(self):
        """Retoma operação"""
        with self._lock:
            self.is_paused = False
    
    def get_current_progress(self) -> DetailedProgress:
        """Retorna cópia do progresso atual"""
        with self._lock:
            # Retorna uma cópia para evitar modificações concorrentes
            import copy
            return copy.deepcopy(self.current_progress)
    
    def _notify_callbacks(self):
        """Notifica todos os callbacks registrados (thread-safe)"""
        # Cria cópia dos callbacks para evitar modificação durante iteração
        callbacks_copy = self.callbacks.copy()
        progress_copy = self.get_current_progress()
        
        for callback in callbacks_copy:
            try:
                callback(progress_copy)
            except Exception as e:
                print(f"Erro em callback de progresso: {e}")

class ProgressManager:
    """Gerenciador central de progresso para múltiplas operações"""
    
    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        self.global_callbacks: List[Callable[[str, DetailedProgress], None]] = []
        self._lock = threading.Lock()
    
    def create_tracker(self, operation_id: str, component_name: str, total_steps: int = 1) -> ProgressTracker:
        """Cria novo tracker de progresso"""
        with self._lock:
            tracker = ProgressTracker(operation_id, component_name, total_steps)
            
            # Adiciona callback para notificar callbacks globais
            def global_callback(progress: DetailedProgress):
                for callback in self.global_callbacks:
                    try:
                        callback(operation_id, progress)
                    except Exception as e:
                        print(f"Erro em callback global: {e}")
            
            tracker.add_callback(global_callback)
            self.trackers[operation_id] = tracker
            return tracker
    
    def get_tracker(self, operation_id: str) -> Optional[ProgressTracker]:
        """Retorna tracker existente"""
        with self._lock:
            return self.trackers.get(operation_id)
    
    def remove_tracker(self, operation_id: str):
        """Remove tracker"""
        with self._lock:
            if operation_id in self.trackers:
                del self.trackers[operation_id]
    
    def add_global_callback(self, callback: Callable[[str, DetailedProgress], None]):
        """Adiciona callback global para todos os trackers"""
        with self._lock:
            self.global_callbacks.append(callback)
    
    def get_all_progress(self) -> Dict[str, DetailedProgress]:
        """Retorna progresso de todas as operações"""
        with self._lock:
            return {op_id: tracker.get_current_progress() 
                   for op_id, tracker in self.trackers.items()}
    
    def cancel_all(self):
        """Cancela todas as operações"""
        with self._lock:
            for tracker in self.trackers.values():
                tracker.cancel("Cancelado pelo usuário")
    
    def pause_all(self):
        """Pausa todas as operações"""
        with self._lock:
            for tracker in self.trackers.values():
                tracker.pause()
    
    def resume_all(self):
        """Retoma todas as operações"""
        with self._lock:
            for tracker in self.trackers.values():
                tracker.resume()

# Instância global do gerenciador
progress_manager = ProgressManager()

# Funções de conveniência
def create_progress_tracker(operation_id: str, component_name: str, total_steps: int = 1) -> ProgressTracker:
    """Cria tracker de progresso usando o gerenciador global"""
    return progress_manager.create_tracker(operation_id, component_name, total_steps)

def get_progress_tracker(operation_id: str) -> Optional[ProgressTracker]:
    """Obtém tracker de progresso existente"""
    return progress_manager.get_tracker(operation_id)

def add_global_progress_callback(callback: Callable[[str, DetailedProgress], None]):
    """Adiciona callback global para monitorar todo progresso"""
    progress_manager.add_global_callback(callback)

# Exemplo de uso
if __name__ == "__main__":
    import time
    
    def progress_callback(progress: DetailedProgress):
        print(f"[{progress.component_name}] {progress.stage.value}: {progress.progress_percent:.1f}% - {progress.current_step}")
        if progress.stage == OperationStage.DOWNLOADING:
            print(f"  Download: {progress.get_download_info()} @ {progress.format_speed()} (ETA: {progress.format_eta()})")
    
    # Teste básico
    tracker = create_progress_tracker("test_op", "TestComponent", 5)
    tracker.add_callback(progress_callback)
    
    # Simula progresso
    tracker.update_stage(OperationStage.DOWNLOADING, step_description="Baixando arquivo...")
    
    # Simula download
    total_size = 1024 * 1024 * 10  # 10MB
    for i in range(0, total_size, 1024 * 100):  # Chunks de 100KB
        tracker.update_download_progress(min(i + 1024 * 100, total_size), total_size)
        time.sleep(0.1)
    
    tracker.complete(True, "Download concluído")