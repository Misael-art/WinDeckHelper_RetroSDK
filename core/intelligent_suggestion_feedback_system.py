# -*- coding: utf-8 -*-
"""
Intelligent Suggestion and Feedback System

This module implements intelligent suggestions based on diagnostic results,
granular component selection interface, feedback system with severity categorization,
and actionable solution provision for detected problems.

Requirements addressed:
- 8.2: Intelligent suggestions based on diagnostic results and granular component selection
- 8.3: Feedback system with severity categorization and actionable solutions
"""

import logging
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

try:
    from .unified_detection_engine import UnifiedDetectionEngine
    from .dependency_validation_system import DependencyValidationSystem
    from .modern_frontend_manager import ModernFrontendManager, ComponentInfo, ComponentStatus, ComponentCategory
    from .security_manager import SecurityManager, SecurityLevel
except ImportError:
    # Fallback for direct execution
    from unified_detection_engine import UnifiedDetectionEngine
    from dependency_validation_system import DependencyValidationSystem
    from modern_frontend_manager import ModernFrontendManager, ComponentInfo, ComponentStatus, ComponentCategory
    from security_manager import SecurityManager, SecurityLevel


class SuggestionType(Enum):
    """Types of suggestions"""
    INSTALL_MISSING = "install_missing"
    UPDATE_OUTDATED = "update_outdated"
    RESOLVE_CONFLICT = "resolve_conflict"
    OPTIMIZE_SETUP = "optimize_setup"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    CONFIGURATION_FIX = "configuration_fix"
    CLEANUP_UNUSED = "cleanup_unused"
    ALTERNATIVE_OPTION = "alternative_option"


class SuggestionPriority(Enum):
    """Priority levels for suggestions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackSeverity(Enum):
    """Severity levels for feedback messages"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"


class SelectionScope(Enum):
    """Scope for component selection"""
    INDIVIDUAL = "individual"
    CATEGORY = "category"
    DEPENDENCY_GROUP = "dependency_group"
    CUSTOM_SET = "custom_set"
    ALL = "all"


@dataclass
class IntelligentSuggestion:
    """Intelligent suggestion based on system analysis"""
    id: str
    suggestion_type: SuggestionType
    priority: SuggestionPriority
    title: str
    description: str
    rationale: str
    affected_components: List[str]
    estimated_time: Optional[str] = None  # e.g., "5 minutes"
    estimated_size: Optional[str] = None  # e.g., "150 MB"
    benefits: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    confidence_score: float = 0.0  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    dismissed: bool = False
    user_feedback: Optional[str] = None


@dataclass
class FeedbackMessage:
    """Feedback message with severity categorization"""
    id: str
    severity: FeedbackSeverity
    category: str
    title: str
    message: str
    component: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    actionable_solutions: List[Dict[str, Any]] = field(default_factory=list)
    related_suggestions: List[str] = field(default_factory=list)
    auto_dismissible: bool = True
    persistent: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class ComponentSelection:
    """Component selection configuration"""
    selection_id: str
    scope: SelectionScope
    selected_components: Set[str] = field(default_factory=set)
    excluded_components: Set[str] = field(default_factory=set)
    selection_criteria: Dict[str, Any] = field(default_factory=dict)
    auto_resolve_dependencies: bool = True
    include_optional_dependencies: bool = False
    respect_conflicts: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


@dataclass
class SuggestionResult:
    """Result of suggestion generation"""
    success: bool
    suggestions_generated: int = 0
    high_priority_suggestions: int = 0
    critical_suggestions: int = 0
    error_message: Optional[str] = None
    suggestions: List[IntelligentSuggestion] = field(default_factory=list)


@dataclass
class SelectionResult:
    """Result of component selection operations"""
    success: bool
    selected_count: int = 0
    excluded_count: int = 0
    dependency_resolved_count: int = 0
    conflicts_detected: int = 0
    error_message: Optional[str] = None
    selection_data: Optional[ComponentSelection] = None


@dataclass
class FeedbackSystemResult:
    """Result of feedback system operations"""
    success: bool
    messages_created: int = 0
    solutions_provided: int = 0
    error_message: Optional[str] = None
    feedback_data: List[FeedbackMessage] = field(default_factory=list)


class IntelligentSuggestionFeedbackSystem:
    """
    Comprehensive Intelligent Suggestion and Feedback System
    
    Provides:
    - Intelligent suggestions based on diagnostic results
    - Granular component selection interface
    - Feedback system with severity categorization
    - Actionable solution provision for detected problems
    - Machine learning-based recommendation engine
    """
    
    def __init__(self,
                 detection_engine: Optional[UnifiedDetectionEngine] = None,
                 dependency_validator: Optional[DependencyValidationSystem] = None,
                 frontend_manager: Optional[ModernFrontendManager] = None,
                 security_manager: Optional[SecurityManager] = None):
        """
        Initialize Intelligent Suggestion and Feedback System
        
        Args:
            detection_engine: Detection engine for system analysis
            dependency_validator: Dependency validation system
            frontend_manager: Frontend manager for UI integration
            security_manager: Security manager for auditing
        """
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.detection_engine = detection_engine or UnifiedDetectionEngine()
        self.dependency_validator = dependency_validator or DependencyValidationSystem()
        self.frontend_manager = frontend_manager or ModernFrontendManager()
        self.security_manager = security_manager or SecurityManager()
        
        # Suggestion and feedback storage
        self.active_suggestions: Dict[str, IntelligentSuggestion] = {}
        self.suggestion_history: List[IntelligentSuggestion] = []
        self.active_feedback: Dict[str, FeedbackMessage] = {}
        self.feedback_history: List[FeedbackMessage] = []
        self.component_selections: Dict[str, ComponentSelection] = {}
        
        # Configuration
        self.max_suggestions = 20
        self.max_feedback_messages = 50
        self.suggestion_refresh_interval = 300  # 5 minutes
        self.enable_ml_suggestions = True
        self.auto_apply_safe_suggestions = False
        
        # Analytics and learning
        self.user_preferences: Dict[str, Any] = {}
        self.suggestion_effectiveness: Dict[str, float] = {}
        self.component_usage_patterns: Dict[str, int] = defaultdict(int)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load configuration and data
        self._load_system_config()
        self._load_user_preferences()
        
        self.logger.info("Intelligent Suggestion and Feedback System initialized")
    
    def offer_intelligent_suggestions_based_on_diagnosis(self, diagnosis_result: Any) -> SuggestionResult:
        """
        Offer intelligent suggestions based on diagnostic results
        
        Args:
            diagnosis_result: Results from system diagnosis
            
        Returns:
            SuggestionResult: Generated suggestions and metadata
        """
        try:
            result = SuggestionResult(success=False)
            suggestions = []
            
            # Analyze diagnostic results
            analysis = self._analyze_diagnostic_results(diagnosis_result)
            
            # Generate different types of suggestions
            missing_component_suggestions = self._generate_missing_component_suggestions(analysis)
            suggestions.extend(missing_component_suggestions)
            
            outdated_component_suggestions = self._generate_outdated_component_suggestions(analysis)
            suggestions.extend(outdated_component_suggestions)
            
            conflict_resolution_suggestions = self._generate_conflict_resolution_suggestions(analysis)
            suggestions.extend(conflict_resolution_suggestions)
            
            optimization_suggestions = self._generate_optimization_suggestions(analysis)
            suggestions.extend(optimization_suggestions)
            
            security_suggestions = self._generate_security_suggestions(analysis)
            suggestions.extend(security_suggestions)
            
            performance_suggestions = self._generate_performance_suggestions(analysis)
            suggestions.extend(performance_suggestions)
            
            # Apply machine learning recommendations if enabled
            if self.enable_ml_suggestions:
                ml_suggestions = self._generate_ml_based_suggestions(analysis)
                suggestions.extend(ml_suggestions)
            
            # Rank and filter suggestions
            ranked_suggestions = self._rank_and_filter_suggestions(suggestions)
            
            # Store suggestions
            with self._lock:
                for suggestion in ranked_suggestions:
                    self.active_suggestions[suggestion.id] = suggestion
                    self.suggestion_history.append(suggestion)
            
            # Calculate result metrics
            result.suggestions = ranked_suggestions
            result.suggestions_generated = len(ranked_suggestions)
            result.high_priority_suggestions = len([s for s in ranked_suggestions if s.priority == SuggestionPriority.HIGH])
            result.critical_suggestions = len([s for s in ranked_suggestions if s.priority == SuggestionPriority.CRITICAL])
            result.success = True
            
            self.logger.info(f"Generated {len(ranked_suggestions)} intelligent suggestions")
            
            # Audit suggestion generation
            self.security_manager.audit_critical_operation(
                operation="intelligent_suggestion_generation",
                component="suggestion_feedback_system",
                details={
                    "suggestions_generated": result.suggestions_generated,
                    "high_priority": result.high_priority_suggestions,
                    "critical": result.critical_suggestions
                },
                success=True,
                security_level=SecurityLevel.LOW
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating intelligent suggestions: {e}")
            return SuggestionResult(
                success=False,
                error_message=str(e)
            )
    
    def allow_granular_component_selection(self, selection_criteria: Dict[str, Any]) -> SelectionResult:
        """
        Allow granular component selection with advanced filtering
        
        Args:
            selection_criteria: Criteria for component selection
            
        Returns:
            SelectionResult: Result of selection operation
        """
        try:
            result = SelectionResult(success=False)
            
            # Create selection configuration
            selection_id = f"selection_{datetime.now().timestamp()}"
            selection = ComponentSelection(
                selection_id=selection_id,
                scope=SelectionScope(selection_criteria.get('scope', 'individual')),
                selection_criteria=selection_criteria,
                auto_resolve_dependencies=selection_criteria.get('auto_resolve_dependencies', True),
                include_optional_dependencies=selection_criteria.get('include_optional_dependencies', False),
                respect_conflicts=selection_criteria.get('respect_conflicts', True)
            )
            
            # Get available components
            dashboard_state = self.frontend_manager.get_dashboard_state()
            available_components = dashboard_state.components
            
            # Apply selection logic
            selected_components = self._apply_selection_criteria(available_components, selection_criteria)
            selection.selected_components = selected_components
            
            # Resolve dependencies if requested
            if selection.auto_resolve_dependencies:
                dependency_resolved = self._resolve_selection_dependencies(selection, available_components)
                result.dependency_resolved_count = len(dependency_resolved)
                selection.selected_components.update(dependency_resolved)
            
            # Check for conflicts
            conflicts = self._detect_selection_conflicts(selection, available_components)
            result.conflicts_detected = len(conflicts)
            
            # Apply conflict resolution if requested
            if selection.respect_conflicts and conflicts:
                resolved_selection = self._resolve_selection_conflicts(selection, conflicts)
                selection = resolved_selection
            
            # Store selection
            with self._lock:
                self.component_selections[selection_id] = selection
            
            # Update result
            result.success = True
            result.selected_count = len(selection.selected_components)
            result.excluded_count = len(selection.excluded_components)
            result.selection_data = selection
            
            self.logger.info(f"Created granular component selection: {result.selected_count} selected, {result.excluded_count} excluded")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in granular component selection: {e}")
            return SelectionResult(
                success=False,
                error_message=str(e)
            )
    
    def implement_feedback_system_with_severity_categorization(self, 
                                                             feedback_data: List[Dict[str, Any]]) -> FeedbackSystemResult:
        """
        Implement feedback system with severity categorization
        
        Args:
            feedback_data: List of feedback items to process
            
        Returns:
            FeedbackSystemResult: Result of feedback system implementation
        """
        try:
            result = FeedbackSystemResult(success=False)
            feedback_messages = []
            
            for feedback_item in feedback_data:
                # Create feedback message
                message = self._create_feedback_message(feedback_item)
                
                # Generate actionable solutions
                solutions = self._generate_actionable_solutions(message)
                message.actionable_solutions = solutions
                
                # Link related suggestions
                related_suggestions = self._find_related_suggestions(message)
                message.related_suggestions = related_suggestions
                
                feedback_messages.append(message)
            
            # Categorize and prioritize messages
            categorized_messages = self._categorize_feedback_messages(feedback_messages)
            
            # Store feedback messages
            with self._lock:
                for message in categorized_messages:
                    self.active_feedback[message.id] = message
                    self.feedback_history.append(message)
                
                # Limit active feedback messages
                if len(self.active_feedback) > self.max_feedback_messages:
                    self._cleanup_old_feedback_messages()
            
            # Update result
            result.success = True
            result.messages_created = len(categorized_messages)
            result.solutions_provided = sum(len(msg.actionable_solutions) for msg in categorized_messages)
            result.feedback_data = categorized_messages
            
            self.logger.info(f"Implemented feedback system: {result.messages_created} messages, {result.solutions_provided} solutions")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error implementing feedback system: {e}")
            return FeedbackSystemResult(
                success=False,
                error_message=str(e)
            )
    
    def provide_actionable_solutions_for_problems(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Provide actionable solutions for detected problems
        
        Args:
            problem_context: Context information about the problem
            
        Returns:
            List[Dict[str, Any]]: List of actionable solutions
        """
        try:
            solutions = []
            
            problem_type = problem_context.get('type', 'unknown')
            problem_severity = problem_context.get('severity', 'medium')
            affected_components = problem_context.get('components', [])
            
            # Generate solutions based on problem type
            if problem_type == 'missing_dependency':
                solutions.extend(self._generate_dependency_solutions(problem_context))
            elif problem_type == 'version_conflict':
                solutions.extend(self._generate_conflict_solutions(problem_context))
            elif problem_type == 'installation_failure':
                solutions.extend(self._generate_installation_solutions(problem_context))
            elif problem_type == 'configuration_error':
                solutions.extend(self._generate_configuration_solutions(problem_context))
            elif problem_type == 'security_issue':
                solutions.extend(self._generate_security_solutions_for_problem(problem_context))
            elif problem_type == 'performance_issue':
                solutions.extend(self._generate_performance_solutions(problem_context))
            else:
                solutions.extend(self._generate_generic_solutions(problem_context))
            
            # Rank solutions by effectiveness and feasibility
            ranked_solutions = self._rank_solutions_by_effectiveness(solutions, problem_context)
            
            self.logger.info(f"Generated {len(ranked_solutions)} actionable solutions for {problem_type}")
            
            return ranked_solutions
            
        except Exception as e:
            self.logger.error(f"Error providing actionable solutions: {e}")
            return []
    
    def get_suggestion_report(self) -> Dict[str, Any]:
        """
        Get comprehensive suggestion and feedback report
        
        Returns:
            Dict[str, Any]: Detailed report
        """
        try:
            with self._lock:
                active_suggestions = list(self.active_suggestions.values())
                active_feedback = list(self.active_feedback.values())
            
            # Calculate statistics
            suggestion_stats = self._calculate_suggestion_statistics(active_suggestions)
            feedback_stats = self._calculate_feedback_statistics(active_feedback)
            
            # Generate effectiveness metrics
            effectiveness_metrics = self._calculate_effectiveness_metrics()
            
            return {
                "summary": {
                    "active_suggestions": len(active_suggestions),
                    "active_feedback": len(active_feedback),
                    "total_suggestions_generated": len(self.suggestion_history),
                    "total_feedback_messages": len(self.feedback_history),
                    "component_selections": len(self.component_selections)
                },
                "suggestion_statistics": suggestion_stats,
                "feedback_statistics": feedback_stats,
                "effectiveness_metrics": effectiveness_metrics,
                "active_suggestions": [
                    {
                        "id": s.id,
                        "type": s.suggestion_type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "confidence_score": s.confidence_score,
                        "applied": s.applied,
                        "dismissed": s.dismissed
                    }
                    for s in active_suggestions
                ],
                "active_feedback": [
                    {
                        "id": f.id,
                        "severity": f.severity.value,
                        "category": f.category,
                        "title": f.title,
                        "component": f.component,
                        "solutions_count": len(f.actionable_solutions),
                        "acknowledged": f.acknowledged
                    }
                    for f in active_feedback
                ],
                "user_preferences": self.user_preferences,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating suggestion report: {e}")
            return {"error": str(e)}
    
    def apply_suggestion(self, suggestion_id: str, user_confirmation: bool = True) -> bool:
        """
        Apply a specific suggestion
        
        Args:
            suggestion_id: ID of suggestion to apply
            user_confirmation: Whether user confirmed the action
            
        Returns:
            bool: True if suggestion was applied successfully
        """
        try:
            with self._lock:
                suggestion = self.active_suggestions.get(suggestion_id)
                if not suggestion:
                    self.logger.warning(f"Suggestion {suggestion_id} not found")
                    return False
                
                if suggestion.applied:
                    self.logger.info(f"Suggestion {suggestion_id} already applied")
                    return True
                
                # Execute suggestion actions
                success = self._execute_suggestion_actions(suggestion, user_confirmation)
                
                if success:
                    suggestion.applied = True
                    self.logger.info(f"Successfully applied suggestion: {suggestion_id}")
                    
                    # Update effectiveness tracking
                    self.suggestion_effectiveness[suggestion.suggestion_type.value] = \
                        self.suggestion_effectiveness.get(suggestion.suggestion_type.value, 0.5) + 0.1
                else:
                    self.logger.error(f"Failed to apply suggestion: {suggestion_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error applying suggestion {suggestion_id}: {e}")
            return False
    
    def dismiss_suggestion(self, suggestion_id: str, reason: Optional[str] = None) -> bool:
        """
        Dismiss a specific suggestion
        
        Args:
            suggestion_id: ID of suggestion to dismiss
            reason: Optional reason for dismissal
            
        Returns:
            bool: True if suggestion was dismissed successfully
        """
        try:
            with self._lock:
                suggestion = self.active_suggestions.get(suggestion_id)
                if not suggestion:
                    self.logger.warning(f"Suggestion {suggestion_id} not found")
                    return False
                
                suggestion.dismissed = True
                suggestion.user_feedback = reason
                
                # Update effectiveness tracking (negative feedback)
                self.suggestion_effectiveness[suggestion.suggestion_type.value] = \
                    max(0.0, self.suggestion_effectiveness.get(suggestion.suggestion_type.value, 0.5) - 0.05)
                
                self.logger.info(f"Dismissed suggestion: {suggestion_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error dismissing suggestion {suggestion_id}: {e}")
            return False
    
    def acknowledge_feedback(self, feedback_id: str) -> bool:
        """
        Acknowledge a feedback message
        
        Args:
            feedback_id: ID of feedback message to acknowledge
            
        Returns:
            bool: True if feedback was acknowledged successfully
        """
        try:
            with self._lock:
                feedback = self.active_feedback.get(feedback_id)
                if not feedback:
                    self.logger.warning(f"Feedback {feedback_id} not found")
                    return False
                
                feedback.acknowledged = True
                
                # Remove from active feedback if auto-dismissible
                if feedback.auto_dismissible and not feedback.persistent:
                    del self.active_feedback[feedback_id]
                
                self.logger.info(f"Acknowledged feedback: {feedback_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error acknowledging feedback {feedback_id}: {e}")
            return False
    
    def shutdown(self):
        """Shutdown suggestion and feedback system"""
        self.logger.info("Shutting down Intelligent Suggestion and Feedback System")
        
        # Save user preferences and effectiveness data
        self._save_user_preferences()
        self._save_effectiveness_data()
        
        self.logger.info("Intelligent Suggestion and Feedback System shutdown complete")
    
    # Private helper methods
    
    def _analyze_diagnostic_results(self, diagnosis_result: Any) -> Dict[str, Any]:
        """Analyze diagnostic results for suggestion generation"""
        analysis = {
            "missing_components": [],
            "outdated_components": [],
            "conflicts": [],
            "security_issues": [],
            "performance_issues": [],
            "configuration_problems": []
        }
        
        try:
            # Extract information from diagnosis result
            if hasattr(diagnosis_result, 'missing_components'):
                analysis["missing_components"] = diagnosis_result.missing_components
            
            if hasattr(diagnosis_result, 'outdated_components'):
                analysis["outdated_components"] = diagnosis_result.outdated_components
            
            if hasattr(diagnosis_result, 'conflicts'):
                analysis["conflicts"] = diagnosis_result.conflicts
            
            # Additional analysis based on dashboard state
            dashboard_state = self.frontend_manager.get_dashboard_state()
            for component_name, component_info in dashboard_state.components.items():
                if component_info.status == ComponentStatus.NOT_INSTALLED:
                    analysis["missing_components"].append(component_name)
                elif component_info.status == ComponentStatus.OUTDATED:
                    analysis["outdated_components"].append(component_name)
                elif component_info.status == ComponentStatus.FAILED:
                    analysis["configuration_problems"].append(component_name)
            
        except Exception as e:
            self.logger.error(f"Error analyzing diagnostic results: {e}")
        
        return analysis   
 
    def _generate_missing_component_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate suggestions for missing components"""
        suggestions = []
        
        for component_name in analysis.get("missing_components", []):
            suggestion = IntelligentSuggestion(
                id=f"install_{component_name}_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.INSTALL_MISSING,
                priority=SuggestionPriority.HIGH,
                title=f"Install {component_name}",
                description=f"Install missing component {component_name} to complete your development environment",
                rationale=f"{component_name} is required for optimal development workflow",
                affected_components=[component_name],
                benefits=[
                    f"Enable {component_name} functionality",
                    "Complete development environment setup",
                    "Resolve dependency requirements"
                ],
                actions=[
                    {
                        "type": "install",
                        "component": component_name,
                        "method": "automatic"
                    }
                ],
                confidence_score=0.9
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_outdated_component_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate suggestions for outdated components"""
        suggestions = []
        
        for component_name in analysis.get("outdated_components", []):
            suggestion = IntelligentSuggestion(
                id=f"update_{component_name}_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.UPDATE_OUTDATED,
                priority=SuggestionPriority.MEDIUM,
                title=f"Update {component_name}",
                description=f"Update {component_name} to the latest version for improved features and security",
                rationale=f"Newer version of {component_name} available with improvements",
                affected_components=[component_name],
                benefits=[
                    "Latest features and improvements",
                    "Security patches and bug fixes",
                    "Better compatibility with other tools"
                ],
                risks=[
                    "Potential breaking changes",
                    "Need to update configurations"
                ],
                actions=[
                    {
                        "type": "update",
                        "component": component_name,
                        "method": "automatic"
                    }
                ],
                confidence_score=0.8
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_conflict_resolution_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate suggestions for resolving conflicts"""
        suggestions = []
        
        for conflict in analysis.get("conflicts", []):
            suggestion = IntelligentSuggestion(
                id=f"resolve_conflict_{conflict.get('id', 'unknown')}_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.RESOLVE_CONFLICT,
                priority=SuggestionPriority.HIGH,
                title=f"Resolve {conflict.get('type', 'Unknown')} Conflict",
                description=f"Resolve conflict between {', '.join(conflict.get('components', []))}",
                rationale="Conflicts can cause installation failures and system instability",
                affected_components=conflict.get("components", []),
                benefits=[
                    "Eliminate system conflicts",
                    "Ensure stable installations",
                    "Prevent future issues"
                ],
                actions=[
                    {
                        "type": "resolve_conflict",
                        "conflict_id": conflict.get("id"),
                        "strategy": "automatic"
                    }
                ],
                confidence_score=0.7
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Suggest cleanup of unused components
        dashboard_state = self.frontend_manager.get_dashboard_state()
        unused_components = [
            name for name, info in dashboard_state.components.items()
            if info.status == ComponentStatus.INSTALLED and 
            self.component_usage_patterns.get(name, 0) == 0
        ]
        
        if unused_components:
            suggestion = IntelligentSuggestion(
                id=f"cleanup_unused_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.CLEANUP_UNUSED,
                priority=SuggestionPriority.LOW,
                title="Clean up unused components",
                description=f"Remove {len(unused_components)} unused components to free up space",
                rationale="Unused components consume disk space and may cause conflicts",
                affected_components=unused_components,
                benefits=[
                    "Free up disk space",
                    "Reduce system complexity",
                    "Improve performance"
                ],
                actions=[
                    {
                        "type": "cleanup",
                        "components": unused_components,
                        "method": "selective"
                    }
                ],
                confidence_score=0.6
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_security_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate security-related suggestions"""
        suggestions = []
        
        for issue in analysis.get("security_issues", []):
            suggestion = IntelligentSuggestion(
                id=f"security_fix_{issue.get('id', 'unknown')}_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.SECURITY_FIX,
                priority=SuggestionPriority.CRITICAL,
                title=f"Fix Security Issue: {issue.get('title', 'Unknown')}",
                description=issue.get("description", "Security vulnerability detected"),
                rationale="Security issues pose risks to system integrity and data safety",
                affected_components=issue.get("components", []),
                benefits=[
                    "Improve system security",
                    "Protect against vulnerabilities",
                    "Ensure compliance"
                ],
                actions=[
                    {
                        "type": "security_fix",
                        "issue_id": issue.get("id"),
                        "method": "automatic"
                    }
                ],
                confidence_score=0.95
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_performance_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate performance improvement suggestions"""
        suggestions = []
        
        for issue in analysis.get("performance_issues", []):
            suggestion = IntelligentSuggestion(
                id=f"performance_fix_{issue.get('id', 'unknown')}_{datetime.now().timestamp()}",
                suggestion_type=SuggestionType.PERFORMANCE_IMPROVEMENT,
                priority=SuggestionPriority.MEDIUM,
                title=f"Improve Performance: {issue.get('title', 'Unknown')}",
                description=issue.get("description", "Performance optimization opportunity"),
                rationale="Performance improvements enhance user experience and productivity",
                affected_components=issue.get("components", []),
                benefits=[
                    "Faster operation",
                    "Better resource utilization",
                    "Improved user experience"
                ],
                actions=[
                    {
                        "type": "performance_fix",
                        "issue_id": issue.get("id"),
                        "method": "automatic"
                    }
                ],
                confidence_score=0.7
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_ml_based_suggestions(self, analysis: Dict[str, Any]) -> List[IntelligentSuggestion]:
        """Generate machine learning based suggestions"""
        suggestions = []
        
        try:
            # Analyze user patterns and preferences
            user_patterns = self._analyze_user_patterns()
            
            # Generate personalized suggestions based on usage patterns
            if user_patterns.get("prefers_latest_versions", False):
                # Suggest updating to latest versions
                for component_name in user_patterns.get("frequently_used_components", []):
                    suggestion = IntelligentSuggestion(
                        id=f"ml_update_{component_name}_{datetime.now().timestamp()}",
                        suggestion_type=SuggestionType.UPDATE_OUTDATED,
                        priority=SuggestionPriority.MEDIUM,
                        title=f"ML Recommendation: Update {component_name}",
                        description=f"Based on your usage patterns, updating {component_name} is recommended",
                        rationale="Machine learning analysis suggests this update aligns with your preferences",
                        affected_components=[component_name],
                        benefits=[
                            "Personalized recommendation",
                            "Based on usage patterns",
                            "Improved workflow efficiency"
                        ],
                        actions=[
                            {
                                "type": "update",
                                "component": component_name,
                                "method": "ml_recommended"
                            }
                        ],
                        confidence_score=user_patterns.get("confidence", 0.6)
                    )
                    suggestions.append(suggestion)
            
            # Suggest alternative tools based on similar users
            similar_user_preferences = self._get_similar_user_preferences()
            for alternative in similar_user_preferences.get("recommended_alternatives", []):
                suggestion = IntelligentSuggestion(
                    id=f"ml_alternative_{alternative}_{datetime.now().timestamp()}",
                    suggestion_type=SuggestionType.ALTERNATIVE_OPTION,
                    priority=SuggestionPriority.LOW,
                    title=f"Consider Alternative: {alternative}",
                    description=f"Users with similar preferences often use {alternative}",
                    rationale="Recommendation based on similar user profiles",
                    affected_components=[alternative],
                    benefits=[
                        "Popular among similar users",
                        "May better fit your workflow",
                        "Community recommended"
                    ],
                    actions=[
                        {
                            "type": "explore_alternative",
                            "component": alternative,
                            "method": "research"
                        }
                    ],
                    confidence_score=0.5
                )
                suggestions.append(suggestion)
        
        except Exception as e:
            self.logger.error(f"Error generating ML-based suggestions: {e}")
        
        return suggestions
    
    def _rank_and_filter_suggestions(self, suggestions: List[IntelligentSuggestion]) -> List[IntelligentSuggestion]:
        """Rank and filter suggestions by priority and relevance"""
        try:
            # Sort by priority and confidence score
            priority_order = {
                SuggestionPriority.CRITICAL: 4,
                SuggestionPriority.HIGH: 3,
                SuggestionPriority.MEDIUM: 2,
                SuggestionPriority.LOW: 1
            }
            
            sorted_suggestions = sorted(
                suggestions,
                key=lambda s: (priority_order[s.priority], s.confidence_score),
                reverse=True
            )
            
            # Filter out low-confidence suggestions
            filtered_suggestions = [
                s for s in sorted_suggestions 
                if s.confidence_score >= 0.3
            ]
            
            # Limit to max suggestions
            return filtered_suggestions[:self.max_suggestions]
            
        except Exception as e:
            self.logger.error(f"Error ranking and filtering suggestions: {e}")
            return suggestions[:self.max_suggestions]
    
    def _apply_selection_criteria(self, available_components: Dict[str, ComponentInfo], 
                                criteria: Dict[str, Any]) -> Set[str]:
        """Apply selection criteria to components"""
        selected = set()
        
        try:
            scope = criteria.get('scope', 'individual')
            
            if scope == 'all':
                selected = set(available_components.keys())
            elif scope == 'category':
                target_categories = criteria.get('categories', [])
                for component_name, component_info in available_components.items():
                    if component_info.category.value in target_categories:
                        selected.add(component_name)
            elif scope == 'individual':
                selected = set(criteria.get('components', []))
            elif scope == 'dependency_group':
                # Select components and their dependencies
                base_components = criteria.get('components', [])
                for component_name in base_components:
                    selected.add(component_name)
                    if component_name in available_components:
                        selected.update(available_components[component_name].dependencies)
            
            # Apply filters
            status_filter = criteria.get('status_filter')
            if status_filter:
                filtered_selected = set()
                for component_name in selected:
                    if component_name in available_components:
                        component_status = available_components[component_name].status.value
                        if component_status in status_filter:
                            filtered_selected.add(component_name)
                selected = filtered_selected
            
            # Apply priority filter
            min_priority = criteria.get('min_priority', 0)
            if min_priority > 0:
                filtered_selected = set()
                for component_name in selected:
                    if component_name in available_components:
                        component_priority = available_components[component_name].priority
                        if component_priority >= min_priority:
                            filtered_selected.add(component_name)
                selected = filtered_selected
            
        except Exception as e:
            self.logger.error(f"Error applying selection criteria: {e}")
        
        return selected
    
    def _resolve_selection_dependencies(self, selection: ComponentSelection, 
                                      available_components: Dict[str, ComponentInfo]) -> Set[str]:
        """Resolve dependencies for selected components"""
        resolved = set()
        
        try:
            for component_name in selection.selected_components:
                if component_name in available_components:
                    component_info = available_components[component_name]
                    resolved.update(component_info.dependencies)
        
        except Exception as e:
            self.logger.error(f"Error resolving selection dependencies: {e}")
        
        return resolved
    
    def _detect_selection_conflicts(self, selection: ComponentSelection, 
                                  available_components: Dict[str, ComponentInfo]) -> List[Dict[str, Any]]:
        """Detect conflicts in component selection"""
        conflicts = []
        
        try:
            for component_name in selection.selected_components:
                if component_name in available_components:
                    component_info = available_components[component_name]
                    for conflict_component in component_info.conflicts:
                        if conflict_component in selection.selected_components:
                            conflicts.append({
                                "type": "component_conflict",
                                "components": [component_name, conflict_component],
                                "description": f"{component_name} conflicts with {conflict_component}"
                            })
        
        except Exception as e:
            self.logger.error(f"Error detecting selection conflicts: {e}")
        
        return conflicts
    
    def _resolve_selection_conflicts(self, selection: ComponentSelection, 
                                   conflicts: List[Dict[str, Any]]) -> ComponentSelection:
        """Resolve conflicts in component selection"""
        try:
            for conflict in conflicts:
                if conflict["type"] == "component_conflict":
                    components = conflict["components"]
                    # Remove lower priority component
                    # This is a simplified resolution strategy
                    if len(components) >= 2:
                        selection.excluded_components.add(components[1])
                        selection.selected_components.discard(components[1])
        
        except Exception as e:
            self.logger.error(f"Error resolving selection conflicts: {e}")
        
        return selection
    
    def _create_feedback_message(self, feedback_item: Dict[str, Any]) -> FeedbackMessage:
        """Create feedback message from feedback item"""
        message_id = f"feedback_{datetime.now().timestamp()}"
        
        return FeedbackMessage(
            id=message_id,
            severity=FeedbackSeverity(feedback_item.get('severity', 'info')),
            category=feedback_item.get('category', 'general'),
            title=feedback_item.get('title', 'System Feedback'),
            message=feedback_item.get('message', ''),
            component=feedback_item.get('component'),
            context=feedback_item.get('context', {}),
            auto_dismissible=feedback_item.get('auto_dismissible', True),
            persistent=feedback_item.get('persistent', False)
        )
    
    def _generate_actionable_solutions(self, message: FeedbackMessage) -> List[Dict[str, Any]]:
        """Generate actionable solutions for feedback message"""
        solutions = []
        
        try:
            if message.severity == FeedbackSeverity.ERROR:
                if "installation" in message.category.lower():
                    solutions.extend([
                        {
                            "title": "Retry Installation",
                            "description": "Attempt to install the component again",
                            "action": "retry_installation",
                            "component": message.component,
                            "difficulty": "easy"
                        },
                        {
                            "title": "Check Prerequisites",
                            "description": "Verify all prerequisites are met",
                            "action": "check_prerequisites",
                            "component": message.component,
                            "difficulty": "medium"
                        }
                    ])
                elif "dependency" in message.category.lower():
                    solutions.extend([
                        {
                            "title": "Install Missing Dependencies",
                            "description": "Automatically install required dependencies",
                            "action": "install_dependencies",
                            "component": message.component,
                            "difficulty": "easy"
                        },
                        {
                            "title": "Resolve Version Conflicts",
                            "description": "Update components to compatible versions",
                            "action": "resolve_version_conflicts",
                            "component": message.component,
                            "difficulty": "medium"
                        }
                    ])
            elif message.severity == FeedbackSeverity.WARNING:
                solutions.extend([
                    {
                        "title": "Review Configuration",
                        "description": "Check component configuration settings",
                        "action": "review_configuration",
                        "component": message.component,
                        "difficulty": "medium"
                    }
                ])
        
        except Exception as e:
            self.logger.error(f"Error generating actionable solutions: {e}")
        
        return solutions
    
    def _find_related_suggestions(self, message: FeedbackMessage) -> List[str]:
        """Find suggestions related to feedback message"""
        related = []
        
        try:
            for suggestion_id, suggestion in self.active_suggestions.items():
                if message.component in suggestion.affected_components:
                    related.append(suggestion_id)
                elif message.category.lower() in suggestion.description.lower():
                    related.append(suggestion_id)
        
        except Exception as e:
            self.logger.error(f"Error finding related suggestions: {e}")
        
        return related
    
    def _categorize_feedback_messages(self, messages: List[FeedbackMessage]) -> List[FeedbackMessage]:
        """Categorize and prioritize feedback messages"""
        try:
            # Sort by severity
            severity_order = {
                FeedbackSeverity.CRITICAL: 5,
                FeedbackSeverity.ERROR: 4,
                FeedbackSeverity.WARNING: 3,
                FeedbackSeverity.INFO: 2,
                FeedbackSeverity.SUCCESS: 1
            }
            
            return sorted(messages, key=lambda m: severity_order[m.severity], reverse=True)
        
        except Exception as e:
            self.logger.error(f"Error categorizing feedback messages: {e}")
            return messages
    
    def _cleanup_old_feedback_messages(self):
        """Clean up old feedback messages"""
        try:
            # Remove oldest auto-dismissible messages
            auto_dismissible = [
                (msg_id, msg) for msg_id, msg in self.active_feedback.items()
                if msg.auto_dismissible and not msg.persistent
            ]
            
            # Sort by timestamp and remove oldest
            auto_dismissible.sort(key=lambda x: x[1].timestamp)
            
            excess_count = len(self.active_feedback) - self.max_feedback_messages
            for i in range(min(excess_count, len(auto_dismissible))):
                msg_id = auto_dismissible[i][0]
                del self.active_feedback[msg_id]
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old feedback messages: {e}")
    
    def _analyze_user_patterns(self) -> Dict[str, Any]:
        """Analyze user patterns for ML suggestions"""
        patterns = {
            "prefers_latest_versions": False,
            "frequently_used_components": [],
            "confidence": 0.5
        }
        
        try:
            # Analyze component usage patterns
            if self.component_usage_patterns:
                most_used = sorted(
                    self.component_usage_patterns.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                patterns["frequently_used_components"] = [comp[0] for comp in most_used]
            
            # Analyze suggestion acceptance patterns
            update_suggestions_applied = sum(
                1 for s in self.suggestion_history
                if s.suggestion_type == SuggestionType.UPDATE_OUTDATED and s.applied
            )
            total_update_suggestions = sum(
                1 for s in self.suggestion_history
                if s.suggestion_type == SuggestionType.UPDATE_OUTDATED
            )
            
            if total_update_suggestions > 0:
                update_acceptance_rate = update_suggestions_applied / total_update_suggestions
                patterns["prefers_latest_versions"] = update_acceptance_rate > 0.7
                patterns["confidence"] = min(0.9, update_acceptance_rate)
        
        except Exception as e:
            self.logger.error(f"Error analyzing user patterns: {e}")
        
        return patterns
    
    def _get_similar_user_preferences(self) -> Dict[str, Any]:
        """Get preferences from similar users (mock implementation)"""
        # This would typically connect to a recommendation service
        return {
            "recommended_alternatives": ["vscode", "git", "nodejs"],
            "confidence": 0.4
        }
    
    def _calculate_suggestion_statistics(self, suggestions: List[IntelligentSuggestion]) -> Dict[str, Any]:
        """Calculate suggestion statistics"""
        if not suggestions:
            return {}
        
        by_type = Counter(s.suggestion_type.value for s in suggestions)
        by_priority = Counter(s.priority.value for s in suggestions)
        
        applied_count = sum(1 for s in suggestions if s.applied)
        dismissed_count = sum(1 for s in suggestions if s.dismissed)
        
        avg_confidence = sum(s.confidence_score for s in suggestions) / len(suggestions)
        
        return {
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "applied_count": applied_count,
            "dismissed_count": dismissed_count,
            "pending_count": len(suggestions) - applied_count - dismissed_count,
            "average_confidence": round(avg_confidence, 2)
        }
    
    def _calculate_feedback_statistics(self, feedback_messages: List[FeedbackMessage]) -> Dict[str, Any]:
        """Calculate feedback statistics"""
        if not feedback_messages:
            return {}
        
        by_severity = Counter(f.severity.value for f in feedback_messages)
        by_category = Counter(f.category for f in feedback_messages)
        
        acknowledged_count = sum(1 for f in feedback_messages if f.acknowledged)
        with_solutions_count = sum(1 for f in feedback_messages if f.actionable_solutions)
        
        return {
            "by_severity": dict(by_severity),
            "by_category": dict(by_category),
            "acknowledged_count": acknowledged_count,
            "with_solutions_count": with_solutions_count,
            "pending_count": len(feedback_messages) - acknowledged_count
        }
    
    def _calculate_effectiveness_metrics(self) -> Dict[str, Any]:
        """Calculate effectiveness metrics"""
        return {
            "suggestion_effectiveness": dict(self.suggestion_effectiveness),
            "total_suggestions_generated": len(self.suggestion_history),
            "total_suggestions_applied": sum(1 for s in self.suggestion_history if s.applied),
            "total_feedback_messages": len(self.feedback_history),
            "user_satisfaction_indicators": {
                "suggestions_applied_rate": len([s for s in self.suggestion_history if s.applied]) / max(1, len(self.suggestion_history)),
                "suggestions_dismissed_rate": len([s for s in self.suggestion_history if s.dismissed]) / max(1, len(self.suggestion_history))
            }
        }
    
    def _execute_suggestion_actions(self, suggestion: IntelligentSuggestion, user_confirmation: bool) -> bool:
        """Execute actions for a suggestion"""
        try:
            for action in suggestion.actions:
                action_type = action.get("type")
                
                if action_type == "install":
                    # Mock installation action
                    self.logger.info(f"Executing install action for {action.get('component')}")
                elif action_type == "update":
                    # Mock update action
                    self.logger.info(f"Executing update action for {action.get('component')}")
                elif action_type == "resolve_conflict":
                    # Mock conflict resolution action
                    self.logger.info(f"Executing conflict resolution for {action.get('conflict_id')}")
                elif action_type == "cleanup":
                    # Mock cleanup action
                    self.logger.info(f"Executing cleanup action for {len(action.get('components', []))} components")
                else:
                    self.logger.warning(f"Unknown action type: {action_type}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing suggestion actions: {e}")
            return False
    
    def _load_system_config(self):
        """Load system configuration"""
        try:
            config_path = Path("config/suggestion_system.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.max_suggestions = config.get("max_suggestions", 20)
                self.max_feedback_messages = config.get("max_feedback_messages", 50)
                self.suggestion_refresh_interval = config.get("suggestion_refresh_interval", 300)
                self.enable_ml_suggestions = config.get("enable_ml_suggestions", True)
                self.auto_apply_safe_suggestions = config.get("auto_apply_safe_suggestions", False)
                
                self.logger.info("Loaded suggestion system configuration")
        except Exception as e:
            self.logger.warning(f"Could not load suggestion system config: {e}")
    
    def _load_user_preferences(self):
        """Load user preferences"""
        try:
            prefs_path = Path("config/user_preferences.json")
            if prefs_path.exists():
                with open(prefs_path, 'r') as f:
                    self.user_preferences = json.load(f)
                
                self.logger.info("Loaded user preferences")
        except Exception as e:
            self.logger.warning(f"Could not load user preferences: {e}")
    
    def _save_user_preferences(self):
        """Save user preferences"""
        try:
            prefs_path = Path("config/user_preferences.json")
            prefs_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(prefs_path, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
            
            self.logger.info("Saved user preferences")
        except Exception as e:
            self.logger.warning(f"Could not save user preferences: {e}")
    
    def _save_effectiveness_data(self):
        """Save effectiveness data"""
        try:
            effectiveness_path = Path("config/suggestion_effectiveness.json")
            effectiveness_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(effectiveness_path, 'w') as f:
                json.dump(self.suggestion_effectiveness, f, indent=2)
            
            self.logger.info("Saved effectiveness data")
        except Exception as e:
            self.logger.warning(f"Could not save effectiveness data: {e}")
    
    def _generate_dependency_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for dependency problems"""
        return [
            {
                "title": "Install Missing Dependencies",
                "description": "Automatically install all required dependencies",
                "action": "install_dependencies",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "2-5 minutes"
            },
            {
                "title": "Manual Dependency Resolution",
                "description": "Manually review and install dependencies",
                "action": "manual_dependency_resolution",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "10-15 minutes"
            }
        ]
    
    def _generate_conflict_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for conflict problems"""
        return [
            {
                "title": "Automatic Conflict Resolution",
                "description": "Let the system automatically resolve version conflicts",
                "action": "auto_resolve_conflicts",
                "component": None,
                "difficulty": "easy",
                "estimated_time": "1-3 minutes"
            },
            {
                "title": "Choose Preferred Version",
                "description": "Manually select which version to keep",
                "action": "manual_version_selection",
                "component": None,
                "difficulty": "medium",
                "estimated_time": "5-10 minutes"
            }
        ]
    
    def _generate_installation_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for installation problems"""
        return [
            {
                "title": "Retry Installation",
                "description": "Attempt installation again with fresh download",
                "action": "retry_installation",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "2-5 minutes"
            },
            {
                "title": "Check System Requirements",
                "description": "Verify system meets all requirements",
                "action": "check_requirements",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "5-10 minutes"
            },
            {
                "title": "Manual Installation",
                "description": "Download and install manually",
                "action": "manual_installation",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "hard",
                "estimated_time": "15-30 minutes"
            }
        ]
    
    def _generate_configuration_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for configuration problems"""
        return [
            {
                "title": "Reset Configuration",
                "description": "Reset component to default configuration",
                "action": "reset_configuration",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "1-2 minutes"
            },
            {
                "title": "Repair Configuration",
                "description": "Automatically detect and fix configuration issues",
                "action": "repair_configuration",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "3-5 minutes"
            }
        ]
    
    def _generate_security_solutions_for_problem(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for security problems"""
        return [
            {
                "title": "Apply Security Patch",
                "description": "Install latest security updates",
                "action": "apply_security_patch",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "2-5 minutes"
            },
            {
                "title": "Update to Secure Version",
                "description": "Upgrade to a version without known vulnerabilities",
                "action": "update_secure_version",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "5-10 minutes"
            }
        ]
    
    def _generate_performance_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate solutions for performance problems"""
        return [
            {
                "title": "Optimize Configuration",
                "description": "Apply performance optimizations",
                "action": "optimize_configuration",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "2-3 minutes"
            },
            {
                "title": "Allocate More Resources",
                "description": "Increase memory or CPU allocation",
                "action": "allocate_resources",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "5-10 minutes"
            }
        ]
    
    def _generate_generic_solutions(self, problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic solutions for unknown problems"""
        return [
            {
                "title": "Restart Component",
                "description": "Restart the affected component",
                "action": "restart_component",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "1-2 minutes"
            },
            {
                "title": "Check Documentation",
                "description": "Review component documentation for troubleshooting",
                "action": "check_documentation",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "medium",
                "estimated_time": "10-15 minutes"
            },
            {
                "title": "Contact Support",
                "description": "Get help from technical support",
                "action": "contact_support",
                "component": problem_context.get('components', [None])[0],
                "difficulty": "easy",
                "estimated_time": "Variable"
            }
        ]
    
    def _rank_solutions_by_effectiveness(self, solutions: List[Dict[str, Any]], 
                                       problem_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank solutions by effectiveness and feasibility"""
        try:
            # Define difficulty scores (lower is better)
            difficulty_scores = {
                "easy": 1,
                "medium": 2,
                "hard": 3
            }
            
            # Add effectiveness score to each solution
            for solution in solutions:
                difficulty_score = difficulty_scores.get(solution.get("difficulty", "medium"), 2)
                
                # Calculate effectiveness based on problem type and solution type
                effectiveness_score = 0.5  # Base score
                
                problem_type = problem_context.get('type', 'unknown')
                action = solution.get('action', '')
                
                # Boost score for matching solution types
                if problem_type == 'missing_dependency' and 'install' in action:
                    effectiveness_score += 0.3
                elif problem_type == 'version_conflict' and 'resolve' in action:
                    effectiveness_score += 0.3
                elif problem_type == 'installation_failure' and 'retry' in action:
                    effectiveness_score += 0.2
                elif problem_type == 'security_issue' and 'security' in action:
                    effectiveness_score += 0.4
                
                # Penalize for difficulty
                effectiveness_score -= (difficulty_score - 1) * 0.1
                
                solution['effectiveness_score'] = max(0.1, min(1.0, effectiveness_score))
            
            # Sort by effectiveness score (descending)
            return sorted(solutions, key=lambda s: s.get('effectiveness_score', 0.5), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error ranking solutions: {e}")
            return solutions


# Global instance
intelligent_suggestion_feedback_system = IntelligentSuggestionFeedbackSystem()


if __name__ == "__main__":
    # Test the Intelligent Suggestion and Feedback System
    import time
    
    # Create system
    system = IntelligentSuggestionFeedbackSystem()
    
    # Mock diagnosis result
    mock_diagnosis = type('MockDiagnosis', (), {
        'missing_components': ['git', 'nodejs'],
        'outdated_components': ['python'],
        'conflicts': [{'id': 'conflict1', 'type': 'version', 'components': ['java', 'maven']}]
    })()
    
    # Generate suggestions
    suggestion_result = system.offer_intelligent_suggestions_based_on_diagnosis(mock_diagnosis)
    print(f"Suggestions generated: {suggestion_result.success}, count: {suggestion_result.suggestions_generated}")
    
    # Test component selection
    selection_criteria = {
        'scope': 'category',
        'categories': ['essential_runtimes'],
        'auto_resolve_dependencies': True
    }
    selection_result = system.allow_granular_component_selection(selection_criteria)
    print(f"Component selection: {selection_result.success}, selected: {selection_result.selected_count}")
    
    # Test feedback system
    feedback_data = [
        {
            'severity': 'error',
            'category': 'installation',
            'title': 'Installation Failed',
            'message': 'Failed to install Git',
            'component': 'git'
        },
        {
            'severity': 'warning',
            'category': 'dependency',
            'title': 'Missing Dependency',
            'message': 'Python dependency not found',
            'component': 'python'
        }
    ]
    feedback_result = system.implement_feedback_system_with_severity_categorization(feedback_data)
    print(f"Feedback system: {feedback_result.success}, messages: {feedback_result.messages_created}")
    
    # Get report
    report = system.get_suggestion_report()
    print(f"Report generated: {len(report)} sections")
    
    # Shutdown
    system.shutdown()
    print("Test completed successfully!")
