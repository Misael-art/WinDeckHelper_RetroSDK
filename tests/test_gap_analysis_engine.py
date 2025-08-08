"""
Unit tests for GapAnalysisEngine.

Tests the gap identification, criticality prioritization, and documentation functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from datetime import datetime
from pathlib import Path

from environment_dev_deep_evaluation.analysis.gap_analysis_engine import GapAnalysisEngine
from environment_dev_deep_evaluation.analysis.interfaces import (
    GapAnalysisReport,
    ConsistencyResult,
    CriticalGap,
    ConsistencyIssue,
    CriticalityLevel
)
from environment_dev_deep_evaluation.core.config import ConfigurationManager
from environment_dev_deep_evaluation.core.base import OperationResult
from environment_dev_deep_evaluation.core.exceptions import ArchitectureAnalysisError


class TestGapAnalysisEngine(unittest.TestCase):
    """Test cases for GapAnalysisEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config_manager = Mock(spec=ConfigurationManager)
        self.mock_config = Mock()
        self.mock_config.log_level = "INFO"
        self.mock_config.debug_mode = True
        self.mock_config.workspace_root = "/test/workspace"
        self.mock_config_manager.get_config.return_value = self.mock_config
        
        self.engine = GapAnalysisEngine(self.mock_config_manager)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine._component_name, "GapAnalysisEngine")
        self.assertIsNotNone(self.engine._gap_detection_rules)
        self.assertIsNotNone(self.engine._criticality_weights)
        self.assertIsNotNone(self.engine._documentation_templates)
    
    def test_initialize_gap_detection_rules(self):
        """Test initialization of gap detection rules."""
        rules = self.engine._initialize_gap_detection_rules()
        
        self.assertIn("missing_implementation_patterns", rules)
        self.assertIn("security_gap_patterns", rules)
        self.assertIn("stability_gap_patterns", rules)
        self.assertIn("functionality_gap_patterns", rules)
        
        # Check that patterns are lists of regex strings
        for pattern_list in rules.values():
            self.assertIsInstance(pattern_list, list)
            self.assertTrue(all(isinstance(pattern, str) for pattern in pattern_list))
    
    def test_initialize_criticality_weights(self):
        """Test initialization of criticality weights."""
        weights = self.engine._initialize_criticality_weights()
        
        self.assertEqual(weights[CriticalityLevel.SECURITY], 1.0)
        self.assertEqual(weights[CriticalityLevel.STABILITY], 0.8)
        self.assertEqual(weights[CriticalityLevel.FUNCTIONALITY], 0.6)
        self.assertEqual(weights[CriticalityLevel.UX], 0.4)
    
    def test_determine_gap_criticality(self):
        """Test determining gap criticality."""
        # Security gaps
        self.assertEqual(
            self.engine._determine_gap_criticality("security_gap_patterns", "password = 'test'"),
            CriticalityLevel.SECURITY
        )
        
        # Stability gaps
        self.assertEqual(
            self.engine._determine_gap_criticality("stability_gap_patterns", "# HACK: temporary fix"),
            CriticalityLevel.STABILITY
        )
        
        # Functionality gaps
        self.assertEqual(
            self.engine._determine_gap_criticality("functionality_gap_patterns", "def test(): pass"),
            CriticalityLevel.FUNCTIONALITY
        )
        
        # Default (UX)
        self.assertEqual(
            self.engine._determine_gap_criticality("unknown_pattern", "some content"),
            CriticalityLevel.UX
        )
    
    def test_assess_gap_impact(self):
        """Test assessing gap impact."""
        # Missing implementation
        impact = self.engine._assess_gap_impact("missing_implementation_patterns", "TODO: implement")
        self.assertIn("Feature incomplete", impact)
        
        # Security gap
        impact = self.engine._assess_gap_impact("security_gap_patterns", "password = 'test'")
        self.assertIn("Security vulnerability", impact)
        
        # Stability gap
        impact = self.engine._assess_gap_impact("stability_gap_patterns", "# HACK")
        self.assertIn("System instability", impact)
        
        # Functionality gap
        impact = self.engine._assess_gap_impact("functionality_gap_patterns", "def test(): pass")
        self.assertIn("Reduced functionality", impact)
    
    def test_recommend_gap_action(self):
        """Test recommending gap actions."""
        # Missing implementation
        action = self.engine._recommend_gap_action("missing_implementation_patterns", "TODO")
        self.assertIn("Complete implementation", action)
        
        # Security gap
        action = self.engine._recommend_gap_action("security_gap_patterns", "password")
        self.assertIn("security measures", action)
        
        # Stability gap
        action = self.engine._recommend_gap_action("stability_gap_patterns", "HACK")
        self.assertIn("robust implementation", action)
        
        # Functionality gap
        action = self.engine._recommend_gap_action("functionality_gap_patterns", "pass")
        self.assertIn("complete functionality", action)
    
    def test_estimate_gap_effort(self):
        """Test estimating gap effort."""
        # Missing implementation - medium effort
        effort = self.engine._estimate_gap_effort("missing_implementation_patterns", "TODO")
        self.assertIn("Medium", effort)
        
        # Security gap - high effort
        effort = self.engine._estimate_gap_effort("security_gap_patterns", "password")
        self.assertIn("High", effort)
        
        # Stability gap - medium effort
        effort = self.engine._estimate_gap_effort("stability_gap_patterns", "HACK")
        self.assertIn("Medium", effort)
        
        # Functionality gap - low effort
        effort = self.engine._estimate_gap_effort("functionality_gap_patterns", "pass")
        self.assertIn("Low", effort)
    
    @patch('pathlib.Path.rglob')
    @patch('builtins.open', new_callable=mock_open, read_data="def test_function():\n    # TODO: implement this\n    pass")
    def test_detect_gaps_in_file(self, mock_file, mock_rglob):
        """Test detecting gaps in a single file."""
        file_path = Path("/test/workspace/test.py")
        content = "def test_function():\n    # TODO: implement this\n    pass"
        
        # Initialize engine
        self.engine.initialize()
        
        gaps = self.engine._detect_gaps_in_file(file_path, content)
        
        self.assertIsInstance(gaps, list)
        if gaps:  # If gaps are found
            gap = gaps[0]
            self.assertIsInstance(gap, CriticalGap)
            self.assertIn("TODO", gap.description)
    
    @patch('pathlib.Path.rglob')
    @patch('builtins.open', new_callable=mock_open, read_data="def test_function():\n    pass")
    def test_check_missing_docstrings(self, mock_file, mock_rglob):
        """Test checking for missing docstrings."""
        file_path = Path("/test/workspace/test.py")
        content = "def test_function():\n    pass\n\nclass TestClass:\n    pass"
        
        # Initialize engine
        self.engine.initialize()
        
        gaps = self.engine._check_missing_docstrings(file_path, content)
        
        self.assertIsInstance(gaps, list)
        # Should find gaps for both function and class without docstrings
        self.assertEqual(len(gaps), 2)
        
        # Check that gaps are for missing docstrings
        descriptions = [gap.description for gap in gaps]
        self.assertTrue(any("Missing docstring for function" in desc for desc in descriptions))
        self.assertTrue(any("Missing docstring for class" in desc for desc in descriptions))
    
    def test_calculate_gaps_by_criticality(self):
        """Test calculating gap counts by criticality."""
        gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("2", "Stability gap", CriticalityLevel.STABILITY, [], "", "", ""),
            CriticalGap("3", "Another security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("4", "UX gap", CriticalityLevel.UX, [], "", "", "")
        ]
        
        counts = self.engine._calculate_gaps_by_criticality(gaps)
        
        self.assertEqual(counts[CriticalityLevel.SECURITY], 2)
        self.assertEqual(counts[CriticalityLevel.STABILITY], 1)
        self.assertEqual(counts[CriticalityLevel.FUNCTIONALITY], 0)
        self.assertEqual(counts[CriticalityLevel.UX], 1)
    
    def test_generate_recommendations(self):
        """Test generating recommendations."""
        gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("2", "Stability gap", CriticalityLevel.STABILITY, [], "", "", ""),
            CriticalGap("3", "Functionality gap", CriticalityLevel.FUNCTIONALITY, [], "", "", "")
        ]
        
        recommendations = self.engine._generate_recommendations(gaps)
        
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        # Check that recommendations address different criticality levels
        rec_text = " ".join(recommendations)
        self.assertIn("security", rec_text.lower())
        self.assertIn("stability", rec_text.lower())
        self.assertIn("functionality", rec_text.lower())
    
    def test_generate_next_steps(self):
        """Test generating next steps."""
        gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("2", "Stability gap", CriticalityLevel.STABILITY, [], "", "", "")
        ]
        
        next_steps = self.engine._generate_next_steps(gaps)
        
        self.assertIsInstance(next_steps, list)
        self.assertTrue(len(next_steps) > 0)
        
        # Check that next steps prioritize security and stability
        steps_text = " ".join(next_steps)
        self.assertIn("IMMEDIATE", steps_text)
        self.assertIn("security", steps_text.lower())
        self.assertIn("Phase", steps_text)
    
    def test_parse_requirements_document(self):
        """Test parsing requirements document."""
        requirements_content = """
# Requirements Document

### Requisito 1: Test Requirement

**User Story:** As a user, I want to test, so that I can verify functionality

#### Acceptance Criteria

1. WHEN test is run THEN system SHALL respond
2. IF condition is met THEN system SHALL validate

### Requisito 2: Another Requirement

**User Story:** As a developer, I want to code, so that I can implement features

#### Acceptance Criteria

1. WHEN code is written THEN system SHALL compile
"""
        
        with patch('builtins.open', mock_open(read_data=requirements_content)):
            result = self.engine._parse_requirements_document("/test/requirements.md")
            
            self.assertIn("requirements", result)
            self.assertEqual(len(result["requirements"]), 2)
            
            # Check first requirement
            req1 = result["requirements"][0]
            self.assertIn("Requisito 1", req1["id"])
            self.assertIn("As a user", req1["user_story"])
            self.assertEqual(len(req1["acceptance_criteria"]), 2)
    
    def test_check_requirements_consistency(self):
        """Test checking requirements consistency."""
        parsed_requirements = {
            "/test/req1.md": {
                "requirements": [
                    {
                        "id": "### Requisito 1: Test",
                        "user_story": "As a user, I want to test",
                        "acceptance_criteria": ["WHEN test THEN pass"]
                    }
                ]
            },
            "/test/req2.md": {
                "requirements": [
                    {
                        "id": "### Requisito 1: Test",  # Duplicate ID
                        "user_story": "As a user, I want to test differently",
                        "acceptance_criteria": ["WHEN test THEN fail"]
                    }
                ]
            }
        }
        
        issues = self.engine._check_requirements_consistency(parsed_requirements)
        
        self.assertIsInstance(issues, list)
        self.assertTrue(len(issues) > 0)
        
        # Should find duplicate requirement ID
        issue_descriptions = [issue.description for issue in issues]
        self.assertTrue(any("Duplicate requirement ID" in desc for desc in issue_descriptions))
    
    def test_calculate_consistency_score(self):
        """Test calculating consistency score."""
        # No issues - perfect score
        score = self.engine._calculate_consistency_score([], 10)
        self.assertEqual(score, 1.0)
        
        # Some high severity issues
        issues = [
            ConsistencyIssue("1", "High issue", [], [], "High", ""),
            ConsistencyIssue("2", "Medium issue", [], [], "Medium", "")
        ]
        score = self.engine._calculate_consistency_score(issues, 10)
        self.assertLess(score, 1.0)
        self.assertGreaterEqual(score, 0.0)
    
    def test_generate_consistency_recommendations(self):
        """Test generating consistency recommendations."""
        issues = [
            ConsistencyIssue("1", "High issue", [], [], "High", ""),
            ConsistencyIssue("2", "Medium issue", [], [], "Medium", "")
        ]
        
        recommendations = self.engine._generate_consistency_recommendations(issues)
        
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)
        
        rec_text = " ".join(recommendations)
        self.assertIn("high-severity", rec_text.lower())
        self.assertIn("medium-severity", rec_text.lower())
    
    def test_group_gaps_by_implementation_phase(self):
        """Test grouping gaps by implementation phase."""
        gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("2", "Stability gap", CriticalityLevel.STABILITY, [], "", "", ""),
            CriticalGap("3", "Functionality gap", CriticalityLevel.FUNCTIONALITY, [], "", "", ""),
            CriticalGap("4", "UX gap", CriticalityLevel.UX, [], "", "", "")
        ]
        
        phases = self.engine._group_gaps_by_implementation_phase(gaps)
        
        self.assertIn("Phase 1 - Critical Security & Stability", phases)
        self.assertIn("Phase 2 - Core Functionality", phases)
        self.assertIn("Phase 3 - Documentation & UX", phases)
        
        # Check that gaps are properly categorized
        self.assertEqual(len(phases["Phase 1 - Critical Security & Stability"]), 2)
        self.assertEqual(len(phases["Phase 2 - Core Functionality"]), 1)
        self.assertEqual(len(phases["Phase 3 - Documentation & UX"]), 1)
    
    def test_calculate_phase_effort(self):
        """Test calculating phase effort."""
        gaps = [
            CriticalGap("1", "Gap 1", CriticalityLevel.SECURITY, [], "", "", "Low (1 day)"),
            CriticalGap("2", "Gap 2", CriticalityLevel.SECURITY, [], "", "", "Medium (3 days)"),
            CriticalGap("3", "Gap 3", CriticalityLevel.SECURITY, [], "", "", "High (7 days)")
        ]
        
        effort = self.engine._calculate_phase_effort(gaps)
        
        self.assertIsInstance(effort, str)
        self.assertIn("weeks", effort)
        self.assertIn("days", effort)
    
    def test_calculate_implementation_timeline(self):
        """Test calculating implementation timeline."""
        phases = {
            "Phase 1": [
                CriticalGap("1", "Gap 1", CriticalityLevel.SECURITY, [], "", "", "Medium (3 days)")
            ],
            "Phase 2": [
                CriticalGap("2", "Gap 2", CriticalityLevel.FUNCTIONALITY, [], "", "", "Low (1 day)")
            ]
        }
        
        timeline = self.engine._calculate_implementation_timeline(phases)
        
        self.assertIn("total_weeks", timeline)
        self.assertIn("phase_timelines", timeline)
        self.assertIn("estimated_completion", timeline)
        self.assertIsInstance(timeline["total_weeks"], int)
    
    @patch.object(GapAnalysisEngine, '_identify_all_gaps')
    def test_generate_gap_analysis_report_integration(self, mock_identify_gaps):
        """Test the complete generate_gap_analysis_report method."""
        # Setup mock gaps
        mock_gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", ""),
            CriticalGap("2", "Functionality gap", CriticalityLevel.FUNCTIONALITY, [], "", "", "")
        ]
        mock_identify_gaps.return_value = mock_gaps
        
        # Initialize engine
        self.engine.initialize()
        
        # Test report generation
        report = self.engine.generate_gap_analysis_report()
        
        self.assertIsInstance(report, GapAnalysisReport)
        self.assertEqual(report.total_gaps_identified, 2)
        self.assertIsInstance(report.gaps_by_criticality, dict)
        self.assertIsInstance(report.detailed_gaps, list)
        self.assertIsInstance(report.recommendations, list)
        self.assertIsInstance(report.next_steps, list)
    
    def test_validate_requirements_consistency_integration(self):
        """Test the complete validate_requirements_consistency method."""
        requirements_content = """
### Requisito 1: Test

**User Story:** As a user, I want to test

#### Acceptance Criteria
1. WHEN test THEN pass
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=requirements_content)):
                # Initialize engine
                self.engine.initialize()
                
                # Test consistency validation
                result = self.engine.validate_requirements_consistency(["/test/req.md"])
                
                self.assertIsInstance(result, ConsistencyResult)
                self.assertIsInstance(result.is_consistent, bool)
                self.assertIsInstance(result.total_requirements_checked, int)
                self.assertIsInstance(result.consistency_issues, list)
                self.assertIsInstance(result.consistency_score, float)
                self.assertIsInstance(result.recommendations, list)
    
    def test_document_architectural_differences_integration(self):
        """Test the complete document_architectural_differences method."""
        current_arch = {
            "layers": {"core": [], "analysis": []},
            "components": {
                "test.py": {"classes": ["TestClass"]}
            }
        }
        
        proposed_arch = {
            "layers": {"core": [], "analysis": [], "detection": []},
            "components": {"TestClass": [], "MissingClass": []},
            "interfaces": {"TestInterface": []}
        }
        
        with patch.object(self.engine, '_save_architectural_differences_documentation', return_value="/test/doc.md"):
            # Initialize engine
            self.engine.initialize()
            
            # Test documentation
            result = self.engine.document_architectural_differences(current_arch, proposed_arch)
            
            self.assertIsInstance(result, OperationResult)
            self.assertTrue(result.success)
            self.assertIn("documentation_path", result.data)
    
    def test_generate_prioritized_action_plan_integration(self):
        """Test the complete generate_prioritized_action_plan method."""
        gaps = [
            CriticalGap("1", "Security gap", CriticalityLevel.SECURITY, [], "", "", "High (7 days)"),
            CriticalGap("2", "Functionality gap", CriticalityLevel.FUNCTIONALITY, [], "", "", "Medium (3 days)")
        ]
        
        with patch.object(self.engine, '_save_action_plan_document', return_value="/test/plan.md"):
            # Initialize engine
            self.engine.initialize()
            
            # Test action plan generation
            result = self.engine.generate_prioritized_action_plan(gaps)
            
            self.assertIsInstance(result, OperationResult)
            self.assertTrue(result.success)
            self.assertIn("action_plan_path", result.data)
            self.assertIn("total_phases", result.data)
            self.assertIn("estimated_timeline", result.data)


if __name__ == '__main__':
    unittest.main()