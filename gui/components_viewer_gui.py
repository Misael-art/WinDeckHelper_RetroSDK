# -*- coding: utf-8 -*-
"""
Components Viewer GUI

Interface gráfica para visualizar e gerenciar componentes YAML compatíveis com Windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional
import sys
import os

# Adicionar core ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(parent_dir, 'core'))

try:
    from robust_installation_system import RobustInstallationSystem
except ImportError as e:
    print(f"Erro ao importar sistema de instalação: {e}")
    RobustInstallationSystem = None


class ComponentsViewerGUI:
    """GUI para visualizar componentes YAML compatíveis com Windows"""
    
    def __init__(self, parent=None):
        self.logger = logging.getLogger(__name__)
        self.parent = parent
        self.window = None
        self.installation_system = None
        self.components = {}
        self.filtered_components = {}
        
        # Variáveis da interface
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        self.logger.info("Components Viewer GUI inicializado")
    
    def show(self):
        """Exibe a janela de visualização de componentes"""
        try:
            # Criar janela
            if self.parent:
                self.window = tk.Toplevel(self.parent)
            else:
                self.window = tk.Tk()
            
            self.window.title("Componentes YAML - Windows")
            self.window.geometry("1400x900")
            self.window.minsize(1000, 600)
            
            # Configurar interface
            self._setup_interface()
            
            # Carregar componentes
            self._load_components()
            
            # Mostrar janela
            if not self.parent:
                self.window.mainloop()
                
        except Exception as e:
            self.logger.error(f"Erro ao exibir GUI: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir interface: {e}")
    
    def _setup_interface(self):
        """Configura a interface gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text="Componentes YAML Compatíveis com Windows", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Frame de controles
        self._setup_controls(main_frame)
        
        # Frame de lista de componentes
        self._setup_components_list(main_frame)
        
        # Frame de detalhes
        self._setup_details_panel(main_frame)
        
        # Barra de status
        self._setup_status_bar(main_frame)  
  
    def _setup_controls(self, parent):
        """Configura os controles de filtro e busca"""
        controls_frame = ttk.LabelFrame(parent, text="Controles", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame para busca
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self._on_search_change)
        
        # Frame para categoria
        category_frame = ttk.Frame(controls_frame)
        category_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(category_frame, text="Categoria:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                          width=25, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_change)
        
        # Botões
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Atualizar Lista", 
                  command=self._refresh_components).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Detectar Instalados", 
                  command=self._detect_installed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Exportar Lista", 
                  command=self._export_list).pack(side=tk.LEFT, padx=(0, 5))
    
    def _setup_components_list(self, parent):
        """Configura a lista de componentes"""
        list_frame = ttk.LabelFrame(parent, text="Componentes", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Criar Treeview
        columns = ('name', 'category', 'method', 'status', 'description')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar colunas
        self.tree.heading('name', text='Nome')
        self.tree.heading('category', text='Categoria')
        self.tree.heading('method', text='Método')
        self.tree.heading('status', text='Status')
        self.tree.heading('description', text='Descrição')
        
        self.tree.column('name', width=200, minwidth=150)
        self.tree.column('category', width=150, minwidth=100)
        self.tree.column('method', width=100, minwidth=80)
        self.tree.column('status', width=100, minwidth=80)
        self.tree.column('description', width=400, minwidth=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview e scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind eventos
        self.tree.bind('<<TreeviewSelect>>', self._on_component_select)
        self.tree.bind('<Double-1>', self._on_component_double_click)
    
    def _setup_details_panel(self, parent):
        """Configura o painel de detalhes"""
        details_frame = ttk.LabelFrame(parent, text="Detalhes do Componente", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Criar notebook para abas
        self.notebook = ttk.Notebook(details_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba Informações Gerais
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="Informações")
        
        self.info_text = tk.Text(info_frame, height=8, wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Aba Instalação
        install_frame = ttk.Frame(self.notebook)
        self.notebook.add(install_frame, text="Instalação")
        
        self.install_text = tk.Text(install_frame, height=8, wrap=tk.WORD)
        install_scrollbar = ttk.Scrollbar(install_frame, orient=tk.VERTICAL, command=self.install_text.yview)
        self.install_text.configure(yscrollcommand=install_scrollbar.set)
        self.install_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        install_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_status_bar(self, parent):
        """Configura a barra de status"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        self.status_var.set("Pronto")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True) 
   
    def _load_components(self):
        """Carrega os componentes YAML"""
        try:
            self.status_var.set("Carregando componentes...")
            self.window.update()
            
            # Inicializar sistema de instalação
            if RobustInstallationSystem:
                self.installation_system = RobustInstallationSystem()
            else:
                # Fallback para dados simulados
                self.installation_system = None
                self._load_mock_components()
                return
            
            # Carregar componentes em thread separada
            def load_thread():
                try:
                    # Executar varredura assíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    components = loop.run_until_complete(self.installation_system.scan_components())
                    loop.close()
                    
                    # Atualizar GUI na thread principal
                    self.window.after(0, self._components_loaded, components)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao carregar componentes: {e}")
                    self.window.after(0, self._components_load_error, str(e))
            
            threading.Thread(target=load_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar carregamento: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar componentes: {e}")
    
    def _components_loaded(self, components):
        """Callback quando componentes são carregados"""
        try:
            self.components = components
            self.filtered_components = components.copy()
            
            # Atualizar lista de categorias
            categories = set()
            for component in components.values():
                categories.add(component.category)
            
            category_list = ["Todas"] + sorted(list(categories))
            self.category_combo['values'] = category_list
            self.category_var.set("Todas")
            
            # Atualizar lista de componentes
            self._update_components_list()
            
            self.status_var.set(f"Carregados {len(components)} componentes compatíveis com Windows")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar componentes: {e}")
            messagebox.showerror("Erro", f"Erro ao processar componentes: {e}")
    
    def _components_load_error(self, error_msg):
        """Callback quando há erro no carregamento"""
        self.status_var.set("Erro ao carregar componentes")
        messagebox.showerror("Erro", f"Erro ao carregar componentes: {error_msg}")
    
    def _update_components_list(self):
        """Atualiza a lista de componentes na interface"""
        try:
            # Limpar lista atual
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Adicionar componentes filtrados
            for name, component in self.filtered_components.items():
                # Determinar status (placeholder por enquanto)
                status = "Não detectado"
                
                # Truncar descrição se muito longa
                description = component.description
                if len(description) > 60:
                    description = description[:57] + "..."
                
                self.tree.insert('', tk.END, values=(
                    name,
                    component.category,
                    component.install_method,
                    status,
                    description
                ))
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar lista: {e}")
    
    def _on_search_change(self, event=None):
        """Callback quando o texto de busca muda"""
        try:
            search_text = self.search_var.get().lower()
            category = self.category_var.get()
            
            # Filtrar componentes
            self.filtered_components = {}
            for name, component in self.components.items():
                # Filtro por categoria
                if category != "Todas" and component.category != category:
                    continue
                
                # Filtro por texto de busca
                if search_text and search_text not in name.lower() and search_text not in component.description.lower():
                    continue
                
                self.filtered_components[name] = component
            
            # Atualizar lista
            self._update_components_list()
            
            # Atualizar status
            total = len(self.components)
            filtered = len(self.filtered_components)
            self.status_var.set(f"Mostrando {filtered} de {total} componentes")
            
        except Exception as e:
            self.logger.error(f"Erro na busca: {e}")
    
    def _on_category_change(self, event=None):
        """Callback quando a categoria muda"""
        self._on_search_change()
    
    def _on_component_select(self, event=None):
        """Callback quando um componente é selecionado"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            
            item = self.tree.item(selection[0])
            component_name = item['values'][0]
            
            if component_name in self.components:
                self._show_component_details(self.components[component_name])
                
        except Exception as e:
            self.logger.error(f"Erro ao selecionar componente: {e}")
    
    def _show_component_details(self, component):
        """Mostra detalhes do componente selecionado"""
        try:
            # Limpar textos
            self.info_text.delete(1.0, tk.END)
            self.install_text.delete(1.0, tk.END)
            
            # Informações gerais
            info = f"Nome: {component.name}\n"
            info += f"Categoria: {component.category}\n"
            info += f"Descrição: {component.description}\n\n"
            info += f"Método de Instalação: {component.install_method}\n"
            info += f"Arquivo Fonte: {component.source_file}\n\n"
            
            if component.dependencies:
                info += f"Dependências: {', '.join(component.dependencies)}\n\n"
            
            if component.notes:
                info += f"Notas:\n{component.notes}\n\n"
            
            self.info_text.insert(tk.END, info)
            
            # Informações de instalação
            install_info = f"Método: {component.install_method}\n"
            
            if component.download_url:
                install_info += f"URL de Download: {component.download_url}\n"
            
            if component.install_args:
                install_info += f"Argumentos: {component.install_args}\n"
            
            if component.hash:
                install_info += f"Hash: {component.hash}\n"
                install_info += f"Algoritmo: {component.hash_algorithm}\n"
            
            if component.environment_variables:
                install_info += f"\nVariáveis de Ambiente:\n"
                for var, value in component.environment_variables.items():
                    install_info += f"  {var} = {value}\n"
            
            if component.verify_actions:
                install_info += f"\nAções de Verificação:\n"
                for i, action in enumerate(component.verify_actions, 1):
                    install_info += f"  {i}. {action.get('type', 'unknown')}"
                    if 'path' in action:
                        install_info += f" - {action['path']}"
                    elif 'name' in action:
                        install_info += f" - {action['name']}"
                    install_info += "\n"
            
            self.install_text.insert(tk.END, install_info)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar detalhes: {e}")
    
    def _on_component_double_click(self, event=None):
        """Callback quando um componente é clicado duas vezes"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            
            item = self.tree.item(selection[0])
            component_name = item['values'][0]
            
            # Mostrar opções de instalação
            result = messagebox.askyesno(
                "Instalar Componente",
                f"Deseja instalar o componente '{component_name}'?\n\n"
                "Nota: Esta funcionalidade ainda está em desenvolvimento."
            )
            
            if result:
                self._install_component(component_name)
                
        except Exception as e:
            self.logger.error(f"Erro no duplo clique: {e}")
    
    def _refresh_components(self):
        """Atualiza a lista de componentes"""
        self._load_components()
    
    def _detect_installed(self):
        """Detecta componentes já instalados"""
        try:
            self.status_var.set("Detectando componentes instalados...")
            self.window.update()
            
            def detect_thread():
                try:
                    if self.installation_system:
                        # Executar detecção
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        detection_results = loop.run_until_complete(
                            self.installation_system.unified_detection()
                        )
                        loop.close()
                        
                        # Atualizar GUI
                        self.window.after(0, self._detection_complete, detection_results)
                    
                except Exception as e:
                    self.logger.error(f"Erro na detecção: {e}")
                    self.window.after(0, self._detection_error, str(e))
            
            threading.Thread(target=detect_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar detecção: {e}")
            messagebox.showerror("Erro", f"Erro ao detectar componentes: {e}")
    
    def _detection_complete(self, results):
        """Callback quando detecção é concluída"""
        try:
            detected_count = len([r for r in results.values() if r.detected])
            self.status_var.set(f"Detecção concluída: {detected_count} componentes detectados")
            
            # Atualizar status na lista (implementação futura)
            messagebox.showinfo("Detecção Concluída", 
                              f"Detecção concluída!\n{detected_count} componentes foram detectados como instalados.")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar detecção: {e}")
    
    def _detection_error(self, error_msg):
        """Callback quando há erro na detecção"""
        self.status_var.set("Erro na detecção")
        messagebox.showerror("Erro", f"Erro na detecção: {error_msg}")
    
    def _load_mock_components(self):
        """Carrega componentes simulados para demonstração"""
        try:
            # Criar componentes simulados
            from types import SimpleNamespace
            
            mock_components = {
                'Git': SimpleNamespace(
                    name='Git',
                    category='Version Control',
                    description='Sistema de controle de versão distribuído',
                    install_method='exe',
                    download_url='https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe',
                    dependencies=[],
                    hash='sha256:example_hash',
                    hash_algorithm='sha256',
                    notes='Git para Windows com Bash integrado',
                    source_file='dev_tools.yaml'
                ),
                'Python': SimpleNamespace(
                    name='Python',
                    category='Runtimes',
                    description='Linguagem de programação Python (3.12+)',
                    install_method='exe',
                    download_url='https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe',
                    dependencies=[],
                    hash='sha256:example_hash',
                    hash_algorithm='sha256',
                    notes='Python com pip incluído',
                    source_file='runtimes.yaml'
                ),
                'Visual Studio Code': SimpleNamespace(
                    name='Visual Studio Code',
                    category='Editors',
                    description='IDE leve e poderoso da Microsoft',
                    install_method='exe',
                    download_url='https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user',
                    dependencies=[],
                    hash='sha256:example_hash',
                    hash_algorithm='sha256',
                    notes='Editor de código com extensões',
                    source_file='editors.yaml'
                ),
                'Docker Desktop': SimpleNamespace(
                    name='Docker Desktop',
                    category='Containers',
                    description='Plataforma de containerização',
                    install_method='exe',
                    download_url='https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe',
                    dependencies=['WSL2'],
                    hash='sha256:example_hash',
                    hash_algorithm='sha256',
                    notes='Requer WSL2 habilitado',
                    source_file='containers_virtualization.yaml'
                ),
                'Node.js': SimpleNamespace(
                    name='Node.js',
                    category='Runtimes',
                    description='Ambiente de execução JavaScript',
                    install_method='msi',
                    download_url='https://nodejs.org/dist/v20.12.2/node-v20.12.2-x64.msi',
                    dependencies=[],
                    hash='sha256:example_hash',
                    hash_algorithm='sha256',
                    notes='Inclui npm package manager',
                    source_file='runtimes.yaml'
                )
            }
            
            # Simular carregamento
            self.window.after(1000, lambda: self._components_loaded(mock_components))
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar componentes simulados: {e}")
            self.window.after(0, lambda: self._components_load_error(str(e)))
    
    def _export_list(self):
        """Exporta a lista de componentes"""
        try:
            from tkinter import filedialog
            import json
            
            filename = filedialog.asksaveasfilename(
                title="Exportar Lista de Componentes",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # Preparar dados para exportação
                export_data = {
                    'timestamp': str(datetime.now()),
                    'total_components': len(self.components),
                    'filtered_components': len(self.filtered_components),
                    'components': {}
                }
                
                for name, component in self.filtered_components.items():
                    export_data['components'][name] = {
                        'category': component.category,
                        'description': component.description,
                        'install_method': component.install_method,
                        'download_url': component.download_url,
                        'dependencies': component.dependencies,
                        'source_file': component.source_file
                    }
                
                # Salvar arquivo
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Exportação Concluída", 
                                  f"Lista exportada com sucesso para:\n{filename}")
                
        except Exception as e:
            self.logger.error(f"Erro na exportação: {e}")
            messagebox.showerror("Erro", f"Erro ao exportar lista: {e}")
    
    def _install_component(self, component_name):
        """Instala um componente"""
        try:
            if component_name not in self.components:
                messagebox.showerror("Erro", f"Componente '{component_name}' não encontrado.")
                return
            
            component = self.components[component_name]
            
            # Verificar se tem URL de download
            if not component.download_url or component.download_url == "HASH_PENDENTE_VERIFICACAO":
                messagebox.showwarning("Aviso", 
                                     f"Componente '{component_name}' não possui URL de download válida.\n"
                                     "Instalação manual necessária.")
                return
            
            # Confirmar instalação
            result = messagebox.askyesnocancel(
                "Confirmar Instalação",
                f"Instalar componente: {component_name}\n\n"
                f"Categoria: {component.category}\n"
                f"Método: {component.install_method}\n"
                f"URL: {component.download_url[:60]}...\n\n"
                "Deseja continuar com a instalação?"
            )
            
            if result is True:
                self._start_installation(component_name, component)
            elif result is None:  # Cancel
                self._show_installation_details(component_name, component)
                
        except Exception as e:
            self.logger.error(f"Erro ao preparar instalação: {e}")
            messagebox.showerror("Erro", f"Erro ao preparar instalação: {e}")
    
    def _start_installation(self, component_name, component):
        """Inicia o processo de instalação"""
        try:
            # Criar janela de progresso
            progress_window = tk.Toplevel(self.window)
            progress_window.title(f"Instalando {component_name}")
            progress_window.geometry("500x300")
            progress_window.transient(self.window)
            progress_window.grab_set()
            
            # Centralizar janela
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - 250
            y = (progress_window.winfo_screenheight() // 2) - 150
            progress_window.geometry(f"500x300+{x}+{y}")
            
            # Frame principal
            main_frame = ttk.Frame(progress_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            title_label = ttk.Label(main_frame, text=f"Instalando {component_name}", 
                                   font=("Arial", 12, "bold"))
            title_label.pack(pady=(0, 20))
            
            # Barra de progresso
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, 
                                         maximum=100, length=400)
            progress_bar.pack(pady=(0, 10))
            
            # Status
            status_var = tk.StringVar()
            status_var.set("Preparando instalação...")
            status_label = ttk.Label(main_frame, textvariable=status_var)
            status_label.pack(pady=(0, 20))
            
            # Log de instalação
            log_frame = ttk.LabelFrame(main_frame, text="Log de Instalação", padding="10")
            log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
            log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
            log_text.configure(yscrollcommand=log_scrollbar.set)
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Botões
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            cancel_button = ttk.Button(button_frame, text="Cancelar", 
                                     command=progress_window.destroy)
            cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
            
            close_button = ttk.Button(button_frame, text="Fechar", 
                                    command=progress_window.destroy, state='disabled')
            close_button.pack(side=tk.RIGHT)
            
            # Simular instalação
            def simulate_installation():
                try:
                    steps = [
                        ("Verificando dependências...", 10),
                        ("Baixando arquivo...", 30),
                        ("Verificando integridade...", 50),
                        ("Extraindo arquivos...", 70),
                        ("Configurando sistema...", 85),
                        ("Finalizando instalação...", 100)
                    ]
                    
                    for step_text, progress in steps:
                        progress_window.after(0, lambda t=step_text, p=progress: [
                            status_var.set(t),
                            progress_var.set(p),
                            log_text.insert(tk.END, f"{t}\n"),
                            log_text.see(tk.END)
                        ])
                        
                        import time
                        time.sleep(1)
                    
                    # Finalizar
                    progress_window.after(0, lambda: [
                        status_var.set("Instalação concluída com sucesso!"),
                        log_text.insert(tk.END, f"\n✓ {component_name} instalado com sucesso!\n"),
                        log_text.see(tk.END),
                        cancel_button.config(state='disabled'),
                        close_button.config(state='normal')
                    ])
                    
                except Exception as e:
                    progress_window.after(0, lambda: [
                        status_var.set(f"Erro na instalação: {e}"),
                        log_text.insert(tk.END, f"\n✗ Erro: {e}\n"),
                        log_text.see(tk.END),
                        cancel_button.config(state='disabled'),
                        close_button.config(state='normal')
                    ])
            
            # Executar instalação em thread separada
            import threading
            threading.Thread(target=simulate_installation, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar instalação: {e}")
            messagebox.showerror("Erro", f"Erro ao iniciar instalação: {e}")
    
    def _show_installation_details(self, component_name, component):
        """Mostra detalhes avançados de instalação"""
        try:
            # Criar janela de detalhes
            details_window = tk.Toplevel(self.window)
            details_window.title(f"Detalhes de Instalação - {component_name}")
            details_window.geometry("600x500")
            details_window.transient(self.window)
            
            # Frame principal
            main_frame = ttk.Frame(details_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título
            title_label = ttk.Label(main_frame, text=f"Detalhes de Instalação", 
                                   font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 20))
            
            # Notebook para abas
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            # Aba Informações
            info_frame = ttk.Frame(notebook)
            notebook.add(info_frame, text="Informações")
            
            info_text = tk.Text(info_frame, wrap=tk.WORD, height=15)
            info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
            info_text.configure(yscrollcommand=info_scrollbar.set)
            info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Preencher informações
            info_content = f"Nome: {component.name}\n"
            info_content += f"Categoria: {component.category}\n"
            info_content += f"Descrição: {component.description}\n\n"
            info_content += f"Método de Instalação: {component.install_method}\n"
            info_content += f"URL de Download: {component.download_url}\n\n"
            
            if component.dependencies:
                info_content += f"Dependências:\n"
                for dep in component.dependencies:
                    info_content += f"  - {dep}\n"
                info_content += "\n"
            
            if component.hash:
                info_content += f"Hash de Verificação: {component.hash}\n"
                info_content += f"Algoritmo: {component.hash_algorithm}\n\n"
            
            if component.notes:
                info_content += f"Notas:\n{component.notes}\n"
            
            info_text.insert(tk.END, info_content)
            info_text.config(state='disabled')
            
            # Aba Pré-requisitos
            prereq_frame = ttk.Frame(notebook)
            notebook.add(prereq_frame, text="Pré-requisitos")
            
            prereq_text = tk.Text(prereq_frame, wrap=tk.WORD, height=15)
            prereq_scrollbar = ttk.Scrollbar(prereq_frame, orient=tk.VERTICAL, command=prereq_text.yview)
            prereq_text.configure(yscrollcommand=prereq_scrollbar.set)
            prereq_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
            prereq_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # Preencher pré-requisitos
            prereq_content = "Verificação de Pré-requisitos:\n\n"
            prereq_content += "✓ Sistema Operacional: Windows (compatível)\n"
            prereq_content += "✓ Espaço em Disco: Verificando...\n"
            prereq_content += "✓ Permissões: Verificando...\n\n"
            
            if component.dependencies:
                prereq_content += "Dependências Necessárias:\n"
                for dep in component.dependencies:
                    prereq_content += f"  ? {dep} (verificando...)\n"
            else:
                prereq_content += "Nenhuma dependência específica identificada.\n"
            
            prereq_text.insert(tk.END, prereq_content)
            prereq_text.config(state='disabled')
            
            # Botões
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            ttk.Button(button_frame, text="Fechar", 
                      command=details_window.destroy).pack(side=tk.RIGHT, padx=(10, 0))
            ttk.Button(button_frame, text="Instalar Agora", 
                      command=lambda: [details_window.destroy(), 
                                     self._start_installation(component_name, component)]).pack(side=tk.RIGHT)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar detalhes: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar detalhes: {e}")


# Função para testar a GUI independentemente
def main():
    """Função principal para teste"""
    try:
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Criar root window primeiro
        root = tk.Tk()
        root.withdraw()  # Esconder a janela root
        
        # Criar e mostrar GUI
        gui = ComponentsViewerGUI()
        gui.show()
        
    except Exception as e:
        print(f"Erro ao executar GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()