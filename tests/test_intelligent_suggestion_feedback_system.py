# -*- coding: utf-8 -*-
"""
Tests for Intelligent Suggestion and Feedback System
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the dependencies before importing
with patch.dict('sys.modules', {
    'core.unified_detection_engine': Mock(),
    'core.dependency_validation_system': Mock(),
    'core.modern_frontend_manager': Mock(),
    'core.security_manager': Mock(),
    'unified_detection_engine': Mock(),
    'dependency_validation_system': Mock(),
    'modern_frontend_manager': Mock(),
    'security_manager': Mock()
}):
    from core.intelligent_suggestion_feedback_system import (
        IntelligentSuggestionFeedbackSystem, SuggestionType, SuggestionPriority,
        FeedbackSeverity, SelectionScope, IntelligentSuggestion, FeedbackMessage,
        ComponentSelection, SuggestionResult, SelectionResult, FeedbackSystemResult
    )


class TestIntelligentSuggestionFeedbackSystem(unittest.TestCase):
    """Test cases for Intelligent Suggestion and Feedback System"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_detection_engine = Mock()
        self.mock_dependency_validator = Mock()
        self.mock_frontend_manager = Mock()
        self.mock_security_manager = Mock()
        
        # Mock dashboard state
        mock_dashboard_state = Mock()
        mock_dashboard_state.components = {
            'git': Mock(
                name='git',
                status=Mock(value='not_installed'),
                category=Mock(value='essential_runtimes'),
                priority=90,
                dependencies=[],
                conflicts=[]
            ),
            'python': Mock(
                name='python',
                status=Mock(value='outdated'),
                category=Mock(value='essential_runtimes'),
                priority=85,
                dependencies=[],
                conflicts=[]
            )
        }
        self.mock_frontend_manager.get_dashboard_state.return_value = mock_dashboard_state
        
        # Create system with mocked dependencies
        self.system = IntelligentSuggestionFeedbackSystem(
            detection_engine=self.mock_detection_engine,
            dependency_validator=self.mock_dependency_validator,
            frontend_manager=self.mock_frontend_manager,
            security_manager=self.mock_security_manager
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.system.shutdown()
    
    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system.active_suggestions)
        self.assertIsNotNone(self.system.active_feedback)
        self.assertIsNotNone(self.system.component_selections)
        self.assertEqual(len(self.system.active_suggestions), 0)
        self.assertEqual(len(self.system.active_feedback), 0)
    
    def test_offer_intelligent_suggestions_based_on_diagnosis(self):
        """Test intelligent suggestion generation"""
        # Create mock diagnosis result
        mock_diagnosis = Mock()
        mock_diagnosis.missing_components = ['git', 'nodejs']
        mock_diagnosis.outdated_components = ['python']
        mock_diagnosis.conflicts = [
            {
                'id': 'conflict1',
                'type': 'version',
                'components': ['java', 'maven']
            }
        ]
        
        # Generate suggestions
        result = self.system.offer_intelligent_suggestions_based_on_diagnosis(mock_diagnosis)
        
        # Verify result
        self.assertIsInstance(result, SuggestionResult)
        self.assertTrue(result.success)
        self.assertGreater(result.suggestions_generated, 0)
        self.assertIsInstance(result.suggestions, list)
        
        # Check that suggestions were stored
        self.assertGreater(len(self.system.active_suggestions), 0)
        
        # Verify suggestion types
        suggestion_types = [s.suggestion_type for s in result.suggestions]
        self.assertIn(SuggestionType.INSTALL_MISSING, suggestion_types)
        self.assertIn(SuggestionType.UPDATE_OUTDATED, suggestion_types)
        self.assertIn(SuggestionType.RESOLVE_CONFLICT, suggestion_types)
    
    def test_allow_granular_component_selection(self):
        """Test granular component selection"""
        # Test individual selection
        selection_criteria = {
            'scope': 'individual',
            'components': ['git', 'python'],
            'auto_resolve_dependencies': True
        }
        
        result = self.system.allow_granular_component_selection(selection_criteria)
        
        # Verify result
        self.assertIsInstance(result, SelectionResult)
        self.assertTrue(result.success)
        self.assertGreater(result.selected_count, 0)
        self.assertIsInstance(result.selection_data, ComponentSelection)
        
        # Check selection was stored
        self.assertGreater(len(self.system.component_selections), 0)
        
        # Test category selection
        category_criteria = {
            'scope': 'category',
            'categories': ['essential_runtimes'],
            'auto_resolve_dependencies': False
        }
        
        category_result = self.system.allow_granular_component_selection(category_criteria)
        self.assertTrue(category_result.success)
        self.assertGreater(category_result.selected_count, 0)
    
    def test_implement_feedback_system_with_severity_categorization(self):
        """Test feedback system implementation"""
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
            },
            {
                'severity': 'info',
                'category': 'general',
                'title': 'System Information',
                'message': 'System scan completed successfully'
            }
        ]
        
        result = self.system.implement_feedback_system_with_severity_categorization(feedback_data)
        
        # Verify result
        self.assertIsInstance(result, FeedbackSystemResult)
        self.assertTrue(result.success)
        self.assertEqual(result.messages_created, 3)
        self.assertGreater(result.solutions_provided, 0)
        self.assertEqual(len(result.feedback_data), 3)
        
        # Check feedback was stored
        self.assertEqual(len(self.system.active_feedback), 3)
        
        # Verify severity categorization
        severities = [f.severity for f in result.feedback_data]
        self.assertIn(FeedbackSeverity.ERROR, severities)
        self.assertIn(FeedbackSeverity.WARNING, severities)
        self.assertIn(FeedbackSeverity.INFO, severities)
        
        # Verify messages are sorted by severity (error first)
        self.assertEqual(result.feedback_data[0].severity, FeedbackSeverity.ERROR)
    
    def test_provide_actionable_solutions_for_problems(self):
        """Test actionable solution generation"""
        # Test missing dependency problem
        problem_context = {
            'type': 'missing_dependency',
            'severity': 'high',
            'components': ['git'],
            'description': 'Git is required but not installed'
        }
        
        solutions = self.system.provide_actionable_solutions_for_problems(problem_context)
        
        # Verify solutions
        self.assertIsInstance(solutions, list)
        self.assertGreater(len(solutions), 0)
        
        # Check solution structure
        for solution in solutions:
            self.assertIn('title', solution)
            self.assertIn('description', solution)
            self.assertIn('action', solution)
            self.assertIn('difficulty', solution)
        
        # Test version conflict problem
        conflict_context = {
            'type': 'version_conflict',
            'severity': 'medium',
            'components': ['java', 'maven'],
            'description': 'Version conflict between Java and Maven'
        }
        
        conflict_solutions = self.system.provide_actionable_solutions_for_problems(conflict_context)
        self.assertGreater(len(conflict_solutions), 0)
    
    def test_suggestion_application_and_dismissal(self):
        """Test suggestion application and dismissal"""
        # Create a test suggestion
        suggestion = IntelligentSuggestion(
            id="test_suggestion_123",
            suggestion_type=SuggestionType.INSTALL_MISSING,
            priority=SuggestionPriority.HIGH,
            title="Install Git",
            description="Install Git for version control",
            rationale="Git is essential for development",
            affected_components=["git"],
            actions=[{"type": "install", "component": "git"}],
            confidence_score=0.9
        )
        
        # Store suggestion
        self.system.active_suggestions[suggestion.id] = suggestion
        
        # Test application
        success = self.system.apply_suggestion(suggestion.id, user_confirmation=True)
        self.assertTrue(success)
        self.assertTrue(suggestion.applied)
        
        # Create another suggestion for dismissal test
        suggestion2 = IntelligentSuggestion(
            id="test_suggestion_456",
            suggestion_type=SuggestionType.UPDATE_OUTDATED,
            priority=SuggestionPriority.MEDIUM,
            title="Update Python",
            description="Update Python to latest version",
            rationale="Newer version available",
            affected_components=["python"],
            actions=[{"type": "update", "component": "python"}],
            confidence_score=0.8
        )
        
        self.system.active_suggestions[suggestion2.id] = suggestion2
        
        # Test dismissal
        dismiss_success = self.system.dismiss_suggestion(suggestion2.id, "Not needed right now")
        self.assertTrue(dismiss_success)
        self.assertTrue(suggestion2.dismissed)
        self.assertEqual(suggestion2.user_feedback, "Not needed right now")
    
    def test_feedback_acknowledgment(self):
        """Test feedback message acknowledgment"""
        # Create test feedback message
        feedback = FeedbackMessage(
            id="test_feedback_123",
            severity=FeedbackSeverity.WARNING,
            category="installation",
            title="Installation Warning",
            message="Component may need manual configuration",
            component="git",
            auto_dismissible=True,
            persistent=False
        )
        
        # Store feedback
        self.system.active_feedback[feedback.id] = feedback
        
        # Test acknowledgment
        success = self.system.acknowledge_feedback(feedback.id)
        self.assertTrue(success)
        self.assertTrue(feedback.acknowledged)
        
        # Check if auto-dismissible feedback was removed
        self.assertNotIn(feedback.id, self.system.active_feedback)
    
    def test_suggestion_ranking_and_filtering(self):
        """Test suggestion ranking and filtering"""
        suggestions = [
            IntelligentSuggestion(
                id="low_priority",
                suggestion_type=SuggestionType.CLEANUP_UNUSED,
                priority=SuggestionPriority.LOW,
                title="Cleanup",
                description="Clean unused components",
                rationale="Free space",
                affected_components=[],
                confidence_score=0.3
            ),
            IntelligentSuggestion(
                id="high_priority",
                suggestion_type=SuggestionType.SECURITY_FIX,
                priority=SuggestionPriority.CRITICAL,
                title="Security Fix",
                description="Fix security vulnerability",
                rationale="Security risk",
                affected_components=["vulnerable_component"],
                confidence_score=0.95
            ),
            IntelligentSuggestion(
                id="low_confidence",
                suggestion_type=SuggestionType.ALTERNATIVE_OPTION,
                priority=SuggestionPriority.MEDIUM,
                title="Alternative",
                description="Consider alternative",
                rationale="May be better",
                affected_components=[],
                confidence_score=0.2  # Below threshold
            )
        ]
        
        ranked = self.system._rank_and_filter_suggestions(suggestions)
        
        # Should filter out low confidence and rank by priority
        self.assertEqual(len(ranked), 2)  # Low confidence filtered out
        self.assertEqual(ranked[0].priority, SuggestionPriority.CRITICAL)  # Highest priority first
        self.assertEqual(ranked[1].priority, SuggestionPriority.LOW)
    
    def test_component_selection_criteria_application(self):
        """Test component selection criteria application"""
        # Mock available components
        from core.modern_frontend_manager import ComponentInfo, ComponentStatus, ComponentCategory
        
        available_components = {
            'git': ComponentInfo(
                name='git',
                display_name='Git',
                category=ComponentCategory.ESSENTIAL_RUNTIMES,
                status=ComponentStatus.NOT_INSTALLED,
                priority=90
            ),
            'vscode': ComponentInfo(
                name='vscode',
                display_name='VS Code',
                category=ComponentCategory.DEVELOPMENT_TOOLS,
                status=ComponentStatus.INSTALLED,
                priority=80
            ),
            'python': ComponentInfo(
                name='python',
                display_name='Python',
                category=ComponentCategory.ESSENTIAL_RUNTIMES,
                status=ComponentStatus.OUTDATED,
                priority=85
            )
        }
        
        # Test category selection
        criteria = {
            'scope': 'category',
            'categories': ['essential_runtimes']
        }
        
        selected = self.system._apply_selection_criteria(available_components, criteria)
        self.assertEqual(len(selected), 2)  # git and python
        self.assertIn('git', selected)
        self.assertIn('python', selected)
        self.assertNotIn('vscode', selected)
        
        # Test status filter
        criteria_with_filter = {
            'scope': 'category',
            'categories': ['essential_runtimes'],
            'status_filter': ['not_installed']
        }
        
        filtered_selected = self.system._apply_selection_criteria(available_components, criteria_with_filter)
        self.assertEqual(len(filtered_selected), 1)  # Only git
        self.assertIn('git', filtered_selected)
        self.assertNotIn('python', filtered_selected)
    
    def test_get_suggestion_report(self):
        """Test suggestion report generation"""
        # Add some test data
        suggestion = IntelligentSuggestion(
            id="test_suggestion",
            suggestion_type=SuggestionType.INSTALL_MISSING,
            priority=SuggestionPriority.HIGH,
            title="Test Suggestion",
            description="Test description",
            rationale="Test rationale",
            affected_components=["test_component"],
            confidence_score=0.8
        )
        self.system.active_suggestions[suggestion.id] = suggestion
        
        feedback = FeedbackMessage(
            id="test_feedback",
            severity=FeedbackSeverity.ERROR,
            category="test",
            title="Test Feedback",
            message="Test message"
        )
        self.system.active_feedback[feedback.id] = feedback
        
        # Generate report
        report = self.system.get_suggestion_report()
        
        # Verify report structure
        self.assertIn('summary', report)
        self.assertIn('suggestion_statistics', report)
        self.assertIn('feedback_statistics', report)
        self.assertIn('effectiveness_metrics', report)
        self.assertIn('active_suggestions', report)
        self.assertIn('active_feedback', report)
        
        # Verify summary data
        summary = report['summary']
        self.assertEqual(summary['active_suggestions'], 1)
        self.assertEqual(summary['active_feedback'], 1)
        
        # Verify active suggestions data
        active_suggestions = report['active_suggestions']
        self.assertEqual(len(active_suggestions), 1)
        self.assertEqual(active_suggestions[0]['id'], suggestion.id)
        self.assertEqual(active_suggestions[0]['type'], suggestion.suggestion_type.value)
    
    def test_ml_based_suggestions(self):
        """Test machine learning based suggestions"""
        # Set up usage patterns
        self.system.component_usage_patterns = {
            'git': 10,
            'python': 8,
            'vscode': 5
        }
        
        # Mock analysis
        analysis = {
            'missing_components': [],
            'outdated_components': [],
            'conflicts': []
        }
        
        # Generate ML suggestions
        ml_suggestions = self.system._generate_ml_based_suggestions(analysis)
        
        # Should generate some suggestions based on patterns
        self.assertIsInstance(ml_suggestions, list)
        # ML suggestions might be empty if patterns don't meet thresholds, which is fine
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid suggestion ID
        result = self.system.apply_suggestion("non_existent_id")
        self.assertFalse(result)
        
        # Test with invalid feedback ID
        result = self.system.acknowledge_feedback("non_existent_id")
        self.assertFalse(result)
        
        # Test with malformed feedback data
        malformed_feedback = [
            {
                # Missing required fields
                'message': 'Test message'
            }
        ]
        
        result = self.system.implement_feedback_system_with_severity_categorization(malformed_feedback)
        # Should handle gracefully and still succeed
        self.assertTrue(result.success)


class TestDataClasses(unittest.TestCase):
    """Test cases for data classes"""
    
    def test_intelligent_suggestion_creation(self):
        """Test IntelligentSuggestion creation"""
        suggestion = IntelligentSuggestion(
            id="test_123",
            suggestion_type=SuggestionType.INSTALL_MISSING,
            priority=SuggestionPriority.HIGH,
            title="Test Suggestion",
            description="Test description",
            rationale="Test rationale",
            affected_components=["component1", "component2"],
            confidence_score=0.85
        )
        
        self.assertEqual(suggestion.id, "test_123")
        self.assertEqual(suggestion.suggestion_type, SuggestionType.INSTALL_MISSING)
        self.assertEqual(suggestion.priority, SuggestionPriority.HIGH)
        self.assertEqual(len(suggestion.affected_components), 2)
        self.assertEqual(suggestion.confidence_score, 0.85)
        self.assertFalse(suggestion.applied)
        self.assertFalse(suggestion.dismissed)
    
    def test_feedback_message_creation(self):
        """Test FeedbackMessage creation"""
        feedback = FeedbackMessage(
            id="feedback_123",
            severity=FeedbackSeverity.WARNING,
            category="installation",
            title="Test Warning",
            message="This is a test warning message",
            component="test_component"
        )
        
        self.assertEqual(feedback.id, "feedback_123")
        self.assertEqual(feedback.severity, FeedbackSeverity.WARNING)
        self.assertEqual(feedback.category, "installation")
        self.assertEqual(feedback.component, "test_component")
        self.assertTrue(feedback.auto_dismissible)
        self.assertFalse(feedback.persistent)
        self.assertFalse(feedback.acknowledged)
    
    def test_component_selection_creation(self):
        """Test ComponentSelection creation"""
        selection = ComponentSelection(
            selection_id="selection_123",
            scope=SelectionScope.CATEGORY,
            auto_resolve_dependencies=True,
            include_optional_dependencies=False
        )
        
        self.assertEqual(selection.selection_id, "selection_123")
        self.assertEqual(selection.scope, SelectionScope.CATEGORY)
        self.assertTrue(selection.auto_resolve_dependencies)
        self.assertFalse(selection.include_optional_dependencies)
        self.assertEqual(len(selection.selected_components), 0)
        self.assertEqual(len(selection.excluded_components), 0)


if __name__ == '__main__':
    unittest.main()