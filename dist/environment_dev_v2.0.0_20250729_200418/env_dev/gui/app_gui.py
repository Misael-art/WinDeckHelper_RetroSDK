import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
import threading
import functools # Para usar partial em chamadas de thread
import queue # Para comunicação entre threads (GUI e instalação)
import os
import sys
import traceback
import time

# Adiciona print para debug
print("app_gui.py: Iniciando carregamento...")

# Ajusta o path para encontrar os módulos core, config, utils
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
print(f"app_gui.py: script_dir = {script_dir}")
print(f"app_gui.py: project_dir = {project_dir}")
sys.path.insert(0, project_dir)
print(f"app_gui.py: sys.path = {sys.path}")

try:
    print("app_gui.py: Tentando importar env_dev.config.loader...")
    from env_dev.config.loader import load_all_components
    print("app_gui.py: Importação de load_all_components bem-sucedida!")

    print("app_gui.py: Tentando importar env_dev.core...")
    from env_dev.core import installer
    print("app_gui.py: Importação de installer bem-sucedida!")

    print("app_gui.py: Tentando importar _verify_installation...")
    from env_dev.core.installer import _verify_installation
    print("app_gui.py: Todas as importações bem-sucedidas!")
except Exception as e:
    print(f"ERRO DE IMPORTAÇÃO em app_gui.py: {e}")
    traceback.print_exc()

# --- Classe Auxiliar para Tooltips ---
class Tooltip:
    """ Cria um tooltip (dica de ferramenta) para um widget Tkinter. """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Esconde se clicar
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # Delay de 500ms

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert") # Pega coordenadas relativas ao widget
        x += self.widget.winfo_rootx() + 25 # Calcula coordenadas absolutas da tela
        y += self.widget.winfo_rooty() + 20
        # Cria a janela toplevel
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True) # Sem decoração de janela
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength=300) # Limita largura
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

# --- Configuração do Logging para a GUI ---
# --- Configuração do Logging para a GUI ---
log_queue = queue.Queue()

class QueueHandler(logging.Handler):
    """Envia registros para uma fila."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

# Configura o logger principal para usar o QueueHandler
logger = logging.getLogger()
logger.setLevel(logging.INFO) # Ou DEBUG para mais detalhes
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(formatter)
logger.addHandler(queue_handler)
# FileHandler movido para main.py para capturar erros mais cedo

# Adiciona também um handler para o console (útil para debug inicial)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

# --- Classe Principal da GUI ---
class AppGUI(tk.Tk):
    def __init__(self, components_data=None):
        logger.info("Inicializando a interface gráfica AppGUI...")
        try:
            super().__init__()
            logger.debug("Classe base Tk inicializada com sucesso")
            
            # Armazena os dados dos componentes
            self.components_data = components_data or {}

            # Configuração da janela principal
            self.title("Environment Dev Installer")
            self.geometry("1000x700")  # Aumentando tamanho inicial da janela
            logger.debug(f"Janela configurada: título='Environment Dev Installer', tamanho=1000x700")

            # Informações do sistema
            logger.debug(f"Sistema operacional: {os.name}, Plataforma: {sys.platform}")
            logger.debug(f"Versão do Python: {sys.version}")
            logger.debug(f"Versão do Tkinter: {tk.TkVersion}")

            # Configura o protocolo de fechamento para garantir que a janela não seja fechada inadvertidamente
            self.protocol("WM_DELETE_WINDOW", self._on_closing)
            logger.debug("Protocolo de fechamento configurado")

            # Configura para que a janela fique sempre no topo para fácil visualização
            self.attributes('-topmost', True)
            self.update()
            self.attributes('-topmost', False)  # Desativa após primeiro plano garantido
            logger.debug("Atributos de janela configurados")
        except Exception as e:
            logger.critical(f"Erro fatal ao inicializar a interface gráfica: {e}")
            logger.exception("Detalhes do erro:")
            raise

        # Definindo cores para mensagens de log
        self.log_colors = {
            "ERROR": "#FF5252",  # Vermelho
            "WARNING": "#FFC107",  # Amarelo
            "INFO": "#2196F3",    # Azul
            "DEBUG": "#757575",   # Cinza
            "SUCCESS": "#4CAF50"  # Verde para mensagens de sucesso
        }

        self.components_data = {}
        self.component_widgets = {}  # Dicionário para {nome_componente: (tk.BooleanVar, ttk.Checkbutton)}
        self.installed_in_session = set()  # Rastreia instalações nesta sessão

        # Status da instalação atual
        self.current_component = None
        self.current_stage = None

        # Fila para comunicação entre threads
        self.status_queue = queue.Queue()

        # Configuração do estilo
        self._setup_styles()

        self._create_widgets()
        self._load_components_list()
        self.after(100, self._process_log_queue)  # Inicia o processamento da fila de logs
        self.after(100, self._process_status_queue)  # Inicia o processamento da fila de status de componentes

    def _setup_styles(self):
        """Configura estilos personalizados para a interface"""
        style = ttk.Style()
        style.configure("Header.TLabel", font=('TkDefaultFont', 11, 'bold'))
        style.configure("Stage.TLabel", font=('TkDefaultFont', 10))
        style.configure("Bold.TLabel", font=('TkDefaultFont', 10, 'bold'))
        style.configure("Success.TLabel", foreground='#4CAF50')
        style.configure("Error.TLabel", foreground='#FF5252')
        style.configure("Warning.TLabel", foreground='#FFC107')

    def _on_closing(self):
        """Gerencia o fechamento da janela"""
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            # Loga informação sobre o fechamento normal
            logger.info("Interface gráfica fechada pelo usuário.")
            self.destroy()

    def _create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Frame para a lista de componentes (esquerda)
        list_frame = ttk.LabelFrame(main_frame, text="Componentes Disponíveis", padding="10", width=300)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        list_frame.pack_propagate(False)  # Impede que o frame encolha quando vazio

        # Canvas e Scrollbar para a lista de checkboxes
        self.canvas = tk.Canvas(list_frame, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)  # Frame onde os checkboxes serão colocados

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Frame para controles e log (direita)
        right_frame = ttk.Frame(main_frame, padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Botão Instalar
        self.install_button = ttk.Button(right_frame, text="Instalar Selecionados", command=self._start_installation_thread)
        self.install_button.pack(pady=(0, 10), fill=tk.X)

        # Frame para informações de status
        status_frame = ttk.LabelFrame(right_frame, text="Status de Instalação", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Componente atual
        component_frame = ttk.Frame(status_frame)
        component_frame.pack(fill=tk.X, pady=2)

        ttk.Label(component_frame, text="Componente:", style="Bold.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        self.component_status_label = ttk.Label(component_frame, text="Nenhum")
        self.component_status_label.pack(side=tk.LEFT, fill=tk.X)

        # Estágio atual
        stage_frame = ttk.Frame(status_frame)
        stage_frame.pack(fill=tk.X, pady=2)

        ttk.Label(stage_frame, text="Etapa:", style="Bold.TLabel").pack(side=tk.LEFT, padx=(0, 5))
        self.stage_status_label = ttk.Label(stage_frame, text="Nenhuma")
        self.stage_status_label.pack(side=tk.LEFT, fill=tk.X)

        # Barra de progresso para downloads e operações
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X)

        # Label de porcentagem para barra de progresso
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(anchor=tk.E, pady=(2, 0))

        # Frame para visualizar o log com estilo
        log_frame = ttk.LabelFrame(right_frame, text="Log de Instalação", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        # Área de Log com tags para cores
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=12)
        self.log_text.pack(expand=True, fill=tk.BOTH)

        # Configurar tags de cores para o log
        for level, color in self.log_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def _update_progress(self, progress_value, message=""):
        """Atualiza a barra de progresso"""
        if progress_value <= 0:
            self.progress_bar["value"] = 0
        elif progress_value >= 100:
            self.progress_bar["value"] = 100
        else:
            self.progress_bar["value"] = progress_value

        self.progress_label.config(text=f"{int(progress_value)}%")
        if message:
            self.log_message(message, "INFO")

    def _update_stage(self, stage_name):
        """Atualiza o estágio atual do processo"""
        self.current_stage = stage_name
        self.stage_status_label.config(text=stage_name)
        self._update_progress(0)  # Reinicia a barra para novo estágio
        self.log_message(f"Iniciando etapa: {stage_name}", "INFO")

    def _update_component(self, component_name):
        """Atualiza o componente atual em instalação"""
        self.current_component = component_name
        self.component_status_label.config(text=component_name)
        self._update_progress(0)  # Reinicia a barra para novo componente
        self.log_message(f"Iniciando processo para: {component_name}", "INFO")

    def _load_components_list(self):
        """Carrega componentes do YAML e popula a lista de checkboxes."""
        self.components_data = load_all_components()
        if not self.components_data:
            messagebox.showerror("Erro", "Falha ao carregar componentes. Verifique o arquivo e os logs.")
            return

        # Limpa checkboxes antigos se houver recarregamento
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.component_widgets.clear()

        # Agrupa por categoria
        components_by_category = {}
        for name, data in self.components_data.items():
            category = data.get('category', 'Outros')
            if category not in components_by_category:
                components_by_category[category] = []
            components_by_category[category].append((name, data))

        # Ordena categorias e componentes dentro delas
        sorted_categories = sorted(components_by_category.keys())

        for category in sorted_categories:
            # Adiciona label da categoria
            category_label = ttk.Label(self.scrollable_frame, text=f"--- {category} ---", style="Header.TLabel")
            category_label.pack(anchor=tk.W, pady=(5, 2))

            sorted_components = sorted(components_by_category[category], key=lambda item: item[0])
            for name, data in sorted_components:
                var = tk.BooleanVar()
                description = data.get('description', 'Sem descrição disponível.')

                # Cria um frame para conter o checkbox e o ícone de info
                item_frame = ttk.Frame(self.scrollable_frame)
                item_frame.pack(anchor=tk.W, fill=tk.X, padx=5)

                # Cria o checkbox apenas com o nome
                chk = ttk.Checkbutton(item_frame, text=name, variable=var, state=tk.NORMAL)
                chk.pack(side=tk.LEFT, padx=(5, 0))

                # Cria o label com o ícone de informação
                info_icon = ttk.Label(item_frame, text="💡", cursor="hand2")
                info_icon.pack(side=tk.LEFT, padx=(2, 5))

                # Adiciona o tooltip ao ícone
                Tooltip(info_icon, text=description)

                # Armazena a variável e o widget checkbox
                self.component_widgets[name] = (var, chk)

                # Inicia a verificação em background
                threading.Thread(target=self._check_component_status_worker, args=(name, data), daemon=True).start()

    def _update_component_display(self, component_name, is_installed):
        """Atualiza o estado de um checkbox na thread principal."""
        if component_name in self.component_widgets:
            var, chk = self.component_widgets[component_name]

            if is_installed:
                chk_state = tk.DISABLED
                # Adiciona um indicador visual que está instalado
                chk.config(text=f"{component_name} [Instalado]")
            else:
                chk_state = tk.NORMAL

            chk.config(state=chk_state)
        else:
            self.log_message(f"Tentativa de atualizar componente não encontrado: {component_name}", "WARNING")

    def _check_component_status_worker(self, component_name, component_data):
        """Verifica o status de um componente em uma thread separada."""
        is_installed = False
        try:
            # Remover o parâmetro log_level que não é mais aceito
            is_installed = _verify_installation(component_name, component_data)
        except Exception as e:
            logging.error(f"Erro ao verificar o estado de '{component_name}': {e}")

        # Em vez de chamar self.after() diretamente, apenas armazena o resultado
        # que será processado pela thread principal depois
        try:
            # Envia um dicionário estruturado para a fila de status
            self.status_queue.put({'type': 'initial_status', 'component': component_name, 'installed': is_installed})
        except Exception as e:
            logging.error(f"Erro ao enfileirar status do componente '{component_name}': {e}")

    def log_message(self, message, level="INFO"):
        """Adiciona uma mensagem colorida à área de log."""
        self.log_text.configure(state='normal')

        # Detectar nível de log a partir da mensagem se não especificado
        if level == "INFO" and ":" in message:
            prefix = message.split(":", 1)[0].strip().upper()
            if "ERRO" in prefix or "FALHA" in prefix:
                level = "ERROR"
            elif "AVISO" in prefix or "ALERTA" in prefix:
                level = "WARNING"
            elif "SUCESSO" in prefix or "CONCLUÍDO" in prefix:
                level = "SUCCESS"
            elif "DEBUG" in message:
                level = "DEBUG"

        # Formatar timestamp
        timestamp = time.strftime("%H:%M:%S")

        # Aplicar cor com tag
        self.log_text.insert(tk.END, f"[{timestamp}] ", "DEBUG")
        self.log_text.insert(tk.END, f"{message}\n", level)

        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)  # Auto-scroll

    def _process_log_queue(self):
        """Processa mensagens da fila de log e as exibe na GUI."""
        while not log_queue.empty():
            try:
                record = log_queue.get_nowait()

                # Simplesmente exibe o log formatado que veio da fila
                # A detecção de nível pode ser feita aqui ou assumir que o logger já formatou
                level = "INFO" # Default level
                if "ERROR" in record or "ERRO" in record: level = "ERROR"
                elif "WARNING" in record or "AVISO" in record: level = "WARNING"
                elif "SUCCESS" in record or "Sucesso" in record: level = "SUCCESS"
                elif "DEBUG" in record: level = "DEBUG"

                self.log_message(record, level) # Passa o registro inteiro e o nível detectado

            except queue.Empty:
                break
            except Exception as e:
                # Evita que erros no processamento de log bloqueiem a GUI
                print(f"Erro ao processar log: {e}") # Mantém um print básico para erros aqui
                logger.exception(f"Erro detalhado ao processar log na GUI: {e}") # Loga o traceback completo

        # Reagenda a verificação da fila
        self.after(100, self._process_log_queue)

    def download_progress_callback(self, percent):
        """
        Callback para receber atualizações de progresso do downloader
        Esta função é chamada pelo downloader durante downloads
        """
        # Usa after para garantir que a atualização ocorra na thread principal
        self.after(0, lambda p=percent: self._update_progress(p, f"Download: {int(p)}%"))

    def _installation_task(self, components_to_install):
        """Tarefa de instalação executada em uma thread separada."""
        failed_components = []
        try:
            total_components = len(components_to_install)

            # Não é mais necessário fazer monkey-patching
            # O callback será passado diretamente para install_component
            for index, component_name in enumerate(components_to_install):
                # Atualiza o progresso geral
                overall_progress = int((index / total_components) * 100)
                self.after(0, lambda p=overall_progress: self._update_progress(p))

                # Atualiza o componente atual
                self.after(0, lambda name=component_name: self._update_component(name))

                if component_name in self.installed_in_session:
                    self.after(0, lambda msg=f"Componente '{component_name}' já instalado nesta sessão. Pulando.": self.log_message(msg, "INFO"))
                    continue

                if component_name in self.components_data:
                    self.after(0, lambda name=component_name: self.log_message(f"Iniciando instalação de {name} pela GUI...", "INFO"))
                    
                    # Modifica o status_queue global do installer para temporariamente apontar para nossa fila de status
                    from env_dev.core import installer
                    original_queue = installer.status_queue
                    installer.status_queue = self.status_queue
                    
                    try:
                        # Passa o callback diretamente para install_component
                        success = installer.install_component(
                            component_name=component_name,
                            component_data=self.components_data[component_name],
                            all_components_data=self.components_data,
                            installed_components=self.installed_in_session, # Passa o set para rastrear
                            progress_callback=self.download_progress_callback, # Passa o callback
                            rollback_mgr=None, # Permite que a função crie seu próprio RollbackManager
                            status_queue=self.status_queue # Passa explicitamente nossa fila de status
                        )
                        if not success:
                            self.after(0, lambda name=component_name: self.log_message(f"Falha geral ao instalar o componente '{name}'.", "ERROR"))
                            failed_components.append(component_name)
                    finally:
                        # Restaura a fila original
                        installer.status_queue = original_queue
                else:
                    # Esta verificação é redundante se a lista for gerada corretamente, mas segura
                    self.after(0, lambda name=component_name: self.log_message(f"Componente '{name}' selecionado mas não encontrado nos dados carregados.", "ERROR"))
                    failed_components.append(component_name)

            # Progresso final
            self.after(0, lambda: self._update_progress(100))

            # Mensagem final na GUI
            if failed_components:
                final_message = f"Instalação concluída com falhas: {', '.join(failed_components)}"
                self.after(0, lambda msg=final_message: self.log_message(msg, "WARNING"))
                # Usar messagebox na thread principal
                self.after(0, lambda: messagebox.showwarning("Instalação Concluída", final_message))
            else:
                final_message = "Todos os componentes selecionados foram instalados com sucesso!"
                self.after(0, lambda msg=final_message: self.log_message(msg, "SUCCESS"))
                self.after(0, lambda: messagebox.showinfo("Instalação Concluída", final_message))

        except Exception as e:
            error_message = f"Erro inesperado durante a instalação: {e}"
            self.after(0, lambda msg=error_message: self.log_message(msg, "ERROR"))
            self.after(0, lambda: messagebox.showerror("Erro na Instalação", error_message))
            
        finally:
            # Reabilita o botão na thread principal
            self.after(0, lambda: self.install_button.config(state=tk.NORMAL))
            # Reset do status
            self.after(0, lambda: self._update_component("Nenhum"))
            self.after(0, lambda: self._update_stage("Nenhuma"))

    def _start_installation_thread(self):
        """Inicia a instalação em uma nova thread para não bloquear a GUI."""
        selected_components = [name for name, (var, chk) in self.component_widgets.items()
                              if var.get() and str(chk.cget('state')) == str(tk.NORMAL)]

        if not selected_components:
            messagebox.showinfo("Nenhum Componente", "Selecione pelo menos um componente habilitado para instalar.")
            return

        # Lista componentes selecionados com formatação
        components_list = "\n".join([f"• {name}" for name in selected_components])
        confirm = messagebox.askyesno("Confirmar Instalação",
                                     f"Instalar os seguintes componentes?\n\n{components_list}")
        if not confirm:
            return

        # Desabilita o botão durante a instalação
        self.install_button.config(state=tk.DISABLED)

        # Reset do log e status
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')

        # Inicializa os indicadores
        self._update_component("Iniciando...")
        self._update_stage("Preparação")
        self._update_progress(0)

        # Cria e inicia a thread de instalação
        self.log_message(f"Iniciando instalação de {len(selected_components)} componentes...", "INFO")
        install_thread = threading.Thread(target=self._installation_task, args=(selected_components,), daemon=True)
        install_thread.start()

    def _process_status_queue(self):
        """Processa mensagens da fila de status de componentes."""
        while not self.status_queue.empty():
            try:
                payload = self.status_queue.get_nowait()
                
                # Verifica se o payload é um dicionário estruturado com campo 'type'
                if isinstance(payload, dict) and 'type' in payload:
                    payload_type = payload.get('type')
                    component_name = payload.get('component')

                    if payload_type == 'initial_status':
                        # Processa o status inicial verificado pelo worker da GUI
                        self._update_component_display(component_name, payload.get('installed', False))
                    elif payload_type == 'stage':
                        # Atualiza o componente e o estágio atual
                        if component_name:
                            self._update_component(component_name)
                        stage = payload.get('stage', 'Unknown Stage')
                        self._update_stage(stage)
                    elif payload_type == 'progress':
                        # Atualiza a barra de progresso
                        percent = payload.get('percent', 0.0)
                        self._update_progress(percent)
                    elif payload_type == 'result':
                        # Processa o resultado final da instalação de um componente
                        status = payload.get('status', 'UNKNOWN')
                        message = payload.get('message', '')
                        self._handle_result_status(component_name, status, message)
                    elif payload_type == 'log':
                        # Se o backend enviar logs estruturados (opcional)
                        level = payload.get('level', 'INFO')
                        message = payload.get('message', '')
                        self.log_message(f"[Backend] {message}", level)
                    elif payload_type == 'error':
                        # Processa erros estruturados
                        error_message = payload.get('message', 'Erro desconhecido')
                        category = payload.get('category', 'UNKNOWN')
                        severity = payload.get('severity', 'ERROR')
                        self.log_message(f"[{category}] {error_message}", severity)
                        
                        # Se for um erro crítico, atualiza o status do componente
                        if component_name and severity in ['ERROR', 'CRITICAL']:
                            self._handle_result_status(component_name, 'FAILED', error_message)
                    elif payload_type == 'verification_result':
                        # Processa resultados de verificação
                        status = payload.get('status', 'UNKNOWN')
                        results = payload.get('results', {})
                        message = payload.get('message', '')
                        
                        # Log do resultado de verificação
                        self.log_message(f"Verificação de {component_name}: {status}", 
                                       'SUCCESS' if status == 'SUCCESS' else 'ERROR')
                        
                        # Se houver detalhes dos resultados, mostra algumas informações
                        if isinstance(results, dict) and results.get('errors'):
                            error_count = len(results.get('errors', []))
                            self.log_message(f"  {error_count} verificação(ões) falharam", 'WARNING')
                        elif isinstance(results, list):
                            passed_count = sum(1 for r in results if r.get('passed', False))
                            total_count = len(results)
                            self.log_message(f"  {passed_count}/{total_count} verificações passaram", 
                                           'SUCCESS' if passed_count == total_count else 'WARNING')
                    else:
                        logger.debug(f"Tipo de payload de status não processado: {payload_type}")
                else:
                    logger.warning(f"Formato inválido recebido na fila de status. Esperado dicionário com campo 'type': {type(payload)}")
                    
            except queue.Empty:
                break
            except Exception as e:
                # Evita que erros no processamento de status bloqueiem a GUI
                logger.exception(f"Erro ao processar payload da fila de status: {e}")
                
        # Reagenda a verificação da fila
        self.after(100, self._process_status_queue)
        
    def _handle_result_status(self, component_name, status, message):
        """
        Processa o resultado da instalação de um componente.
        
        Args:
            component_name (str): Nome do componente
            status (str): Status da operação (SUCCESS, FAILED, WARNING, etc.)
            message (str): Mensagem adicional
        """
        try:
            if not component_name:
                logger.warning("Recebido resultado de componente sem nome.")
                return

            log_level = "INFO" # Padrão
            if status == "SUCCESS":
                log_level = "SUCCESS"
                # Marca como instalado na interface e na sessão
                self._update_component_display(component_name, True)
                self.installed_in_session.add(component_name)
                # Atualiza o status geral para indicar sucesso
                self.log_message(f"Resultado para '{component_name}': {status} - {message}", log_level)
            elif status == "FAILED":
                log_level = "ERROR"
                # Mantém o componente como não instalado na interface
                self._update_component_display(component_name, False)
                self.log_message(f"Resultado para '{component_name}': {status} - {message}", log_level)
            elif status == "WARNING":
                log_level = "WARNING"
                self.log_message(f"Aviso para '{component_name}': {message}", log_level)
            else:
                logger.warning(f"Status de resultado desconhecido '{status}' para componente '{component_name}'")
                self.log_message(f"Resultado inesperado para '{component_name}': {status} - {message}", "WARNING")

            # Garante que a última mensagem de resultado seja visível
            self.log_text.see(tk.END)
        except Exception as e:
            logger.error(f"Erro ao processar resultado do componente {component_name}: {e}", exc_info=True)
            # Adiciona o traceback completo para melhor depuração
            self.log_message(f"Erro interno ao processar status: {e}", "ERROR")


if __name__ == '__main__':
    # Para testar a GUI diretamente
    app = AppGUI()
    app.mainloop()