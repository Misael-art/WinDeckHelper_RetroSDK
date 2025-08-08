"""
Unit tests for RequirementsConsistencyValidator.

Tests the requirements parsing and consistency validation functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from datetime import datetime
from pathlib import Path

from environment_dev_deep_evaluation.analysis.requirements_validator import RequirementsConsistencyValidator
from environment_dev_deep_evaluation.analysis.interfaces import (
    ConsistencyResult,
    ConsistencyIssue
)
from environment_dev_deep_evaluation.core.config import ConfigurationManager
from environment_dev_deep_evaluation.core.exceptions import ArchitectureAnalysisError


class TestRequirementsConsistencyValidator(unittest.TestCase):
    """Test cases for RequirementsConsistencyValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config_manager = Mock(spec=ConfigurationManager)
        self.mock_config = Mock()
        self.mock_config.log_level = "INFO"
        self.mock_config.debug_mode = True
        self.mock_config.workspace_root = "/test/workspace"
        self.mock_config_manager.get_config.return_value = self.mock_config
        
        self.validator = RequirementsConsistencyValidator(self.mock_config_manager)
    
    def test_initialization(self):
        """Test validator initialization."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator._component_name, "RequirementsConsistencyValidator")
        self.assertIsNotNone(self.validator._parsing_patterns)
        self.assertIsNotNone(self.validator._consistency_rules)
        self.assertIsNotNone(self.validator._validation_weights)
    
    def test_initialize_parsing_patterns(self):
        """Test initialization of parsing patterns."""
        patterns = self.validator._initialize_parsing_patterns()
        
        self.assertIn("requirement_headers", patterns)
        self.assertIn("user_story_patterns", patterns)
        self.assertIn("acceptance_criteria_patterns", patterns)
        self.assertIn("criteria_item_patterns", patterns)
        self.assertIn("cross_reference_patterns", patterns)
        
        # Check that patterns are lists of regex strings
        for pattern_list in patterns.values():
            self.assertIsInstance(pattern_list, list)
            self.assertTrue(all(isinstance(pattern, str) for pattern in pattern_list))
    
    def test_initialize_consistency_rules(self):
        """Test initialization of consistency rules."""
        rules = self.validator._initialize_consistency_rules()
        
        expected_rules = [
            "duplicate_id_check",
            "conflicting_criteria_check",
            "missing_cross_references_check",
            "inconsistent_terminology_check",
            "structural_consistency_check",
            "completeness_check"
        ]
        
        for rule in expected_rules:
            self.assertIn(rule, rules)
            self.assertIn("enabled", rules[rule])
            self.assertIn("severity", rules[rule])
            self.assertIn("description", rules[rule])
    
    def test_detect_document_language(self):
        """Test document language detection."""
        # Portuguese content
        portuguese_content = "### Requisito 1: Como usuário, eu quero testar, para que eu possa verificar"
        self.assertEqual(self.validator._detect_document_language(portuguese_content), "Portuguese")
        
        # English content
        english_content = "### Requirement 1: As a user, I want to test, so that I can verify"
        self.assertEqual(self.validator._detect_document_language(english_content), "English")
        
        # Unknown content
        unknown_content = "Some random text without keywords"
        self.assertEqual(self.validator._detect_document_language(unknown_content), "Unknown")
    
    def test_extract_document_title(self):
        """Test document title extraction."""
        content_with_title = "# Requirements Document\n\nThis is the content"
        title = self.validator._extract_document_title(content_with_title)
        self.assertEqual(title, "Requirements Document")
        
        content_without_title = "This is content without a title"
        title = self.validator._extract_document_title(content_without_title)
        self.assertIsNone(title)
    
    def test_match_requirement_header(self):
        """Test requirement header matching."""
        # Test Portuguese format
        portuguese_header = "### Requisito 1: Test Requirement"
        match = self.validator._match_requirement_header(portuguese_header)
        self.assertIsNotNone(match)
        self.assertEqual(match["type"], "Requisito")
        self.assertEqual(match["id"], "1")
        self.assertEqual(match["title"], "Test Requirement")
        
        # Test English format
        english_header = "### Requirement 2.1: Another Test"
        match = self.validator._match_requirement_header(english_header)
        self.assertIsNotNone(match)
        self.assertEqual(match["type"], "Requirement")
        self.assertEqual(match["id"], "2.1")
        self.assertEqual(match["title"], "Another Test")
        
        # Test non-matching line
        non_header = "This is not a header"
        match = self.validator._match_requirement_header(non_header)
        self.assertIsNone(match)
    
    def test_match_user_story(self):
        """Test user story matching."""
        # Test English format
        english_story = "**User Story:** As a user, I want to test, so that I can verify"
        match = self.validator._match_user_story(english_story)
        self.assertIsNotNone(match)
        self.assertIn("As a user", match)
        
        # Test Portuguese format
        portuguese_story = "Como usuário, eu quero testar, para que eu possa verificar"
        match = self.validator._match_user_story(portuguese_story)
        self.assertIsNotNone(match)
        self.assertIn("Como usuário", match)
        
        # Test non-matching line
        non_story = "This is not a user story"
        match = self.validator._match_user_story(non_story)
        self.assertIsNone(match)
    
    def test_is_acceptance_criteria_header(self):
        """Test acceptance criteria header detection."""
        # Test English
        self.assertTrue(self.validator._is_acceptance_criteria_header("#### Acceptance Criteria"))
        self.assertTrue(self.validator._is_acceptance_criteria_header("### Acceptance Criteria"))
        
        # Test Portuguese
        self.assertTrue(self.validator._is_acceptance_criteria_header("#### Critérios de Aceitação"))
        
        # Test non-matching
        self.assertFalse(self.validator._is_acceptance_criteria_header("Some other header"))
    
    def test_match_criteria_item(self):
        """Test acceptance criteria item matching."""
        # Test WHEN-THEN format
        when_then = "1. WHEN user clicks button THEN system SHALL respond"
        match = self.validator._match_criteria_item(when_then)
        self.assertIsNotNone(match)
        self.assertIn("condition", match)
        self.assertIn("result", match)
        self.assertIn("full_text", match)
        
        # Test IF-THEN format
        if_then = "- IF condition is met THEN system SHALL validate"
        match = self.validator._match_criteria_item(if_then)
        self.assertIsNotNone(match)
        
        # Test non-matching
        non_criteria = "This is not a criteria item"
        match = self.validator._match_criteria_item(non_criteria)
        self.assertIsNone(match)
    
    def test_extract_line_cross_references(self):
        """Test cross-reference extraction from lines."""
        # Test with Requirements format
        line_with_refs = "_Requirements: 1.1, 1.2, 2.3_"
        refs = self.validator._extract_line_cross_references(line_with_refs)
        self.assertEqual(set(refs), {"1.1", "1.2", "2.3"})
        
        # Test with Portuguese format
        portuguese_refs = "Requisitos: 1, 2, 3"
        refs = self.validator._extract_line_cross_references(portuguese_refs)
        self.assertEqual(set(refs), {"1", "2", "3"})
        
        # Test line without references
        no_refs = "This line has no references"
        refs = self.validator._extract_line_cross_references(no_refs)
        self.assertEqual(refs, [])
    
    def test_analyze_id_format(self):
        """Test requirement ID format analysis."""
        # Test numeric format
        self.assertEqual(self.validator._analyze_id_format("Requisito 1"), "numeric")
        self.assertEqual(self.validator._analyze_id_format("Requirement 5"), "numeric")
        
        # Test decimal format
        self.assertEqual(self.validator._analyze_id_format("Requisito 1.2"), "decimal")
        self.assertEqual(self.validator._analyze_id_format("Requirement 2.1"), "decimal")
        
        # Test alphanumeric format
        self.assertEqual(self.validator._analyze_id_format("Requirement REQ1"), "alphanumeric")
        
        # Test custom format
        self.assertEqual(self.validator._analyze_id_format("Requirement ABC-123-XYZ"), "custom")
    
    def test_parse_requirements_sections(self):
        """Test parsing requirements sections."""
        requirements_content = """
# Requirements Document

### Requisito 1: Test Requirement

**User Story:** Como usuário, eu quero testar, para que eu possa verificar

#### Acceptance Criteria

1. WHEN test is executed THEN system SHALL respond
2. IF condition is met THEN system SHALL validate

_Requirements: 2.1_

### Requisito 2: Another Requirement

**User Story:** As a user, I want to verify, so that I can confirm

#### Acceptance Criteria

1. WHEN verification starts THEN system SHALL check
"""
        
        # Initialize validator
        self.validator.initialize()
        
        requirements = self.validator._parse_requirements_sections(requirements_content)
        
        self.assertEqual(len(requirements), 2)
        
        # Check first requirement
        req1 = requirements[0]
        self.assertEqual(req1["id"], "1")
        self.assertEqual(req1["title"], "Test Requirement")
        self.assertIn("Como usuário", req1["user_story"])
        self.assertEqual(len(req1["acceptance_criteria"]), 2)
        self.assertIn("2.1", req1["cross_references"])
        
        # Check second requirement
        req2 = requirements[1]
        self.assertEqual(req2["id"], "2")
        self.assertEqual(req2["title"], "Another Requirement")
        self.assertIn("As a user", req2["user_story"])
        self.assertEqual(len(req2["acceptance_criteria"]), 1)
    
    def test_analyze_requirement_structure(self):
        """Test requirement structure analysis."""
        requirements = [
            {
                "id": "1",
                "title": "Test 1",
                "user_story": "As a user, I want to test",
                "acceptance_criteria": [{"condition": "WHEN test", "result": "THEN pass"}],
                "cross_references": ["2"]
            },
            {
                "id": "2",
                "title": "Test 2",
                "user_story": "",  # Missing user story
                "acceptance_criteria": [],  # Missing criteria
                "cross_references": []
            }
        ]
        
        analysis = self.validator._analyze_requirement_structure(requirements)
        
        self.assertEqual(analysis["total_requirements"], 2)
        self.assertEqual(analysis["requirements_with_user_stories"], 1)
        self.assertEqual(analysis["requirements_with_acceptance_criteria"], 1)
        self.assertEqual(analysis["requirements_with_cross_references"], 1)
        self.assertTrue(len(analysis["structural_issues"]) > 0)  # Should find missing content
    
    def test_calculate_text_similarity(self):
        """Test text similarity calculation."""
        # Identical texts
        similarity = self.validator._calculate_text_similarity("test text", "test text")
        self.assertEqual(similarity, 1.0)
        
        # Completely different texts
        similarity = self.validator._calculate_text_similarity("hello world", "goodbye universe")
        self.assertEqual(similarity, 0.0)
        
        # Partially similar texts
        similarity = self.validator._calculate_text_similarity("hello world test", "hello universe test")
        self.assertGreater(similarity, 0.0)
        self.assertLess(similarity, 1.0)
        
        # Empty texts
        similarity = self.validator._calculate_text_similarity("", "test")
        self.assertEqual(similarity, 0.0)
    
    def test_are_criteria_contradictory(self):
        """Test criteria contradiction detection."""
        # Contradictory criteria
        criteria1 = {"full_text": "system SHALL allow access"}
        criteria2 = {"full_text": "system SHALL NOT allow access"}
        self.assertTrue(self.validator._are_criteria_contradictory(criteria1, criteria2))
        
        # Non-contradictory criteria
        criteria3 = {"full_text": "system SHALL validate input"}
        criteria4 = {"full_text": "system SHALL process data"}
        self.assertFalse(self.validator._are_criteria_contradictory(criteria3, criteria4))
    
    def test_check_duplicate_requirement_ids(self):
        """Test duplicate requirement ID checking."""
        parsed_requirements = {
            "/test/req1.md": {
                "requirements": [
                    {"id": "1", "title": "Test 1", "line_number": 5}
                ]
            },
            "/test/req2.md": {
                "requirements": [
                    {"id": "1", "title": "Test 1 Duplicate", "line_number": 3}  # Duplicate ID
                ]
            }
        }
        
        issues = self.validator._check_duplicate_requirement_ids(parsed_requirements, 1)
        
        self.assertEqual(len(issues), 1)
        self.assertIn("Duplicate requirement ID", issues[0].description)
        self.assertEqual(len(issues[0].conflicting_documents), 2)
    
    def test_check_requirements_completeness(self):
        """Test requirements completeness checking."""
        parsed_requirements = {
            "/test/req.md": {
                "requirements": [
                    {
                        "id": "1",
                        "title": "Complete Requirement",
                        "user_story": "As a user, I want to test",
                        "acceptance_criteria": [{"condition": "WHEN", "result": "THEN"}]
                    },
                    {
                        "id": "2",
                        "title": "Incomplete Requirement",
                        "user_story": "",  # Missing
                        "acceptance_criteria": []  # Missing
                    }
                ]
            }
        }
        
        issues = self.validator._check_requirements_completeness(parsed_requirements, 1)
        
        self.assertEqual(len(issues), 2)  # Missing user story + missing criteria
        descriptions = [issue.description for issue in issues]
        self.assertTrue(any("missing user story" in desc for desc in descriptions))
        self.assertTrue(any("missing acceptance criteria" in desc for desc in descriptions))
    
    def test_calculate_comprehensive_consistency_score(self):
        """Test comprehensive consistency score calculation."""
        # No issues - perfect score
        score = self.validator._calculate_comprehensive_consistency_score([], 10)
        self.assertEqual(score, 1.0)
        
        # Some issues
        issues = [
            ConsistencyIssue("1", "High issue", [], [], "High", ""),
            ConsistencyIssue("2", "Medium issue", [], [], "Medium", ""),
            ConsistencyIssue("3", "Low issue", [], [], "Low", "")
        ]
        score = self.validator._calculate_comprehensive_consistency_score(issues, 10)
        self.assertLess(score, 1.0)
        self.assertGreaterEqual(score, 0.0)
    
    def test_categorize_issue_type(self):
        """Test issue type categorization."""
        self.assertEqual(self.validator._categorize_issue_type("Duplicate requirement ID found"), "duplicate_ids")
        self.assertEqual(self.validator._categorize_issue_type("Missing user story"), "missing_content")
        self.assertEqual(self.validator._categorize_issue_type("Inconsistent terminology usage"), "terminology")
        self.assertEqual(self.validator._categorize_issue_type("Broken cross-reference"), "cross_references")
        self.assertEqual(self.validator._categorize_issue_type("Conflicting acceptance criteria"), "conflicts")
        self.assertEqual(self.validator._categorize_issue_type("Some other issue"), "other")
    
    @patch('os.path.exists')
    @patch('os.path.getmtime')
    def test_parse_requirements_document_integration(self, mock_getmtime, mock_exists):
        """Test the complete parse_requirements_document method."""
        requirements_content = """
# Test Requirements Document

### Requisito 1: Test Requirement

**User Story:** Como usuário, eu quero testar, para que eu possa verificar

#### Acceptance Criteria

1. WHEN test is executed THEN system SHALL respond
2. IF condition is met THEN system SHALL validate

_Requirements: 2.1_
"""
        
        mock_exists.return_value = True
        mock_getmtime.return_value = 1640995200  # Mock timestamp
        
        with patch('builtins.open', mock_open(read_data=requirements_content)):
            # Initialize validator
            self.validator.initialize()
            
            # Test parsing
            result = self.validator.parse_requirements_document("/test/requirements.md")
            
            self.assertIn("file_path", result)
            self.assertIn("metadata", result)
            self.assertIn("requirements", result)
            self.assertIn("cross_references", result)
            self.assertIn("structure_analysis", result)
            
            # Check metadata
            metadata = result["metadata"]
            self.assertEqual(metadata["file_name"], "requirements.md")
            self.assertEqual(metadata["language"], "Portuguese")
            
            # Check requirements
            requirements = result["requirements"]
            self.assertEqual(len(requirements), 1)
            self.assertEqual(requirements[0]["id"], "1")
            self.assertEqual(requirements[0]["title"], "Test Requirement")
    
    def test_validate_requirements_consistency_integration(self):
        """Test the complete validate_requirements_consistency method."""
        requirements_content = """
### Requisito 1: Test

**User Story:** Como usuário, eu quero testar

#### Acceptance Criteria
1. WHEN test THEN pass
"""
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getmtime', return_value=1640995200):
                with patch('builtins.open', mock_open(read_data=requirements_content)):
                    # Initialize validator
                    self.validator.initialize()
                    
                    # Test consistency validation
                    result = self.validator.validate_requirements_consistency(["/test/req.md"])
                    
                    self.assertIsInstance(result, ConsistencyResult)
                    self.assertIsInstance(result.is_consistent, bool)
                    self.assertIsInstance(result.total_requirements_checked, int)
                    self.assertIsInstance(result.consistency_issues, list)
                    self.assertIsInstance(result.consistency_score, float)
                    self.assertIsInstance(result.recommendations, list)
    
    def test_generate_consistency_report_integration(self):
        """Test the complete generate_consistency_report method."""
        # Create a sample consistency result
        consistency_result = ConsistencyResult(
            is_consistent=False,
            total_requirements_checked=5,
            consistency_issues=[
                ConsistencyIssue(
                    issue_id="001",
                    description="Duplicate requirement ID",
                    conflicting_documents=["/test/req1.md", "/test/req2.md"],
                    conflicting_requirements=["1"],
                    severity="High",
                    resolution_suggestion="Use unique IDs"
                )
            ],
            consistency_score=0.8,
            recommendations=["Fix duplicate IDs", "Implement review process"]
        )
        
        # Initialize validator
        self.validator.initialize()
        
        # Test report generation
        report = self.validator.generate_consistency_report(consistency_result)
        
        self.assertIsInstance(report, str)
        self.assertIn("Requirements Consistency Report", report)
        self.assertIn("Executive Summary", report)
        self.assertIn("Detailed Issues Analysis", report)
        self.assertIn("Consistency Metrics", report)
        self.assertIn("Recommendations", report)
        self.assertIn("Action Plan", report)
        self.assertIn("Duplicate requirement ID", report)


if __name__ == '__main__':
    unittest.main()