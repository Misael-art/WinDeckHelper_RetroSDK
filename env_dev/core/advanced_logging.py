#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Logging and Reporting System for Environment Dev
Provides organized, searchable logs and automatic report generation with performance metrics
"""

import logging
import json
import csv
import sqlite3
import threading
import time
import psutil
import os
import sys
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import shutil
from collections import defaultdict, deque
import re

# Import notification manager for integration
from env_dev.core.notification_manager import (
    NotificationManager, NotificationSeverity, OperationCategory,
    get_notification_manager
)

class LogLevel(Enum):
    """Enhanced log levels"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class LogCategory(Enum):
    """Log categories for organization"""
    SYSTEM = "system"
    APPLICATION = "application"
    INSTALLATION = "installation"
    DOWNLOAD = "download"
    DIAGNOSTIC = "diagnostic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER_ACTION = "user_action"
    ERROR = "error"
    AUDIT = "audit"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    operation_id: Optional[str] = None
    component: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    performance_data: Optional[Dict[str, float]] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics data"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int
    operation_id: Optional[str] = None
    component: Optional[str] = None

@dataclass
class ReportConfig:
    """Report generation configuration"""
    name: str
    description: str
    categories: List[LogCategory]
    levels: List[LogLevel]
    time_range: timedelta
    include_performance: bool = True
    include_statistics: bool = True
    include_trends: bool = True
    format: str = "html"  # html, json, csv, pdf
    auto_generate: bool = False
    generation_interval: timedelta = timedelta(hours=24)

class AdvancedLogHandler(logging.Handler):
    """Advanced log handler with structured logging and search capabilities"""
    
    def __init__(self, log_manager):
        super().__init__()
        self.log_manager = log_manager
        self.setLevel(logging.DEBUG)
    
    def emit(self, record):
        """Emit a log record"""
        try:
            # Extract structured information
            log_entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=LogLevel(record.levelno),
                category=self._determine_category(record),
                logger_name=record.name,
                message=record.getMessage(),
                module=record.module if hasattr(record, 'module') else record.filename,
                function=record.funcName,
                line_number=record.lineno,
                thread_id=record.thread,
                process_id=record.process,
                operation_id=getattr(record, 'operation_id', None),
                component=getattr(record, 'component', None),
                user_id=getattr(record, 'user_id', None),
                session_id=getattr(record, 'session_id', None),
                tags=getattr(record, 'tags', []),
                metadata=getattr(record, 'metadata', {}),
                stack_trace=self.format(record) if record.exc_info else None
            )
            
            # Add performance data if available
            if hasattr(record, 'performance_data'):
                log_entry.performance_data = record.performance_data
            
            # Send to log manager
            self.log_manager.add_log_entry(log_entry)
            
        except Exception as e:
            # Fallback to prevent logging loops
            print(f"Error in AdvancedLogHandler: {e}", file=sys.stderr)
    
    def _determine_category(self, record) -> LogCategory:
        """Determine log category based on record information"""
        logger_name = record.name.lower()
        message = record.getMessage().lower()
        
        # Category mapping based on logger name and message content
        if 'install' in logger_name or 'install' in message:
            return LogCategory.INSTALLATION
        elif 'download' in logger_name or 'download' in message:
            return LogCategory.DOWNLOAD
        elif 'diagnostic' in logger_name or 'diagnostic' in message:
            return LogCategory.DIAGNOSTIC
        elif 'performance' in logger_name or 'performance' in message:
            return LogCategory.PERFORMANCE
        elif 'security' in logger_name or 'security' in message:
            return LogCategory.SECURITY
        elif 'error' in logger_name or record.levelno >= logging.ERROR:
            return LogCategory.ERROR
        elif 'audit' in logger_name or 'audit' in message:
            return LogCategory.AUDIT
        elif 'user' in logger_name or 'user' in message:
            return LogCategory.USER_ACTION
        elif 'system' in logger_name or 'system' in message:
            return LogCategory.SYSTEM
        else:
            return LogCategory.APPLICATION

class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self, log_manager, monitoring_interval: float = 5.0):
        self.log_manager = log_manager
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.process = psutil.Process()
        
        # Baseline metrics
        self.baseline_metrics = None
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 measurements
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                self.log_manager.add_performance_metrics(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"Error in performance monitoring: {e}", file=sys.stderr)
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        try:
            # CPU and memory
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Disk I/O
            disk_io = self.process.io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024)
            disk_write_mb = disk_io.write_bytes / (1024 * 1024)
            
            # Network I/O (system-wide)
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024 * 1024)
            net_recv_mb = net_io.bytes_recv / (1024 * 1024)
            
            # Thread and file counts
            active_threads = self.process.num_threads()
            open_files = len(self.process.open_files())
            
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_info.rss / (1024 * 1024),
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                active_threads=active_threads,
                open_files=open_files
            )
            
        except Exception as e:
            # Return minimal metrics on error
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_threads=0,
                open_files=0
            )
    
    def get_performance_summary(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get performance summary for specified time range"""
        if not self.metrics_history:
            return {}
        
        # Filter by time range if specified
        if time_range:
            cutoff_time = datetime.now() - time_range
            filtered_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        else:
            filtered_metrics = list(self.metrics_history)
        
        if not filtered_metrics:
            return {}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in filtered_metrics]
        memory_values = [m.memory_percent for m in filtered_metrics]
        memory_mb_values = [m.memory_used_mb for m in filtered_metrics]
        
        return {
            'time_range': {
                'start': filtered_metrics[0].timestamp.isoformat(),
                'end': filtered_metrics[-1].timestamp.isoformat(),
                'duration_minutes': (filtered_metrics[-1].timestamp - filtered_metrics[0].timestamp).total_seconds() / 60
            },
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'current': cpu_values[-1] if cpu_values else 0
            },
            'memory': {
                'avg_percent': sum(memory_values) / len(memory_values),
                'min_percent': min(memory_values),
                'max_percent': max(memory_values),
                'current_percent': memory_values[-1] if memory_values else 0,
                'avg_mb': sum(memory_mb_values) / len(memory_mb_values),
                'min_mb': min(memory_mb_values),
                'max_mb': max(memory_mb_values),
                'current_mb': memory_mb_values[-1] if memory_mb_values else 0
            },
            'threads': {
                'avg': sum(m.active_threads for m in filtered_metrics) / len(filtered_metrics),
                'min': min(m.active_threads for m in filtered_metrics),
                'max': max(m.active_threads for m in filtered_metrics),
                'current': filtered_metrics[-1].active_threads
            },
            'files': {
                'avg': sum(m.open_files for m in filtered_metrics) / len(filtered_metrics),
                'min': min(m.open_files for m in filtered_metrics),
                'max': max(m.open_files for m in filtered_metrics),
                'current': filtered_metrics[-1].open_files
            }
        }

class LogDatabase:
    """SQLite database for log storage and searching"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database schema"""
        with self.lock:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS log_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    thread_id INTEGER,
                    process_id INTEGER,
                    operation_id TEXT,
                    component TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    tags TEXT,
                    metadata TEXT,
                    stack_trace TEXT,
                    performance_data TEXT
                )
            ''')
            
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_io_read_mb REAL,
                    disk_io_write_mb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    active_threads INTEGER,
                    open_files INTEGER,
                    operation_id TEXT,
                    component TEXT
                )
            ''')
            
            # Create indexes for better search performance
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON log_entries(timestamp)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_level ON log_entries(level)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_category ON log_entries(category)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_operation_id ON log_entries(operation_id)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_component ON log_entries(component)')
            
            self.connection.commit()
    
    def add_log_entry(self, entry: LogEntry):
        """Add a log entry to the database"""
        with self.lock:
            self.connection.execute('''
                INSERT INTO log_entries (
                    timestamp, level, category, logger_name, message, module, function,
                    line_number, thread_id, process_id, operation_id, component, user_id,
                    session_id, tags, metadata, stack_trace, performance_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.timestamp.isoformat(),
                entry.level.value,
                entry.category.value,
                entry.logger_name,
                entry.message,
                entry.module,
                entry.function,
                entry.line_number,
                entry.thread_id,
                entry.process_id,
                entry.operation_id,
                entry.component,
                entry.user_id,
                entry.session_id,
                json.dumps(entry.tags),
                json.dumps(entry.metadata),
                entry.stack_trace,
                json.dumps(entry.performance_data) if entry.performance_data else None
            ))
            self.connection.commit()
    
    def add_performance_metrics(self, metrics: PerformanceMetrics):
        """Add performance metrics to the database"""
        with self.lock:
            self.connection.execute('''
                INSERT INTO performance_metrics (
                    timestamp, cpu_percent, memory_percent, memory_used_mb,
                    disk_io_read_mb, disk_io_write_mb, network_sent_mb, network_recv_mb,
                    active_threads, open_files, operation_id, component
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp.isoformat(),
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.memory_used_mb,
                metrics.disk_io_read_mb,
                metrics.disk_io_write_mb,
                metrics.network_sent_mb,
                metrics.network_recv_mb,
                metrics.active_threads,
                metrics.open_files,
                metrics.operation_id,
                metrics.component
            ))
            self.connection.commit()
    
    def search_logs(self,
                   query: Optional[str] = None,
                   levels: Optional[List[LogLevel]] = None,
                   categories: Optional[List[LogCategory]] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   operation_id: Optional[str] = None,
                   component: Optional[str] = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """Search logs with various filters"""
        with self.lock:
            sql = "SELECT * FROM log_entries WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (message LIKE ? OR logger_name LIKE ? OR component LIKE ?)"
                query_param = f"%{query}%"
                params.extend([query_param, query_param, query_param])
            
            if levels:
                level_values = [level.value for level in levels]
                placeholders = ','.join(['?' for _ in level_values])
                sql += f" AND level IN ({placeholders})"
                params.extend(level_values)
            
            if categories:
                category_values = [cat.value for cat in categories]
                placeholders = ','.join(['?' for _ in category_values])
                sql += f" AND category IN ({placeholders})"
                params.extend(category_values)
            
            if start_time:
                sql += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                sql += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            if operation_id:
                sql += " AND operation_id = ?"
                params.append(operation_id)
            
            if component:
                sql += " AND component = ?"
                params.append(component)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = self.connection.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Parse JSON fields
                if result['tags']:
                    result['tags'] = json.loads(result['tags'])
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                if result['performance_data']:
                    result['performance_data'] = json.loads(result['performance_data'])
                results.append(result)
            
            return results
    
    def get_log_statistics(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get log statistics"""
        with self.lock:
            sql = "SELECT level, category, COUNT(*) as count FROM log_entries"
            params = []
            
            if time_range:
                cutoff_time = datetime.now() - time_range
                sql += " WHERE timestamp >= ?"
                params.append(cutoff_time.isoformat())
            
            sql += " GROUP BY level, category"
            
            cursor = self.connection.execute(sql, params)
            results = cursor.fetchall()
            
            # Organize statistics
            stats = {
                'by_level': defaultdict(int),
                'by_category': defaultdict(int),
                'total': 0
            }
            
            for level, category, count in results:
                stats['by_level'][level] += count
                stats['by_category'][category] += count
                stats['total'] += count
            
            return dict(stats)
    
    def cleanup_old_logs(self, older_than: timedelta):
        """Remove logs older than specified time"""
        with self.lock:
            cutoff_time = datetime.now() - older_than
            
            # Remove old log entries
            self.connection.execute(
                "DELETE FROM log_entries WHERE timestamp < ?",
                (cutoff_time.isoformat(),)
            )
            
            # Remove old performance metrics
            self.connection.execute(
                "DELETE FROM performance_metrics WHERE timestamp < ?",
                (cutoff_time.isoformat(),)
            )
            
            self.connection.commit()
            
            # Vacuum to reclaim space
            self.connection.execute("VACUUM")
    
    def close(self):
        """Close the database connection"""
        with self.lock:
            if self.connection:
                self.connection.close()
                self.connection = None

class ReportGenerator:
    """Automatic report generation system"""
    
    def __init__(self, log_manager, output_dir: str):
        self.log_manager = log_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.report_configs = {}
        self.generation_thread = None
        self.is_generating = False
    
    def add_report_config(self, config: ReportConfig):
        """Add a report configuration"""
        self.report_configs[config.name] = config
    
    def start_auto_generation(self):
        """Start automatic report generation"""
        if not self.is_generating:
            self.is_generating = True
            self.generation_thread = threading.Thread(target=self._generation_loop, daemon=True)
            self.generation_thread.start()
    
    def stop_auto_generation(self):
        """Stop automatic report generation"""
        self.is_generating = False
        if self.generation_thread and self.generation_thread.is_alive():
            self.generation_thread.join(timeout=5.0)
    
    def _generation_loop(self):
        """Main report generation loop"""
        while self.is_generating:
            try:
                for config in self.report_configs.values():
                    if config.auto_generate:
                        self._generate_report(config)
                
                # Sleep for a reasonable interval
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Error in report generation: {e}", file=sys.stderr)
                time.sleep(3600)
    
    def generate_report(self, config_name: str) -> str:
        """Generate a specific report"""
        if config_name not in self.report_configs:
            raise ValueError(f"Report configuration '{config_name}' not found")
        
        config = self.report_configs[config_name]
        return self._generate_report(config)
    
    def _generate_report(self, config: ReportConfig) -> str:
        """Generate a report based on configuration"""
        # Collect data
        end_time = datetime.now()
        start_time = end_time - config.time_range
        
        # Get logs
        logs = self.log_manager.search_logs(
            levels=config.levels,
            categories=config.categories,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Get statistics
        statistics = self.log_manager.get_log_statistics(config.time_range)
        
        # Get performance data
        performance_summary = None
        if config.include_performance:
            performance_summary = self.log_manager.performance_monitor.get_performance_summary(config.time_range)
        
        # Generate report based on format
        if config.format == "html":
            return self._generate_html_report(config, logs, statistics, performance_summary)
        elif config.format == "json":
            return self._generate_json_report(config, logs, statistics, performance_summary)
        elif config.format == "csv":
            return self._generate_csv_report(config, logs, statistics, performance_summary)
        else:
            raise ValueError(f"Unsupported report format: {config.format}")
    
    def _generate_html_report(self, config: ReportConfig, logs: List[Dict], 
                            statistics: Dict, performance_summary: Optional[Dict]) -> str:
        """Generate HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.name}_{timestamp}.html"
        filepath = self.output_dir / filename
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{config.name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .stats-table {{ border-collapse: collapse; width: 100%; }}
        .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .stats-table th {{ background-color: #f2f2f2; }}
        .log-entry {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .log-error {{ border-left-color: #f44336; }}
        .log-warning {{ border-left-color: #ff9800; }}
        .log-success {{ border-left-color: #4caf50; }}
        .log-info {{ border-left-color: #2196f3; }}
        .performance-chart {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{config.name}</h1>
        <p><strong>Description:</strong> {config.description}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Time Range:</strong> {config.time_range}</p>
    </div>
    
    <div class="section">
        <h2>Summary Statistics</h2>
        <table class="stats-table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Log Entries</td><td>{statistics.get('total', 0)}</td></tr>
        """
        
        # Add level statistics
        for level, count in statistics.get('by_level', {}).items():
            html_content += f"<tr><td>Level {level}</td><td>{count}</td></tr>"
        
        # Add category statistics
        for category, count in statistics.get('by_category', {}).items():
            html_content += f"<tr><td>Category {category}</td><td>{count}</td></tr>"
        
        html_content += "</table></div>"
        
        # Add performance summary if available
        if performance_summary:
            html_content += f"""
    <div class="section">
        <h2>Performance Summary</h2>
        <table class="stats-table">
            <tr><th>Metric</th><th>Average</th><th>Min</th><th>Max</th><th>Current</th></tr>
            <tr>
                <td>CPU Usage (%)</td>
                <td>{performance_summary['cpu']['avg']:.2f}</td>
                <td>{performance_summary['cpu']['min']:.2f}</td>
                <td>{performance_summary['cpu']['max']:.2f}</td>
                <td>{performance_summary['cpu']['current']:.2f}</td>
            </tr>
            <tr>
                <td>Memory Usage (%)</td>
                <td>{performance_summary['memory']['avg_percent']:.2f}</td>
                <td>{performance_summary['memory']['min_percent']:.2f}</td>
                <td>{performance_summary['memory']['max_percent']:.2f}</td>
                <td>{performance_summary['memory']['current_percent']:.2f}</td>
            </tr>
            <tr>
                <td>Memory Usage (MB)</td>
                <td>{performance_summary['memory']['avg_mb']:.2f}</td>
                <td>{performance_summary['memory']['min_mb']:.2f}</td>
                <td>{performance_summary['memory']['max_mb']:.2f}</td>
                <td>{performance_summary['memory']['current_mb']:.2f}</td>
            </tr>
        </table>
    </div>
            """
        
        # Add recent log entries
        html_content += """
    <div class="section">
        <h2>Recent Log Entries</h2>
        """
        
        for log in logs[:50]:  # Show last 50 entries
            level_class = f"log-{log.get('level', '').lower()}"
            html_content += f"""
        <div class="log-entry {level_class}">
            <strong>{log.get('timestamp', '')}</strong> 
            [{log.get('level', '')}] 
            [{log.get('category', '')}] 
            {log.get('component', '') + ' - ' if log.get('component') else ''}
            {log.get('message', '')}
        </div>
            """
        
        html_content += """
    </div>
</body>
</html>
        """
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _generate_json_report(self, config: ReportConfig, logs: List[Dict], 
                            statistics: Dict, performance_summary: Optional[Dict]) -> str:
        """Generate JSON report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.name}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        report_data = {
            'report_info': {
                'name': config.name,
                'description': config.description,
                'generated_at': datetime.now().isoformat(),
                'time_range': str(config.time_range),
                'categories': [cat.value for cat in config.categories],
                'levels': [level.value for level in config.levels]
            },
            'statistics': statistics,
            'performance_summary': performance_summary,
            'logs': logs[:1000]  # Limit to 1000 entries for JSON
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def _generate_csv_report(self, config: ReportConfig, logs: List[Dict], 
                           statistics: Dict, performance_summary: Optional[Dict]) -> str:
        """Generate CSV report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.name}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if logs:
                writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
        
        return str(filepath)

class AdvancedLogManager:
    """Main advanced logging manager"""
    
    def __init__(self, 
                 log_dir: str,
                 db_path: Optional[str] = None,
                 enable_performance_monitoring: bool = True,
                 enable_auto_reports: bool = True,
                 max_log_age: timedelta = timedelta(days=30)):
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize database
        if db_path is None:
            db_path = str(self.log_dir / "logs.db")
        self.database = LogDatabase(db_path)
        
        # Initialize performance monitoring
        self.performance_monitor = None
        if enable_performance_monitoring:
            self.performance_monitor = PerformanceMonitor(self)
            self.performance_monitor.start_monitoring()
        
        # Initialize report generator
        self.report_generator = None
        if enable_auto_reports:
            reports_dir = self.log_dir / "reports"
            self.report_generator = ReportGenerator(self, str(reports_dir))
            self._setup_default_reports()
            self.report_generator.start_auto_generation()
        
        # Configuration
        self.max_log_age = max_log_age
        
        # Setup advanced log handler
        self.log_handler = AdvancedLogHandler(self)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Integration with notification manager
        self.notification_manager = get_notification_manager()
        
        print(f"AdvancedLogManager initialized with database at {db_path}")
    
    def _setup_default_reports(self):
        """Setup default report configurations"""
        # Daily summary report
        daily_report = ReportConfig(
            name="daily_summary",
            description="Daily system activity summary",
            categories=[LogCategory.SYSTEM, LogCategory.APPLICATION, LogCategory.ERROR],
            levels=[LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL],
            time_range=timedelta(days=1),
            include_performance=True,
            include_statistics=True,
            format="html",
            auto_generate=True,
            generation_interval=timedelta(hours=24)
        )
        
        # Error report
        error_report = ReportConfig(
            name="error_report",
            description="Error and warning analysis",
            categories=[LogCategory.ERROR, LogCategory.SYSTEM, LogCategory.APPLICATION],
            levels=[LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL],
            time_range=timedelta(hours=6),
            include_performance=True,
            include_statistics=True,
            format="html",
            auto_generate=True,
            generation_interval=timedelta(hours=6)
        )
        
        # Performance report
        performance_report = ReportConfig(
            name="performance_report",
            description="System performance analysis",
            categories=[LogCategory.PERFORMANCE, LogCategory.SYSTEM],
            levels=[LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR],
            time_range=timedelta(hours=12),
            include_performance=True,
            include_statistics=True,
            format="json",
            auto_generate=True,
            generation_interval=timedelta(hours=12)
        )
        
        if self.report_generator:
            self.report_generator.add_report_config(daily_report)
            self.report_generator.add_report_config(error_report)
            self.report_generator.add_report_config(performance_report)
    
    def add_log_entry(self, entry: LogEntry):
        """Add a log entry"""
        self.database.add_log_entry(entry)
        
        # Send notification for critical errors
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] and self.notification_manager:
            self.notification_manager.notify(
                NotificationSeverity.ERROR if entry.level == LogLevel.ERROR else NotificationSeverity.CRITICAL,
                OperationCategory.SYSTEM,
                f"Log {entry.level.name}",
                entry.message,
                component=entry.component,
                operation_id=entry.operation_id,
                details={
                    'logger': entry.logger_name,
                    'module': entry.module,
                    'function': entry.function,
                    'line': entry.line_number
                }
            )
    
    def add_performance_metrics(self, metrics: PerformanceMetrics):
        """Add performance metrics"""
        self.database.add_performance_metrics(metrics)
    
    def search_logs(self, **kwargs) -> List[Dict[str, Any]]:
        """Search logs with filters"""
        return self.database.search_logs(**kwargs)
    
    def get_log_statistics(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get log statistics"""
        return self.database.get_log_statistics(time_range)
    
    def generate_report(self, config_name: str) -> str:
        """Generate a specific report"""
        if self.report_generator:
            return self.report_generator.generate_report(config_name)
        else:
            raise RuntimeError("Report generator not initialized")
    
    def export_logs(self, 
                   filepath: str,
                   format: str = "json",
                   **search_kwargs) -> str:
        """Export logs to file"""
        logs = self.search_logs(**search_kwargs)
        
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            if logs:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return filepath
    
    def _cleanup_loop(self):
        """Periodic cleanup of old logs"""
        while True:
            try:
                time.sleep(3600 * 24)  # Run daily
                self.database.cleanup_old_logs(self.max_log_age)
                print(f"Cleaned up logs older than {self.max_log_age}")
            except Exception as e:
                print(f"Error in log cleanup: {e}", file=sys.stderr)
    
    def shutdown(self):
        """Shutdown the log manager"""
        if self.performance_monitor:
            self.performance_monitor.stop_monitoring()
        
        if self.report_generator:
            self.report_generator.stop_auto_generation()
        
        self.database.close()
        
        # Remove handler from root logger
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)

# Global advanced log manager instance
_advanced_log_manager: Optional[AdvancedLogManager] = None

def get_advanced_log_manager() -> Optional[AdvancedLogManager]:
    """Get the global advanced log manager instance"""
    return _advanced_log_manager

def initialize_advanced_logging(log_dir: str, **kwargs) -> AdvancedLogManager:
    """Initialize the global advanced log manager"""
    global _advanced_log_manager
    if _advanced_log_manager is None:
        _advanced_log_manager = AdvancedLogManager(log_dir=log_dir, **kwargs)
    return _advanced_log_manager

def shutdown_advanced_logging():
    """Shutdown the global advanced log manager"""
    global _advanced_log_manager
    if _advanced_log_manager:
        _advanced_log_manager.shutdown()
        _advanced_log_manager = None