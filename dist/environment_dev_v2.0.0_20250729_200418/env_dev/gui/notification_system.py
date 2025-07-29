#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Notification System for Environment Dev
Provides non-intrusive status updates, progress tracking, and error reporting
"""

import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"

class NotificationCategory(Enum):
    """Notification categories"""
    SYSTEM = "system"
    INSTALLATION = "installation"
    DOWNLOAD = "download"
    DIAGNOSTIC = "diagnostic"
    CLEANUP = "cleanup"
    USER_ACTION = "user_action"

@dataclass
class Notification:
    """Notification data structure"""
    id: str
    level: NotificationLevel
    category: NotificationCategory
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    progress: Optional[float] = None
    details: Optional[str] = None
    action_text: Optional[str] = None
    action_callback: Optional[Callable] = None
    auto_dismiss: bool = True
    dismiss_after: int = 5000  # milliseconds
    persistent: bool = False

class ProgressTracker:
    """Tracks progress for long-running operations"""
    
    def __init__(self, operation_id: str, total_steps: int, description: str = ""):
        self.operation_id = operation_id
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = datetime.now()
        self.step_descriptions = {}
        self.is_complete = False
        self.is_cancelled = False
        self.error_message = None
    
    def update_step(self, step: int, step_description: str = ""):
        """Update current step"""
        self.current_step = min(step, self.total_steps)
        if step_description:
            self.step_descriptions[step] = step_description
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
    
    def get_current_description(self) -> str:
        """Get current step description"""
        return self.step_descriptions.get(self.current_step, self.description)
    
    def complete(self):
        """Mark operation as complete"""
        self.current_step = self.total_steps
        self.is_complete = True
    
    def cancel(self, error_message: str = ""):
        """Cancel operation"""
        self.is_cancelled = True
        self.error_message = error_message

class NotificationToast(tk.Toplevel):
    """Modern toast notification widget"""
    
    def __init__(self, parent, notification: Notification):
        super().__init__(parent)
        self.notification = notification
        self.parent_window = parent
        
        self.setup_window()
        self.setup_ui()
        self.position_window()
        
        # Auto-dismiss timer
        if notification.auto_dismiss and not notification.persistent:
            self.after(notification.dismiss_after, self.dismiss)
    
    def setup_window(self):
        """Setup toast window properties"""
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        
        # Configure for modern appearance
        if hasattr(self, 'wm_attributes'):
            try:
                self.wm_attributes('-transparentcolor', 'grey')
            except tk.TclError:
                pass  # Not supported on all platforms
    
    def setup_ui(self):
        """Setup toast UI"""
        # Main frame with modern styling
        main_frame = tk.Frame(self, 
                             bg=self.get_background_color(),
                             relief='solid',
                             borderwidth=1,
                             padx=15,
                             pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with icon and title
        header_frame = tk.Frame(main_frame, bg=self.get_background_color())
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Icon
        icon_label = tk.Label(header_frame,
                             text=self.get_icon(),
                             font=("Segoe UI", 12),
                             fg=self.get_accent_color(),
                             bg=self.get_background_color())
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Title
        title_label = tk.Label(header_frame,
                              text=self.notification.title,
                              font=("Segoe UI", 10, "bold"),
                              fg=self.get_text_color(),
                              bg=self.get_background_color())
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Close button
        close_button = tk.Label(header_frame,
                               text="×",
                               font=("Segoe UI", 12, "bold"),
                               fg="#666666",
                               bg=self.get_background_color(),
                               cursor="hand2")
        close_button.pack(side=tk.RIGHT)
        close_button.bind("<Button-1>", lambda e: self.dismiss())
        close_button.bind("<Enter>", lambda e: close_button.config(fg="#333333"))
        close_button.bind("<Leave>", lambda e: close_button.config(fg="#666666"))
        
        # Message
        message_label = tk.Label(main_frame,
                                text=self.notification.message,
                                font=("Segoe UI", 9),
                                fg=self.get_text_color(),
                                bg=self.get_background_color(),
                                wraplength=300,
                                justify=tk.LEFT)
        message_label.pack(fill=tk.X, pady=(0, 8))
        
        # Progress bar (if applicable)
        if self.notification.progress is not None:
            progress_frame = tk.Frame(main_frame, bg=self.get_background_color())
            progress_frame.pack(fill=tk.X, pady=(0, 8))
            
            self.progress_bar = ttk.Progressbar(progress_frame,
                                              mode='determinate',
                                              length=280)
            self.progress_bar.pack(fill=tk.X)
            self.progress_bar['value'] = self.notification.progress
            
            # Progress text
            progress_text = f"{self.notification.progress:.1f}%"
            progress_label = tk.Label(progress_frame,
                                    text=progress_text,
                                    font=("Segoe UI", 8),
                                    fg=self.get_text_color(),
                                    bg=self.get_background_color())
            progress_label.pack(anchor=tk.E, pady=(2, 0))
        
        # Action button (if applicable)
        if self.notification.action_text and self.notification.action_callback:
            action_button = tk.Button(main_frame,
                                    text=self.notification.action_text,
                                    font=("Segoe UI", 9),
                                    bg=self.get_accent_color(),
                                    fg="white",
                                    relief='flat',
                                    padx=12,
                                    pady=4,
                                    cursor="hand2",
                                    command=self.handle_action)
            action_button.pack(anchor=tk.E, pady=(4, 0))
        
        # Details (if applicable)
        if self.notification.details:
            details_label = tk.Label(main_frame,
                                   text=self.notification.details,
                                   font=("Segoe UI", 8),
                                   fg="#666666",
                                   bg=self.get_background_color(),
                                   wraplength=300,
                                   justify=tk.LEFT)
            details_label.pack(fill=tk.X, pady=(4, 0))
    
    def get_background_color(self) -> str:
        """Get background color based on notification level"""
        colors = {
            NotificationLevel.INFO: "#ffffff",
            NotificationLevel.SUCCESS: "#f8fff8",
            NotificationLevel.WARNING: "#fffbf0",
            NotificationLevel.ERROR: "#fff5f5",
            NotificationLevel.PROGRESS: "#f0f8ff"
        }
        return colors.get(self.notification.level, "#ffffff")
    
    def get_accent_color(self) -> str:
        """Get accent color based on notification level"""
        colors = {
            NotificationLevel.INFO: "#2196F3",
            NotificationLevel.SUCCESS: "#4CAF50",
            NotificationLevel.WARNING: "#FF9800",
            NotificationLevel.ERROR: "#F44336",
            NotificationLevel.PROGRESS: "#2196F3"
        }
        return colors.get(self.notification.level, "#2196F3")
    
    def get_text_color(self) -> str:
        """Get text color"""
        return "#333333"
    
    def get_icon(self) -> str:
        """Get icon based on notification level"""
        icons = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.PROGRESS: "⏳"
        }
        return icons.get(self.notification.level, "ℹ️")
    
    def position_window(self):
        """Position toast in bottom-right corner"""
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Get window dimensions
        window_width = self.winfo_reqwidth()
        window_height = self.winfo_reqheight()
        
        # Position in bottom-right with margin
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        
        self.geometry(f"+{x}+{y}")
        
        # Animate in
        self.animate_in()
    
    def animate_in(self):
        """Animate toast sliding in"""
        # Simple fade-in animation
        for alpha in [0.1, 0.3, 0.5, 0.7, 0.9, 0.95]:
            self.attributes('-alpha', alpha)
            self.update()
            time.sleep(0.02)
    
    def animate_out(self, callback=None):
        """Animate toast sliding out"""
        # Simple fade-out animation
        for alpha in [0.8, 0.6, 0.4, 0.2, 0.0]:
            self.attributes('-alpha', alpha)
            self.update()
            time.sleep(0.02)
        
        if callback:
            callback()
    
    def handle_action(self):
        """Handle action button click"""
        if self.notification.action_callback:
            try:
                self.notification.action_callback()
            except Exception as e:
                print(f"Error executing notification action: {e}")
        self.dismiss()
    
    def dismiss(self):
        """Dismiss the toast"""
        self.animate_out(lambda: self.destroy())

class NotificationCenter:
    """Central notification management system"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.notifications = {}  # id -> notification
        self.active_toasts = {}  # id -> toast widget
        self.progress_trackers = {}  # operation_id -> ProgressTracker
        self.notification_queue = queue.Queue()
        self.notification_history = []
        self.max_history = 100
        
        # Start processing notifications
        self.start_processing()
    
    def start_processing(self):
        """Start processing notification queue"""
        self.process_queue()
    
    def process_queue(self):
        """Process pending notifications"""
        try:
            while not self.notification_queue.empty():
                notification = self.notification_queue.get_nowait()
                self.show_notification(notification)
        except queue.Empty:
            pass
        
        # Schedule next processing
        self.parent_window.after(100, self.process_queue)
    
    def notify(self, 
               level: NotificationLevel,
               category: NotificationCategory,
               title: str,
               message: str,
               **kwargs) -> str:
        """Create and queue a notification"""
        notification_id = f"{category.value}_{int(time.time() * 1000)}"
        
        notification = Notification(
            id=notification_id,
            level=level,
            category=category,
            title=title,
            message=message,
            **kwargs
        )
        
        self.notifications[notification_id] = notification
        self.notification_queue.put(notification)
        
        # Add to history
        self.notification_history.append(notification)
        if len(self.notification_history) > self.max_history:
            self.notification_history.pop(0)
        
        return notification_id
    
    def show_notification(self, notification: Notification):
        """Show notification toast"""
        try:
            # Dismiss existing toast with same category if not persistent
            for toast_id, toast in list(self.active_toasts.items()):
                existing_notification = self.notifications.get(toast_id)
                if (existing_notification and 
                    existing_notification.category == notification.category and
                    not existing_notification.persistent):
                    toast.dismiss()
                    del self.active_toasts[toast_id]
            
            # Create new toast
            toast = NotificationToast(self.parent_window, notification)
            self.active_toasts[notification.id] = toast
            
            # Remove from active toasts when dismissed
            original_destroy = toast.destroy
            def cleanup_destroy():
                if notification.id in self.active_toasts:
                    del self.active_toasts[notification.id]
                original_destroy()
            toast.destroy = cleanup_destroy
            
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def update_progress(self, operation_id: str, step: int, step_description: str = ""):
        """Update progress for an operation"""
        if operation_id in self.progress_trackers:
            tracker = self.progress_trackers[operation_id]
            tracker.update_step(step, step_description)
            
            # Update existing progress notification
            progress_percentage = tracker.get_progress_percentage()
            current_description = tracker.get_current_description()
            
            self.notify(
                NotificationLevel.PROGRESS,
                NotificationCategory.SYSTEM,
                f"Progress: {tracker.description}",
                f"{current_description} ({progress_percentage:.1f}%)",
                progress=progress_percentage,
                persistent=True,
                auto_dismiss=False
            )
    
    def start_progress_tracking(self, operation_id: str, total_steps: int, description: str = "") -> ProgressTracker:
        """Start tracking progress for an operation"""
        tracker = ProgressTracker(operation_id, total_steps, description)
        self.progress_trackers[operation_id] = tracker
        
        # Show initial progress notification
        self.notify(
            NotificationLevel.PROGRESS,
            NotificationCategory.SYSTEM,
            f"Starting: {description}",
            "Initializing...",
            progress=0.0,
            persistent=True,
            auto_dismiss=False
        )
        
        return tracker
    
    def complete_progress_tracking(self, operation_id: str, success: bool = True, message: str = ""):
        """Complete progress tracking for an operation"""
        if operation_id in self.progress_trackers:
            tracker = self.progress_trackers[operation_id]
            
            if success:
                tracker.complete()
                self.notify(
                    NotificationLevel.SUCCESS,
                    NotificationCategory.SYSTEM,
                    f"Completed: {tracker.description}",
                    message or "Operation completed successfully",
                    progress=100.0
                )
            else:
                tracker.cancel(message)
                self.notify(
                    NotificationLevel.ERROR,
                    NotificationCategory.SYSTEM,
                    f"Failed: {tracker.description}",
                    message or "Operation failed",
                    persistent=True
                )
            
            # Clean up tracker
            del self.progress_trackers[operation_id]
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss a specific notification"""
        if notification_id in self.active_toasts:
            self.active_toasts[notification_id].dismiss()
    
    def dismiss_category(self, category: NotificationCategory):
        """Dismiss all notifications of a specific category"""
        for notification_id, toast in list(self.active_toasts.items()):
            notification = self.notifications.get(notification_id)
            if notification and notification.category == category:
                toast.dismiss()
    
    def get_notification_history(self, category: Optional[NotificationCategory] = None) -> List[Notification]:
        """Get notification history, optionally filtered by category"""
        if category:
            return [n for n in self.notification_history if n.category == category]
        return self.notification_history.copy()
    
    def clear_history(self):
        """Clear notification history"""
        self.notification_history.clear()
    
    # Convenience methods for common notification types
    def info(self, title: str, message: str, **kwargs):
        """Show info notification"""
        return self.notify(NotificationLevel.INFO, NotificationCategory.SYSTEM, title, message, **kwargs)
    
    def success(self, title: str, message: str, **kwargs):
        """Show success notification"""
        return self.notify(NotificationLevel.SUCCESS, NotificationCategory.SYSTEM, title, message, **kwargs)
    
    def warning(self, title: str, message: str, **kwargs):
        """Show warning notification"""
        return self.notify(NotificationLevel.WARNING, NotificationCategory.SYSTEM, title, message, **kwargs)
    
    def error(self, title: str, message: str, **kwargs):
        """Show error notification"""
        return self.notify(NotificationLevel.ERROR, NotificationCategory.SYSTEM, title, message, **kwargs)
    
    def installation_started(self, component_name: str):
        """Notify installation started"""
        return self.notify(
            NotificationLevel.INFO,
            NotificationCategory.INSTALLATION,
            "Installation Started",
            f"Installing {component_name}...",
            persistent=True,
            auto_dismiss=False
        )
    
    def installation_completed(self, component_name: str, success: bool = True):
        """Notify installation completed"""
        if success:
            return self.notify(
                NotificationLevel.SUCCESS,
                NotificationCategory.INSTALLATION,
                "Installation Complete",
                f"{component_name} installed successfully"
            )
        else:
            return self.notify(
                NotificationLevel.ERROR,
                NotificationCategory.INSTALLATION,
                "Installation Failed",
                f"Failed to install {component_name}",
                persistent=True
            )
    
    def download_progress(self, filename: str, progress: float):
        """Notify download progress"""
        return self.notify(
            NotificationLevel.PROGRESS,
            NotificationCategory.DOWNLOAD,
            "Downloading",
            f"Downloading {filename}...",
            progress=progress,
            persistent=True,
            auto_dismiss=False
        )
    
    def download_completed(self, filename: str, success: bool = True):
        """Notify download completed"""
        if success:
            return self.notify(
                NotificationLevel.SUCCESS,
                NotificationCategory.DOWNLOAD,
                "Download Complete",
                f"{filename} downloaded successfully"
            )
        else:
            return self.notify(
                NotificationLevel.ERROR,
                NotificationCategory.DOWNLOAD,
                "Download Failed",
                f"Failed to download {filename}",
                persistent=True
            )

class LogViewer(tk.Toplevel):
    """Advanced log viewer with search and filtering"""
    
    def __init__(self, parent, notification_center: NotificationCenter):
        super().__init__(parent)
        self.notification_center = notification_center
        
        self.setup_window()
        self.setup_ui()
        self.load_logs()
    
    def setup_window(self):
        """Setup log viewer window"""
        self.title("System Logs")
        self.geometry("800x600")
        self.transient(self.master)
        self.grab_set()
    
    def setup_ui(self):
        """Setup log viewer UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        
        # Search and filter frame
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filter_frame.grid_columnconfigure(1, weight=1)
        
        # Search
        ttk.Label(filter_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.search_var.trace("w", self.filter_logs)
        
        # Level filter
        ttk.Label(filter_frame, text="Level:").grid(row=0, column=2, padx=(0, 5))
        self.level_var = tk.StringVar(value="All")
        level_combo = ttk.Combobox(filter_frame, textvariable=self.level_var, 
                                  values=["All", "INFO", "SUCCESS", "WARNING", "ERROR"],
                                  state="readonly", width=10)
        level_combo.grid(row=0, column=3, padx=(0, 10))
        level_combo.bind("<<ComboboxSelected>>", self.filter_logs)
        
        # Clear button
        clear_button = ttk.Button(filter_frame, text="Clear", command=self.clear_logs)
        clear_button.grid(row=0, column=4)
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(side=tk.LEFT)
        
        # Log text area
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, 
                               wrap=tk.WORD,
                               font=("Consolas", 9),
                               state=tk.DISABLED)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        h_scrollbar = ttk.Scrollbar(log_frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        
        self.log_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.log_text.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure text tags for colors
        self.log_text.tag_configure("INFO", foreground="#2196F3")
        self.log_text.tag_configure("SUCCESS", foreground="#4CAF50")
        self.log_text.tag_configure("WARNING", foreground="#FF9800")
        self.log_text.tag_configure("ERROR", foreground="#F44336")
        self.log_text.tag_configure("timestamp", foreground="#666666")
    
    def load_logs(self):
        """Load logs from notification history"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        history = self.notification_center.get_notification_history()
        
        for notification in history:
            timestamp = notification.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            level = notification.level.value.upper()
            
            # Insert timestamp
            self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Insert level
            self.log_text.insert(tk.END, f"{level}: ", level)
            
            # Insert message
            self.log_text.insert(tk.END, f"{notification.title} - {notification.message}\n")
            
            # Insert details if available
            if notification.details:
                self.log_text.insert(tk.END, f"    Details: {notification.details}\n", "timestamp")
        
        self.log_text.configure(state=tk.DISABLED)
        self.update_stats()
    
    def filter_logs(self, *args):
        """Filter logs based on search and level"""
        # This is a simplified implementation
        # In a real application, you would implement proper filtering
        self.load_logs()
    
    def clear_logs(self):
        """Clear all logs"""
        self.notification_center.clear_history()
        self.load_logs()
    
    def update_stats(self):
        """Update log statistics"""
        history = self.notification_center.get_notification_history()
        total = len(history)
        
        level_counts = {}
        for notification in history:
            level = notification.level.value.upper()
            level_counts[level] = level_counts.get(level, 0) + 1
        
        stats_text = f"Total: {total}"
        for level, count in level_counts.items():
            stats_text += f" | {level}: {count}"
        
        self.stats_label.config(text=stats_text)

# Example usage and testing
if __name__ == "__main__":
    # Create test window
    root = tk.Tk()
    root.title("Notification System Test")
    root.geometry("400x300")
    
    # Create notification center
    notification_center = NotificationCenter(root)
    
    # Test buttons
    def test_info():
        notification_center.info("Information", "This is an info message")
    
    def test_success():
        notification_center.success("Success", "Operation completed successfully")
    
    def test_warning():
        notification_center.warning("Warning", "This is a warning message")
    
    def test_error():
        notification_center.error("Error", "Something went wrong")
    
    def test_progress():
        tracker = notification_center.start_progress_tracking("test_op", 5, "Test Operation")
        
        def update_progress(step):
            if step <= 5:
                notification_center.update_progress("test_op", step, f"Step {step} of 5")
                root.after(1000, lambda: update_progress(step + 1))
            else:
                notification_center.complete_progress_tracking("test_op", True, "All steps completed")
        
        update_progress(1)
    
    def show_logs():
        LogViewer(root, notification_center)
    
    # Create test buttons
    ttk.Button(root, text="Info", command=test_info).pack(pady=5)
    ttk.Button(root, text="Success", command=test_success).pack(pady=5)
    ttk.Button(root, text="Warning", command=test_warning).pack(pady=5)
    ttk.Button(root, text="Error", command=test_error).pack(pady=5)
    ttk.Button(root, text="Progress", command=test_progress).pack(pady=5)
    ttk.Button(root, text="Show Logs", command=show_logs).pack(pady=5)
    
    root.mainloop()