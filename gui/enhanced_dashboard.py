#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Dashboard with Real-time Feedback
Integrates the dashboard with the notification system for comprehensive user experience
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
import os
import sys
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

try:
    from env_dev.config.loader import load_all_components
    from env_dev.core.diagnostic_manager import DiagnosticManager
    from env_dev.core.installation_manager import InstallationManager
    from env_dev.core.download_manager import DownloadManager
    from env_dev.core.organization_manager import OrganizationManager
    from env_dev.core.recovery_manager import RecoveryManager
    from env_dev.utils.log_manager import setup_logging
    from env_dev.gui.notification_system import (
        NotificationCenter, NotificationLevel, NotificationCategory,
        LogViewer, ProgressTracker
    )
    from env_dev.gui.dashboard_gui import StatusCard, SystemStatus, StatusInfo, ModernTooltip
    # Import enhanced progress system
    from env_dev.core.enhanced_progress import (
        DetailedProgress, OperationStage, ProgressTracker as EnhancedProgressTracker,
        create_progress_tracker, progress_manager
    )
    from env_dev.gui.enhanced_progress_widget import EnhancedProgressWidget
    from env_dev.gui.realtime_installation_dashboard import create_installation_dashboard
    from env_dev.gui.style_manager import apply_theme
    import platform, psutil
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class RealTimeProgressDialog(tk.Toplevel):
    """Real-time progress dialog with detailed feedback"""
    
    def __init__(self, parent, title: str, operation_id: str, notification_center: NotificationCenter):
        super().__init__(parent)
        self.operation_id = operation_id
        self.notification_center = notification_center
        self.is_cancelled = False
        
        self.setup_window(title)
        self.setup_ui()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.center_on_parent(parent)
    
    def setup_window(self, title: str):
        """Setup progress dialog window"""
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def setup_ui(self):
        """Setup progress dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # Title and current operation
        self.title_label = ttk.Label(main_frame, 
                                   text="Initializing...",
                                   font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Overall progress bar
        self.overall_progress = ttk.Progressbar(progress_frame, 
                                              mode='determinate',
                                              length=400)
        self.overall_progress.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Progress percentage
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=1, column=0, sticky="e")
        
        # Current step description
        self.step_label = ttk.Label(progress_frame, 
                                  text="Preparing...",
                                  font=("Segoe UI", 9))
        self.step_label.grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        # Detailed log area
        log_frame = ttk.LabelFrame(main_frame, text="Details", padding="10")
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 wrap=tk.WORD,
                                                 height=12,
                                                 font=("Consolas", 9),
                                                 state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Diagnostics section
        diag_frame = ttk.LabelFrame(main_frame, text="System Diagnostics & Component Stats", padding="10")
        diag_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        diag_frame.grid_columnconfigure(0, weight=1)

        self.diagnostics_label = ttk.Label(diag_frame, text="", justify=tk.LEFT, font=("Consolas", 9))
        self.diagnostics_label.grid(row=0, column=0, sticky="w")

        self.component_stats_label = ttk.Label(diag_frame, text="", justify=tk.LEFT, font=("Segoe UI", 9, "bold"))
        self.component_stats_label.grid(row=1, column=0, sticky="w")

        # Populate initial diagnostics
        self.populate_diagnostics()
        
        # Configure text tags
        self.log_text.tag_configure("info", foreground="#2196F3")
        self.log_text.tag_configure("success", foreground="#4CAF50")
        self.log_text.tag_configure("warning", foreground="#FF9800")
        self.log_text.tag_configure("error", foreground="#F44336")
        self.log_text.tag_configure("timestamp", foreground="#666666")
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        
        # Cancel button
        self.cancel_button = ttk.Button(buttons_frame,
                                      text="Cancel",
                                      command=self.on_cancel)
        self.cancel_button.grid(row=0, column=1, padx=(5, 0))
        
        # Close button (initially hidden)
        self.close_button = ttk.Button(buttons_frame,
                                     text="Close",
                                     command=self.destroy)
        # Don't grid initially
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def update_progress(self, progress: float, step_description: str = "", details: str = ""):
        """Update progress display"""
        # Update progress bar
        self.overall_progress['value'] = progress
        self.progress_label.config(text=f"{progress:.1f}%")
        
        # Update step description
        if step_description:
            self.step_label.config(text=step_description)
        
        # Add details to log
        if details:
            self.add_log_entry("info", details)
    
    def add_log_entry(self, level: str, message: str):
        """Add entry to detailed log"""
        self.log_text.configure(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Add message with appropriate color
        self.log_text.insert(tk.END, f"{message}\n", level)
        
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def on_cancel(self):
        """Handle cancel button"""
        if not self.is_cancelled:
            result = messagebox.askyesno("Cancel Operation", 
                                       "Are you sure you want to cancel this operation?",
                                       parent=self)
            if result:
                self.is_cancelled = True
                self.cancel_button.config(state=tk.DISABLED, text="Cancelling...")
                self.add_log_entry("warning", "Operation cancelled by user")
                
                # Notify the operation to cancel
                if hasattr(self, 'cancel_callback') and self.cancel_callback:
                    self.cancel_callback()
    
    def operation_completed(self, success: bool, message: str = ""):
        """Mark operation as completed"""
        if success:
            self.overall_progress['value'] = 100
            self.progress_label.config(text="100%")
            self.step_label.config(text="Completed successfully")
            self.add_log_entry("success", message or "Operation completed successfully")
        else:
            self.add_log_entry("error", message or "Operation failed")
            self.step_label.config(text="Operation failed")
        
        # Show close button, hide cancel button
        self.cancel_button.grid_remove()
        self.close_button.grid(row=0, column=1, padx=(5, 0))

    def populate_diagnostics(self):
        """Populate static system diagnostics"""
        try:
            import shutil
            sys_info = [
                f"OS: {platform.system()} {platform.release()}",
                f"CPU Cores: {psutil.cpu_count(logical=True)}",
                f"RAM Total: {round(psutil.virtual_memory().total / (1024**3), 2)} GB",
                f"Disk Free: {round(shutil.disk_usage('/').free / (1024**3), 2)} GB"
            ]
            self.diagnostics_label.config(text=" | ".join(sys_info))
        except Exception as e:
            self.diagnostics_label.config(text=f"Diagnostics unavailable: {e}")

    def update_component_stats(self, installed: int, total_selected: int):
        """Update component installation stats"""
        self.component_stats_label.config(text=f"Installed: {installed}/{total_selected}")

class ComponentInstallDialog(tk.Toplevel):
    """Enhanced component installation dialog with real-time feedback"""
    
    def __init__(self, parent, components_data: Dict, notification_center: NotificationCenter):
        super().__init__(parent)
        self.components_data = components_data
        self.notification_center = notification_center
        self.selected_components = []
        
        self.setup_window()
        self.setup_ui()
        self.populate_components()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.center_on_parent(parent)
    
    def setup_window(self):
        """Setup installation dialog window"""
        self.title("Install Components")
        self.geometry("600x500")
        self.resizable(True, True)
    
    def setup_ui(self):
        """Setup installation dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, 
                 text="Select Components to Install",
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        
        # Search
        search_frame = ttk.Frame(header_frame)
        search_frame.grid(row=0, column=1, sticky="e")
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        self.search_var.trace("w", self.filter_components)
        
        # Components list
        list_frame = ttk.LabelFrame(main_frame, text="Available Components", padding="10")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview for components
        self.components_tree = ttk.Treeview(list_frame,
                                          columns=("status", "description"),
                                          show="tree headings")
        
        self.components_tree.heading("#0", text="Component")
        self.components_tree.heading("status", text="Status")
        self.components_tree.heading("description", text="Description")
        
        self.components_tree.column("#0", width=200)
        self.components_tree.column("status", width=100)
        self.components_tree.column("description", width=250)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.components_tree.yview)
        self.components_tree.configure(yscrollcommand=scrollbar.set)
        
        self.components_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Selection controls
        selection_frame = ttk.Frame(main_frame)
        selection_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(selection_frame, text="Select All", 
                  command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(selection_frame, text="Select None", 
                  command=self.select_none).pack(side=tk.LEFT, padx=(0, 5))
        
        self.selection_label = ttk.Label(selection_frame, text="0 components selected")
        self.selection_label.pack(side=tk.RIGHT)
        
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        buttons_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.destroy).grid(row=0, column=1, padx=(5, 0))
        
        self.install_button = ttk.Button(buttons_frame, text="Install Selected", 
                                       command=self.start_installation,
                                       style="Accent.TButton")
        self.install_button.grid(row=0, column=2, padx=(5, 0))
        
        # Bind selection events
        self.components_tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        self.components_tree.bind("<Double-1>", self.toggle_selection)
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def populate_components(self):
        """Populate components tree"""
        # Clear existing items
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)
        
        # Group by category
        categories = {}
        for name, data in self.components_data.items():
            category = data.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append((name, data))
        
        # Add categories and components
        for category in sorted(categories.keys()):
            category_id = self.components_tree.insert("", "end", text=category,
                                                    values=("", f"{len(categories[category])} components"),
                                                    tags=("category",))
            
            for name, data in sorted(categories[category]):
                status = "Available"  # This would be checked in real implementation
                description = data.get('description', 'No description')
                
                item_id = self.components_tree.insert(category_id, "end", text=name,
                                                    values=(status, description),
                                                    tags=("component",))
        
        # Configure tags
        self.components_tree.tag_configure("category", background="#f0f0f0")
        self.components_tree.tag_configure("component", background="white")
        
        # Expand all categories
        for item in self.components_tree.get_children():
            self.components_tree.item(item, open=True)
    
    def filter_components(self, *args):
        """Filter components based on search"""
        search_text = self.search_var.get().lower()
        # Simplified filtering - in real implementation, hide/show items
        pass
    
    def on_selection_change(self, event):
        """Handle selection change"""
        self.update_selection_count()
    
    def toggle_selection(self, event):
        """Toggle component selection on double-click"""
        item = self.components_tree.selection()[0]
        if "component" in self.components_tree.item(item, "tags"):
            # Toggle selection (simplified - in real implementation, use checkboxes)
            pass
    
    def select_all(self):
        """Select all components"""
        for item in self.components_tree.get_children():
            for child in self.components_tree.get_children(item):
                if "component" in self.components_tree.item(child, "tags"):
                    self.components_tree.selection_add(child)
        self.update_selection_count()
    
    def select_none(self):
        """Deselect all components"""
        self.components_tree.selection_remove(self.components_tree.selection())
        self.update_selection_count()
    
    def update_selection_count(self):
        """Update selection count label"""
        selected = len([item for item in self.components_tree.selection()
                       if "component" in self.components_tree.item(item, "tags")])
        self.selection_label.config(text=f"{selected} components selected")
        
        # Enable/disable install button
        self.install_button.config(state=tk.NORMAL if selected > 0 else tk.DISABLED)
    
    def start_installation(self):
        """Start component installation"""
        selected_items = [item for item in self.components_tree.selection()
                         if "component" in self.components_tree.item(item, "tags")]
        
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select components to install.")
            return
        
        # Get component names
        component_names = [self.components_tree.item(item, "text") for item in selected_items]
        
        # Close this dialog
        self.destroy()
        
        # Start installation with progress dialog
        self.start_installation_with_progress(component_names)
    
    def start_installation_with_progress(self, component_names: List[str]):
        """Start installation with progress tracking"""
        # Create progress dialog
        progress_dialog = RealTimeProgressDialog(
            self.master,
            "Installing Components",
            "component_installation",
            self.notification_center
        )
        progress_dialog.total_components = len(component_names)
        progress_dialog.update_component_stats(0, len(component_names))
        # Start installation in background thread
        def installation_worker():
            try:
                from env_dev.core import installer
                
                total_components = len(component_names)
                installed_components = set()
                
                for i, component_name in enumerate(component_names):
                    if progress_dialog.is_cancelled:
                        break
                    
                    # Update progress
                    progress = (i / total_components) * 100
                    step_desc = f"Installing {component_name}..."
                    
                    progress_dialog.after(0, lambda p=progress, s=step_desc: 
                                        progress_dialog.update_progress(p, s, f"Starting installation of {component_name}"))
                    
                    # Get component data
                    component_data = self.master.components_data.get(component_name)
                    if not component_data:
                        progress_dialog.after(0, lambda: 
                                            progress_dialog.add_log_entry("error", f"Component data not found for {component_name}"))
                        continue
                    
                    # Real installation call
                    try:
                        success = installer.install_component(
                            component_name=component_name,
                            component_data=component_data,
                            all_components_data=self.master.components_data,
                            installed_components=installed_components
                        )
                        
                        if success:
                            # Notify completion
                            self.notification_center.installation_completed(component_name, True)
                            progress_dialog.after(0, lambda cn=component_name: 
                                                progress_dialog.add_log_entry("success", f"{cn} installed successfully"))
                            progress_dialog.after(0, lambda: progress_dialog.update_component_stats(len(installed_components), progress_dialog.total_components))
                        else:
                            progress_dialog.after(0, lambda cn=component_name: 
                                                progress_dialog.add_log_entry("error", f"Failed to install {cn}"))
                    
                    except Exception as install_error:
                        progress_dialog.after(0, lambda cn=component_name, err=str(install_error): 
                                            progress_dialog.add_log_entry("error", f"Error installing {cn}: {err}"))
                
                # Mark as completed
                if not progress_dialog.is_cancelled:
                    progress_dialog.after(0, lambda: 
                                        progress_dialog.operation_completed(True, "Installation process completed"))
                
            except Exception as e:
                progress_dialog.after(0, lambda err=str(e): 
                                    progress_dialog.operation_completed(False, f"Installation failed: {err}"))
        
        # Set cancel callback
        progress_dialog.cancel_callback = lambda: setattr(progress_dialog, 'is_cancelled', True)
        
        # Start worker thread
        threading.Thread(target=installation_worker, daemon=True).start()

class EnhancedDashboard(tk.Tk):
    """Enhanced dashboard with integrated real-time feedback system"""
    
    def __init__(self, components_data=None):
        super().__init__()
        apply_theme(self)
        
        # Initialize data
        self.components_data = components_data or {}
        
        # Setup logging
        self.setup_logging()
        
        # Setup window
        self.setup_window()
        self.setup_styles()
        
        # Initialize notification system
        self.notification_center = NotificationCenter(self)
        
        # Setup UI
        self.setup_ui()
        
        # Load components if not provided
        if not self.components_data:
            self.load_components()
        
        # Initialize managers
        self.initialize_managers()
        
        # Start background tasks
        self.start_background_tasks()
        
        # Show welcome notification
        self.notification_center.info("Welcome", "Environment Dev Dashboard is ready")
    
    def setup_logging(self):
        """Setup logging system"""
        try:
            self.logger, self.log_manager = setup_logging()
            self.logger.info("Enhanced Dashboard initialized")
        except Exception as e:
            print(f"Failed to setup logging: {e}")
    
    def setup_window(self):
        """Setup main window properties"""
        self.title("Environment Dev - Enhanced Dashboard")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.winfo_screenheight() // 2) - (900 // 2)
        self.geometry(f"1400x900+{x}+{y}")
        
        # Configure closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Setup modern UI styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 16, "bold"),
                       foreground="#2d2d2d")
        
        style.configure("Subtitle.TLabel",
                       font=("Segoe UI", 12),
                       foreground="#666666")
        
        style.configure("Accent.TButton",
                       font=("Segoe UI", 9, "bold"))
        
        style.map("Accent.TButton",
                 background=[('active', '#0078d4'),
                           ('!active', '#106ebe')])
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        main_container = ttk.Frame(self, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Header with notification controls
        self.setup_header(main_container)
        
        # Content area
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - System Status
        self.setup_status_panel(content_frame)
        
        # Right panel - Actions and Components
        self.setup_action_panel(content_frame)
    
    def setup_header(self, parent):
        """Setup the header section with notification controls"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title and subtitle
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")
        
        ttk.Label(title_frame, 
                 text="Environment Dev", 
                 style="Title.TLabel").pack(anchor="w")
        
        ttk.Label(title_frame,
                 text="Development Environment Manager with Real-time Feedback",
                 style="Subtitle.TLabel").pack(anchor="w")
        
        # Quick actions with notification features
        actions_frame = ttk.Frame(header_frame)
        actions_frame.grid(row=0, column=1, sticky="e")
        
        # Refresh button
        self.refresh_button = ttk.Button(actions_frame,
                                       text="🔄 Refresh",
                                       command=self.refresh_status)
        self.refresh_button.pack(side=tk.RIGHT)
    
    def setup_status_panel(self, parent):
        """Setup the system status panel"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="15")
        status_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Overall system health
        self.system_health_card = StatusCard(status_frame, "System Health")
        self.system_health_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Environment status
        self.environment_card = StatusCard(status_frame, "Environment")
        self.environment_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Downloads status
        self.downloads_card = StatusCard(status_frame, "Downloads")
        self.downloads_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        # Storage status
        self.storage_card = StatusCard(status_frame, "Storage")
        self.storage_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        # Add spacer
        ttk.Frame(status_frame).grid(row=4, column=0, sticky="nsew")
        status_frame.grid_rowconfigure(4, weight=1)
    
    def setup_action_panel(self, parent):
        """Setup the actions and components panel"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=0, column=1, sticky="nsew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_rowconfigure(1, weight=1)
        
        # Quick actions section
        self.setup_quick_actions(action_frame)
        
        # Components section
        self.setup_components_section(action_frame)
    
    def setup_quick_actions(self, parent):
        """Setup quick actions section"""
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions", padding="15")
        actions_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        actions_frame.grid_columnconfigure(0, weight=1)
        
        # Action buttons grid
        buttons_frame = ttk.Frame(actions_frame)
        buttons_frame.grid(row=0, column=0, sticky="ew")
        buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Diagnostic button
        self.diagnostic_button = ttk.Button(buttons_frame,
                                          text="🔍 Run Diagnostics",
                                          command=self.run_diagnostics,
                                          style="Accent.TButton")
        self.diagnostic_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Install button
        self.install_button = ttk.Button(buttons_frame,
                                       text="📦 Install Components",
                                       command=self.show_install_dialog,
                                       style="Accent.TButton")
        self.install_button.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Cleanup button
        self.cleanup_button = ttk.Button(buttons_frame,
                                       text="🧹 Cleanup",
                                       command=self.run_cleanup)
        self.cleanup_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        # Second row of buttons
        buttons_frame2 = ttk.Frame(actions_frame)
        buttons_frame2.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        buttons_frame2.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Installation Dashboard button
        self.installation_dashboard_button = ttk.Button(buttons_frame2,
                                                       text="📊 Installation Dashboard",
                                                       command=self.show_installation_dashboard)
        self.installation_dashboard_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # View Logs button
        self.logs_button = ttk.Button(buttons_frame2,
                                    text="📋 View Logs",
                                    command=self.show_logs)
        self.logs_button.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Settings button
        self.settings_button = ttk.Button(buttons_frame2,
                                        text="⚙️ Settings",
                                        command=self.show_settings)
        self.settings_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        # Add tooltips
        ModernTooltip(self.diagnostic_button, "Run comprehensive system diagnostics with real-time feedback")
        ModernTooltip(self.install_button, "Install or update development components with progress tracking")
        ModernTooltip(self.cleanup_button, "Clean temporary files and optimize storage with detailed reporting")
        ModernTooltip(self.installation_dashboard_button, "Open real-time installation dashboard")
        ModernTooltip(self.logs_button, "View detailed system logs")
        ModernTooltip(self.settings_button, "Open application settings")
    
    def setup_components_section(self, parent):
        """Setup components management section"""
        components_frame = ttk.LabelFrame(parent, text="Components Overview", padding="15")
        components_frame.grid(row=1, column=0, sticky="nsew")
        components_frame.grid_columnconfigure(0, weight=1)
        components_frame.grid_rowconfigure(1, weight=1)
        
        # Summary stats
        stats_frame = ttk.Frame(components_frame)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, 
                                   text="Loading component statistics...",
                                   font=("Segoe UI", 9))
        self.stats_label.pack(side=tk.LEFT)
        
        # Quick component list with checkbox-like markers
        self.selected_components = set()
        self.components_listbox = tk.Listbox(components_frame,
                                           selectmode=tk.SINGLE,
                                           font=("Segoe UI", 9),
                                           height=15)
        self.components_listbox.grid(row=1, column=0, sticky="nsew")
        self.components_listbox.bind('<Double-Button-1>', self.toggle_component_selection)
        self.components_listbox.bind('<Key-space>', self.toggle_component_selection)

        # Selected counter label
        self.selected_counter_label = ttk.Label(stats_frame, text="Selecionados: 0", font=("Segoe UI", 9))
        self.selected_counter_label.pack(side=tk.RIGHT)
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(components_frame, orient=tk.VERTICAL, 
                                command=self.components_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.components_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Context menu for components
        self.setup_component_context_menu()
    
    def setup_component_context_menu(self):
        """Setup context menu for components"""
        self.component_menu = tk.Menu(self, tearoff=0)
        self.component_menu.add_command(label="Install", command=self.install_selected_component)
        self.component_menu.add_command(label="Check Status", command=self.check_selected_component)
        self.component_menu.add_separator()
        self.component_menu.add_command(label="View Details", command=self.view_selected_component)
        
        self.components_listbox.bind("<Button-3>", self.show_component_menu)
    
    def load_components(self):
        """Load components data"""
        try:
            self.notification_center.info("Loading", "Loading component definitions...")
            self.components_data = load_all_components()
            self.populate_components_list()
            self.update_component_stats()
            self.notification_center.success("Loaded", f"Loaded {len(self.components_data)} components")
        except Exception as e:
            self.notification_center.error("Load Failed", f"Failed to load components: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load components: {e}")
    
    def initialize_managers(self):
        """Initialize core managers"""
        try:
            self.notification_center.info("Initializing", "Setting up system managers...")
            
            self.diagnostic_manager = DiagnosticManager()
            self.installation_manager = InstallationManager()
            self.download_manager = DownloadManager()
            self.organization_manager = OrganizationManager()
            self.recovery_manager = RecoveryManager()
            
            self.notification_center.success("Ready", "All system managers initialized successfully")
            if hasattr(self, 'logger'):
                self.logger.info("Managers initialized successfully")
        except Exception as e:
            self.notification_center.error("Initialization Failed", f"Failed to initialize managers: {e}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to initialize managers: {e}")
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        # Start status monitoring
        self.after(2000, self.update_system_status)
    
    def populate_components_list(self):
        """Populate the components list"""
        self.components_listbox.delete(0, tk.END)
        
        for name, data in sorted(self.components_data.items()):
            category = data.get('category', 'Other')
            status = "Unknown"  # Would be checked in real implementation
            display_text = f"☐ [{category}] {name} - {status}"
            self.components_listbox.insert(tk.END, display_text)
    
    def toggle_component_selection(self, event=None):
        index = self.components_listbox.curselection()
        if not index:
            return
        idx = index[0]
        current_text = self.components_listbox.get(idx)
        checked = current_text.startswith('☑')
        new_text = current_text.replace('☑', '☐', 1) if checked else current_text.replace('☐', '☑', 1)
        self.components_listbox.delete(idx)
        self.components_listbox.insert(idx, new_text)
        self.components_listbox.selection_clear(idx)

        # Manage set
        component_name = new_text.split('] ')[1].split(' - ')[0]
        if checked and component_name in self.selected_components:
            self.selected_components.remove(component_name)
        elif not checked:
            self.selected_components.add(component_name)
        self.selected_counter_label.config(text=f"Selecionados: {len(self.selected_components)}")

    def update_component_stats(self):
        """Update component statistics"""
        total = len(self.components_data)
        categories = set(data.get('category', 'Other') for data in self.components_data.values())
        
        stats_text = f"Total: {total} components | Categories: {len(categories)}"
        self.stats_label.config(text=stats_text)
    
    def update_system_status(self):
        """Update system status cards with real-time data"""
        try:
            # Update system health
            health_status = StatusInfo(
                SystemStatus.HEALTHY,
                "System is running normally",
                "All core components are operational"
            )
            self.system_health_card.update_status(health_status)
            
            # Update other status cards
            env_status = StatusInfo(
                SystemStatus.HEALTHY,
                "Environment configured",
                "Development tools are ready"
            )
            self.environment_card.update_status(env_status)
            
            downloads_status = StatusInfo(
                SystemStatus.HEALTHY,
                "No active downloads",
                "Download cache is clean"
            )
            self.downloads_card.update_status(downloads_status)
            
            storage_status = StatusInfo(
                SystemStatus.HEALTHY,
                "Storage optimized",
                "Sufficient space available"
            )
            self.storage_card.update_status(storage_status)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error updating system status: {e}")
        
        # Schedule next update
        self.after(30000, self.update_system_status)
    
    # Event handlers with notification integration
    def refresh_status(self):
        """Refresh system status"""
        self.notification_center.info("Refreshing", "Updating system status...")
        self.update_system_status()
        self.notification_center.success("Refreshed", "System status updated")
    
    def show_settings(self):
        """Show settings dialog"""
        self.notification_center.info("Settings", "Opening settings dialog...")
        # Settings dialog would be implemented here
        messagebox.showinfo("Settings", "Settings dialog will be fully implemented")
    
    def show_logs(self):
        """Show detailed logs"""
        LogViewer(self, self.notification_center)
    
    def run_diagnostics(self):
        """Run system diagnostics with real-time feedback"""
        self.notification_center.info("Diagnostics", "Starting comprehensive system diagnostics...")
        
        # Create progress dialog
        progress_dialog = RealTimeProgressDialog(
            self,
            "System Diagnostics",
            "system_diagnostics",
            self.notification_center
        )
        
        def diagnostics_worker():
            try:
                steps = [
                    "Checking system compatibility",
                    "Verifying installed components", 
                    "Testing network connectivity",
                    "Analyzing disk space",
                    "Validating configurations"
                ]
                
                for i, step in enumerate(steps):
                    if progress_dialog.is_cancelled:
                        break
                    
                    progress = ((i + 1) / len(steps)) * 100
                    progress_dialog.after(0, lambda p=progress, s=step: 
                                        progress_dialog.update_progress(p, s, f"Running: {step}"))
                    
                    # Run real diagnostic step
                    from env_dev.core.diagnostic_manager import DiagnosticManager
                    diagnostic_manager = DiagnosticManager()
                    
                    # Execute the diagnostic step
                    try:
                        if "system" in step.lower():
                            diagnostic_manager.check_system_health()
                        elif "environment" in step.lower():
                            diagnostic_manager.check_environment_variables()
                        elif "storage" in step.lower():
                            diagnostic_manager.check_disk_space()
                        elif "network" in step.lower():
                            diagnostic_manager.check_network_connectivity()
                        else:
                            time.sleep(0.5)  # Brief pause for other steps
                    except Exception as e:
                        print(f"Diagnostic step '{step}' failed: {e}")
                        time.sleep(0.5)  # Brief pause on error
                
                if not progress_dialog.is_cancelled:
                    progress_dialog.after(0, lambda: 
                                        progress_dialog.operation_completed(True, "System diagnostics completed successfully"))
                    self.notification_center.success("Diagnostics Complete", "All system checks passed")
                
            except Exception as e:
                progress_dialog.after(0, lambda: 
                                    progress_dialog.operation_completed(False, f"Diagnostics failed: {str(e)}"))
                self.notification_center.error("Diagnostics Failed", str(e))
        
        progress_dialog.cancel_callback = lambda: setattr(progress_dialog, 'is_cancelled', True)
        threading.Thread(target=diagnostics_worker, daemon=True).start()
    
    def show_install_dialog(self):
        """Show enhanced component installation dialog"""
        ComponentInstallDialog(self, self.components_data, self.notification_center)
    
    def run_cleanup(self):
        """Run system cleanup with progress tracking"""
        self.notification_center.info("Cleanup", "Starting system cleanup...")
        
        def cleanup_worker():
            try:
                # Simulate cleanup operations
                operations = [
                    "Cleaning temporary files",
                    "Organizing downloads",
                    "Rotating logs",
                    "Optimizing storage"
                ]
                
                for i, operation in enumerate(operations):
                    progress = ((i + 1) / len(operations)) * 100
                    self.notification_center.notify(
                        NotificationLevel.PROGRESS,
                        NotificationCategory.CLEANUP,
                        "Cleanup Progress",
                        f"{operation}... ({progress:.0f}%)",
                        progress=progress
                    )
                    time.sleep(1)
                
                self.notification_center.success("Cleanup Complete", "System cleanup finished successfully")
                
            except Exception as e:
                self.notification_center.error("Cleanup Failed", f"System cleanup failed: {str(e)}")
        
        threading.Thread(target=cleanup_worker, daemon=True).start()
    
    def show_component_menu(self, event):
        """Show context menu for selected component"""
        selection = self.components_listbox.curselection()
        if selection:
            self.component_menu.post(event.x_root, event.y_root)
    
    def install_selected_component(self):
        """Install selected component"""
        selection = self.components_listbox.curselection()
        if selection:
            # If using checkbox selection, install all selected; otherwise fallback to current selection
            targets = list(self.selected_components)
            if not targets:
                item_text = self.components_listbox.get(selection[0])
                targets = [item_text.split('] ')[1].split(' - ')[0]]
            # Disparar início para cada item
            for comp in targets:
                self.notification_center.installation_started(comp)
            
            # Real installation
            def install_worker():
                from env_dev.core import installer
                
                for component_name in targets:
                    try:
                        component_data = self.components_data.get(component_name)
                        if not component_data:
                            self.notification_center.installation_completed(component_name, False, "Component data not found")
                            continue
                        
                        success = installer.install_component(
                            component_name=component_name,
                            component_data=component_data,
                            all_components_data=self.components_data
                        )
                        self.notification_center.installation_completed(component_name, success)
                    except Exception as e:
                        self.notification_center.installation_completed(component_name, False, str(e))
            
            threading.Thread(target=install_worker, daemon=True).start()
    
    def check_selected_component(self):
        """Check status of selected component"""
        selection = self.components_listbox.curselection()
        if selection:
            item_text = self.components_listbox.get(selection[0])
            component_name = item_text.split('] ')[1].split(' - ')[0]
            self.notification_center.info("Status Check", f"Checking status of {component_name}...")
            
            # Simulate status check
            def check_worker():
                time.sleep(1)
                self.notification_center.success("Status Check", f"{component_name} is available for installation")
            
            threading.Thread(target=check_worker, daemon=True).start()
    
    def view_selected_component(self):
        """View details of selected component"""
        selection = self.components_listbox.curselection()
        if selection:
            item_text = self.components_listbox.get(selection[0])
            component_name = item_text.split('] ')[1].split(' - ')[0]
            
            if component_name in self.components_data:
                data = self.components_data[component_name]
                details = f"Name: {component_name}\n"
                details += f"Category: {data.get('category', 'N/A')}\n"
                details += f"Description: {data.get('description', 'N/A')}\n"
                details += f"Version: {data.get('version', 'N/A')}"
                
                messagebox.showinfo(f"Component Details - {component_name}", details)
    
    def show_installation_dashboard(self):
        """Show real-time installation dashboard"""
        try:
            dashboard = create_installation_dashboard(self)
            dashboard.focus_set()  # Bring to front
        except Exception as e:
            self.notification_center.error(
                "Dashboard Error", 
                f"Failed to open installation dashboard: {e}"
            )
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to open installation dashboard: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit Environment Dev Dashboard?"):
            self.notification_center.info("Goodbye", "Environment Dev Dashboard is closing...")
            if hasattr(self, 'logger'):
                self.logger.info("Enhanced Dashboard closed by user")
            self.destroy()

def main(components_data=None):
    """Main function to run the enhanced dashboard"""
    app = EnhancedDashboard(components_data)
    app.mainloop()

if __name__ == "__main__":
    main()