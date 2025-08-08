"""
Unit tests for ArchitectureAnalysisEngine.

Tests the architecture mapping and comparison functionality.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from datetime import datetime
from pathlib import Path

from environment_dev_deep_evaluation.analysis.architecture_engine import ArchitectureAnalysisEngine
from environment_dev_deep_evaluation.analysis.interfaces import (
    ArchitectureAnalysis,
    ComparisonResult,
    CriticalGap,
    LostFunctionality,
    CriticalityLevel
)
from environment_dev_deep_evaluation.core.config import ConfigurationManager
from environment_dev_deep_evaluation.core.exceptions import ArchitectureAnalysisError


class TestArchitectureAnalysisEngine(unittest.TestCase):
    """Test cases for ArchitectureAnalysisEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config_manager = Mock(spec=ConfigurationManager)
        self.mock_config = Mock()
        self.mock_config.log_level = "INFO"
        self.mock_config.debug_mode = True
        self.mock_config.workspace_root = "/test/workspace"
        self.mock_config_manager.get_config.return_value = self.mock_config
        
        self.engine = ArchitectureAnalysisEngine(self.mock_config_manager)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine._component_name, "ArchitectureAnalysisEngine")
        self.assertIsNotNone(self.engine._analysis_patterns)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Design\n## Components\nTestEngine\nTestManager")
    def test_load_design_documents(self, mock_file, mock_isdir, mock_listdir, mock_exists):
        """Test loading design documents."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ['test-spec']
        mock_isdir.return_value = True
        
        with patch.object(self.engine, '_parse_design_document') as mock_parse:
            mock_parse.return_value = {
                "components": ["TestEngine", "TestManager"],
                "interfaces": ["TestInterface"]
            }
            
            # Initialize engine
            self.engine.initialize()
            
            # Test loading design documents
            design_data = self.engine._load_design_documents()
            
            self.assertIsInstance(design_data, dict)
            mock_parse.assert_called()
    
    def test_parse_design_document(self):
        """Test parsing a design document."""
        design_content = """
# Test Design Document

## Overview
This is a test design.

## Components and Interfaces

```python
class TestEngine:
    def analyze(self):
        pass

class TestManagerInterface:
    def manage(self):
        pass
```

## Architecture
The system has multiple layers.
"""
        
        with patch('builtins.open', mock_open(read_data=design_content)):
            result = self.engine._parse_design_document("/test/design.md")
            
            self.assertIn("sections", result)
            self.assertIn("components", result)
            self.assertIn("interfaces", result)
            self.assertIn("TestEngine", result["components"])
            self.assertIn("TestManagerInterface", result["interfaces"])
    
    def test_extract_components_from_design(self):
        """Test extracting components from design content."""
        content = """
        ```python
        class ArchitectureEngine:
            pass
        
        class DetectionManager:
            pass
        ```
        
        The ValidationSystem handles validation.
        """
        
        components = self.engine._extract_components_from_design(content)
        
        self.assertIn("ArchitectureEngine", components)
        self.assertIn("DetectionManager", components)
        self.assertIn("ValidationSystem", components)
    
    def test_extract_interfaces_from_design(self):
        """Test extracting interfaces from design content."""
        content = """
        ```python
        class AnalysisInterface:
            pass
        
        class DetectionInterface:
            pass
        ```
        """
        
        interfaces = self.engine._extract_interfaces_from_design(content)
        
        self.assertIn("AnalysisInterface", interfaces)
        self.assertIn("DetectionInterface", interfaces)
    
    def test_determine_component_criticality(self):
        """Test determining component criticality levels."""
        # Security components
        self.assertEqual(
            self.engine._determine_component_criticality("SecurityValidator"),
            CriticalityLevel.SECURITY
        )
        
        # Stability components
        self.assertEqual(
            self.engine._determine_component_criticality("CoreEngine"),
            CriticalityLevel.STABILITY
        )
        
        # Functionality components
        self.assertEqual(
            self.engine._determine_component_criticality("DataDetector"),
            CriticalityLevel.FUNCTIONALITY
        )
        
        # UX components
        self.assertEqual(
            self.engine._determine_component_criticality("GuiInterface"),
            CriticalityLevel.UX
        )
    
    def test_assess_component_impact(self):
        """Test assessing component impact."""
        # Security component
        impact = self.engine._assess_component_impact("SecurityValidator")
        self.assertIn("Security vulnerability", impact)
        
        # Stability component
        impact = self.engine._assess_component_impact("CoreEngine")
        self.assertIn("System stability", impact)
        
        # Functionality component
        impact = self.engine._assess_component_impact("DataDetector")
        self.assertIn("Feature functionality", impact)
        
        # UX component
        impact = self.engine._assess_component_impact("GuiInterface")
        self.assertIn("User interface", impact)
    
    def test_estimate_implementation_effort(self):
        """Test estimating implementation effort."""
        # High complexity
        effort = self.engine._estimate_implementation_effort("ArchitectureEngine")
        self.assertIn("High", effort)
        
        # Medium complexity
        effort = self.engine._estimate_implementation_effort("DataAnalyzer")
        self.assertIn("Medium", effort)
        
        # Low complexity
        effort = self.engine._estimate_implementation_effort("BaseInterface")
        self.assertIn("Low", effort)
    
    @patch('pathlib.Path.rglob')
    @patch('builtins.open', new_callable=mock_open, read_data="class TestClass:\n    def test_method(self):\n        pass")
    def test_map_current_architecture(self, mock_file, mock_rglob):
        """Test mapping current architecture."""
        # Setup mock file paths
        mock_files = [
            Path("/test/workspace/core/base.py"),
            Path("/test/workspace/analysis/engine.py")
        ]
        mock_rglob.return_value = mock_files
        
        # Initialize engine
        self.engine.initialize()
        
        # Test architecture mapping
        architecture = self.engine._map_current_architecture()
        
        self.assertIn("components", architecture)
        self.assertIn("layers", architecture)
        self.assertIn("metadata", architecture)
        self.assertIsInstance(architecture["metadata"]["total_files_analyzed"], int)
    
    def test_analyze_file_architecture(self):
        """Test analyzing a single file's architecture."""
        file_content = """
from typing import List
import os

class TestEngine:
    def analyze(self):
        pass

def helper_function():
    pass
"""
        
        architecture = {"components": {}, "dependencies": {}}
        
        with patch('builtins.open', mock_open(read_data=file_content)):
            self.engine._analyze_file_architecture(
                Path("/test/workspace/test.py"), 
                architecture
            )
        
        self.assertIn("test.py", architecture["components"])
        component_info = architecture["components"]["test.py"]
        self.assertIn("TestEngine", component_info["classes"])
        self.assertIn("helper_function", component_info["functions"])
    
    def test_identify_architectural_gaps(self):
        """Test identifying architectural gaps."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["ExistingClass"],
                    "interfaces": ["ExistingInterface"]
                }
            }
        }
        
        design_arch = {
            "test-spec": {
                "components": ["ExistingClass", "MissingClass"],
                "interfaces": ["ExistingInterface", "MissingInterface"]
            }
        }
        
        gaps = self.engine._identify_architectural_gaps(current_arch, design_arch)
        
        self.assertIsInstance(gaps, list)
        # Should find gaps for MissingClass and MissingInterface
        gap_descriptions = [gap.description for gap in gaps]
        self.assertTrue(any("MissingClass" in desc for desc in gap_descriptions))
        self.assertTrue(any("MissingInterface" in desc for desc in gap_descriptions))
    
    def test_identify_lost_functionalities(self):
        """Test identifying lost functionalities."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["ExistingClass"],
                    "functions": ["existing_function"]
                }
            }
        }
        
        design_arch = {
            "test-spec": {
                "sections": {
                    "components and interfaces": "The system provides validation functionality and handles authentication."
                }
            }
        }
        
        lost_functionalities = self.engine._identify_lost_functionalities(current_arch, design_arch)
        
        self.assertIsInstance(lost_functionalities, list)
        # Should identify missing functionalities mentioned in design
        if lost_functionalities:
            self.assertIsInstance(lost_functionalities[0], LostFunctionality)
    
    def test_functionality_exists_in_current(self):
        """Test checking if functionality exists in current implementation."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["ValidationEngine"],
                    "functions": ["validate_data"]
                }
            }
        }
        
        # Should find validation functionality
        self.assertTrue(self.engine._functionality_exists_in_current("validation", current_arch))
        
        # Should not find missing functionality
        self.assertFalse(self.engine._functionality_exists_in_current("authentication", current_arch))
    
    def test_find_architectural_matches(self):
        """Test finding architectural matches."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["SharedClass", "CurrentOnlyClass"],
                    "interfaces": ["SharedInterface"]
                }
            }
        }
        
        design_data = {
            "test-spec": {
                "components": ["SharedClass", "DesignOnlyClass"],
                "interfaces": ["SharedInterface", "DesignOnlyInterface"]
            }
        }
        
        matches = self.engine._find_architectural_matches(current_arch, design_data)
        
        self.assertIn("SharedClass", matches)
        self.assertIn("SharedInterface", matches)
        self.assertNotIn("CurrentOnlyClass", matches)
        self.assertNotIn("DesignOnlyClass", matches)
    
    def test_find_missing_components(self):
        """Test finding missing components."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["ExistingClass"],
                    "interfaces": []
                }
            }
        }
        
        design_data = {
            "test-spec": {
                "components": ["ExistingClass", "MissingClass"],
                "interfaces": ["MissingInterface"]
            }
        }
        
        missing = self.engine._find_missing_components(current_arch, design_data)
        
        self.assertIn("MissingClass", missing)
        self.assertIn("MissingInterface", missing)
        self.assertNotIn("ExistingClass", missing)
    
    def test_find_extra_components(self):
        """Test finding extra components."""
        current_arch = {
            "components": {
                "test.py": {
                    "classes": ["SharedClass", "ExtraClass"],
                    "interfaces": ["ExtraInterface"]
                }
            }
        }
        
        design_data = {
            "test-spec": {
                "components": ["SharedClass"],
                "interfaces": []
            }
        }
        
        extra = self.engine._find_extra_components(current_arch, design_data)
        
        self.assertIn("ExtraClass", extra)
        self.assertIn("ExtraInterface", extra)
        self.assertNotIn("SharedClass", extra)
    
    def test_prioritize_by_criticality(self):
        """Test prioritizing gaps by criticality."""
        gaps = [
            CriticalGap(
                gap_id="gap_001",
                description="UX issue",
                criticality=CriticalityLevel.UX,
                affected_components=["UIComponent"],
                impact_assessment="Low impact",
                recommended_action="Fix UI",
                estimated_effort="Low"
            ),
            CriticalGap(
                gap_id="gap_002",
                description="Security issue",
                criticality=CriticalityLevel.SECURITY,
                affected_components=["SecurityComponent"],
                impact_assessment="High impact",
                recommended_action="Fix security",
                estimated_effort="High"
            ),
            CriticalGap(
                gap_id="gap_003",
                description="Functionality issue",
                criticality=CriticalityLevel.FUNCTIONALITY,
                affected_components=["FeatureComponent"],
                impact_assessment="Medium impact",
                recommended_action="Fix feature",
                estimated_effort="Medium"
            )
        ]
        
        # Initialize engine to set up patterns
        self.engine.initialize()
        
        prioritized_fixes = self.engine.prioritize_by_criticality(gaps)
        
        self.assertEqual(len(prioritized_fixes), 3)
        # Security should be first (highest priority)
        self.assertEqual(prioritized_fixes[0].criticality, CriticalityLevel.SECURITY)
        # UX should be last (lowest priority)
        self.assertEqual(prioritized_fixes[-1].criticality, CriticalityLevel.UX)
    
    @patch.object(ArchitectureAnalysisEngine, '_map_current_architecture')
    @patch.object(ArchitectureAnalysisEngine, '_load_design_documents')
    def test_analyze_current_architecture_integration(self, mock_load_design, mock_map_current):
        """Test the complete analyze_current_architecture method."""
        # Setup mocks
        mock_current_arch = {
            "components": {"test.py": {"classes": ["TestClass"]}},
            "layers": {"core": ["test.py"]},
            "metadata": {"total_files_analyzed": 1}
        }
        mock_design_arch = {
            "test-spec": {
                "components": ["TestClass", "MissingClass"],
                "interfaces": []
            }
        }
        
        mock_map_current.return_value = mock_current_arch
        mock_load_design.return_value = mock_design_arch
        
        # Initialize engine
        self.engine.initialize()
        
        # Test analysis
        result = self.engine.analyze_current_architecture()
        
        self.assertIsInstance(result, ArchitectureAnalysis)
        self.assertEqual(result.current_architecture, mock_current_arch)
        self.assertEqual(result.design_architecture, mock_design_arch)
        self.assertIsInstance(result.identified_gaps, list)
        self.assertIsInstance(result.lost_functionalities, list)
        self.assertIsInstance(result.analysis_timestamp, datetime)
    
    def test_compare_with_design_documents_integration(self):
        """Test the complete compare_with_design_documents method."""
        # Setup current architecture
        mock_current_arch = {
            "components": {
                "test.py": {
                    "classes": ["SharedClass", "ExtraClass"],
                    "interfaces": []
                }
            }
        }
        
        design_content = """
        ```python
        class SharedClass:
            pass
        
        class MissingClass:
            pass
        ```
        """
        
        with patch.object(self.engine, '_map_current_architecture', return_value=mock_current_arch):
            with patch('builtins.open', mock_open(read_data=design_content)):
                # Initialize engine
                self.engine.initialize()
                
                # Test comparison
                result = self.engine.compare_with_design_documents(["/test/design.md"])
                
                self.assertIsInstance(result, ComparisonResult)
                self.assertIn("SharedClass", result.matches)
                self.assertIn("MissingClass", result.missing_components)
                self.assertIn("ExtraClass", result.extra_components)
                self.assertIsInstance(result.compliance_score, float)
                self.assertGreaterEqual(result.compliance_score, 0.0)
                self.assertLessEqual(result.compliance_score, 1.0)


if __name__ == '__main__':
    unittest.main()