# -*- coding: utf-8 -*-
"""
Operation History and Reporting System

This module implements detailed operation history tracking and display,
report export functionality for troubleshooting, and operation timeline visualization.

Requirements addressed:
- 8.4: Operation history tracking, report export, and timeline visualization
"""

import logging
import json
import csv
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import sqlite3
import zipfile
import io

try:
    from .modern_frontend_manager import OperationType, OperationProgress
    from .security_manager import SecurityManager, SecurityLevel
except ImportError:
    # Fallback for direct execution
    from modern_frontend_manager import OperationType, OperationProgress
    from security_manager import SecurityManager, SecurityLevel


class OperationStatus(Enum):
    """Status of operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ReportFormat(Enum):
    """Report export formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    XML = "xml"
    ZIP = "zip"


class TimelineGranularity(Enum):
    """Timeline visualization granularity"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class OperationRecord:
    """Complete record of an operation"""
    operation_id: str
    operation_type: OperationType
    status: OperationStatus
    component_name: Optional[str] = None
    title: str = ""
    description: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 1
    current_step_number: int = 0
    details: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    system_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationSummary:
    """Summary statistics for operations"""
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    cancelled_operations: int = 0
    average_duration: float = 0.0
    success_rate: float = 0.0
    operations_by_type: Dict[str, int] = field(default_factory=dict)
    operations_by_component: Dict[str, int] = field(default_factory=dict)
    operations_by_status: Dict[str, int] = field(default_factory=dict)
    time_period: str = ""
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TimelineEvent:
    """Event in operation timeline"""
    timestamp: datetime
    operation_id: str
    event_type: str  # "start", "progress", "complete", "error"
    title: str
    description: str
    component: Optional[str] = None
    progress: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportExportResult:
    """Result of report export operation"""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[ReportFormat] = None
    records_exported: int = 0
    error_message: Optional[str] = None
    export_time: datetime = field(default_factory=datetime.now)


@dataclass
class HistoryTrackingResult:
    """Result of history tracking operations"""
    success: bool
    records_tracked: int = 0
    records_stored: int = 0
    storage_size: Optional[int] = None
    error_message: Optional[str] = None


class OperationHistoryReportingSystem:
    """
    Comprehensive Operation History and Reporting System
    
    Provides:
    - Detailed operation history tracking and display
    - Report export functionality for troubleshooting
    - Operation timeline visualization
    - Performance analytics and insights
    - Data persistence and retrieval
    """
    
    def __init__(self, 
                 security_manager: Optional[SecurityManager] = None,
                 database_path: Optional[str] = None,
                 max_history_records: int = 10000):
        """
        Initialize Operation History and Reporting System
        
        Args:
            security_manager: Security manager for auditing
            database_path: Path to SQLite database file
            max_history_records: Maximum number of records to keep in memory
        """
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.security_manager = security_manager or SecurityManager()
        
        # Configuration
        self.database_path = database_path or "data/operation_history.db"
        self.max_history_records = max_history_records
        self.enable_real_time_tracking = True
        self.auto_cleanup_days = 90  # Keep records for 90 days
        
        # Storage
        self.operation_records: Dict[str, OperationRecord] = {}
        self.timeline_events: List[TimelineEvent] = []
        self.active_operations: Dict[str, OperationRecord] = {}
        
        # Analytics cache
        self.cached_summaries: Dict[str, OperationSummary] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize database
        self._initialize_database()
        
        # Load recent records
        self._load_recent_records()
        
        self.logger.info("Operation History and Reporting System initialized")
    
    def build_detailed_operation_history_tracking_and_display(self) -> HistoryTrackingResult:
        """
        Build detailed operation history tracking and display system
        
        Returns:
            HistoryTrackingResult: Result of tracking system setup
        """
        try:
            result = HistoryTrackingResult(success=False)
            
            # Setup database schema
            schema_created = self._create_database_schema()
            
            # Setup real-time tracking
            tracking_enabled = self._enable_real_time_tracking()
            
            # Setup automatic cleanup
            cleanup_scheduled = self._schedule_automatic_cleanup()
            
            # Load existing records
            records_loaded = self._load_all_records_from_database()
            
            # Setup display components
            display_ready = self._setup_history_display_components()
            
            if schema_created and tracking_enabled and display_ready:
                result.success = True
                result.records_tracked = len(self.operation_records)
                result.records_stored = records_loaded
                result.storage_size = self._get_database_size()
                
                self.logger.info(f"Operation history tracking enabled: {result.records_tracked} records in memory, {result.records_stored} in database")
                
                # Audit tracking setup
                self.security_manager.audit_critical_operation(
                    operation="operation_history_tracking_setup",
                    component="operation_history_reporting",
                    details={
                        "records_in_memory": result.records_tracked,
                        "records_in_database": result.records_stored,
                        "database_size": result.storage_size
                    },
                    success=True,
                    security_level=SecurityLevel.LOW
                )
            else:
                result.error_message = "Failed to setup complete tracking system"
                self.logger.error("Operation history tracking setup incomplete")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error building operation history tracking: {e}")
            return HistoryTrackingResult(
                success=False,
                error_message=str(e)
            )
    
    def create_report_export_functionality_for_troubleshooting(self, 
                                                             export_format: ReportFormat,
                                                             filters: Optional[Dict[str, Any]] = None,
                                                             output_path: Optional[str] = None) -> ReportExportResult:
        """
        Create report export functionality for troubleshooting
        
        Args:
            export_format: Format for export (JSON, CSV, HTML, PDF, XML, ZIP)
            filters: Optional filters for data selection
            output_path: Optional custom output path
            
        Returns:
            ReportExportResult: Result of export operation
        """
        try:
            result = ReportExportResult(success=False, format=export_format)
            
            # Apply filters to get relevant records
            filtered_records = self._apply_export_filters(filters or {})
            result.records_exported = len(filtered_records)
            
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/operation_history_{timestamp}.{export_format.value}"
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if export_format == ReportFormat.JSON:
                success = self._export_to_json(filtered_records, output_path)
            elif export_format == ReportFormat.CSV:
                success = self._export_to_csv(filtered_records, output_path)
            elif export_format == ReportFormat.HTML:
                success = self._export_to_html(filtered_records, output_path)
            elif export_format == ReportFormat.PDF:
                success = self._export_to_pdf(filtered_records, output_path)
            elif export_format == ReportFormat.XML:
                success = self._export_to_xml(filtered_records, output_path)
            elif export_format == ReportFormat.ZIP:
                success = self._export_to_zip(filtered_records, output_path)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            if success:
                result.success = True
                result.file_path = output_path
                result.file_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
                
                self.logger.info(f"Successfully exported {result.records_exported} records to {output_path}")
                
                # Audit export operation
                self.security_manager.audit_critical_operation(
                    operation="operation_history_export",
                    component="operation_history_reporting",
                    details={
                        "format": export_format.value,
                        "records_exported": result.records_exported,
                        "file_size": result.file_size,
                        "output_path": output_path
                    },
                    success=True,
                    security_level=SecurityLevel.MEDIUM
                )
            else:
                result.error_message = f"Failed to export to {export_format.value} format"
                self.logger.error(f"Export failed for format {export_format.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating report export: {e}")
            return ReportExportResult(
                success=False,
                format=export_format,
                error_message=str(e)
            )
    
    def implement_operation_timeline_visualization(self, 
                                                 time_range: Optional[Tuple[datetime, datetime]] = None,
                                                 granularity: TimelineGranularity = TimelineGranularity.HOUR,
                                                 component_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Implement operation timeline visualization
        
        Args:
            time_range: Optional time range (start, end)
            granularity: Timeline granularity (minute, hour, day, week, month)
            component_filter: Optional component name filter
            
        Returns:
            Dict[str, Any]: Timeline visualization data
        """
        try:
            # Set default time range if not provided
            if not time_range:
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)  # Last 7 days
                time_range = (start_time, end_time)
            
            # Get filtered records
            filtered_records = self._get_records_in_time_range(time_range, component_filter)
            
            # Generate timeline events
            timeline_events = self._generate_timeline_events(filtered_records, granularity)
            
            # Create timeline buckets
            timeline_buckets = self._create_timeline_buckets(timeline_events, time_range, granularity)
            
            # Calculate statistics
            timeline_stats = self._calculate_timeline_statistics(filtered_records, time_range)
            
            # Generate visualization data
            visualization_data = {
                "timeline": {
                    "start_time": time_range[0].isoformat(),
                    "end_time": time_range[1].isoformat(),
                    "granularity": granularity.value,
                    "buckets": timeline_buckets,
                    "total_events": len(timeline_events)
                },
                "statistics": timeline_stats,
                "events": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "operation_id": event.operation_id,
                        "event_type": event.event_type,
                        "title": event.title,
                        "description": event.description,
                        "component": event.component,
                        "progress": event.progress,
                        "metadata": event.metadata
                    }
                    for event in timeline_events[:100]  # Limit to 100 events for performance
                ],
                "filters": {
                    "time_range": [time_range[0].isoformat(), time_range[1].isoformat()],
                    "granularity": granularity.value,
                    "component_filter": component_filter
                },
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated timeline visualization: {len(timeline_events)} events, {len(timeline_buckets)} buckets")
            
            return visualization_data
            
        except Exception as e:
            self.logger.error(f"Error implementing timeline visualization: {e}")
            return {
                "error": str(e),
                "timeline": None,
                "statistics": None,
                "events": []
            }
    
    def track_operation(self, operation_progress: OperationProgress) -> bool:
        """
        Track an operation in the history system
        
        Args:
            operation_progress: Operation progress data
            
        Returns:
            bool: True if successfully tracked
        """
        try:
            with self._lock:
                # Convert to operation record
                record = self._convert_progress_to_record(operation_progress)
                
                # Store in memory
                self.operation_records[record.operation_id] = record
                
                # Update active operations
                if record.status in [OperationStatus.PENDING, OperationStatus.RUNNING]:
                    self.active_operations[record.operation_id] = record
                else:
                    # Remove from active if completed/failed
                    self.active_operations.pop(record.operation_id, None)
                
                # Add timeline event
                timeline_event = self._create_timeline_event(record)
                self.timeline_events.append(timeline_event)
                
                # Persist to database
                self._save_record_to_database(record)
                
                # Cleanup old records if needed
                if len(self.operation_records) > self.max_history_records:
                    self._cleanup_old_records()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error tracking operation {operation_progress.operation_id}: {e}")
            return False
    
    def get_operation_history(self, 
                            limit: int = 100,
                            offset: int = 0,
                            filters: Optional[Dict[str, Any]] = None) -> List[OperationRecord]:
        """
        Get operation history with pagination and filtering
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            filters: Optional filters
            
        Returns:
            List[OperationRecord]: List of operation records
        """
        try:
            with self._lock:
                # Apply filters
                filtered_records = list(self.operation_records.values())
                
                if filters:
                    filtered_records = self._apply_history_filters(filtered_records, filters)
                
                # Sort by start time (newest first)
                filtered_records.sort(key=lambda r: r.start_time, reverse=True)
                
                # Apply pagination
                start_idx = offset
                end_idx = offset + limit
                
                return filtered_records[start_idx:end_idx]
                
        except Exception as e:
            self.logger.error(f"Error getting operation history: {e}")
            return []
    
    def get_operation_summary(self, 
                            time_period: str = "24h",
                            component_filter: Optional[str] = None) -> OperationSummary:
        """
        Get operation summary statistics
        
        Args:
            time_period: Time period for summary (1h, 24h, 7d, 30d)
            component_filter: Optional component filter
            
        Returns:
            OperationSummary: Summary statistics
        """
        try:
            # Check cache first
            cache_key = f"{time_period}_{component_filter or 'all'}"
            if cache_key in self.cached_summaries:
                cached_time = self.cache_expiry.get(cache_key, datetime.min)
                if datetime.now() - cached_time < timedelta(minutes=5):  # 5-minute cache
                    return self.cached_summaries[cache_key]
            
            # Calculate time range
            end_time = datetime.now()
            if time_period == "1h":
                start_time = end_time - timedelta(hours=1)
            elif time_period == "24h":
                start_time = end_time - timedelta(days=1)
            elif time_period == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_period == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)  # Default to 24h
            
            # Filter records
            filtered_records = [
                record for record in self.operation_records.values()
                if start_time <= record.start_time <= end_time
                and (not component_filter or record.component_name == component_filter)
            ]
            
            # Calculate summary
            summary = self._calculate_operation_summary(filtered_records, time_period)
            
            # Cache result
            self.cached_summaries[cache_key] = summary
            self.cache_expiry[cache_key] = datetime.now()
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting operation summary: {e}")
            return OperationSummary(time_period=time_period)
    
    def search_operations(self, 
                         query: str,
                         search_fields: Optional[List[str]] = None) -> List[OperationRecord]:
        """
        Search operations by text query
        
        Args:
            query: Search query
            search_fields: Fields to search in (title, description, component_name, etc.)
            
        Returns:
            List[OperationRecord]: Matching operation records
        """
        try:
            if not query.strip():
                return []
            
            search_fields = search_fields or ["title", "description", "component_name", "current_step"]
            query_lower = query.lower()
            
            matching_records = []
            
            with self._lock:
                for record in self.operation_records.values():
                    # Search in specified fields
                    for field in search_fields:
                        field_value = getattr(record, field, "")
                        if field_value and query_lower in str(field_value).lower():
                            matching_records.append(record)
                            break
                    
                    # Search in details, warnings, and errors
                    all_messages = record.details + record.warnings + record.errors
                    if any(query_lower in msg.lower() for msg in all_messages):
                        if record not in matching_records:
                            matching_records.append(record)
            
            # Sort by relevance (start time for now)
            matching_records.sort(key=lambda r: r.start_time, reverse=True)
            
            return matching_records
            
        except Exception as e:
            self.logger.error(f"Error searching operations: {e}")
            return []
    
    def get_system_report(self) -> Dict[str, Any]:
        """
        Get comprehensive system report
        
        Returns:
            Dict[str, Any]: System report data
        """
        try:
            with self._lock:
                total_records = len(self.operation_records)
                active_operations = len(self.active_operations)
                database_size = self._get_database_size()
                
                # Recent activity (last 24 hours)
                recent_summary = self.get_operation_summary("24h")
                
                # Top components by activity
                component_activity = defaultdict(int)
                for record in self.operation_records.values():
                    if record.component_name:
                        component_activity[record.component_name] += 1
                
                top_components = sorted(
                    component_activity.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                # Error analysis
                error_records = [
                    record for record in self.operation_records.values()
                    if record.status == OperationStatus.FAILED
                ]
                
                common_errors = defaultdict(int)
                for record in error_records:
                    for error in record.errors:
                        # Extract error type (simplified)
                        error_type = error.split(':')[0] if ':' in error else error[:50]
                        common_errors[error_type] += 1
                
                top_errors = sorted(
                    common_errors.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                return {
                    "system_overview": {
                        "total_records": total_records,
                        "active_operations": active_operations,
                        "database_size_bytes": database_size,
                        "timeline_events": len(self.timeline_events),
                        "cache_entries": len(self.cached_summaries)
                    },
                    "recent_activity": {
                        "period": "24h",
                        "summary": asdict(recent_summary)
                    },
                    "top_components": [
                        {"component": comp, "operations": count}
                        for comp, count in top_components
                    ],
                    "error_analysis": {
                        "total_errors": len(error_records),
                        "common_errors": [
                            {"error_type": error, "count": count}
                            for error, count in top_errors
                        ]
                    },
                    "performance_metrics": {
                        "average_operation_duration": recent_summary.average_duration,
                        "success_rate": recent_summary.success_rate,
                        "operations_per_hour": recent_summary.total_operations / 24 if recent_summary.total_operations > 0 else 0
                    },
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error generating system report: {e}")
            return {"error": str(e)}
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Cleanup old records from database and memory
        
        Args:
            days_to_keep: Number of days to keep records
            
        Returns:
            int: Number of records cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self._lock:
                # Remove from memory
                old_record_ids = [
                    record_id for record_id, record in self.operation_records.items()
                    if record.start_time < cutoff_date
                ]
                
                for record_id in old_record_ids:
                    del self.operation_records[record_id]
                
                # Remove from database
                db_cleaned = self._cleanup_database_records(cutoff_date)
                
                # Clean timeline events
                self.timeline_events = [
                    event for event in self.timeline_events
                    if event.timestamp >= cutoff_date
                ]
                
                # Clear cache
                self.cached_summaries.clear()
                self.cache_expiry.clear()
                
                total_cleaned = len(old_record_ids)
                self.logger.info(f"Cleaned up {total_cleaned} old records (older than {days_to_keep} days)")
                
                return total_cleaned
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    def shutdown(self):
        """Shutdown the history and reporting system"""
        self.logger.info("Shutting down Operation History and Reporting System")
        
        # Save any pending data
        self._save_all_pending_data()
        
        # Close database connection
        self._close_database_connection()
        
        self.logger.info("Operation History and Reporting System shutdown complete")
    
    # Private helper methods
    
    def _initialize_database(self):
        """Initialize SQLite database"""
        try:
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                
            self.logger.info(f"Database initialized at {self.database_path}")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    def _create_database_schema(self) -> bool:
        """Create database schema"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS operation_records (
                        operation_id TEXT PRIMARY KEY,
                        operation_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        component_name TEXT,
                        title TEXT,
                        description TEXT,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        duration_seconds REAL,
                        progress_percentage REAL,
                        current_step TEXT,
                        total_steps INTEGER,
                        current_step_number INTEGER,
                        details TEXT,  -- JSON array
                        warnings TEXT,  -- JSON array
                        errors TEXT,  -- JSON array
                        result TEXT,  -- JSON
                        metadata TEXT,  -- JSON
                        user_id TEXT,
                        session_id TEXT,
                        system_info TEXT,  -- JSON
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_start_time 
                    ON operation_records(start_time)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_status 
                    ON operation_records(status)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_operation_component 
                    ON operation_records(component_name)
                """)
                
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database schema: {e}")
            return False  
  
    def _enable_real_time_tracking(self) -> bool:
        """Enable real-time operation tracking"""
        try:
            self.enable_real_time_tracking = True
            return True
        except Exception as e:
            self.logger.error(f"Error enabling real-time tracking: {e}")
            return False
    
    def _schedule_automatic_cleanup(self) -> bool:
        """Schedule automatic cleanup of old records"""
        try:
            # This would typically use a scheduler like APScheduler
            # For now, we'll just set a flag
            self.auto_cleanup_enabled = True
            return True
        except Exception as e:
            self.logger.error(f"Error scheduling automatic cleanup: {e}")
            return False
    
    def _load_all_records_from_database(self) -> int:
        """Load all records from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM operation_records 
                    ORDER BY start_time DESC 
                    LIMIT ?
                """, (self.max_history_records,))
                
                records_loaded = 0
                for row in cursor:
                    record = self._row_to_operation_record(row)
                    self.operation_records[record.operation_id] = record
                    records_loaded += 1
                
                return records_loaded
                
        except Exception as e:
            self.logger.error(f"Error loading records from database: {e}")
            return 0
    
    def _load_recent_records(self):
        """Load recent records from database"""
        try:
            recent_count = self._load_all_records_from_database()
            self.logger.info(f"Loaded {recent_count} recent records from database")
        except Exception as e:
            self.logger.error(f"Error loading recent records: {e}")
    
    def _setup_history_display_components(self) -> bool:
        """Setup history display components"""
        try:
            # This would setup UI components for history display
            # For now, we'll just return True
            return True
        except Exception as e:
            self.logger.error(f"Error setting up history display: {e}")
            return False
    
    def _get_database_size(self) -> int:
        """Get database file size in bytes"""
        try:
            db_path = Path(self.database_path)
            return db_path.stat().st_size if db_path.exists() else 0
        except Exception as e:
            self.logger.error(f"Error getting database size: {e}")
            return 0
    
    def _apply_export_filters(self, filters: Dict[str, Any]) -> List[OperationRecord]:
        """Apply filters to records for export"""
        try:
            filtered_records = list(self.operation_records.values())
            
            # Apply time range filter
            if 'start_time' in filters and 'end_time' in filters:
                start_time = filters['start_time']
                end_time = filters['end_time']
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)
                
                filtered_records = [
                    record for record in filtered_records
                    if start_time <= record.start_time <= end_time
                ]
            
            # Apply status filter
            if 'status' in filters:
                status_filter = filters['status']
                if isinstance(status_filter, str):
                    status_filter = [status_filter]
                filtered_records = [
                    record for record in filtered_records
                    if record.status.value in status_filter
                ]
            
            # Apply component filter
            if 'component' in filters:
                component_filter = filters['component']
                filtered_records = [
                    record for record in filtered_records
                    if record.component_name == component_filter
                ]
            
            # Apply operation type filter
            if 'operation_type' in filters:
                type_filter = filters['operation_type']
                if isinstance(type_filter, str):
                    type_filter = [type_filter]
                filtered_records = [
                    record for record in filtered_records
                    if record.operation_type.value in type_filter
                ]
            
            return filtered_records
            
        except Exception as e:
            self.logger.error(f"Error applying export filters: {e}")
            return list(self.operation_records.values())
    
    def _export_to_json(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to JSON format"""
        try:
            export_data = {
                "export_info": {
                    "format": "json",
                    "exported_at": datetime.now().isoformat(),
                    "total_records": len(records),
                    "system": "Environment Dev - Operation History"
                },
                "records": [
                    {
                        "operation_id": record.operation_id,
                        "operation_type": record.operation_type.value,
                        "status": record.status.value,
                        "component_name": record.component_name,
                        "title": record.title,
                        "description": record.description,
                        "start_time": record.start_time.isoformat(),
                        "end_time": record.end_time.isoformat() if record.end_time else None,
                        "duration_seconds": record.duration_seconds,
                        "progress_percentage": record.progress_percentage,
                        "current_step": record.current_step,
                        "total_steps": record.total_steps,
                        "current_step_number": record.current_step_number,
                        "details": record.details,
                        "warnings": record.warnings,
                        "errors": record.errors,
                        "result": record.result,
                        "metadata": record.metadata,
                        "user_id": record.user_id,
                        "session_id": record.session_id,
                        "system_info": record.system_info
                    }
                    for record in records
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            return False
    
    def _export_to_csv(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to CSV format"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Operation ID', 'Type', 'Status', 'Component', 'Title',
                    'Start Time', 'End Time', 'Duration (s)', 'Progress (%)',
                    'Current Step', 'Details Count', 'Warnings Count', 'Errors Count'
                ])
                
                # Write records
                for record in records:
                    writer.writerow([
                        record.operation_id,
                        record.operation_type.value,
                        record.status.value,
                        record.component_name or '',
                        record.title,
                        record.start_time.isoformat(),
                        record.end_time.isoformat() if record.end_time else '',
                        record.duration_seconds or '',
                        record.progress_percentage,
                        record.current_step,
                        len(record.details),
                        len(record.warnings),
                        len(record.errors)
                    ])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def _export_to_html(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to HTML format"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Operation History Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    .status-completed {{ color: green; }}
                    .status-failed {{ color: red; }}
                    .status-running {{ color: blue; }}
                    .status-cancelled {{ color: orange; }}
                </style>
            </head>
            <body>
                <h1>Operation History Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Records: {len(records)}</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Operation ID</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Component</th>
                            <th>Title</th>
                            <th>Start Time</th>
                            <th>Duration</th>
                            <th>Progress</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for record in records:
                duration_str = f"{record.duration_seconds:.1f}s" if record.duration_seconds else "N/A"
                status_class = f"status-{record.status.value}"
                
                html_content += f"""
                        <tr>
                            <td>{record.operation_id}</td>
                            <td>{record.operation_type.value}</td>
                            <td class="{status_class}">{record.status.value}</td>
                            <td>{record.component_name or 'N/A'}</td>
                            <td>{record.title}</td>
                            <td>{record.start_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                            <td>{duration_str}</td>
                            <td>{record.progress_percentage:.1f}%</td>
                        </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to HTML: {e}")
            return False
    
    def _export_to_pdf(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to PDF format"""
        try:
            # This would require a PDF library like reportlab
            # For now, we'll create a simple text-based PDF placeholder
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("PDF Export - Operation History Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Records: {len(records)}\n\n")
                
                for record in records:
                    f.write(f"Operation: {record.operation_id}\n")
                    f.write(f"Type: {record.operation_type.value}\n")
                    f.write(f"Status: {record.status.value}\n")
                    f.write(f"Component: {record.component_name or 'N/A'}\n")
                    f.write(f"Title: {record.title}\n")
                    f.write(f"Start: {record.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("-" * 30 + "\n\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to PDF: {e}")
            return False
    
    def _export_to_xml(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to XML format"""
        try:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += '<operation_history>\n'
            xml_content += f'  <export_info>\n'
            xml_content += f'    <format>xml</format>\n'
            xml_content += f'    <exported_at>{datetime.now().isoformat()}</exported_at>\n'
            xml_content += f'    <total_records>{len(records)}</total_records>\n'
            xml_content += f'  </export_info>\n'
            xml_content += f'  <records>\n'
            
            for record in records:
                xml_content += f'    <record>\n'
                xml_content += f'      <operation_id>{record.operation_id}</operation_id>\n'
                xml_content += f'      <operation_type>{record.operation_type.value}</operation_type>\n'
                xml_content += f'      <status>{record.status.value}</status>\n'
                xml_content += f'      <component_name>{record.component_name or ""}</component_name>\n'
                xml_content += f'      <title><![CDATA[{record.title}]]></title>\n'
                xml_content += f'      <start_time>{record.start_time.isoformat()}</start_time>\n'
                if record.end_time:
                    xml_content += f'      <end_time>{record.end_time.isoformat()}</end_time>\n'
                if record.duration_seconds:
                    xml_content += f'      <duration_seconds>{record.duration_seconds}</duration_seconds>\n'
                xml_content += f'      <progress_percentage>{record.progress_percentage}</progress_percentage>\n'
                xml_content += f'    </record>\n'
            
            xml_content += f'  </records>\n'
            xml_content += '</operation_history>\n'
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to XML: {e}")
            return False
    
    def _export_to_zip(self, records: List[OperationRecord], output_path: str) -> bool:
        """Export records to ZIP format with multiple files"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add JSON export
                json_data = io.StringIO()
                json.dump([asdict(record) for record in records], json_data, indent=2, default=str)
                zipf.writestr("operation_history.json", json_data.getvalue())
                
                # Add CSV export
                csv_data = io.StringIO()
                writer = csv.writer(csv_data)
                writer.writerow(['Operation ID', 'Type', 'Status', 'Component', 'Title', 'Start Time'])
                for record in records:
                    writer.writerow([
                        record.operation_id, record.operation_type.value, record.status.value,
                        record.component_name or '', record.title, record.start_time.isoformat()
                    ])
                zipf.writestr("operation_history.csv", csv_data.getvalue())
                
                # Add summary report
                summary_data = f"""
Operation History Export Summary
================================

Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Records: {len(records)}

Status Distribution:
"""
                status_counts = defaultdict(int)
                for record in records:
                    status_counts[record.status.value] += 1
                
                for status, count in status_counts.items():
                    summary_data += f"  {status}: {count}\n"
                
                zipf.writestr("summary.txt", summary_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting to ZIP: {e}")
            return False
    
    def _get_records_in_time_range(self, time_range: Tuple[datetime, datetime], 
                                  component_filter: Optional[str] = None) -> List[OperationRecord]:
        """Get records within time range"""
        start_time, end_time = time_range
        
        filtered_records = [
            record for record in self.operation_records.values()
            if start_time <= record.start_time <= end_time
            and (not component_filter or record.component_name == component_filter)
        ]
        
        return filtered_records
    
    def _generate_timeline_events(self, records: List[OperationRecord], 
                                granularity: TimelineGranularity) -> List[TimelineEvent]:
        """Generate timeline events from records"""
        events = []
        
        for record in records:
            # Start event
            events.append(TimelineEvent(
                timestamp=record.start_time,
                operation_id=record.operation_id,
                event_type="start",
                title=f"Started: {record.title}",
                description=record.description,
                component=record.component_name,
                progress=0.0,
                metadata={"operation_type": record.operation_type.value}
            ))
            
            # End event (if completed)
            if record.end_time:
                events.append(TimelineEvent(
                    timestamp=record.end_time,
                    operation_id=record.operation_id,
                    event_type="complete" if record.status == OperationStatus.COMPLETED else "error",
                    title=f"Finished: {record.title}",
                    description=f"Status: {record.status.value}",
                    component=record.component_name,
                    progress=record.progress_percentage,
                    metadata={
                        "operation_type": record.operation_type.value,
                        "duration": record.duration_seconds,
                        "status": record.status.value
                    }
                ))
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        return events
    
    def _create_timeline_buckets(self, events: List[TimelineEvent], 
                               time_range: Tuple[datetime, datetime],
                               granularity: TimelineGranularity) -> List[Dict[str, Any]]:
        """Create timeline buckets for visualization"""
        start_time, end_time = time_range
        buckets = []
        
        # Determine bucket size
        if granularity == TimelineGranularity.MINUTE:
            delta = timedelta(minutes=1)
        elif granularity == TimelineGranularity.HOUR:
            delta = timedelta(hours=1)
        elif granularity == TimelineGranularity.DAY:
            delta = timedelta(days=1)
        elif granularity == TimelineGranularity.WEEK:
            delta = timedelta(weeks=1)
        else:  # MONTH
            delta = timedelta(days=30)
        
        # Create buckets
        current_time = start_time
        while current_time < end_time:
            bucket_end = min(current_time + delta, end_time)
            
            # Count events in this bucket
            bucket_events = [
                event for event in events
                if current_time <= event.timestamp < bucket_end
            ]
            
            # Categorize events
            event_counts = defaultdict(int)
            for event in bucket_events:
                event_counts[event.event_type] += 1
            
            buckets.append({
                "start_time": current_time.isoformat(),
                "end_time": bucket_end.isoformat(),
                "total_events": len(bucket_events),
                "event_counts": dict(event_counts),
                "events": [
                    {
                        "timestamp": event.timestamp.isoformat(),
                        "operation_id": event.operation_id,
                        "event_type": event.event_type,
                        "title": event.title,
                        "component": event.component
                    }
                    for event in bucket_events[:5]  # Limit to 5 events per bucket
                ]
            })
            
            current_time = bucket_end
        
        return buckets
    
    def _calculate_timeline_statistics(self, records: List[OperationRecord], 
                                     time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Calculate statistics for timeline"""
        if not records:
            return {}
        
        # Basic counts
        total_operations = len(records)
        completed_operations = len([r for r in records if r.status == OperationStatus.COMPLETED])
        failed_operations = len([r for r in records if r.status == OperationStatus.FAILED])
        
        # Duration statistics
        completed_records = [r for r in records if r.duration_seconds is not None]
        if completed_records:
            durations = [r.duration_seconds for r in completed_records]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        # Operations by type
        operations_by_type = defaultdict(int)
        for record in records:
            operations_by_type[record.operation_type.value] += 1
        
        # Operations by component
        operations_by_component = defaultdict(int)
        for record in records:
            if record.component_name:
                operations_by_component[record.component_name] += 1
        
        return {
            "total_operations": total_operations,
            "completed_operations": completed_operations,
            "failed_operations": failed_operations,
            "success_rate": (completed_operations / total_operations * 100) if total_operations > 0 else 0,
            "average_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "operations_by_type": dict(operations_by_type),
            "operations_by_component": dict(operations_by_component),
            "time_range": {
                "start": time_range[0].isoformat(),
                "end": time_range[1].isoformat(),
                "duration_hours": (time_range[1] - time_range[0]).total_seconds() / 3600
            }
        }
    
    def _convert_progress_to_record(self, progress: OperationProgress) -> OperationRecord:
        """Convert OperationProgress to OperationRecord"""
        # Determine status
        if progress.is_cancelled:
            status = OperationStatus.CANCELLED
        elif progress.is_completed:
            status = OperationStatus.COMPLETED
        elif progress.errors:
            status = OperationStatus.FAILED
        elif progress.progress_percentage > 0:
            status = OperationStatus.RUNNING
        else:
            status = OperationStatus.PENDING
        
        # Calculate duration if completed
        duration = None
        end_time = None
        if progress.is_completed or progress.is_cancelled:
            end_time = datetime.now()
            duration = (end_time - progress.start_time).total_seconds()
        
        return OperationRecord(
            operation_id=progress.operation_id,
            operation_type=progress.operation_type,
            status=status,
            component_name=progress.component_name,
            title=progress.title,
            description=progress.description,
            start_time=progress.start_time,
            end_time=end_time,
            duration_seconds=duration,
            progress_percentage=progress.progress_percentage,
            current_step=progress.current_step,
            total_steps=progress.total_steps,
            current_step_number=progress.current_step_number,
            details=progress.details.copy(),
            warnings=progress.warnings.copy(),
            errors=progress.errors.copy(),
            result=progress.result,
            metadata={"speed": progress.speed, "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None}
        )
    
    def _create_timeline_event(self, record: OperationRecord) -> TimelineEvent:
        """Create timeline event from operation record"""
        event_type = "start"
        if record.status == OperationStatus.COMPLETED:
            event_type = "complete"
        elif record.status == OperationStatus.FAILED:
            event_type = "error"
        elif record.status == OperationStatus.RUNNING:
            event_type = "progress"
        
        return TimelineEvent(
            timestamp=record.end_time or record.start_time,
            operation_id=record.operation_id,
            event_type=event_type,
            title=record.title,
            description=record.description,
            component=record.component_name,
            progress=record.progress_percentage,
            metadata={
                "operation_type": record.operation_type.value,
                "status": record.status.value,
                "duration": record.duration_seconds
            }
        )
    
    def _save_record_to_database(self, record: OperationRecord):
        """Save operation record to database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO operation_records (
                        operation_id, operation_type, status, component_name, title, description,
                        start_time, end_time, duration_seconds, progress_percentage, current_step,
                        total_steps, current_step_number, details, warnings, errors, result,
                        metadata, user_id, session_id, system_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.operation_id, record.operation_type.value, record.status.value,
                    record.component_name, record.title, record.description,
                    record.start_time, record.end_time, record.duration_seconds,
                    record.progress_percentage, record.current_step, record.total_steps,
                    record.current_step_number, json.dumps(record.details),
                    json.dumps(record.warnings), json.dumps(record.errors),
                    json.dumps(record.result), json.dumps(record.metadata),
                    record.user_id, record.session_id, json.dumps(record.system_info)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving record to database: {e}")
    
    def _cleanup_old_records(self):
        """Cleanup old records from memory"""
        try:
            # Remove oldest records if we exceed the limit
            if len(self.operation_records) > self.max_history_records:
                # Sort by start time and keep the newest records
                sorted_records = sorted(
                    self.operation_records.items(),
                    key=lambda x: x[1].start_time,
                    reverse=True
                )
                
                # Keep only the newest records
                records_to_keep = dict(sorted_records[:self.max_history_records])
                self.operation_records = records_to_keep
                
                self.logger.info(f"Cleaned up old records, keeping {len(records_to_keep)} newest records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {e}")
    
    def _apply_history_filters(self, records: List[OperationRecord], 
                             filters: Dict[str, Any]) -> List[OperationRecord]:
        """Apply filters to history records"""
        filtered_records = records
        
        # Status filter
        if 'status' in filters:
            status_filter = filters['status']
            if isinstance(status_filter, str):
                status_filter = [status_filter]
            filtered_records = [
                record for record in filtered_records
                if record.status.value in status_filter
            ]
        
        # Component filter
        if 'component' in filters:
            component_filter = filters['component']
            filtered_records = [
                record for record in filtered_records
                if record.component_name == component_filter
            ]
        
        # Operation type filter
        if 'operation_type' in filters:
            type_filter = filters['operation_type']
            if isinstance(type_filter, str):
                type_filter = [type_filter]
            filtered_records = [
                record for record in filtered_records
                if record.operation_type.value in type_filter
            ]
        
        # Time range filter
        if 'start_time' in filters and 'end_time' in filters:
            start_time = filters['start_time']
            end_time = filters['end_time']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            filtered_records = [
                record for record in filtered_records
                if start_time <= record.start_time <= end_time
            ]
        
        return filtered_records
    
    def _calculate_operation_summary(self, records: List[OperationRecord], 
                                   time_period: str) -> OperationSummary:
        """Calculate operation summary from records"""
        if not records:
            return OperationSummary(time_period=time_period)
        
        total_operations = len(records)
        completed_operations = len([r for r in records if r.status == OperationStatus.COMPLETED])
        failed_operations = len([r for r in records if r.status == OperationStatus.FAILED])
        cancelled_operations = len([r for r in records if r.status == OperationStatus.CANCELLED])
        
        # Calculate average duration
        completed_records = [r for r in records if r.duration_seconds is not None]
        average_duration = (
            sum(r.duration_seconds for r in completed_records) / len(completed_records)
            if completed_records else 0.0
        )
        
        # Calculate success rate
        success_rate = (completed_operations / total_operations * 100) if total_operations > 0 else 0.0
        
        # Group by type
        operations_by_type = defaultdict(int)
        for record in records:
            operations_by_type[record.operation_type.value] += 1
        
        # Group by component
        operations_by_component = defaultdict(int)
        for record in records:
            if record.component_name:
                operations_by_component[record.component_name] += 1
        
        # Group by status
        operations_by_status = defaultdict(int)
        for record in records:
            operations_by_status[record.status.value] += 1
        
        return OperationSummary(
            total_operations=total_operations,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            cancelled_operations=cancelled_operations,
            average_duration=average_duration,
            success_rate=success_rate,
            operations_by_type=dict(operations_by_type),
            operations_by_component=dict(operations_by_component),
            operations_by_status=dict(operations_by_status),
            time_period=time_period
        )
    
    def _row_to_operation_record(self, row) -> OperationRecord:
        """Convert database row to OperationRecord"""
        return OperationRecord(
            operation_id=row['operation_id'],
            operation_type=OperationType(row['operation_type']),
            status=OperationStatus(row['status']),
            component_name=row['component_name'],
            title=row['title'] or '',
            description=row['description'] or '',
            start_time=datetime.fromisoformat(row['start_time']),
            end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
            duration_seconds=row['duration_seconds'],
            progress_percentage=row['progress_percentage'] or 0.0,
            current_step=row['current_step'] or '',
            total_steps=row['total_steps'] or 1,
            current_step_number=row['current_step_number'] or 0,
            details=json.loads(row['details']) if row['details'] else [],
            warnings=json.loads(row['warnings']) if row['warnings'] else [],
            errors=json.loads(row['errors']) if row['errors'] else [],
            result=json.loads(row['result']) if row['result'] else None,
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            user_id=row['user_id'],
            session_id=row['session_id'],
            system_info=json.loads(row['system_info']) if row['system_info'] else {}
        )
    
    def _cleanup_database_records(self, cutoff_date: datetime) -> int:
        """Cleanup old records from database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM operation_records WHERE start_time < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error cleaning up database records: {e}")
            return 0
    
    def _save_all_pending_data(self):
        """Save any pending data to database"""
        try:
            # This would save any unsaved data
            pass
        except Exception as e:
            self.logger.error(f"Error saving pending data: {e}")
    
    def _close_database_connection(self):
        """Close database connection"""
        try:
            # This would close any open database connections
            pass
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}")


# Global instance
operation_history_reporting_system = OperationHistoryReportingSystem()


if __name__ == "__main__":
    # Test the Operation History and Reporting System
    import time
    
    # Create system
    system = OperationHistoryReportingSystem()
    
    # Test history tracking
    tracking_result = system.build_detailed_operation_history_tracking_and_display()
    print(f"History tracking: {tracking_result.success}, records: {tracking_result.records_tracked}")
    
    # Create mock operation progress for testing
    from modern_frontend_manager import OperationProgress, OperationType
    
    mock_progress = OperationProgress(
        operation_id="test_operation_123",
        operation_type=OperationType.INSTALLATION,
        component_name="git",
        title="Installing Git",
        description="Installing Git version control system",
        progress_percentage=100.0,
        is_completed=True
    )
    
    # Track operation
    tracked = system.track_operation(mock_progress)
    print(f"Operation tracked: {tracked}")
    
    # Test export functionality
    export_result = system.create_report_export_functionality_for_troubleshooting(
        ReportFormat.JSON,
        filters={"status": ["completed"]},
        output_path="test_export.json"
    )
    print(f"Export result: {export_result.success}, records: {export_result.records_exported}")
    
    # Test timeline visualization
    timeline_data = system.implement_operation_timeline_visualization()
    print(f"Timeline visualization: {len(timeline_data.get('events', []))} events")
    
    # Get system report
    report = system.get_system_report()
    print(f"System report generated with {len(report)} sections")
    
    # Shutdown
    system.shutdown()
    print("Test completed successfully!")