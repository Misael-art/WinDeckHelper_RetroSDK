# Plano de Implementação: Melhorias de Feedback de Instalação

## Visão Geral

Este documento detalha a implementação prática das melhorias identificadas na avaliação de feedback de instalação, com foco em implementações de alto impacto e baixo risco.

## Prioridade 1: Enhanced Progress Tracking (Implementação Imediata)

### 1.1 Estrutura de Progresso Detalhado

**Arquivo**: `core/enhanced_progress.py` (novo)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

class OperationStage(Enum):
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    CONFIGURING = "configuring"
    VERIFYING = "verifying"
    COMPLETING = "completing"

@dataclass
class DetailedProgress:
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

class ProgressTracker:
    """Rastreador de progresso aprimorado"""
    
    def __init__(self, operation_id: str, component_name: str):
        self.operation_id = operation_id
        self.component_name = component_name
        self.current_progress = DetailedProgress(
            operation_id=operation_id,
            component_name=component_name,
            stage=OperationStage.PREPARING,
            progress_percent=0.0,
            current_step="Inicializando...",
            total_steps=1,
            current_step_number=0
        )
        self.callbacks = []
        self.speed_history = []
        self.max_speed_samples = 10
    
    def add_callback(self, callback):
        """Adiciona callback para updates de progresso"""
        self.callbacks.append(callback)
    
    def update_stage(self, stage: OperationStage, total_steps: int = None):
        """Atualiza estágio atual"""
        self.current_progress.stage = stage
        if total_steps:
            self.current_progress.total_steps = total_steps
        self._notify_callbacks()
    
    def update_step(self, step_number: int, step_description: str):
        """Atualiza passo atual"""
        self.current_progress.current_step_number = step_number
        self.current_progress.current_step = step_description
        self.current_progress.progress_percent = (
            step_number / self.current_progress.total_steps
        ) * 100
        self._notify_callbacks()
    
    def update_download_progress(self, downloaded: int, total: int):
        """Atualiza progresso de download com cálculo de velocidade"""
        now = datetime.now()
        
        # Calcula velocidade baseada em amostras recentes
        if self.current_progress.bytes_downloaded > 0:
            time_diff = (now - self.current_progress.last_update).total_seconds()
            if time_diff > 0:
                bytes_diff = downloaded - self.current_progress.bytes_downloaded
                speed = bytes_diff / time_diff
                
                # Mantém histórico de velocidade para suavização
                self.speed_history.append(speed)
                if len(self.speed_history) > self.max_speed_samples:
                    self.speed_history.pop(0)
                
                # Usa média das amostras recentes
                self.current_progress.download_speed = sum(self.speed_history) / len(self.speed_history)
        
        self.current_progress.bytes_downloaded = downloaded
        self.current_progress.total_bytes = total
        self.current_progress.last_update = now
        
        if total > 0:
            self.current_progress.progress_percent = (downloaded / total) * 100
        
        self._notify_callbacks()
    
    def _notify_callbacks(self):
        """Notifica todos os callbacks registrados"""
        for callback in self.callbacks:
            try:
                callback(self.current_progress)
            except Exception as e:
                print(f"Erro em callback de progresso: {e}")
```

### 1.2 Integração com Download Manager

**Modificação**: `core/download_manager.py`

```python
# Adicionar ao DownloadManager existente

def download_with_enhanced_progress(self, url: str, destination: str, 
                                  progress_tracker: ProgressTracker) -> bool:
    """Download com progresso detalhado"""
    try:
        progress_tracker.update_stage(OperationStage.DOWNLOADING)
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    progress_tracker.update_download_progress(downloaded, total_size)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        return False
```

## Prioridade 2: Enhanced UI Components

### 2.1 Componente de Progresso Avançado

**Arquivo**: `gui/enhanced_progress_widget.py` (novo)

```python
import tkinter as tk
from tkinter import ttk
from typing import Optional
from core.enhanced_progress import DetailedProgress, OperationStage

class EnhancedProgressWidget(ttk.Frame):
    """Widget de progresso com informações detalhadas"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
        self.current_progress: Optional[DetailedProgress] = None
    
    def setup_ui(self):
        """Configura a interface do widget"""
        # Frame principal
        self.grid_columnconfigure(1, weight=1)
        
        # Título do componente
        self.component_label = ttk.Label(self, text="Componente", 
                                       font=("Segoe UI", 10, "bold"))
        self.component_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        
        # Estágio atual
        self.stage_label = ttk.Label(self, text="Preparando...", 
                                   font=("Segoe UI", 9))
        self.stage_label.grid(row=1, column=0, columnspan=3, sticky="w")
        
        # Barra de progresso principal
        self.main_progress = ttk.Progressbar(self, mode='determinate', length=300)
        self.main_progress.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        
        # Informações de progresso
        progress_info_frame = ttk.Frame(self)
        progress_info_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        progress_info_frame.grid_columnconfigure(1, weight=1)
        
        # Porcentagem
        self.percent_label = ttk.Label(progress_info_frame, text="0%")
        self.percent_label.grid(row=0, column=0, sticky="w")
        
        # Velocidade e ETA (para downloads)
        self.speed_eta_label = ttk.Label(progress_info_frame, text="")
        self.speed_eta_label.grid(row=0, column=2, sticky="e")
        
        # Passo atual
        self.step_label = ttk.Label(self, text="", font=("Segoe UI", 8))
        self.step_label.grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 0))
        
        # Barra de progresso secundária (para sub-operações)
        self.sub_progress = ttk.Progressbar(self, mode='determinate', length=300)
        self.sub_progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(2, 0))
        self.sub_progress.grid_remove()  # Oculta inicialmente
    
    def update_progress(self, progress: DetailedProgress):
        """Atualiza o widget com novo progresso"""
        self.current_progress = progress
        
        # Atualiza componente
        self.component_label.config(text=progress.component_name)
        
        # Atualiza estágio
        stage_text = self._format_stage(progress.stage)
        self.stage_label.config(text=stage_text)
        
        # Atualiza barra de progresso
        self.main_progress['value'] = progress.progress_percent
        
        # Atualiza porcentagem
        self.percent_label.config(text=f"{progress.progress_percent:.1f}%")
        
        # Atualiza informações de velocidade/ETA para downloads
        if progress.stage == OperationStage.DOWNLOADING:
            speed_eta_text = f"{progress.format_speed()} • ETA: {progress.format_eta()}"
            self.speed_eta_label.config(text=speed_eta_text)
        else:
            self.speed_eta_label.config(text="")
        
        # Atualiza passo atual
        step_text = f"Passo {progress.current_step_number}/{progress.total_steps}: {progress.current_step}"
        self.step_label.config(text=step_text)
    
    def _format_stage(self, stage: OperationStage) -> str:
        """Formata nome do estágio para exibição"""
        stage_names = {
            OperationStage.PREPARING: "Preparando",
            OperationStage.DOWNLOADING: "Baixando",
            OperationStage.EXTRACTING: "Extraindo",
            OperationStage.INSTALLING: "Instalando",
            OperationStage.CONFIGURING: "Configurando",
            OperationStage.VERIFYING: "Verificando",
            OperationStage.COMPLETING: "Finalizando"
        }
        return stage_names.get(stage, str(stage.value))
    
    def show_sub_progress(self, value: float = 0):
        """Mostra barra de progresso secundária"""
        self.sub_progress.grid()
        self.sub_progress['value'] = value
    
    def hide_sub_progress(self):
        """Oculta barra de progresso secundária"""
        self.sub_progress.grid_remove()
```

### 2.2 Dashboard de Instalação em Tempo Real

**Arquivo**: `gui/realtime_installation_dashboard.py` (novo)

```python
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List, Optional
from core.enhanced_progress import DetailedProgress, ProgressTracker
from gui.enhanced_progress_widget import EnhancedProgressWidget
from gui.notification_system import NotificationCenter, NotificationLevel

class RealtimeInstallationDashboard(tk.Toplevel):
    """Dashboard de instalação em tempo real"""
    
    def __init__(self, parent, components: List[str], notification_center: NotificationCenter):
        super().__init__(parent)
        self.components = components
        self.notification_center = notification_center
        self.progress_widgets: Dict[str, EnhancedProgressWidget] = {}
        self.progress_trackers: Dict[str, ProgressTracker] = {}
        self.is_cancelled = False
        
        self.setup_window()
        self.setup_ui()
        self.center_on_parent(parent)
    
    def setup_window(self):
        """Configura janela do dashboard"""
        self.title("Instalação em Tempo Real")
        self.geometry("800x600")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Torna modal
        self.transient(self.master)
        self.grab_set()
    
    def setup_ui(self):
        """Configura interface do dashboard"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Cabeçalho
        self.setup_header(main_frame)
        
        # Área de conteúdo com abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        # Aba de progresso
        self.setup_progress_tab()
        
        # Aba de logs
        self.setup_logs_tab()
        
        # Rodapé com controles
        self.setup_footer(main_frame)
    
    def setup_header(self, parent):
        """Configura cabeçalho do dashboard"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(header_frame, 
                              text=f"Instalando {len(self.components)} componente(s)",
                              font=("Segoe UI", 12, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Status geral
        self.overall_status = ttk.Label(header_frame, text="Preparando...")
        self.overall_status.grid(row=0, column=1, sticky="e")
        
        # Progresso geral
        self.overall_progress = ttk.Progressbar(header_frame, mode='determinate')
        self.overall_progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
    
    def setup_progress_tab(self):
        """Configura aba de progresso"""
        progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(progress_frame, text="Progresso")
        
        # Canvas com scrollbar para lista de componentes
        canvas = tk.Canvas(progress_frame)
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Cria widgets de progresso para cada componente
        for i, component in enumerate(self.components):
            widget = EnhancedProgressWidget(self.scrollable_frame, padding="10")
            widget.grid(row=i, column=0, sticky="ew", pady=(0, 10))
            
            # Configura tracker de progresso
            tracker = ProgressTracker(f"install_{component}", component)
            tracker.add_callback(widget.update_progress)
            
            self.progress_widgets[component] = widget
            self.progress_trackers[component] = tracker
        
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
    
    def setup_logs_tab(self):
        """Configura aba de logs"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Área de logs
        self.log_text = scrolledtext.ScrolledText(logs_frame, 
                                                 wrap=tk.WORD, 
                                                 height=20,
                                                 font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar tags para diferentes níveis de log
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
    
    def setup_footer(self, parent):
        """Configura rodapé com controles"""
        footer_frame = ttk.Frame(parent)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Botões de controle
        button_frame = ttk.Frame(footer_frame)
        button_frame.grid(row=0, column=1, sticky="e")
        
        self.pause_button = ttk.Button(button_frame, text="Pausar", 
                                     command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancelar", 
                                      command=self.cancel_installation)
        self.cancel_button.pack(side=tk.LEFT)
    
    def get_progress_tracker(self, component: str) -> Optional[ProgressTracker]:
        """Retorna tracker de progresso para componente"""
        return self.progress_trackers.get(component)
    
    def add_log_entry(self, level: str, message: str, component: str = None):
        """Adiciona entrada ao log"""
        timestamp = tk.datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}]"
        if component:
            prefix += f" [{component}]"
        
        log_line = f"{prefix} {message}\n"
        
        self.log_text.insert(tk.END, log_line, level)
        self.log_text.see(tk.END)
    
    def update_overall_progress(self, completed: int, total: int):
        """Atualiza progresso geral"""
        progress = (completed / total) * 100 if total > 0 else 0
        self.overall_progress['value'] = progress
        self.overall_status.config(text=f"{completed}/{total} concluídos")
    
    def toggle_pause(self):
        """Alterna pausa/retomada"""
        # Implementar lógica de pausa
        current_text = self.pause_button['text']
        if current_text == "Pausar":
            self.pause_button.config(text="Retomar")
            # Pausar instalações
        else:
            self.pause_button.config(text="Pausar")
            # Retomar instalações
    
    def cancel_installation(self):
        """Cancela instalação"""
        self.is_cancelled = True
        self.destroy()
    
    def on_close(self):
        """Handler para fechamento da janela"""
        if not self.is_cancelled:
            result = tk.messagebox.askyesno(
                "Cancelar Instalação",
                "Tem certeza que deseja cancelar a instalação?"
            )
            if result:
                self.cancel_installation()
        else:
            self.destroy()
    
    def center_on_parent(self, parent):
        """Centraliza janela no pai"""
        self.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
```

## Prioridade 3: Integração com Sistema Existente

### 3.1 Modificações no Enhanced Dashboard

**Modificação**: `gui/enhanced_dashboard.py`

```python
# Adicionar ao método show_install_dialog
def show_install_dialog_with_realtime_feedback(self):
    """Mostra diálogo de instalação com feedback em tempo real"""
    if not self.components_data:
        self.notification_center.error(
            "Erro", 
            "Nenhum componente carregado"
        )
        return
    
    # Usar o novo dashboard em tempo real
    from gui.realtime_installation_dashboard import RealtimeInstallationDashboard
    
    # Selecionar componentes (pode usar diálogo existente ou simplificar)
    selected_components = self._get_selected_components()  # Implementar seleção
    
    if not selected_components:
        self.notification_center.warning(
            "Aviso",
            "Nenhum componente selecionado"
        )
        return
    
    # Criar dashboard em tempo real
    dashboard = RealtimeInstallationDashboard(
        self, 
        selected_components, 
        self.notification_center
    )
    
    # Iniciar instalação com feedback em tempo real
    self._start_realtime_installation(dashboard, selected_components)

def _start_realtime_installation(self, dashboard, components):
    """Inicia instalação com feedback em tempo real"""
    def installation_worker():
        try:
            from core.installation_manager import InstallationManager
            
            manager = InstallationManager()
            completed = 0
            
            for component in components:
                if dashboard.is_cancelled:
                    break
                
                # Obter tracker de progresso
                tracker = dashboard.get_progress_tracker(component)
                
                # Configurar callbacks no manager
                # (Requer modificação no InstallationManager)
                
                # Instalar componente
                result = manager.install_component_with_tracker(component, tracker)
                
                if result.success:
                    completed += 1
                    dashboard.add_log_entry("SUCCESS", 
                                          f"Instalação concluída com sucesso", 
                                          component)
                else:
                    dashboard.add_log_entry("ERROR", 
                                          f"Falha na instalação: {result.message}", 
                                          component)
                
                # Atualizar progresso geral
                dashboard.update_overall_progress(completed, len(components))
            
            # Finalizar
            if not dashboard.is_cancelled:
                dashboard.add_log_entry("INFO", "Instalação concluída")
                
        except Exception as e:
            dashboard.add_log_entry("ERROR", f"Erro durante instalação: {e}")
    
    # Executar em thread separada
    import threading
    thread = threading.Thread(target=installation_worker, daemon=True)
    thread.start()
```

## Cronograma de Implementação

### Semana 1
- [ ] Implementar `enhanced_progress.py`
- [ ] Modificar `download_manager.py` para suporte a progresso detalhado
- [ ] Testes básicos de progresso

### Semana 2
- [ ] Implementar `enhanced_progress_widget.py`
- [ ] Criar `realtime_installation_dashboard.py`
- [ ] Integração básica com sistema existente

### Semana 3
- [ ] Modificar `installation_manager.py` para suporte a trackers
- [ ] Integrar com `enhanced_dashboard.py`
- [ ] Testes de integração

### Semana 4
- [ ] Refinamentos de UI/UX
- [ ] Otimizações de performance
- [ ] Documentação e testes finais

## Considerações de Implementação

### Compatibilidade
- Manter APIs existentes funcionando
- Implementar feature flags para rollback
- Testes em diferentes cenários

### Performance
- Throttling de updates de UI (máximo 10 FPS)
- Batch updates quando possível
- Cleanup adequado de recursos

### Usabilidade
- Tooltips explicativos
- Keyboard shortcuts
- Acessibilidade básica

Esta implementação fornecerá uma experiência significativamente melhorada para os usuários, com feedback detalhado e controle granular sobre o processo de instalação.