"""
Unit tests for Dependency Graph Analyzer.
Tests graph construction, analysis, and visualization capabilities.
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

from core.dependency_graph_analyzer import DependencyGraphAnalyzer
from core.dependency_graph_models import (
    DependencyGraph, DependencyNode, DependencyEdge, DependencyType,
    CircularDependency, VersionConflict, ConflictType, ResolutionPath,
    DependencyAnalysisResult
)


class TestDependencyGraphModels(unittest.TestCase):
    """Test the dependency graph data models."""
    
    def test_dependency_node_creation(self):
        """Test DependencyNode creation and properties."""
        node = DependencyNode(
            name="test-component",
            version="1.0.0",
            installed_version="1.0.0",
            is_installed=True
        )
        
        self.assertEqual(node.name, "test-component")
        self.assertEqual(node.version, "1.0.0")
        self.assertTrue(node.is_installed)
    
    def test_dependency_node_equality(self):
        """Test DependencyNode equality and hashing."""
        node1 = DependencyNode(name="test", version="1.0.0")
        node2 = DependencyNode(name="test", version="1.0.0")
        node3 = DependencyNode(name="test", version="2.0.0")
        
        self.assertEqual(node1, node2)
        self.assertNotEqual(node1, node3)
        self.assertEqual(hash(node1), hash(node2))
        self.assertNotEqual(hash(node1), hash(node3))
    
    def test_dependency_edge_creation(self):
        """Test DependencyEdge creation."""
        edge = DependencyEdge(
            source="component-a",
            target="component-b",
            dependency_type=DependencyType.REQUIRED,
            version_constraint=">=1.0.0"
        )
        
        self.assertEqual(edge.source, "component-a")
        self.assertEqual(edge.target, "component-b")
        self.assertEqual(edge.dependency_type, DependencyType.REQUIRED)
        self.assertEqual(edge.version_constraint, ">=1.0.0")
    
    def test_dependency_graph_operations(self):
        """Test DependencyGraph operations."""
        graph = DependencyGraph()
        
        # Test adding nodes
        node1 = DependencyNode(name="component-a", version="1.0.0")
        node2 = DependencyNode(name="component-b", version="2.0.0")
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        self.assertEqual(len(graph.nodes), 2)
        self.assertIn("component-a", graph.nodes)
        self.assertIn("component-b", graph.nodes)
        
        # Test adding edges
        edge = DependencyEdge(
            source="component-a",
            target="component-b",
            dependency_type=DependencyType.REQUIRED
        )
        graph.add_edge(edge)
        
        self.assertEqual(len(graph.edges), 1)
        self.assertIn("component-b", graph.get_dependencies("component-a"))
        self.assertIn("component-a", graph.get_dependents("component-b"))
    
    def test_circular_dependency_creation(self):
        """Test CircularDependency creation and properties."""
        circular = CircularDependency(
            cycle_path=["A", "B", "C"],
            cycle_length=3,
            severity="high"
        )
        
        self.assertEqual(circular.cycle_description, "A -> B -> C -> A")
        self.assertEqual(circular.cycle_length, 3)
        self.assertEqual(circular.severity, "high")
    
    def test_version_conflict_creation(self):
        """Test VersionConflict creation."""
        conflict = VersionConflict(
            component="test-lib",
            required_versions=["1.0.0", "2.0.0"],
            installed_version="1.5.0",
            conflict_type=ConflictType.VERSION_CONFLICT,
            conflicting_dependencies=["app-a", "app-b"],
            severity="high",
            suggested_resolution="Use version 2.0.0"
        )
        
        self.assertEqual(conflict.component, "test-lib")
        self.assertEqual(len(conflict.required_versions), 2)
        self.assertEqual(conflict.conflict_type, ConflictType.VERSION_CONFLICT)


class TestDependencyGraphAnalyzer(unittest.TestCase):
    """Test the DependencyGraphAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DependencyGraphAnalyzer()
        
        # Register test components
        self.analyzer.register_component("git", {
            "version": "2.47.1",
            "installed_version": "2.47.1",
            "is_installed": True,
            "type": "runtime",
            "dependencies": {}
        })
        
        self.analyzer.register_component("dotnet-sdk", {
            "version": "8.0.0",
            "installed_version": "8.0.0",
            "is_installed": True,
            "type": "sdk",
            "dependencies": {
                "dotnet-runtime": {
                    "type": "required",
                    "version_constraint": ">=8.0.0"
                }
            }
        })
        
        self.analyzer.register_component("dotnet-runtime", {
            "version": "8.0.0",
            "installed_version": "8.0.0",
            "is_installed": True,
            "type": "runtime",
            "dependencies": {}
        })
        
        self.analyzer.register_component("java-jdk", {
            "version": "21.0.0",
            "installed_version": None,
            "is_installed": False,
            "type": "sdk",
            "dependencies": {}
        })
    
    def tearDown(self):
        """Clean up after tests."""
        self.analyzer.clear_registry()
    
    def test_create_dependency_graph(self):
        """Test dependency graph creation."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        
        # Check nodes
        self.assertEqual(len(graph.nodes), 3)
        self.assertIn("git", graph.nodes)
        self.assertIn("dotnet-sdk", graph.nodes)
        self.assertIn("dotnet-runtime", graph.nodes)
        
        # Check edges
        self.assertTrue(len(graph.edges) >= 1)
        
        # Check dependencies
        dotnet_deps = graph.get_dependencies("dotnet-sdk")
        self.assertIn("dotnet-runtime", dotnet_deps)
    
    def test_analyze_graph_basic(self):
        """Test basic graph analysis."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        result = self.analyzer.analyze_graph(graph)
        
        self.assertIsInstance(result, DependencyAnalysisResult)
        self.assertEqual(result.total_components, 3)
        self.assertGreaterEqual(result.satisfied_dependencies, 0)
        self.assertGreaterEqual(result.analysis_duration, 0)
    
    def test_detect_circular_dependencies_none(self):
        """Test circular dependency detection with no cycles."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        
        circular_deps = self.analyzer.detect_circular_dependencies(graph)
        self.assertEqual(len(circular_deps), 0)
    
    def test_detect_circular_dependencies_with_cycle(self):
        """Test circular dependency detection with cycles."""
        # Register components with circular dependencies
        self.analyzer.register_component("comp-a", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-b": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("comp-b", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-c": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("comp-c", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-a": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        components = ["comp-a", "comp-b", "comp-c"]
        graph = self.analyzer.create_dependency_graph(components)
        
        circular_deps = self.analyzer.detect_circular_dependencies(graph)
        self.assertGreater(len(circular_deps), 0)
        
        # Check that the cycle is properly detected
        cycle = circular_deps[0]
        self.assertEqual(cycle.cycle_length, 3)
        self.assertIn("comp-a", cycle.cycle_path)
        self.assertIn("comp-b", cycle.cycle_path)
        self.assertIn("comp-c", cycle.cycle_path)
    
    def test_detect_version_conflicts_none(self):
        """Test version conflict detection with no conflicts."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        
        conflicts = self.analyzer.detect_version_conflicts(graph)
        self.assertEqual(len(conflicts), 0)
    
    def test_detect_version_conflicts_with_conflicts(self):
        """Test version conflict detection with actual conflicts."""
        # Register components with conflicting version requirements
        self.analyzer.register_component("app-a", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "shared-lib": {"type": "required", "version_constraint": "==1.0.0"}
            }
        })
        
        self.analyzer.register_component("app-b", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "shared-lib": {"type": "required", "version_constraint": "==2.0.0"}
            }
        })
        
        self.analyzer.register_component("shared-lib", {
            "version": "1.5.0",
            "installed_version": "1.5.0",
            "is_installed": True,
            "dependencies": {}
        })
        
        components = ["app-a", "app-b", "shared-lib"]
        graph = self.analyzer.create_dependency_graph(components)
        
        conflicts = self.analyzer.detect_version_conflicts(graph)
        self.assertGreater(len(conflicts), 0)
        
        # Check conflict details
        conflict = conflicts[0]
        self.assertEqual(conflict.component, "shared-lib")
        self.assertIn("==1.0.0", conflict.required_versions)
        self.assertIn("==2.0.0", conflict.required_versions)
        self.assertIn("app-a", conflict.conflicting_dependencies)
        self.assertIn("app-b", conflict.conflicting_dependencies)
    
    def test_calculate_shortest_resolution_path_no_conflicts(self):
        """Test resolution path calculation with no conflicts."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        
        path = self.analyzer.calculate_shortest_resolution_path(graph)
        self.assertIsNotNone(path)
        self.assertEqual(path.steps, ["No conflicts to resolve"])
        self.assertEqual(path.estimated_time, 0)
    
    def test_calculate_shortest_resolution_path_with_conflicts(self):
        """Test resolution path calculation with conflicts."""
        # Create a graph with conflicts
        self.analyzer.register_component("conflict-app", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "conflict-lib": {"type": "required", "version_constraint": "==1.0.0"}
            }
        })
        
        self.analyzer.register_component("conflict-lib", {
            "version": "2.0.0",
            "installed_version": "2.0.0",
            "is_installed": True,
            "dependencies": {}
        })
        
        components = ["conflict-app", "conflict-lib"]
        graph = self.analyzer.create_dependency_graph(components)
        
        # Force a conflict by manually adding one
        conflict = VersionConflict(
            component="conflict-lib",
            required_versions=["==1.0.0", "==2.0.0"],
            installed_version="2.0.0",
            conflict_type=ConflictType.VERSION_CONFLICT,
            conflicting_dependencies=["conflict-app"],
            suggested_resolution="Use version 2.0.0"
        )
        graph.version_conflicts.append(conflict)
        
        path = self.analyzer.calculate_shortest_resolution_path(graph)
        self.assertIsNotNone(path)
        self.assertGreater(len(path.steps), 0)
        self.assertGreater(path.estimated_time, 0)
    
    def test_visualize_dependencies(self):
        """Test dependency visualization."""
        components = ["git", "dotnet-sdk", "dotnet-runtime"]
        graph = self.analyzer.create_dependency_graph(components)
        
        visualization = self.analyzer.visualize_dependencies(graph)
        
        self.assertIsInstance(visualization, str)
        self.assertIn("Dependency Graph Visualization", visualization)
        self.assertIn("Components:", visualization)
        self.assertIn("Dependencies:", visualization)
        self.assertIn("git", visualization)
        self.assertIn("dotnet-sdk", visualization)
        self.assertIn("dotnet-runtime", visualization)
    
    def test_visualize_dependencies_with_conflicts(self):
        """Test visualization with conflicts."""
        # Create graph with conflicts
        components = ["git"]
        graph = self.analyzer.create_dependency_graph(components)
        
        # Add a mock conflict
        conflict = VersionConflict(
            component="git",
            required_versions=["2.47.1", "2.46.0"],
            installed_version="2.47.1",
            conflict_type=ConflictType.VERSION_CONFLICT,
            conflicting_dependencies=["app1", "app2"]
        )
        graph.version_conflicts.append(conflict)
        
        # Add a mock circular dependency
        circular = CircularDependency(
            cycle_path=["A", "B", "C"],
            cycle_length=3
        )
        graph.circular_dependencies.append(circular)
        
        visualization = self.analyzer.visualize_dependencies(graph)
        
        self.assertIn("Version Conflicts:", visualization)
        self.assertIn("Circular Dependencies:", visualization)
        self.assertIn("⚠", visualization)
        self.assertIn("🔄", visualization)
    
    def test_component_registration(self):
        """Test component registration and clearing."""
        # Test registration
        self.analyzer.register_component("test-component", {
            "version": "1.0.0",
            "is_installed": True
        })
        
        # Verify registration worked
        components = ["test-component"]
        graph = self.analyzer.create_dependency_graph(components)
        self.assertIn("test-component", graph.nodes)
        
        # Test clearing
        self.analyzer.clear_registry()
        graph2 = self.analyzer.create_dependency_graph(components)
        node = graph2.get_node("test-component")
        self.assertIsNotNone(node)
        self.assertFalse(node.is_installed)  # Should be default values
    
    def test_version_constraint_checking(self):
        """Test version constraint satisfaction checking."""
        # Test various version constraints
        test_cases = [
            ("1.0.0", ">=1.0.0", True),
            ("1.1.0", ">=1.0.0", True),
            ("0.9.0", ">=1.0.0", False),
            ("1.0.0", "<=1.0.0", True),
            ("0.9.0", "<=1.0.0", True),
            ("1.1.0", "<=1.0.0", False),
            ("1.0.0", "==1.0.0", True),
            ("1.0.1", "==1.0.0", False),
            ("1.1.0", ">1.0.0", True),
            ("1.0.0", ">1.0.0", False),
            ("0.9.0", "<1.0.0", True),
            ("1.0.0", "<1.0.0", False),
        ]
        
        for version, constraint, expected in test_cases:
            with self.subTest(version=version, constraint=constraint):
                result = self.analyzer._version_satisfies_constraint(version, constraint)
                self.assertEqual(result, expected)
    
    def test_dependency_analysis_result_properties(self):
        """Test DependencyAnalysisResult calculated properties."""
        graph = DependencyGraph()
        result = DependencyAnalysisResult(
            graph=graph,
            total_components=5,
            satisfied_dependencies=8,
            unsatisfied_dependencies=2,
            conflicts_found=1,
            circular_dependencies_found=0,
            analysis_duration=1.5
        )
        
        # Test satisfaction rate
        self.assertEqual(result.satisfaction_rate, 80.0)
        
        # Test critical issues detection
        self.assertTrue(result.has_critical_issues)
        
        # Test with no issues
        result_no_issues = DependencyAnalysisResult(
            graph=graph,
            total_components=3,
            satisfied_dependencies=5,
            unsatisfied_dependencies=0,
            conflicts_found=0,
            circular_dependencies_found=0
        )
        
        self.assertEqual(result_no_issues.satisfaction_rate, 100.0)
        self.assertFalse(result_no_issues.has_critical_issues)
    
    def test_resolution_path_operations(self):
        """Test ResolutionPath operations."""
        path = ResolutionPath(
            steps=["Step 1"],
            estimated_time=30,
            complexity="medium"
        )
        
        # Test adding steps and actions
        path.add_step("Step 2")
        path.add_action("Action 1")
        
        self.assertEqual(len(path.steps), 2)
        self.assertEqual(len(path.required_actions), 1)
        self.assertIn("Step 2", path.steps)
        self.assertIn("Action 1", path.required_actions)


class TestDependencyGraphIntegration(unittest.TestCase):
    """Integration tests for the complete dependency graph system."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.analyzer = DependencyGraphAnalyzer()
        
        # Register a complex set of components for integration testing
        self.analyzer.register_component("web-app", {
            "version": "1.0.0",
            "installed_version": "1.0.0",
            "is_installed": True,
            "type": "application",
            "dependencies": {
                "node-js": {"type": "runtime", "version_constraint": ">=18.0.0"},
                "database": {"type": "required", "version_constraint": ">=5.0.0"}
            }
        })
        
        self.analyzer.register_component("node-js", {
            "version": "18.17.0",
            "installed_version": "18.17.0",
            "is_installed": True,
            "type": "runtime",
            "dependencies": {}
        })
        
        self.analyzer.register_component("database", {
            "version": "5.2.0",
            "installed_version": "4.9.0",  # Older version installed
            "is_installed": True,
            "type": "service",
            "dependencies": {}
        })
        
        self.analyzer.register_component("admin-tool", {
            "version": "2.0.0",
            "installed_version": None,
            "is_installed": False,
            "type": "tool",
            "dependencies": {
                "database": {"type": "required", "version_constraint": ">=5.0.0"}
            }
        })
    
    def tearDown(self):
        """Clean up after integration tests."""
        self.analyzer.clear_registry()
    
    def test_complete_analysis_workflow(self):
        """Test the complete analysis workflow from creation to resolution."""
        components = ["web-app", "node-js", "database", "admin-tool"]
        
        # Step 1: Create dependency graph
        graph = self.analyzer.create_dependency_graph(components)
        self.assertEqual(len(graph.nodes), 4)
        
        # Step 2: Analyze the graph
        result = self.analyzer.analyze_graph(graph)
        self.assertIsInstance(result, DependencyAnalysisResult)
        self.assertEqual(result.total_components, 4)
        
        # Step 3: Check for expected issues
        # Should have unsatisfied dependencies due to database version mismatch
        self.assertGreater(result.unsatisfied_dependencies, 0)
        
        # Step 4: Generate visualization
        visualization = self.analyzer.visualize_dependencies(graph)
        self.assertIn("web-app", visualization)
        self.assertIn("database", visualization)
        
        # Step 5: Calculate resolution path
        resolution = self.analyzer.calculate_shortest_resolution_path(graph)
        self.assertIsNotNone(resolution)
    
    def test_transitive_dependency_calculation(self):
        """Test that transitive dependencies are correctly calculated."""
        # Create a chain: A -> B -> C -> D
        self.analyzer.register_component("comp-a", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-b": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("comp-b", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-c": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("comp-c", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "comp-d": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("comp-d", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {}
        })
        
        components = ["comp-a", "comp-b", "comp-c", "comp-d"]
        graph = self.analyzer.create_dependency_graph(components)
        
        # Check transitive dependencies
        transitive_a = graph.transitive_dependencies.get("comp-a", set())
        self.assertIn("comp-b", transitive_a)
        self.assertIn("comp-c", transitive_a)
        self.assertIn("comp-d", transitive_a)
        
        # comp-d should have no transitive dependencies
        transitive_d = graph.transitive_dependencies.get("comp-d", set())
        self.assertEqual(len(transitive_d), 0)
    
    def test_complex_conflict_scenario(self):
        """Test a complex scenario with multiple types of conflicts."""
        # Create components with both version conflicts and circular dependencies
        self.analyzer.register_component("frontend", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "shared-utils": {"type": "required", "version_constraint": "==1.0.0"},
                "backend": {"type": "required", "version_constraint": ">=1.0.0"}
            }
        })
        
        self.analyzer.register_component("backend", {
            "version": "1.0.0",
            "is_installed": True,
            "dependencies": {
                "shared-utils": {"type": "required", "version_constraint": "==2.0.0"},
                "frontend": {"type": "optional", "version_constraint": ">=1.0.0"}  # Creates cycle
            }
        })
        
        self.analyzer.register_component("shared-utils", {
            "version": "1.5.0",
            "installed_version": "1.5.0",
            "is_installed": True,
            "dependencies": {}
        })
        
        components = ["frontend", "backend", "shared-utils"]
        graph = self.analyzer.create_dependency_graph(components)
        result = self.analyzer.analyze_graph(graph)
        
        # Should detect both version conflicts and circular dependencies
        self.assertGreater(result.conflicts_found, 0)
        self.assertGreater(result.circular_dependencies_found, 0)
        self.assertTrue(result.has_critical_issues)
        
        # Resolution path should address both issues
        resolution = self.analyzer.calculate_shortest_resolution_path(graph)
        self.assertIsNotNone(resolution)
        self.assertGreater(len(resolution.steps), 1)  # Multiple steps needed
        self.assertIn(resolution.complexity, ["medium", "high"])  # Should be medium or high complexity


if __name__ == '__main__':
    unittest.main()