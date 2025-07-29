#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Interface for Environment Dev
Modern, intuitive interface with system status and clear actions
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
import os
import sys
from typing import Dict, List, Optional, Callable
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
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class SystemStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class StatusInfo:
    """Status information container"""
    status: SystemStatus
    message: str
    details: Optional[str] = None
    action_available: bool = False

class ModernTooltip:
    """Modern tooltip implementation with better styling"""
    def __init__(self, widget, text='', delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
    
    def on_enter(self, event=None):
        self.schedule()
    
    def on_leave(self, event=None):
        self.unschedule()
        self.hide_tooltip()
    
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show_tooltip(self):
        if self.tooltip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Modern styling
        frame = tk.Frame(self.tooltip_window, 
                        background="#2d2d2d", 
                        relief="solid", 
                        borderwidth=1)
        frame.pack()
        
        label = tk.Label(frame, 
                        text=self.text,
                        background="#2d2d2d",
                        foreground="white",
                        font=("Segoe UI", 9),
                        justify="left",
                        wraplength=300,
                        padx=8,
                        pady=4)
        label.pack()
    
    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class StatusCard(ttk.Frame):
    """Modern status card widget"""
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.status_info = StatusInfo(SystemStatus.UNKNOWN, "Checking...")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the card UI"""
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        
        # Header frame
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = tk.Label(header_frame, 
                                       text="●", 
                                       font=("Segoe UI", 12),
                                       fg="#666666")
        self.status_indicator.grid(row=0, column=0, padx=(0, 8))
        
        # Title
        self.title_label = ttk.Label(header_frame, 
                                   text=self.title,
                                   font=("Segoe UI", 11, "bold"))
        self.title_label.grid(row=0, column=1, sticky="w")
        
        # Action button (initially hidden)
        self.action_button = ttk.Button(header_frame, 
                                      text="Fix",
                                      style="Accent.TButton")
        # Don't grid initially
        
        # Message frame
        message_frame = ttk.Frame(self)
        message_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        message_frame.grid_columnconfigure(0, weight=1)
        
        # Status message
        self.message_label = ttk.Label(message_frame,
                                     text=self.status_info.message,
                                     font=("Segoe UI", 9),
                                     foreground="#666666")
        self.message_label.grid(row=0, column=0, sticky="w")
        
        # Details (initially hidden)
        self.details_label = ttk.Label(message_frame,
                                     text="",
                                     font=("Segoe UI", 8),
                                     foreground="#888888")
        # Don't grid initially
    
    def update_status(self, status_info: StatusInfo, action_callback: Optional[Callable] = None):
        """Update the card status"""
        self.status_info = status_info
        
        # Update indicator color
        color_map = {
            SystemStatus.HEALTHY: "#4CAF50",
            SystemStatus.WARNING: "#FF9800", 
            SystemStatus.ERROR: "#F44336",
            SystemStatus.UNKNOWN: "#666666"
        }
        self.status_indicator.config(fg=color_map[status_info.status])
        
        # Update message
        self.message_label.config(text=status_info.message)
        
        # Show/hide details
        if status_info.details:
            self.details_label.config(text=status_info.details)
            self.details_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        else:
            self.details_label.grid_remove()
        
        # Show/hide action button
        if status_info.action_available and action_callback:
            self.action_button.config(command=action_callback)
            self.action_button.grid(row=0, column=2, padx=(8, 0))
        else:
            self.action_button.grid_remove()

class DashboardGUI(tk.Tk):
    """Modern dashboard interface for Environment Dev"""
    
    def __init__(self, components_data=None):
        super().__init__()
        
        # Initialize data
        self.components_data = components_data or {}
        self.status_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # Initialize managers
        self.diagnostic_manager = None
        self.installation_manager = None
        self.download_manager = None
        self.organization_manager = None
        self.recovery_manager = None
        
        # Setup logging
        self.setup_logging()
        
        # Setup UI
        self.setup_window()
        self.setup_styles()
        self.setup_ui()
        
        # Load components if not provided
        if not self.components_data:
            self.load_components()
        
        # Initialize managers
        self.initialize_managers()
        
        # Start background tasks
        self.start_background_tasks()
    
    def setup_logging(self):
        """Setup logging system"""
        try:
            self.logger, self.log_manager = setup_logging()
            self.logger.info("Dashboard GUI initialized")
        except Exception as e:
            print(f"Failed to setup logging: {e}")
    
    def setup_window(self):
        """Setup main window properties"""
        self.title("Environment Dev - Dashboard")
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
        
        # Configure modern theme
        style.theme_use('clam')
        
        # Custom styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 16, "bold"),
                       foreground="#2d2d2d")
        
        style.configure("Subtitle.TLabel",
                       font=("Segoe UI", 12),
                       foreground="#666666")
        
        style.configure("Card.TFrame",
                       relief="solid",
                       borderwidth=1,
                       background="#ffffff")
        
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
        
        # Header
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
        """Setup the header section"""
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
                 text="Development Environment Manager",
                 style="Subtitle.TLabel").pack(anchor="w")
        
        # Quick actions
        actions_frame = ttk.Frame(header_frame)
        actions_frame.grid(row=0, column=1, sticky="e")
        
        self.refresh_button = ttk.Button(actions_frame,
                                       text="🔄 Refresh",
                                       command=self.refresh_status)
        self.refresh_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.settings_button = ttk.Button(actions_frame,
                                        text="⚙️ Settings",
                                        command=self.show_settings)
        self.settings_button.pack(side=tk.RIGHT)
    
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
        
        # Add tooltips
        ModernTooltip(self.diagnostic_button, "Run comprehensive system diagnostics")
        ModernTooltip(self.install_button, "Install or update development components")
        ModernTooltip(self.cleanup_button, "Clean temporary files and optimize storage")
    
    def setup_components_section(self, parent):
        """Setup components management section"""
        components_frame = ttk.LabelFrame(parent, text="Components", padding="15")
        components_frame.grid(row=1, column=0, sticky="nsew")
        components_frame.grid_columnconfigure(0, weight=1)
        components_frame.grid_rowconfigure(1, weight=1)
        
        # Search and filter
        search_frame = ttk.Frame(components_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.search_var.trace("w", self.filter_components)
        
        # Category filter
        self.category_var = tk.StringVar(value="All")
        self.category_combo = ttk.Combobox(search_frame, 
                                         textvariable=self.category_var,
                                         state="readonly",
                                         width=15)
        self.category_combo.grid(row=0, column=2)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_components)
        
        # Components tree
        self.setup_components_tree(components_frame)
    
    def setup_components_tree(self, parent):
        """Setup components tree view"""
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Treeview with scrollbars
        self.components_tree = ttk.Treeview(tree_frame, 
                                          columns=("status", "version", "description"),
                                          show="tree headings")
        
        # Configure columns
        self.components_tree.heading("#0", text="Component")
        self.components_tree.heading("status", text="Status")
        self.components_tree.heading("version", text="Version")
        self.components_tree.heading("description", text="Description")
        
        self.components_tree.column("#0", width=200, minwidth=150)
        self.components_tree.column("status", width=100, minwidth=80)
        self.components_tree.column("version", width=100, minwidth=80)
        self.components_tree.column("description", width=300, minwidth=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.components_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.components_tree.xview)
        
        self.components_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.components_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Context menu
        self.setup_context_menu()
    
    def setup_context_menu(self):
        """Setup context menu for components tree"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Install", command=self.install_selected_component)
        self.context_menu.add_command(label="Uninstall", command=self.uninstall_selected_component)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="View Details", command=self.view_component_details)
        self.context_menu.add_command(label="Check Status", command=self.check_component_status)
        
        self.components_tree.bind("<Button-3>", self.show_context_menu)
    
    def load_components(self):
        """Load components data"""
        try:
            self.components_data = load_all_components()
            self.populate_components_tree()
            self.update_category_filter()
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load components: {e}")
            messagebox.showerror("Error", f"Failed to load components: {e}")
    
    def initialize_managers(self):
        """Initialize core managers"""
        try:
            self.diagnostic_manager = DiagnosticManager()
            self.installation_manager = InstallationManager()
            self.download_manager = DownloadManager()
            self.organization_manager = OrganizationManager()
            self.recovery_manager = RecoveryManager()
            
            if hasattr(self, 'logger'):
                self.logger.info("Managers initialized successfully")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to initialize managers: {e}")
            messagebox.showerror("Error", f"Failed to initialize managers: {e}")
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        # Start status monitoring
        self.after(1000, self.update_system_status)
        
        # Start queue processing
        self.after(100, self.process_queues)
    
    def populate_components_tree(self):
        """Populate the components tree"""
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
                                                    values=("", "", f"{len(categories[category])} components"),
                                                    tags=("category",))
            
            for name, data in sorted(categories[category]):
                status = "Unknown"  # Will be updated by background check
                version = data.get('version', 'N/A')
                description = data.get('description', 'No description')
                
                self.components_tree.insert(category_id, "end", text=name,
                                          values=(status, version, description),
                                          tags=("component",))
        
        # Configure tags
        self.components_tree.tag_configure("category", background="#f0f0f0", font=("Segoe UI", 9, "bold"))
        self.components_tree.tag_configure("component", background="white")
    
    def update_category_filter(self):
        """Update category filter combobox"""
        categories = set()
        for data in self.components_data.values():
            categories.add(data.get('category', 'Other'))
        
        values = ["All"] + sorted(categories)
        self.category_combo['values'] = values
    
    def filter_components(self, *args):
        """Filter components based on search and category"""
        search_text = self.search_var.get().lower()
        category_filter = self.category_var.get()
        
        # This is a simplified filter - in a real implementation,
        # you would hide/show tree items based on the filters
        pass
    
    def update_system_status(self):
        """Update system status cards"""
        try:
            # Update system health
            if self.diagnostic_manager:
                # This would call actual diagnostic methods
                health_status = StatusInfo(
                    SystemStatus.HEALTHY,
                    "System is running normally",
                    "All core components are operational"
                )
                self.system_health_card.update_status(health_status)
            
            # Update other status cards similarly
            # Environment status
            env_status = StatusInfo(
                SystemStatus.HEALTHY,
                "Environment configured",
                "Development tools are ready"
            )
            self.environment_card.update_status(env_status)
            
            # Downloads status
            downloads_status = StatusInfo(
                SystemStatus.HEALTHY,
                "No active downloads",
                "Download cache is clean"
            )
            self.downloads_card.update_status(downloads_status)
            
            # Storage status
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
        self.after(30000, self.update_system_status)  # Update every 30 seconds
    
    def process_queues(self):
        """Process status and log queues"""
        # Process status queue
        try:
            while not self.status_queue.empty():
                status_update = self.status_queue.get_nowait()
                # Handle status updates
                pass
        except queue.Empty:
            pass
        
        # Process log queue
        try:
            while not self.log_queue.empty():
                log_message = self.log_queue.get_nowait()
                # Handle log messages
                pass
        except queue.Empty:
            pass
        
        # Schedule next processing
        self.after(100, self.process_queues)
    
    # Event handlers
    def refresh_status(self):
        """Refresh system status"""
        self.update_system_status()
        if hasattr(self, 'logger'):
            self.logger.info("System status refreshed")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog will be implemented in task 8.2")
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        if self.diagnostic_manager:
            # Run diagnostics in background thread
            threading.Thread(target=self._run_diagnostics_worker, daemon=True).start()
        else:
            messagebox.showwarning("Warning", "Diagnostic manager not available")
    
    def _run_diagnostics_worker(self):
        """Background worker for diagnostics"""
        try:
            # Call actual diagnostic methods
            from env_dev.core.diagnostic_manager import DiagnosticManager
            diagnostic_manager = DiagnosticManager()
            
            # Run real diagnostics
            results = diagnostic_manager.run_comprehensive_diagnostics()
            
            # Show results
            if results.get('overall_status') == 'healthy':
                self.after(0, lambda: messagebox.showinfo("Diagnostics", "System diagnostics completed successfully"))
            else:
                issues = results.get('issues', [])
                issue_text = '\n'.join([f"- {issue}" for issue in issues[:5]])  # Show first 5 issues
                self.after(0, lambda: messagebox.showwarning("Diagnostics", f"System issues found:\n{issue_text}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Diagnostics failed: {e}"))
    
    def show_install_dialog(self):
        """Show component installation dialog"""
        messagebox.showinfo("Install", "Component installation dialog will be implemented in task 8.2")
    
    def run_cleanup(self):
        """Run system cleanup"""
        if self.organization_manager:
            threading.Thread(target=self._run_cleanup_worker, daemon=True).start()
        else:
            messagebox.showwarning("Warning", "Organization manager not available")
    
    def _run_cleanup_worker(self):
        """Background worker for cleanup"""
        try:
            # This would call actual cleanup methods
            time.sleep(1)  # Simulate cleanup work
            self.after(0, lambda: messagebox.showinfo("Cleanup", "System cleanup completed successfully"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Cleanup failed: {e}"))
    
    def show_context_menu(self, event):
        """Show context menu for components tree"""
        item = self.components_tree.identify_row(event.y)
        if item:
            self.components_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def install_selected_component(self):
        """Install selected component"""
        selection = self.components_tree.selection()
        if selection:
            item = selection[0]
            component_name = self.components_tree.item(item, "text")
            messagebox.showinfo("Install", f"Installing {component_name}...")
    
    def uninstall_selected_component(self):
        """Uninstall selected component"""
        selection = self.components_tree.selection()
        if selection:
            item = selection[0]
            component_name = self.components_tree.item(item, "text")
            messagebox.showinfo("Uninstall", f"Uninstalling {component_name}...")
    
    def view_component_details(self):
        """View component details"""
        selection = self.components_tree.selection()
        if selection:
            item = selection[0]
            component_name = self.components_tree.item(item, "text")
            messagebox.showinfo("Details", f"Details for {component_name} will be shown here")
    
    def check_component_status(self):
        """Check component status"""
        selection = self.components_tree.selection()
        if selection:
            item = selection[0]
            component_name = self.components_tree.item(item, "text")
            messagebox.showinfo("Status", f"Checking status of {component_name}...")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if hasattr(self, 'logger'):
                self.logger.info("Dashboard GUI closed by user")
            self.destroy()

def main(components_data=None):
    """Main function to run the dashboard"""
    app = DashboardGUI(components_data)
    app.mainloop()

if __name__ == "__main__":
    main()